"""
Decision Tree Visualizer Routes - Flask endpoints for the interactive visualizer

Endpoints:
- GET /wiki/decision-tree - Main visualizer page
- GET /wiki/decision-tree/api/tree - Get master logic tree
- GET /wiki/decision-tree/api/vendors - Get vendor list and parameters
- POST /wiki/decision-tree/api/evaluate - Evaluate tree with inputs
- POST /wiki/decision-tree/api/resolve-labels - Get labels with placeholders resolved
"""

from flask import render_template, jsonify, request
from . import decision_tree_bp
from .tree_engine import get_engine, reload_engine


# ============================================================================
# PAGE ROUTES
# ============================================================================

@decision_tree_bp.route('/')
def visualizer():
    """
    Main decision tree visualizer page.

    Renders the interactive SVG-based decision tree with:
    - Vendor selection sidebar
    - Test input controls
    - Live path tracing canvas
    """
    engine = get_engine()

    # Get vendor list for dropdown
    vendors = engine.get_vendor_list()

    # Get the tree structure
    tree = engine.get_tree()

    return render_template(
        'decision_tree.html',
        vendors=vendors,
        tree=tree
    )


# ============================================================================
# API ROUTES
# ============================================================================

@decision_tree_bp.route('/api/tree')
def api_get_tree():
    """
    GET the master logic tree (with placeholders).

    Returns:
        {
            "success": true,
            "tree": {...master_logic.json contents...}
        }
    """
    try:
        engine = get_engine()
        tree = engine.get_tree()

        return jsonify({
            'success': True,
            'tree': tree
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/vendors')
def api_get_vendors():
    """
    GET list of available vendors and their parameters.

    Returns:
        {
            "success": true,
            "vendors": [...vendor list...],
            "vendor_details": {...full vendor configs...}
        }
    """
    try:
        engine = get_engine()
        vendor_list = engine.get_vendor_list()
        all_vendors = engine.get_vendors()

        return jsonify({
            'success': True,
            'vendors': vendor_list,
            'vendor_details': all_vendors.get('vendors', {}),
            'parameter_descriptions': all_vendors.get('parameter_descriptions', {})
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/evaluate', methods=['POST'])
def api_evaluate_tree():
    """
    POST to evaluate tree with specific inputs and vendor.

    Request:
        {
            "vendor_id": "bullseye",
            "inputs": {
                "quantity_in_stock": 50,
                "purchased": 100
            }
        }

    Returns:
        {
            "success": true,
            "path": ["START", "CHECK_SALES", ...],
            "active_edges": ["e1", "e2", ...],
            "variables": {"years_in_stock": 0.5, ...},
            "result": {...},
            "reorder_quantity": 15
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        # Validate required fields
        vendor_id = data.get('vendor_id')
        if not vendor_id:
            return jsonify({
                'success': False,
                'error': 'Missing required field: vendor_id'
            }), 400

        inputs = data.get('inputs', {})

        # Validate inputs
        quantity = inputs.get('quantity_in_stock')
        purchased = inputs.get('purchased')

        if quantity is None:
            return jsonify({
                'success': False,
                'error': 'Missing required input: quantity_in_stock'
            }), 400

        if purchased is None:
            return jsonify({
                'success': False,
                'error': 'Missing required input: purchased'
            }), 400

        # Convert to numbers
        try:
            inputs['quantity_in_stock'] = float(quantity)
            inputs['purchased'] = float(purchased)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Inputs must be numeric values'
            }), 400

        # Validate non-negative
        if inputs['quantity_in_stock'] < 0:
            return jsonify({
                'success': False,
                'error': 'quantity_in_stock cannot be negative'
            }), 400

        if inputs['purchased'] < 0:
            return jsonify({
                'success': False,
                'error': 'purchased cannot be negative'
            }), 400

        # Trace the path
        engine = get_engine()
        result = engine.trace_path(vendor_id, inputs)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/resolve-labels', methods=['POST'])
def api_resolve_labels():
    """
    POST to get all labels with placeholders resolved for a vendor.

    Request:
        {"vendor_id": "bullseye"}

    Returns:
        {
            "success": true,
            "labels": {
                "CHECK_THRESHOLD": "YIS >= 0.25?",
                "e5": "Yes (>= 0.25)",
                ...
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        vendor_id = data.get('vendor_id')
        if not vendor_id:
            return jsonify({
                'success': False,
                'error': 'Missing required field: vendor_id'
            }), 400

        engine = get_engine()

        # Verify vendor exists
        vendor = engine.get_vendor(vendor_id)
        if not vendor:
            return jsonify({
                'success': False,
                'error': f'Unknown vendor: {vendor_id}'
            }), 400

        labels = engine.resolve_all_labels(vendor_id)

        return jsonify({
            'success': True,
            'vendor_id': vendor_id,
            'labels': labels
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/reload', methods=['POST'])
def api_reload_config():
    """
    POST to reload configuration files (for development/admin use).

    Returns:
        {
            "success": true,
            "message": "Configuration reloaded"
        }
    """
    try:
        reload_engine()
        return jsonify({
            'success': True,
            'message': 'Configuration reloaded successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
