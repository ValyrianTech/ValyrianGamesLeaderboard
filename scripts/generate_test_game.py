#!/usr/bin/env python3
"""
Script to generate random test games for the ValyrianGamesLeaderboard.
This script creates a random game result with existing or new models.
"""

import os
import sys
import json
import random
import uuid
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Path to data directory
DATA_DIR = Path(__file__).parent.parent / 'data'
GAMES_DIR = DATA_DIR / 'games'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'

# Game types
GAME_TYPES = [
    "CodeGolf",
    "LogicalReasoning",
    "MathematicalProblemSolving",
    "CreativeWriting",
    "CodeDebug",
    "TextSummarization",
    "QuestionAnswering",
    "FactChecking",
    "DataAnalysis",
    "ImageCaptioning"
]

# Test model name prefixes
TEST_MODEL_PREFIXES = ["TestModel-", "ExperimentalModel-", "Prototype-"]

# Greek letters for model naming
GREEK_LETTERS = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi",
    "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
]

def load_existing_models():
    """Load existing models from the leaderboard"""
    if not LEADERBOARD_FILE.exists():
        return []
    
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = json.load(f)
            return [model['name'] for model in leaderboard.get('models', [])]
    except (json.JSONDecodeError, KeyError):
        return []

def generate_model_name(existing_models):
    """Generate a new model name that doesn't exist yet"""
    prefix = random.choice(TEST_MODEL_PREFIXES)
    suffix = random.choice(GREEK_LETTERS)
    
    # If the model already exists, add a number to make it unique
    base_name = f"{prefix}{suffix}"
    if base_name in existing_models:
        i = 2
        while f"{base_name}-{i}" in existing_models:
            i += 1
        return f"{base_name}-{i}"
    
    return base_name

def generate_random_game(num_participants=None, use_existing_models=True, game_type=None):
    """
    Generate a random game result
    
    Args:
        num_participants: Number of participants (default: random between 2 and 6)
        use_existing_models: Whether to use existing models or generate new ones
        game_type: Type of game (default: random from GAME_TYPES)
        
    Returns:
        Dictionary with game data
    """
    # Load existing models
    existing_models = load_existing_models() if use_existing_models else []
    
    # Determine number of participants
    if num_participants is None:
        num_participants = random.randint(2, 6)
    
    # Select or generate participants
    participants = []
    for _ in range(num_participants):
        if existing_models and use_existing_models and random.random() < 0.7:
            # 70% chance to use an existing model if available
            participants.append(random.choice(existing_models))
        else:
            # Generate a new model name
            new_model = generate_model_name(existing_models + participants)
            participants.append(new_model)
    
    # Generate ranks (no ties for simplicity)
    ranks = list(range(num_participants))
    random.shuffle(ranks)
    
    # Generate scores (higher is better)
    base_score = random.randint(70, 95)
    scores = []
    for rank in ranks:
        # Higher ranks get lower scores
        score = max(0, base_score - (rank * random.randint(3, 8)))
        scores.append(score)
    
    # Select game type
    if game_type is None:
        game_type = random.choice(GAME_TYPES)
    
    # Generate game date (within the last 30 days)
    days_ago = random.randint(0, 30)
    game_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
    
    # Create game data
    game_id = f"game-{uuid.uuid4().hex[:8]}"
    game_data = {
        "game_id": game_id,
        "date": game_date,
        "game_type": game_type,
        "participants": participants,
        "ranks": ranks,
        "scores": scores,
        "description": f"A randomly generated {game_type} challenge for testing purposes."
    }
    
    # Add some game-specific details
    if game_type == "CodeGolf":
        game_data["details"] = {
            "challenge_prompt": "Implement a function to solve a coding problem with minimal characters.",
            "character_count": {p: random.randint(50, 500) for p in participants}
        }
    elif game_type == "MathematicalProblemSolving":
        game_data["details"] = {
            "challenge_prompt": "Solve a set of mathematical problems.",
            "accuracy": {p: round(random.uniform(0.6, 0.98), 2) for p in participants}
        }
    elif game_type == "CreativeWriting":
        game_data["details"] = {
            "challenge_prompt": "Write a creative story based on a given prompt.",
            "human_ratings": {
                p: {
                    "creativity": round(random.uniform(3.0, 5.0), 1),
                    "coherence": round(random.uniform(3.0, 5.0), 1),
                    "emotional_impact": round(random.uniform(3.0, 5.0), 1)
                } for p in participants
            }
        }
    
    return game_data

def save_game_result(game_data, output_file=None):
    """
    Save the game result to a file
    
    Args:
        game_data: Dictionary with game data
        output_file: Path to output file (default: print to stdout)
        
    Returns:
        Path to the saved file or None if printed to stdout
    """
    if output_file:
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save to file
        with open(output_file, 'w') as f:
            json.dump(game_data, f, indent=2)
        return output_file
    else:
        # Print to stdout
        print(json.dumps(game_data, indent=2))
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate random test games for the ValyrianGamesLeaderboard')
    parser.add_argument('--participants', type=int, help='Number of participants')
    parser.add_argument('--game-type', choices=GAME_TYPES, help='Type of game')
    parser.add_argument('--new-models-only', action='store_true', help='Only generate new models, don\'t use existing ones')
    parser.add_argument('--output', '-o', help='Output file (default: print to stdout)')
    parser.add_argument('--update', action='store_true', help='Update the leaderboard with the generated game')
    
    args = parser.parse_args()
    
    # Generate random game
    game_data = generate_random_game(
        num_participants=args.participants,
        use_existing_models=not args.new_models_only,
        game_type=args.game_type
    )
    
    # Save game result
    output_file = save_game_result(game_data, args.output)
    
    # Update leaderboard if requested
    if args.update:
        try:
            from app.utils.trueskill_calculator import update_leaderboard_from_game
            updated_leaderboard = update_leaderboard_from_game(game_data)
            print(f"Leaderboard updated successfully with game {game_data['game_id']}")
            
            # Save the game to the games directory
            game_file = GAMES_DIR / f"{game_data['game_id']}.json"
            GAMES_DIR.mkdir(parents=True, exist_ok=True)
            with open(game_file, 'w') as f:
                json.dump(game_data, f, indent=2)
            print(f"Game saved to {game_file}")
        except Exception as e:
            print(f"Error updating leaderboard: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
