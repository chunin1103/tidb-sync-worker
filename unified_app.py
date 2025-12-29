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

Environment Variables:
- PORT: Server port (default: 8080)
- TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASSWORD, TIDB_DATABASE
- IDRIVE_ACCESS_KEY, IDRIVE_SECRET_KEY, IDRIVE_ENDPOINT, IDRIVE_BUCKET
"""

import os
import sys
import logging
from flask import Flask, jsonify

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
        # Skip static routes
        if rule.endpoint != 'static':
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
        static_folder=os.path.join(agent_garden_path, 'static') if os.path.exists(os.path.join(agent_garden_path, 'static')) else None
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
# ROOT ENDPOINT (Unified Health Check)
# =============================================================================

@app.route('/')
def unified_health():
    """Unified health check endpoint."""
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
            'tidb_mcp': {
                'health': '/',
                'mcp': '/mcp',
                'tools': '/tools',
                'query': '/query'
            },
            'agent_garden': {
                'ui': '/AgentGarden/',
                'execute': '/AgentGarden/execute_agent',
                'sessions': '/AgentGarden/sessions'
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
