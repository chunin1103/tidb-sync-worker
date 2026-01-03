#!/usr/bin/env python3
"""
Import existing OneDrive reports to database
Run this script locally on Mac to migrate all .md reports to PostgreSQL
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent_garden.src.core.database import save_claude_report, init_db

def import_reports_from_onedrive():
    """Import all markdown reports from OneDrive to database"""

    # Load environment variables
    load_dotenv()

    # Initialize database (create tables if needed)
    print("Initializing database...")
    init_db()

    # Get OneDrive Reports folder path
    reports_base = Path.home() / 'Library' / 'CloudStorage' / 'OneDrive-Personal' / 'Claude Tools' / 'Reports'

    if not reports_base.exists():
        print(f"❌ Reports folder not found: {reports_base}")
        return

    print(f"📁 Scanning reports folder: {reports_base}")

    # Find all markdown files
    md_files = list(reports_base.rglob('*.md'))
    total = len(md_files)

    if total == 0:
        print("⚠️  No markdown files found")
        return

    print(f"📊 Found {total} markdown files\n")

    # Import each file
    imported = 0
    skipped = 0
    errors = 0

    for i, md_file in enumerate(md_files, 1):
        try:
            # Determine agent type from parent folder
            parent_folder = md_file.parent.name
            agent_type = parent_folder if parent_folder != 'Reports' else 'general_report'

            # Extract title from filename (without extension)
            report_title = md_file.stem

            # Read file content
            with open(md_file, 'r', encoding='utf-8') as f:
                report_content = f.read()

            # Build relative path from Reports folder
            file_path = str(md_file.relative_to(reports_base))

            # Save to database
            report_id = save_claude_report(
                agent_type=agent_type,
                report_title=report_title,
                report_content=report_content,
                file_path=file_path
            )

            if report_id:
                imported += 1
                print(f"[{i}/{total}] ✅ {agent_type}/{report_title}")
            else:
                skipped += 1
                print(f"[{i}/{total}] ⏭️  {agent_type}/{report_title} (already exists)")

        except Exception as e:
            errors += 1
            print(f"[{i}/{total}] ❌ {md_file.name}: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Import Complete!")
    print(f"{'='*60}")
    print(f"✅ Imported: {imported}")
    print(f"⏭️  Skipped:  {skipped}")
    print(f"❌ Errors:   {errors}")
    print(f"📊 Total:    {total}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("Claude Reports → Database Import Tool")
    print("="*60 + "\n")

    try:
        import_reports_from_onedrive()
    except KeyboardInterrupt:
        print("\n\n⚠️  Import cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
