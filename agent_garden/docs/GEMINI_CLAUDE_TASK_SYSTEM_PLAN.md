# Gemini-Claude Task Execution System - Implementation Plan

## Overview

Transform the current system where:
- **Current:** Claude builds code → Gemini executes
- **New:** Gemini receives user requests → Claude executes tasks

**New Architecture:**
```
User → Gemini (UI) → Task Queue (Celery + Redis) → Claude (Terminal) → OneDrive Results
```

---

## Architecture Components

### 1. **Gemini (Front-of-House)** - Web UI on Render
- Hosted on Render (Agent Garden UI)
- Chats with users in natural language
- Interprets user intent into structured tasks
- Creates tasks in database
- Shows task status and results to user

### 2. **Task Queue (Celery + Redis)** - On Render
- PostgreSQL table: `claude_tasks`
- Celery Beat for scheduling
- Redis for task queue
- Manages task lifecycle (pending → ready → in_progress → completed)

### 3. **Claude Executor (Back-of-House)** - Your Mac Terminal
- Runs 24/7 on your Mac
- Polls for ready tasks every 30 seconds
- Has access to:
  - Project files (SOPs, rules, calculations)
  - TiDB database (via MCP)
  - OneDrive (save reports)
  - Local Python scripts
- Executes tasks and updates status

---

## Phase 1: Database Schema Setup

**Duration:** 30 minutes

### 1.1 Create `claude_tasks` Table

**File:** Add migration to Agent Garden database

```sql
CREATE TABLE claude_tasks (
    id SERIAL PRIMARY KEY,

    -- Task Definition
    task_type VARCHAR(50) NOT NULL,           -- 'report', 'query', 'calculation', 'analysis'
    task_json TEXT NOT NULL,                  -- Full task details as JSON

    -- Scheduling
    schedule_cron VARCHAR(50),                -- NULL = one-time, "0 7 * * *" = recurring
    schedule_enabled BOOLEAN DEFAULT TRUE,    -- Can disable without deleting

    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending',     -- 'pending', 'ready', 'in_progress', 'completed', 'failed'

    -- Results
    result_path VARCHAR(500),                 -- OneDrive path to generated file
    result_summary TEXT,                      -- Brief description of result
    error_log TEXT,                           -- Error details if failed

    -- Metadata
    created_by VARCHAR(100),                  -- User ID or 'system'
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Execution Stats
    execution_count INTEGER DEFAULT 0,        -- How many times run (for recurring)
    last_execution_at TIMESTAMP,

    -- Indexes
    INDEX idx_status (status),
    INDEX idx_schedule (schedule_cron, schedule_enabled),
    INDEX idx_created_at (created_at)
);
```

### 1.2 Create `task_execution_history` Table

```sql
CREATE TABLE task_execution_history (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES claude_tasks(id) ON DELETE CASCADE,

    -- Execution Details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20),                       -- 'completed', 'failed'

    -- Results
    result_path VARCHAR(500),
    error_log TEXT,
    execution_time_seconds INTEGER,

    INDEX idx_task_id (task_id),
    INDEX idx_started_at (started_at)
);
```

### 1.3 Task JSON Schema Examples

**Example 1: Low Stock Report**
```json
{
  "task_type": "report_generation",
  "report_name": "low_stock",
  "parameters": {
    "threshold": "reorder_point",
    "include_categories": ["all"]
  },
  "output": {
    "format": "xlsx",
    "path": "Reports/LowStock/",
    "filename_pattern": "LowStock_{date}.xlsx"
  },
  "sop_reference": "sops/inventory/low_stock_calculation.md"
}
```

**Example 2: Custom Query**
```json
{
  "task_type": "query_execution",
  "query": "SELECT * FROM products WHERE quantity < 10",
  "output": {
    "format": "csv",
    "path": "Reports/Custom/",
    "filename_pattern": "Query_{timestamp}.csv"
  }
}
```

