#!/usr/bin/env python3
"""
Script to update the leaderboard with new game results.
This script:
1. Takes a game result file as input
2. Updates the leaderboard using TrueSkill
3. Saves the game result to the games directory
4. Optionally commits the changes to the Git repository
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

def main():
    parser = argparse.ArgumentParser(description='Update leaderboard with new game results')
    parser.add_argument('game_file', help='Path to JSON file containing game results')
    parser.add_argument('--commit', action='store_true', help='Commit changes to Git repository')
    parser.add_argument('--message', help='Custom commit message (only used with --commit)')
    
    args = parser.parse_args()
    
    # Ensure data directories exist
    ensure_data_dirs()
    
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
