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

# Cross-platform OneDrive path detection
def get_onedrive_path():
    """Detect OneDrive path on Windows or Mac with robust fallbacks"""

    # 1. Check for explicit override via environment variable
    if os.getenv('CLAUDE_TOOLS_PATH'):
        return Path(os.getenv('CLAUDE_TOOLS_PATH'))

    # 2. On Windows, check the OneDrive environment variable (set by OneDrive app)
    if sys.platform == 'win32':
        # Windows sets these env vars automatically
        onedrive_env = os.getenv('OneDrive') or os.getenv('OneDriveConsumer') or os.getenv('OneDriveCommercial')
        if onedrive_env:
            return Path(onedrive_env) / "Claude Tools"

        # Fallback: check common Windows OneDrive locations
        possible_paths = [
            Path.home() / "OneDrive" / "Claude Tools",
            Path.home() / "OneDrive - Personal" / "Claude Tools",
        ]
        for path in possible_paths:
            if path.exists():
                return path
        # Default if nothing found
        return Path.home() / "OneDrive" / "Claude Tools"

    else:
        # Mac: check CloudStorage folder for OneDrive variants
        cloud_storage = Path.home() / "Library/CloudStorage"
        if cloud_storage.exists():
            for folder in cloud_storage.iterdir():
                if folder.name.startswith("OneDrive"):
                    claude_tools = folder / "Claude Tools"
                    if claude_tools.exists():
                        return claude_tools
        # Default Mac path
        return Path.home() / "Library/CloudStorage/OneDrive-Personal/Claude Tools"

