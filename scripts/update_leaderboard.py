#!/usr/bin/env python3
"""
Script to update the leaderboard with new game results.
This script:
1. Takes a game result file as input
2. Updates the leaderboard using TrueSkill
3. Saves the game result to the games directory
4. Optionally commits the changes to the Git repository

Additional features:
- Can recalculate the entire leaderboard from all game files (--recalculate)
"""

import os
import sys
import json
import argparse
import uuid
from datetime import datetime
from pathlib import Path
import subprocess

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.trueskill_calculator import update_leaderboard_from_game

# Path to data directory
DATA_DIR = Path(__file__).parent.parent / 'data'
GAMES_DIR = DATA_DIR / 'games'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'

def ensure_data_dirs():
    """Ensure data directories exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GAMES_DIR.mkdir(parents=True, exist_ok=True)

def validate_game_data(game_data):
    """
    Validate that the game data has the required fields
    
    Args:
        game_data: Dictionary containing game data
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['participants', 'ranks']
    
    for field in required_fields:
        if field not in game_data:
            print(f"Error: Missing required field '{field}' in game data")
            return False
    
    if len(game_data['participants']) != len(game_data['ranks']):
        print("Error: 'participants' and 'ranks' must be the same length")
        return False
    
    return True

def save_game_result(game_data):
    """
    Save the game result to the games directory
    
    Args:
        game_data: Dictionary containing game data
        
    Returns:
        Path to the saved game file
    """
    # Generate a game ID if not provided
    if 'game_id' not in game_data:
        game_data['game_id'] = str(uuid.uuid4())
    
    # Add timestamp if not provided
    if 'date' not in game_data:
        game_data['date'] = datetime.now().isoformat()
    
    # Save to file
    game_file = GAMES_DIR / f"{game_data['game_id']}.json"
    with open(game_file, 'w') as f:
        json.dump(game_data, f, indent=2)
    
    return game_file

def commit_changes(game_id, commit_message=None):
    """
    Commit changes to the Git repository
    
    Args:
        game_id: ID of the game that was added
        commit_message: Optional custom commit message
    
    Returns:
        True if successful, False otherwise
    """
    if commit_message is None:
        commit_message = f"Add results of Game {game_id}"
    
    try:
        # Add files
        subprocess.run(['git', 'add', str(DATA_DIR)], check=True)
        
        # Commit
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        print(f"Changes committed: {commit_message}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error committing changes: {e}")
        return False

def load_all_games():
    """
    Load all game files from the games directory
    
    Returns:
        List of game data dictionaries, sorted by date (oldest first)
    """
    games = []
    
    # Create games directory if it doesn't exist
    if not GAMES_DIR.exists():
        GAMES_DIR.mkdir(parents=True, exist_ok=True)
        return games
    
    # Read all game files
    for game_file in GAMES_DIR.glob('*.json'):
        try:
            with open(game_file, 'r') as f:
                game_data = json.load(f)
                games.append(game_data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load game file {game_file}: {e}")
    
    # Sort games by date (oldest first)
    games.sort(key=lambda x: x.get('date', ''))
    
    return games

def recalculate_leaderboard():
    """
    Recalculate the entire leaderboard from all game files
    
    Returns:
        Updated leaderboard data or None if an error occurred
    """
    # Load all games
    games = load_all_games()
    
    if not games:
        print("No game files found. Nothing to recalculate.")
        return None
    
    print(f"Recalculating leaderboard from {len(games)} game files...")
    
    # Delete existing leaderboard file if it exists
    if LEADERBOARD_FILE.exists():
        LEADERBOARD_FILE.unlink()
    
    # Process each game in chronological order
    leaderboard = None
    for i, game_data in enumerate(games):
        try:
            if not validate_game_data(game_data):
                print(f"Skipping invalid game: {game_data.get('game_id', 'unknown')}")
                continue
                
            leaderboard = update_leaderboard_from_game(game_data)
            print(f"Processed game {i+1}/{len(games)}: {game_data.get('game_id', 'unknown')}")
        except Exception as e:
            print(f"Error processing game {game_data.get('game_id', 'unknown')}: {e}")
    
    if leaderboard:
        print(f"Leaderboard recalculation complete. {len(leaderboard['models'])} models updated.")
    
    return leaderboard

def main():
    parser = argparse.ArgumentParser(description='Update leaderboard with new game results')
    parser.add_argument('--game-file', dest='game_file', help='Path to JSON file containing game results')
    parser.add_argument('--recalculate', action='store_true', help='Recalculate entire leaderboard from all game files')
    parser.add_argument('--commit', action='store_true', help='Commit changes to Git repository')
    parser.add_argument('--message', help='Custom commit message (only used with --commit)')
    
    args = parser.parse_args()
    
    # Ensure data directories exist
    ensure_data_dirs()
    
    # Check if we need to recalculate the entire leaderboard
    if args.recalculate:
        updated_leaderboard = recalculate_leaderboard()
        if not updated_leaderboard:
            return 1
            
        # Commit changes if requested
        if args.commit:
            commit_message = args.message or "Recalculate leaderboard from all game files"
            if not commit_changes("recalculate", commit_message):
                return 1
                
        return 0
    
    # Otherwise, process a single game file
    if not args.game_file:
        print("Error: Either --game-file or --recalculate must be specified")
        parser.print_help()
        return 1
    
    # Load game data
    try:
        with open(args.game_file, 'r') as f:
            game_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading game file: {e}")
        return 1
    
    # Validate game data
    if not validate_game_data(game_data):
        return 1
    
    # Save game result
    game_file = save_game_result(game_data)
    print(f"Game result saved to {game_file}")
    
    # Update leaderboard
    try:
        updated_leaderboard = update_leaderboard_from_game(game_data)
        print(f"Leaderboard updated successfully")
    except Exception as e:
        print(f"Error updating leaderboard: {e}")
        return 1
    
    # Commit changes if requested
    if args.commit:
        commit_message = args.message or f"Add results of Game {game_data['game_id']}"
        if not commit_changes(game_data['game_id'], commit_message):
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
