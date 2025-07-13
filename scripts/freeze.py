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
app.config['FREEZER_RELATIVE_URLS'] = False  # Use absolute URLs instead of relative
app.config['FREEZER_IGNORE_MIMETYPE_WARNINGS'] = True
app.config['FREEZER_DEFAULT_MIMETYPE'] = 'text/html'  # Set default MIME type for all files
app.config['FREEZER_BASE_URL'] = 'https://valyriantech.github.io/ValyrianGamesLeaderboard/'

freezer = Freezer(app)

@freezer.register_generator
def main_api_leaderboard_json():
    # Use the correct blueprint route name with extension
    yield 'main.api_leaderboard_json', {}

@freezer.register_generator
def main_api_games_json():
    # Use the correct blueprint route name with extension
    yield 'main.api_games_json', {}

@freezer.register_generator
def main_leaderboard_html():
    # Generate leaderboard.html
    yield 'main.leaderboard_html', {}

@freezer.register_generator
def main_history_html():
    # Generate history.html
    yield 'main.history_html', {}

@freezer.register_generator
def main_index_html():
    # Generate index.html
    yield 'main.index_html', {}

if __name__ == '__main__':
    # Clean the build directory if it exists
    build_dir = app.config['FREEZER_DESTINATION']
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # Create .nojekyll file to prevent GitHub Pages from using Jekyll
    build_dir.mkdir(parents=True, exist_ok=True)
    (build_dir / '.nojekyll').touch()
    
    # Create a _config.yml file to set correct MIME types for GitHub Pages
    with open(build_dir / '_config.yml', 'w') as f:
        f.write("""
# GitHub Pages configuration
include:
  - ".nojekyll"
  - ".htaccess"
defaults:
  -
    scope:
      path: "" # all files
    values:
      layout: "default"
      
# Set proper MIME types
webrick:
  headers:
    Content-Type: text/html; charset=utf-8
""")
    
    # Create an .htaccess file to set correct MIME types
    with open(build_dir / '.htaccess', 'w') as f:
        f.write("""
# Set default MIME type for HTML files
AddType text/html .html

# Ensure HTML files are served with the right content type
<FilesMatch "\\.(html)$">
    ForceType text/html
    Header set Content-Type "text/html; charset=UTF-8"
</FilesMatch>

# Ensure JSON files are served with the right content type
<FilesMatch "\\.(json)$">
    ForceType application/json
    Header set Content-Type "application/json; charset=UTF-8"
</FilesMatch>

# Ensure JavaScript files are served with the right content type
<FilesMatch "\\.(js)$">
    ForceType application/javascript
    Header set Content-Type "application/javascript; charset=UTF-8"
</FilesMatch>

# Ensure CSS files are served with the right content type
<FilesMatch "\\.(css)$">
    ForceType text/css
    Header set Content-Type "text/css; charset=UTF-8"
</FilesMatch>
""")
    
    # Create a MIME types file for GitHub Pages
    with open(build_dir / 'mime.types', 'w') as f:
        f.write("""
text/html                             html htm
application/json                      json
application/javascript                js
text/css                              css
""")
    
    # Freeze the app
    print(f"Freezing app to {build_dir}...")
    freezer.freeze()
    
    # Count the number of files generated
    file_count = sum(1 for _ in build_dir.rglob('*') if _.is_file())
    print(f"Static site generation complete!")
    print(f"Files generated: {file_count}")
    
    # Create a .github-pages-mime.json file in the root of the build directory
    with open(build_dir / '.github-pages-mime.json', 'w') as f:
        f.write("""
{
  "*.html": "text/html",
  "*.json": "application/json",
  "*.js": "application/javascript",
  "*.css": "text/css"
}
""")
