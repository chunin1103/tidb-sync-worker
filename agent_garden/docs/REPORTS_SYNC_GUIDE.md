# Reports Sync Guide

## Overview

Reports are now stored in **two places** for maximum flexibility:
1. **Local OneDrive** - Your familiar file-based workflow (preserved)
2. **PostgreSQL Database** - Makes reports accessible on the web UI from anywhere

## How It Works

When Claude executor creates a report:
1. **Save to OneDrive** - Report saved to `~/OneDrive/Claude Tools/Reports/{agent_type}/` (as before)
2. **Push to Database** - Run `push_report.py` to sync to database (NEW)
3. **View on Web** - Report appears in Agent Garden "Generated Reports" section

## Quick Start

### Push a Single Report
```bash
python push_report.py inventory_intelligence "/Users/vusmac/Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports/inventory_intelligence/report_20260103_110831.md"
```

### Import All Existing Reports
```bash
python import_reports.py
```

## Integration with Claude Executor

Add this to your Claude executor workflow after saving reports:

```python
import requests
from pathlib import Path

def save_and_sync_report(agent_type, report_path):
    """Save report to OneDrive AND sync to database"""

    # 1. Save to OneDrive (existing code)
    with open(report_path, 'w') as f:
        f.write(report_content)

    # 2. Sync to database (NEW)
    with open(report_path, 'r') as f:
        content = f.read()

    response = requests.post(
        'https://gpt-mcp.onrender.com/AgentGarden/api/reports/save',
        json={
            'agent_type': agent_type,
            'report_title': Path(report_path).stem,
            'report_content': content,
            'file_path': str(Path(report_path).relative_to(reports_base))
        }
    )

    if response.status_code == 200:
        print(f"✅ Report synced to database")
    else:
        print(f"❌ Failed to sync: {response.text}")
```

## File Locations

- **import_reports.py** - Bulk import all existing OneDrive reports (project root)
- **push_report.py** - Push single report to database (project root)
- **Local Reports** - `~/Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports/`
- **Web UI** - https://gpt-mcp.onrender.com/AgentGarden/

## Benefits

✅ **Local files preserved** - Your existing workflow unchanged
✅ **Web accessible** - View reports from any device via Agent Garden
✅ **No costs** - Uses existing PostgreSQL database (Neon)
✅ **Reliable** - Platform-independent, no Mac filesystem dependencies
✅ **Automatic updates** - Re-running import updates existing reports

## Troubleshooting

**Reports not appearing in UI?**
- Run `python import_reports.py` to sync all reports
- Check database connection in `.env` file
- Verify API endpoint: https://gpt-mcp.onrender.com/AgentGarden/api/reports/list

**Import script errors?**
- Ensure `.env` has `DATABASE_URL` set
- Check OneDrive folder path exists: `~/Library/CloudStorage/OneDrive-Personal/Claude Tools/Reports/`
- Verify Python packages installed: `pip install -r requirements.txt`