ONEDRIVE_BASE = get_onedrive_path()

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
        logger.info(f"[DIR] OneDrive base: {self.onedrive_base}")
        logger.info(f"[FOLDER] Project root: {self.project_root}")

    def poll_ready_tasks(self) -> list:
        """Poll MCP server for tasks ready to execute"""
        try:
            response = requests.get(f"{self.mcp_server}/AgentGarden/tasks/ready", timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Error polling tasks: {e}")
            return []

    def mark_task_started(self, task_id: int) -> bool:
        """Mark task as in_progress"""
        try:
            response = requests.post(f"{self.mcp_server}/AgentGarden/tasks/{task_id}/start", timeout=10)
            response.raise_for_status()
            logger.info(f"[TASK] Task {task_id} started")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as started: {e}")
            return False

    def mark_task_completed(self, task_id: int, result_path: str, summary: str, tool_usage: list = None) -> bool:
        """Mark task as completed"""
        try:
            payload = {
                'result_path': result_path,
                'result_summary': summary
            }
            if tool_usage:
                payload['tool_usage'] = json.dumps(tool_usage)

            response = requests.post(
                f"{self.mcp_server}/AgentGarden/tasks/{task_id}/complete",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            tools_str = f" (tools: {', '.join(tool_usage)})" if tool_usage else ""
            logger.info(f"[OK] Task {task_id} completed: {summary}{tools_str}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as completed: {e}")
            return False

    def mark_task_failed(self, task_id: int, error_log: str) -> bool:
        """Mark task as failed"""
        try:
            response = requests.post(
                f"{self.mcp_server}/AgentGarden/tasks/{task_id}/fail",
                json={'error_log': error_log},
                timeout=10
            )
            response.raise_for_status()
            logger.error(f"[ERROR] Task {task_id} failed: {error_log}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marking task {task_id} as failed: {e}")
            return False

    def sync_report_to_server(self, agent_type: str, report_title: str,
                               report_content: str, file_path: str, task_id: int = None) -> bool:
        """Sync a generated report to the Render server database"""
        try:
            payload = {
                'agent_type': agent_type,
                'report_title': report_title,
                'report_content': report_content,
                'file_path': file_path
            }
            if task_id:
                payload['task_id'] = task_id

            response = requests.post(
                f"{self.mcp_server}/AgentGarden/api/reports/save",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if result.get('success'):
                report_id = result.get('report_id')
                logger.info(f"[CLOUD]  Report synced to server (ID: {report_id})")
                return True
            else:
                logger.warning(f"[WARN]  Server returned error: {result.get('error')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.warning(f"[WARN]  Failed to sync report to server: {e}")
            return False

    def execute_task(self, task: Dict[str, Any]):
        """Execute a single task"""
        task_id = task['id']
        task_type = task['task_type']
        task_json = task['task_json']
        output_format = task.get('output_format', 'md')

        logger.info(f"[START] Executing task {task_id} ({task_type}) - Format: {output_format}")

        # Mark as started
        if not self.mark_task_started(task_id):
            return

        try:
            # Route to appropriate handler
            # Dashboard agent types all use handle_agent_report
            agent_types = [
                'agent_report',
                'inventory_intelligence',
                'sales_analysis',
                'customer_insights',
                'product_performance',
                'general_report'
            ]

            if task_type == 'report_generation':
                result = self.handle_report_generation(task_json, output_format)
            elif task_type == 'query_execution':
                result = self.handle_query_execution(task_json, output_format)
            elif task_type == 'calculation':
                result = self.handle_calculation(task_json, output_format)
            elif task_type in agent_types:
                result = self.handle_agent_report(task_json, output_format, task_id)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Mark as completed
            self.mark_task_completed(
                task_id,
                result['path'],
                result['summary'],
                result.get('tool_usage', [])
            )

        except Exception as e:
            # Mark as failed
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}\n\n{traceback.format_exc()}"
            self.mark_task_failed(task_id, error_msg)

    def handle_report_generation(self, task_json: Dict) -> Dict:
        """Handle report generation tasks"""
        logger.info(f"[REPORT] Generating report: {task_json.get('report_name', 'Unknown')}")

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
        logger.info(f"[SEARCH] Executing query")

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
        logger.info(f"[CALC] Running calculation: {task_json.get('calculation_name', 'Unknown')}")

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
        logger.info(f"[POLL] Fetching database context via MCP...")

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
            logger.info(f"[OK] Fetched {len(context_parts)} data sections from MCP")
            return "\n".join(context_parts)
        else:
            logger.warning(f"[WARN]  No database context fetched")
            return "No database context available"

    def _get_format_instructions(self, output_format: str, result_file: Path) -> str:
        """Get format-specific instructions for Claude Code CLI"""

        filename = result_file.name  # Get just the filename, not full path

        if output_format == 'csv':
            return """Generate a CSV file with:
1. Header row with clear column names
2. Data rows with comma-separated values
3. Properly escaped fields (wrap in quotes if contains commas)
4. No markdown formatting - pure CSV data only

Use Python's csv module or write directly:
```python
import csv
with open('{filename}', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Column1', 'Column2', 'Column3'])
    writer.writerow(['value1', 'value2', 'value3'])
```""".format(filename=filename)

        elif output_format == 'xlsx':
            return """Generate an Excel (XLSX) file with:
1. Sheet with clear headers in Row 1 (bold if possible)
2. Data rows starting from Row 2
3. Formatted cells (numbers as numbers, dates as dates)
4. Optional: Multiple sheets for different data categories
5. Optional: Summary sheet with key insights

METHOD: Create a Python script and execute it immediately

Step 1: Use Write tool to create a temp Python script (e.g. create_excel.py)
Step 2: Use Bash tool to run: python create_excel.py
Step 3: Use Bash tool to verify file was created: ls -lh {filename}

Example Python script content:
```python
from openpyxl import Workbook
from openpyxl.styles import Font

wb = Workbook()
ws = wb.active
ws.title = "Report Data"

# Headers
ws.append(['Column1', 'Column2', 'Column3'])
ws['A1'].font = Font(bold=True)

# Data
ws.append(['value1', 'value2', 'value3'])

wb.save('{filename}')
print("Excel file created: {filename}")
```

CRITICAL: You MUST run the Python script after creating it, don't just write the script!""".format(filename=filename)

        elif output_format == 'json':
            return """Generate a JSON file with:
1. Well-structured JSON object or array
2. Clear property names
3. Proper data types (strings, numbers, booleans, arrays, objects)
4. Pretty-printed with indentation for readability

Use Python's json module:
```python
import json
data = {{
    "report_title": "...",
    "generated_at": "...",
    "data": [...]
}}
with open('{filename}', 'w') as f:
    json.dump(data, f, indent=2)
```""".format(filename=filename)

        elif output_format == 'multi':
            base_name = result_file.stem  # Get filename without extension
            md_file = f"{base_name}.md"
            csv_file = f"{base_name}.csv"
            xlsx_file = f"{base_name}.xlsx"

            return f"""Generate THREE files in different formats:

1. MARKDOWN ({md_file}):
   - Executive summary with insights
   - Clear section headings (##)
   - Formatted tables if needed

2. CSV ({csv_file}):
   - Raw data in tabular format
   - Header row + data rows

3. EXCEL ({xlsx_file}):
   - Formatted spreadsheet with headers
   - Multiple sheets if appropriate
   - Use openpyxl library

Save all three files - user wants maximum flexibility!"""

        else:  # Default: markdown
            return """Generate a Markdown report with:
1. Clear section headings (## for main sections, ### for subsections)
2. Actionable insights and recommendations based on the REAL DATA above
3. Specific data points (reference actual order IDs, quantities, dates from the data)
4. Tables for tabular data (use markdown table syntax)
5. Bullet points for lists
6. **Bold** for emphasis on key findings
7. Concrete next steps section at the end

Use the Write tool to save the markdown content."""

    def _get_debug_logs_before(self) -> set:
        """Get set of existing debug log files before execution"""
        debug_dir = Path.home() / ".claude" / "debug"
        if debug_dir.exists():
            return set(debug_dir.glob("*.txt"))
        return set()

    def _parse_debug_log(self, log_path: Path) -> list:
        """Parse a Claude debug log file for tool usage"""
        tool_calls = []
        try:
            with open(log_path, 'r') as f:
                for line in f:
                    # Look for tool execution patterns
                    if 'executePreToolHooks called for tool:' in line:
                        # Extract tool name
                        parts = line.split('executePreToolHooks called for tool:')
                        if len(parts) > 1:
                            tool_name = parts[1].strip()
                            tool_calls.append(('start', tool_name, line.split('[DEBUG]')[0].strip()))

                    elif 'PostToolUse with query:' in line:
                        # Tool completed
                        parts = line.split('PostToolUse with query:')
                        if len(parts) > 1:
                            tool_name = parts[1].strip()
                            tool_calls.append(('end', tool_name, line.split('[DEBUG]')[0].strip()))

                    elif "MCP server" in line and "Calling MCP tool:" in line:
                        # MCP tool call
                        parts = line.split('Calling MCP tool:')
                        if len(parts) > 1:
                            tool_name = parts[1].strip()
                            tool_calls.append(('mcp', tool_name, line.split('[DEBUG]')[0].strip()))

                    elif "Tool '" in line and "completed successfully" in line:
                        # MCP tool completed
                        import re
                        match = re.search(r"Tool '([^']+)' completed successfully in (\d+)ms", line)
                        if match:
                            tool_name = match.group(1)
                            duration = match.group(2)
                            tool_calls.append(('mcp_done', f"{tool_name} ({duration}ms)", line.split('[DEBUG]')[0].strip()))

        except Exception as e:
            logger.error(f"Error parsing debug log: {e}")

        return tool_calls

    def _get_session_file_path(self, session_id: str, cwd: str) -> Path:
        """Get the path to a Claude session file based on working directory"""
        # Claude stores sessions in ~/.claude/projects/{project-key}/{session-id}.jsonl
        # The project key is the cwd path with:
        # - / replaced by -
        # - spaces replaced by -
        # - leading - preserved
        project_key = cwd.replace('/', '-').replace('\\', '-').replace(' ', '-').replace('_', '-')
        # Ensure leading dash for absolute paths
        if not project_key.startswith('-'):
            project_key = '-' + project_key

        session_file = Path.home() / '.claude' / 'projects' / project_key / f'{session_id}.jsonl'
        return session_file

    def parse_session_reasoning(self, session_id: str, cwd: str) -> Dict[str, Any]:
        """Parse a Claude session file for full reasoning chain

        Returns a dictionary with:
        - session_id: The session ID
        - reasoning_chain: List of reasoning steps (thinking, tool_use, tool_result, text)
        - total_steps: Total number of steps
        - model: Model used
        - token_usage: Token usage stats
        """
        session_file = self._get_session_file_path(session_id, cwd)

        if not session_file.exists():
            logger.warning(f"[WARN] Session file not found: {session_file}")
            return {
                'session_id': session_id,
                'reasoning_chain': [],
                'total_steps': 0,
                'error': f'Session file not found: {session_file}'
            }

        reasoning_chain = []
        model_used = None
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get('type')
                        timestamp = entry.get('timestamp')

                        if entry_type == 'assistant':
                            message = entry.get('message', {})

                            # Track model
                            if not model_used:
                                model_used = message.get('model')

                            # Track token usage
                            usage = message.get('usage', {})
                            total_input_tokens += usage.get('input_tokens', 0)
                            total_output_tokens += usage.get('output_tokens', 0)

                            # Parse content blocks
                            content_list = message.get('content', [])
                            for content in content_list:
                                content_type = content.get('type')

                                if content_type == 'thinking':
                                    reasoning_chain.append({
                                        'type': 'thinking',
                                        'content': content.get('thinking', ''),
                                        'timestamp': timestamp
                                    })
                                elif content_type == 'text':
                                    reasoning_chain.append({
                                        'type': 'text',
                                        'content': content.get('text', ''),
                                        'timestamp': timestamp
                                    })
                                elif content_type == 'tool_use':
                                    reasoning_chain.append({
                                        'type': 'tool_use',
                                        'tool_id': content.get('id'),
                                        'tool_name': content.get('name'),
                                        'tool_input': content.get('input', {}),
                                        'timestamp': timestamp
                                    })

                        elif entry_type == 'user':
                            # Check for tool results
                            message = entry.get('message', {})
                            content_list = message.get('content', [])

                            if isinstance(content_list, list):
                                for content in content_list:
                                    if isinstance(content, dict) and content.get('type') == 'tool_result':
                                        # Get tool result from the entry's toolUseResult field
                                        tool_result = entry.get('toolUseResult', {})
                                        reasoning_chain.append({
                                            'type': 'tool_result',
                                            'tool_id': content.get('tool_use_id'),
                                            'content': content.get('content', ''),
                                            'stdout': tool_result.get('stdout', ''),
                                            'stderr': tool_result.get('stderr', ''),
                                            'is_error': content.get('is_error', False),
                                            'timestamp': timestamp
                                        })

                    except json.JSONDecodeError:
                        continue

            logger.info(f"[BRAIN] Parsed {len(reasoning_chain)} reasoning steps from session {session_id}")

            return {
                'session_id': session_id,
                'reasoning_chain': reasoning_chain,
                'total_steps': len(reasoning_chain),
                'model': model_used,
                'token_usage': {
                    'input_tokens': total_input_tokens,
                    'output_tokens': total_output_tokens,
                    'total_tokens': total_input_tokens + total_output_tokens
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to parse session file: {e}")
            return {
                'session_id': session_id,
                'reasoning_chain': [],
                'total_steps': 0,
                'error': str(e)
            }

    def store_reasoning_to_server(self, task_id: int, reasoning_data: Dict[str, Any],
                                   prompt_sent: str, duration_seconds: float) -> bool:
        """Store Claude's full reasoning to server for admin viewing"""
        try:
            payload = {
                'task_id': task_id,
                'session_id': reasoning_data.get('session_id'),
                'reasoning_chain': json.dumps(reasoning_data.get('reasoning_chain', [])),
                'total_steps': reasoning_data.get('total_steps', 0),
                'model': reasoning_data.get('model'),
                'token_usage': json.dumps(reasoning_data.get('token_usage', {})),
                'prompt_sent': prompt_sent,
                'duration_seconds': duration_seconds,
                'captured_at': datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.mcp_server}/admin/tasks/{task_id}/reasoning",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"[BRAIN] Reasoning stored for task {task_id} ({reasoning_data.get('total_steps', 0)} steps)")
            return True

        except requests.exceptions.RequestException as e:
            logger.warning(f"[WARN] Failed to store reasoning: {e}")
            return False

    def _stream_claude_execution(self, command: list, cwd: str, prompt: str = None,
                                  timeout: int = 300, session_id: str = None) -> tuple:
        """Execute Claude Code CLI and parse debug logs for detailed tool usage

        Args:
            command: Claude CLI command (without prompt - prompt goes via stdin)
            cwd: Working directory for Claude execution
            prompt: Prompt to send via stdin (avoids Windows command-line truncation)
            timeout: Execution timeout in seconds
            session_id: Optional session ID to use (for reasoning capture)

        Returns:
            tuple: (stdout, stderr, returncode, tool_usage_list, session_id)
        """
        import subprocess
        import uuid

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Add session ID to command
        command = command + ['--session-id', session_id]

        logger.info("[BOT] Starting Claude Code CLI execution...")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Timeout: {timeout}s")
        if prompt:
            logger.info(f"   Prompt: {len(prompt)} chars (via stdin)")

        # Get existing debug logs before execution
        debug_logs_before = self._get_debug_logs_before()

        full_output = []
        error_output = []
        tools_used = []  # List of unique tools used

        # Use Popen to capture output
        # On Windows, use shell=True because Claude is installed as .cmd wrapper (not .exe)
        use_shell = sys.platform == 'win32'

        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE if prompt else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=use_shell
        )

        logger.info("   [WORK] Claude is working...")

        # Wait for process with timeout
        # Prompt is piped via stdin to avoid Windows command-line truncation issues
        try:
            stdout, stderr = process.communicate(input=prompt, timeout=timeout)
            full_output.append(stdout)
            if stderr:
                error_output.append(stderr)
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            logger.error(f"   [TIME]  Claude execution TIMEOUT after {timeout}s - killing process...")
            process.kill()
            stdout, stderr = process.communicate()
            full_output.append(stdout)
            if stderr:
                error_output.append(stderr)
            returncode = -1

        # Find new debug logs created during execution
        debug_logs_after = self._get_debug_logs_before()
        new_debug_logs = debug_logs_after - debug_logs_before

        # Parse new debug logs for tool usage
        if new_debug_logs:
            logger.info(f"   [TASK] Parsing {len(new_debug_logs)} debug log(s) for tool usage...")

            all_tool_calls = []
            for log_path in sorted(new_debug_logs, key=lambda p: p.stat().st_mtime):
                tool_calls = self._parse_debug_log(log_path)
                all_tool_calls.extend(tool_calls)

            # Log tool usage summary and collect unique tools
            if all_tool_calls:
                logger.info(f"   [TOOL] Tool calls detected: {len(all_tool_calls)}")
                for call_type, tool_name, _ in all_tool_calls:
                    if call_type == 'start':
                        logger.info(f"      >  {tool_name}")
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
                    elif call_type == 'mcp':
                        logger.info(f"      🌐 MCP: {tool_name}")
                        mcp_tool = f"MCP:{tool_name}"
                        if mcp_tool not in tools_used:
                            tools_used.append(mcp_tool)
                    elif call_type == 'mcp_done':
                        logger.info(f"      [OK] MCP completed: {tool_name}")
            else:
                logger.info("   [INFO]  No tool calls found in debug logs")
        else:
            logger.info("   [INFO]  No new debug logs created")

        if error_output:
            logger.warning(f"   [WARN]  Stderr: {''.join(error_output)[:200]}")

        logger.info(f"   {'[OK]' if returncode == 0 else '[ERROR]'} Claude execution finished (exit code: {returncode})")
        if tools_used:
            logger.info(f"   [TOOLS]  Tools used: {', '.join(tools_used)}")

        return (
            ''.join(full_output).strip(),
            ''.join(error_output).strip(),
            returncode,
            tools_used,
            session_id
        )

    def handle_agent_report(self, task_json: Dict, output_format: str = 'md', task_id: int = None) -> Dict:
        """Handle autonomous agent reports (HYBRID: Direct MCP + Claude Code CLI)"""
        agent_type = task_json.get('agent_type', 'Unknown')
        report_title = task_json.get('report_title', 'Agent Report')
        report_type = task_json.get('report_type', 'unknown')
        prompt = task_json.get('prompt', 'No prompt provided')

        logger.info(f"[REPORT] Generating agent report: {report_title} ({agent_type})")
        logger.info(f"[TOOL] HYBRID MODE: Direct MCP data fetch + Claude Code CLI analysis")
        logger.info(f"[DOC] Output format: {output_format.upper()}")

        # Initialize tools_used for tracking
        tools_used = []

        # Get output configuration - organize by agent_type
        output_config = task_json.get('output', {})
        default_path = f'Reports/{agent_type}'  # e.g., Reports/inventory_intelligence
        output_path = self.onedrive_base / output_config.get('path', default_path)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate filename with appropriate extension based on format
        file_extension = output_format if output_format in ['md', 'csv', 'json'] else 'xlsx'
        filename_pattern = output_config.get('filename_pattern', f'report_{{timestamp}}.{file_extension}')
        # Replace .md with correct extension if pattern has .md
        filename_pattern = filename_pattern.replace('.md', f'.{file_extension}')
        filename = filename_pattern.format(
            date=datetime.now().strftime('%Y-%m-%d'),
            timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
        )

        result_file = output_path / filename

        # Step 1: Fetch database context directly from MCP
        database_context = self.fetch_database_context(agent_type, prompt)

        # Step 2: Build enhanced prompt with real data for Claude Code CLI
        import subprocess

        # Build format-specific instructions
        format_instructions = self._get_format_instructions(output_format, result_file)

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

OUTPUT FORMAT REQUIREMENTS:
{format_instructions}

CRITICAL: You must save the output to this EXACT filename:
{filename}

(You are running from the correct directory, so just use the filename, not full path)

Analyze the database context provided and generate the file now:"""

        # Track execution time for reasoning capture
        import time as time_module
        start_time = time_module.time()
        session_id = None

        try:
            # Call Claude Code CLI with auto-approval for automated execution
            # Set working directory to output folder so Claude can write files directly
            # NOTE: Prompt is passed via stdin (not command-line) to avoid truncation on Windows
            command = ['claude', '--dangerously-skip-permissions']

            # Use streaming execution for detailed logging
            # Prompt is piped via stdin to handle multi-line prompts correctly on all platforms
            stdout, stderr, returncode, tools_used, session_id = self._stream_claude_execution(
                command,
                str(output_path),
                prompt=claude_prompt
            )

            # Calculate duration
            duration_seconds = time_module.time() - start_time

            if returncode == 0:
                report_content = stdout

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
                error_msg = stderr if stderr else "Unknown error"
                logger.error(f"[ERROR] Claude Code CLI failed: {error_msg}")

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
            duration_seconds = time_module.time() - start_time
            tools_used = []
            logger.error(f"[ERROR] Claude Code CLI timed out after 5 minutes")
            full_report = f"""# {report_title} - TIMEOUT

**Generated**: {datetime.now().isoformat()}
**Status**: TIMEOUT

Claude Code CLI execution timed out after 5 minutes.
"""

        except Exception as e:
            duration_seconds = time_module.time() - start_time
            tools_used = []
            logger.error(f"[ERROR] Failed to execute Claude Code CLI: {e}")
            full_report = f"""# {report_title} - ERROR

**Generated**: {datetime.now().isoformat()}
**Status**: ERROR

{str(e)}
"""

        # Handle output based on format
        if output_format in ['csv', 'xlsx', 'json']:
            # For data files, Claude should have created the file - verify it exists
            if result_file.exists():
                logger.info(f"[OK] Data file created by Claude: {result_file.name}")

                # Save execution log separately (don't overwrite the data file!)
                log_file = result_file.with_suffix(result_file.suffix + '.log')
                with open(log_file, 'w') as f:
                    f.write(full_report)
                logger.info(f"📝 Execution log saved: {log_file.name}")
            else:
                error_msg = f"Claude did not create the expected file: {result_file.name}"
                logger.error(f"[ERROR] {error_msg}")
                # Create error report
                with open(result_file.with_suffix('.error.md'), 'w') as f:
                    f.write(f"# ERROR: File Not Created\n\n{error_msg}\n\n{full_report}")
                raise FileNotFoundError(error_msg)
        else:
            # For markdown/text reports, check if Claude created the file with actual content
            if result_file.exists() and result_file.stat().st_size > 200:
                # Claude wrote meaningful content - read it and use as the report
                with open(result_file, 'r', encoding='utf-8') as f:
                    claude_content = f.read()
                logger.info(f"[OK] Using Claude's markdown content ({len(claude_content)} chars)")
                # Keep Claude's content as-is (don't wrap in template)
            else:
                # Claude didn't create the file or it's too small - use stdout wrapped in template
                with open(result_file, 'w', encoding='utf-8') as f:
                    f.write(full_report)
                logger.info(f"[OK] Wrote stdout-based report ({len(full_report)} chars)")

        relative_path = str(result_file.relative_to(self.onedrive_base))

        logger.info(f"[OK] Agent report saved: {relative_path}")

        # Sync report to server database for UI display
        self.sync_report_to_server(
            agent_type=agent_type,
            report_title=report_title,
            report_content=full_report,
            file_path=relative_path,
            task_id=task_id
        )

        # Capture and store reasoning chain for admin viewing
        if session_id and task_id:
            try:
                reasoning_data = self.parse_session_reasoning(session_id, str(output_path))
                if reasoning_data.get('total_steps', 0) > 0:
                    self.store_reasoning_to_server(
                        task_id=task_id,
                        reasoning_data=reasoning_data,
                        prompt_sent=claude_prompt,
                        duration_seconds=duration_seconds
                    )
            except Exception as e:
                logger.warning(f"[WARN] Failed to capture reasoning: {e}")

        return {
            'path': relative_path,
            'summary': f"Generated {report_title} ({agent_type})",
            'tool_usage': tools_used,
            'session_id': session_id
        }

    def run(self):
        """Main execution loop"""
        logger.info("=" * 70)
        logger.info("[START] CLAUDE TASK EXECUTOR STARTED")
        logger.info("=" * 70)
        logger.info(f"[POLL] Polling: {self.mcp_server}")
        logger.info(f"[TIME]  Interval: Every {POLL_INTERVAL} seconds")
        logger.info(f"[DIR] OneDrive: {self.onedrive_base}")
        logger.info("=" * 70)
        logger.info("")

        while True:
            try:
                # Poll for ready tasks
                tasks = self.poll_ready_tasks()

                if tasks:
                    logger.info(f"[TASK] Found {len(tasks)} ready task(s)")

                    for task in tasks:
                        self.execute_task(task)

                # Wait before next poll
                time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("")
                logger.info("=" * 70)
                logger.info("[STOP]  Executor stopped by user")
                logger.info("=" * 70)
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(POLL_INTERVAL)


def main():
    """Main entry point"""
    # Validate Claude Tools path exists (uses robust detection from ONEDRIVE_BASE)
    if not ONEDRIVE_BASE.exists():
        logger.error(f"[ERROR] Claude Tools path not found: {ONEDRIVE_BASE}")
        logger.info("   Set CLAUDE_TOOLS_PATH environment variable to override:")
        logger.info("   Example: set CLAUDE_TOOLS_PATH=C:\\path\\to\\Claude Tools")
        sys.exit(1)

    # Create executor and run
    executor = ClaudeExecutor()
    executor.run()


if __name__ == '__main__':
    main()
