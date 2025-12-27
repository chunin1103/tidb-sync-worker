#!/usr/bin/env python3
"""
TiDB MCP Server - Query TiDB Cloud from Claude

This MCP server exposes tools to query your TiDB database directly from Claude.
Designed to run as a Render Web Service alongside the sync worker.

Tools:
- query: Run SELECT queries on the database
- list_tables: List all tables in the database
- describe_table: Get table schema/structure
- today_orders: Get today's orders (convenience method)
- recent_orders: Get recent orders (convenience method)
"""

import os
import json
import logging
import pymysql
from datetime import datetime, date
from decimal import Decimal
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# TiDB Configuration from environment
TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'port': int(os.environ.get('TIDB_PORT', 4000)),
    'user': os.environ.get('TIDB_USER', ''),
    'password': os.environ.get('TIDB_PASSWORD', ''),
    'database': os.environ.get('TIDB_DATABASE', 'test'),
    'ssl': {'ssl': {'ca': None}},
    'autocommit': True,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Maximum rows to return (safety limit)
MAX_ROWS = int(os.environ.get('MAX_QUERY_ROWS', 1000))


def get_connection():
    """Get a connection to TiDB."""
    return pymysql.connect(**TIDB_CONFIG)


def json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Type {type(obj)} not serializable")


def execute_query(sql, params=None):
    """Execute a SQL query and return results."""
    # Safety check - only allow SELECT queries
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('SHOW') and not sql_upper.startswith('DESCRIBE'):
        return {'error': 'Only SELECT, SHOW, and DESCRIBE queries are allowed'}

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchmany(MAX_ROWS)

        # Check if there are more rows
        has_more = cursor.fetchone() is not None

        cursor.close()
        conn.close()

        return {
            'rows': rows,
            'row_count': len(rows),
            'has_more': has_more,
            'max_rows': MAX_ROWS
        }
    except pymysql.Error as e:
        return {'error': f"Database error: {e}"}
    except Exception as e:
        return {'error': f"Error: {e}"}


# =============================================================================
# MCP Protocol Implementation
# =============================================================================

# Define available tools
MCP_TOOLS = [
    {
        "name": "query",
        "description": "Execute a SELECT query on the TiDB database. Only read-only queries are allowed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL SELECT query to execute"
                }
            },
            "required": ["sql"]
        }
    },
    {
        "name": "list_tables",
        "description": "List all tables in the database",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "describe_table",
        "description": "Get the schema/structure of a specific table",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": "Name of the table to describe"
                }
            },
            "required": ["table_name"]
        }
    },
    {
        "name": "today_orders",
        "description": "Get all orders placed today with count",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "recent_orders",
        "description": "Get the most recent orders from the database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of orders to return (default: 10, max: 100)",
                    "default": 10
                }
            }
        }
    },
    {
        "name": "order_details",
        "description": "Get full details of a specific order including products",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The order ID to look up"
                }
            },
            "required": ["order_id"]
        }
    }
]


def handle_tool_call(tool_name, arguments):
    """Handle a tool call and return the result."""

    if tool_name == "query":
        sql = arguments.get("sql", "")
        result = execute_query(sql)
        return json.dumps(result, default=json_serial)

    elif tool_name == "list_tables":
        result = execute_query("SHOW TABLES")
        if 'rows' in result:
            # Extract just table names
            tables = [list(row.values())[0] for row in result['rows']]
            return json.dumps({'tables': tables, 'count': len(tables)})
        return json.dumps(result)

    elif tool_name == "describe_table":
        table_name = arguments.get("table_name", "")
        # Sanitize table name to prevent injection
        if not table_name.replace('_', '').isalnum():
            return json.dumps({'error': 'Invalid table name'})
        result = execute_query(f"DESCRIBE `{table_name}`")
        return json.dumps(result, default=json_serial)

    elif tool_name == "today_orders":
        sql = """
            SELECT COUNT(*) as count
            FROM orders
            WHERE DATE(date_purchased) = CURDATE()
        """
        count_result = execute_query(sql)
        count = count_result.get('rows', [{}])[0].get('count', 0) if count_result.get('rows') else 0

        sql = """
            SELECT orders_id, customers_name, customers_email_address,
                   date_purchased, orders_status, billing_city, billing_state
            FROM orders
            WHERE DATE(date_purchased) = CURDATE()
            ORDER BY date_purchased DESC
        """
        orders_result = execute_query(sql)

        return json.dumps({
            'count': count,
            'orders': orders_result.get('rows', [])
        }, default=json_serial)

    elif tool_name == "recent_orders":
        limit = min(arguments.get("limit", 10), 100)
        sql = f"""
            SELECT orders_id, customers_name, customers_email_address,
                   date_purchased, orders_status, billing_city, billing_state
            FROM orders
            ORDER BY date_purchased DESC
            LIMIT {limit}
        """
        result = execute_query(sql)
        return json.dumps(result, default=json_serial)

    elif tool_name == "order_details":
        order_id = arguments.get("order_id")
        if not order_id:
            return json.dumps({'error': 'order_id is required'})

        # Get order info
        order_result = execute_query(
            "SELECT * FROM orders WHERE orders_id = %s",
            (order_id,)
        )

        # Get order products
        products_result = execute_query(
            """SELECT op.*, p.products_model
               FROM orders_products op
               LEFT JOIN products p ON op.products_id = p.products_id
               WHERE op.orders_id = %s""",
            (order_id,)
        )

        # Get order totals
        totals_result = execute_query(
            "SELECT * FROM orders_total WHERE orders_id = %s ORDER BY sort_order",
            (order_id,)
        )

        return json.dumps({
            'order': order_result.get('rows', [{}])[0] if order_result.get('rows') else None,
            'products': products_result.get('rows', []),
            'totals': totals_result.get('rows', [])
        }, default=json_serial)

    else:
        return json.dumps({'error': f'Unknown tool: {tool_name}'})


