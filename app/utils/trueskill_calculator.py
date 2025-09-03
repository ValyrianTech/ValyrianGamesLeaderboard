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
                    'conservative_rating': ratings[model_name].mu - 3 * ratings[model_name].sigma,
                    'avg_total_cost': 0.0,
                    'avg_tokens_per_second': 0.0
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
            
            # Update performance metrics if available
            self._update_performance_metrics(model_entry, model_name, game_data)
        
        # Sort leaderboard by actual rating (mu)
        leaderboard['models'].sort(key=lambda x: x.get('mu', 0), reverse=True)
        
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
    
    def _update_performance_metrics(self, model_entry, model_name, game_data):
        """
        Update the running average of performance metrics for a model.
        
        Args:
            model_entry: The model's entry in the leaderboard
            model_name: Name of the model
            game_data: The game data containing performance metrics
        """
        # Check if performance metrics exist in the game data
        performance_metrics = game_data.get('additional_info', {}).get('performance_metrics', {})
        model_metrics = performance_metrics.get(model_name, {})
        
        if not model_metrics:
            # No performance metrics available for this model in this game
            return
        
        # Get current averages (initialize if not present)
        current_avg_cost = model_entry.get('avg_total_cost', 0.0)
        current_avg_speed = model_entry.get('avg_tokens_per_second', 0.0)
        games_played = model_entry.get('games_played', 0)
        
        # Get new metrics from this game
        new_cost = model_metrics.get('total_cost', 0.0)
        new_speed = model_metrics.get('tokens_per_second', 0.0)
        
        # Calculate running averages
        # Note: games_played will be incremented after this method is called
        if games_played == 0:
            # First game for this model
            model_entry['avg_total_cost'] = new_cost
            model_entry['avg_tokens_per_second'] = new_speed
        else:
            # Update running average: new_avg = (old_avg * old_count + new_value) / new_count
            model_entry['avg_total_cost'] = (current_avg_cost * games_played + new_cost) / (games_played + 1)
            model_entry['avg_tokens_per_second'] = (current_avg_speed * games_played + new_speed) / (games_played + 1)


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
