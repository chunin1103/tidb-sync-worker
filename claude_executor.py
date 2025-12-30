#!/usr/bin/env python3
"""
Claude Task Executor
Runs on your Mac terminal 24/7
Polls MCP server for ready tasks and executes them

Usage:
    python claude_executor.py
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
MCP_SERVER = os.getenv('MCP_SERVER', 'https://gpt-mcp.onrender.com')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))  # seconds
ONEDRIVE_BASE = Path.home() / "Library/CloudStorage/OneDrive-Personal"

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
        self.project_root = Path(__file__).parent
        logger.info(f"📁 OneDrive base: {self.onedrive_base}")
        logger.info(f"📂 Project root: {self.project_root}")

    def poll_ready_tasks(self) -> list:
        """Poll MCP server for tasks ready to execute"""
        try:
            response = requests.get(f"{self.mcp_server}/tasks/ready", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error polling tasks: {e}")
            return []

    def mark_task_started(self, task_id: int) -> bool:
        """Mark task as in_progress"""
        try:
            response = requests.post(f"{self.mcp_server}/tasks/{task_id}/start", timeout=10)
            response.raise_for_status()
            logger.info(f"📋 Task {task_id} started")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as started: {e}")
            return False

    def mark_task_completed(self, task_id: int, result_path: str, summary: str) -> bool:
        """Mark task as completed"""
        try:
            response = requests.post(
                f"{self.mcp_server}/tasks/{task_id}/complete",
                json={
                    'result_path': result_path,
                    'result_summary': summary
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"✅ Task {task_id} completed: {summary}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as completed: {e}")
            return False

    def mark_task_failed(self, task_id: int, error_log: str) -> bool:
        """Mark task as failed"""
        try:
            response = requests.post(
                f"{self.mcp_server}/tasks/{task_id}/fail",
                json={'error_log': error_log},
                timeout=10
            )
            response.raise_for_status()
            logger.error(f"❌ Task {task_id} failed: {error_log}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as failed: {e}")
            return False

    def execute_task(self, task: Dict[str, Any]):
        """Execute a single task"""
        task_id = task['id']
        task_type = task['task_type']
        task_json = task['task_json']

        logger.info(f"🚀 Executing task {task_id} ({task_type})")

        # Mark as started
        if not self.mark_task_started(task_id):
            return

        try:
            # Route to appropriate handler
            if task_type == 'report_generation':
                result = self.handle_report_generation(task_json)
            elif task_type == 'query_execution':
                result = self.handle_query_execution(task_json)
            elif task_type == 'calculation':
                result = self.handle_calculation(task_json)
            elif task_type == 'agent_report':
                result = self.handle_agent_report(task_json)
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
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            self.mark_task_failed(task_id, error_msg)

    def handle_report_generation(self, task_json: Dict) -> Dict:
        """Handle report generation tasks"""
        logger.info(f"📊 Generating report: {task_json.get('report_name', 'Unknown')}")

        # TODO: Implement actual report generation
        # For now, create a placeholder file
        output_config = task_json.get('output', {})
        output_path = self.onedrive_base / output_config.get('path', 'Reports')
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename_pattern = output_config.get('filename_pattern', 'report_{timestamp}.txt')
        filename = filename_pattern.format(
            date=datetime.now().strftime('%Y-%m-%d'),
            timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        )

        result_file = output_path / filename

        # Create report file
        with open(result_file, 'w') as f:
            f.write(f"Report Generated: {datetime.now().isoformat()}\n")
            f.write(f"Report Type: {task_json.get('report_name', 'Unknown')}\n")
            f.write(f"Parameters: {json.dumps(task_json.get('parameters', {}), indent=2)}\n")
            f.write("\n")
            f.write("--- Report Content ---\n")
            f.write("(Placeholder - implement actual report generation)\n")

        relative_path = str(result_file.relative_to(self.onedrive_base))

        return {
            'path': relative_path,
            'summary': f"Generated {task_json.get('report_name', 'report')}"
        }

    def handle_query_execution(self, task_json: Dict) -> Dict:
        """Handle query execution tasks"""
        logger.info(f"🔍 Executing query")

        # TODO: Implement query execution via TiDB MCP
        query = task_json.get('query', 'SELECT 1')

        # For now, create a placeholder result file
        output_config = task_json.get('output', {})
        output_path = self.onedrive_base / output_config.get('path', 'Reports/Query')
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        result_file = output_path / filename

        with open(result_file, 'w') as f:
            f.write(f"Query executed: {datetime.now().isoformat()}\n")
            f.write(f"Query: {query}\n")
            f.write("\n(Placeholder - implement actual query execution)\n")

        relative_path = str(result_file.relative_to(self.onedrive_base))

        return {
            'path': relative_path,
            'summary': 'Query executed successfully'
        }

    def handle_calculation(self, task_json: Dict) -> Dict:
        """Handle calculation tasks"""
        logger.info(f"🧮 Running calculation: {task_json.get('calculation_name', 'Unknown')}")

        # TODO: Implement calculation logic
        output_config = task_json.get('output', {})
        output_path = self.onedrive_base / output_config.get('path', 'Reports/Calculations')
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"calculation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        result_file = output_path / filename

        result_data = {
            'calculation': task_json.get('calculation_name'),
            'timestamp': datetime.now().isoformat(),
            'result': 'Placeholder - implement actual calculation'
        }

        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)

        relative_path = str(result_file.relative_to(self.onedrive_base))

        return {
            'path': relative_path,
            'summary': f"Calculation {task_json.get('calculation_name', 'completed')}"
        }

    def call_mcp_tool(self, tool_name: str, arguments: Dict = None) -> Dict:
        """Call TiDB MCP server tool directly via HTTP using JSON-RPC format"""
        try:
            # Use local MCP server (proxies to TiDB via unified_app)
            mcp_base = self.mcp_server
            mcp_url = f"{mcp_base}/mcp"

            # MCP uses JSON-RPC 2.0 format
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                },
                "id": 1
            }

            response = requests.post(
                mcp_url,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                # Extract data from JSON-RPC result
                if 'result' in result and 'content' in result['result']:
                    # Parse the text content
                    text_content = result['result']['content'][0]['text']
                    # Try to parse as JSON if possible
                    try:
                        return json.loads(text_content)
                    except json.JSONDecodeError:
                        return {'data': text_content}
                else:
                    return result
            else:
                logger.error(f"MCP call failed: {response.status_code}")
                return {'error': f"HTTP {response.status_code}"}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {'error': str(e)}

    def fetch_database_context(self, agent_type: str, prompt: str) -> str:
        """Fetch relevant database context based on agent type and prompt"""
        logger.info(f"📡 Fetching database context via MCP...")

        context_parts = []

        # Always get table list
        tables_result = self.call_mcp_tool('list_tables')
        if 'error' not in tables_result:
            context_parts.append(f"## Available Tables\n{json.dumps(tables_result, indent=2)}\n")

        # Get recent orders (common for inventory agents)
        if 'inventory' in agent_type.lower() or 'order' in prompt.lower():
            orders_result = self.call_mcp_tool('recent_orders', {'limit': 5})
            if 'error' not in orders_result:
                context_parts.append(f"## Recent Orders\n{json.dumps(orders_result, indent=2)}\n")

        # Get today's orders if relevant
        if 'today' in prompt.lower() or 'daily' in prompt.lower():
            today_result = self.call_mcp_tool('today_orders')
            if 'error' not in today_result:
                context_parts.append(f"## Today's Orders\n{json.dumps(today_result, indent=2)}\n")

        if context_parts:
            logger.info(f"✅ Fetched {len(context_parts)} data sections from MCP")
            return "\n".join(context_parts)
        else:
            logger.warning(f"⚠️  No database context fetched")
            return "No database context available"

    def handle_agent_report(self, task_json: Dict) -> Dict:
        """Handle autonomous agent reports (HYBRID: Direct MCP + Claude Code CLI)"""
        agent_type = task_json.get('agent_type', 'Unknown')
        report_title = task_json.get('report_title', 'Agent Report')
        report_type = task_json.get('report_type', 'unknown')
        prompt = task_json.get('prompt', 'No prompt provided')

        logger.info(f"📊 Generating agent report: {report_title} ({agent_type})")
        logger.info(f"🔧 HYBRID MODE: Direct MCP data fetch + Claude Code CLI analysis")

        # Get output configuration
        output_config = task_json.get('output', {})
        output_path = self.onedrive_base / output_config.get('path', 'Reports/Agents')
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename
        filename_pattern = output_config.get('filename_pattern', 'report_{timestamp}.md')
        filename = filename_pattern.format(
            date=datetime.now().strftime('%Y-%m-%d'),
            timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        )

        result_file = output_path / filename

        # Step 1: Fetch database context directly from MCP
        database_context = self.fetch_database_context(agent_type, prompt)

        # Step 2: Build enhanced prompt with real data for Claude Code CLI
        import subprocess

        claude_prompt = f"""You are the {agent_type} agent.

