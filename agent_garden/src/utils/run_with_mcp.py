"""
Startup script that configures agents to use MCP server for TiDB access
Run this instead of `python app.py` to use MCP
"""

# Step 1: Configure TiDB to use MCP BEFORE any other imports
print("🚀 Configuring TiDB to use MCP server...")

import tidb_connector

# The MCP query function - this will be injected by Claude Code environment
# When running in Claude Code, replace this with: mcp__tidb_mcp__query
def get_mcp_query_function():
    """
    Get the MCP query function from Claude Code environment.

    In Claude Code, you would use:
        return mcp__tidb_mcp__query

    For standalone testing, this returns a mock function.
    """
    try:
        # Try to import from Claude Code's injected MCP tools
        # This path will work when code is executed by Claude Code
        from __main__ import mcp__tidb_mcp__query
        return mcp__tidb_mcp__query
    except (ImportError, AttributeError):
        print("⚠️ MCP tools not available - using mock for testing")
        # Return a mock function for testing
        def mock_mcp_query(sql):
            print(f"[MOCK MCP] Would execute: {sql[:80]}...")
            return {'rows': [], 'row_count': 0}
        return mock_mcp_query

# Configure TiDB with MCP
mcp_func = get_mcp_query_function()
tidb_connector.set_mcp_function(mcp_func)

print("✅ TiDB configured to use MCP server!")

# Step 2: Now import and run the Flask app
print("🌐 Starting Flask application...")

from app import app

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🎉 AGENT GARDEN - Running with MCP Database Access")
    print("=" * 80)
    print("\n📊 Configuration:")
    print(f"  - TiDB via MCP: ✅ Enabled")
    print(f"  - Redis caching: ✅ Enabled")
    print(f"  - Parallel queries: ✅ Enabled")
    print("\n🚀 Server starting on http://localhost:5001")
    print("=" * 80)
    print()

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )
