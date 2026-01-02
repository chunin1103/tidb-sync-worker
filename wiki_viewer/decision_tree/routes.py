"""
Decision Tree Visualizer Routes - Flask endpoints for the interactive visualizer

Production-ready implementation with:
- Real Mermaid decision trees parsed from wiki files
- Multi-tree support with tree selector
- Live path tracing
- Node feedback system

Endpoints:
- GET /wiki/decision-tree - Main visualizer page
- GET /wiki/decision-tree/api/trees - List all available trees
- GET /wiki/decision-tree/api/tree/<tree_id> - Get specific tree
- GET /wiki/decision-tree/api/vendors - Get vendor list and parameters
- POST /wiki/decision-tree/api/evaluate - Evaluate tree with inputs
- POST /wiki/decision-tree/api/feedback - Save node feedback
- GET /wiki/decision-tree/api/feedback/<node_id> - Get node feedback
"""

import os
from flask import render_template, jsonify, request, current_app
from . import decision_tree_bp
from .tree_engine import get_engine, reload_engine
from .mermaid_parser import MermaidParser, get_available_trees, reload_trees


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_wiki_dir():
    """Get the wiki directory path."""
    current_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(os.path.dirname(current_dir))
    return os.path.join(repo_root, 'wiki')


def get_feedback_file():
    """Get the feedback storage file path."""
    current_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(os.path.dirname(current_dir))
    feedback_dir = os.path.join(repo_root, 'data')
    os.makedirs(feedback_dir, exist_ok=True)
    return os.path.join(feedback_dir, 'node_feedback.json')


def load_feedback():
    """Load feedback from JSON file."""
    import json
    feedback_file = get_feedback_file()
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_feedback(feedback_data):
    """Save feedback to JSON file."""
    import json
    feedback_file = get_feedback_file()
    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, indent=2)


# ============================================================================
# PAGE ROUTES
# ============================================================================

@decision_tree_bp.route('/')
def visualizer():
    """
    Main decision tree visualizer page.

    Renders the interactive SVG-based decision tree with:
    - Tree selector dropdown
    - Vendor selection with parameter cards
    - Test input sliders
    - Live path tracing canvas
    - Node feedback system
    """
    # Get the engine (loads from config/decision_trees/)
    engine = get_engine()

    # Get vendor list for dropdown
    vendors = engine.get_vendor_list()
    vendor_details = engine.get_vendors().get('vendors', {})

    # Get the master logic tree from engine (master_logic.json)
    master_tree = engine.get_tree()

    # Also check for wiki-based trees
    wiki_dir = get_wiki_dir()
    try:
        trees = get_available_trees(wiki_dir)
        tree_list = [
            {
                'id': tree_id,
                'title': tree_data.get('metadata', {}).get('title', tree_id),
                'description': tree_data.get('metadata', {}).get('description', ''),
                'node_count': tree_data.get('metadata', {}).get('node_count', 0),
                'edge_count': tree_data.get('metadata', {}).get('edge_count', 0),
            }
            for tree_id, tree_data in trees.items()
        ]
    except Exception:
        tree_list = []

    # Use master_logic.json as the primary tree
    default_tree = master_tree if master_tree else {'tree': {'nodes': {}, 'edges': []}}
    default_tree_id = 'master_logic'

    # Load feedback counts for nodes with unresolved comments
    feedback = load_feedback()
    feedback_counts = {}
    for node_id, comments in feedback.items():
        unresolved = sum(1 for c in comments if not c.get('resolved', False))
        if unresolved > 0:
            feedback_counts[node_id] = unresolved

    return render_template(
        'decision_tree.html',
        vendors=vendors,
        vendor_details=vendor_details,
        tree=default_tree,
        tree_list=tree_list,
        default_tree_id=default_tree_id,
        feedback_counts=feedback_counts
    )


# ============================================================================
# API ROUTES - TREES
# ============================================================================

