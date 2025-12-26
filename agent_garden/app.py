#!/usr/bin/env python3
"""
Agent Garden Flask App - Launcher Script
This script launches the main Flask application from src/core/app.py
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
from src.core.app import app

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.getenv('PORT', 5001))

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    )
