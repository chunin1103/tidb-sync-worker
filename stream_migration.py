#!/usr/bin/env python3
"""
Stream Categories/Products SQL dump from IDrive e2 directly to TiDB Cloud.
No local storage required - data flows through memory only.

KEY COMPATIBILITY FIXES APPLIED (MySQL → TiDB):
1. Character Set: Convert utf8/latin1 to utf8mb4 using (?!mb) lookahead
   - WRONG: utf8[^m] - eats semicolons and breaks parsing!
   - RIGHT: utf8(?!mb) - negative lookahead preserves following chars

2. Block Comments: Only detect at START of line, not anywhere in data
   - WRONG: if '/*' in stripped - matches /* in INSERT data values
   - RIGHT: if stripped.startswith('/*') - only matches real comments

3. Invalid Dates: Replace 0000-00-00 with 1970-01-01 (TiDB strict mode)

4. FULLTEXT Indexes: Remove (not supported by TiDB)

5. Storage Engine: Convert MyISAM to InnoDB

See MIGRATION_INSTRUCTIONS.md for full documentation.
"""

import subprocess
import gzip
import pymysql
import sys
import io
import re
from pymysql.constants import CLIENT

# Configuration
RCLONE_PATH = r"C:\Users\tnguyen24_mantu\AppData\Local\Microsoft\WinGet\Packages\Rclone.Rclone_Microsoft.Winget.Source_8wekyb3d8bbwe\rclone-v1.72.1-windows-amd64\rclone.exe"
IDRIVE_FILE = "idrive:dbdaily/db/categories-products/2025-12-22-05-00-02_suppliesart1_maindb_categories-products.sql.gz"

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

def stream_and_execute():
    """Stream SQL from IDrive through rclone, decompress, and execute on TiDB."""

    print(f"[1/4] Connecting to TiDB Cloud...")
    conn = pymysql.connect(**TIDB_CONFIG)
    cursor = conn.cursor()
    print("       Connected!")

    print(f"[2/4] Starting rclone stream from IDrive...")
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

            # Convert unsupported collations and charsets to utf8mb4
            # Use negative lookahead (?!mb) to avoid eating semicolons
            statement = re.sub(r"CHARACTER SET latin1\s+COLLATE\s+latin1_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARACTER SET utf8\s+COLLATE\s+utf8_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARACTER SET utf8mb3\s+COLLATE\s+utf8mb3_\w+", "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement, flags=re.IGNORECASE)

            # Handle standalone charset/collate at table level
            statement = re.sub(r"DEFAULT CHARSET=latin1\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT CHARSET=utf8(?!mb)", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT CHARSET=utf8mb3\b", "DEFAULT CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARSET\s*=\s*latin1\b", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"CHARSET\s*=\s*utf8(?!mb)", "CHARSET=utf8mb4", statement, flags=re.IGNORECASE)
            statement = re.sub(r"COLLATE\s*=\s*latin1_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)
            statement = re.sub(r"COLLATE\s*=\s*utf8_\w+", "COLLATE=utf8mb4_general_ci", statement, flags=re.IGNORECASE)

            # Fix invalid default dates (TiDB strict mode)
            statement = re.sub(r"NOT NULL DEFAULT '0000-00-00 00:00:00'", "NOT NULL DEFAULT '1970-01-01 00:00:01'", statement, flags=re.IGNORECASE)
            statement = re.sub(r"NOT NULL DEFAULT '0000-00-00'", "NOT NULL DEFAULT '1970-01-01'", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT '0000-00-00 00:00:00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)
            statement = re.sub(r"DEFAULT '0000-00-00'", "DEFAULT NULL", statement, flags=re.IGNORECASE)

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
                    print(f"\n       Note: Removed FULLTEXT index from {table_name}")

            # Debug: show CREATE TABLE statements
            if 'CREATE TABLE' in statement.upper():
                match = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
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
                if error_code != 1062 and errors <= 15:  # Skip duplicate key errors
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
    print(f"       Tables in database: {len(tables)}")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM `{table[0]}`")
        count = cursor.fetchone()[0]
        print(f"         - {table[0]}: {count:,} rows")

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
