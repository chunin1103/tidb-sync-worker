"""
Decision Validation Web Interface

Flask blueprint for displaying decision tree mapping gaps
and collecting client clarifications.
"""

__version__ = "1.0.0"

from .routes import decision_validation_bp

__all__ = ['decision_validation_bp']
