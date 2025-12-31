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
        "description": """Execute a SELECT query on the TiDB database. Only read-only queries are allowed.

⚠️ CRITICAL: Before writing SQL, you MUST read the schema guide at:
   Production/wiki/08_Database_Schema/TIDB_SCHEMA_GUIDE.md

This guide contains:
- Golden Rules (e.g., duplicate quantity field bug - use products.products_quantity NOT products_description.products_quantity)
- Table reference with business definitions
- Pre-written JOIN recipes for common queries
- Common mistakes to avoid

Key Rules to Remember:
✅ Use products.products_quantity for inventory (NOT products_description.products_quantity)
✅ Use orders_total WHERE class='ot_total' for revenue (NOT sum of orders_products)
✅ Always filter web_id=1 AND language_id=1 on description tables
""",
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
