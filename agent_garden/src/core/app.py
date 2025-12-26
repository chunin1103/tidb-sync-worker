"""
Agent Garden - Flask Server
Routes: / (UI), /execute_agent (SSE streaming API)
"""

import os
import uuid
import logging
from flask import Flask, render_template, request, Response, jsonify, stream_with_context, make_response
from src.core.agent_backend import execute_agent, clear_session, get_active_sessions
from src.core.database import (
    get_sessions_with_metadata,
    get_session_history,
    get_session_export_data,
    get_recent_agent_runs,
    get_agent_reports,
    mark_report_as_read,
    get_all_schedules,
    get_schedule,
    update_schedule,
    get_system_settings,
    update_timezone,
    get_available_timezones
)
from autonomous_agents import trigger_task_now, get_task_status
from src.scheduling.schedule_loader import get_schedule_summary
from datetime import datetime
import json

# Get project root directory (2 levels up from this file: src/core/app.py -> project root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Initialize Flask app with correct template and static folders
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static') if os.path.exists(os.path.join(project_root, 'static')) else None
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# INITIALIZE TIDB WITH MCP (if MCP tools are available)
# ============================================================================
try:
    # If running in Claude Code, MCP tools are available as functions
    # This will be injected by Claude Code at runtime
    def get_mcp_query_func():
        """
        This function will be replaced with actual MCP tool when running in Claude Code.
        For standalone Flask app, it returns None (uses direct connection instead).
        """
        return None

    mcp_query = get_mcp_query_func()

    if mcp_query:
        from src.utils.init_tidb_mcp import init_tidb_with_mcp
        import tidb_connector
        tidb_connector.tidb = init_tidb_with_mcp(mcp_query)
        logger.info("🚀 TiDB initialized with MCP server!")
    else:
        logger.info("📌 TiDB using direct connection (MCP not available)")

except Exception as e:
    logger.warning(f"⚠️ Could not initialize TiDB with MCP: {e}")
    logger.info("📌 Falling back to direct TiDB connection")

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """
    Serve the main UI (Agent Garden dashboard).
    """
    return render_template('index.html')


@app.route('/execute_agent', methods=['POST'])
def execute_agent_route():
    """
    Execute an agent with Server-Sent Events (SSE) streaming.

    Request Body (JSON):
    {
        "agent_type": "inventory_intelligence",
        "message": "What should we cut this week?",
        "session_id": "unique-session-id"
    }

    Response: text/event-stream (SSE format)
    """
    try:
        # Parse request body
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        agent_type = data.get("agent_type")
        message = data.get("message")
        session_id = data.get("session_id")

        # Validate required fields
        if not agent_type:
            return jsonify({"error": "Missing required field: agent_type"}), 400
        if not message:
            return jsonify({"error": "Missing required field: message"}), 400
        if not session_id:
            # Generate session ID if not provided
            session_id = str(uuid.uuid4())
            logger.info(f"Generated new session ID: {session_id}")

        logger.info(f"Executing agent: {agent_type}, session: {session_id}")

        # Define SSE streaming generator
        def generate():
            """Stream response chunks as Server-Sent Events."""
            try:
                for chunk in execute_agent(agent_type, message, session_id):
                    # SSE format: "data: {content}\n\n"
                    yield f"data: {chunk}\n\n"

                # Send completion signal
                yield "data: [DONE]\n\n"

            except ValueError as e:
                # Invalid agent type
                logger.error(f"Validation error: {str(e)}")
                yield f"data: ⚠️ Error: {str(e)}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                # Other errors (already logged in agent_backend.py)
                logger.error(f"Execution error: {str(e)}")
                yield f"data: ⚠️ Unexpected error occurred. Please try again.\n\n"
                yield "data: [DONE]\n\n"

        # Return SSE stream
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'  # Disable Nginx buffering
            }
        )

    except Exception as e:
        logger.error(f"Request handling error: {str(e)}")
        return jsonify({"error": "Failed to process request"}), 500


@app.route('/clear_session', methods=['POST'])
def clear_session_route():
    """
    Clear conversation history for a session.

    Request Body (JSON):
    {
        "session_id": "session-to-clear"
    }

    Response:
    {
        "success": true,
        "message": "Session cleared"
    }
    """
    try:
        data = request.get_json()

        if not data or not data.get("session_id"):
            return jsonify({"error": "Missing required field: session_id"}), 400

        session_id = data["session_id"]
        success = clear_session(session_id)

        if success:
            return jsonify({"success": True, "message": f"Session {session_id} cleared"})
        else:
            return jsonify({"success": False, "message": f"Session {session_id} not found"}), 404

    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return jsonify({"error": "Failed to clear session"}), 500


