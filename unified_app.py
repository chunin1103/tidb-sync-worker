#!/usr/bin/env python3
"""
Unified Flask Application - TiDB MCP + Agent Garden
=====================================================

This unified application hosts:
1. TiDB MCP Server (root level endpoints)
   - GET  /             - Health check
   - POST /mcp          - MCP JSON-RPC endpoint
   - GET  /tools        - List MCP tools
   - POST /query        - Direct query endpoint
   - GET  /status       - Sync status
   - POST /sync         - Trigger manual sync

2. Agent Garden (mounted at /AgentGarden)
   - GET  /AgentGarden/                - Agent Garden UI
   - POST /AgentGarden/execute_agent   - Execute agent with SSE streaming
   - GET  /AgentGarden/sessions        - Get active sessions
   - And all other Agent Garden routes...

3. Claude Task Queue (mounted at /AgentGarden/tasks)
   - POST /AgentGarden/tasks/create         - Create new task
   - GET  /AgentGarden/tasks/ready          - Get tasks ready for execution
   - POST /AgentGarden/tasks/<id>/start     - Mark task as in progress
   - POST /AgentGarden/tasks/<id>/complete  - Mark task as completed
   - POST /AgentGarden/tasks/<id>/fail      - Mark task as failed
   - GET  /AgentGarden/tasks/<id>           - Get task details
   - GET  /AgentGarden/tasks/list           - List all tasks

4. Wiki Viewer (mounted at /wiki)
   - GET  /wiki/              - Workflow overview
   - GET  /wiki/browse        - File browser
   - GET  /wiki/view/<path>   - Markdown viewer with Mermaid diagrams

Environment Variables:
- PORT: Server port (default: 8080)
- TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASSWORD, TIDB_DATABASE
- IDRIVE_ACCESS_KEY, IDRIVE_SECRET_KEY, IDRIVE_ENDPOINT, IDRIVE_BUCKET
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

# Load environment variables from agent_garden/.env
load_dotenv(Path(__file__).parent / 'agent_garden' / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# INITIALIZE MAIN FLASK APP
# =============================================================================

app = Flask(__name__)
app.url_map.strict_slashes = False  # Allow both /path and /path/ to work
logger.info("🚀 Initializing Unified Flask App...")

# =============================================================================
# IMPORT AND REGISTER TiDB MCP ROUTES (Root Level)
# =============================================================================

try:
    # Import MCP server routes
    from mcp_server import app as mcp_app

    # Copy MCP routes to main app
    for rule in mcp_app.url_map.iter_rules():
        # Get the view function for this rule
        view_func = mcp_app.view_functions[rule.endpoint]

        # Register the route in the main app
        # Skip static routes and root route (we have our own home page)
        if rule.endpoint != 'static' and rule.rule != '/':
            app.add_url_rule(
                rule.rule,
                endpoint=f"mcp_{rule.endpoint}",
                view_func=view_func,
                methods=rule.methods
            )

    logger.info("✅ TiDB MCP Server routes registered (root level)")
    logger.info("   - GET  /         - Health check")
    logger.info("   - POST /mcp      - MCP endpoint")
    logger.info("   - GET  /tools    - List tools")
    logger.info("   - POST /query    - Direct query")

except Exception as e:
    logger.error(f"❌ Failed to import TiDB MCP routes: {e}")
    logger.info("⚠️  MCP endpoints will not be available")

# =============================================================================
# IMPORT AND REGISTER SYNC WORKER ROUTES (Root Level)
# =============================================================================

try:
    # Import sync worker if it exists
    import sync_worker

    # Check if sync_worker has Flask routes
    if hasattr(sync_worker, 'app'):
        sync_app = sync_worker.app

        for rule in sync_app.url_map.iter_rules():
            view_func = sync_app.view_functions[rule.endpoint]

            # Only register routes that don't conflict with MCP
            if rule.endpoint != 'static' and not rule.rule.startswith('/mcp') and rule.rule not in ['/', '/tools', '/query']:
                app.add_url_rule(
                    rule.rule,
                    endpoint=f"sync_{rule.endpoint}",
                    view_func=view_func,
                    methods=rule.methods
                )

        logger.info("✅ Sync Worker routes registered (root level)")
        logger.info("   - GET  /status   - Sync status")
        logger.info("   - POST /sync     - Manual sync")

except ImportError:
    logger.info("ℹ️  Sync worker not available (optional)")
except Exception as e:
    logger.error(f"⚠️  Error importing sync worker: {e}")

# =============================================================================
# IMPORT AND REGISTER AGENT GARDEN (Mounted at /AgentGarden)
# =============================================================================

try:
    # Add agent_garden to Python path
    agent_garden_path = os.path.join(os.path.dirname(__file__), 'agent_garden')
    sys.path.insert(0, agent_garden_path)

    # Import Agent Garden app
    from src.core.app import app as garden_app
    from flask import Blueprint

    # Create a blueprint from Agent Garden routes
    garden_blueprint = Blueprint(
        'agent_garden',
        __name__,
        url_prefix='/AgentGarden',
        template_folder=os.path.join(agent_garden_path, 'templates'),
        static_folder=os.path.join(agent_garden_path, 'static') if os.path.exists(os.path.join(agent_garden_path, 'static')) else None,
        static_url_path='/static'  # Relative to blueprint prefix = /AgentGarden/static
    )

    # Copy all routes from garden_app to the blueprint
    for rule in garden_app.url_map.iter_rules():
        view_func = garden_app.view_functions[rule.endpoint]

        # Skip static routes
        if rule.endpoint != 'static':
            # Remove the leading '/' from the rule since blueprint already has url_prefix
            route = rule.rule if rule.rule == '/' else rule.rule

            garden_blueprint.add_url_rule(
                route,
                endpoint=rule.endpoint,
                view_func=view_func,
                methods=rule.methods
            )

    # Register the blueprint
    app.register_blueprint(garden_blueprint)

    logger.info("✅ Agent Garden registered at /AgentGarden")
    logger.info("   - GET  /AgentGarden/              - Agent Garden UI")
    logger.info("   - POST /AgentGarden/execute_agent - Execute agent")
    logger.info("   - GET  /AgentGarden/sessions      - Get sessions")
    logger.info("   - And 30+ more Agent Garden routes...")

except Exception as e:
    logger.error(f"❌ Failed to import Agent Garden: {e}")
    logger.info("⚠️  Agent Garden will not be available")
    import traceback
    traceback.print_exc()

# =============================================================================
# IMPORT AND REGISTER WIKI VIEWER (Mounted at /wiki)
# =============================================================================

try:
    # Import wiki viewer blueprint
    from wiki_viewer import wiki_bp

    # Register blueprint
    app.register_blueprint(wiki_bp)

    logger.info("✅ Wiki Viewer registered at /wiki")
    logger.info("   - GET  /wiki/              - Workflow overview")
    logger.info("   - GET  /wiki/browse        - File browser")
    logger.info("   - GET  /wiki/view/<path>   - Markdown viewer")
    logger.info("   - GET  /wiki/admin         - Admin mode guide")
    logger.info("   - POST /wiki/api/mappings  - Create mappings (API)")

except Exception as e:
    logger.error(f"❌ Failed to import Wiki Viewer: {e}")
    logger.info("⚠️  Wiki Viewer will not be available")
    import traceback
    traceback.print_exc()

# =============================================================================
# IMPORT AND REGISTER REPORTS VIEWER (Mounted at /reports)
# =============================================================================

try:
    # Import reports viewer blueprint
    from reports_viewer import reports_bp

    # Register blueprint
    app.register_blueprint(reports_bp)

    logger.info("✅ Reports Viewer registered at /reports")
    logger.info("   - GET  /reports/reorder-calculator           - Upload CSV")
    logger.info("   - POST /reports/reorder-calculator/upload    - Process CSV")
    logger.info("   - GET  /reports/reorder-calculator/questions - Clarification questions")
    logger.info("   - GET  /reports/reorder-calculator/download  - Download results")

except Exception as e:
    logger.error(f"❌ Failed to import Reports Viewer: {e}")
    logger.info("⚠️  Reports Viewer will not be available")
    import traceback
    traceback.print_exc()

# =============================================================================
# IMPORT AND REGISTER DECISION VALIDATION (Mounted at /decision-validation)
# =============================================================================

try:
    # Import decision validation blueprint
    from decision_validation import decision_validation_bp

    # Register blueprint
    app.register_blueprint(decision_validation_bp)

    logger.info("✅ Decision Validation registered at /decision-validation")
    logger.info("   - GET  /decision-validation/                     - Dashboard")
    logger.info("   - GET  /decision-validation/workflow/<path>      - Workflow detail")
    logger.info("   - GET  /decision-validation/clarifications       - Clarification questions")
    logger.info("   - GET  /decision-validation/clarification/<id>   - Answer question")
    logger.info("   - POST /decision-validation/api/submit           - Submit clarification")

except Exception as e:
    logger.error(f"❌ Failed to import Decision Validation: {e}")
    logger.info("⚠️  Decision Validation will not be available")
    import traceback
    traceback.print_exc()

# =============================================================================
# CLAUDE TASK QUEUE ENDPOINTS (Mounted at /AgentGarden/tasks)
# =============================================================================

@app.route('/AgentGarden/tasks/create', methods=['POST'])
def create_claude_task_endpoint():
    """
    Create a new Claude task
    Called by Gemini when user requests a task

    Scheduling is handled by database polling:
    - Immediate tasks: status='ready', picked up by executor on next poll
    - Scheduled tasks: next_run_time calculated from schedule_cron, picked up when due
    """
    try:
        from flask import request
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import create_claude_task

        data = request.json

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        # Create task in database (scheduling handled by database_claude_tasks)
        task_id = create_claude_task(
            db,
            task_type=data['task_type'],
            task_json=data['task_json'],
            schedule_cron=data.get('schedule_cron'),
            created_by=data.get('created_by', 'gemini'),
            output_format=data.get('output_format', 'md')
        )

        if not task_id:
            db.close()
            return jsonify({'success': False, 'error': 'Failed to create task'}), 500

        # Check if this is a scheduled task
        scheduled = bool(data.get('schedule_cron'))
        if scheduled:
            logger.info(f"📅 Created scheduled Claude task {task_id}: {data['schedule_cron']}")
        else:
            logger.info(f"📋 Created immediate Claude task {task_id}")

        db.close()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Task created successfully',
            'scheduled': scheduled
        })

    except Exception as e:
        logger.error(f"Error creating Claude task: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/ready', methods=['GET'])
def get_ready_claude_tasks():
    """
    Get tasks ready for Claude executor to process
    Claude executor polls this endpoint
    """
    try:
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import get_ready_tasks

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        tasks = get_ready_tasks(db)
        db.close()

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error getting ready tasks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/<int:task_id>/start', methods=['POST'])
def start_claude_task_endpoint(task_id):
    """
    Mark task as in_progress
    Called by Claude executor when starting execution
    """
    try:
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import start_claude_task

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        success = start_claude_task(db, task_id)
        db.close()

        if success:
            logger.info(f"📋 Claude started task {task_id}")
            return jsonify({'success': True, 'message': 'Task started'})
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404

    except Exception as e:
        logger.error(f"Error starting task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/<int:task_id>/complete', methods=['POST'])
def complete_claude_task_endpoint(task_id):
    """
    Mark task as completed
    Called by Claude executor when task finishes successfully
    """
    try:
        from flask import request
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import complete_claude_task

        data = request.json or {}

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        success = complete_claude_task(
            db,
            task_id,
            result_path=data.get('result_path'),
            result_summary=data.get('result_summary'),
            tool_usage=data.get('tool_usage')
        )
        db.close()

        if success:
            tools = data.get('tool_usage', '')
            tools_str = f" (tools: {tools})" if tools else ""
            logger.info(f"✅ Claude completed task {task_id}: {data.get('result_summary', 'No summary')}{tools_str}")
            return jsonify({'success': True, 'message': 'Task completed'})
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404

    except Exception as e:
        logger.error(f"Error completing task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/<int:task_id>/fail', methods=['POST'])
def fail_claude_task_endpoint(task_id):
    """
    Mark task as failed
    Called by Claude executor when task fails
    """
    try:
        from flask import request
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import fail_claude_task

        data = request.json or {}

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        success = fail_claude_task(
            db,
            task_id,
            error_log=data.get('error_log', 'Unknown error')
        )
        db.close()

        if success:
            logger.error(f"❌ Claude task {task_id} failed: {data.get('error_log', 'Unknown')}")
            return jsonify({'success': True, 'message': 'Task marked as failed'})
        else:
            return jsonify({'success': False, 'error': 'Task not found'}), 404

    except Exception as e:
        logger.error(f"Error failing task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/<int:task_id>', methods=['GET'])
def get_claude_task_details(task_id):
    """
    Get detailed information about a specific task
    """
    try:
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import get_claude_task, get_task_execution_history

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        task = get_claude_task(db, task_id)

        if not task:
            db.close()
            return jsonify({'success': False, 'error': 'Task not found'}), 404

        # Get execution history
        history = get_task_execution_history(db, task_id, limit=10)
        db.close()

        return jsonify({
            'success': True,
            'task': task,
            'execution_history': history
        })

    except Exception as e:
        logger.error(f"Error getting task {task_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/migrate', methods=['POST'])
def run_migration():
    """
    Run database migrations to add missing columns
    This is needed when new columns are added to SQLAlchemy models
    """
    try:
        from agent_garden.src.core.database import get_db, engine
        from sqlalchemy import text

        migrations = []

        # Check and add tool_usage column if missing
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'claude_tasks' AND column_name = 'tool_usage'
            """))
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("ALTER TABLE claude_tasks ADD COLUMN tool_usage TEXT"))
                conn.commit()
                migrations.append("Added 'tool_usage' column to claude_tasks table")
                logger.info("✅ Migration: Added tool_usage column to claude_tasks")
            else:
                migrations.append("Column 'tool_usage' already exists")

        return jsonify({
            'success': True,
            'message': 'Migration completed',
            'migrations': migrations
        })

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/tasks/list', methods=['GET'])
def list_claude_tasks():
    """
    List all tasks with optional filtering
    Query params: status, task_type, limit
    """
    try:
        from flask import request
        from agent_garden.src.core.database import get_db
        from agent_garden.src.core.database_claude_tasks import get_all_claude_tasks

        status = request.args.get('status')
        task_type = request.args.get('task_type')
        limit = request.args.get('limit', 100, type=int)

        db = get_db()
        if not db:
            return jsonify({'success': False, 'error': 'Database not available'}), 500

        tasks = get_all_claude_tasks(db, status=status, task_type=task_type, limit=limit)
        db.close()

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# AGENT GARDEN REPORTS API
# =============================================================================

