"""
Decision Tree Visualizer - Interactive decision tree with vendor configurations

This module provides an interactive visualization of decision trees with:
- Dynamic placeholder resolution based on vendor selection
- Live path tracing through the decision tree
- SVG-based rendering with click/hover interactions

The core concept is "One Tree, Many Configurations" - a single master logic tree
with placeholders that get resolved at runtime based on vendor-specific parameters.
"""

from flask import Blueprint

# Create blueprint for decision tree routes
decision_tree_bp = Blueprint(
    'decision_tree',
    __name__,
    url_prefix='/decision-tree'
)

# Import routes after blueprint creation (to avoid circular imports)
from . import routes
