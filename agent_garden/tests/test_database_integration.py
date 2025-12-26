"""
Test script to verify database integration with agents
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("🧪 TESTING DATABASE INTEGRATION WITH AGENTS")
print("=" * 80)

# Test 1: TiDB Connection
print("\n[TEST 1] Testing TiDB Connection...")
try:
    from src.connectors.tidb_connector import tidb

    if tidb.enabled:
        result = tidb.test_connection()
        if result:
            print("✅ TiDB connection successful!")

            # Get some stats
            stats = tidb.get_database_stats()
            print(f"   - Total Products: {stats['total_products']:,}")
            print(f"   - Total Orders: {stats['total_orders']:,}")
            print(f"   - Orders Today: {stats['orders_today']}")
        else:
            print("❌ TiDB connection test failed")
    else:
        print("⚠️ TiDB not configured (credentials missing)")
except Exception as e:
    print(f"❌ TiDB test failed: {e}")

# Test 2: Database Context Builder
print("\n[TEST 2] Testing Database Context Builder...")
try:
    from src.connectors.agent_database_context_optimized import get_agent_database_context_optimized

    context = get_agent_database_context_optimized("inventory_intelligence")

    if context:
        print(f"✅ Database context generated!")
        print(f"   - Context length: {len(context):,} characters")
        print(f"   - Contains 'CRITICAL INVENTORY': {'CRITICAL INVENTORY' in context}")
        print(f"   - Contains 'SALES INTELLIGENCE': {'SALES INTELLIGENCE' in context}")
        print(f"   - Contains 'RECENT BUSINESS': {'RECENT BUSINESS' in context}")

        # Show a preview
        print("\n   Preview (first 500 chars):")
        print("   " + "-" * 76)
        preview = context[:500].replace('\n', '\n   ')
        print(f"   {preview}...")
        print("   " + "-" * 76)
    else:
        print("⚠️ Database context is empty (may be expected if TiDB not connected)")

except Exception as e:
    print(f"❌ Context builder test failed: {e}")

# Test 3: Agent Backend Integration
print("\n[TEST 3] Testing Agent Backend Integration...")
try:
    from src.core.agent_backend import execute_agent

    print("✅ Agent backend imported successfully")
    print("   Testing agent execution with simple query...")

    # Create a test session
    session_id = "test_integration_123"
    test_message = "What are the critical inventory issues right now?"

    print(f"   Query: '{test_message}'")
    print("\n   Agent Response:")
    print("   " + "-" * 76)

    response_chunks = []
    for chunk in execute_agent("inventory_intelligence", test_message, session_id):
        response_chunks.append(chunk)
        # Print in real-time
        print(chunk, end='', flush=True)

    print("\n   " + "-" * 76)

    full_response = ''.join(response_chunks)

    if full_response:
        print(f"\n✅ Agent executed successfully!")
        print(f"   - Response length: {len(full_response):,} characters")

        # Check if agent referenced database data
        has_data_refs = any(keyword in full_response.lower() for keyword in [
            'zero inventory', 'stock', 'product', 'database', 'current'
        ])

        if has_data_refs:
            print("   - ✅ Agent appears to be using database context!")
        else:
            print("   - ⚠️ Agent may not be referencing database data")
    else:
        print("❌ Agent returned empty response")

except Exception as e:
    print(f"❌ Agent backend test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check specific database queries
print("\n[TEST 4] Testing Specific Database Queries...")
try:
    from src.connectors.tidb_connector import tidb

    if tidb.enabled:
        # Zero inventory
        zero = tidb.get_zero_inventory_products()
        print(f"✅ Zero inventory products: {len(zero)}")

        # Low stock
        low_stock = tidb.get_low_stock_products(threshold=10)
        print(f"✅ Low stock products: {len(low_stock)}")

        # Sales velocity
        velocity = tidb.get_sales_velocity(days=30, limit=5)
        print(f"✅ Sales velocity calculated: {len(velocity)} products")

        # Bestsellers
        bestsellers = tidb.get_bestsellers(days=30, limit=5)
        print(f"✅ Bestsellers found: {len(bestsellers)} products")

        # Recent orders
        recent = tidb.get_recent_orders(days=7, limit=10)
        print(f"✅ Recent orders: {len(recent)} orders")

    else:
        print("⚠️ Skipping (TiDB not configured)")

except Exception as e:
    print(f"❌ Database queries failed: {e}")

print("\n" + "=" * 80)
print("🏁 TESTING COMPLETE")
print("=" * 80)

# Summary
print("\n📊 SUMMARY:")
print("If all tests passed with ✅, your agents are now LEGENDARY with database integration!")
print("\nNext steps:")
print("1. Start the Flask app: python app.py")
print("2. Send a message to an agent via POST /execute_agent")
print("3. Watch as the agent uses REAL database intelligence!")
print("\n🚀 Your agents are now database-powered and ready to provide intelligent insights!")
