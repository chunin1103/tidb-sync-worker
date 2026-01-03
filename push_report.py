#!/usr/bin/env python3
"""
Push a report to the Agent Garden database (for local Claude executor)
Usage: python push_report.py <agent_type> <report_file_path> [task_id]
"""

import sys
import requests
from pathlib import Path

def push_report_to_db(agent_type: str, report_path: str, task_id: int = None):
    """
    Push a report to the Agent Garden database via API

    Args:
        agent_type: Type of agent (e.g., 'inventory_intelligence')
        report_path: Path to the markdown report file
        task_id: Optional task ID if linked to a ClaudeTask
    """
    # API endpoint
    API_URL = "https://gpt-mcp.onrender.com/AgentGarden/api/reports/save"

    # Read report file
    report_file = Path(report_path)
    if not report_file.exists():
        print(f"❌ Report file not found: {report_path}")
        return False

    with open(report_file, 'r', encoding='utf-8') as f:
        report_content = f.read()

    # Extract title from filename
    report_title = report_file.stem

    # Build relative path (if in OneDrive Reports folder)
    try:
        reports_base = Path.home() / 'Library' / 'CloudStorage' / 'OneDrive-Personal' / 'Claude Tools' / 'Reports'
        if report_file.is_relative_to(reports_base):
            file_path = str(report_file.relative_to(reports_base))
        else:
            file_path = str(report_file)
    except:
        file_path = str(report_file)

    # Prepare payload
    payload = {
        'agent_type': agent_type,
        'report_title': report_title,
        'report_content': report_content,
        'file_path': file_path
    }

    if task_id:
        payload['task_id'] = task_id

    # Send POST request
    try:
        print(f"📤 Pushing report to database...")
        print(f"   Agent Type: {agent_type}")
        print(f"   Title: {report_title}")
        print(f"   Size: {len(report_content):,} bytes")

        response = requests.post(API_URL, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Report saved successfully (ID: {result.get('report_id')})")
                return True
            else:
                print(f"❌ Failed: {result.get('error')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error pushing report: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python push_report.py <agent_type> <report_file_path> [task_id]")
        print("\nExample:")
        print('  python push_report.py inventory_intelligence "~/OneDrive/Reports/inventory/report.md"')
        sys.exit(1)

    agent_type = sys.argv[1]
    report_path = sys.argv[2]
    task_id = int(sys.argv[3]) if len(sys.argv) > 3 else None

    success = push_report_to_db(agent_type, report_path, task_id)
    sys.exit(0 if success else 1)
