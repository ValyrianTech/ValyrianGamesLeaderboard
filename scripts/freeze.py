#!/usr/bin/env python3
"""
Script to freeze the Flask app into static files for GitHub Pages deployment.
This script uses Frozen-Flask to generate a static version of the site.
"""

import os
import sys
import shutil
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask_frozen import Freezer
from app import create_app

# Create the Flask app
app = create_app()

# Configure Frozen-Flask
app.config['FREEZER_DESTINATION'] = Path(__file__).parent.parent / 'build'
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
freezer = Freezer(app)

@freezer.register_generator
def main_api_leaderboard():
    # Use the correct blueprint route name
    yield 'main.api_leaderboard', {}

@freezer.register_generator
def main_api_games():
    # Use the correct blueprint route name
    yield 'main.api_games', {}

if __name__ == '__main__':
    # Clean the build directory if it exists
    build_dir = app.config['FREEZER_DESTINATION']
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create .nojekyll file to prevent GitHub Pages from using Jekyll
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / '.nojekyll').touch()
    
    # Freeze the app
    print(f"Freezing app to {build_dir}...")
    freezer.freeze()
    
    print("Static site generation complete!")
    print(f"Files generated: {sum(1 for _ in build_dir.glob('**/*'))}")
