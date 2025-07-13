#!/usr/bin/env python3
"""
Development server entry point for the Valyrian Games Leaderboard.
This script runs a Flask development server for local testing.
"""

from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