@app.route('/sessions', methods=['GET'])
def get_sessions_route():
    """
    Get list of active sessions (for debugging/monitoring).

    Response:
    {
        "sessions": ["session-id-1", "session-id-2"]
    }
    """
    try:
        sessions = get_active_sessions()
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Error getting sessions: {str(e)}")
        return jsonify({"error": "Failed to retrieve sessions"}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for deployment monitoring.

    Response:
    {
        "status": "healthy",
        "active_sessions": 3
    }
    """
    try:
        active_sessions = len(get_active_sessions())
        return jsonify({
            "status": "healthy",
            "active_sessions": active_sessions
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route('/get_sessions', methods=['GET'])
def get_sessions_list():
    """
    Get all chat sessions with metadata.

    Response:
    {
        "sessions": [
            {
                "session_id": "session_123",
                "agent_type": "inventory_intelligence",
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T13:00:00",
                "preview": "What should we cut this week?"
            }
        ]
    }
    """
    try:
        sessions = get_sessions_with_metadata()
        return jsonify({"sessions": sessions})
    except Exception as e:
        logger.error(f"Error getting sessions list: {str(e)}")
        return jsonify({"error": "Failed to retrieve sessions"}), 500


@app.route('/load_session/<session_id>', methods=['GET'])
def load_session(session_id):
    """
    Load conversation history for a specific session.

    Response:
    {
        "session_id": "session_123",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi there!"}
        ]
    }
    """
    try:
        messages = get_session_history(session_id)
        return jsonify({
            "session_id": session_id,
            "messages": messages
        })
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {str(e)}")
        return jsonify({"error": "Failed to load session"}), 500


@app.route('/export_session/<session_id>/<format>', methods=['GET'])
def export_session(session_id, format):
    """
    Export a session to various formats (json, markdown, txt).

    Args:
        session_id: Session to export
        format: Export format ('json', 'md', 'txt')

    Returns:
        File download response
    """
    try:
        # Get session data
        session_data = get_session_export_data(session_id)

        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        agent_name = session_data.get('agent_type', 'agent').replace('_', '-')

        if format == 'json':
            # JSON export
            filename = f"{agent_name}_chat_{timestamp}.json"
            content = json.dumps(session_data, indent=2, ensure_ascii=False)
            mimetype = 'application/json'

        elif format == 'md':
            # Markdown export
            filename = f"{agent_name}_chat_{timestamp}.md"
            content = format_markdown(session_data)
            mimetype = 'text/markdown'

        elif format == 'txt':
            # Plain text export
            filename = f"{agent_name}_chat_{timestamp}.txt"
            content = format_text(session_data)
            mimetype = 'text/plain'

        else:
            return jsonify({"error": "Invalid format. Use 'json', 'md', or 'txt'"}), 400

        # Create response with file download
        response = make_response(content)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'

        return response

    except Exception as e:
        logger.error(f"Error exporting session {session_id}: {str(e)}")
        return jsonify({"error": "Failed to export session"}), 500


def format_markdown(session_data):
    """Format session data as Markdown"""
    md = f"# Chat Export - {session_data.get('agent_type', 'Agent').replace('_', ' ').title()}\n\n"
    md += f"**Session ID:** `{session_data['session_id']}`  \n"
    md += f"**Created:** {session_data.get('created_at', 'N/A')}  \n"
    md += f"**Last Updated:** {session_data.get('updated_at', 'N/A')}  \n"
    md += f"**Messages:** {session_data.get('message_count', 0)}  \n\n"
    md += "---\n\n"

    for i, msg in enumerate(session_data.get('messages', []), 1):
        role = "👤 **User**" if msg['role'] == 'user' else "🤖 **Agent**"
        timestamp = msg.get('timestamp', 'N/A')
        content = msg['content']

        md += f"### Message {i} - {role}\n"
        md += f"*{timestamp}*\n\n"
        md += f"{content}\n\n"
        md += "---\n\n"

    md += f"\n*Exported from Agent Garden on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    return md


def format_text(session_data):
    """Format session data as plain text"""
    txt = f"CHAT EXPORT - {session_data.get('agent_type', 'Agent').replace('_', ' ').upper()}\n"
    txt += "=" * 80 + "\n\n"
    txt += f"Session ID: {session_data['session_id']}\n"
    txt += f"Created: {session_data.get('created_at', 'N/A')}\n"
    txt += f"Last Updated: {session_data.get('updated_at', 'N/A')}\n"
    txt += f"Total Messages: {session_data.get('message_count', 0)}\n\n"
    txt += "=" * 80 + "\n\n"

    for i, msg in enumerate(session_data.get('messages', []), 1):
        role = "USER" if msg['role'] == 'user' else "AGENT"
        timestamp = msg.get('timestamp', 'N/A')
        content = msg['content']

        txt += f"[{i}] {role} - {timestamp}\n"
        txt += "-" * 80 + "\n"
        txt += f"{content}\n\n"

    txt += "=" * 80 + "\n"
    txt += f"Exported from Agent Garden on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    return txt


# ============================================================================
# AUTONOMOUS AGENT API ENDPOINTS
# ============================================================================

@app.route('/get_agent_runs', methods=['GET'])
def get_agent_runs():
    """
    Get recent autonomous agent runs.

    Query params:
        limit: Number of runs to return (default: 10)

    Response:
    {
        "runs": [
            {
                "id": 1,
                "agent_type": "inventory_intelligence",
                "run_type": "scheduled",
                "trigger": "cron:daily_7am",
                "started_at": "2024-01-15T07:00:00",
                "completed_at": "2024-01-15T07:02:30",
                "status": "completed",
                "output_summary": "Morning report generated..."
            }
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 10))
        runs = get_recent_agent_runs(limit=limit)
        return jsonify({"runs": runs})
    except Exception as e:
        logger.error(f"Error getting agent runs: {str(e)}")
        return jsonify({"error": "Failed to retrieve agent runs"}), 500


