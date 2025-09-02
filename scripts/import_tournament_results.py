#!/usr/bin/env python3
"""
Import script to load Valyrian Games tournament results into the leaderboard system.

This script converts tournament result files from the Valyrian Games coding challenge
tournaments into the format expected by the leaderboard system, preserving all
performance metrics and tournament details in the additional_info section.
"""

import os
import sys
import json
import argparse
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict

# Add the parent directory to the path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def parse_arguments():
    """Parse command-line arguments for the import script."""
    parser = argparse.ArgumentParser(
        description='Import Valyrian Games tournament results into the leaderboard',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'tournament_files',
        nargs='*',
        help='Tournament result files to import (if none specified, imports all from tournaments directory)'
    )
    
    parser.add_argument(
        '--tournaments-dir',
        type=str,
        default='/volumes/Serendipity/ValyrianGames/Tournaments',
        help='Directory containing tournament result files'
    )
    
    parser.add_argument(
        '--leaderboard-dir',
        type=str,
        default='/home/wouter/Repos/ValyrianGamesLeaderboard',
        help='Directory of the leaderboard project'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without actually updating the leaderboard'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force import even if game already exists (will skip duplicates by default)'
    )
    
    parser.add_argument(
        '--commit',
        action='store_true',
        help='Commit changes to Git repository after successful import'
    )
    
    return parser.parse_args()


def load_tournament_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load and parse a tournament results file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        print(f"Error loading tournament file {filepath}: {e}")
        return None


