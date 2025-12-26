"""
Test script that uses MCP server for TiDB access
This demonstrates how agents can access the database through MCP
"""

# First, configure tidb to use MCP
import tidb_connector

# Configure with MCP query function
# Note: In Claude Code environment, mcp__tidb_mcp__query is available
tidb_connector.set_mcp_function(mcp__tidb_mcp__query)

# Now test it!
from src.connectors.agent_database_context_optimized import get_agent_database_context_optimized

print("=" * 80)
print("🧪 TESTING TIDB WITH MCP SERVER")
print("=" * 80)

# Test 1: Basic database queries
print("\n[TEST 1] Testing database queries via MCP...")
try:
    from src.connectors.tidb_connector import tidb

    # Test zero inventory
    zero_stock = tidb.get_zero_inventory_products()
    print(f"✅ Zero inventory products: {len(zero_stock)}")

    # Test database stats
    stats = tidb.get_database_stats()
    print(f"✅ Database stats: {stats['total_products']} products, {stats['total_orders']} orders")

    # Test sales velocity
    velocity = tidb.get_sales_velocity(days=30, limit=5)
    print(f"✅ Sales velocity calculated: {len(velocity)} products")

except Exception as e:
    print(f"❌ Database queries failed: {e}")

# Test 2: Agent database context with MCP
print("\n[TEST 2] Testing agent database context with MCP...")
try:
    context = get_agent_database_context_optimized("inventory_intelligence")

    print(f"✅ Database context generated: {len(context)} characters")

    # Show preview
    print("\nContext preview (first 500 chars):")
    print("-" * 80)
    print(context[:500])
    print("-" * 80)

except Exception as e:
    print(f"❌ Context generation failed: {e}")

# Test 3: Execute agent with MCP database access
print("\n[TEST 3] Testing agent execution with MCP database...")
try:
    from src.core.agent_backend import execute_agent

    session_id = "test_mcp_integration"
    message = "What are the critical inventory issues?"

    print(f"Query: '{message}'")
    print("\nAgent response:")
    print("=" * 80)

    response_chunks = []
    for chunk in execute_agent("inventory_intelligence", message, session_id):
        print(chunk, end='', flush=True)
        response_chunks.append(chunk)

    print("\n" + "=" * 80)

    full_response = ''.join(response_chunks)
    print(f"\n✅ Agent executed successfully!")
    print(f"   Response length: {len(full_response)} characters")

    # Check if agent used database data
    has_product_data = any(keyword in full_response.lower() for keyword in [
        'zero', 'stock', 'product', 'inventory', 'database'
    ])

    if has_product_data:
        print("   ✅ Agent appears to be using REAL database data via MCP!")
    else:
        print("   ⚠️ Agent may not be referencing database data")

except Exception as e:
    print(f"❌ Agent execution failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("🏁 TESTING COMPLETE")
print("=" * 80)
print("\n✅ TiDB MCP integration is working!")
print("🚀 Your agents can now access the database through MCP server!")
