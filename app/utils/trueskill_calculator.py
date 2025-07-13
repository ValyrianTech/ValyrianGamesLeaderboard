import trueskill
import json
from pathlib import Path
import datetime

# Path to data directory
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'

class TrueSkillCalculator:
    """
    Calculator for TrueSkill ratings based on game results.
    Uses the trueskill library to update ratings.
    """
    
    def __init__(self, draw_probability=0.0):
        """
        Initialize the TrueSkill environment.
        
        Args:
            draw_probability: Probability of a draw (default: 0.0)
        """
        self.env = trueskill.TrueSkill(draw_probability=draw_probability)
    
    def update_ratings_from_game(self, game_data):
        """
        Update ratings based on a single game result.
        
        Args:
            game_data: Dictionary containing game results
            
        Returns:
            Updated leaderboard data
        """
        # Load current leaderboard
        leaderboard = self._load_leaderboard()
        
        # Extract participants and their ranks from the game
        participants = game_data.get('participants', [])
        ranks = game_data.get('ranks', [])
        
        if not participants or not ranks or len(participants) != len(ranks):
            raise ValueError("Invalid game data: participants and ranks must be non-empty and of equal length")
        
        # Get current ratings for participants
        ratings = {}
        for model_name in participants:
            # Find the model in the leaderboard or create a new entry
            model_entry = next((m for m in leaderboard['models'] if m['name'] == model_name), None)
            
            if model_entry:
                # Use existing rating
                ratings[model_name] = self.env.create_rating(
                    mu=model_entry['mu'],
                    sigma=model_entry['sigma']
                )
            else:
                # Create new rating with default values
                ratings[model_name] = self.env.create_rating()
                # Add new model to leaderboard
                leaderboard['models'].append({
                    'name': model_name,
                    'mu': ratings[model_name].mu,
                    'sigma': ratings[model_name].sigma,
                    'games_played': 0,
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                    'conservative_rating': ratings[model_name].mu - 3 * ratings[model_name].sigma
                })
        
        # Prepare teams for TrueSkill update
        # Each model is its own "team" in this case
        teams = [[ratings[model_name]] for model_name in participants]
        
        # Update ratings
        updated_teams = self.env.rate(teams, ranks=ranks)
        
        # Update leaderboard with new ratings
        for i, model_name in enumerate(participants):
            new_rating = updated_teams[i][0]
            
            # Find the model in the leaderboard
            model_entry = next(m for m in leaderboard['models'] if m['name'] == model_name)
            
            # Update rating
            model_entry['mu'] = new_rating.mu
            model_entry['sigma'] = new_rating.sigma
            model_entry['games_played'] = model_entry.get('games_played', 0) + 1
            
            # Update win/loss/draw record
            rank = ranks[i]
            better_ranks = [r for r in ranks if r < rank]
            worse_ranks = [r for r in ranks if r > rank]
            equal_ranks = [r for r in ranks if r == rank and ranks.index(r) != i]
            
            model_entry['wins'] = model_entry.get('wins', 0) + len(worse_ranks)
            model_entry['losses'] = model_entry.get('losses', 0) + len(better_ranks)
            model_entry['draws'] = model_entry.get('draws', 0) + len(equal_ranks)
            
            # Calculate conservative rating (μ - 3σ)
            model_entry['conservative_rating'] = new_rating.mu - 3 * new_rating.sigma
        
        # Sort leaderboard by conservative rating
        leaderboard['models'].sort(key=lambda x: x.get('conservative_rating', 0), reverse=True)
        
        # Update last_updated timestamp
        leaderboard['last_updated'] = datetime.datetime.now().isoformat()
        
        # Save updated leaderboard
        self._save_leaderboard(leaderboard)
        
        return leaderboard
    
    def _load_leaderboard(self):
        """Load the leaderboard from file or create a new one if it doesn't exist"""
        if LEADERBOARD_FILE.exists():
            with open(LEADERBOARD_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create empty leaderboard
            return {
                'last_updated': datetime.datetime.now().isoformat(),
                'models': []
            }
    
    def _save_leaderboard(self, leaderboard):
        """Save the leaderboard to file"""
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f, indent=2)


def update_leaderboard_from_game(game_data):
    """
    Convenience function to update the leaderboard from a game result.
    
    Args:
        game_data: Dictionary containing game results
        
    Returns:
        Updated leaderboard data
    """
    calculator = TrueSkillCalculator()
    return calculator.update_ratings_from_game(game_data)
