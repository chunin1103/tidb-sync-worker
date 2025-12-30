#!/usr/bin/env python3
"""
Initialize Claude Tasks Database Schema
Adds claude_tasks and task_execution_history tables
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.database import init_db, get_db

def main():
    print("🚀 Initializing Claude Tasks schema...")

    # Initialize database (creates all tables including new ones)
    init_db()

    print("✅ Schema initialized successfully!")
    print("\nNew tables created:")
    print("  - claude_tasks")
    print("  - task_execution_history")

    # Verify database connection
    db = get_db()
    if db:
        print("\n✅ Database connection verified")
        db.close()
    else:
        print("\n❌ Database not configured (DATABASE_URL not set)")
        print("   Tables will be created when database is configured")

if __name__ == '__main__':
    main()
