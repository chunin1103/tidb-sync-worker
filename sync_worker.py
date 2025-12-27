#!/usr/bin/env python3
"""
TiDB Unified Service - Sync Worker + MCP Server

Runs as a single Render Web Service providing:
1. Scheduled sync from IDrive e2 backups to TiDB Cloud (6 AM / 6 PM UTC)
2. MCP server for querying TiDB from Claude

Endpoints:
- GET  /         - Health check (combined status)
- GET  /status   - Detailed sync status and schedule
- POST /sync     - Trigger manual sync
- POST /mcp      - MCP endpoint for Claude
- GET  /tools    - List available MCP tools
- POST /query    - Direct query endpoint for testing
"""

import boto3
import gzip
import pymysql
import sys
import os
import io
import re
import json
import logging
import threading
from datetime import datetime, date
from decimal import Decimal
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pymysql.constants import CLIENT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# =============================================================================
# Configuration
# =============================================================================

# TiDB Configuration (shared by sync and MCP)
TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'port': int(os.environ.get('TIDB_PORT', 4000)),
    'user': os.environ.get('TIDB_USER', ''),
    'password': os.environ.get('TIDB_PASSWORD', ''),
    'database': os.environ.get('TIDB_DATABASE', 'test'),
    'ssl': {'ssl': {'ca': None}},
    'autocommit': True,
    'charset': 'utf8mb4'
}

# IDrive/S3 Configuration
IDRIVE_ACCESS_KEY = os.environ.get('IDRIVE_ACCESS_KEY', '')
IDRIVE_SECRET_KEY = os.environ.get('IDRIVE_SECRET_KEY', '')
IDRIVE_ENDPOINT = os.environ.get('IDRIVE_ENDPOINT', '')
S3_BUCKET = os.environ.get('IDRIVE_BUCKET', 'dbdaily')
CATEGORIES_PRODUCTS_PREFIX = 'db/categories-products/'
ORDERS_PREFIX = 'db/orders/'

# MCP Configuration
MAX_ROWS = int(os.environ.get('MAX_QUERY_ROWS', 1000))

# Sync state tracking
sync_state = {
    'last_run': None,
    'last_status': 'never_run',
    'last_duration': None,
    'last_statements': 0,
    'last_errors': 0,
    'is_running': False,
    'current_phase': None
}
sync_lock = threading.Lock()


# =============================================================================
# Database Helpers
# =============================================================================

def get_sync_connection():
    """Get connection for sync operations (with MULTI_STATEMENTS)."""
    config = TIDB_CONFIG.copy()
    config['client_flag'] = CLIENT.MULTI_STATEMENTS
    return pymysql.connect(**config)


def get_query_connection():
    """Get connection for MCP queries (with DictCursor)."""
    config = TIDB_CONFIG.copy()
    config['cursorclass'] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)


def json_serial(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    raise TypeError(f"Type {type(obj)} not serializable")


# =============================================================================
# Sync Worker Functions
# =============================================================================

def get_s3_client():
    """Get boto3 S3 client configured for IDrive e2."""
    return boto3.client(
        's3',
        endpoint_url=IDRIVE_ENDPOINT,
        aws_access_key_id=IDRIVE_ACCESS_KEY,
        aws_secret_access_key=IDRIVE_SECRET_KEY
    )


def get_latest_backup_file(prefix):
    """List files in IDrive bucket and return the latest backup filename.

    Uses pagination to handle buckets with more than 1000 files.
    """
    logger.info(f"Finding latest backup in {S3_BUCKET}/{prefix}...")

    try:
        s3 = get_s3_client()

        # Use paginator to handle >1000 files
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix)

        files = []
        page_count = 0
        for page in pages:
            page_count += 1
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.sql.gz'):
                        files.append(obj['Key'])

        logger.info(f"Scanned {page_count} page(s), found {len(files)} backup files")

        if not files:
            logger.error(f"No .sql.gz files found in {S3_BUCKET}/{prefix}")
            return None

        files.sort()
        latest_key = files[-1]
        latest_filename = latest_key.split('/')[-1]
        logger.info(f"Latest backup: {latest_filename}")
        return latest_key

    except Exception as e:
        logger.error(f"Failed to list S3 objects: {e}")
        return None


