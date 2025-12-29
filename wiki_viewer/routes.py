"""
Wiki Viewer Routes

Flask routes for the interactive wiki viewer:
- Pages: overview, browser, file viewer, admin
- APIs: files, mappings CRUD, color suggestions
"""

import os
import logging
from flask import render_template, jsonify, request, abort
from . import wiki_bp, WIKI_ROOT_PATH
from .markdown_parser import WikiMarkdownParser
from .mapping_manager import MappingManager

logger = logging.getLogger(__name__)

# Initialize parser and mapping manager
_repo_root = os.path.dirname(os.path.dirname(__file__))
_mappings_path = os.path.join(_repo_root, 'wiki_mappings.json')

parser = WikiMarkdownParser(WIKI_ROOT_PATH)
mapper = MappingManager(_mappings_path)


# =============================================================================
# PAGE ROUTES
# =============================================================================

@wiki_bp.route('/')
def workflow_overview():
    """
    Main page: Workflow overview with visual timeline

    Shows 4 main stages: Input → Rules → Decision → Output
    Click each stage to navigate to that folder
    """
    # Get folder stats (file counts)
    folder_stats = _get_folder_stats()

    return render_template('workflow_overview.html', folder_stats=folder_stats)


@wiki_bp.route('/browse')
def file_browser():
    """
    File browser: Tree view of all 7 folders + 31 files

    Query params:
        - folder: Filter to specific folder (e.g., "03_Decision_Workflows")
    """
    folder_filter = request.args.get('folder', None)

    # Get directory structure
    structure = _get_wiki_structure(folder_filter)

    return render_template('file_browser.html',
                           structure=structure,
                           folder_filter=folder_filter)


@wiki_bp.route('/view/<path:filepath>')
def view_file(filepath):
    """
    Markdown file viewer with Mermaid diagrams

    Args:
        filepath: Relative path to wiki file (with or without .md extension)

    Features:
        - Renders markdown to HTML
        - Preserves Mermaid diagrams
        - Shows table of contents
        - Loads mappings for bidirectional linking
        - Admin mode toggle
    """
    # Add .md extension if not present
    if not filepath.endswith('.md'):
        filepath = filepath + '.md'

    # Construct absolute path
    absolute_path = os.path.join(WIKI_ROOT_PATH, filepath)

    # Check if file exists
    if not os.path.exists(absolute_path):
        abort(404, f"Wiki file not found: {filepath}")

    # Read file content
    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading wiki file {filepath}: {e}")
        abort(500, f"Error reading file: {str(e)}")

    # Parse markdown
    result = parser.parse(content, filepath)

    # Get mappings for this file
    mappings = mapper.get_mappings(filepath)

    # Build breadcrumb trail
    breadcrumb = _build_breadcrumb(filepath)

    return render_template('wiki_file.html',
                           file_path=filepath,
                           filename=os.path.basename(filepath),
                           content=result['html'],
                           toc=result['toc'],
                           diagram_count=result['diagram_count'],
                           mappings=mappings,
                           breadcrumb_trail=breadcrumb)


@wiki_bp.route('/admin')
def admin_documentation():
    """
    Admin documentation page

    Explains how to use admin mode to create mappings
    """
    return render_template('admin_mode.html')


# =============================================================================
# API ROUTES (JSON)
# =============================================================================

@wiki_bp.route('/api/files')
def api_list_files():
    """
    List all wiki files in tree structure

    Returns:
        JSON: {
            "folders": [...],
            "files": [...]
        }
    """
    structure = _get_wiki_structure()
    return jsonify(structure)


@wiki_bp.route('/api/mappings/<path:filepath>', methods=['GET'])
def api_get_mappings(filepath):
    """
    Get all mappings for a specific file

    Args:
        filepath: Relative path to wiki file

    Returns:
        JSON: {
            "file": "...",
            "mappings": [...]
        }
    """
    # Add .md extension if not present
    if not filepath.endswith('.md'):
        filepath = filepath + '.md'

    mappings = mapper.get_mappings(filepath)

    return jsonify({
        'file': filepath,
        'mappings': mappings
    })


