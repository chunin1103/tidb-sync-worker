"""
Reports Viewer Blueprint
Handles CSV-based reorder calculations with decision tree logic
"""
from flask import Blueprint

reports_bp = Blueprint(
    'reports',
    __name__,
    url_prefix='/reports',
    template_folder='templates'
)

# Import routes after blueprint creation to avoid circular imports
from . import routes
