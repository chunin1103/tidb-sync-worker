#!/usr/bin/env python3
"""Import only products_description data from the SQL dump."""

import subprocess
import gzip
import pymysql
import io

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
    'charset': 'utf8mb4'
}

print("Connecting to TiDB...")
conn = pymysql.connect(**TIDB_CONFIG)
cursor = conn.cursor()

print("Streaming from IDrive...")
proc = subprocess.Popen([RCLONE_PATH, 'cat', IDRIVE_FILE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
decompressor = gzip.GzipFile(fileobj=proc.stdout)
text_stream = io.TextIOWrapper(decompressor, encoding='utf-8', errors='replace')

# Find and execute INSERT statements for products_description
statement_buffer = []
inserts_executed = 0
capturing = False

for line in text_stream:
    stripped = line.strip()

    # Start capturing when we see INSERT INTO products_description
    if 'INSERT INTO `products_description`' in line:
        capturing = True
        statement_buffer = [line.rstrip('\n\r')]
        continue

    if capturing:
        statement_buffer.append(line.rstrip('\n\r'))

        if stripped.endswith(';'):
            statement = '\n'.join(statement_buffer)
            try:
                cursor.execute(statement)
                inserts_executed += 1
                if inserts_executed % 10 == 0:
                    print(f"  Inserted {inserts_executed} batches...", end='\r')
            except pymysql.Error as e:
                print(f"\nError: {e}")

            statement_buffer = []
            capturing = False

proc.kill()

# Final count
cursor.execute("SELECT COUNT(*) FROM products_description")
count = cursor.fetchone()[0]
print(f"\nDone! products_description now has {count:,} rows")

conn.close()
