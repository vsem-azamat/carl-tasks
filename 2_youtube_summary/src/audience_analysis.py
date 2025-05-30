"""
Audience analysis module for YouTube comments.
Analyzes language distribution, sentiment patterns, and audience demographics.
"""

import json
from typing import Any
from collections import Counter, defaultdict
import pandas as pd
from langdetect import detect, DetectorFactory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Set seed for consistent language detection
DetectorFactory.seed = 0

# Language code to name mapping
LANGUAGE_NAMES = {
    'cs': 'Czech', 'sk': 'Slovak', 'en': 'English', 'de': 'German', 
    'pl': 'Polish', 'hu': 'Hungarian', 'ru': 'Russian', 'fr': 'French',
    'es': 'Spanish', 'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch',
    'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian', 'fi': 'Finnish',
    'ar': 'Arabic', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean',
    'hi': 'Hindi', 'tr': 'Turkish', 'unknown': 'Unknown'
}


def detect_language_safe(text: str) -> str:
    """Safely detect language of text, return 'unknown' if detection fails."""
    try:
        return detect(text)
    except:
        return 'unknown'


def analyze_language_distribution(comments: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze the language distribution of comments.
    """
    if not comments:
        return {"languages": {}, "total_comments": 0, "detected_languages": 0}
    
    # Extract text and detect languages
    comment_texts = [comment.get('text', '') for comment in comments if comment.get('text')]
    
    # Detect languages
    languages = []
    for text in comment_texts:
        if len(text.strip()) >= 10:  # Only detect for longer texts
            lang = detect_language_safe(text)
            languages.append(lang)
    
    # Count languages
    language_counts = Counter(languages)
    total_detected = len(languages)
    
    # Calculate percentages and create detailed stats
    language_stats = {}
    for lang_code, count in language_counts.most_common():
        lang_name = LANGUAGE_NAMES.get(lang_code, lang_code.upper())
        percentage = (count / total_detected * 100) if total_detected > 0 else 0
        
        language_stats[lang_code] = {
            'name': lang_name,
            'count': count,
            'percentage': round(percentage, 2)
        }
    
    return {
        'languages': language_stats,
        'total_comments': len(comment_texts),
        'detected_languages': total_detected,
        'primary_language': language_counts.most_common(1)[0] if language_counts else ('unknown', 0)
    }


def analyze_sentiment_by_language(analyzed_comments: list[dict[str, Any]], comments_raw: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze sentiment patterns by language.
    """
    if not analyzed_comments or not comments_raw:
        return {}
    
    # Map analyzed comments back to original texts for language detection
    sentiment_by_language = defaultdict(lambda: {'positive': 0, 'negative': 0, 'neutral': 0, 'total': 0})
    
    # Process comments that have both raw text and analysis
    min_length = min(len(analyzed_comments), len(comments_raw))
    
    for i in range(min_length):
        analysis = analyzed_comments[i]
        raw_comment = comments_raw[i]
        
        if analysis and not analysis.get('error') and raw_comment.get('text'):
            # Detect language
            lang = detect_language_safe(raw_comment['text'])
            sentiment = analysis.get('sentiment', 'neutral')
            
            # Count sentiment by language
            sentiment_by_language[lang][sentiment] += 1
            sentiment_by_language[lang]['total'] += 1
    
    # Calculate percentages
    result = {}
    for lang, sentiments in sentiment_by_language.items():
        total = sentiments['total']
        if total > 0:
            lang_name = LANGUAGE_NAMES.get(lang, lang.upper())
            result[lang] = {
                'name': lang_name,
                'total_comments': total,
                'positive': sentiments['positive'],
                'negative': sentiments['negative'],
                'neutral': sentiments['neutral'],
                'positive_percentage': round((sentiments['positive'] / total) * 100, 2),
                'negative_percentage': round((sentiments['negative'] / total) * 100, 2),
                'neutral_percentage': round((sentiments['neutral'] / total) * 100, 2)
            }
    
    return result


def analyze_engagement_patterns(analyzed_comments: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analyze engagement patterns from comments.
    """
    if not analyzed_comments:
        return {}
    
    valid_comments = [c for c in analyzed_comments if not c.get('error')]
    
    if not valid_comments:
        return {}
    
    # Analyze relevance and feedback quality
    relevant_count = sum(1 for c in valid_comments if c.get('is_relevant_feedback', False))
    total_count = len(valid_comments)
    
    # Analyze topics distribution
    all_topics = []
    for comment in valid_comments:
        topics = comment.get('topics', [])
        if topics:
            all_topics.extend([topic.lower().strip() for topic in topics if isinstance(topic, str)])
    
    topic_counts = Counter(all_topics)
    
    # Analyze feedback types
    has_pain_points = sum(1 for c in valid_comments if c.get('pain_points') and len(c['pain_points']) > 0)
    has_advantages = sum(1 for c in valid_comments if c.get('advantages') and len(c['advantages']) > 0)
    has_recommendations = sum(1 for c in valid_comments if c.get('recommendations_for_creator') and len(c['recommendations_for_creator']) > 0)
    
    return {
        'total_analyzed': total_count,
        'relevant_feedback_count': relevant_count,
        'relevant_feedback_percentage': round((relevant_count / total_count) * 100, 2) if total_count > 0 else 0,
        'feedback_patterns': {
            'constructive_criticism': has_pain_points,
            'positive_feedback': has_advantages,
            'suggestions_provided': has_recommendations,
            'criticism_percentage': round((has_pain_points / total_count) * 100, 2) if total_count > 0 else 0,
            'praise_percentage': round((has_advantages / total_count) * 100, 2) if total_count > 0 else 0,
            'suggestions_percentage': round((has_recommendations / total_count) * 100, 2) if total_count > 0 else 0
        },
        'top_discussion_topics': [{'topic': topic, 'count': count} for topic, count in topic_counts.most_common(10)]
    }


def generate_audience_profile(language_analysis: dict[str, Any], sentiment_by_language: dict[str, Any], 
                            engagement_patterns: dict[str, Any], model_name: str) -> str:
    """
    Generate an AI-powered audience profile analysis.
    """
    # Prepare data for LLM analysis
    analysis_data = {
        'language_distribution': language_analysis,
        'sentiment_by_language': sentiment_by_language,
        'engagement_patterns': engagement_patterns
    }
    
    # Initialize LLM
    llm = ChatOpenAI(
        model=model_name,
        temperature=0
    )
    
    # Create prompt
    prompt_template = """
    You are an expert audience analyst for YouTube channels. Based on the following comment analysis data, 
    provide insights about the channel's audience demographics, behavior patterns, and engagement characteristics.

    Analysis Data:
    {analysis_data}

    Please provide a comprehensive audience profile that includes:

    1. **Geographic/Cultural Audience**: Based on language distribution, what can we infer about the audience's geographic spread and cultural background?

    2. **Engagement Quality**: How engaged and constructive is this audience? What does their feedback behavior tell us?

    3. **Audience Characteristics**: What personality traits, interests, or demographics can we infer from comment patterns?

    4. **Content Preferences**: What topics or content types seem to resonate most with this audience?

    5. **Community Health**: How healthy and constructive is the comment community?

    6. **Growth Opportunities**: What insights for channel growth can be derived from this audience analysis?

    Provide specific, actionable insights based on the data. Be concrete rather than generic.
    Respond in English with clear headings and bullet points.
    """
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | llm | StrOutputParser()
    
    try:
        profile = chain.invoke({"analysis_data": json.dumps(analysis_data, indent=2, ensure_ascii=False)})
        return profile
    except Exception as e:
        return f"Error generating audience profile: {e}"


def analyze_video_audience(video_id: str, comments_raw: list[dict[str, Any]], 
                          analyzed_comments: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """
    Complete audience analysis for a single video.
    """
    print(f"  📊 Analyzing audience for video {video_id}...")
    
    # Language distribution analysis
    language_analysis = analyze_language_distribution(comments_raw)
    
    # Sentiment by language analysis
    sentiment_by_language = analyze_sentiment_by_language(analyzed_comments, comments_raw)
    
    # Engagement patterns analysis
    engagement_patterns = analyze_engagement_patterns(analyzed_comments)
    
    # Generate AI audience profile if enabled
    audience_profile = ""
    if config.get('analyze_audience', False):
        print(f"  🤖 Generating AI audience profile...")
        audience_profile = generate_audience_profile(
            language_analysis, sentiment_by_language, engagement_patterns, config['analysis_model']
        )
    
    return {
        'video_id': video_id,
        'language_analysis': language_analysis,
        'sentiment_by_language': sentiment_by_language,
        'engagement_patterns': engagement_patterns,
        'audience_profile': audience_profile,
        'analysis_timestamp': pd.Timestamp.now().isoformat()
    }


def aggregate_audience_analysis(video_analyses: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate audience analysis across multiple videos.
    """
    if not video_analyses:
        return {}
    
    # Aggregate language distribution
    total_languages = defaultdict(lambda: {'count': 0, 'percentage': 0})
    total_comments = 0
    
    for analysis in video_analyses:
        lang_analysis = analysis.get('language_analysis', {})
        languages = lang_analysis.get('languages', {})
        video_total = lang_analysis.get('total_comments', 0)
        
        total_comments += video_total
        
        for lang_code, lang_data in languages.items():
            total_languages[lang_code]['count'] += lang_data['count']
            total_languages[lang_code]['name'] = lang_data.get('name', lang_code.upper())
    
    # Recalculate percentages
    for lang_code, lang_data in total_languages.items():
        if total_comments > 0:
            lang_data['percentage'] = round((lang_data['count'] / total_comments) * 100, 2)
    
    # Aggregate engagement patterns
    total_engagement = {
        'total_analyzed': sum(a.get('engagement_patterns', {}).get('total_analyzed', 0) for a in video_analyses),
        'total_relevant': sum(a.get('engagement_patterns', {}).get('relevant_feedback_count', 0) for a in video_analyses),
        'videos_analyzed': len(video_analyses)
    }
    
    if total_engagement['total_analyzed'] > 0:
        total_engagement['overall_relevance_percentage'] = round(
            (total_engagement['total_relevant'] / total_engagement['total_analyzed']) * 100, 2
        )
    
    return {
        'channel_language_distribution': dict(total_languages),
        'channel_engagement_summary': total_engagement,
        'total_comments_analyzed': total_comments,
        'videos_analyzed': len(video_analyses),
        'analysis_timestamp': pd.Timestamp.now().isoformat()
    }
