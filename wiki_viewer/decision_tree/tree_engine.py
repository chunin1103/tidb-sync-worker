"""
Decision Tree Engine - Core evaluation logic for decision trees

This module handles:
- Loading and parsing master_logic.json and vendors.json
- Resolving placeholders with vendor-specific parameters
- Evaluating conditions based on user inputs
- Tracing the valid execution path through the tree
"""

import json
import os
import re
import math
from typing import Dict, List, Tuple, Any, Optional

# Path to config files
_current_dir = os.path.dirname(__file__)
_repo_root = os.path.dirname(os.path.dirname(_current_dir))
CONFIG_DIR = os.path.join(_repo_root, 'config', 'decision_trees')


class DecisionTreeEngine:
    """
    Evaluates decision tree paths based on input parameters and vendor config.

    Key responsibilities:
    1. Load and parse master_logic.json
    2. Replace placeholders with vendor parameters
    3. Evaluate conditions based on user inputs
    4. Trace the valid execution path
    """

    def __init__(self):
        self.master_tree = None
        self.vendors = None
        self._load_configs()

    def _load_configs(self):
        """Load master_logic.json and vendors.json from config directory."""
        master_path = os.path.join(CONFIG_DIR, 'master_logic.json')
        vendors_path = os.path.join(CONFIG_DIR, 'vendors.json')

        try:
            with open(master_path, 'r', encoding='utf-8') as f:
                self.master_tree = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Master logic file not found: {master_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in master_logic.json: {e}")

        try:
            with open(vendors_path, 'r', encoding='utf-8') as f:
                self.vendors = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Vendors file not found: {vendors_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in vendors.json: {e}")

    def get_tree(self) -> Dict:
        """Return the master logic tree structure."""
        return self.master_tree

    def get_vendors(self) -> Dict:
        """Return all vendor configurations."""
        return self.vendors

    def get_vendor(self, vendor_id: str) -> Optional[Dict]:
        """Get a specific vendor's configuration."""
        return self.vendors.get('vendors', {}).get(vendor_id)

    def get_vendor_list(self) -> List[Dict]:
        """Return list of vendors with id, name, and description."""
        vendors = self.vendors.get('vendors', {})
        return [
            {
                'id': vid,
                'name': v.get('name', vid),
                'description': v.get('description', ''),
                'color': v.get('display', {}).get('color', '#616161')
            }
            for vid, v in vendors.items()
        ]

    def resolve_placeholder(self, template: Any, vendor_params: Dict, variables: Dict = None) -> Any:
        """
        Replace {placeholder} patterns with actual values.

        Args:
            template: The value to resolve (string, number, or other)
            vendor_params: Vendor-specific parameters
            variables: Runtime variables (e.g., calculated years_in_stock)

        Returns:
            Resolved value with placeholders replaced
        """
        if template is None:
            return None

        if variables is None:
            variables = {}

        # If not a string, return as-is (numbers, booleans, etc.)
        if not isinstance(template, str):
            return template

        # Check if entire string is a placeholder like "{threshold_years}"
        full_match = re.match(r'^\{(\w+)\}$', template)
        if full_match:
            key = full_match.group(1)
            # Check vendor params first, then variables
            if key in vendor_params:
                return vendor_params[key]
            if key in variables:
                return variables[key]
            return template  # Return unchanged if not found

        # Replace inline placeholders in strings like "YIS >= {threshold_years}"
        def replace_match(match):
            key = match.group(1)
            if key in vendor_params:
                value = vendor_params[key]
                # Format floats nicely
                if isinstance(value, float):
                    return f"{value:.2f}" if value == int(value) else f"{value}"
                return str(value)
            if key in variables:
                value = variables[key]
                if isinstance(value, float):
                    return f"{value:.2f}"
                return str(value)
            return match.group(0)  # Return unchanged

        return re.sub(r'\{(\w+)\}', replace_match, template)

    def resolve_all_labels(self, vendor_id: str) -> Dict[str, str]:
        """
        Resolve all labels in the tree for a given vendor.

        Returns dict mapping node/edge IDs to resolved label strings.
        """
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {}

        params = vendor.get('parameters', {})
        resolved = {}
        tree = self.master_tree.get('tree', {})

        # Resolve node labels
        for node_id, node in tree.get('nodes', {}).items():
            label = node.get('label', '')
            resolved[node_id] = self.resolve_placeholder(label, params)

            # Also resolve description
            desc = node.get('description', '')
            resolved[f"{node_id}_desc"] = self.resolve_placeholder(desc, params)

            # Resolve result reason if present
            result = node.get('result', {})
            if result:
                reason = result.get('reason', '')
                resolved[f"{node_id}_reason"] = self.resolve_placeholder(reason, params)

        # Resolve edge labels
        for edge in tree.get('edges', []):
            edge_id = edge.get('id', '')
            label = edge.get('label', '')
            resolved[edge_id] = self.resolve_placeholder(label, params)

        return resolved

    def evaluate_condition(self, condition: Dict, variables: Dict, vendor_params: Dict) -> bool:
        """
        Evaluate a single condition against current variables.

        Args:
            condition: {field, operator, value}
            variables: Current runtime variables (quantity_in_stock, purchased, etc.)
            vendor_params: Vendor parameters for placeholder resolution

        Returns:
            Boolean result of the condition
        """
        field = condition.get('field', '')
        operator = condition.get('operator', '==')
        compare_value = condition.get('value')

        # Resolve field (might be a placeholder like "{allow_cascade}")
        resolved_field = self.resolve_placeholder(field, vendor_params, variables)

        # Get actual value from variables or use resolved field directly
        if resolved_field in variables:
            actual_value = variables[resolved_field]
        else:
            # The field itself might be a resolved value (for {allow_cascade})
            actual_value = resolved_field

        # Resolve compare value (might be a placeholder)
        resolved_compare = self.resolve_placeholder(compare_value, vendor_params, variables)

        # Handle None/null values
        if actual_value is None:
            return False

        # Perform comparison
        try:
            if operator == '>=':
                return float(actual_value) >= float(resolved_compare)
            elif operator == '>':
                return float(actual_value) > float(resolved_compare)
            elif operator == '<=':
                return float(actual_value) <= float(resolved_compare)
            elif operator == '<':
                return float(actual_value) < float(resolved_compare)
            elif operator == '==':
                # Handle boolean comparison
                if isinstance(resolved_compare, bool):
                    return actual_value == resolved_compare
                # Handle numeric comparison
                try:
                    return float(actual_value) == float(resolved_compare)
                except (ValueError, TypeError):
                    return str(actual_value) == str(resolved_compare)
            elif operator == '!=':
                try:
                    return float(actual_value) != float(resolved_compare)
                except (ValueError, TypeError):
                    return str(actual_value) != str(resolved_compare)
            else:
                return False
        except (ValueError, TypeError):
            return False

    def execute_calculation(self, node: Dict, variables: Dict, vendor_params: Dict) -> Dict:
        """
        Execute a calculation node and update variables.

        Args:
            node: The calculation node
            variables: Current runtime variables
            vendor_params: Vendor parameters

        Returns:
            Updated variables dict
        """
        formula = node.get('formula', '')
        output_field = node.get('output_field', '')

        if not formula or not output_field:
            return variables

        # Simple formula evaluation (for YIS = quantity / purchased)
        try:
            # Replace variable names with actual values
            eval_formula = formula
            for var_name, var_value in variables.items():
                if var_value is not None:
                    eval_formula = eval_formula.replace(var_name, str(var_value))

            # Safe evaluation (only allow basic math operations)
            result = eval(eval_formula, {"__builtins__": {}}, {"math": math})

            # Handle division by zero
            if result == float('inf') or result == float('-inf') or result != result:
                result = None

            variables[output_field] = result
        except Exception:
            variables[output_field] = None

        return variables

    def find_outgoing_edge(self, node_id: str, condition_result: Optional[bool] = None) -> Optional[Dict]:
        """
        Find the outgoing edge from a node.

        Args:
            node_id: Current node ID
            condition_result: True/False for decision nodes, None for others

        Returns:
            The matching edge dict or None
        """
        tree = self.master_tree.get('tree', {})
        edges = tree.get('edges', [])

        for edge in edges:
            if edge.get('from') != node_id:
                continue

            # If condition_result is specified, match it
            edge_result = edge.get('condition_result')
            if condition_result is not None and edge_result is not None:
                if edge_result == condition_result:
                    return edge
            elif edge_result is None:
                # Edge without condition_result (for non-decision nodes)
                return edge

        # Fallback: return first matching edge
        for edge in edges:
            if edge.get('from') == node_id:
                return edge

        return None

    def calculate_reorder_quantity(self, variables: Dict, vendor_params: Dict, target_field: str) -> int:
        """
        Calculate the reorder quantity to reach target.

        Args:
            variables: Current runtime variables
            vendor_params: Vendor parameters
            target_field: Field name for target (e.g., "{target_years}")

        Returns:
            Calculated reorder quantity (integer, minimum 1)
        """
        purchased = variables.get('purchased', 0)
        quantity = variables.get('quantity_in_stock', 0)

        if purchased <= 0:
            return 0

        # Resolve target
        target = self.resolve_placeholder(target_field, vendor_params, variables)
        if isinstance(target, str):
            try:
                target = float(target)
            except ValueError:
                target = vendor_params.get('target_years', 0.35)

        # Calculate target quantity and deficit
        target_quantity = purchased * target
        deficit = target_quantity - quantity

        if deficit <= 0:
            return 0

        # Apply rounding
        rounding_method = vendor_params.get('rounding_method', 'ceil')
        rounding_multiple = vendor_params.get('rounding_multiple', 1)

        if rounding_method == 'ceil':
            reorder = math.ceil(deficit)
        elif rounding_method == 'floor':
            reorder = math.floor(deficit)
        else:
            reorder = round(deficit)

        # Round to multiple if specified
        if rounding_multiple > 1:
            reorder = math.ceil(reorder / rounding_multiple) * rounding_multiple

        # Add zero stock bonus if applicable
        zero_bonus = vendor_params.get('zero_stock_bonus', 0)
        if quantity == 0 and zero_bonus > 0:
            reorder += zero_bonus

        return max(1, reorder)

    def trace_path(self, vendor_id: str, inputs: Dict) -> Dict:
        """
        Trace execution path through the tree with given inputs.

        Args:
            vendor_id: The vendor configuration to use
            inputs: User inputs (quantity_in_stock, purchased)

        Returns:
            {
                'success': bool,
                'path': List of node IDs in order visited,
                'active_edges': List of edge IDs traversed,
                'variables': Dict of all calculated variables,
                'result': Final result node info,
                'reorder_quantity': Calculated quantity (if applicable),
                'error': Error message (if any)
            }
        """
        vendor = self.get_vendor(vendor_id)
        if not vendor:
            return {
                'success': False,
                'error': f"Unknown vendor: {vendor_id}",
                'path': [],
                'active_edges': [],
                'variables': {},
                'result': None
            }

        params = vendor.get('parameters', {})
        tree = self.master_tree.get('tree', {})
        nodes = tree.get('nodes', {})

        # Initialize variables with inputs
        variables = {
            'quantity_in_stock': inputs.get('quantity_in_stock', 0),
            'purchased': inputs.get('purchased', 0)
        }

        path = []
        active_edges = []
        max_iterations = 50  # Safety limit
        iteration = 0

        # Start at root
        current_node_id = tree.get('root', 'START')

        while current_node_id and iteration < max_iterations:
            iteration += 1
            current_node = nodes.get(current_node_id)

            if not current_node:
                break

            path.append(current_node_id)
            node_type = current_node.get('type', '')

            # Handle node based on type
            if node_type == 'start':
                # Just move to next node
                edge = self.find_outgoing_edge(current_node_id)
                if edge:
                    active_edges.append(edge['id'])
                    current_node_id = edge.get('to')
                else:
                    break

            elif node_type == 'calculation':
                # Execute calculation
                variables = self.execute_calculation(current_node, variables, params)

                # Move to next node
                edge = self.find_outgoing_edge(current_node_id)
                if edge:
                    active_edges.append(edge['id'])
                    current_node_id = edge.get('to')
                else:
                    break

            elif node_type == 'decision':
                # Evaluate condition
                condition = current_node.get('condition', {})
                result = self.evaluate_condition(condition, variables, params)

                # Find appropriate edge based on result
                edge = self.find_outgoing_edge(current_node_id, result)
                if edge:
                    active_edges.append(edge['id'])
                    current_node_id = edge.get('to')
                else:
                    break

            elif node_type == 'result':
                # Terminal node - we're done
                result_info = current_node.get('result', {})

                # Calculate reorder quantity if needed
                reorder_qty = None
                if result_info.get('calculate_quantity'):
                    target_field = result_info.get('target_field', '{target_years}')
                    reorder_qty = self.calculate_reorder_quantity(variables, params, target_field)

                return {
                    'success': True,
                    'path': path,
                    'active_edges': active_edges,
                    'variables': variables,
                    'result': {
                        'node_id': current_node_id,
                        'action': result_info.get('action'),
                        'priority': result_info.get('priority'),
                        'reason': self.resolve_placeholder(result_info.get('reason', ''), params, variables),
                        'color': result_info.get('color', '#616161')
                    },
                    'reorder_quantity': reorder_qty,
                    'error': None
                }

            else:
                # Unknown node type
                break

        # Didn't reach a result node
        return {
            'success': False,
            'path': path,
            'active_edges': active_edges,
            'variables': variables,
            'result': None,
            'reorder_quantity': None,
            'error': 'Path did not reach a result node'
        }


# Singleton instance
_engine_instance = None

def get_engine() -> DecisionTreeEngine:
    """Get or create the singleton engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DecisionTreeEngine()
    return _engine_instance


def reload_engine():
    """Force reload of configuration files."""
    global _engine_instance
    _engine_instance = DecisionTreeEngine()
    return _engine_instance
