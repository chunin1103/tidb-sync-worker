"""
TiDB Cloud Connector - Hybrid MCP + Direct Database Access
Provides high-performance access to e-commerce data for agent intelligence
Uses MCP server when available, falls back to direct connection
"""

import os
import logging
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from decimal import Decimal
import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TiDBConnector:
    """
    Hybrid TiDB connector that prefers MCP server, falls back to direct connection.
    This solves IP whitelisting issues by using MCP when available.
    """

    def __init__(self, mcp_query_func: Optional[Callable] = None):
        """
        Initialize TiDB connection configuration.

        Args:
            mcp_query_func: Optional MCP query function (mcp__tidb-mcp__query)
                           If provided, will use MCP server instead of direct connection
        """
        # MCP server integration (preferred method)
        self.mcp_query_func = mcp_query_func
        self.use_mcp = mcp_query_func is not None

        # Direct connection config (fallback)
        self.config = {
            'host': os.getenv('TIDB_HOST', 'gateway01.ap-southeast-1.prod.aws.tidbcloud.com'),
            'port': int(os.getenv('TIDB_PORT', 4000)),
            'user': os.getenv('TIDB_USER', ''),
            'password': os.getenv('TIDB_PASSWORD', ''),
            'database': os.getenv('TIDB_DATABASE', 'test'),
            'charset': 'utf8mb4',
            'cursorclass': DictCursor,
            'autocommit': True,
            # Enable SSL for TiDB Cloud
            'ssl': {'ssl_mode': 'VERIFY_IDENTITY'},
            'ssl_verify_cert': True,
            'ssl_verify_identity': True
        }

        # Determine connection method
        if self.use_mcp:
            self.enabled = True
            logger.info("✅ TiDB Connector initialized: Using MCP server (no credentials needed)")
        elif self.config['user'] and self.config['password']:
            self.enabled = True
            logger.info(f"✅ TiDB Connector initialized: Direct connection to {self.config['host']}")
        else:
            logger.warning("⚠️ TiDB not configured. Provide MCP function or set TIDB_USER and TIDB_PASSWORD")
            self.enabled = False

    def _get_connection(self):
        """Get a database connection."""
        if not self.enabled:
            raise ValueError("TiDB not configured.")
        if self.use_mcp:
            raise ValueError("Using MCP - direct connection not available")
        return pymysql.connect(**self.config)

    def _execute_query(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        Uses MCP if available, otherwise direct connection.

        Args:
            sql: SQL query string
            params: Query parameters (optional, not supported with MCP)

        Returns:
            List of dictionaries (one per row)
        """
        try:
            if self.use_mcp:
                # Use MCP server
                result = self.mcp_query_func(sql=sql)
                return result.get('rows', [])
            else:
                # Use direct connection
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return rows
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            raise

    # ========================================================================
    # ORDERS INTELLIGENCE
    # ========================================================================

    def get_recent_orders(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent orders for sales trend analysis.

        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum orders to return (default: 100)

        Returns:
            List of order dictionaries with customer and status info
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        sql = """
            SELECT
                orders_id,
                customers_name,
                customers_email_address,
                date_purchased,
                orders_status,
                billing_city,
                billing_state,
                billing_country,
                currency,
                currency_value
            FROM orders
            WHERE date_purchased >= %s
            ORDER BY date_purchased DESC
            LIMIT %s
        """

        rows = self._execute_query(sql, (cutoff_date, limit))
        logger.info(f"📦 Retrieved {len(rows)} orders from last {days} days")
        return rows

    def get_todays_orders(self) -> List[Dict[str, Any]]:
        """Get all orders placed today."""
        today = datetime.now().date()

        sql = """
            SELECT
                orders_id,
                customers_name,
                date_purchased,
                orders_status,
                billing_city,
                billing_state
            FROM orders
            WHERE DATE(date_purchased) = %s
            ORDER BY date_purchased DESC
        """

        rows = self._execute_query(sql, (today,))
        logger.info(f"📦 Today's orders: {len(rows)}")
        return rows

    def get_order_details(self, order_id: int) -> Dict[str, Any]:
        """
        Get complete order details including products and totals.

        Args:
            order_id: Order ID to retrieve

        Returns:
            Dictionary with order info, products, and totals
        """
        # Get order header
        order_sql = "SELECT * FROM orders WHERE orders_id = %s"
        order = self._execute_query(order_sql, (order_id,))

        # Get order products
        products_sql = """
            SELECT op.*, p.products_model, p.products_price
            FROM orders_products op
            LEFT JOIN products p ON op.products_id = p.products_id
            WHERE op.orders_id = %s
        """
        products = self._execute_query(products_sql, (order_id,))

        # Get order totals
        totals_sql = """
            SELECT * FROM orders_total
            WHERE orders_id = %s
            ORDER BY sort_order
        """
        totals = self._execute_query(totals_sql, (order_id,))

        return {
            'order': order[0] if order else None,
            'products': products,
            'totals': totals
        }

    # ========================================================================
    # PRODUCT & INVENTORY INTELLIGENCE
    # ========================================================================

    def get_product_by_model(self, product_model: str) -> Optional[Dict[str, Any]]:
        """
        Get product details by model number.

        Args:
            product_model: Product model/SKU

        Returns:
            Product dictionary or None
        """
        sql = """
            SELECT
                products_id,
                products_model,
                products_quantity,
                products_price,
                products_cost,
                products_status,
                products_weight,
                manufacturers_id,
                products_date_added,
                products_last_modified
            FROM products
            WHERE products_model = %s
        """

        rows = self._execute_query(sql, (product_model,))
        return rows[0] if rows else None

    def get_low_stock_products(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """
        Get products below stock threshold.

        Args:
            threshold: Quantity threshold (default: 10)

        Returns:
            List of low-stock products with details
        """
        sql = """
            SELECT
                p.products_id,
                p.products_model,
                p.products_quantity,
                p.products_price,
                p.products_status,
                pd.products_name
            FROM products p
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE p.products_quantity <= %s
            AND p.products_status = 1
            ORDER BY p.products_quantity ASC
            LIMIT 100
        """

        rows = self._execute_query(sql, (threshold,))
        logger.info(f"⚠️ Found {len(rows)} products below {threshold} units")
        return rows

    def get_products_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        """Get all products in a specific category."""
        sql = """
            SELECT
                p.products_id,
                p.products_model,
                p.products_quantity,
                p.products_price,
                pd.products_name
            FROM products p
            INNER JOIN products_to_categories pc ON p.products_id = pc.products_id
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE pc.categories_id = %s
            AND p.products_status = 1
            ORDER BY pd.products_name
        """

        return self._execute_query(sql, (category_id,))

    # ========================================================================
    # SALES VELOCITY & ANALYTICS
    # ========================================================================

    def get_sales_velocity(self, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Calculate sales velocity (units per day) for top-selling products.

        Args:
            days: Period to analyze (default: 30 days)
            limit: Number of products to return (default: 50)

        Returns:
            List of products with sales velocity metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        sql = """
            SELECT
                p.products_model,
                pd.products_name,
                COUNT(op.products_id) as units_sold,
                ROUND(COUNT(op.products_id) / %s, 2) as units_per_day,
                p.products_quantity as current_stock,
                ROUND(p.products_quantity / (COUNT(op.products_id) / %s), 1) as days_of_stock
            FROM orders_products op
            INNER JOIN orders o ON op.orders_id = o.orders_id
            INNER JOIN products p ON op.products_id = p.products_id
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE o.date_purchased >= %s
            GROUP BY p.products_id, p.products_model, pd.products_name, p.products_quantity
            ORDER BY units_sold DESC
            LIMIT %s
        """

        rows = self._execute_query(sql, (days, days, cutoff_date, limit))
        logger.info(f"📊 Calculated sales velocity for {len(rows)} products ({days}-day period)")
        return rows

    def get_bestsellers(self, days: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get best-selling products by order frequency.

        Args:
            days: Period to analyze (default: 30 days)
            limit: Number of products to return (default: 20)

        Returns:
            List of bestselling products
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        sql = """
            SELECT
                p.products_model,
                pd.products_name,
                COUNT(DISTINCT op.orders_id) as order_count,
                SUM(op.products_quantity) as total_quantity,
                p.products_quantity as current_stock,
                p.products_price
            FROM orders_products op
            INNER JOIN orders o ON op.orders_id = o.orders_id
            INNER JOIN products p ON op.products_id = p.products_id
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE o.date_purchased >= %s
            GROUP BY p.products_id, p.products_model, pd.products_name, p.products_quantity, p.products_price
            ORDER BY order_count DESC
            LIMIT %s
        """

        rows = self._execute_query(sql, (cutoff_date, limit))
        logger.info(f"🏆 Top {len(rows)} bestsellers ({days}-day period)")
        return rows

    # ========================================================================
    # INVENTORY RISK ANALYSIS
    # ========================================================================

    def get_zero_inventory_products(self) -> List[Dict[str, Any]]:
        """Get products with ZERO inventory (critical alert)."""
        sql = """
            SELECT
                p.products_id,
                p.products_model,
                pd.products_name,
                p.products_price,
                p.products_status
            FROM products p
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE p.products_quantity = 0
            AND p.products_status = 1
            ORDER BY pd.products_name
        """

        rows = self._execute_query(sql)
        if rows:
            logger.warning(f"🚨 CRITICAL: {len(rows)} products at ZERO inventory!")
        return rows

    def get_overstock_products(self, threshold: int = 100) -> List[Dict[str, Any]]:
        """
        Get products with excessive inventory.

        Args:
            threshold: Quantity threshold for overstock (default: 100)

        Returns:
            List of overstocked products
        """
        sql = """
            SELECT
                p.products_id,
                p.products_model,
                pd.products_name,
                p.products_quantity,
                p.products_price,
                p.products_cost
            FROM products p
            LEFT JOIN products_description pd ON p.products_id = pd.products_id
            WHERE p.products_quantity >= %s
            AND p.products_status = 1
            ORDER BY p.products_quantity DESC
            LIMIT 50
        """

        rows = self._execute_query(sql, (threshold,))
        logger.info(f"📦 Found {len(rows)} products above {threshold} units (potential overstock)")
        return rows

    # ========================================================================
    # DATABASE METADATA
    # ========================================================================

    def get_table_list(self) -> List[str]:
        """Get list of all tables in the database."""
        sql = "SHOW TABLES"
        rows = self._execute_query(sql)
        # Extract table names from dict format
        tables = [list(row.values())[0] for row in rows]
        return tables

    def get_database_stats(self) -> Dict[str, Any]:
        """Get high-level database statistics."""
        stats = {}

        # Total orders
        total_orders = self._execute_query("SELECT COUNT(*) as count FROM orders")[0]['count']
        stats['total_orders'] = total_orders

        # Total products
        total_products = self._execute_query("SELECT COUNT(*) as count FROM products")[0]['count']
        stats['total_products'] = total_products

        # Active products
        active_products = self._execute_query(
            "SELECT COUNT(*) as count FROM products WHERE products_status = 1"
        )[0]['count']
        stats['active_products'] = active_products

        # Total customers
        total_customers = self._execute_query("SELECT COUNT(*) as count FROM customers")[0]['count']
        stats['total_customers'] = total_customers

        # Orders today
        today = datetime.now().date()
        orders_today = self._execute_query(
            "SELECT COUNT(*) as count FROM orders WHERE DATE(date_purchased) = %s",
            (today,)
        )[0]['count']
        stats['orders_today'] = orders_today

        logger.info(f"📊 Database stats: {stats}")
        return stats

    # ========================================================================
    # HEALTH CHECK
    # ========================================================================

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.use_mcp:
                # Test MCP connection
                result = self._execute_query("SELECT 1")
                logger.info("✅ TiDB MCP connection test: SUCCESS")
                return True
            else:
                # Test direct connection
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                conn.close()
                logger.info("✅ TiDB direct connection test: SUCCESS")
                return True
        except Exception as e:
            logger.error(f"❌ TiDB connection test FAILED: {e}")
            return False


# ============================================================================
# GLOBAL INSTANCE (Singleton Pattern)
# ============================================================================

# Create default instance (without MCP)
# This can be replaced later by calling: tidb.set_mcp_function(mcp_query_func)
tidb = TiDBConnector()


def set_mcp_function(mcp_query_func):
    """
    Configure the global tidb instance to use MCP server.

    Args:
        mcp_query_func: The MCP query function to use

    Example:
        from src.connectors.tidb_connector import set_mcp_function, tidb
        set_mcp_function(mcp__tidb_mcp__query)
    """
    global tidb
    tidb = TiDBConnector(mcp_query_func=mcp_query_func)
    logger.info("🚀 Reconfigured TiDB to use MCP server!")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def format_currency(value: float) -> str:
    """Format a number as USD currency."""
    return f"${value:,.2f}"


def format_date(dt: datetime) -> str:
    """Format a datetime as readable string."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('T', ' ').replace('Z', ''))
    return dt.strftime("%b %d, %Y %I:%M %p")


def calculate_inventory_days(current_stock: int, units_per_day: float) -> float:
    """
    Calculate days of inventory remaining.

    Args:
        current_stock: Current inventory quantity
        units_per_day: Sales velocity (units per day)

    Returns:
        Days of inventory remaining (999 if velocity is 0)
    """
    if units_per_day == 0:
        return 999.0
    return round(current_stock / units_per_day, 1)