@wiki_bp.route('/api/mappings/<path:filepath>', methods=['POST'])
def api_save_mapping(filepath):
    """
    Save new mapping for a file

    Args:
        filepath: Relative path to wiki file

    Request JSON:
        {
            "diagram_id": "diagram_0",
            "node_id": "B",
            "section_id": "step-1-load-snapshot",
            "color": "#ffeb3b",
            "label": "Load & Snapshot",
            "preview_text": "Input: Excel or CSV file..."
        }

    Returns:
        JSON: {
            "success": true,
            "mapping_id": "map_001"
        }
    """
    # Add .md extension if not present
    if not filepath.endswith('.md'):
        filepath = filepath + '.md'

    # Get mapping data from request
    mapping_data = request.get_json()

    # Validate required fields
    required_fields = ['diagram_id', 'node_id', 'section_id', 'color', 'label', 'preview_text']
    for field in required_fields:
        if field not in mapping_data:
            return jsonify({
                'success': False,
                'error': f'Missing required field: {field}'
            }), 400

    # Add mapping
    try:
        mapping_id = mapper.add_mapping(filepath, mapping_data)

        logger.info(f"Created mapping {mapping_id} for {filepath}: {mapping_data['node_id']} → {mapping_data['section_id']}")

        return jsonify({
            'success': True,
            'mapping_id': mapping_id
        })

    except Exception as e:
        logger.error(f"Error saving mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@wiki_bp.route('/api/mappings/<path:filepath>', methods=['DELETE'])
def api_delete_mapping(filepath):
    """
    Delete a specific mapping

    Args:
        filepath: Relative path to wiki file

    Query params:
        - id: Mapping ID to delete (e.g., "map_001")

    Returns:
        JSON: {
            "success": true
        }
    """
    # Add .md extension if not present
    if not filepath.endswith('.md'):
        filepath = filepath + '.md'

    # Get mapping ID from query params
    mapping_id = request.args.get('id')
    if not mapping_id:
        return jsonify({
            'success': False,
            'error': 'Missing mapping ID parameter'
        }), 400

    # Delete mapping
    success = mapper.delete_mapping(filepath, mapping_id)

    if success:
        logger.info(f"Deleted mapping {mapping_id} from {filepath}")
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': f'Mapping {mapping_id} not found'
        }), 404


@wiki_bp.route('/api/suggest-color')
def api_suggest_color():
    """
    Suggest next available color from palette

    Query params:
        - file: Relative path to wiki file

    Returns:
        JSON: {
            "color": "#ffeb3b"
        }
    """
    filepath = request.args.get('file', '')

    # Add .md extension if not present
    if filepath and not filepath.endswith('.md'):
        filepath = filepath + '.md'

    color = mapper.suggest_next_color(filepath)

    return jsonify({'color': color})


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_wiki_structure(folder_filter=None):
    """
    Get wiki directory structure

    Args:
        folder_filter: Optional folder name to filter to

    Returns:
        Dict with folders and files lists
    """
    folders = []
    files = []

    # List all items in wiki root
    for item in os.listdir(WIKI_ROOT_PATH):
        item_path = os.path.join(WIKI_ROOT_PATH, item)

        if os.path.isdir(item_path):
            # It's a folder
            if folder_filter and item != folder_filter:
                continue

            # Count files in folder
            file_count = len([f for f in os.listdir(item_path) if f.endswith('.md')])

            folders.append({
                'name': item,
                'path': item,
                'file_count': file_count
            })

        elif item.endswith('.md'):
            # It's a markdown file in root
            if not folder_filter:
                files.append({
                    'name': item,
                    'path': item,
                    'has_mappings': mapper.get_mapping_count(item) > 0
                })

    # If filtering to a specific folder, list its files
    if folder_filter:
        folder_path = os.path.join(WIKI_ROOT_PATH, folder_filter)
        if os.path.exists(folder_path):
            for item in os.listdir(folder_path):
                if item.endswith('.md'):
                    relative_path = os.path.join(folder_filter, item)
                    files.append({
                        'name': item,
                        'path': relative_path,
                        'has_mappings': mapper.get_mapping_count(relative_path) > 0
                    })

    # Sort folders and files
    folders.sort(key=lambda x: x['name'])
    files.sort(key=lambda x: x['name'])

    return {
        'folders': folders,
        'files': files
    }


def _get_folder_stats():
    """
    Get statistics for each workflow stage folder

    Returns:
        Dict mapping folder name to file count
    """
    stats = {}

    # Define the 7 workflow folders
    folders = [
        '01_Input_Data_Processing',
        '02_Business_Rules',
        '03_Decision_Workflows',
        '04_Output_Generation',
        '05_System_Specific',
        '06_Reference_Data',
        '07_Archive'
    ]

    for folder in folders:
        folder_path = os.path.join(WIKI_ROOT_PATH, folder)
        if os.path.exists(folder_path):
            file_count = len([f for f in os.listdir(folder_path) if f.endswith('.md')])
            stats[folder] = file_count

    return stats


def _build_breadcrumb(filepath):
    """
    Build breadcrumb trail for file path

    Args:
        filepath: Relative file path (e.g., "03_Decision_Workflows/Inventory_Filtering_Workflow.md")

    Returns:
        List of folder names (excluding filename)
    """
    parts = filepath.split('/')
    # Return all parts except the last one (filename)
    return parts[:-1]
