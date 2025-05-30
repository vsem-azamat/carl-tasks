"""
Centralized configuration management for YouTube Comments Analysis Pipeline.
All configuration loading and constants are defined here.
"""

import yaml
import os
from pathlib import Path
from typing import Any

# Project structure constants
PROJECT_ROOT = Path(__file__).parent  # config.py is in project root
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
DATA_DIR = PROJECT_ROOT / "data"
COMMENTS_DIR = DATA_DIR / "comments"
ANALYSIS_DIR = DATA_DIR / "analysis"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# File naming patterns
COMMENT_FILE_PATTERN = "comments_{video_id}.json"  # Remove timestamp from pattern
ANALYSIS_FILE_PATTERN = "analysis_{video_id}.json"
AUDIENCE_FILE_PATTERN = "audience_{video_id}.json"
INDEX_FILE = "video_comments_index.json"

# Global config instance
_config = None

def get_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    global _config
    if _config is None:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                    _config = yaml.safe_load(file)
                    
                if not _config:
                    raise ValueError("Config file is empty or invalid")
                
                # Validate required fields
                if 'video_urls' not in _config or not _config['video_urls']:
                    raise ValueError("video_urls is required in config.yaml")
                
                print(f"✓ Configuration loaded from: {CONFIG_FILE}")
                
            else:
                raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")
                
        except Exception as e:
            print(f"✗ Error loading configuration: {e}")
            print(f"  Expected location: {CONFIG_FILE}")
            print(f"  Current working directory: {os.getcwd()}")
            raise
    
    return _config


# Ensure all required directories exist
directories = [COMMENTS_DIR, ANALYSIS_DIR, REPORTS_DIR, LOGS_DIR]
for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)

def validate_environment():
    """Validate required environment variables and configuration."""
    errors = []
    
    if not os.getenv('OPENAI_API_KEY'):
        errors.append("OPENAI_API_KEY environment variable not set")
    
    if not CONFIG_FILE.exists():
        errors.append(f"Configuration file not found: {CONFIG_FILE}")
    
    if errors:
        print("✗ Environment validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise EnvironmentError("Environment validation failed")
    print("✓ Environment validation passed")

def get_video_id_from_url(video_url: str) -> str:
    """Extract video ID from YouTube URL."""
    return video_url.split('v=')[-1].split('&')[0]

def get_comment_file_path(video_id: str) -> Path:
    """Get the full path for a comment file."""
    filename = COMMENT_FILE_PATTERN.format(video_id=video_id)  # Remove timestamp parameter
    return COMMENTS_DIR / filename

def get_analysis_file_path(video_id: str) -> Path:
    """Get the full path for an analysis file."""
    filename = ANALYSIS_FILE_PATTERN.format(video_id=video_id)
    return ANALYSIS_DIR / filename

def get_index_file_path() -> Path:
    """Get the full path for the video index file."""
    return DATA_DIR / INDEX_FILE
