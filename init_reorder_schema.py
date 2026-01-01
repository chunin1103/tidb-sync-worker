#!/usr/bin/env python3
"""
Initialize Reorder Calculator Database Schema
Runs the schema.sql file to create necessary tables in Agent Garden database
"""
import os
from reports_viewer.database import init_schema

if __name__ == '__main__':
    print("Initializing Reorder Calculator database schema...")
    try:
        init_schema()
        print("✅ Database schema initialized successfully!")
        print("\nCreated tables:")
        print("  - reorder_sessions")
        print("  - reorder_questions")
        print("  - reorder_manual_edits")
        print("  - reorder_decision_learning")
    except Exception as e:
        print(f"❌ Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