def validate_tournament_data(tournament_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate that tournament data has required fields."""
    errors = []
    
    # Check required top-level fields
    required_fields = ['tournament_info', 'contenders', 'final_scores']
    for field in required_fields:
        if field not in tournament_data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Check tournament_info structure
    tournament_info = tournament_data.get('tournament_info', {})
    if 'timestamp' not in tournament_info:
        errors.append("Missing timestamp in tournament_info")
    
    # Check contenders and final_scores consistency
    contenders = tournament_data.get('contenders', [])
    final_scores = tournament_data.get('final_scores', {})
    
    if not contenders:
        errors.append("No contenders found")
    
    if not final_scores:
        errors.append("No final scores found")
    
    # Check that all contenders have scores
    missing_scores = [c for c in contenders if c not in final_scores]
    if missing_scores:
        errors.append(f"Missing scores for contenders: {missing_scores}")
    
    # Check that all scored participants are in contenders list
    extra_scores = [p for p in final_scores.keys() if p not in contenders]
    if extra_scores:
        errors.append(f"Scores found for non-contenders: {extra_scores}")
    
    return len(errors) == 0, errors


def calculate_ranks_from_scores(final_scores: Dict[str, int]) -> Dict[str, int]:
    """Convert final scores to ranks (0=best, 1=second, etc.), handling ties properly."""
    # Sort participants by score (descending)
    sorted_participants = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    
    ranks = {}
    current_rank = 0
    
    for i, (participant, score) in enumerate(sorted_participants):
        if i > 0 and score < sorted_participants[i-1][1]:
            # Score is different from previous, update rank
            current_rank = i
        
        ranks[participant] = current_rank
    
    return ranks


def aggregate_performance_metrics(detailed_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Aggregate performance metrics by participant."""
    participant_metrics = defaultdict(lambda: {
        'total_tokens': 0,
        'total_cost': 0.0,
        'total_time': 0.0,
        'total_attempts': 0,
        'successful_attempts': 0,
        'challenges_created': 0,
        'own_challenges_solved': 0,
        'others_challenges_solved': 0
    })
    
    for result in detailed_results:
        participant = result.get('solver', '')
        creator = result.get('challenge_creator', '')
        metrics = result.get('metrics', {})
        
        if not participant:
            continue
        
        # Aggregate basic metrics
        if not metrics.get('error'):
            participant_metrics[participant]['total_tokens'] += metrics.get('total_tokens', 0)
            participant_metrics[participant]['total_cost'] += metrics.get('total_cost', 0.0)
            participant_metrics[participant]['total_time'] += metrics.get('total_time', 0.0)
        
        participant_metrics[participant]['total_attempts'] += 1
        
        # Track success
        if result.get('result', {}).get('is_correct', False):
            participant_metrics[participant]['successful_attempts'] += 1
            
            if participant == creator:
                participant_metrics[participant]['own_challenges_solved'] += 1
            else:
                participant_metrics[participant]['others_challenges_solved'] += 1
    
    # Count challenges created
    creators = set()
    for result in detailed_results:
        creator = result.get('challenge_creator', '')
        if creator:
            creators.add(creator)
    
    for creator in creators:
        participant_metrics[creator]['challenges_created'] += 1
    
    # Calculate derived metrics
    for participant, metrics in participant_metrics.items():
        if metrics['total_time'] > 0:
            metrics['tokens_per_second'] = metrics['total_tokens'] / metrics['total_time']
        else:
            metrics['tokens_per_second'] = 0.0
        
        if metrics['total_cost'] > 0:
            metrics['tokens_per_dollar'] = metrics['total_tokens'] / metrics['total_cost']
        else:
            metrics['tokens_per_dollar'] = 0.0
        
        if metrics['total_attempts'] > 0:
            metrics['success_rate'] = metrics['successful_attempts'] / metrics['total_attempts']
        else:
            metrics['success_rate'] = 0.0
    
    return dict(participant_metrics)


def generate_game_id(tournament_timestamp: str, tournament_file: str) -> str:
    """Generate a unique game ID from tournament timestamp and file."""
    # Use tournament timestamp as base
    try:
        dt = datetime.fromisoformat(tournament_timestamp.replace('Z', '+00:00'))
        base_id = dt.strftime('valyrian_tournament_%Y%m%d_%H%M%S')
    except ValueError:
        # Fallback to filename if timestamp parsing fails
        filename = Path(tournament_file).stem
        base_id = f"valyrian_tournament_{filename}"
    
    # Add hash of filename for uniqueness
    file_hash = hashlib.md5(Path(tournament_file).name.encode()).hexdigest()[:8]
    return f"{base_id}_{file_hash}"


def extract_challenge_quality_info(tournament_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract challenge quality warnings and analysis from tournament data."""
    quality_info = {
        'warnings_detected': 0,
        'flagged_challenges': [],
        'total_challenges': 0,
        'success_rates': {}
    }
    
    # Count challenges
    challenges = tournament_data.get('challenges', [])
    quality_info['total_challenges'] = len(challenges)
    
    # Analyze detailed results for challenge quality
    detailed_results = tournament_data.get('detailed_results', [])
    
    # Group results by challenge
    challenge_results = defaultdict(list)
    for result in detailed_results:
        challenge_num = result.get('challenge_number', 0)
        challenge_results[challenge_num].append(result)
    
    # Analyze each challenge
    for challenge_num, results in challenge_results.items():
        if not results:
            continue
        
        # Calculate success rate for this challenge
        successful = sum(1 for r in results if r.get('result', {}).get('is_correct', False))
        total = len(results)
        success_rate = successful / total if total > 0 else 0.0
        
        challenge_creator = results[0].get('challenge_creator', 'Unknown')
        quality_info['success_rates'][f"challenge_{challenge_num}_{challenge_creator}"] = {
            'success_rate': success_rate,
            'successful_attempts': successful,
            'total_attempts': total,
            'creator': challenge_creator
        }
        
        # Flag challenges with very low success rates as potentially problematic
        if success_rate < 0.2 and total >= 3:  # Less than 20% success with at least 3 attempts
            quality_info['warnings_detected'] += 1
            quality_info['flagged_challenges'].append({
                'challenge_number': challenge_num,
                'creator': challenge_creator,
                'success_rate': success_rate,
                'reason': 'Very low success rate - possible quality issue'
            })
    
    return quality_info


def convert_tournament_to_game_format(tournament_data: Dict[str, Any], tournament_file: str) -> Dict[str, Any]:
    """Convert tournament data to the game format expected by the leaderboard."""
    tournament_info = tournament_data['tournament_info']
    contenders = tournament_data['contenders']
    final_scores = tournament_data['final_scores']
    detailed_results = tournament_data.get('detailed_results', [])
    
    # Generate game ID
    game_id = generate_game_id(tournament_info['timestamp'], tournament_file)
    
    # Convert timestamp to ISO format
    timestamp = tournament_info['timestamp']
    if not timestamp.endswith('Z') and '+' not in timestamp:
        timestamp += 'Z'
    
    # Calculate ranks from scores
    ranks_dict = calculate_ranks_from_scores(final_scores)
    
    # Create participants list and corresponding ranks/scores lists
    participants = contenders
    ranks = [ranks_dict[p] for p in participants]
    scores = [final_scores[p] for p in participants]
    
    # Aggregate performance metrics
    performance_metrics = aggregate_performance_metrics(detailed_results)
    
    # Extract challenge quality information
    challenge_quality = extract_challenge_quality_info(tournament_data)
    
    # Create description
    num_challenges = tournament_info.get('num_challenges', len(tournament_data.get('challenges', [])))
    temperature = tournament_info.get('temperature', 'unknown')
    description = f"Valyrian Games coding challenge tournament with {len(contenders)} contenders solving {num_challenges} peer-created challenges (temperature: {temperature})"
    
    # Build the game format
    game_data = {
        'game_id': game_id,
        'date': timestamp,
        'game_type': 'ValyrianGamesTournament',
        'participants': participants,
        'ranks': ranks,
        'scores': scores,
        'description': description,
        'additional_info': {
            'tournament_details': {
                'source_file': os.path.basename(tournament_file),
                'num_contenders': len(contenders),
                'num_challenges': num_challenges,
                'temperature': tournament_info.get('temperature'),
                'seed': tournament_info.get('seed'),
                'total_attempts': len(detailed_results),
                'overall_success_rate': sum(1 for r in detailed_results if r.get('result', {}).get('is_correct', False)) / len(detailed_results) if detailed_results else 0.0
            },
            'performance_metrics': performance_metrics,
            'challenge_quality': challenge_quality,
            'scoring_system': {
                'correct_solution': '+1 point',
                'incorrect_solution': '-1 point',
                'failed_own_challenge': '-2 points (additional penalty)',
                'solved_others_challenge': '+2 points (bonus)'
            },
            'challenges_summary': [
                {
                    'creator': challenge.get('creator', 'Unknown'),
                    'expected_answer': challenge.get('expected_answer'),
                    'prompt_preview': challenge.get('challenge_prompt', '')[:100] + '...' if len(challenge.get('challenge_prompt', '')) > 100 else challenge.get('challenge_prompt', '')
                }
                for challenge in tournament_data.get('challenges', [])
            ]
        }
    }
    
    return game_data


def check_game_exists(game_id: str, games_dir: Path) -> bool:
    """Check if a game with the given ID already exists."""
    game_file = games_dir / f"{game_id}.json"
    return game_file.exists()


def commit_changes_to_git(game_id: str, commit_message: str) -> bool:
    """Commit changes to the Git repository."""
    try:
        # Add all changes in data directory
        subprocess.run(['git', 'add', 'data/'], check=True, capture_output=True)
        
        # Commit with the provided message
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during Git commit: {e}")
        return False


def import_tournament_to_leaderboard(tournament_file: str, args) -> bool:
    """Import a single tournament file to the leaderboard."""
    if args.verbose:
        print(f"\nProcessing tournament file: {tournament_file}")
    
    # Load tournament data
    tournament_data = load_tournament_file(tournament_file)
    if not tournament_data:
        print(f"Failed to load tournament file: {tournament_file}")
        return False
    
    # Validate tournament data
    is_valid, errors = validate_tournament_data(tournament_data)
    if not is_valid:
        print(f"Invalid tournament data in {tournament_file}:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # Convert to game format
    try:
        game_data = convert_tournament_to_game_format(tournament_data, tournament_file)
    except Exception as e:
        print(f"Error converting tournament data: {e}")
        return False
    
    # Check if game already exists
    leaderboard_path = Path(args.leaderboard_dir)
    games_dir = leaderboard_path / 'data' / 'games'
    
    if check_game_exists(game_data['game_id'], games_dir) and not args.force:
        print(f"Game {game_data['game_id']} already exists, skipping (use --force to override)")
        return True
    
    if args.verbose:
        print(f"Game ID: {game_data['game_id']}")
        print(f"Participants: {len(game_data['participants'])}")
        print(f"Tournament date: {game_data['date']}")
        print(f"Final scores: {dict(zip(game_data['participants'], game_data['scores']))}")
    
    if args.dry_run:
        print(f"DRY RUN: Would import game {game_data['game_id']}")
        return True
    
    # Save game file
    games_dir.mkdir(parents=True, exist_ok=True)
    game_file = games_dir / f"{game_data['game_id']}.json"
    
    try:
        with open(game_file, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2, ensure_ascii=False)
        
        if args.verbose:
            print(f"Saved game file: {game_file}")
        
        # Update leaderboard using the TrueSkill calculator
        try:
            # Change to leaderboard directory for proper path resolution
            original_cwd = os.getcwd()
            os.chdir(args.leaderboard_dir)
            
            # Import the update function from the correct module
            sys.path.insert(0, str(leaderboard_path))
            from app.utils.trueskill_calculator import update_leaderboard_from_game
            
            # Update leaderboard with game data (not file path)
            updated_leaderboard = update_leaderboard_from_game(game_data)
            
            # Restore original directory
            os.chdir(original_cwd)
            
            if updated_leaderboard:
                print(f"✅ Successfully imported tournament: {game_data['game_id']}")
                
                # Handle Git commit if requested
                if args.commit:
                    try:
                        success = commit_changes_to_git(game_data['game_id'], 
                            f"Import Valyrian Games tournament: {game_data['game_id']}")
                        if success:
                            print(f"   Changes committed to Git repository")
                        else:
                            print(f"   Warning: Failed to commit changes to Git")
                    except Exception as commit_error:
                        print(f"   Warning: Git commit failed: {commit_error}")
                
                return True
            else:
                print(f"❌ Failed to update leaderboard for: {game_data['game_id']}")
                return False
                
        except Exception as e:
            os.chdir(original_cwd)  # Ensure we restore directory even on error
            print(f"Error updating leaderboard: {e}")
            return False
            
    except Exception as e:
        print(f"Error saving game file: {e}")
        return False


def find_tournament_files(tournaments_dir: str, specified_files: List[str]) -> List[str]:
    """Find tournament files to process."""
    if specified_files:
        # Use specified files
        tournament_files = []
        for file_path in specified_files:
            if os.path.exists(file_path):
                tournament_files.append(file_path)
            else:
                print(f"Warning: Tournament file not found: {file_path}")
        return tournament_files
    else:
        # Find all tournament result files in the directory
        tournaments_path = Path(tournaments_dir)
        if not tournaments_path.exists():
            print(f"Tournaments directory not found: {tournaments_dir}")
            return []
        
        pattern = "tournament_results_*.json"
        tournament_files = list(tournaments_path.glob(pattern))
        return [str(f) for f in sorted(tournament_files)]


def main():
    """Main entry point for the import script."""
    args = parse_arguments()
    
    print("Valyrian Games Tournament Results Importer")
    print("=" * 50)
    
    # Find tournament files to process
    tournament_files = find_tournament_files(args.tournaments_dir, args.tournament_files)
    
    if not tournament_files:
        print("No tournament files found to process.")
        return 1
    
    print(f"Found {len(tournament_files)} tournament file(s) to process:")
    for file_path in tournament_files:
        print(f"  - {os.path.basename(file_path)}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made")
    
    # Process each tournament file
    successful_imports = 0
    failed_imports = 0
    
    for tournament_file in tournament_files:
        try:
            success = import_tournament_to_leaderboard(tournament_file, args)
            if success:
                successful_imports += 1
            else:
                failed_imports += 1
        except Exception as e:
            print(f"Unexpected error processing {tournament_file}: {e}")
            failed_imports += 1
    
    # Summary
    print(f"\n" + "=" * 50)
    print(f"Import Summary:")
    print(f"  ✅ Successful imports: {successful_imports}")
    print(f"  ❌ Failed imports: {failed_imports}")
    print(f"  📁 Total files processed: {len(tournament_files)}")
    
    if args.dry_run:
        print(f"\n🔍 This was a dry run - no actual changes were made")
        print(f"   Run without --dry-run to perform the actual import")
    elif successful_imports > 0:
        print(f"\n🎉 Import completed successfully!")
        if args.commit:
            print(f"   Changes have been committed to the Git repository")
        else:
            print(f"   Run with --commit to automatically commit changes to Git")
    
    return 0 if failed_imports == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
