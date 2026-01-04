#!/usr/bin/env python3
"""
Run database migration to add next_run_time column
"""
import os
import sys
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from sqlalchemy import create_engine, text

def run_migration():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return False

    print(f"🔗 Connecting to database...")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'claude_tasks' AND column_name = 'next_run_time'
        """))

        if result.fetchone():
            print("✅ Column 'next_run_time' already exists - no migration needed")
            return True

        print("📝 Adding 'next_run_time' column...")
        conn.execute(text("""
            ALTER TABLE claude_tasks ADD COLUMN next_run_time TIMESTAMP NULL
        """))
        conn.commit()

        print("📝 Creating index on 'next_run_time'...")
        conn.execute(text("""
            CREATE INDEX idx_claude_tasks_next_run_time ON claude_tasks(next_run_time)
        """))
        conn.commit()

        print("✅ Migration completed successfully!")
        return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
