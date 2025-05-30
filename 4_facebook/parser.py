"""
Facebook Posts Data Processing Script
Processes scraped Facebook posts data and creates structured dataset.
"""

import json
import pandas as pd
import csv
from typing import List, Dict, Any
import argparse

from models import FacebookPost

def determine_content_type(post: FacebookPost) -> str:
    """Determine the content type of a Facebook post."""
    if post.isVideo:
        return 'video'
    elif post.media and len(post.media) > 0:
        media_item = post.media[0]
        if media_item.type_name == 'Video':
            return 'video'
        elif media_item.thumbnail:
            return 'image'
        else:
            return 'media'
    else:
        return 'text'

def extract_post_data(posts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract structured data from Facebook posts."""
    structured_posts = []
    for post_data in posts_data:
        try:
            post = FacebookPost(**post_data)
            content_type = determine_content_type(post)
            text = post.text.strip().replace('\r\n', ' ').replace('\n', ' ')
            
            post_info = {
                'post_id': post.postId,
                'text': text,
                'url': post.url,
                'content_type': content_type,
                'shares_count': post.shares,
                'comments_count': post.comments,
                'likes_count': post.likes,
                'timestamp': post.timestamp,
                'post_date': post.time
            }
            
            # Add video-specific information
            if content_type == 'video':
                post_info['views_count'] = post.viewsCount or 0
                if post.media and len(post.media) > 0:
                    duration_ms = post.media[0].playable_duration_in_ms
                    post_info['video_duration_seconds'] = round(duration_ms / 1000, 1) if duration_ms else 0
                else:
                    post_info['video_duration_seconds'] = 0
            else:
                post_info['views_count'] = 0
                post_info['video_duration_seconds'] = 0
                
            structured_posts.append(post_info)
            
        except Exception:
            # Skip invalid posts
            continue
    
    return structured_posts


def save_to_csv(data: List[Dict[str, Any]], filename: str) -> None:
    """Save structured data to CSV file."""
    df = pd.DataFrame(data)
    df = df[df['text'] != '']
    column_order = [
        'post_id', 'text', 'url', 'content_type', 
        'shares_count', 'comments_count', 'likes_count',
        'views_count', 'video_duration_seconds',
        'timestamp', 'post_date'
    ]
    df = df[column_order]
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        df.to_csv(f, index=False, quoting=csv.QUOTE_ALL)


def display_summary(data: List[Dict[str, Any]]) -> None:
    """Display summary statistics."""
    df = pd.DataFrame(data)
    df = df[df['text'] != '']  # Filter empty text
    
    print(f"Total posts: {len(df)}")
    print(f"Content types: {df['content_type'].value_counts().to_dict()}")
    print(f"Total engagement: {df['likes_count'].sum() + df['comments_count'].sum() + df['shares_count'].sum():,}")
    
    video_posts = df[df['content_type'] == 'video']
    if not video_posts.empty:
        print(f"Video views: {video_posts['views_count'].sum():,}")


def main():
    """Main processing function."""
    parser = argparse.ArgumentParser(description="Process Facebook posts data.")
    parser.add_argument(
        "--input", "-i",
        default="apify.json",
        help="Path to input JSON file (default: %(default)s)"
    )
    parser.add_argument(
        "--output", "-o",
        default="facebook_posts_dataset.csv",
        help="Path to output CSV file (default: %(default)s)"
    )
    args = parser.parse_args()

    try:
        with open(args.input, 'r', encoding='utf-8') as file:
            posts_data = json.load(file)
        
        structured_data = extract_post_data(posts_data)
        save_to_csv(structured_data, args.output)
        display_summary(structured_data)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
