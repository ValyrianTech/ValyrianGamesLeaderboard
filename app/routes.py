from flask import Blueprint, render_template, jsonify
import json
import os
from app.models import get_leaderboard_data, get_game_history

# Create a blueprint for our routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with overview of the leaderboard system"""
    return render_template('index.html', title="Valyrian Games Leaderboard")

@main_bp.route('/leaderboard')
def leaderboard():
    """Main leaderboard page showing LLM rankings"""
    leaderboard_data = get_leaderboard_data()
    return render_template('leaderboard.html', 
                          title="LLM Rankings", 
                          leaderboard=leaderboard_data)

@main_bp.route('/history')
def history():
    """Game history page showing all past games"""
    games = get_game_history()
    return render_template('game_history.html', 
                          title="Game History", 
                          games=games)

@main_bp.route('/api/leaderboard')
def api_leaderboard():
    """API endpoint for leaderboard data"""
    leaderboard_data = get_leaderboard_data()
    return jsonify(leaderboard_data)

@main_bp.route('/api/games')
def api_games():
    """API endpoint for game history data"""
    games = get_game_history()
    return jsonify(games)