def apply_tidb_fixes(statement):
    """Apply all MySQL to TiDB compatibility fixes."""
    # Character sets
    statement = re.sub(
        r"CHARACTER SET latin1\s+COLLATE\s+latin1_\w+",
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci",
        statement, flags=re.IGNORECASE
    )
    statement = re.sub(
        r"CHARACTER SET utf8\s+COLLATE\s+utf8_\w+",
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci",
        statement, flags=re.IGNORECASE
    )
    statement = re.sub(
        r"CHARACTER SET utf8mb3\s+COLLATE\s+utf8mb3_\w+",
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci",
        statement, flags=re.IGNORECASE
    )

    statement = re.sub(r"DEFAULT CHARSET=latin1\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT CHARSET=utf8(?!mb)", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT CHARSET=utf8mb3\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"CHARSET\s*=\s*latin1\b", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"CHARSET\s*=\s*utf8(?!mb)", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"COLLATE\s*=\s*latin1_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)
    statement = re.sub(r"COLLATE\s*=\s*utf8_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)

    # Invalid dates
    statement = re.sub(r"NOT NULL DEFAULT '0000-00-00 00:00:00'", "NOT NULL DEFAULT '1970-01-01 00:00:01'", statement, flags=re.IGNORECASE)
    statement = re.sub(r"NOT NULL DEFAULT '0000-00-00'", "NOT NULL DEFAULT '1970-01-01'", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT '0000-00-00 00:00:00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT '0000-00-00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)

    # Storage engine
    statement = re.sub(r"ENGINE\s*=\s*MyISAM", "ENGINE=InnoDB", statement, flags=re.IGNORECASE)

    # FULLTEXT indexes
    if 'CREATE TABLE' in statement.upper() and 'FULLTEXT' in statement.upper():
        match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            lines = statement.split('\n')
            new_lines = [l for l in lines if 'FULLTEXT' not in l.upper()]
            statement = '\n'.join(new_lines)
            statement = re.sub(r',\s*\)', ')', statement)
            logger.info(f"Removed FULLTEXT index from {table_name}")

    # Long composite keys
    if 'CREATE TABLE' in statement.upper():
        lines = statement.split('\n')
        new_lines = [l for l in lines if 'KEY `idx_cust_email_pass`' not in l]
        if len(new_lines) != len(lines):
            logger.info("Removed long composite index idx_cust_email_pass")
        statement = '\n'.join(new_lines)
        statement = re.sub(r',\s*\)', ')', statement)

    return statement


def stream_and_execute(s3_key, conn, cursor, dataset_name):
    """Stream SQL from IDrive S3, decompress, and execute on TiDB."""
    global sync_state

    filename = s3_key.split('/')[-1]
    logger.info(f"Starting {dataset_name} sync from {filename}")
    sync_state['current_phase'] = dataset_name

    s3 = get_s3_client()
    response = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)

    decompressor = gzip.GzipFile(fileobj=response['Body'])
    text_stream = io.TextIOWrapper(decompressor, encoding='utf-8', errors='replace')

    statement_buffer = []
    statements_executed = 0
    errors = 0
    in_block_comment = False
    bytes_processed = 0

    for line in text_stream:
        bytes_processed += len(line.encode('utf-8'))
        stripped = line.strip()

        if not stripped:
            continue
        if stripped.startswith('--') or stripped.startswith('#'):
            continue

        if stripped.startswith('/*') and not stripped.startswith('/*!'):
            if '*/' not in stripped:
                in_block_comment = True
                continue
            elif stripped.endswith('*/'):
                continue
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue

        if stripped.upper().startswith(('LOCK TABLES', 'UNLOCK TABLES')):
            continue

        statement_buffer.append(line.rstrip('\n\r'))

        if stripped.endswith(';'):
            statement = '\n'.join(statement_buffer)
            statement_buffer = []
            statement = apply_tidb_fixes(statement)

            if 'CREATE TABLE' in statement.upper():
                match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
                table_name = match.group(1) if match else 'unknown'
                logger.info(f"Creating table: {table_name}")

            try:
                cursor.execute(statement)
                while cursor.nextset():
                    pass
                statements_executed += 1

                if statements_executed % 1000 == 0:
                    mb = bytes_processed / (1024 * 1024)
                    logger.info(f"Progress: {statements_executed} statements (~{mb:.1f} MB)")

            except pymysql.Error as e:
                errors += 1
                if e.args[0] != 1062 and errors <= 20:
                    logger.warning(f"SQL Error [{e.args[0]}]: {str(e)[:150]}")

    logger.info(f"{dataset_name} complete: {statements_executed} statements, {errors} errors")
    return statements_executed, errors


def run_sync():
    """Main sync function - called by scheduler or manually."""
    global sync_state

    with sync_lock:
        if sync_state['is_running']:
            logger.warning("Sync already in progress, skipping")
            return {'status': 'skipped', 'reason': 'already_running'}
        sync_state['is_running'] = True

    start_time = datetime.utcnow()
    logger.info("=" * 60)
    logger.info("TiDB Sync Starting")
    logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 60)

    total_statements = 0
    total_errors = 0
    status = 'success'

    try:
        logger.info("Connecting to TiDB Cloud...")
        conn = get_sync_connection()
        cursor = conn.cursor()
        logger.info("Connected!")

        # Sync Categories/Products
        logger.info("-" * 40)
        logger.info("PHASE 1: Categories/Products")
        cat_key = get_latest_backup_file(CATEGORIES_PRODUCTS_PREFIX)
        if cat_key:
            stmts, errs = stream_and_execute(cat_key, conn, cursor, "Categories/Products")
            total_statements += stmts
            total_errors += errs

        # Sync Orders
        logger.info("-" * 40)
        logger.info("PHASE 2: Orders/Customers")
        orders_key = get_latest_backup_file(ORDERS_PREFIX)
        if orders_key:
            stmts, errs = stream_and_execute(orders_key, conn, cursor, "Orders/Customers")
            total_statements += stmts
            total_errors += errs

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        logger.info(f"Total tables: {len(tables)}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        status = 'failed'
        total_errors += 1

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    with sync_lock:
        sync_state['last_run'] = end_time.isoformat() + 'Z'
        sync_state['last_status'] = status
        sync_state['last_duration'] = f"{duration:.1f}s"
        sync_state['last_statements'] = total_statements
        sync_state['last_errors'] = total_errors
        sync_state['is_running'] = False
        sync_state['current_phase'] = None

    logger.info("=" * 60)
    logger.info(f"SYNC COMPLETE - {status.upper()}")
    logger.info(f"Statements: {total_statements}, Errors: {total_errors}, Duration: {duration:.1f}s")
    logger.info("=" * 60)

    return {
        'status': status,
        'statements': total_statements,
        'errors': total_errors,
        'duration': f"{duration:.1f}s"
    }


# =============================================================================
# MCP Server Functions
# =============================================================================

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
        "name": "today_orders",
        "description": "Get all orders placed today with count and summary",
        "inputSchema": {
            "type": "object",
            "properties": {}
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


def execute_query(sql, params=None):
    """Execute a SQL query and return results."""
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('SHOW') and not sql_upper.startswith('DESCRIBE'):
        return {'error': 'Only SELECT, SHOW, and DESCRIBE queries are allowed'}

    try:
        conn = get_query_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchmany(MAX_ROWS)

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


def handle_tool_call(tool_name, arguments):
    """Handle a tool call and return the result."""

    if tool_name == "query":
        sql = arguments.get("sql", "")
        result = execute_query(sql)
        return json.dumps(result, default=json_serial)

    elif tool_name == "list_tables":
        result = execute_query("SHOW TABLES")
        if 'rows' in result:
            tables = [list(row.values())[0] for row in result['rows']]
            return json.dumps({'tables': tables, 'count': len(tables)})
        return json.dumps(result)

    elif tool_name == "describe_table":
        table_name = arguments.get("table_name", "")
        if not table_name.replace('_', '').isalnum():
            return json.dumps({'error': 'Invalid table name'})
        result = execute_query(f"DESCRIBE `{table_name}`")
        return json.dumps(result, default=json_serial)

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

    elif tool_name == "today_orders":
        # Get count and list of today's orders
        count_sql = """
            SELECT COUNT(*) as order_count
            FROM orders
            WHERE DATE(date_purchased) = CURDATE()
        """
        count_result = execute_query(count_sql)

        orders_sql = """
            SELECT orders_id, customers_name, customers_email_address,
                   date_purchased, orders_status, billing_city, billing_state
            FROM orders
            WHERE DATE(date_purchased) = CURDATE()
            ORDER BY date_purchased DESC
        """
        orders_result = execute_query(orders_sql)

        return json.dumps({
            'today': datetime.now().strftime('%Y-%m-%d'),
            'order_count': count_result.get('rows', [{}])[0].get('order_count', 0) if count_result.get('rows') else 0,
            'orders': orders_result.get('rows', [])
        }, default=json_serial)

    elif tool_name == "order_details":
        order_id = arguments.get("order_id")
        if not order_id:
            return json.dumps({'error': 'order_id is required'})

        order_result = execute_query(
            "SELECT * FROM orders WHERE orders_id = %s",
            (order_id,)
        )

        products_result = execute_query(
            """SELECT op.*, p.products_model
               FROM orders_products op
               LEFT JOIN products p ON op.products_id = p.products_id
               WHERE op.orders_id = %s""",
            (order_id,)
        )

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
# Flask Routes - Combined
# =============================================================================

@app.route('/')
def health():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'service': 'tidb-unified',
        'features': {
            'sync_worker': True,
            'mcp_server': True
        },
        'sync_status': sync_state['last_status'],
        'is_syncing': sync_state['is_running'],
        'database': TIDB_CONFIG['database']
    })