**Example 3: Calculation Task**
```json
{
  "task_type": "calculation",
  "calculation_name": "reorder_quantities",
  "script": "scripts/calculate_reorder.py",
  "output": {
    "format": "json",
    "path": "Reports/Calculations/",
    "return_to_gemini": true
  }
}
```

---

## Phase 2: Celery Task Integration

**Duration:** 1 hour

### 2.1 Create Celery Task for Claude Triggering

**File:** `/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/agent_garden/autonomous_agents/claude_executor_trigger.py`

```python
"""
Celery task that triggers Claude task execution
Runs on Render at scheduled times via Celery Beat
"""

from src.scheduling.celery_app import celery_app
from src.core.database import get_db_connection
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='autonomous_agents.trigger_claude_task')
def trigger_claude_task(task_id):
    """
    Mark a task as ready for Claude to execute
    This is triggered by Celery Beat at the scheduled time

    Args:
        task_id: ID of the task in claude_tasks table
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update task status to 'ready'
        cursor.execute("""
            UPDATE claude_tasks
            SET status = 'ready'
            WHERE id = %s AND status = 'pending'
        """, (task_id,))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"✅ Task {task_id} marked ready for Claude execution")
        return {'success': True, 'task_id': task_id}

    except Exception as e:
        logger.error(f"❌ Error triggering task {task_id}: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='autonomous_agents.cleanup_old_tasks')
def cleanup_old_tasks():
    """
    Cleanup completed tasks older than 30 days
    Runs daily via Celery Beat
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM claude_tasks
            WHERE status = 'completed'
            AND completed_at < NOW() - INTERVAL '30 days'
            AND schedule_cron IS NULL
        """)

        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"🧹 Cleaned up {deleted} old completed tasks")
        return {'deleted': deleted}

    except Exception as e:
        logger.error(f"❌ Error cleaning up tasks: {e}")
        return {'success': False, 'error': str(e)}
```

### 2.2 Register Cleanup Task in Schedule

**File:** Add to database schedules or `celeryconfig.py`

```python
# Add to beat_schedule in database
{
    'cleanup-old-claude-tasks': {
        'task': 'autonomous_agents.cleanup_old_tasks',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    }
}
```

---

## Phase 3: API Endpoints for Task Management

**Duration:** 1.5 hours

### 3.1 Add Task Endpoints to `unified_app.py`

**File:** `/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/unified_app.py`

Add these endpoints:

