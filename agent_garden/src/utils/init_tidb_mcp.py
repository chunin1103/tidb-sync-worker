"""
Initialize TiDB connector with MCP server support
Run this ONCE at application startup to configure MCP access
"""

from src.connectors.tidb_connector import TiDBConnector
import logging

logger = logging.getLogger(__name__)


def init_tidb_with_mcp(mcp_query_function):
    """
    Initialize TiDB connector with MCP server.

    Args:
        mcp_query_function: The mcp__tidb-mcp__query function

    Returns:
        Configured TiDBConnector instance

    Example usage in app.py:
        from src.utils.init_tidb_mcp import init_tidb_with_mcp
        import tidb_connector

        # Initialize with MCP
        tidb_connector.tidb = init_tidb_with_mcp(mcp__tidb_mcp__query)
    """
    logger.info("🚀 Initializing TiDB with MCP server...")

    # Create new connector with MCP support
    connector = TiDBConnector(mcp_query_func=mcp_query_function)

    # Test the connection
    if connector.test_connection():
        logger.info("✅ TiDB MCP connector ready!")
        return connector
    else:
        logger.error("❌ TiDB MCP connector failed to initialize")
        raise ConnectionError("Failed to connect to TiDB via MCP")


# For standalone testing
if __name__ == "__main__":
    print("This module should be imported and used with MCP query function")
    print("\nExample usage:")
    print("  from src.utils.init_tidb_mcp import init_tidb_with_mcp")
    print("  import tidb_connector")
    print("  tidb_connector.tidb = init_tidb_with_mcp(mcp__tidb_mcp__query)")
