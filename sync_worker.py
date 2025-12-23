#!/usr/bin/env python3
"""
TiDB Sync Worker - Automated MySQL to TiDB Cloud migration.
Runs as a Render Cron Job to sync IDrive e2 backups to TiDB Cloud.

Syncs both:
1. Categories/Products (~5.5 MB, ~2-3 min)
2. Orders/Customers (~112 MB, ~15-20 min)

All MySQL→TiDB compatibility fixes are applied automatically.
"""

import subprocess
import gzip
import pymysql
import sys
import os
import io
import re
import logging
from datetime import datetime
from pymysql.constants import CLIENT

# Configure logging for Render dashboard
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Environment variables (set in Render dashboard)
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

# Backup paths on IDrive
CATEGORIES_PRODUCTS_PATH = 'dbdaily/db/categories-products/'
ORDERS_PATH = 'dbdaily/db/orders/'


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
    """
    List files in IDrive bucket and return the latest backup filename.
    Files are named like: 2025-12-23-05-00-01_suppliesart1_maindb.sql.gz
    """
    logger.info(f"Finding latest backup in {bucket_path}...")

    args = get_rclone_base_args() + [
        'lsf', f':s3:{bucket_path}',
        '--files-only'
    ]

    result = subprocess.run(args, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"rclone lsf failed: {result.stderr}")
        return None

    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]

    if not files:
        logger.error(f"No files found in {bucket_path}")
        return None

    # Files are named with timestamp prefix, so sorting gives us chronological order
    # Pick the latest (last when sorted)
    files.sort()
    latest = files[-1]

    logger.info(f"Latest backup: {latest}")
    return latest


