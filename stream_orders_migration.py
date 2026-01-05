#!/usr/bin/env python3
"""
Stream Orders SQL dump from IDrive e2 directly to TiDB Cloud.
Handles larger files with progress tracking.

KEY COMPATIBILITY FIXES APPLIED (MySQL → TiDB):
1. Character Set: Convert utf8/latin1 to utf8mb4 using (?!mb) lookahead
   - WRONG: utf8[^m] - eats semicolons and breaks parsing!
   - RIGHT: utf8(?!mb) - negative lookahead preserves following chars

2. Block Comments: Only detect at START of line, not anywhere in data
   - WRONG: if '/*' in stripped - matches /* in INSERT data values
   - RIGHT: if stripped.startswith('/*') - only matches real comments

3. Invalid Dates: Replace 0000-00-00 with 1970-01-01 (TiDB strict mode)

4. FULLTEXT Indexes: Remove (not supported by TiDB)

5. Long Composite Keys: Remove indexes exceeding 3072 bytes (TiDB limit)

6. Storage Engine: Convert MyISAM to InnoDB

See MIGRATION_INSTRUCTIONS.md for full documentation.
"""

import subprocess
import gzip
import pymysql
import sys
import io
from pymysql.constants import CLIENT

# Configuration
RCLONE_PATH = r"C:\Users\tnguyen24_mantu\AppData\Local\Microsoft\WinGet\Packages\Rclone.Rclone_Microsoft.Winget.Source_8wekyb3d8bbwe\rclone-v1.72.1-windows-amd64\rclone.exe"
IDRIVE_FILE = "idrive:dbdaily/db/orders/2025-12-22-08-00-01_suppliesart1_maindb.sql.gz"

TIDB_CONFIG = {
    'host': 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3oTjjLfAngfGpch.root',
    'password': 'Ke6VLVqBBr9REemt',
    'database': 'test',
    'ssl': {'ssl': {'ca': None}},
    'autocommit': True,
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS
}

# Tables with FULLTEXT indexes that need modification
FULLTEXT_TABLES = set()

