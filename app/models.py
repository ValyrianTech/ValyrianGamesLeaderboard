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

def get_game_history(limit=None):
    """
    Read and return the game history data from the games directory.
    Each game is stored in a separate JSON file.
    
    Args:
        limit: Optional limit on number of games to return
    
    Returns:
        List of game data dictionaries, sorted by date (newest first)
    """
    games = []
    
    # Create games directory if it doesn't exist
    if not GAMES_DIR.exists():
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        return games
    
    # Read all game files
    for game_file in GAMES_DIR.glob('*.json'):
        with open(game_file, 'r') as f:
            game_data = json.load(f)
            games.append(game_data)
    
    # Sort games by date (newest first)
    games.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Apply limit if specified
    if limit and isinstance(limit, int):
        games = games[:limit]
        
    return games

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