# =============================================================================
# HTTP Endpoints for MCP over HTTP (Streamable)
# =============================================================================

@app.route('/')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'tidb-mcp-server',
        'database': TIDB_CONFIG['database']
    })


@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """Main MCP endpoint - handles JSON-RPC style requests."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON body provided'}), 400

        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')

        # Log all incoming MCP method calls for debugging
        logger.info(f"🔧 MCP method: {method} | params: {list(params.keys()) if params else 'none'}")

        # Handle different MCP methods
        if method == 'initialize':
            response = {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'tidb-mcp-server',
                    'version': '1.0.1'
                }
            }
            logger.info("✅ MCP initialized")

        elif method == 'initialized':
            # Notification sent by client after initialize - no response needed
            response = {}
            logger.info("✅ Client sent initialized notification")

        elif method == 'notifications/initialized':
            # Some clients send this instead of 'initialized'
            response = {}
            logger.info("✅ Client sent notifications/initialized")

        elif method == 'tools/list':
            response = {'tools': MCP_TOOLS}
            logger.info(f"✅ Returned {len(MCP_TOOLS)} tools")

        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            logger.info(f"🔨 Calling tool: {tool_name}")

            result = handle_tool_call(tool_name, arguments)

            response = {
                'content': [
                    {
                        'type': 'text',
                        'text': result
                    }
                ]
            }
            logger.info(f"✅ Tool {tool_name} completed")

        elif method == 'ping':
            response = {}
            logger.info("✅ Ping response")

        elif method == 'resources/list':
            response = {'resources': []}
            logger.info("ℹ️  Resources not supported (returned empty list)")

        elif method == 'resources/read':
            logger.warning(f"⚠️  Resources not supported, resource requested: {params.get('uri')}")
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': 'Resources not supported'},
                'id': request_id
            }), 200  # Return 200, not 404

        elif method == 'prompts/list':
            response = {'prompts': []}
            logger.info("ℹ️  Prompts not supported (returned empty list)")

        elif method == 'prompts/get':
            logger.warning(f"⚠️  Prompts not supported, prompt requested: {params.get('name')}")
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': 'Prompts not supported'},
                'id': request_id
            }), 200  # Return 200, not 404

        elif method == 'completion/complete':
            response = {'completion': {'values': [], 'total': 0, 'hasMore': False}}
            logger.info("ℹ️  Completion not supported (returned empty)")

        elif method == 'logging/setLevel':
            response = {}
            logger.info(f"ℹ️  Logging level change requested: {params.get('level')} (ignored)")

        else:
            # For any other unknown method, return empty response instead of 404
            response = {}
            logger.warning(f"⚠️  Unknown MCP method: {method} (returned empty response)")

        return jsonify({
            'jsonrpc': '2.0',
            'result': response,
            'id': request_id
        })

    except Exception as e:
        logger.error(f"❌ MCP error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32603, 'message': str(e)},
            'id': request.get_json().get('id') if request.get_json() else None
        }), 500


@app.route('/tools', methods=['GET'])
def list_tools():
    """List available tools (convenience endpoint)."""
    return jsonify({'tools': MCP_TOOLS})


@app.route('/query', methods=['POST'])
def direct_query():
    """Direct query endpoint for testing."""
    data = request.get_json()
    sql = data.get('sql', '')
    result = execute_query(sql)
    return jsonify(result)


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    # Validate environment
    required_vars = ['TIDB_USER', 'TIDB_PASSWORD']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        logger.info("Set TIDB_HOST, TIDB_PORT, TIDB_USER, TIDB_PASSWORD, TIDB_DATABASE")
        exit(1)

    # Test connection
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        logger.info(f"Connected to TiDB: {TIDB_CONFIG['host']}/{TIDB_CONFIG['database']}")
    except Exception as e:
        logger.error(f"Failed to connect to TiDB: {e}")
        exit(1)

    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting TiDB MCP Server on port {port}")
    logger.info(f"MCP endpoint: http://localhost:{port}/mcp")
    app.run(host='0.0.0.0', port=port)
