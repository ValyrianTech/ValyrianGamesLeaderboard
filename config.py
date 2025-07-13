"""
Configuration settings for the Valyrian Games Leaderboard application.
"""

import os
from pathlib import Path

# Base directory of the application
BASE_DIR = Path(__file__).parent

# Data directory
DATA_DIR = BASE_DIR / 'data'
GAMES_DIR = DATA_DIR / 'games'
LEADERBOARD_FILE = DATA_DIR / 'leaderboard.json'

# Build directory for static site
BUILD_DIR = BASE_DIR / 'build'

# Flask configuration
class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-valyrian-games')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
# Default configuration
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# TrueSkill configuration
TRUESKILL_DRAW_PROBABILITY = 0.0
TRUESKILL_BETA = 4.166  # Default is 4.166
TRUESKILL_TAU = 0.083   # Default is 0.083
