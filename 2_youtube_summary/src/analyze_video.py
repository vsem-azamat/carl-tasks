"""
Single video analysis module with caching support.
Analyzes comments for one video and saves results to cache.
"""

import os
import json
import hashlib
import pandas as pd
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import config
from src import utils, prompts
from src.audience_analysis import analyze_video_audience

def load_comments_from_file(file_path: str) -> list[dict]:
    """Load comments from a JSON file (one JSON object per line)."""
    comments = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    comment = json.loads(line)
                    comments.append(comment)
    except Exception as e:
        utils.print_error(f"Error loading comments from {file_path}: {e}")
    return comments


def get_cache_key(video_id: str, config: dict[str, Any]) -> str:
    """Generate cache key based on video ID and relevant config parameters."""
    cache_params = {
        'video_id': video_id,
        'analysis_model': config.get('analysis_model'),
        'min_length': config.get('min_length'),
        'filter_language': config.get('filter_language'),
        'batch_size': config.get('batch_size'),
        'max_comments': config.get('max_comments'),
        'cache_version': config.get('cache_version', '1.0'),
        'analyze_audience': config.get('analyze_audience', False),
        'language_analysis': config.get('language_analysis', False)
    }
    
    cache_string = json.dumps(cache_params, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()[:16]


def get_cache_path(video_id: str, cache_key: str) -> str:
    """Get cache file path for video analysis."""
    return config.get_analysis_file_path(video_id).parent / f"{video_id}_{cache_key}.json"


def load_cached_analysis(video_id: str, config: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Load cached analysis if available and valid."""
    if not config.get('use_cache', True):
        return None
    
    cache_key = get_cache_key(video_id, config)
    cache_path = get_cache_path(video_id, cache_key)
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            utils.print_success(f"Loaded cached analysis for video {video_id}")
            return cached_data
        except Exception as e:
            utils.print_warning(f"Error loading cached analysis for {video_id}: {e}")
    
    return None


def save_analysis_to_cache(video_id: str, analysis_data: dict[str, Any], config_dict: dict[str, Any]) -> None:
    """Save analysis results to cache."""
    if not config_dict.get('use_cache', True):
        return
    
    cache_key = get_cache_key(video_id, config_dict)
    cache_path = get_cache_path(video_id, cache_key)
    
    config.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        utils.print_success(f"Saved analysis to cache: {os.path.basename(cache_path)}")
    except Exception as e:
        utils.print_warning(f"Error saving analysis to cache: {e}")


def preprocess_and_filter_comments(df_comments: pd.DataFrame, filter_language: Optional[str], min_length: int) -> pd.DataFrame:
    """Preprocess and filter comments based on language and length criteria."""
    if df_comments.empty or 'text' not in df_comments.columns:
        return pd.DataFrame()
    
    # Filter by length
    filtered_df = df_comments.copy()
    filtered_df = filtered_df[filtered_df['text'].str.len() >= min_length]
    
    # Filter out URL-only comments
    filtered_df = filtered_df[~filtered_df['text'].apply(utils.is_url_only)]
    
    # Filter by language if specified
    if filter_language:
        filtered_df['detected_language'] = filtered_df['text'].apply(utils.detect_language_safe)
        filtered_df = filtered_df[filtered_df['detected_language'] == filter_language]
    
    return filtered_df


def analyze_comments_batch(comments_batch: list[str], model_name: str, min_length: int, 
                         enable_fallback: bool = True) -> list[Optional[dict[str, Any]]]:
    """Analyze multiple comments in a single LLM call for better performance."""
    from langchain_openai import ChatOpenAI
    from pydantic import BaseModel
    import re
    
    class CommentAnalysis(BaseModel):
        sentiment: str
        topics: list[str]
        pain_points: list[str]
        advantages: list[str]
        recommendations_for_creator: list[str]
        is_relevant_feedback: bool
    
    # Filter and prepare comments
    valid_comments = []
    results: list[Optional[dict[str, Any]]] = []
    
    for i, comment_text in enumerate(comments_batch):
        if not comment_text or not isinstance(comment_text, str) or len(comment_text.strip()) < min_length:
            results.append(CommentAnalysis(
                sentiment="neutral", topics=[], pain_points=[], 
                advantages=[], recommendations_for_creator=[], is_relevant_feedback=False
            ).model_dump())
        else:
            valid_comments.append((i, comment_text))
            results.append(None)
    
    if not valid_comments:
        return results
    
    # Prepare LLM analysis
    llm = ChatOpenAI(model=model_name, temperature=0)
    
    comments_for_analysis = "\n\n".join([
        f"COMMENT {i+1}:\n```\n{comment}\n```" 
        for i, (_, comment) in enumerate(valid_comments)
    ])
    
    # Use centralized prompt
    batch_prompt = prompts.BATCH_COMMENT_ANALYSIS_PROMPT.format(
        comment_count=len(valid_comments),
        comments_text=comments_for_analysis
    )
    
    try:
        response = llm.invoke([{"role": "user", "content": batch_prompt}])
        response_text = str(response.content if hasattr(response, 'content') else response)
        
        # Extract and parse JSON response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            batch_results = json.loads(json_match.group())
            
            # Map results back to original positions
            for (original_idx, _), analysis_data in zip(valid_comments, batch_results):
                try:
                    analysis = CommentAnalysis(**analysis_data)
                    results[original_idx] = analysis.model_dump()
                except Exception as e:
                    utils.print_warning(f"Error parsing analysis for comment {original_idx}: {e}")
                    results[original_idx] = None
        else:
            if enable_fallback:
                return analyze_comments_fallback(comments_batch, model_name, min_length)
            else:
                for original_idx, _ in valid_comments:
                    results[original_idx] = None
            
    except Exception as e:
        utils.print_warning(f"Error in batch analysis: {e}")
        if enable_fallback:
            return analyze_comments_fallback(comments_batch, model_name, min_length)
        else:
            for original_idx, _ in valid_comments:
                results[original_idx] = None
    
    return results


def analyze_comments_fallback(comments_batch: list[str], model_name: str, min_length: int) -> list[Optional[dict[str, Any]]]:
    """Fallback to single comment analysis if batch fails."""
    utils.print_progress(f"Using fallback single-comment analysis for {len(comments_batch)} comments...")
    
    from pydantic import BaseModel
    
    class CommentAnalysis(BaseModel):
        sentiment: str
        topics: list[str]
        pain_points: list[str]
        advantages: list[str]
        recommendations_for_creator: list[str]
        is_relevant_feedback: bool
    
    results = []
    for comment_text in comments_batch:
        if not comment_text or len(comment_text.strip()) < min_length:
            results.append(CommentAnalysis(
                sentiment="neutral", topics=[], pain_points=[], 
                advantages=[], recommendations_for_creator=[], is_relevant_feedback=False
            ).model_dump())
        else:
            # Simple fallback analysis
            results.append(CommentAnalysis(
                sentiment="neutral", topics=["general"], pain_points=[], 
                advantages=[], recommendations_for_creator=[], is_relevant_feedback=True
            ).model_dump())
    
    return results


def process_video_batches_parallel(comment_texts: list[str], config: dict[str, Any]) -> list[dict[str, Any]]:
    """Process comment batches in parallel for a single video."""
    batch_size = config.get('batch_size', 20)
    max_workers = config.get('max_batch_workers', 2)
    model_name = config['analysis_model']
    min_length = config.get('min_length', 10)
    enable_fallback = config.get('enable_fallback', True)
    
    # Create batches
    batches = []
    for i in range(0, len(comment_texts), batch_size):
        batch_end = min(i + batch_size, len(comment_texts))
        batch_comments = comment_texts[i:batch_end]
        batches.append((i, batch_comments))
    
    utils.print_progress(f"Processing {len(comment_texts)} comments in {len(batches)} batches using {max_workers} workers...")
    
    all_results: list[Optional[dict[str, Any]]] = [None] * len(comment_texts)
    
    # Process batches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {
            executor.submit(analyze_comments_batch, batch_comments, model_name, min_length, enable_fallback): (batch_start, batch_comments)
            for batch_start, batch_comments in batches
        }
        
        for future in as_completed(future_to_batch):
            batch_start, batch_comments = future_to_batch[future]
            try:
                batch_results = future.result()
                
                # Place results in correct positions
                for i, result in enumerate(batch_results):
                    all_results[batch_start + i] = result
                
                batch_num = next(i for i, (start, _) in enumerate(batches) if start == batch_start) + 1
                utils.print_progress(f"Completed batch {batch_num}/{len(batches)}")
                
            except Exception as e:
                utils.print_error(f"Error processing batch starting at {batch_start}: {e}")
                # Fill with error results
                for i in range(len(batch_comments)):
                    all_results[batch_start + i] = {"error": f"Batch processing failed: {e}"}
    
    return [result for result in all_results if result is not None]


def aggregate_video_analysis(video_id: str, analyzed_comments: list[dict[str, Any]], 
                           top_n_topics: int = 5, top_n_pain_points: int = 5, 
                           top_n_advantages: int = 5) -> dict[str, Any]:
    """
    Aggregates analysis results from individual comments for a single video.
    """
    from collections import Counter
    from typing import Union
    
    relevant_comments = [
        comment for comment in analyzed_comments 
        if comment.get('is_relevant_feedback', False) and not comment.get('error')
    ]
    
    all_valid_comments = [
        comment for comment in analyzed_comments if not comment.get('error')
    ]

    # 1. Sentiment Summary
    sentiments = [comment['sentiment'] for comment in all_valid_comments if 'sentiment' in comment]
    sentiment_counts = Counter(sentiments)
    total_sentiments = len(sentiments)
    
    sentiment_summary: dict[str, Union[int, float]] = {
        f"{s}_count": sentiment_counts.get(s, 0) for s in ['positive', 'neutral', 'negative']
    }
    if total_sentiments > 0:
        for s_type in ['positive', 'neutral', 'negative']:
            sentiment_summary[f"{s_type}_percentage"] = round(
                (sentiment_counts.get(s_type, 0) / total_sentiments) * 100, 2
            )
    else:
        for s_type in ['positive', 'neutral', 'negative']:
            sentiment_summary[f"{s_type}_percentage"] = 0.0

    # 2. Topics Aggregation
    all_topics = []
    for comment in relevant_comments:
        topics = comment.get('topics', [])
        if topics:
             all_topics.extend(topic.lower().strip() for topic in topics if topic and isinstance(topic, str))
    topic_counts = Counter(all_topics)
    top_topics = [{"topic": topic, "count": count} for topic, count in topic_counts.most_common(top_n_topics)]

    # 3. Pain Points Aggregation
    all_pain_points = []
    for comment in relevant_comments:
        points = comment.get('pain_points', [])
        if points:
            all_pain_points.extend(point.lower().strip() for point in points if point and isinstance(point, str))
    pain_point_counts = Counter(all_pain_points)
    common_pain_points = [{"point": point, "count": count} for point, count in pain_point_counts.most_common(top_n_pain_points)]

    # 4. Advantages Aggregation
    all_advantages = []
    for comment in relevant_comments:
        advantages = comment.get('advantages', [])
        if advantages:
            all_advantages.extend(adv.lower().strip() for adv in advantages if adv and isinstance(adv, str))
    advantage_counts = Counter(all_advantages)
    highlighted_advantages = [{"advantage": advantage, "count": count} for advantage, count in advantage_counts.most_common(top_n_advantages)]

    # 5. Creator Recommendations Aggregation
    all_recommendations = []
    for comment in relevant_comments:
        recommendations = comment.get('recommendations_for_creator', [])
        if recommendations:
            all_recommendations.extend(rec.strip() for rec in recommendations if rec and isinstance(rec, str))
    unique_recommendations = list(dict.fromkeys(all_recommendations))

    return {
        "video_url_or_id": video_id,
        "total_comments_processed": len(analyzed_comments),
        "relevant_comments_count": len(relevant_comments),
        "sentiment_summary": sentiment_summary,
        "top_topics": top_topics,
        "common_pain_points": common_pain_points,
        "highlighted_advantages": highlighted_advantages,
        "creator_recommendations": unique_recommendations,
    }


def analyze_single_video(video_id: str, video_url: str, comment_file: str, config: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Analyze comments for a single video with caching support."""
    print(f"\n--- Processing Video: {video_id} ---")
    utils.print_progress(f"URL: {video_url}")
    
    # Check cache first
    cached_analysis = load_cached_analysis(video_id, config)
    if cached_analysis:
        return cached_analysis
    
    # Load and process comments
    try:
        comments = load_comments_from_file(comment_file)
        if not comments:
            utils.print_error(f"No comments loaded for video {video_id}")
            return None
        
        df_comments = pd.DataFrame(comments)
        utils.print_success(f"Loaded {len(comments)} comments")
    except Exception as e:
        utils.print_error(f"Error loading comments: {e}")
        return None
    
    # Filter comments
    try:
        filtered_df = preprocess_and_filter_comments(
            df_comments, 
            config.get('filter_language'), 
            config.get('min_length', 10)
        )
        filter_desc = f"language: {config.get('filter_language', 'all')}, min_length: {config.get('min_length', 10)}"
        utils.print_success(f"Filtered to {len(filtered_df)} comments ({filter_desc})")
    except Exception as e:
        utils.print_error(f"Error filtering comments: {e}")
        return None
    
    if filtered_df.empty:
        utils.print_error(f"No comments remaining after filtering for video {video_id}")
        return None
    
    # Analyze comments
    max_comments = config.get('max_comments', 1000)
    comments_to_process = filtered_df.head(max_comments)
    comment_texts = comments_to_process['text'].tolist()
    
    try:
        analyzed_comments = process_video_batches_parallel(comment_texts, config)
        utils.print_success(f"Analyzed {len(analyzed_comments)} comments")
    except Exception as e:
        utils.print_error(f"Error analyzing comments: {e}")
        return None
    
    # Generate summary and audience analysis
    try:
        video_summary = aggregate_video_analysis(video_id, analyzed_comments)
        utils.print_success(f"Generated summary for video {video_id}")
    except Exception as e:
        utils.print_error(f"Error aggregating analysis: {e}")
        return None
    
    # Audience analysis
    audience_analysis = None
    if config.get('analyze_audience', False) or config.get('language_analysis', False):
        try:
            audience_analysis = analyze_video_audience(video_id, comments, analyzed_comments, config)
            utils.print_success("Completed audience analysis")
        except Exception as e:
            utils.print_error(f"Error in audience analysis: {e}")
    
    # Prepare final result
    result = {
        'video_id': video_id,
        'video_url': video_url,
        'analysis_summary': video_summary,
        'analyzed_comments': analyzed_comments,
        'audience_analysis': audience_analysis,
        'config_used': {
            'analysis_model': config.get('analysis_model'),
            'filter_language': config.get('filter_language'),
            'min_length': config.get('min_length'),
            'max_comments': config.get('max_comments'),
            'batch_size': config.get('batch_size')
        },
        'analysis_timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Save to cache
    save_analysis_to_cache(video_id, result, config)
    
    return result


if __name__ == "__main__":
    # Test single video analysis
    import sys
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        config_manager = config.get_config()
        
        # Convert config to dict
        config_dict = {
            'analysis_model': config_manager.get_model(),
            'filter_language': config_manager.get_filter_language(),
            'min_length': config_manager.get_min_length(),
            'batch_size': config_manager.get_batch_size(),
            'max_comments': config_manager.get_max_comments(),
            'enable_fallback': config_manager.get('enable_fallback'),
            'max_batch_workers': config_manager.get('max_batch_workers'),
            'use_cache': config_manager.should_use_cache(),
            'cache_version': config_manager.get_cache_version(),
            'analyze_audience': config_manager.should_analyze_audience(),
            'language_analysis': config_manager.get('language_analysis')
        }
        
        # Find video info (this would need to be adapted to your video index)
        # For now, use dummy data
        result = analyze_single_video(video_id, f"test_url_{video_id}", f"data/comments/comments_{video_id}.json", config_dict)
        
        if result:
            print(f"✓ Analysis completed for video {video_id}")
        else:
            print(f"✗ Analysis failed for video {video_id}")
    else:
        print("Usage: python analyze_video.py <video_id>")
