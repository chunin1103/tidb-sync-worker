#!/usr/bin/env python3
"""
Database initialization script for Agent Garden
Creates tables in Neon PostgreSQL database
"""

import os
from dotenv import load_dotenv
from src.core.database import init_db, USE_DATABASE, DATABASE_URL

load_dotenv()

def main():
    """Initialize database tables"""
    print("Agent Garden - Database Initialization")
    print("=" * 50)

    if not USE_DATABASE:
        print("❌ DATABASE_URL not found in environment variables")
        print("\nTo enable database support:")
        print("1. Add DATABASE_URL to your .env file")
        print("2. Format: postgresql://user:password@host/database")
        print("3. Get your Neon connection string from: https://console.neon.tech")
        return 1

    print(f"✅ Database configured: {DATABASE_URL[:30]}...")
    print("\nInitializing database tables...")

    try:
        init_db()
        print("✅ Database tables created successfully!")
        print("\nTables created:")
        print("  - chat_sessions (session metadata)")
        print("  - chat_messages (conversation history)")
        print("\nYou can now run the application with persistent chat storage.")
        return 0

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        print("\nPlease check:")
        print("1. DATABASE_URL is correct in .env")
        print("2. Neon database is accessible")
        print("3. Network connection is working")
        return 1

if __name__ == "__main__":
    exit(main())