@app.route('/AgentGarden/api/reports/list', methods=['GET'])
def list_reports():
    """
    List all Claude-generated reports (HYBRID: database + local folder scan)
    Returns: List of report metadata (title, path, size, created_at, agent_type)

    This hybrid approach ensures reports show up even if sync to database failed.
    """
    try:
        from flask import request
        from agent_garden.src.core.database import get_claude_reports
        from pathlib import Path
        from datetime import datetime
        import os

        limit = request.args.get('limit', 50, type=int)
        agent_type_filter = request.args.get('agent_type', None)

        all_reports = []
        seen_paths = set()

        # 1. Get reports from database first (authoritative source)
        try:
            db_reports = get_claude_reports(limit=limit, agent_type=agent_type_filter)
            for r in db_reports:
                all_reports.append(r)
                seen_paths.add(r.get('path', ''))
        except Exception as db_error:
            logger.warning(f"Database query failed, using local scan only: {db_error}")

        # 2. Scan local OneDrive Reports folder (fallback/supplement)
        # This ensures reports show up even if sync to database failed
        local_reports_paths = [
            Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports",
            Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools/reports",
            Path("/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports"),
        ]

        for reports_base in local_reports_paths:
            if reports_base.exists():
                try:
                    for agent_dir in reports_base.iterdir():
                        if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
                            agent_type = agent_dir.name

                            # Apply agent_type filter if specified
                            if agent_type_filter and agent_type != agent_type_filter:
                                continue

                            for report_file in agent_dir.glob('*.md'):
                                relative_path = f"{agent_type}/{report_file.name}"

                                # Skip if already in database results
                                if relative_path in seen_paths:
                                    continue

                                # Get file stats
                                stat = report_file.stat()
                                created_at = datetime.fromtimestamp(stat.st_mtime)

                                all_reports.append({
                                    'id': None,  # Local file, no DB id
                                    'path': relative_path,
                                    'title': report_file.stem,
                                    'agent_type': agent_type,
                                    'size': stat.st_size,
                                    'created_at': created_at.isoformat(),
                                    'summary': f'{agent_type} report (local)',
                                    'content': None,  # Don't load content for list
                                    'source': 'local'  # Mark as local file
                                })
                                seen_paths.add(relative_path)
                except Exception as scan_error:
                    logger.warning(f"Error scanning {reports_base}: {scan_error}")
                break  # Only use first existing path

        # Sort by created_at descending, apply limit
        all_reports.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        all_reports = all_reports[:limit]

        return jsonify({
            'success': True,
            'reports': all_reports,
            'count': len(all_reports)
        })

    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/api/reports/save', methods=['POST'])
