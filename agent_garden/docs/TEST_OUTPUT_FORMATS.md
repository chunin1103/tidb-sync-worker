# Testing Output Formats for Claude Agent Garden

## Overview

Claude Code CLI can now generate reports in **multiple formats** autonomously:
- **Markdown (`.md`)** - Default, human-readable reports
- **CSV (`.csv`)** - Tabular data for Excel/spreadsheet tools
- **XLSX (`.xlsx`)** - Formatted Excel files with multiple sheets
- **JSON (`.json`)** - Structured data for APIs
- **Multi** - Generates all three formats (MD + CSV + XLSX)

---

## How It Works

1. **Database**: `claude_tasks.output_format` column added
2. **API**: `/AgentGarden/tasks/create` accepts `output_format` parameter
3. **Executor**: Builds format-specific prompts for Claude Code CLI
4. **Claude**: Autonomously generates files using Write tool (Python libraries)

---

## Test Examples

### 1. Generate CSV Report

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "output_format": "csv",
    "task_json": {
      "agent_type": "inventory_intelligence",
      "report_title": "Top 10 Products by Revenue",
      "prompt": "Query TiDB for top 10 products by revenue this month. Output as CSV with columns: Product ID, Product Name, Units Sold, Revenue, Profit Margin"
    }
  }'
```

**Expected Output:**
- File: `Reports/inventory_intelligence/top_products_20260103_143022.csv`
- Format:
```csv
Product ID,Product Name,Units Sold,Revenue,Profit Margin
12345,Product A,150,$4500,35%
67890,Product B,120,$3600,28%
...
```

---

### 2. Generate XLSX Report (Excel)

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "output_format": "xlsx",
    "task_json": {
      "agent_type": "sales_analysis",
      "report_title": "Monthly Sales Dashboard",
      "prompt": "Analyze orders from past 30 days. Create Excel file with 3 sheets: (1) Summary metrics, (2) Daily sales trend, (3) Top customers. Use bold headers and number formatting."
    }
  }'
```

**Expected Output:**
- File: `Reports/sales_analysis/monthly_dashboard_20260103_143530.xlsx`
- Sheets:
  - **Summary**: Total revenue, order count, avg order value
  - **Daily Trend**: Date, orders, revenue (with chart if Claude adds it)
  - **Top Customers**: Customer ID, name, total spent

---

### 3. Generate JSON Report (API-friendly)

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "output_format": "json",
    "task_json": {
      "agent_type": "order_monitoring",
      "report_title": "Today Orders Summary",
      "prompt": "Get today orders count, total revenue, and list of orders with basic details. Output as structured JSON."
    }
  }'
```

**Expected Output:**
- File: `Reports/order_monitoring/today_summary_20260103_144015.json`
- Structure:
```json
{
  "report_date": "2026-01-03",
  "summary": {
    "total_orders": 23,
    "total_revenue": 12450.50,
    "avg_order_value": 541.76
  },
  "orders": [
    {"order_id": 646100, "customer": "John Doe", "amount": 125.50, "status": "completed"},
    ...
  ]
}
```

---

### 4. Generate Multi-Format (All 3 Files)

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "output_format": "multi",
    "task_json": {
      "agent_type": "inventory_intelligence",
      "report_title": "Low Stock Alert",
      "prompt": "Find products with less than 10 units in stock. Generate report in 3 formats: MD (executive summary), CSV (raw data), XLSX (formatted with conditional formatting for urgent items)"
    }
  }'
```

**Expected Output:**
- `Reports/inventory_intelligence/low_stock_20260103_144530.md` - Executive summary
- `Reports/inventory_intelligence/low_stock_20260103_144530.csv` - Raw data
- `Reports/inventory_intelligence/low_stock_20260103_144530.xlsx` - Formatted Excel

---

## Migration Steps

### 1. Run Database Migration

```bash
cd render-tidb-sync/agent_garden

# Execute migration SQL on Neon database
psql $DATABASE_URL -f migrations/002_add_output_format.sql
```

