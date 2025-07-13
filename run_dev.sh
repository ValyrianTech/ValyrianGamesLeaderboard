#!/bin/bash
# Development script to run the Flask application

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the Flask app
echo "Starting Flask development server..."
python run.py
