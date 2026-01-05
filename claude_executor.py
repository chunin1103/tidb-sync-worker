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

    def _stream_claude_execution(self, command: list, cwd: str, timeout: int = 300) -> tuple:
        """Execute Claude Code CLI and parse debug logs for detailed tool usage

        Returns:
            tuple: (stdout, stderr, returncode, tool_usage_list)
        """
        import subprocess

        logger.info("[BOT] Starting Claude Code CLI execution...")
        logger.info(f"   Timeout: {timeout}s")

        # Get existing debug logs before execution
        debug_logs_before = self._get_debug_logs_before()

        full_output = []
        error_output = []
        tools_used = []  # List of unique tools used

        # Use Popen to capture output
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        logger.info("   📝 Claude is working...")

        # Wait for process with timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
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
            tools_used
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

        try:
            # Call Claude Code CLI with auto-approval for automated execution
            # Set working directory to output folder so Claude can write files directly
            # NOTE: --print flag disabled to allow tool usage (Write, Bash, etc.)
            command = ['claude', '--dangerously-skip-permissions', claude_prompt]

            # Use streaming execution for detailed logging
            stdout, stderr, returncode, tools_used = self._stream_claude_execution(
                command,
                str(output_path)
            )

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
            logger.error(f"[ERROR] Claude Code CLI timed out after 5 minutes")
            full_report = f"""# {report_title} - TIMEOUT

**Generated**: {datetime.now().isoformat()}
**Status**: TIMEOUT

Claude Code CLI execution timed out after 5 minutes.
"""

        except Exception as e:
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
            # For markdown/text reports, write the full report content
            with open(result_file, 'w') as f:
                f.write(full_report)

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

        return {
            'path': relative_path,
            'summary': f"Generated {report_title} ({agent_type})",
            'tool_usage': tools_used
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
