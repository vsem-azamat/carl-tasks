"""
Multi-threaded video analysis coordinator.
Processes multiple videos in parallel and manages the overall analysis workflow.
"""

import os
import time
import json
from json import JSONDecodeError
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from src import utils
from src.analyze_video import analyze_single_video

def load_video_index(index_path: str = None) -> dict:
    """Load the video comments index file."""
    if index_path is None:
        index_path = config.get_index_file_path()
    
    with open(index_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def process_single_video_wrapper(video_info: dict[str, Any], config_dict: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Wrapper function for processing a single video in a thread."""
    video_id = video_info['video_id']
    video_url = video_info['video_url']
    comment_file = video_info['comment_file']
    
    try:
        return analyze_single_video(video_id, video_url, comment_file, config_dict)
    except Exception as e:
        utils.print_error(f"Error processing video {video_id}: {e}")
        return None


def analyze_all_videos_parallel(cfg) -> list[dict[str, Any]]:
    """Analyze all videos in parallel using ThreadPoolExecutor."""
    utils.print_progress("Starting parallel video analysis...")
    
    # Load video index
    try:
        video_index = load_video_index()
        videos_to_process = video_index['videos']
        utils.print_success(f"Found {len(videos_to_process)} videos to analyze")
    except (JSONDecodeError, FileNotFoundError) as e:
        utils.print_error(f"Error loading video index: {e}")
        utils.print_progress("Please run download_comments.py first to download the comments.")
        return []
    except Exception as e:
        utils.print_error(f"Unexpected error loading video index: {e}")
        return []
    
    if not videos_to_process:
        utils.print_error("No videos found to process")
        return []
    
    # Configure parallel processing
    max_workers = cfg.get('max_video_workers')
    max_workers = min(max_workers, len(videos_to_process))

    utils.print_progress(f"Using {max_workers} parallel workers for video analysis")

    successful_analyses = []
    start_time = time.time()
    
    # Process videos in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_video = {
            executor.submit(process_single_video_wrapper, video_info, cfg): video_info
            for video_info in videos_to_process
        }
        
        completed_count = 0
        for future in as_completed(future_to_video):
            video_info = future_to_video[future]
            video_id = video_info['video_id']
            completed_count += 1
            
            try:
                result = future.result()
                if result:
                    successful_analyses.append(result)
                    utils.print_success(f"[{completed_count}/{len(videos_to_process)}] Completed: {video_id}")
                else:
                    utils.print_error(f"[{completed_count}/{len(videos_to_process)}] Failed: {video_id}")

            except Exception as e:
                utils.print_error(f"[{completed_count}/{len(videos_to_process)}] Error processing {video_id}: {e}")

    elapsed_time = time.time() - start_time
    utils.print_section("Analysis Summary")
    utils.print_success(f"Successfully analyzed: {len(successful_analyses)}/{len(videos_to_process)} videos")
    utils.print_progress(f"Total time: {elapsed_time:.2f} seconds")
    utils.print_progress(f"Average time per video: {elapsed_time/len(videos_to_process):.2f} seconds")

    return successful_analyses


def save_aggregated_results(analyses: list[dict[str, Any]], output_path: str = None) -> None:
    """Save all analysis results to a single aggregated file."""
    if output_path is None:
        output_path = config.DATA_DIR / "aggregated_analysis.json"
    
    if not analyses:
        utils.print_warning("No analyses to save")
        return
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare aggregated data
    aggregated_data = {
        'analysis_metadata': {
            'total_videos': len(analyses),
            'analysis_timestamp': analyses[0].get('analysis_timestamp') if analyses else None,
            'config_used': analyses[0].get('config_used') if analyses else None
        },
        'video_analyses': []
    }
    
    # Extract summaries
    for analysis in analyses:
        video_summary = {
            'video_id': analysis.get('video_id'),
            'video_url': analysis.get('video_url'),
            'analysis_summary': analysis.get('analysis_summary'),
            'audience_analysis': analysis.get('audience_analysis'),
            'analysis_timestamp': analysis.get('analysis_timestamp')
        }
        aggregated_data['video_analyses'].append(video_summary)
    
    # Save aggregated results
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated_data, f, indent=2, ensure_ascii=False)
        utils.print_success(f"Saved aggregated analysis to: {output_path}")
    except Exception as e:
        utils.print_error(f"Error saving aggregated analysis: {e}")


def main():
    """Main function to coordinate parallel analysis of all videos."""
    utils.print_section("YouTube Comments Analysis Pipeline - Parallel Processing")

    # Load configuration
    try:
        utils.print_step(1, 4, "Setup and Configuration")
        config.validate_environment()
        cfg = config.get_config()

        utils.print_success("Configuration loaded:")
        utils.print_progress(f"Analysis model: {cfg.get('analysis_model')}")
        utils.print_progress(f"Filter language: {cfg.get('filter_language', 'all languages')}")
        utils.print_progress(f"Output language: {cfg.get('output_language')}")
        utils.print_progress(f"Minimum comment length: {cfg.get('min_length')}")
        utils.print_progress(f"Batch size: {cfg.get('batch_size')}")
        utils.print_progress(f"Max comments per video: {cfg.get('max_comments')}")
        utils.print_progress(f"Max video workers: {cfg.get('max_video_workers')}")
        utils.print_progress(f"Max batch workers: {cfg.get('max_batch_workers')}")
        utils.print_progress(f"Use cache: {cfg.get('use_cache')}")
        utils.print_progress(f"Analyze audience: {cfg.get('analyze_audience')}")
    except Exception as e:
        utils.print_error(f"Error loading configuration: {e}")
        return
    
    # Clean old cache files
    utils.print_step(2, 4, "Maintenance")
    cleaned_count = utils.clean_temp_files(config.ANALYSIS_DIR)
    if cleaned_count > 0:
        utils.print_success(f"Cleaned {cleaned_count} old cache files")

    # Analyze all videos
    utils.print_step(3, 4, "Parallel Video Analysis")
    analyses = analyze_all_videos_parallel(cfg)
    
    if not analyses:
        utils.print_error("No successful analyses completed")
        return
    
    # Save results (only aggregated, individual files are already cached)
    utils.print_step(4, 4, "Save Results")
    save_aggregated_results(analyses)

    utils.print_section("Parallel Analysis Completed")
    utils.print_success("Parallel analysis completed successfully!")
    utils.print_progress("Individual analysis files are cached in data/analysis/ with cache keys")
    utils.print_progress("Next step: Run 'python src/summarize_results.py' to generate the final report")


if __name__ == "__main__":
    main()
