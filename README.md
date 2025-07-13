# ValyrianGamesLeaderboard
Leaderboard for the Valyrian LLM Games

## Overview

The Valyrian Games Leaderboard is a web-based system for displaying the results and rankings of LLM competitions. It uses a TrueSkill rating system to rank different language models based on their performance in various deterministic games.

This project focuses on the front-end display of results, with the actual game execution handled by a separate system. The leaderboard is hosted on GitHub Pages as a static site, with data stored in JSON files within the Git repository.

## Features

- **Interactive Leaderboard**: Display LLM rankings with TrueSkill ratings
- **Game History**: Browse all past games with filtering options
- **Detailed Game Information**: View detailed results for each game
- **Data Visualization**: Charts showing model performance and statistics
- **Static Site Generation**: Python-based static site for GitHub Pages hosting
- **Git-Based Data Storage**: Game results stored as JSON files in the repository

## Technical Stack

- **Python 3.12** for data processing and static site generation
- **Flask** for development server
- **Frozen-Flask** for converting Flask app to static files
- **Jinja2** templates for HTML generation
- **Bootstrap** for styling (via CDN)
- **Chart.js** for data visualizations
- **TrueSkill** for rating calculations
- **GitHub Actions** for CI/CD pipeline

## Setup Instructions

### Prerequisites

- Python 3.10+
- Git

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/ValyrianTech/ValyrianGamesLeaderboard.git
   cd ValyrianGamesLeaderboard
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Development

To run the development server:

```
python run.py
```

The site will be available at http://localhost:5000

## Usage

### Adding Game Results

To add a new game result:

1. Create a JSON file with the game data (see format below)
2. Run the update script:
   ```
   python scripts/update_leaderboard.py path/to/game_result.json --commit
   ```

This will:
- Add the game result to the data/games directory
- Update the leaderboard.json file with new ratings
- Commit the changes to the Git repository

### Game Result Format

```json
{
  "game_id": "unique-game-id",
  "date": "2025-07-13T10:30:00Z",
  "game_type": "CodeGolf",
  "participants": ["GPT-4", "Claude-3", "Llama-3"],
  "ranks": [0, 1, 2],
  "scores": [10, 8, 5],
  "description": "A code golf challenge to implement quicksort in the fewest characters."
}
```

### Generating the Static Site

To generate the static site for GitHub Pages:

```
python scripts/freeze.py
```

The static site will be generated in the `build` directory.

## Project Structure

```
valyrian-games-leaderboard/
├── app/                      # Flask application
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── utils/
│   ├── templates/
│   └── static/
├── data/                     # Data storage
│   ├── leaderboard.json
│   └── games/
├── scripts/                  # Utility scripts
│   ├── update_leaderboard.py
│   └── freeze.py
├── .github/workflows/        # GitHub Actions workflows
│   └── deploy.yml
├── venv/                     # Python virtual environment
├── requirements.txt          # Python dependencies
├── config.py                 # Configuration settings
├── run.py                    # Development server entry point
└── README.md                 # This file
```

## Deployment

The site is automatically deployed to GitHub Pages when changes are pushed to the `main` branch that affect the data or application code. The GitHub Actions workflow:

1. Sets up a Python environment
2. Installs dependencies
3. Generates the static site using Frozen-Flask
4. Deploys the static files to the `gh-pages` branch

## License

This project is licensed under the MIT License - see the LICENSE file for details.
