import json
from datetime import datetime
from youtube_comment_downloader import YoutubeCommentDownloader
import os

import config
from src import utils

def _atomic_write_json(path, data):
    """Atomically write JSON: dump → flush+fsync → rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)

def download_comments(video_url: str, force_download: bool = False) -> list:
    """Download comments from a YouTube video."""
    video_id = config.get_video_id_from_url(video_url)
    filepath = config.get_comment_file_path(video_id)
    
    # Check if file already exists
    if os.path.exists(filepath) and not force_download:
        utils.print_info(f"Comments file already exists for video {video_id}: {filepath}")
        utils.print_info("Use force_download=True to re-download")
        return []
    
    ycd = YoutubeCommentDownloader()
    comments = []
    
    try:
        utils.print_progress(f"Downloading comments from: {video_url}")
        for comment in ycd.get_comments_from_url(video_url):
            comments.append(comment)
        utils.print_success(f"Downloaded {len(comments)} comments")
    except Exception as e:
        utils.print_error(f"Error downloading comments: {e}")

    return comments

def save_comments_to_file(comments: list, video_url: str) -> str:
    """Save comments to a JSON file."""
    video_id = config.get_video_id_from_url(video_url)
    filepath = config.get_comment_file_path(video_id)  # Remove timestamp parameter
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            for comment in comments:
                f.write(json.dumps(comment, ensure_ascii=False) + '\n')

        utils.print_success(f"Saved {len(comments)} comments to: {filepath}")
        return str(filepath)
    except Exception as e:
        utils.print_error(f"Error saving comments to file: {e}")
        raise

def create_video_index(video_urls: list, comment_files: list) -> str:
    """Create an index file mapping video URLs to comment files."""
    index_data = {
        "created_at": datetime.now().isoformat(),
        "videos": [
            {
                "video_url": url,
                "comment_file": file_path,
                "video_id": config.get_video_id_from_url(url)
            }
            for url, file_path in zip(video_urls, comment_files)
        ]
    }
    index_filepath = config.get_index_file_path()
    _atomic_write_json(index_filepath, index_data)

    utils.print_success(f"Created index file: {index_filepath}")
    return str(index_filepath)

def main():
    """Main function to download comments from all configured videos."""
    utils.print_section("YouTube Comments Downloader")

    try:
        # Setup and validation
        utils.print_step(1, 3, "Setup and Configuration")
        config.validate_environment()
        cfg = config.get_config()

        utils.print_success("Configuration loaded")
        utils.print_progress(f"Videos to process: {len(cfg['video_urls'])}")
        utils.print_progress(f"Analysis model: {cfg.get('analysis_model', 'not specified')}")

        video_urls = cfg['video_urls']
        force_download = cfg.get('force_download', False)  # Add force download option
        
    except Exception as e:
        utils.print_error(f"Setup failed: {e}")
        return
    
    # Download comments for all videos
    utils.print_step(2, 3, "Download Comments")
    comment_files = []
    successful_downloads = 0
    
    for video_index, video_url in enumerate(video_urls):
        utils.print_info(f"\n--- Processing Video {video_index + 1}/{len(video_urls)} ---")

        try:
            comments = download_comments(video_url, force_download)
            
            if comments:
                comment_file = save_comments_to_file(comments, video_url)
                comment_files.append(comment_file)
                successful_downloads += 1
            else:
                # Check if file already exists (skipped download)
                video_id = config.get_video_id_from_url(video_url)
                existing_file = config.get_comment_file_path(video_id)
                if os.path.exists(existing_file):
                    comment_files.append(existing_file)
                    successful_downloads += 1
                    utils.print_success(f"Using existing comments file: {existing_file}")
                else:
                    utils.print_error(f"No comments downloaded for video {video_index + 1}")
                    comment_files.append(None)
                
        except Exception as e:
            utils.print_error(f"Error processing video {video_index + 1}: {e}")
            comment_files.append(None)
    
    # Create index file
    utils.print_step(3, 3, "Create Index")
    if successful_downloads > 0:
        valid_urls = [url for url, file in zip(video_urls, comment_files) if file is not None]
        valid_files = [file for file in comment_files if file is not None]
        
        create_video_index(valid_urls, valid_files)

        utils.print_section("Download Completed")
        utils.print_success(f"Successfully downloaded: {successful_downloads}/{len(video_urls)} videos")
        utils.print_progress(f"Comments saved to: {config.COMMENTS_DIR}")
        utils.print_progress(f"Index file: {config.get_index_file_path()}")
        utils.print_progress("Next step: Run the analysis script to process the downloaded comments.")
    else:
        utils.print_error("No comments were successfully downloaded!")


if __name__ == "__main__":
    main()
