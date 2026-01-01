#!/usr/bin/env python3
"""
Initialize Reorder Calculator Database Schema (Standalone)
Runs schema.sql directly without importing Flask
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_schema():
    """Initialize database schema by executing schema.sql"""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Read schema.sql
    schema_file = os.path.join(os.path.dirname(__file__), 'reports_viewer', 'schema.sql')
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    # Connect to database and execute schema
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Execute schema (split by semicolon for multiple statements)
        statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

        for statement in statements:
            try:
                conn.execute(text(statement))
                conn.commit()
            except Exception as e:
                # Ignore "table already exists" errors
                if 'already exists' not in str(e).lower():
                    raise

        print("SUCCESS: Schema initialization complete!")

    engine.dispose()

if __name__ == '__main__':
    print("Initializing Reorder Calculator database schema...")
    print(f"Working directory: {os.getcwd()}")

    try:
        init_schema()
        print("\nSUCCESS: Database schema initialized successfully!")
        print("\nCreated tables:")
        print("  - reorder_sessions")
        print("  - reorder_questions")
        print("  - reorder_manual_edits")
        print("  - reorder_decision_learning")
    except Exception as e:
        print(f"FAILED: Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