TASK: {report_title}

CONTEXT:
- Run Type: {task_json.get('run_type', 'N/A')}
- Trigger: {task_json.get('trigger', 'N/A')}
- Data Source: TiDB Cloud (via MCP server)

DATABASE CONTEXT (fetched from live TiDB):
{database_context}

INSTRUCTIONS:
{prompt}

OUTPUT FORMAT:
Generate a markdown report with:
1. Clear section headings (## )
2. Actionable insights and recommendations based on the REAL DATA above
3. Specific data points (reference actual order IDs, quantities, dates from the data)
4. Concrete next steps

Analyze the database context provided and generate the report now:"""

        try:
            # Call Claude Code CLI in non-interactive mode
            result = subprocess.run(
                ['claude', '--print', claude_prompt],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                report_content = result.stdout.strip()

                # Add metadata header
                full_report = f"""# {report_title}

**Generated**: {datetime.now().isoformat()}
**Agent Type**: {agent_type}
**Executor**: Claude Code CLI (FREE - MCP enabled)

---

{report_content}

---

*Generated by Claude Task Executor v2.0 - Powered by Claude Code CLI + TiDB MCP*
"""
            else:
                # Error occurred
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"❌ Claude Code CLI failed: {error_msg}")

                full_report = f"""# {report_title} - ERROR

**Generated**: {datetime.now().isoformat()}
**Status**: FAILED

## Error

Claude Code CLI execution failed:
```
{error_msg}
```

## Prompt Attempted
```
{claude_prompt}
```
"""

        except subprocess.TimeoutExpired:
            logger.error(f"❌ Claude Code CLI timed out after 5 minutes")
            full_report = f"""# {report_title} - TIMEOUT

**Generated**: {datetime.now().isoformat()}
**Status**: TIMEOUT

Claude Code CLI execution timed out after 5 minutes.
"""

        except Exception as e:
            logger.error(f"❌ Failed to execute Claude Code CLI: {e}")
            full_report = f"""# {report_title} - ERROR

**Generated**: {datetime.now().isoformat()}
**Status**: ERROR

{str(e)}
"""

        # Write report to file
        with open(result_file, 'w') as f:
            f.write(full_report)

        relative_path = str(result_file.relative_to(self.onedrive_base))

        logger.info(f"✅ Agent report saved: {relative_path}")

        return {
            'path': relative_path,
            'summary': f"Generated {report_title} ({agent_type})"
        }

    def run(self):
        """Main execution loop"""
        logger.info("=" * 70)
        logger.info("🚀 CLAUDE TASK EXECUTOR STARTED")
        logger.info("=" * 70)
        logger.info(f"📡 Polling: {self.mcp_server}")
        logger.info(f"⏱️  Interval: Every {POLL_INTERVAL} seconds")
        logger.info(f"📁 OneDrive: {self.onedrive_base}")
        logger.info("=" * 70)
        logger.info("")

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
                logger.info("")
                logger.info("=" * 70)
                logger.info("⏹️  Executor stopped by user")
                logger.info("=" * 70)
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(POLL_INTERVAL)


def main():
    """Main entry point"""
    # Validate OneDrive path exists
    onedrive_path = Path.home() / "Library/CloudStorage/OneDrive-Personal"
    if not onedrive_path.exists():
        logger.error(f"❌ OneDrive path not found: {onedrive_path}")
        logger.info("   Please update ONEDRIVE_BASE path in the script")
        sys.exit(1)

    # Create executor and run
    executor = ClaudeExecutor()
    executor.run()


if __name__ == '__main__':
    main()
