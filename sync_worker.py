#!/usr/bin/env python3
"""
TiDB Sync Worker - Web Service with Built-in Scheduler

Runs as a Render Web Service with APScheduler to automatically sync
IDrive e2 backups to TiDB Cloud at 6 AM and 6 PM UTC daily.

Endpoints:
- GET /         - Health check (keeps Render happy)
- GET /status   - Show last sync status and next scheduled run
- POST /sync    - Trigger manual sync
"""

import subprocess
import gzip
import pymysql
import sys
import os
import io
import re
import logging
import threading
from datetime import datetime
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

# Environment variables
TIDB_CONFIG = {
    'host': os.environ.get('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
    'port': int(os.environ.get('TIDB_PORT', 4000)),
    'user': os.environ.get('TIDB_USER', ''),
    'password': os.environ.get('TIDB_PASSWORD', ''),
    'database': os.environ.get('TIDB_DATABASE', 'test'),
    'ssl': {'ssl': {'ca': None}},
    'autocommit': True,
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS
}

IDRIVE_ACCESS_KEY = os.environ.get('IDRIVE_ACCESS_KEY', '')
IDRIVE_SECRET_KEY = os.environ.get('IDRIVE_SECRET_KEY', '')
IDRIVE_ENDPOINT = os.environ.get('IDRIVE_ENDPOINT', '')

CATEGORIES_PRODUCTS_PATH = 'dbdaily/db/categories-products/'
ORDERS_PATH = 'dbdaily/db/orders/'


# =============================================================================
# Core Sync Functions
# =============================================================================

def get_rclone_base_args():
    """Get base rclone arguments with S3 credentials."""
    return [
        'rclone',
        '--s3-provider=Other',
        f'--s3-access-key-id={IDRIVE_ACCESS_KEY}',
        f'--s3-secret-access-key={IDRIVE_SECRET_KEY}',
        f'--s3-endpoint={IDRIVE_ENDPOINT}'
    ]


def get_latest_backup_file(bucket_path):
    """List files in IDrive bucket and return the latest backup filename."""
    logger.info(f"Finding latest backup in {bucket_path}...")

    args = get_rclone_base_args() + ['lsf', f':s3:{bucket_path}', '--files-only']
    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"rclone lsf failed: {result.stderr}")
        return None

    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    if not files:
        logger.error(f"No files found in {bucket_path}")
        return None

    files.sort()
    latest = files[-1]
    logger.info(f"Latest backup: {latest}")
    return latest


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


def stream_and_execute(bucket_path, filename, conn, cursor, dataset_name):
    """Stream SQL from IDrive, decompress, and execute on TiDB."""
    global sync_state

    full_path = f':s3:{bucket_path}{filename}'
    logger.info(f"Starting {dataset_name} sync from {filename}")
    sync_state['current_phase'] = dataset_name

    args = get_rclone_base_args() + ['cat', full_path]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    decompressor = gzip.GzipFile(fileobj=proc.stdout)
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

    proc.stdout.close()
    proc.wait()

    stderr = proc.stderr.read().decode()
    if proc.returncode != 0 and stderr:
        logger.warning(f"rclone warning: {stderr[:200]}")

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
        # Connect to TiDB
        logger.info("Connecting to TiDB Cloud...")
        conn = pymysql.connect(**TIDB_CONFIG)
        cursor = conn.cursor()
        logger.info("Connected!")

        # Sync Categories/Products
        logger.info("-" * 40)
        logger.info("PHASE 1: Categories/Products")
        cat_file = get_latest_backup_file(CATEGORIES_PRODUCTS_PATH)
        if cat_file:
            stmts, errs = stream_and_execute(CATEGORIES_PRODUCTS_PATH, cat_file, conn, cursor, "Categories/Products")
            total_statements += stmts
            total_errors += errs

        # Sync Orders
        logger.info("-" * 40)
        logger.info("PHASE 2: Orders/Customers")
        orders_file = get_latest_backup_file(ORDERS_PATH)
        if orders_file:
            stmts, errs = stream_and_execute(ORDERS_PATH, orders_file, conn, cursor, "Orders/Customers")
            total_statements += stmts
            total_errors += errs

        # Summary
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

    # Update state
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
# Flask Routes
# =============================================================================

@app.route('/')
def health():
    """Health check endpoint for Render."""
    return jsonify({
        'status': 'healthy',
        'service': 'tidb-sync-worker',
        'sync_status': sync_state['last_status'],
        'is_running': sync_state['is_running']
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
            'idrive_endpoint': IDRIVE_ENDPOINT
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

    # Run sync in background thread
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
    # Validate environment
    required_vars = ['TIDB_USER', 'TIDB_PASSWORD', 'IDRIVE_ACCESS_KEY', 'IDRIVE_SECRET_KEY', 'IDRIVE_ENDPOINT']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started - syncs at 6 AM and 6 PM UTC")

    # Show next run times
    for job in scheduler.get_jobs():
        logger.info(f"  {job.name}: next run at {job.next_run_time}")

    # Start Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting web server on port {port}")
    app.run(host='0.0.0.0', port=port)