```python
# ============================================
# CLAUDE TASK QUEUE ENDPOINTS
# ============================================

@app.route('/tasks/create', methods=['POST'])
def create_task():
    """
    Gemini calls this to create a new task for Claude

    Request Body:
    {
        "task_type": "report_generation",
        "task_json": {...},
        "schedule_cron": "0 7 * * *",  // optional
        "created_by": "user_123"       // optional
    }
    """
    try:
        data = request.json

        # Insert into database
        cursor = db_connection.cursor()
        cursor.execute("""
            INSERT INTO claude_tasks
            (task_type, task_json, schedule_cron, created_by, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['task_type'],
            json.dumps(data['task_json']),
            data.get('schedule_cron'),
            data.get('created_by', 'gemini'),
            'ready' if not data.get('schedule_cron') else 'pending'
        ))

        task_id = cursor.fetchone()[0]
        db_connection.commit()

        # If scheduled, add to Celery Beat
        if data.get('schedule_cron'):
            from celery.schedules import crontab
            from agent_garden.src.scheduling.celery_app import celery_app

            # Parse cron expression
            parts = data['schedule_cron'].split()
            schedule_config = {
                'minute': parts[0] if len(parts) > 0 else '*',
                'hour': parts[1] if len(parts) > 1 else '*',
                'day_of_month': parts[2] if len(parts) > 2 else '*',
                'month_of_year': parts[3] if len(parts) > 3 else '*',
                'day_of_week': parts[4] if len(parts) > 4 else '*',
            }

            # Add to Celery Beat schedule
            celery_app.conf.beat_schedule[f'claude-task-{task_id}'] = {
                'task': 'autonomous_agents.trigger_claude_task',
                'schedule': crontab(**schedule_config),
                'args': (task_id,)
            }

            logger.info(f"📅 Scheduled task {task_id} with cron: {data['schedule_cron']}")

        cursor.close()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task created successfully',
            'scheduled': bool(data.get('schedule_cron'))
        })

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/ready', methods=['GET'])
def get_ready_tasks():
    """
    Claude executor polls this to get tasks ready for execution
    Returns all tasks with status='ready'
    """
    try:
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, task_type, task_json, created_at, created_by
            FROM claude_tasks
            WHERE status = 'ready'
            ORDER BY created_at ASC
        """)

        tasks = cursor.fetchall()
        cursor.close()

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error fetching ready tasks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """
    Claude calls this when starting execution
    Updates status to 'in_progress'
    """
    try:
        cursor = db_connection.cursor()
        cursor.execute("""
            UPDATE claude_tasks
            SET status = 'in_progress',
                started_at = NOW()
            WHERE id = %s
        """, (task_id,))

        db_connection.commit()
        cursor.close()

        return jsonify({'success': True, 'message': 'Task started'})

    except Exception as e:
        logger.error(f"Error starting task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """
    Claude calls this when task completes successfully

    Request Body:
    {
        "result_path": "OneDrive/Reports/LowStock/2025-12-29.xlsx",
        "result_summary": "Generated low stock report with 45 items"
    }
    """
    try:
        data = request.json

        cursor = db_connection.cursor()

        # Get task details to check if recurring
        cursor.execute("""
            SELECT schedule_cron, execution_count
            FROM claude_tasks
            WHERE id = %s
        """, (task_id,))

        task = cursor.fetchone()
        is_recurring = task[0] is not None

        # Insert into execution history
        cursor.execute("""
            INSERT INTO task_execution_history
            (task_id, started_at, completed_at, status, result_path)
            SELECT id, started_at, NOW(), 'completed', %s
            FROM claude_tasks
            WHERE id = %s
        """, (data.get('result_path'), task_id))

        if is_recurring:
            # Reset to pending for next run
            cursor.execute("""
                UPDATE claude_tasks
                SET status = 'pending',
                    result_path = %s,
                    result_summary = %s,
                    last_execution_at = NOW(),
                    execution_count = execution_count + 1
                WHERE id = %s
            """, (data.get('result_path'), data.get('result_summary'), task_id))
        else:
            # One-time task - mark as completed
            cursor.execute("""
                UPDATE claude_tasks
                SET status = 'completed',
                    completed_at = NOW(),
                    result_path = %s,
                    result_summary = %s,
                    execution_count = execution_count + 1
                WHERE id = %s
            """, (data.get('result_path'), data.get('result_summary'), task_id))

        db_connection.commit()
        cursor.close()

        logger.info(f"✅ Task {task_id} completed: {data.get('result_summary')}")

        return jsonify({
            'success': True,
            'message': 'Task completed',
            'is_recurring': is_recurring
        })

    except Exception as e:
        logger.error(f"Error completing task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/<int:task_id>/fail', methods=['POST'])
def fail_task(task_id):
    """
    Claude calls this when task fails

    Request Body:
    {
        "error_log": "Error message details..."
    }
    """
    try:
        data = request.json

        cursor = db_connection.cursor()

        # Insert into execution history
        cursor.execute("""
            INSERT INTO task_execution_history
            (task_id, started_at, completed_at, status, error_log)
            SELECT id, started_at, NOW(), 'failed', %s
            FROM claude_tasks
            WHERE id = %s
        """, (data.get('error_log'), task_id))

        # Update task
        cursor.execute("""
            UPDATE claude_tasks
            SET status = 'failed',
                error_log = %s,
                last_execution_at = NOW()
            WHERE id = %s
        """, (data.get('error_log'), task_id))

        db_connection.commit()
        cursor.close()

        logger.error(f"❌ Task {task_id} failed: {data.get('error_log')}")

        return jsonify({'success': True, 'message': 'Task marked as failed'})

    except Exception as e:
        logger.error(f"Error marking task {task_id} as failed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task_details(task_id):
    """
    Get detailed information about a specific task
    Includes execution history
    """
    try:
        cursor = db_connection.cursor(cursor_factory=RealDictCursor)

        # Get task details
        cursor.execute("""
            SELECT * FROM claude_tasks WHERE id = %s
        """, (task_id,))

        task = cursor.fetchone()

        if not task:
            return jsonify({'success': False, 'error': 'Task not found'}), 404

        # Get execution history
        cursor.execute("""
            SELECT * FROM task_execution_history
            WHERE task_id = %s
            ORDER BY started_at DESC
            LIMIT 10
        """, (task_id,))

        history = cursor.fetchall()
        cursor.close()

        return jsonify({
            'success': True,
            'task': task,
            'execution_history': history
        })

    except Exception as e:
        logger.error(f"Error fetching task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/tasks/list', methods=['GET'])
def list_tasks():
    """
    List all tasks with optional filtering
    Query params: status, task_type, limit
    """
    try:
        status = request.args.get('status')
        task_type = request.args.get('task_type')
        limit = request.args.get('limit', 100, type=int)

        query = "SELECT * FROM claude_tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        if task_type:
            query += " AND task_type = %s"
            params.append(task_type)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor = db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)

        tasks = cursor.fetchall()
        cursor.close()

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## Phase 4: Claude Executor Script

**Duration:** 2 hours

### 4.1 Create Main Executor Script

**File:** `/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/claude_executor.py`

```python
#!/usr/bin/env python3
"""
Claude Task Executor
Runs on your Mac terminal 24/7
Polls MCP server for ready tasks and executes them
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
import subprocess

# Configuration
MCP_SERVER = os.getenv('MCP_SERVER', 'https://gpt-mcp.onrender.com')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))  # seconds
ONEDRIVE_BASE = Path.home() / "Library/CloudStorage/OneDrive-Personal"
PROJECT_ROOT = Path(__file__).parent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('claude_executor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ClaudeExecutor:
    """Main executor class for Claude tasks"""

    def __init__(self):
        self.mcp_server = MCP_SERVER
        self.onedrive_base = ONEDRIVE_BASE
        self.project_root = PROJECT_ROOT

    def poll_ready_tasks(self):
        """Poll MCP server for tasks ready to execute"""
        try:
            response = requests.get(f"{self.mcp_server}/tasks/ready", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except Exception as e:
            logger.error(f"Error polling tasks: {e}")
            return []

    def mark_task_started(self, task_id):
        """Mark task as in_progress"""
        try:
            requests.post(f"{self.mcp_server}/tasks/{task_id}/start")
            logger.info(f"📋 Task {task_id} started")
        except Exception as e:
            logger.error(f"Error marking task {task_id} as started: {e}")

    def mark_task_completed(self, task_id, result_path, summary):
        """Mark task as completed"""
        try:
            requests.post(
                f"{self.mcp_server}/tasks/{task_id}/complete",
                json={
                    'result_path': result_path,
                    'result_summary': summary
                }
            )
            logger.info(f"✅ Task {task_id} completed: {summary}")
        except Exception as e:
            logger.error(f"Error marking task {task_id} as completed: {e}")

    def mark_task_failed(self, task_id, error_log):
        """Mark task as failed"""
        try:
            requests.post(
                f"{self.mcp_server}/tasks/{task_id}/fail",
                json={'error_log': error_log}
            )
            logger.error(f"❌ Task {task_id} failed: {error_log}")
        except Exception as e:
            logger.error(f"Error marking task {task_id} as failed: {e}")

    def execute_task(self, task):
        """Execute a single task"""
        task_id = task['id']
        task_type = task['task_type']
        task_json = json.loads(task['task_json'])

        logger.info(f"🚀 Executing task {task_id} ({task_type})")

        # Mark as started
        self.mark_task_started(task_id)

        try:
            # Route to appropriate handler
            if task_type == 'report_generation':
                result = self.handle_report_generation(task_json)
            elif task_type == 'query_execution':
                result = self.handle_query_execution(task_json)
            elif task_type == 'calculation':
                result = self.handle_calculation(task_json)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Mark as completed
            self.mark_task_completed(
                task_id,
                result['path'],
                result['summary']
            )

        except Exception as e:
            # Mark as failed
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.mark_task_failed(task_id, error_msg)

    def handle_report_generation(self, task_json):
        """Handle report generation tasks"""
        logger.info(f"📊 Generating report: {task_json.get('report_name')}")

        # TODO: Implement report generation logic
        # 1. Read SOP from task_json['sop_reference']
        # 2. Query TiDB via MCP
        # 3. Run calculations
        # 4. Generate report file
        # 5. Save to OneDrive

        # Placeholder
        output_path = self.onedrive_base / task_json['output']['path']
        output_path.mkdir(parents=True, exist_ok=True)

        filename = task_json['output']['filename_pattern'].format(
            date=datetime.now().strftime('%Y-%m-%d'),
            timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        )

        result_file = output_path / filename

        # Create placeholder file
        with open(result_file, 'w') as f:
            f.write(f"Report generated at {datetime.now()}\n")

        return {
            'path': str(result_file.relative_to(self.onedrive_base)),
            'summary': f"Generated {task_json.get('report_name')} report"
        }

    def handle_query_execution(self, task_json):
        """Handle query execution tasks"""
        logger.info(f"🔍 Executing query")

        # TODO: Implement query execution
        # 1. Execute query via TiDB MCP
        # 2. Format results
        # 3. Save to OneDrive

        return {
            'path': 'Reports/Query/result.csv',
            'summary': 'Query executed successfully'
        }

    def handle_calculation(self, task_json):
        """Handle calculation tasks"""
        logger.info(f"🧮 Running calculation: {task_json.get('calculation_name')}")

        # TODO: Implement calculation logic
        # 1. Load calculation script
        # 2. Execute with parameters
        # 3. Save results

        return {
            'path': 'Reports/Calculations/result.json',
            'summary': 'Calculation completed'
        }

    def run(self):
        """Main execution loop"""
        logger.info("🚀 Claude Task Executor started")
        logger.info(f"📡 Polling {self.mcp_server} every {POLL_INTERVAL}s")
        logger.info(f"📁 OneDrive base: {self.onedrive_base}")

        while True:
            try:
                # Poll for ready tasks
                tasks = self.poll_ready_tasks()

                if tasks:
                    logger.info(f"📋 Found {len(tasks)} ready task(s)")

                    for task in tasks:
                        self.execute_task(task)

                # Wait before next poll
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("⏹️  Executor stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    executor = ClaudeExecutor()
    executor.run()
```

### 4.2 Create Helper Functions Module

**File:** `/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/executor_helpers.py`

```python
"""
Helper functions for Claude executor
Handles SOPs, calculations, OneDrive operations
"""

from pathlib import Path
import json


def read_sop(sop_path):
    """Read SOP markdown file"""
    sop_file = Path(__file__).parent / sop_path
    if sop_file.exists():
        return sop_file.read_text()
    raise FileNotFoundError(f"SOP not found: {sop_path}")


def query_tidb_via_mcp(query):
    """Query TiDB database via MCP"""
    # TODO: Implement MCP query
    pass


def save_to_onedrive(data, output_config, onedrive_base):
    """Save data to OneDrive following output config"""
    from datetime import datetime

    output_path = Path(onedrive_base) / output_config['path']
    output_path.mkdir(parents=True, exist_ok=True)

    filename = output_config['filename_pattern'].format(
        date=datetime.now().strftime('%Y-%m-%d'),
        timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    )

    result_file = output_path / filename

    # Save based on format
    if output_config['format'] == 'json':
        with open(result_file, 'w') as f:
            json.dump(data, f, indent=2)
    elif output_config['format'] == 'csv':
        # TODO: Implement CSV writing
        pass
    elif output_config['format'] == 'xlsx':
        # TODO: Implement Excel writing
        pass

    return result_file
```

---

## Phase 5: Update Gemini to Create Tasks

**Duration:** 1 hour

### 5.1 Modify Agent Backend

**File:** `/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/render-tidb-sync/agent_garden/src/core/agent_backend.py`

Add function for Gemini to create tasks:

```python
def create_claude_task(user_message, user_context):
    """
    Gemini analyzes user message and creates structured task for Claude

    Args:
        user_message: User's natural language request
        user_context: User session context

    Returns:
        Task creation result
    """
    import requests

    # Use Gemini to interpret user intent
    interpretation = interpret_user_intent(user_message)

    # Create structured task
    task_data = {
        'task_type': interpretation['task_type'],
        'task_json': interpretation['task_details'],
        'schedule_cron': interpretation.get('schedule_cron'),
        'created_by': user_context.get('user_id', 'anonymous')
    }

    # Send to task queue
    response = requests.post(
        'http://localhost:8080/tasks/create',
        json=task_data
    )

    result = response.json()

    if result['success']:
        task_id = result['task_id']

        if result['scheduled']:
            return f"✅ Task created! Claude will execute it on schedule: {interpretation.get('schedule_cron')}\n\nTask ID: {task_id}"
        else:
            return f"✅ Task created! Claude is executing it now.\n\nTask ID: {task_id}\n\nYou can check status with: /task {task_id}"
    else:
        return f"❌ Error creating task: {result.get('error')}"


def interpret_user_intent(user_message):
    """
    Use Gemini to interpret user's natural language into structured task

    Example inputs:
    - "I need a low stock report at 7AM daily"
    - "Show me all products below reorder point"
    - "Calculate reorder quantities for all vendors"
    """
    # TODO: Implement Gemini interpretation
    # This will use Gemini API to understand intent and extract:
    # - task_type
    # - parameters
    # - schedule (if any)
    # - output preferences

    # Placeholder
    if "low stock" in user_message.lower():
        return {
            'task_type': 'report_generation',
            'task_details': {
                'report_name': 'low_stock',
                'parameters': {'threshold': 'reorder_point'},
                'output': {
                    'format': 'xlsx',
                    'path': 'Reports/LowStock/',
                    'filename_pattern': 'LowStock_{date}.xlsx'
                }
            },
            'schedule_cron': '0 7 * * *' if 'daily' in user_message.lower() else None
        }

    # Add more patterns...

    return {
        'task_type': 'query_execution',
        'task_details': {
            'query': user_message
        }
    }
```

---

## Phase 6: Testing Plan

**Duration:** 2 hours

### Test Case 1: One-Time Report
```
1. User says to Gemini: "Generate a low stock report now"
2. Gemini creates task with no schedule
3. Verify task appears in database with status='ready'
4. Claude executor picks it up within 30 seconds
5. Verify status changes: ready → in_progress → completed
6. Check OneDrive for generated file
7. Verify task marked completed in database
```

### Test Case 2: Scheduled Report
```
1. User says: "I need low stock reports every morning at 7 AM"
2. Gemini creates task with schedule_cron='0 7 * * *'
3. Verify task in database with status='pending'
4. Verify Celery Beat schedule added
5. Wait for scheduled time (or trigger manually)
6. Verify Celery marks task as 'ready'
7. Claude executes and saves to OneDrive
8. Verify task reset to 'pending' for next run
```

### Test Case 3: Error Handling
```
1. Create task with invalid parameters
2. Claude picks up task
3. Execution fails
4. Verify task marked as 'failed' with error_log
5. Verify error logged in execution_history
```

---

## Phase 7: OneDrive Integration

**Duration:** 1 hour

### 7.1 OneDrive Folder Structure

Create folders:
```
OneDrive/
├── Reports/
│   ├── LowStock/
│   ├── Sales/
│   ├── Custom/
│   └── Calculations/
└── SOPs/
    ├── inventory/
    │   ├── low_stock_calculation.md
    │   └── reorder_rules.md
    └── reports/
        └── report_templates.md
```

### 7.2 OneDrive Helper Functions

Add to `executor_helpers.py`:

```python
from pathlib import Path
import shutil

def ensure_onedrive_structure(onedrive_base):
    """Ensure OneDrive folder structure exists"""
    folders = [
        'Reports/LowStock',
        'Reports/Sales',
        'Reports/Custom',
        'Reports/Calculations',
        'SOPs/inventory',
        'SOPs/reports'
    ]

    for folder in folders:
        (Path(onedrive_base) / folder).mkdir(parents=True, exist_ok=True)
```

---

## Deployment Checklist

### On Render:
- [ ] Add `claude_tasks` table migration
- [ ] Add `task_execution_history` table migration
- [ ] Deploy updated `unified_app.py` with task endpoints
- [ ] Add Celery task: `claude_executor_trigger.py`
- [ ] Verify Redis connection working
- [ ] Test endpoints with Postman/curl

### On Your Mac:
- [ ] Install dependencies: `pip install requests`
- [ ] Set environment variables in `.env`
- [ ] Create OneDrive folder structure
- [ ] Create SOPs folder with sample files
- [ ] Test `claude_executor.py` locally
- [ ] Set up as background service (screen/tmux/launchd)

### Testing:
- [ ] Create one-time task via Gemini
- [ ] Verify Claude picks it up and executes
- [ ] Create scheduled task
- [ ] Verify Celery triggers it at scheduled time
- [ ] Test error handling
- [ ] Verify OneDrive file creation

---

## Success Criteria

1. **User Request Flow:**
   - User tells Gemini: "I need X report"
   - Task appears in database within 1 second
   - Claude picks it up within 30 seconds
   - Result in OneDrive within execution time

2. **Scheduling Works:**
   - Scheduled tasks trigger at exact time
   - Recurring tasks reset after completion
   - No missed executions

3. **Error Handling:**
   - Failed tasks marked with error details
   - Execution history tracks all attempts
   - User notified of failures

4. **Performance:**
   - No more than 30 second polling delay
   - Database queries < 100ms
   - Full execution time < 5 minutes for typical report

---

## Next Steps After Implementation

1. **Add More Task Types:**
   - Email sending
   - Data exports
   - Analytics generation

2. **Improve Gemini Intent Recognition:**
   - Train on common user patterns
   - Add natural language templates

3. **Add Monitoring:**
   - Task execution dashboard
   - Failure alerts
   - Performance metrics

4. **Add User Features:**
   - Task history view
   - Report preview
   - Schedule management UI

---

## Estimated Total Time

| Phase | Duration |
|-------|----------|
| Phase 1: Database Schema | 30 min |
| Phase 2: Celery Integration | 1 hour |
| Phase 3: API Endpoints | 1.5 hours |
| Phase 4: Claude Executor | 2 hours |
| Phase 5: Gemini Updates | 1 hour |
| Phase 6: Testing | 2 hours |
| Phase 7: OneDrive Setup | 1 hour |
| **Total** | **~9 hours** |

---

**Status:** Ready for implementation
**Last Updated:** 2025-12-29