@app.route('/status')
def status():
    """Get detailed sync status."""
    scheduler_jobs = []
    for job in scheduler.get_jobs():
        scheduler_jobs.append({
            'id': job.id,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None
        })

    return jsonify({
        'sync_state': sync_state,
        'scheduled_jobs': scheduler_jobs,
        'environment': {
            'tidb_host': TIDB_CONFIG['host'],
            'tidb_database': TIDB_CONFIG['database'],
            'idrive_endpoint': IDRIVE_ENDPOINT,
            's3_bucket': S3_BUCKET
        }
    })


@app.route('/sync', methods=['POST'])
def trigger_sync():
    """Manually trigger a sync."""
    if sync_state['is_running']:
        return jsonify({
            'status': 'error',
            'message': 'Sync already in progress',
            'current_phase': sync_state['current_phase']
        }), 409

    thread = threading.Thread(target=run_sync)
    thread.start()

    return jsonify({
        'status': 'started',
        'message': 'Sync started in background. Check /status for progress.'
    })


@app.route('/sync', methods=['GET'])
def sync_info():
    """Info about the sync endpoint."""
    return jsonify({
        'message': 'Use POST /sync to trigger a manual sync',
        'last_run': sync_state['last_run'],
        'last_status': sync_state['last_status']
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

        logger.info(f"MCP request: method={method}, id={request_id}")

        if method == 'initialize':
            response = {
                'protocolVersion': '2024-11-05',
                'capabilities': {
                    'tools': {}
                },
                'serverInfo': {
                    'name': 'tidb-mcp-server',
                    'version': '1.0.0'
                }
            }

        elif method == 'notifications/initialized' or method == 'initialized':
            # Notification - no response needed, return empty success
            return jsonify({
                'jsonrpc': '2.0',
                'result': {},
                'id': request_id
            })

        elif method == 'tools/list':
            response = {'tools': MCP_TOOLS}

        elif method == 'tools/call':
            tool_name = params.get('name')
            arguments = params.get('arguments', {})
            logger.info(f"Tool call: {tool_name} with args: {arguments}")

            result = handle_tool_call(tool_name, arguments)

            response = {
                'content': [
                    {
                        'type': 'text',
                        'text': result
                    }
                ]
            }

        elif method == 'ping':
            response = {}

        elif method == 'resources/list':
            # No resources, return empty list
            response = {'resources': []}

        elif method == 'prompts/list':
            # No prompts, return empty list
            response = {'prompts': []}

        else:
            # Return error but with 200 status (JSON-RPC errors shouldn't be HTTP errors)
            logger.warning(f"Unknown MCP method: {method}")
            return jsonify({
                'jsonrpc': '2.0',
                'error': {'code': -32601, 'message': f'Method not found: {method}'},
                'id': request_id
            })

        return jsonify({
            'jsonrpc': '2.0',
            'result': response,
            'id': request_id
        })

    except Exception as e:
        logger.error(f"MCP error: {e}")
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32603, 'message': str(e)},
            'id': request.get_json().get('id') if request.get_json() else None
        }), 500