def stream_and_execute():
    """Stream SQL from IDrive through rclone, decompress, and execute on TiDB."""

    print(f"[1/4] Connecting to TiDB Cloud...")
    conn = pymysql.connect(**TIDB_CONFIG)
    cursor = conn.cursor()
    print("       Connected!")

    print(f"[2/4] Starting rclone stream from IDrive (117 MB compressed)...")
    proc = subprocess.Popen(
        [RCLONE_PATH, 'cat', IDRIVE_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    print(f"[3/4] Decompressing and executing SQL statements...")

    # Decompress gzip stream
    decompressor = gzip.GzipFile(fileobj=proc.stdout)

    # Buffer for multi-line SQL statements
    statement_buffer = []
    statements_executed = 0
    errors = 0
    skipped_tables = set()
    in_block_comment = False
    bytes_processed = 0

    # Read and process line by line (streaming)
    text_stream = io.TextIOWrapper(decompressor, encoding='utf-8', errors='replace')

    for line in text_stream:
        bytes_processed += len(line.encode('utf-8'))

        # Skip empty lines
        stripped = line.strip()
        if not stripped:
            continue

        # Skip single-line comments
        if stripped.startswith('--') or stripped.startswith('#'):
            continue

        # Handle block comments (only at start of line, not in data values)
        if stripped.startswith('/*') and not stripped.startswith('/*!'):
            if '*/' not in stripped:
                in_block_comment = True
                continue
            elif stripped.endswith('*/'):
                # Single-line block comment like /* comment */
                continue
        if in_block_comment:
            if '*/' in stripped:
                in_block_comment = False
            continue

        # Skip MySQL-specific commands that TiDB might not support
        if stripped.upper().startswith(('LOCK TABLES', 'UNLOCK TABLES')):
            continue

        # Add line to buffer
        statement_buffer.append(line.rstrip('\n\r'))

        # Check if statement is complete (ends with semicolon)
        if stripped.endswith(';'):
            statement = '\n'.join(statement_buffer)
            statement_buffer = []

            import re

            # Convert unsupported collations and charsets to utf8mb4
            # Handle inline column definitions: CHARACTER SET latin1 COLLATE latin1_swedish_ci
            statement = re.sub(r"CHARACTER SET latin1\s+COLLATE\s+latin1_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARACTER SET utf8\s+COLLATE\s+utf8_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARACTER SET utf8mb3\s+COLLATE\s+utf8mb3_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)

            # Handle standalone charset/collate at table level
            # Use word boundary or lookahead to avoid eating semicolons
            statement = re.sub(r"DEFAULT CHARSET=latin1\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT CHARSET=utf8(?!mb)", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT CHARSET=utf8mb3\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARSET\s*=\s*latin1\b", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARSET\s*=\s*utf8(?!mb)", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"COLLATE\s*=\s*latin1_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"COLLATE\s*=\s*utf8_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)

            # Fix invalid default dates (TiDB strict mode)
            # For NOT NULL columns, use epoch; for nullable, use NULL
            statement = re.sub(r"NOT NULL DEFAULT '0000-00-00 00:00:00'", "NOT NULL DEFAULT '1970-01-01 00:00:01'", statement, flags=re.IGNORECASE)
            statement = re.sub(r"NOT NULL DEFAULT '0000-00-00'", "NOT NULL DEFAULT '1970-01-01'", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT '0000-00-00 00:00:00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT '0000-00-00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)

            # Replace MyISAM with InnoDB (TiDB uses InnoDB-compatible storage)
            statement = re.sub(r"ENGINE\s*=\s*MyISAM", "ENGINE=InnoDB", statement, flags=re.IGNORECASE)

            # Check for FULLTEXT index in CREATE TABLE
            if 'CREATE TABLE' in statement.upper() and 'FULLTEXT' in statement.upper():
                # Extract table name
                match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    # Remove FULLTEXT index lines
                    lines = statement.split('\n')
                    new_lines = [l for l in lines if 'FULLTEXT' not in l.upper()]
                    # Fix trailing comma issues
                    statement = '\n'.join(new_lines)
                    # Remove trailing comma before closing paren
                    statement = re.sub(r',\s*\)', ')', statement)
                    skipped_tables.add(table_name)
                    print(f"\n       Note: Removed FULLTEXT index from {table_name}")

            # Fix long composite indexes (TiDB max key length is 3072 bytes)
            # This typically affects indexes on multiple varchar columns when using utf8mb4
            if 'CREATE TABLE' in statement.upper():
                # Remove problematic composite indexes that would exceed key length
                # Pattern: KEY `idx_name` (`col1`,`col2`,...) with long varchar combinations
                lines = statement.split('\n')
                new_lines = []
                for l in lines:
                    # Skip KEY lines with multiple columns and long field names that might exceed limit
                    # Specifically for customers table which has a composite key issue
                    if 'KEY `idx_cust_email_pass`' in l:
                        print(f"\n       Note: Removed long composite index idx_cust_email_pass")
                        continue
                    new_lines.append(l)
                statement = '\n'.join(new_lines)
                # Fix trailing comma before closing paren
                statement = re.sub(r',\s*\)', ')', statement)

            # Debug: show CREATE TABLE statements
            if 'CREATE TABLE' in statement.upper():
                import re as re2
                match = re2.search(r'CREATE TABLE `?(\w+)`?', statement, re2.IGNORECASE)
                table_name = match.group(1) if match else 'unknown'
                print(f"\n       Creating table: {table_name}...", end='')

            try:
                cursor.execute(statement)
                # Consume all result sets for multi-statement
                while cursor.nextset():
                    pass
                statements_executed += 1

                if 'CREATE TABLE' in statement.upper():
                    print(" OK")

                # Progress indicator (every 500 statements)
                elif statements_executed % 500 == 0:
                    mb_processed = bytes_processed / (1024 * 1024)
                    print(f"       Executed {statements_executed} statements (~{mb_processed:.1f} MB processed)...", end='\r')

            except pymysql.Error as e:
                errors += 1
                error_code = e.args[0]
                # Only show non-duplicate key errors (1062) in detail
                if error_code != 1062 and errors <= 15:
                    print(f"\n       Error [{error_code}]: {str(e)[:150]}")
                    if 'CREATE TABLE' in statement.upper():
                        print(f"       Statement preview: {statement[:200]}...")

    # Close streams
    proc.stdout.close()
    proc.wait()

    # Check for rclone errors
    stderr = proc.stderr.read().decode()
    if proc.returncode != 0 and stderr:
        print(f"\n       rclone warning: {stderr[:200]}")

    print(f"\n[4/4] Migration complete!")
    print(f"       Statements executed: {statements_executed}")
    print(f"       Errors: {errors}")

    # Show final table count
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"       Total tables in database: {len(tables)}")

    # Count new tables (orders-related)
    order_tables = [t[0] for t in tables if 'order' in t[0].lower()]
    print(f"\n       Order-related tables:")
    for table in sorted(order_tables):
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        count = cursor.fetchone()[0]
        print(f"         - {table}: {count:,} rows")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        stream_and_execute()
    except KeyboardInterrupt:
        print("\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