**Migration SQL:**
```sql
ALTER TABLE claude_tasks ADD COLUMN output_format VARCHAR(10) DEFAULT 'md';
UPDATE claude_tasks SET output_format = 'md' WHERE output_format IS NULL;
```

---

### 2. Install Dependencies

```bash
# Install openpyxl for XLSX support
pip install openpyxl>=3.1.0
```

**Note:** Already added to `requirements.txt` - will auto-install on Render deployment.

---

### 3. Deploy to Render

```bash
git add .
git commit -m "Add output_format support (CSV/XLSX/JSON/Multi)"
git push origin main
```

Render will automatically:
1. Install `openpyxl` from requirements.txt
2. Deploy updated `unified_app.py` with new API parameter
3. Update executor (runs locally on Mac, pull changes)

---

## Executor Update (Local Mac)

```bash
# On your Mac, pull latest executor code
cd render-tidb-sync
git pull

# Restart executor
# (If running in background with screen/launchd, kill and restart)
python claude_executor.py
```

---

## Verification

### Test Markdown (Default)

```bash
curl -X POST http://localhost:8080/AgentGarden/tasks/create \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "agent_report",
    "task_json": {
      "agent_type": "test",
      "report_title": "Test MD",
      "prompt": "Generate a simple markdown report with 3 sections"
    }
  }'
```

Check output in: `~/Library/CloudStorage/OneDrive-Personal/Reports/test/`

### Test CSV

```bash
# Same as above, add: "output_format": "csv"
```

Check output: File should end with `.csv` and contain comma-separated values.

### Test XLSX

```bash
# Same as above, add: "output_format": "xlsx"
```

Check output: Open in Excel/Numbers - should have formatted headers.

---

## Format-Specific Instructions Given to Claude

### CSV Format
```
Generate a CSV file with:
1. Header row with clear column names
2. Data rows with comma-separated values
3. Properly escaped fields (wrap in quotes if contains commas)
4. No markdown formatting - pure CSV data only

Use Python's csv module...
```

### XLSX Format
```
Generate an Excel (XLSX) file with:
1. Sheet with clear headers in Row 1 (bold if possible)
2. Data rows starting from Row 2
3. Formatted cells (numbers as numbers, dates as dates)
4. Optional: Multiple sheets for different data categories
5. Optional: Summary sheet with key insights

Use openpyxl library...
```

### JSON Format
```
Generate a JSON file with:
1. Well-structured JSON object or array
2. Clear property names
3. Proper data types (strings, numbers, booleans, arrays, objects)
4. Pretty-printed with indentation for readability

Use Python's json module...
```

---

## Next Steps for "AI Employee" Workflow

Now that Claude can generate CSV/XLSX autonomously, you can build:

1. **Reorder Calculator** - Claude generates reorder spreadsheets for Bullseye/Oceanside
2. **Vendor Orders** - Claude creates purchase orders in Excel format
3. **Inventory Reports** - Automated daily/weekly inventory snapshots
4. **Sales Dashboards** - Excel files with charts and pivot tables

All **fully autonomous** - Gemini creates task → Claude executes → Excel file saved to OneDrive!

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| XLSX fails with "No module named 'openpyxl'" | Run `pip install openpyxl` on Mac |
| CSV has markdown formatting | Check Claude prompt - may need to emphasize "CSV only, no markdown" |
| File saved but wrong extension | Check `output_format` parameter matches expected format |
| Multi format only creates 1 file | Claude may need explicit instruction - check executor logs |

---

## Files Modified

1. **Database Schema**: `agent_garden/migrations/002_add_output_format.sql`
2. **Database Model**: `agent_garden/src/core/database.py:127` (added output_format column)
3. **Database Functions**: `agent_garden/src/core/database_claude_tasks.py:12,73,261,311` (added output_format parameter)
4. **API Endpoint**: `unified_app.py:290` (accept output_format from request)
5. **Executor**: `claude_executor.py:108,307-407,409` (format-specific prompts)
6. **Dependencies**: `requirements.txt:30` (added openpyxl)

---

**Created:** 2026-01-03
**Status:** Ready for Testing
