from flask import Blueprint, render_template, jsonify, redirect, url_for, request
import json
import os
from app.models import get_leaderboard_data, get_game_history

# Create a blueprint for our routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with overview of the leaderboard system"""
    return render_template('index.html', title="Valyrian Games Leaderboard")

@main_bp.route('/index.html')
def index_html():
    """HTML extension route for index page (GitHub Pages compatibility)"""
    return render_template('index.html', title="Valyrian Games Leaderboard")

@main_bp.route('/leaderboard')
def leaderboard():
    """Main leaderboard page showing LLM rankings"""
    leaderboard_data = get_leaderboard_data()
    return render_template('leaderboard.html', 
                          title="LLM Rankings", 
                          leaderboard=leaderboard_data)

@main_bp.route('/leaderboard.html')
def leaderboard_html():
    """HTML extension route for leaderboard page (GitHub Pages compatibility)"""
    return leaderboard()

@main_bp.route('/history')
def history():
    """Game history page - uses pure client-side pagination via API"""
    # No server-side pagination - everything handled by JavaScript via /api/games
    return render_template('game_history.html', title="Game History")

@main_bp.route('/history.html')
def history_html():
    """HTML extension route for history page (GitHub Pages compatibility)"""
    return history()

@main_bp.route('/api/leaderboard')
def api_leaderboard():
    """API endpoint for leaderboard data"""
    leaderboard_data = get_leaderboard_data()
    return jsonify(leaderboard_data)

@main_bp.route('/api/leaderboard.json')
def api_leaderboard_json():
    """JSON extension route for leaderboard API (GitHub Pages compatibility)"""
    return api_leaderboard()

@main_bp.route('/api/games')
def api_games():
    """API endpoint for game history data - returns ALL games for client-side pagination"""
    import json
    from pathlib import Path
    
    # Read ALL games directly from the games directory
    games = []
    games_dir = Path(__file__).parent.parent / 'data' / 'games'
    
    if games_dir.exists():
        for game_file in games_dir.glob('*.json'):
            with open(game_file, 'r') as f:
                game_data = json.load(f)
                games.append(game_data)
    
    # Sort games by date (newest first)
    games.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Return all games in the expected format
    pagination_data = {
        'games': games,
        'total': len(games),
        'page': 1,
        'per_page': len(games),
        'total_pages': 1,
        'has_prev': False,
        'has_next': False
    }
    
    # Ensure pagination_data is a dict (not a list for backwards compatibility)
    if isinstance(pagination_data, list):
        # Handle backwards compatibility case
        pagination_data = {
            'games': pagination_data,
            'total': len(pagination_data),
            'page': 1,
            'per_page': len(pagination_data),
            'total_pages': 1,
            'has_prev': False,
            'has_next': False
        }
    
    return jsonify(pagination_data)

@main_bp.route('/api/games.json')
def api_games_json():
    """JSON extension route for games API (GitHub Pages compatibility)"""
    return api_games()