@decision_tree_bp.route('/api/trees')
def api_list_trees():
    """
    GET list of all available decision trees.

    Returns:
        {
            "success": true,
            "trees": [
                {
                    "id": "vendor-order-decision-tree",
                    "title": "Vendor Order Decision Tree",
                    "description": "...",
                    "node_count": 42,
                    "edge_count": 45
                },
                ...
            ]
        }
    """
    try:
        wiki_dir = get_wiki_dir()
        trees = get_available_trees(wiki_dir)

        tree_list = [
            {
                'id': tree_id,
                'title': tree_data.get('metadata', {}).get('title', tree_id),
                'description': tree_data.get('metadata', {}).get('description', ''),
                'node_count': tree_data.get('metadata', {}).get('node_count', 0),
                'edge_count': tree_data.get('metadata', {}).get('edge_count', 0),
                'source_file': tree_data.get('metadata', {}).get('source_file', ''),
            }
            for tree_id, tree_data in trees.items()
        ]

        return jsonify({
            'success': True,
            'trees': tree_list,
            'count': len(tree_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/tree/<tree_id>')
def api_get_tree(tree_id):
    """
    GET a specific decision tree by ID.

    Returns:
        {
            "success": true,
            "tree": {...tree data...}
        }
    """
    try:
        wiki_dir = get_wiki_dir()
        trees = get_available_trees(wiki_dir)

        if tree_id not in trees:
            return jsonify({
                'success': False,
                'error': f'Tree not found: {tree_id}'
            }), 404

        return jsonify({
            'success': True,
            'tree_id': tree_id,
            'tree': trees[tree_id]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/tree')
def api_get_default_tree():
    """
    GET the master logic tree (legacy endpoint for backwards compatibility).

    Returns:
        {
            "success": true,
            "tree": {...master_logic.json contents...}
        }
    """
    try:
        wiki_dir = get_wiki_dir()
        trees = get_available_trees(wiki_dir)

        # Return first tree or synthetic one
        if trees:
            first_tree = list(trees.values())[0]
            return jsonify({
                'success': True,
                'tree': first_tree
            })
        else:
            # Fallback to engine's synthetic tree
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


# ============================================================================
# API ROUTES - VENDORS
# ============================================================================

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


# ============================================================================
# API ROUTES - EVALUATION
# ============================================================================

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


# ============================================================================
# API ROUTES - FEEDBACK
# ============================================================================

@decision_tree_bp.route('/api/feedback/<node_id>', methods=['GET'])
def api_get_feedback(node_id):
    """
    GET feedback comments for a specific node.

    Returns:
        {
            "success": true,
            "node_id": "CHECK_SALES",
            "comments": [
                {
                    "id": "c1",
                    "author": "John",
                    "text": "This threshold seems too low",
                    "created_at": "2025-01-02T10:30:00Z",
                    "resolved": false
                },
                ...
            ],
            "unresolved_count": 1
        }
    """
    try:
        feedback = load_feedback()
        comments = feedback.get(node_id, [])
        unresolved = sum(1 for c in comments if not c.get('resolved', False))

        return jsonify({
            'success': True,
            'node_id': node_id,
            'comments': comments,
            'unresolved_count': unresolved
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/feedback', methods=['POST'])
def api_save_feedback():
    """
    POST to save a new feedback comment for a node.

    Request:
        {
            "node_id": "CHECK_SALES",
            "author": "John",
            "text": "This threshold seems too low"
        }

    Returns:
        {
            "success": true,
            "comment_id": "c123"
        }
    """
    try:
        import uuid
        from datetime import datetime

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400

        node_id = data.get('node_id')
        author = data.get('author', 'Anonymous')
        text = data.get('text', '')

        if not node_id:
            return jsonify({
                'success': False,
                'error': 'Missing required field: node_id'
            }), 400

        if not text.strip():
            return jsonify({
                'success': False,
                'error': 'Comment text cannot be empty'
            }), 400

        # Load existing feedback
        feedback = load_feedback()

        # Create new comment
        comment_id = f"c{uuid.uuid4().hex[:8]}"
        comment = {
            'id': comment_id,
            'author': author,
            'text': text.strip(),
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'resolved': False
        }

        # Add to node's comments
        if node_id not in feedback:
            feedback[node_id] = []
        feedback[node_id].append(comment)

        # Save feedback
        save_feedback(feedback)

        return jsonify({
            'success': True,
            'comment_id': comment_id,
            'comment': comment
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/feedback/<node_id>/<comment_id>/resolve', methods=['POST'])
def api_resolve_feedback(node_id, comment_id):
    """
    POST to mark a feedback comment as resolved.

    Returns:
        {
            "success": true,
            "resolved": true
        }
    """
    try:
        feedback = load_feedback()

        if node_id not in feedback:
            return jsonify({
                'success': False,
                'error': f'No feedback found for node: {node_id}'
            }), 404

        # Find and update comment
        for comment in feedback[node_id]:
            if comment.get('id') == comment_id:
                comment['resolved'] = True
                save_feedback(feedback)
                return jsonify({
                    'success': True,
                    'resolved': True
                })

        return jsonify({
            'success': False,
            'error': f'Comment not found: {comment_id}'
        }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@decision_tree_bp.route('/api/feedback/summary')
def api_feedback_summary():
    """
    GET summary of all feedback with unresolved counts per node.

    Returns:
        {
            "success": true,
            "nodes_with_feedback": 5,
            "total_unresolved": 12,
            "by_node": {
                "CHECK_SALES": 3,
                "CALC_YIS": 1,
                ...
            }
        }
    """
    try:
        feedback = load_feedback()
        by_node = {}
        total_unresolved = 0

        for node_id, comments in feedback.items():
            unresolved = sum(1 for c in comments if not c.get('resolved', False))
            if unresolved > 0:
                by_node[node_id] = unresolved
                total_unresolved += unresolved

        return jsonify({
            'success': True,
            'nodes_with_feedback': len(feedback),
            'total_unresolved': total_unresolved,
            'by_node': by_node
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# API ROUTES - ADMIN
# ============================================================================

@decision_tree_bp.route('/api/reload', methods=['POST'])
def api_reload_config():
    """
    POST to reload configuration files and re-parse wiki trees.

    Returns:
        {
            "success": true,
            "message": "Configuration reloaded",
            "tree_count": 6
        }
    """
    try:
        # Reload engine configs
        reload_engine()

        # Reload wiki trees
        wiki_dir = get_wiki_dir()
        trees = reload_trees(wiki_dir)

        return jsonify({
            'success': True,
            'message': 'Configuration reloaded successfully',
            'tree_count': len(trees)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