def apply_tidb_fixes(statement):
    """
    Apply all MySQL→TiDB compatibility fixes to a SQL statement.

    Fixes applied:
    1. Character set: utf8/latin1 → utf8mb4
    2. Invalid dates: 0000-00-00 → 1970-01-01
    3. Storage engine: MyISAM → InnoDB
    4. FULLTEXT indexes: removed
    5. Long composite keys: removed (idx_cust_email_pass)
    """
    # Convert character sets to utf8mb4
    # Use negative lookahead (?!mb) to avoid eating semicolons
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

    # Table-level charset/collate
    statement = re.sub(r"DEFAULT CHARSET=latin1\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT CHARSET=utf8(?!mb)", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DEFAULT CHARSET=utf8mb3\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"CHARSET\s*=\s*latin1\b", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"CHARSET\s*=\s*utf8(?!mb)", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
    statement = re.sub(r"COLLATE\s*=\s*latin1_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)
    statement = re.sub(r"COLLATE\s*=\s*utf8_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)

    # Fix invalid default dates (TiDB strict mode)
    statement = re.sub(
        r"NOT NULL DEFAULT '0000-00-00 00:00:00'",
        "NOT NULL DEFAULT '1970-01-01 00:00:01'",
        statement, flags=re.IGNORECASE
    )
    statement = re.sub(
        r"NOT NULL DEFAULT '0000-00-00'",
        "NOT NULL DEFAULT '1970-01-01'",
        statement, flags=re.IGNORECASE
    )
    statement = re.sub(
        r"DEFAULT '0000-00-00 00:00:00'",
        "DEFAULT NULL",
        statement, flags=re.IGNORECASE
    )
    statement = re.sub(
        r"DEFAULT '0000-00-00'",
        "DEFAULT NULL",
        statement, flags=re.IGNORECASE
    )

    # Replace MyISAM with InnoDB
    statement = re.sub(r"ENGINE\s*=\s*MyISAM", "ENGINE=InnoDB", statement, flags=re.IGNORECASE)

    # Remove FULLTEXT indexes (not supported by TiDB)
    if 'CREATE TABLE' in statement.upper() and 'FULLTEXT' in statement.upper():
        match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
        if match:
            table_name = match.group(1)
            lines = statement.split('\n')
            new_lines = [l for l in lines if 'FULLTEXT' not in l.upper()]
            statement = '\n'.join(new_lines)
            statement = re.sub(r',\s*\)', ')', statement)
            logger.info(f"Removed FULLTEXT index from {table_name}")

    # Remove long composite keys (TiDB max key length is 3072 bytes)
    if 'CREATE TABLE' in statement.upper():
        lines = statement.split('\n')
        new_lines = []
        for l in lines:
            if 'KEY `idx_cust_email_pass`' in l:
                logger.info("Removed long composite index idx_cust_email_pass")
                continue
            new_lines.append(l)
        statement = '\n'.join(new_lines)
        statement = re.sub(r',\s*\)', ')', statement)

    return statement


def stream_and_execute(bucket_path, filename, conn, cursor, dataset_name):
    """
    Stream SQL from IDrive through rclone, decompress, and execute on TiDB.

    Args:
        bucket_path: IDrive bucket path (e.g., 'dbdaily/db/orders/')
        filename: Backup filename to process
        conn: TiDB connection
        cursor: TiDB cursor
        dataset_name: Human-readable name for logging

    Returns:
        tuple: (statements_executed, errors)
    """
    full_path = f':s3:{bucket_path}{filename}'
    logger.info(f"Starting {dataset_name} sync from {filename}")

    # Start rclone stream
    args = get_rclone_base_args() + ['cat', full_path]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Decompress gzip stream
    decompressor = gzip.GzipFile(fileobj=proc.stdout)
    text_stream = io.TextIOWrapper(decompressor, encoding='utf-8', errors='replace')

    # Processing state
    statement_buffer = []
    statements_executed = 0
    errors = 0
    in_block_comment = False
    bytes_processed = 0

    for line in text_stream:
        bytes_processed += len(line.encode('utf-8'))
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Skip single-line comments
        if stripped.startswith('--') or stripped.startswith('#'):
            continue

        # Handle block comments (only at START of line, not in data values!)
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

        # Skip MySQL-specific commands
        if stripped.upper().startswith(('LOCK TABLES', 'UNLOCK TABLES')):
            continue

        # Add line to buffer
        statement_buffer.append(line.rstrip('\n\r'))

        # Check if statement is complete
        if stripped.endswith(';'):
            statement = '\n'.join(statement_buffer)
            statement_buffer = []

            # Apply TiDB compatibility fixes
            statement = apply_tidb_fixes(statement)

            # Log CREATE TABLE statements
            if 'CREATE TABLE' in statement.upper():
                match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
                table_name = match.group(1) if match else 'unknown'
                logger.info(f"Creating table: {table_name}")

            try:
                cursor.execute(statement)
                while cursor.nextset():
                    pass
                statements_executed += 1

                # Progress every 1000 statements
                if statements_executed % 1000 == 0:
                    mb = bytes_processed / (1024 * 1024)
                    logger.info(f"Progress: {statements_executed} statements (~{mb:.1f} MB)")

            except pymysql.Error as e:
                errors += 1
                error_code = e.args[0]
                # Only log non-duplicate key errors
                if error_code != 1062 and errors <= 20:
                    logger.warning(f"SQL Error [{error_code}]: {str(e)[:150]}")

    # Close streams
    proc.stdout.close()
    proc.wait()

    # Check for rclone errors
    stderr = proc.stderr.read().decode()
    if proc.returncode != 0 and stderr:
        logger.warning(f"rclone warning: {stderr[:200]}")

    logger.info(f"{dataset_name} complete: {statements_executed} statements, {errors} errors")
    return statements_executed, errors


def main():
    """Main entry point for the sync worker."""
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("TiDB Sync Worker Starting")
    logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 60)

    # Validate environment variables
    required_vars = ['TIDB_USER', 'TIDB_PASSWORD', 'IDRIVE_ACCESS_KEY', 'IDRIVE_SECRET_KEY', 'IDRIVE_ENDPOINT']
    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Connect to TiDB
    logger.info("Connecting to TiDB Cloud...")
    try:
        conn = pymysql.connect(**TIDB_CONFIG)
        cursor = conn.cursor()
        logger.info("Connected successfully!")
    except Exception as e:
        logger.error(f"Failed to connect to TiDB: {e}")
        sys.exit(1)

    total_statements = 0
    total_errors = 0

    # --- Sync Categories/Products ---
    logger.info("-" * 40)
    logger.info("PHASE 1: Categories/Products")
    logger.info("-" * 40)

    cat_file = get_latest_backup_file(CATEGORIES_PRODUCTS_PATH)
    if cat_file:
        stmts, errs = stream_and_execute(
            CATEGORIES_PRODUCTS_PATH, cat_file, conn, cursor,
            "Categories/Products"
        )
        total_statements += stmts
        total_errors += errs
    else:
        logger.error("Skipping Categories/Products: no backup file found")

    # --- Sync Orders ---
    logger.info("-" * 40)
    logger.info("PHASE 2: Orders/Customers")
    logger.info("-" * 40)

    orders_file = get_latest_backup_file(ORDERS_PATH)
    if orders_file:
        stmts, errs = stream_and_execute(
            ORDERS_PATH, orders_file, conn, cursor,
            "Orders/Customers"
        )
        total_statements += stmts
        total_errors += errs
    else:
        logger.error("Skipping Orders: no backup file found")

    # --- Summary ---
    logger.info("=" * 60)
    logger.info("SYNC COMPLETE")
    logger.info("=" * 60)

    # Show table counts
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    logger.info(f"Total tables in database: {len(tables)}")

    # Show order-related table counts
    order_tables = ['orders', 'orders_products', 'orders_total', 'orders_status_history', 'customers']
    for table_name in order_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]
            logger.info(f"  {table_name}: {count:,} rows")
        except:
            pass

    cursor.close()
    conn.close()

    # Final stats
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("-" * 40)
    logger.info(f"Total statements: {total_statements:,}")
    logger.info(f"Total errors: {total_errors}")
    logger.info(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    logger.info("=" * 60)

    # Exit with error if too many failures
    if total_errors > 100:
        logger.error("Too many errors, marking job as failed")
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Sync cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
