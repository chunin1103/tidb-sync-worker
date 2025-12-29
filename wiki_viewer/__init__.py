"""
Wiki Viewer Blueprint - Interactive documentation viewer with Mermaid diagram linking

This module provides an interactive web interface for browsing the Production wiki,
featuring bidirectional linking between Mermaid diagram nodes and markdown text sections.

Features:
- Workflow overview with visual timeline
- Markdown rendering with Mermaid diagram support
- Interactive node-to-text mapping system
- Admin mode for creating mappings
- Color-coded highlighting with tooltips
"""

from flask import Blueprint
import os

# Get the absolute path to wiki files
_current_dir = os.path.dirname(__file__)
_repo_root = os.path.dirname(_current_dir)
WIKI_ROOT_PATH = os.path.join(_repo_root, 'wiki')

# Create blueprint
wiki_bp = Blueprint(
    'wiki',
    __name__,
    url_prefix='/wiki',
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/wiki'
)

# Import routes after blueprint creation (to avoid circular imports)
from . import routes
