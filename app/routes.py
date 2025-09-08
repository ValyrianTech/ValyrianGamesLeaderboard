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
    """Game history page showing past games with pagination"""
    from app.models import get_game_history
    
    # Check if this is for static site generation (needs all games)
    static_site = request.args.get('static_site', 'false').lower() == 'true'
    
    if static_site:
        # For static site generation, get ALL games without pagination
        all_games_data = get_game_history(limit=None, page=1, per_page=999999)
        # Ensure we get all games by using the total count as per_page
        if isinstance(all_games_data, dict) and 'total' in all_games_data:
            total_games = all_games_data['total']
            pagination_data = get_game_history(page=1, per_page=total_games)
        else:
            pagination_data = all_games_data
    else:
        # Normal pagination for regular web requests
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Ensure per_page is within reasonable bounds
        per_page = max(5, min(per_page, 100))
        
        # Get paginated game history
        pagination_data = get_game_history(page=page, per_page=per_page)
    
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
    
    return render_template('game_history.html', 
                          title="Game History", 
                          games=pagination_data['games'],
                          pagination=pagination_data)

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
    """API endpoint for game history data with pagination support"""
    # Get pagination parameters from URL
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Ensure per_page is within reasonable bounds
    per_page = max(5, min(per_page, 100))
    
    # Get paginated game history
    pagination_data = get_game_history(page=page, per_page=per_page)
    
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
