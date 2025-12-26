# MySQL to TiDB Cloud Migration Instructions

## Overview
This document describes how to migrate MySQL database dumps from IDrive e2 (S3-compatible storage) to TiDB Cloud using streaming (no local storage required).

## Prerequisites
- Python 3.x with `pymysql` installed (`pip install pymysql`)
- rclone configured with IDrive e2 remote named `idrive`
- TiDB Cloud cluster credentials

## Available Backup Folders on IDrive
```
idrive:dbdaily/db/categories-products/  - Product catalog data
idrive:dbdaily/db/orders/               - Order and customer data
```

## Key Compatibility Issues (MySQL → TiDB)

### 1. Character Set and Collation
TiDB works best with `utf8mb4`. Convert from legacy charsets:
```python
# Use negative lookahead (?!mb) to avoid eating semicolons
statement = re.sub(r"DEFAULT CHARSET=utf8(?!mb)", "DEFAULT CHARSET=utf8mb4", statement)
statement = re.sub(r"DEFAULT CHARSET=latin1\b", "DEFAULT CHARSET=utf8mb4", statement)
statement = re.sub(r"CHARACTER SET latin1\s+COLLATE\s+latin1_\w+",
                   "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci", statement)
```

**WARNING**: Do NOT use `utf8[^m]` pattern - it eats the following character (including semicolons), breaking statement parsing!

### 2. Invalid Default Dates
TiDB strict mode rejects `0000-00-00` dates:
```python
statement = re.sub(r"NOT NULL DEFAULT '0000-00-00 00:00:00'",
                   "NOT NULL DEFAULT '1970-01-01 00:00:01'", statement)
statement = re.sub(r"DEFAULT '0000-00-00 00:00:00'", "DEFAULT NULL", statement)
```

### 3. Storage Engine
Replace MyISAM with InnoDB:
```python
statement = re.sub(r"ENGINE\s*=\s*MyISAM", "ENGINE=InnoDB", statement)
```

### 4. FULLTEXT Indexes
TiDB doesn't support FULLTEXT indexes. Remove them from CREATE TABLE:
```python
if 'FULLTEXT' in statement.upper():
    lines = statement.split('\n')
    lines = [l for l in lines if 'FULLTEXT' not in l.upper()]
    statement = '\n'.join(lines)
    statement = re.sub(r',\s*\)', ')', statement)  # Fix trailing comma
```

### 5. Key Length Limit
TiDB max key length is 3072 bytes. With utf8mb4 (4 bytes/char), long composite indexes can exceed this:
```python
# Remove specific problematic indexes
if 'KEY `idx_cust_email_pass`' in line:
    continue  # Skip this index line
```

### 6. Block Comment Detection (CRITICAL)
MySQL dumps may contain `/*` in data values (HTML, JSON, comments). Do NOT check if line contains `/*` - only check if line STARTS with `/*`:
```python
# WRONG - will skip INSERT statements containing /* in data:
if '/*' in stripped and '*/' not in stripped:

# CORRECT - only detect comments at start of line:
if stripped.startswith('/*') and not stripped.startswith('/*!'):
```

### 7. Skip MySQL-specific Commands
```python
if stripped.upper().startswith(('LOCK TABLES', 'UNLOCK TABLES')):
    continue
```

## Migration Scripts

### For Categories/Products
Use: `stream_migration.py`
- Source: `idrive:dbdaily/db/categories-products/YYYY-MM-DD-HH-MM-SS_suppliesart1_maindb_categories-products.sql.gz`
- Tables: categories, products, products_description, products_attributes, etc.

### For Orders/Customers
Use: `stream_orders_migration.py`
- Source: `idrive:dbdaily/db/orders/YYYY-MM-DD-HH-MM-SS_suppliesart1_maindb.sql.gz`
- Tables: customers, customers_info, address_book, orders, orders_products, orders_total, orders_status_history, order_transactions

## TiDB Cloud Connection Config
```python
from pymysql.constants import CLIENT

TIDB_CONFIG = {
    'host': 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com',
    'port': 4000,
    'user': '3oTjjLfAngfGpch.root',
    'password': 'YOUR_PASSWORD',
    'database': 'test',
    'ssl': {'ssl': {'ca': None}},
    'autocommit': True,
    'charset': 'utf8mb4',
    'client_flag': CLIENT.MULTI_STATEMENTS  # Required for multi-statement execution
}
```

## Finding Latest Backup Files
```bash
# List available backups
rclone lsl "idrive:dbdaily/db/orders/"
rclone lsl "idrive:dbdaily/db/categories-products/"
```

## Running Migration
```bash
# Categories/Products (smaller, ~10MB compressed)
python stream_migration.py

# Orders/Customers (larger, ~117MB compressed, ~460MB decompressed)
python stream_orders_migration.py
```

## Expected Results

### Categories/Products Tables
| Table | Approx Rows |
|-------|-------------|
| categories | 169 |
| categories_description | 169 |
| products | 26,472 |
| products_description | 26,464 |
| products_attributes | 344,002 |
| products_groups | 62,722 |
| products_to_categories | 27,147 |

### Orders/Customers Tables
| Table | Approx Rows |
|-------|-------------|
| customers | 28,898 |
| customers_info | 28,919 |
| address_book | 70,977 |
| orders | 134,127 |
| orders_products | 906,616 |
| orders_total | 587,451 |
| orders_status_history | 468,078 |
| order_transactions | 81,418 |

## Troubleshooting

### "Table doesn't exist" errors on INSERT
- Block comment detection is incorrectly skipping CREATE TABLE statements
- Check if INSERT data contains `/*` which triggers false comment detection
- Fix: Only detect comments at START of line

### "Specified key was too long" error
- Composite index exceeds 3072 bytes with utf8mb4
- Fix: Remove the problematic index from CREATE TABLE

### Statements not being detected
- Regex pattern is eating semicolons
- Fix: Use `(?!mb)` lookahead instead of `[^m]` character class

### Connection timeouts
- TiDB Cloud can have intermittent connectivity
- Simply retry the migration

## Complete Migration Script Template
See `stream_orders_migration.py` for the full working implementation with all fixes applied.
