import json
import os
from pathlib import Path

# Path to data directory
DATA_DIR = Path(__file__).parent.parent / 'data'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'
GAMES_DIR = DATA_DIR / 'games'

def get_leaderboard_data():
    """
    Read and return the leaderboard data from the JSON file.
    If the file doesn't exist yet, return an empty leaderboard.
    """
    if LEADERBOARD_FILE.exists():
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    else:
        # Return empty leaderboard structure
        return {
            "last_updated": "",
            "models": []
        }

def get_game_history(limit=None, page=1, per_page=20):
    """
    Read and return the game history data from the games directory with pagination support.
    Each game is stored in a separate JSON file.
    
    Args:
        limit: Optional limit on number of games to return (for backwards compatibility)
        page: Page number (1-indexed)
        per_page: Number of games per page
    
    Returns:
        Dictionary containing:
        - games: List of game data dictionaries for the current page
        - total: Total number of games
        - page: Current page number
        - per_page: Games per page
        - total_pages: Total number of pages
        - has_prev: Whether there's a previous page
        - has_next: Whether there's a next page
    """
    games = []
    
    # Create games directory if it doesn't exist
    if not GAMES_DIR.exists():
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        return {
            'games': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 0,
            'has_prev': False,
            'has_next': False
        }
    
    # Read all game files
    for game_file in GAMES_DIR.glob('*.json'):
        with open(game_file, 'r') as f:
            game_data = json.load(f)
            games.append(game_data)
    
    # Sort games by date (newest first)
    games.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Handle backwards compatibility with limit parameter
    if limit and isinstance(limit, int):
        games = games[:limit]
        return games
    
    # Calculate pagination
    total = len(games)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages)) if total_pages > 0 else 1
    
    # Calculate start and end indices for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    # Get games for current page
    page_games = games[start_idx:end_idx]
    
    return {
        'games': page_games,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }

def get_game_by_id(game_id):
    """
    Get a specific game by its ID.
    
    Args:
        game_id: The ID of the game to retrieve
        
    Returns:
        Game data dictionary or None if not found
    """
    game_file = GAMES_DIR / f"{game_id}.json"
    
    if game_file.exists():
        with open(game_file, 'r') as f:
            return json.load(f)
    
    return None
