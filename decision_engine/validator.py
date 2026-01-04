"""
Decision Validator - Executes mapped decisions against database

Validates decision tree logic by running actual database queries
and Python calculations to ensure consistent output.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tidb_mcp import execute_query
except ImportError:
    # Mock for testing
    def execute_query(sql: str) -> List[Dict]:
        return []


@dataclass
class ValidationResult:
    """Result of validating a decision against database"""
    decision_id: str
    success: bool
    value: Any
    sql_executed: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'decision_id': self.decision_id,
            'success': self.success,
            'value': self.value,
            'sql_executed': self.sql_executed,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms
        }


class DecisionValidator:
    """
    Validates decision tree logic against live database

    Responsibilities:
    - Execute mapped SQL queries
    - Run Python calculations
    - Evaluate decision conditions
    - Return consistent results for decision trees
    """

    def __init__(self, tidb_connection=None):
        """
        Initialize validator

        Args:
            tidb_connection: Optional TiDB connection (uses MCP server if None)
        """
        self.tidb_connection = tidb_connection

    def validate_decision(self, mapping: Dict, context: Dict = None) -> ValidationResult:
        """
        Validate a single decision by executing its mapped database operation

        Args:
            mapping: DatabaseMapping dictionary
            context: Context data (product_id, customer_id, etc.)

        Returns:
            ValidationResult with execution outcome
        """
        import time

        start_time = time.time()

        try:
            # Determine validation method based on mapping
            if mapping.get('calculation'):
                result = self._execute_calculation(mapping, context)
            elif mapping.get('table') and mapping.get('column'):
                result = self._execute_query(mapping, context)
            else:
                return ValidationResult(
                    decision_id=mapping['decision_id'],
                    success=False,
                    value=None,
                    error="No calculation or table/column mapping provided"
                )

            execution_time = (time.time() - start_time) * 1000  # milliseconds

            return ValidationResult(
                decision_id=mapping['decision_id'],
                success=True,
                value=result['value'],
                sql_executed=result.get('sql'),
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            return ValidationResult(
                decision_id=mapping['decision_id'],
                success=False,
                value=None,
                error=str(e),
                execution_time_ms=execution_time
            )

    def _execute_query(self, mapping: Dict, context: Dict = None) -> Dict:
        """
        Execute a database query based on mapping

        Args:
            mapping: DatabaseMapping with table/column info
            context: Context data for WHERE clause

        Returns:
            Dictionary with query result
        """
        table = mapping['table']
        column = mapping['column']
        filters = mapping.get('filters', {})

        # Build WHERE clause
        where_parts = []

        # Add filters from mapping
        for key, value in filters.items():
            if isinstance(value, str):
                where_parts.append(f"{key} = '{value}'")
            else:
                where_parts.append(f"{key} = {value}")

        # Add context filters
        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    where_parts.append(f"{key} = '{value}'")
                else:
                    where_parts.append(f"{key} = {value}")

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        # Build SQL
        sql = f"SELECT {column} FROM {table} WHERE {where_clause}"

        # Execute query
        results = execute_query(sql)

        if not results:
            return {'value': None, 'sql': sql}

        # Return first result
        value = results[0].get(column)

        return {'value': value, 'sql': sql}

    def _execute_calculation(self, mapping: Dict, context: Dict = None) -> Dict:
        """
        Execute a calculation (SQL expression or Python code)

        Args:
            mapping: DatabaseMapping with calculation formula
            context: Context data for calculation

        Returns:
            Dictionary with calculation result
        """
        calculation = mapping['calculation']

        # Check if it's a SQL calculation or Python calculation
        if '/' in calculation or 'SELECT' in calculation.upper():
            return self._execute_sql_calculation(mapping, context)
        else:
            return self._execute_python_calculation(mapping, context)

    def _execute_sql_calculation(self, mapping: Dict, context: Dict = None) -> Dict:
        """
        Execute SQL calculation

        Example: products_quantity / (lifetime_units_sold / 365)
        """
        calculation = mapping['calculation']
        table = mapping.get('table', 'products')

        # Build SQL with calculation
        # Handle common patterns

        # Pattern: years_in_stock = products_quantity / (lifetime_units_sold / 365)
        if 'products_quantity' in calculation and 'lifetime_units_sold' in calculation:
            # Get context
            products_id = context.get('products_id') if context else None

            if not products_id:
                # Get aggregate stats
                sql = f"""
                    SELECT
                        AVG(p.products_quantity / NULLIF(
                            (SELECT COALESCE(SUM(op.products_quantity), 0)
                             FROM orders_products op
                             WHERE op.products_id = p.products_id) / 365.0, 0)
                        ) AS avg_years_in_stock
                    FROM products p
                    WHERE p.products_status = 1
                """
            else:
                sql = f"""
                    SELECT
                        p.products_quantity,
                        COALESCE(SUM(op.products_quantity), 0) AS lifetime_sold,
                        p.products_quantity / NULLIF(COALESCE(SUM(op.products_quantity), 0) / 365.0, 0) AS years_in_stock
                    FROM products p
                    LEFT JOIN orders_products op ON p.products_id = op.products_id
                    WHERE p.products_id = {products_id}
                    GROUP BY p.products_id, p.products_quantity
                """

            results = execute_query(sql)

            if not results:
                return {'value': None, 'sql': sql}

            if products_id:
                value = results[0].get('years_in_stock')
            else:
                value = results[0].get('avg_years_in_stock')

            return {'value': value, 'sql': sql}

        # Default: direct calculation
        where_clause = self._build_where_clause(mapping, context)
        sql = f"SELECT {calculation} AS result FROM {table} WHERE {where_clause}"

        results = execute_query(sql)

        if not results:
            return {'value': None, 'sql': sql}

        return {'value': results[0].get('result'), 'sql': sql}

    def _execute_python_calculation(self, mapping: Dict, context: Dict = None) -> Dict:
        """
        Execute Python calculation

        Args:
            mapping: DatabaseMapping with Python expression
            context: Variable context for calculation

        Returns:
            Dictionary with calculation result
        """
        calculation = mapping['calculation']

        # Create safe execution environment
        safe_globals = {
            '__builtins__': {},
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sum': sum,
            'len': len
        }

        # Add context variables
        safe_locals = context.copy() if context else {}

        # Execute calculation
        try:
            result = eval(calculation, safe_globals, safe_locals)
            return {'value': result, 'python': calculation}
        except Exception as e:
            raise ValueError(f"Python calculation failed: {e}")

    def _build_where_clause(self, mapping: Dict, context: Dict = None) -> str:
        """Build WHERE clause from mapping and context"""
        parts = []

        # Add filters from mapping
        for key, value in mapping.get('filters', {}).items():
            if isinstance(value, str):
                parts.append(f"{key} = '{value}'")
            else:
                parts.append(f"{key} = {value}")

        # Add context
        if context:
            for key, value in context.items():
                if isinstance(value, str):
                    parts.append(f"{key} = '{value}'")
                else:
                    parts.append(f"{key} = {value}")

        return " AND ".join(parts) if parts else "1=1"

    def validate_workflow(self, workflow_mappings: List[Dict], context: Dict = None) -> List[ValidationResult]:
        """
        Validate an entire workflow (multiple decisions)

        Args:
            workflow_mappings: List of DatabaseMapping dictionaries
            context: Shared context for workflow

        Returns:
            List of ValidationResult objects
        """
        results = []

        for mapping in workflow_mappings:
            result = self.validate_decision(mapping, context)
            results.append(result)

        return results

    def evaluate_condition(self, condition: str, context: Dict) -> bool:
        """
        Evaluate a decision condition (e.g., "years_in_stock < 0.25")

        Args:
            condition: Condition string
            context: Variable context

        Returns:
            Boolean result
        """
        # Replace common patterns
        condition = condition.replace('≥', '>=').replace('≤', '<=')

        # Safe evaluation
        safe_globals = {
            '__builtins__': {},
        }

        try:
            result = eval(condition, safe_globals, context)
            return bool(result)
        except Exception as e:
            raise ValueError(f"Condition evaluation failed: {condition} - {e}")


def main():
    """Test the validator"""
    print("\n=== Decision Validator Test ===\n")

    validator = DecisionValidator()

    # Test 1: Years in Stock calculation
    mapping_years = {
        'decision_id': 'test_years_in_stock',
        'table': 'products',
        'calculation': 'products_quantity / (lifetime_units_sold / 365)',
        'filters': {}
    }

    print("Test 1: Years in Stock Calculation")
    result = validator.validate_decision(mapping_years, {'products_id': 12345})
    print(f"Success: {result.success}")
    print(f"Value: {result.value}")
    print(f"SQL: {result.sql_executed}")
    print(f"Time: {result.execution_time_ms:.2f}ms\n")

    # Test 2: Stock quantity check
    mapping_stock = {
        'decision_id': 'test_stock_check',
        'table': 'products',
        'column': 'products_quantity',
        'filters': {'products_status': 1}
    }

    print("Test 2: Stock Quantity Check")
    result = validator.validate_decision(mapping_stock, {'products_id': 12345})
    print(f"Success: {result.success}")
    print(f"Value: {result.value}")
    print(f"SQL: {result.sql_executed}\n")

    # Test 3: Condition evaluation
    print("Test 3: Condition Evaluation")
    context = {'years_in_stock': 0.20, 'threshold': 0.25}
    condition_result = validator.evaluate_condition('years_in_stock < threshold', context)
    print(f"Condition: years_in_stock < threshold")
    print(f"Context: {context}")
    print(f"Result: {condition_result}\n")


if __name__ == '__main__':
    main()
