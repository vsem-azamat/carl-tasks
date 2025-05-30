"""
Utility functions for YouTube Comments Analysis Pipeline.
Common helper functions to reduce code duplication.
"""

import json
import re
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup basic logging configuration."""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/pipeline.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def print_info(message: str):
    """Print formatted info message."""
    print(f"ℹ️ {message}")

def print_progress(message: str, emoji: str = "ℹ️"):
    """Print formatted progress message."""
    print(f"{emoji} {message}")


def print_success(message: str):
    """Print formatted success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print formatted error message."""
    print(f"❌ {message}")


def print_warning(message: str):
    """Print formatted warning message."""
    print(f"⚠️ {message}")


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")


def print_step(step_num: int, total_steps: int, description: str):
    """Print formatted step progress."""
    print(f"\n🔄 Step {step_num}/{total_steps}: {description}")
    print("-" * 50)


def is_url_only(text: str) -> bool:
    """Check if text contains only URLs."""
    url_pattern = r'https?://[^\s]+'
    text_without_urls = re.sub(url_pattern, '', text).strip()
    return len(text_without_urls) == 0 and len(re.findall(url_pattern, text)) > 0


def detect_language_safe(text: str) -> str:
    """Safely detect language of text, return 'unknown' if detection fails."""
    try:
        from langdetect import detect
        return detect(text)
    except:
        return 'unknown'


def create_timestamped_filename(base_name: str, extension: str = "md") -> str:
    """Create filename with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return f"{base_name}_{timestamp}.{extension}"


def save_json_safely(data: dict[str, Any], filepath: Path, encoding: str = 'utf-8'):
    """Safely save JSON data to file."""
    try:
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print_error(f"Error saving JSON to {filepath}: {e}")
        return False


def load_json_safely(filepath: Path, encoding: str = 'utf-8') -> Optional[dict[str, Any]]:
    """Safely load JSON data from file."""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Error loading JSON from {filepath}: {e}")
        return None


def format_file_size(filepath: Path) -> str:
    """Format file size in human readable format."""
    try:
        size = filepath.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except:
        return "Unknown"


def clean_temp_files(temp_dir: Path, max_age_hours: int = 24):
    """Clean temporary files older than specified hours."""
    if not temp_dir.exists():
        return 0
    
    import time
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned_count = 0
    for temp_file in temp_dir.glob("*"):
        if temp_file.is_file() and temp_file.stat().st_mtime < (current_time - max_age_seconds):
            try:
                temp_file.unlink()
                cleaned_count += 1
            except Exception as e:
                print_warning(f"Could not remove temp file {temp_file}: {e}")
    
    return cleaned_count