def save_report():
    """
    Save a Claude-generated report to database (called by local executor)
    Expects JSON: {agent_type, report_title, report_content, file_path?, task_id?}
    """
    try:
        from flask import request
        from agent_garden.src.core.database import save_claude_report

        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

        # Validate required fields
        required = ['agent_type', 'report_title', 'report_content']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'success': False, 'error': f'Missing fields: {missing}'}), 400

        # Save to database
        report_id = save_claude_report(
            agent_type=data['agent_type'],
            report_title=data['report_title'],
            report_content=data['report_content'],
            file_path=data.get('file_path'),
            task_id=data.get('task_id')
        )

        if report_id:
            return jsonify({
                'success': True,
                'report_id': report_id,
                'message': 'Report saved successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save report'}), 500

    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/AgentGarden/api/reports/view/<path:report_path>', methods=['GET'])
def view_report(report_path):
    """
    View/download a Claude-generated report (HYBRID: database + local file fallback)
    Path format: Reports/{agent_type}/{filename} or {agent_type}/{filename}

    For .md files: Returns markdown content
    For .csv files: Returns CSV content or JSON preview (if ?preview=true)
    For .xlsx/.json: Returns file download
    """
    try:
        from agent_garden.src.core.database import get_db, ClaudeReport
        from pathlib import Path
        from flask import Response, send_file, request
        import csv
        import io

        # Strip "Reports/" prefix if present
        if report_path.startswith('Reports/'):
            report_path = report_path[8:]  # Remove "Reports/"

        # Parse path to extract agent_type and filename
        parts = report_path.rsplit('/', 1)
        if len(parts) != 2:
            return jsonify({'error': 'Invalid report path'}), 400

        agent_type = parts[0]
        filename = parts[1]

        # Get file extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'md'
        report_title = filename.rsplit('.', 1)[0]

        # Check if preview mode requested (for CSV)
        preview_mode = request.args.get('preview', 'false').lower() == 'true'
        preview_rows = int(request.args.get('rows', 25))

        # Find the file locally
        local_reports_paths = [
            Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports",
            Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools/reports",
        ]

        local_file = None
        for reports_base in local_reports_paths:
            candidate = reports_base / agent_type / filename
            if candidate.exists():
                local_file = candidate
                break

        # If not found locally, try database (for .md files)
        if not local_file and ext == 'md':
            db = get_db()
            if db:
                try:
                    # Search by file_path first (most reliable)
                    report = db.query(ClaudeReport).filter(
                        ClaudeReport.file_path.like(f'%{filename}%')
                    ).first()
                    # Fallback: search by agent_type and report_title
                    if not report:
                        report = db.query(ClaudeReport).filter(
                            ClaudeReport.agent_type == agent_type,
                            ClaudeReport.report_title == report_title
                        ).first()
                    if report:
                        return Response(report.report_content, mimetype='text/markdown')
                finally:
                    db.close()

        if not local_file:
            # File not found locally - check if it's a non-md file stored on user's OneDrive
            if ext in ['csv', 'xlsx', 'xls', 'json']:
                # For data files, return info about where to find them
                db = get_db()
                db_report = None
                if db:
                    try:
                        # Search by file_path which contains the filename
                        db_report = db.query(ClaudeReport).filter(
                            ClaudeReport.file_path.like(f'%{filename}%')
                        ).first()
                        # Fallback: search by agent_type
                        if not db_report:
                            db_report = db.query(ClaudeReport).filter(
                                ClaudeReport.agent_type == agent_type
                            ).order_by(ClaudeReport.created_at.desc()).first()
                    finally:
                        db.close()

                return jsonify({
                    'success': False,
                    'error': 'local_file_only',
                    'message': f'This {ext.upper()} file is stored on your local OneDrive and cannot be previewed from the cloud.',
                    'filename': filename,
                    'agent_type': agent_type,
                    'expected_path': f'~/Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports/{agent_type}/{filename}',
                    'summary': db_report.report_content if db_report else None,
                    'hint': 'Run the dashboard locally to preview this file, or access it directly in your OneDrive folder.'
                }), 200  # Return 200 so UI can handle gracefully

            return jsonify({'error': f'Report not found: {agent_type}/{filename}'}), 404

        # Handle different file types
        if ext == 'md':
            content = local_file.read_text(encoding='utf-8')
            return Response(content, mimetype='text/markdown; charset=utf-8')

        elif ext == 'csv':
            if preview_mode:
                # Return JSON preview with first N rows
                rows = []
                headers = []
                with open(local_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    for i, row in enumerate(reader):
                        if i >= preview_rows:
                            break
                        rows.append(row)

                total_rows = sum(1 for _ in open(local_file, 'r', encoding='utf-8')) - 1
                return jsonify({
                    'success': True,
                    'headers': headers,
                    'rows': rows,
                    'preview_count': len(rows),
                    'total_rows': total_rows,
                    'filename': filename,
                    'local_path': str(local_file)
                })
            else:
                # Return CSV file download
                return send_file(
                    local_file,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )

        elif ext in ['xlsx', 'xls']:
            return send_file(
                local_file,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )

        elif ext == 'json':
            if preview_mode:
                import json
                with open(local_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify({
                    'success': True,
                    'data': data,
                    'filename': filename,
                    'local_path': str(local_file)
                })
            else:
                return send_file(
                    local_file,
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=filename
                )

        else:
            # Unknown format - try to send as download
            return send_file(local_file, as_attachment=True, download_name=filename)

    except Exception as e:
        logger.error(f"Error viewing report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/AgentGarden/api/reports/info/<path:report_path>', methods=['GET'])
def report_info(report_path):
    """
    Get metadata about a report file (for showing local path, size, etc.)
    """
    try:
        from pathlib import Path
        import os

        # Strip "Reports/" prefix if present
        if report_path.startswith('Reports/'):
            report_path = report_path[8:]

        parts = report_path.rsplit('/', 1)
        if len(parts) != 2:
            return jsonify({'error': 'Invalid report path'}), 400

        agent_type = parts[0]
        filename = parts[1]

        local_reports_paths = [
            Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports",
        ]

        for reports_base in local_reports_paths:
            local_file = reports_base / agent_type / filename
            if local_file.exists():
                stat = local_file.stat()
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'agent_type': agent_type,
                    'local_path': str(local_file),
                    'folder_path': str(local_file.parent),
                    'size_bytes': stat.st_size,
                    'size_human': f"{stat.st_size / 1024:.1f} KB" if stat.st_size < 1024*1024 else f"{stat.st_size / (1024*1024):.1f} MB",
                    'exists': True
                })

        return jsonify({
            'success': False,
            'error': 'File not found locally',
            'exists': False
        }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# TIMEZONE SETTINGS ROUTES
# =============================================================================

@app.route('/AgentGarden/get_settings', methods=['GET'])
def get_settings():
    """
    Get system settings including timezone configuration.
    """
    try:
        from agent_garden.src.core.database import get_system_settings
        settings = get_system_settings()
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({'error': str(e), 'timezone': 'America/Los_Angeles'}), 500


@app.route('/AgentGarden/get_timezones', methods=['GET'])
def get_timezones():
    """
    Get list of available timezones organized by region.
    """
    try:
        from agent_garden.src.core.database import get_available_timezones
        timezones = get_available_timezones()
        return jsonify(timezones)
    except Exception as e:
        logger.error(f"Error getting timezones: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/AgentGarden/update_timezone', methods=['POST'])
def update_timezone_route():
    """
    Update the system timezone.

    Request Body:
    {
        "timezone": "Asia/Bangkok"
    }
    """
    try:
        from agent_garden.src.core.database import update_timezone, get_available_timezones

        data = request.get_json()
        new_timezone = data.get('timezone')

        if not new_timezone:
            return jsonify({'error': 'Timezone is required'}), 400

        # Validate timezone
        valid_timezones = [tz['value'] for tz in get_available_timezones()]
        if new_timezone not in valid_timezones:
            return jsonify({'error': 'Invalid timezone'}), 400

        # Update timezone in database
        success = update_timezone(new_timezone)

        if success:
            logger.info(f"Timezone updated to: {new_timezone}")
            return jsonify({
                'success': True,
                'message': 'Timezone updated successfully',
                'new_timezone': new_timezone
            })
        else:
            return jsonify({'error': 'Failed to update timezone'}), 500

    except Exception as e:
        logger.error(f"Error updating timezone: {e}")
        return jsonify({'error': str(e)}), 500


# =============================================================================
# FAVICON ROUTE (Prevent 404 errors)
# =============================================================================

@app.route('/favicon.ico')
def favicon():
    """Serve a simple favicon to prevent 404 errors in browser console"""
    from flask import send_file
    from io import BytesIO
    import base64

    # Simple 16x16 transparent PNG (1x1 pixel, transparent)
    favicon_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
    )
    return send_file(BytesIO(favicon_data), mimetype='image/x-icon')


# =============================================================================
# ROOT ENDPOINT (Home Page + Health Check)
# =============================================================================

@app.route('/')
def home():
    """Home page with navigation dashboard.
    Returns JSON health check if ?format=json or Accept: application/json
    """
    # Check if JSON response is requested
    wants_json = (
        request.args.get('format') == 'json' or
        request.accept_mimetypes.best == 'application/json'
    )

    if wants_json:
        return health_check_json()

    # Return HTML home page
    return render_template('home.html')


@app.route('/health')
def health_check_json():
    """JSON health check endpoint."""
    services = {
        'tidb_mcp': False,
        'agent_garden': False,
        'sync_worker': False,
        'wiki_viewer': False
    }

    # Check if MCP is available
    try:
        from mcp_server import get_connection
        get_connection()
        services['tidb_mcp'] = True
    except:
        pass

    # Check if Agent Garden is available
    try:
        from src.core.app import app as garden_app
        services['agent_garden'] = True
    except:
        pass

    # Check if Sync Worker is available
    try:
        import sync_worker
        services['sync_worker'] = hasattr(sync_worker, 'app')
    except:
        pass

    # Check if Wiki Viewer is available
    try:
        from wiki_viewer import wiki_bp
        services['wiki_viewer'] = True
    except:
        pass

    return jsonify({
        'status': 'healthy',
        'service': 'unified-tidb-agent-garden',
        'services': services,
        'endpoints': {
            'home': '/',
            'health': '/health',
            'tidb_mcp': {
                'mcp': '/mcp',
                'tools': '/tools',
                'query': '/query'
            },
            'agent_garden': {
                'ui': '/AgentGarden/',
                'execute': '/AgentGarden/execute_agent',
                'sessions': '/AgentGarden/sessions'
            },
            'claude_task_queue': {
                'create': '/AgentGarden/tasks/create',
                'ready': '/AgentGarden/tasks/ready',
                'start': '/AgentGarden/tasks/<id>/start',
                'complete': '/AgentGarden/tasks/<id>/complete',
                'fail': '/AgentGarden/tasks/<id>/fail',
                'details': '/AgentGarden/tasks/<id>',
                'list': '/AgentGarden/tasks/list'
            },
            'sync_worker': {
                'status': '/status',
                'sync': '/sync'
            },
            'wiki_viewer': {
                'overview': '/wiki/',
                'browse': '/wiki/browse',
                'view': '/wiki/view/<path>',
                'admin': '/wiki/admin',
                'api_mappings': '/wiki/api/mappings/<path>'
            },
            'reorder_calculator': {
                'upload': '/reports/reorder-calculator',
                'questions': '/reports/reorder-calculator/questions'
            }
        }
    })

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    # Validate TiDB environment
    required_vars = ['TIDB_USER', 'TIDB_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]

    if missing:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing)}")
        logger.info("   Set TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASSWORD, TIDB_DATABASE")
        logger.info("   Some features may not be available")

    # Get port from environment
    port = int(os.environ.get('PORT', 8080))

    logger.info("")
    logger.info("=" * 80)
    logger.info("🎯 UNIFIED FLASK APPLICATION STARTED")
    logger.info("=" * 80)
    logger.info(f"🌐 Server URL: http://0.0.0.0:{port}")
    logger.info(f"🔧 TiDB MCP Endpoint: http://localhost:{port}/mcp")
    logger.info(f"🤖 Agent Garden UI: http://localhost:{port}/AgentGarden/")
    logger.info(f"📊 Health Check: http://localhost:{port}/")
    logger.info("=" * 80)
    logger.info("")

    # Run the unified Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