@app.route('/get_agent_reports', methods=['GET'])
def get_agent_reports_route():
    """
    Get agent-generated reports.

    Query params:
        limit: Number of reports to return (default: 10)
        unread_only: If true, only return unread reports (default: false)

    Response:
    {
        "reports": [
            {
                "id": 1,
                "agent_run_id": 1,
                "agent_type": "inventory_intelligence",
                "report_type": "morning_intelligence",
                "title": "Morning Intelligence Report - Jan 15, 2024",
                "content": "Full report content...",
                "created_at": "2024-01-15T07:02:00",
                "read_at": null,
                "is_unread": true
            }
        ]
    }
    """
    try:
        limit = int(request.args.get('limit', 10))
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        reports = get_agent_reports(limit=limit, unread_only=unread_only)
        return jsonify({"reports": reports})
    except Exception as e:
        logger.error(f"Error getting agent reports: {str(e)}")
        return jsonify({"error": "Failed to retrieve agent reports"}), 500


@app.route('/mark_report_read/<int:report_id>', methods=['POST'])
def mark_report_read(report_id):
    """
    Mark a report as read.

    Args:
        report_id: ID of the report to mark as read

    Response:
    {
        "success": true,
        "report_id": 1
    }
    """
    try:
        success = mark_report_as_read(report_id)
        if success:
            return jsonify({"success": True, "report_id": report_id})
        else:
            return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        logger.error(f"Error marking report as read: {str(e)}")
        return jsonify({"error": "Failed to mark report as read"}), 500


@app.route('/trigger_agent_task', methods=['POST'])
def trigger_agent_task():
    """
    Manually trigger an autonomous agent task.

    Request Body (JSON):
    {
        "task_name": "morning_intelligence_report"
    }

    Available tasks:
    - morning_intelligence_report
    - inventory_health_check
    - weekly_summary_report

    Response:
    {
        "success": true,
        "task_id": "abc-123-def",
        "task_name": "morning_intelligence_report",
        "message": "Task triggered successfully"
    }
    """
    try:
        data = request.get_json()
        task_name = data.get('task_name')

        if not task_name:
            return jsonify({"error": "task_name is required"}), 400

        # Trigger the task
        result = trigger_task_now(task_name)

        if result:
            return jsonify({
                "success": True,
                "task_id": result.id,
                "task_name": task_name,
                "message": f"Task '{task_name}' triggered successfully"
            })
        else:
            return jsonify({"error": f"Unknown task: {task_name}"}), 400

    except Exception as e:
        logger.error(f"Error triggering agent task: {str(e)}")
        return jsonify({"error": "Failed to trigger task"}), 500


