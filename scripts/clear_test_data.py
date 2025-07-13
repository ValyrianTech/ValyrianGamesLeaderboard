#!/usr/bin/env python3
"""
Script to clear test data from the ValyrianGamesLeaderboard project.
This script removes all game files from the data/games directory,
resets the leaderboard.json file to an empty state, and rebuilds the static site.
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
import argparse
from datetime import datetime

# Add the parent directory to the path so we can import from app
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Path to data directory
DATA_DIR = Path(__file__).parent.parent / 'data'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'
GAMES_DIR = DATA_DIR / 'games'
FREEZE_SCRIPT = Path(__file__).parent / 'freeze.py'

def clear_game_files(backup=True):
    """
    Remove all game files from the games directory.
    
    Args:
        backup: If True, create a backup of the games directory before clearing
    """
    if not GAMES_DIR.exists():
        print(f"Games directory {GAMES_DIR} does not exist. Nothing to clear.")
        return
    
    # Create backup if requested
    if backup:
        backup_dir = DATA_DIR / f"games_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Creating backup of games directory at {backup_dir}")
        shutil.copytree(GAMES_DIR, backup_dir)
    
    # Remove all JSON files from games directory
    game_files = list(GAMES_DIR.glob('*.json'))
    if not game_files:
        print("No game files found to remove.")
        return
    
    print(f"Removing {len(game_files)} game files...")
    for game_file in game_files:
        os.remove(game_file)
        print(f"  Removed {game_file.name}")
    
    print("Game files cleared successfully.")

def reset_leaderboard(backup=True):
    """
    Reset the leaderboard.json file to an empty state.
    
    Args:
        backup: If True, create a backup of the leaderboard file before resetting
    """
    if not LEADERBOARD_FILE.exists():
        print(f"Leaderboard file {LEADERBOARD_FILE} does not exist. Creating new empty leaderboard.")
    else:
        # Create backup if requested
        if backup:
            backup_file = DATA_DIR / f"leaderboard_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            print(f"Creating backup of leaderboard at {backup_file}")
            shutil.copy2(LEADERBOARD_FILE, backup_file)
        
        print("Resetting leaderboard.json to empty state...")
    
    # Create empty leaderboard structure
    empty_leaderboard = {
        "last_updated": datetime.now().isoformat(),
        "models": []
    }
    
    # Write to file
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(empty_leaderboard, f, indent=2)
    
    print("Leaderboard reset successfully.")

def rebuild_static_site():
    """
    Rebuild the static site using the freeze.py script.
    """
    print("\nRebuilding static site...")
    try:
        result = subprocess.run(
            [sys.executable, str(FREEZE_SCRIPT)],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("Static site rebuilt successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error rebuilding static site: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Clear test data from the ValyrianGamesLeaderboard project.')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backups before clearing data')
    parser.add_argument('--keep-games', action='store_true', help='Do not clear game files')
    parser.add_argument('--keep-leaderboard', action='store_true', help='Do not reset leaderboard')
    parser.add_argument('--no-rebuild', action='store_true', help='Do not rebuild the static site')
    args = parser.parse_args()
    
    create_backup = not args.no_backup
    
    print("=== ValyrianGamesLeaderboard Test Data Cleanup ===")
    
    if not args.keep_games:
        clear_game_files(backup=create_backup)
    
    if not args.keep_leaderboard:
        reset_leaderboard(backup=create_backup)
    
    if not args.no_rebuild:
        rebuild_static_site()
    
    print("\nCleanup complete! The system is now ready for real game data.")
    print("To add real games, place game JSON files in the data/games directory")
    print("and run update_leaderboard.py to update the ratings.")

if __name__ == '__main__':
    main()