@app.route('/tools', methods=['GET'])
def list_tools():
    """List available MCP tools."""
    return jsonify({'tools': MCP_TOOLS})


@app.route('/query', methods=['POST'])
def direct_query():
    """Direct query endpoint for testing."""
    data = request.get_json()
    sql = data.get('sql', '')
    result = execute_query(sql)
    return jsonify(result)


# =============================================================================
# Scheduler Setup
# =============================================================================

scheduler = BackgroundScheduler()


def scheduled_sync():
    """Wrapper for scheduled sync runs."""
    logger.info("Scheduled sync triggered")
    run_sync()


# Schedule at 6 AM and 6 PM UTC
scheduler.add_job(
    scheduled_sync,
    CronTrigger(hour=6, minute=0),
    id='sync_6am',
    name='Daily sync at 6 AM UTC'
)
scheduler.add_job(
    scheduled_sync,
    CronTrigger(hour=18, minute=0),
    id='sync_6pm',
    name='Daily sync at 6 PM UTC'
)


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    # Validate environment for sync
    sync_vars = ['TIDB_USER', 'TIDB_PASSWORD', 'IDRIVE_ACCESS_KEY', 'IDRIVE_SECRET_KEY', 'IDRIVE_ENDPOINT']
    missing_sync = [v for v in sync_vars if not os.environ.get(v)]

    # Minimum required for MCP (TiDB only)
    mcp_vars = ['TIDB_USER', 'TIDB_PASSWORD']
    missing_mcp = [v for v in mcp_vars if not os.environ.get(v)]

    if missing_mcp:
        logger.error(f"Missing required environment variables: {', '.join(missing_mcp)}")
        sys.exit(1)

    if missing_sync:
        logger.warning(f"Sync disabled - missing: {', '.join(missing_sync)}")
        logger.info("MCP server will run, but scheduled syncs will fail")
    else:
        # Start scheduler only if sync is fully configured
        scheduler.start()
        logger.info("Scheduler started - syncs at 6 AM and 6 PM UTC")
        for job in scheduler.get_jobs():
            logger.info(f"  {job.name}: next run at {job.next_run_time}")

    # Test TiDB connection
    try:
        conn = get_query_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        logger.info(f"Connected to TiDB: {TIDB_CONFIG['host']}/{TIDB_CONFIG['database']}")
    except Exception as e:
        logger.error(f"Failed to connect to TiDB: {e}")
        sys.exit(1)

    # Start Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting TiDB Unified Service on port {port}")
    logger.info(f"Endpoints:")
    logger.info(f"  Health:     http://localhost:{port}/")
    logger.info(f"  Status:     http://localhost:{port}/status")
    logger.info(f"  Sync:       http://localhost:{port}/sync")
    logger.info(f"  MCP:        http://localhost:{port}/mcp")
    logger.info(f"  Tools:      http://localhost:{port}/tools")
    app.run(host='0.0.0.0', port=port)