@app.route('/get_task_status/<task_id>', methods=['GET'])
def get_task_status_route(task_id):
    """
    Check the status of a Celery task.

    Args:
        task_id: Celery task ID

    Response:
    {
        "task_id": "abc-123-def",
        "state": "SUCCESS",
        "ready": true,
        "successful": true,
        "result": "Task completed"
    }
    """
    try:
        status = get_task_status(task_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({"error": "Failed to get task status"}), 500


# ============================================================================
# SCHEDULE MANAGEMENT API
# ============================================================================

@app.route('/get_schedules', methods=['GET'])
def get_schedules():
    """
    Get all schedule configurations.

    Response:
    {
        "success": true,
        "schedules": [
            {
                "task_name": "morning_intelligence_report",
                "display_name": "Morning Intelligence Report",
                "schedule_type": "cron",
                "hour": 7,
                "minute": 0,
                "enabled": 1,
                "description": "...",
                "last_modified": "2025-12-24T10:30:00"
            },
            ...
        ],
        "summary": {
            "total_schedules": 3,
            "enabled": 3,
            "disabled": 0
        }
    }
    """
    try:
        schedules = get_all_schedules()
        summary = get_schedule_summary()

        return jsonify({
            "success": True,
            "schedules": schedules,
            "summary": summary
        })
    except Exception as e:
        logger.error(f"Error getting schedules: {str(e)}")
        return jsonify({"error": "Failed to get schedules"}), 500


@app.route('/get_schedule/<task_name>', methods=['GET'])
def get_schedule_route(task_name):
    """
    Get a specific schedule configuration.

    Args:
        task_name: Name of the scheduled task

    Response:
    {
        "success": true,
        "schedule": {
            "task_name": "morning_intelligence_report",
            "display_name": "Morning Intelligence Report",
            ...
        }
    }
    """
    try:
        schedule = get_schedule(task_name)

        if schedule:
            return jsonify({
                "success": True,
                "schedule": schedule
            })
        else:
            return jsonify({"error": f"Schedule not found: {task_name}"}), 404

    except Exception as e:
        logger.error(f"Error getting schedule: {str(e)}")
        return jsonify({"error": "Failed to get schedule"}), 500


@app.route('/update_schedule/<task_name>', methods=['POST'])
def update_schedule_route(task_name):
    """
    Update a schedule configuration.

    Request Body (JSON):
    {
        "hour": 8,           // For cron schedules
        "minute": 30,        // For cron schedules
        "day_of_week": 1,    // For cron schedules (optional)
        "interval_seconds": 21600,  // For interval schedules
        "enabled": 1         // 0 or 1
    }

    Response:
    {
        "success": true,
        "message": "Schedule updated successfully",
        "schedule": { ... },
        "requires_restart": true
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Request body must be JSON"}), 400

        # Update the schedule
        success = update_schedule(task_name, data)

        if success:
            # Get the updated schedule
            updated_schedule = get_schedule(task_name)

            return jsonify({
                "success": True,
                "message": f"Schedule '{task_name}' updated successfully",
                "schedule": updated_schedule,
                "requires_restart": False,
                "auto_reload_seconds": 30,
                "info": "Changes will take effect within 30 seconds automatically"
            })
        else:
            return jsonify({"error": f"Schedule not found: {task_name}"}), 404

    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        return jsonify({"error": "Failed to update schedule"}), 500


@app.route('/celery_status', methods=['GET'])
def celery_status():
    """
    Check if Celery Beat is currently running.

    Response:
    {
        "running": true/false,
        "pids": [12345],
        "count": 1
    }
    """
    try:
        import subprocess

        result = subprocess.run(
            ['pgrep', '-f', 'celery.*beat'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            pids = [int(pid) for pid in result.stdout.strip().split('\n') if pid]
            return jsonify({
                "running": True,
                "pids": pids,
                "count": len(pids)
            })
        else:
            return jsonify({
                "running": False,
                "pids": [],
                "count": 0
            })

    except Exception as e:
        logger.error(f"Error checking Celery status: {str(e)}")
        return jsonify({"error": str(e), "running": False}), 500


@app.route('/restart_celery_beat', methods=['POST'])
def restart_celery_beat():
    """
    Restart Celery Beat to reload schedules.

    If Celery Beat is not running, provides instructions to start it manually.

    This endpoint triggers a graceful restart of the Celery Beat scheduler
    to apply schedule changes from the database.

    Response:
    {
        "success": true,
        "message": "Celery Beat restart initiated",
        "estimated_downtime": "3-8 seconds"
    }
    """
    try:
        import subprocess
        import signal

        # Find and kill existing Celery Beat process
        try:
            # Find PID of celery beat
            result = subprocess.run(
                ['pgrep', '-f', 'celery.*beat'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        logger.info(f"Sending SIGTERM to Celery Beat (PID: {pid})")
                        os.kill(int(pid), signal.SIGTERM)

                return jsonify({
                    "success": True,
                    "message": "Celery Beat restart signal sent",
                    "pids_terminated": pids,
                    "estimated_downtime": "3-8 seconds",
                    "instructions": "Celery Beat should automatically restart if using supervisor/systemd"
                })
            else:
                # Changed from 404 to 200 with success: false
                # This prevents scary 404 errors in the browser console
                return jsonify({
                    "success": False,
                    "not_running": True,
                    "message": "Celery Beat is not currently running",
                    "instructions": "Please start Celery Beat manually using: ./start_celery_beat.sh",
                    "manual_start_command": "./start_celery_beat.sh"
                }), 200  # Return 200 instead of 404

        except Exception as e:
            logger.error(f"Error restarting Celery Beat: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        logger.error(f"Error in restart_celery_beat: {str(e)}")
        return jsonify({"success": False, "error": "Failed to restart Celery Beat"}), 500


# ============================================================================
# SYSTEM SETTINGS ROUTES
# ============================================================================

@app.route('/get_settings', methods=['GET'])
def get_settings():
    """
    Get system settings including timezone configuration.

    Response:
    {
        "timezone": "Asia/Kuala_Lumpur",
        "updated_at": "2024-12-24T10:30:00"
    }
    """
    try:
        settings = get_system_settings()
        return jsonify(settings)
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({"error": "Failed to get settings"}), 500


@app.route('/get_timezones', methods=['GET'])
def get_timezones():
    """
    Get list of available timezones organized by region.

    Response:
    [
        {
            "value": "Asia/Kuala_Lumpur",
            "label": "Malaysia (Kuala Lumpur) - UTC+8",
            "region": "Asia"
        },
        ...
    ]
    """
    try:
        timezones = get_available_timezones()
        return jsonify(timezones)
    except Exception as e:
        logger.error(f"Error getting timezones: {str(e)}")
        return jsonify({"error": "Failed to get timezones"}), 500


@app.route('/update_timezone', methods=['POST'])
def update_timezone_route():
    """
    Update the system timezone.

    Request Body:
    {
        "timezone": "Asia/Bangkok"
    }

    Response:
    {
        "success": true,
        "message": "Timezone updated successfully",
        "new_timezone": "Asia/Bangkok",
        "requires_restart": true
    }
    """
    try:
        data = request.get_json()
        new_timezone = data.get('timezone')

        if not new_timezone:
            return jsonify({"error": "Timezone is required"}), 400

        # Validate timezone (basic check)
        valid_timezones = [tz['value'] for tz in get_available_timezones()]
        if new_timezone not in valid_timezones:
            return jsonify({"error": "Invalid timezone"}), 400

        # Update timezone in database
        success = update_timezone(new_timezone)

        if success:
            logger.info(f"Timezone updated to: {new_timezone}")

            return jsonify({
                "success": True,
                "message": "Timezone updated successfully",
                "new_timezone": new_timezone,
                "requires_restart": False,
                "auto_reload_seconds": 30,
                "info": "Timezone changes will take effect within 30 seconds automatically"
            })
        else:
            return jsonify({"error": "Failed to update timezone"}), 500

    except Exception as e:
        logger.error(f"Error updating timezone: {str(e)}")
        return jsonify({"error": "Failed to update timezone"}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# DEVELOPMENT SERVER
# ============================================================================

def find_available_port(start_port=5001, max_attempts=10):
    """Find an available port starting from start_port"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None


if __name__ == '__main__':
    # Development server configuration
    # Default to 5001 to avoid macOS AirPlay Receiver conflict on port 5000
    requested_port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Find available port
    port = find_available_port(requested_port)

    if port is None:
        logger.error(f"No available ports found starting from {requested_port}")
        exit(1)

    if port != requested_port:
        logger.warning(f"Port {requested_port} is in use. Using port {port} instead.")

    logger.info(f"Starting Agent Garden server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Access at: http://localhost:{port}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
