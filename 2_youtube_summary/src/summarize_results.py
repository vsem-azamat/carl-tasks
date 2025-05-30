"""
Final summarization module.
Generates comprehensive reports from aggregated analysis results.
"""

import json
from typing import Any, Optional
from pathlib import Path
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import config
from config import get_config
from src import prompts
from src.audience_analysis import aggregate_audience_analysis

def load_aggregated_analysis(analysis_path: Optional[str] = None) -> dict:
    """Load aggregated analysis results."""
    if analysis_path is None:
        analysis_path = str(config.DATA_DIR / "aggregated_analysis.json")
    
    try:
        with open(analysis_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Aggregated analysis file not found: {analysis_path}")
        print("ℹ️ Please run analyze_all.py first to generate the analysis data.")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing aggregated analysis file: {e}")
        print("ℹ️ The analysis file may be corrupted. Please run analyze_all.py again.")
        raise

def generate_video_summaries_for_report(video_analyses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract and format video summaries for report generation."""
    summaries = []
    for analysis in video_analyses:
        if analysis.get('analysis_summary'):
            summary = analysis['analysis_summary'].copy()
            summary['video_id'] = analysis.get('video_id')
            summary['video_url'] = analysis.get('video_url')
            summaries.append(summary)
    
    return summaries

def get_config_with_fallback(analysis_config: dict[str, Any]) -> dict[str, Any]:
    """Get config with fallback to original YAML config for missing keys."""
    original_config = get_config()
    
    # Merge with fallbacks
    merged_config = {
        'analysis_model': analysis_config.get('analysis_model', original_config.get('analysis_model', 'gpt-3.5-turbo')),
        'output_language': analysis_config.get('output_language', original_config.get('output_language', 'English')),
        'analyze_audience': analysis_config.get('analyze_audience', original_config.get('analyze_audience', False)),
        'language_filter': analysis_config.get('language_filter', original_config.get('filter_language', 'all')),
        'min_comment_length': analysis_config.get('min_comment_length', original_config.get('min_length', 0))
    }
    
    return merged_config

def generate_audience_insights_report(video_analyses: list[dict[str, Any]], analysis_config: dict[str, Any]) -> str:
    """Generate audience insights report from video analyses."""
    if not any(analysis.get('audience_analysis') for analysis in video_analyses):
        return "Audience analysis was not enabled for this analysis."
    
    # Extract audience analyses
    audience_analyses = [
        analysis['audience_analysis'] 
        for analysis in video_analyses 
        if analysis.get('audience_analysis')
    ]
    
    if not audience_analyses:
        return "No audience analysis data available."
    
    # Aggregate audience data across all videos
    aggregated_data = aggregate_audience_analysis(audience_analyses)
    
    # Format audience data for the prompt
    audience_data = json.dumps(aggregated_data, indent=2, ensure_ascii=False)
    
    # Format individual video analyses
    video_analyses_text = ""
    for i, analysis in enumerate(audience_analyses, 1):
        video_analyses_text += f"\n=== Video {i} Audience Analysis ===\n"
        video_analyses_text += json.dumps(analysis, indent=2, ensure_ascii=False)
        video_analyses_text += "\n"
    
    # Generate the report using LLM
    config_with_fallback = get_config_with_fallback(analysis_config)
    model = ChatOpenAI(
        model=config_with_fallback['analysis_model'],
        temperature=0.1
    )
    
    prompt = ChatPromptTemplate.from_template(prompts.AUDIENCE_INSIGHTS_REPORT_PROMPT)
    
    chain = prompt | model | StrOutputParser()
    
    response = chain.invoke({
        "audience_data": audience_data,
        "video_analyses": video_analyses_text,
        "output_language": config_with_fallback['output_language']
    })
    
    return response

def generate_key_insights_report(video_analyses: list[dict[str, Any]], analysis_config: dict[str, Any]) -> str:
    """Generate focused key insights report using centralized prompt."""
    video_summaries = generate_video_summaries_for_report(video_analyses)
    
    # Convert to JSON string for the prompt
    video_summaries_text = json.dumps(video_summaries, indent=2, ensure_ascii=False)
    
    # Generate the report using LLM
    config_with_fallback = get_config_with_fallback(analysis_config)
    model = ChatOpenAI(
        model=config_with_fallback['analysis_model'],
        temperature=0.1
    )
    
    prompt = ChatPromptTemplate.from_template(prompts.KEY_INSIGHTS_REPORT_PROMPT)
    
    chain = prompt | model | StrOutputParser()
    
    response = chain.invoke({
        "video_summaries": video_summaries_text,
        "output_language": config_with_fallback['output_language']
    })
    
    return response

def generate_comprehensive_report(video_analyses: list[dict[str, Any]], analysis_config: dict[str, Any]) -> str:
    """Generate comprehensive analysis report."""
    video_summaries = generate_video_summaries_for_report(video_analyses)
    
    # Convert to JSON string for the prompt
    video_summaries_json = json.dumps(video_summaries, indent=2, ensure_ascii=False)
    
    # Get config with fallbacks
    config_with_fallback = get_config_with_fallback(analysis_config)
    
    # Generate audience insights if available
    audience_insights = ""
    if config_with_fallback['analyze_audience']:
        audience_insights = generate_audience_insights_report(video_analyses, analysis_config)
    else:
        audience_insights = "Audience analysis was not enabled for this analysis."
    
    # Generate the report using LLM
    model = ChatOpenAI(
        model=config_with_fallback['analysis_model'],
        temperature=0.1
    )
    
    prompt = ChatPromptTemplate.from_template(prompts.COMPREHENSIVE_REPORT_PROMPT)
    
    chain = prompt | model | StrOutputParser()
    
    response = chain.invoke({
        "video_summaries_json": video_summaries_json,
        "audience_insights": audience_insights,
        "analysis_model": config_with_fallback['analysis_model'],
        "videos_analyzed": len(video_analyses),
        "language_filter": config_with_fallback['language_filter'],
        "min_length": config_with_fallback['min_comment_length'],
        "output_language": config_with_fallback['output_language']
    })
    
    return response

def save_report(report_content: str, filename: str) -> None:
    """Save report to file."""
    # Convert Path objects to strings if needed
    if hasattr(filename, '__fspath__'):
        filename = str(filename)
    
    # Ensure directory exists
    reports_dir = Path(filename).parent
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(report_content)
    
    print(f"Report saved to {filename}")

def main():
    """Generate final summary reports from aggregated analysis."""
    print("Loading aggregated analysis...")
    
    # Load the aggregated analysis data
    try:
        aggregated_data = load_aggregated_analysis()
    except (FileNotFoundError, json.JSONDecodeError):
        return
    
    video_analyses = aggregated_data.get('video_analyses', [])
    analysis_config = aggregated_data.get('config', {})
    
    print(f"Generating reports for {len(video_analyses)} videos...")
    
    # Create timestamp for files
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    
    # Generate comprehensive report with audience insights
    print("Generating comprehensive analysis report...")
    comprehensive_report = generate_comprehensive_report(video_analyses, analysis_config)
    
    # Generate key insights report (focused version)
    print("Generating key insights report...")
    key_insights_report = generate_key_insights_report(video_analyses, analysis_config)
    
    # Save timestamped reports
    comprehensive_filename = str(config.REPORTS_DIR / f"comprehensive_analysis_{timestamp}.md")
    key_insights_filename = str(config.REPORTS_DIR / f"key_insights_{timestamp}.md")
    
    save_report(comprehensive_report, comprehensive_filename)
    save_report(key_insights_report, key_insights_filename)
    
    # Save latest reports (overwrite previous)
    latest_comprehensive_filename = str(config.REPORTS_DIR / "latest_comprehensive_analysis.md")
    latest_key_insights_filename = str(config.REPORTS_DIR / "latest_key_insights.md")
    
    save_report(comprehensive_report, latest_comprehensive_filename)
    save_report(key_insights_report, latest_key_insights_filename)
    
    print("\n" + "="*50)
    print("REPORT GENERATION COMPLETE")
    print("="*50)
    print(f"Comprehensive Analysis: {comprehensive_filename}")
    print(f"Key Insights Report: {key_insights_filename}")
    print(f"Latest Comprehensive: {latest_comprehensive_filename}")
    print(f"Latest Key Insights: {latest_key_insights_filename}")

if __name__ == "__main__":
    main()