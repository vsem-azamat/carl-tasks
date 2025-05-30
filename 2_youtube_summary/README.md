# YouTube Comments Analysis Pipeline

A 3-step pipeline for extracting insights from YouTube comments using parallel processing and AI analysis.

## 🔄 Pipeline Overview

```
📥 STEP 1: Download Comments
   │
   ├── YouTube URLs → Raw Comments (JSON)
   │   (This step can be replaced with any comment data source)
   │
   └── Creates: data/comments/*.json + index file

         ↓

🔄 STEP 2: Parallel Analysis  
   │
   ├── Load Comments → Filter by Language/Length
   │
   ├── Batch Processing → LLM Analysis (GPT-4)
   │   ├── Sentiment (positive/negative/neutral)
   │   ├── Topics & Pain Points
   │   ├── Advantages & Recommendations
   │   └── Audience Demographics
   │
   └── Creates: data/analysis/*.json (cached results)

         ↓

📊 STEP 3: Generate Reports
   │
   ├── Aggregate All Results → AI Summarization
   │
   └── Creates: reports/*.md (comprehensive + key insights)
```

## ⚡ Quick Start

```bash
# Setup
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"

# Run complete pipeline
make run
# OR step by step:
python -m src.download_comments
python -m src.analyze_all  
python -m src.summarize_results
```

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
video_urls:
  - "https://www.youtube.com/watch?v=VIDEO_ID"

analysis_model: "gpt-4o-mini"
filter_language: null        # null=all, "en"=English only
min_length: 10              # Skip short comments
batch_size: 20              # Comments per LLM call
max_comments: 1000          # Limit per video
max_video_workers: 3        # Parallel videos
use_cache: true             # Skip re-analysis
```

## 📁 Output Structure

```
data/
├── comments/               # Raw downloaded comments
├── analysis/              # Cached analysis results (one per video+config)
│   └── videoId_cacheKey.json
└── aggregated_analysis.json  # Combined results from all videos

reports/
├── comprehensive_analysis_YYYY-MM-DD.md  # Full report
├── key_insights_YYYY-MM-DD.md           # Executive summary
├── latest_comprehensive_analysis.md      # Quick access
└── latest_key_insights.md               # Quick access
```

## 🚀 Key Features

- **Parallel Processing**: Multiple videos and comment batches processed simultaneously
- **Smart Caching**: Skip re-analysis when re-running with same settings  
- **Multi-language Support**: Analyze all languages or filter by specific language
- **Audience Intelligence**: Language distribution, demographics, engagement patterns
- **Batch Optimization**: Efficient LLM usage with configurable batch sizes
- **Flexible Data Source**: Download step can be replaced with any comment data

## 📊 What Gets Analyzed

For each video:
- **Sentiment Distribution**: % positive/negative/neutral
- **Top Topics**: Most discussed themes  
- **Pain Points**: Common criticisms and complaints
- **Advantages**: What viewers praise
- **Creator Recommendations**: Actionable suggestions from audience
- **Audience Profile**: Demographics, language distribution, engagement quality

## 🛠️ Technical Architecture

```python
# STEP 1: Download (replaceable)
src/download_comments.py    # YouTube API → JSON files

# STEP 2: Analysis (core logic)  
src/analyze_all.py         # Coordinator for parallel processing
src/analyze_video.py       # Single video analysis with caching
src/audience_analysis.py   # Language & demographic analysis

# STEP 3: Reporting
src/summarize_results.py   # AI-powered report generation
src/prompts.py            # LLM prompt templates
```

### Performance Features
- **Video-level parallelism**: Process multiple videos simultaneously
- **Batch-level parallelism**: Process comment batches in parallel per video
- **Configuration-aware caching**: Automatic cache invalidation when settings change
- **Fallback mechanisms**: Graceful handling of API failures

## 📈 Sample Output

**Key Insights Report Example:**
```
EXECUTIVE SUMMARY
• 73% positive sentiment across 1,247 comments
• Main topics: tutorial quality, explanation clarity
• Top request: more advanced examples

TOP 3 STRATEGIC RECOMMENDATIONS  
1. Create advanced tutorial series (requested by 23% of viewers)
2. Improve audio quality (mentioned in 15% of feedback)
3. Add timestamps for better navigation

AUDIENCE INSIGHTS
• Primary: English (68%), Czech (22%), German (10%)
• High engagement quality: 82% constructive feedback
• Demographics: Technical professionals, students, hobbyists
```

## 🔧 Advanced Usage

**Custom batch processing:**
```bash
# Larger batches for speed (more API cost)
batch_size: 40
max_video_workers: 5

# Smaller batches for precision  
batch_size: 10
max_video_workers: 2
```

**Language filtering:**
```yaml
filter_language: "cs"    # Czech only
filter_language: "en"    # English only  
filter_language: null    # All languages
```

**Cache management:**
```bash
# Force re-analysis
rm -rf data/analysis/*.json

# Or increment cache version
cache_version: "1.1"
```

## 💡 Project Notes

This is a **proof-of-concept** focused on **information extraction quality** rather than perfect code organization. The pipeline demonstrates:

- Effective parallel processing for large-scale comment analysis
- Smart caching to avoid redundant API calls
- Comprehensive audience intelligence extraction
- Production-ready error handling and logging

The **download step is replaceable** - you can substitute any comment data source as long as it produces the expected JSON format.

**Core Goal**: Extract maximum actionable insights from user feedback using AI analysis.

---

**Next Steps**: Run `make run` to see the pipeline in action, then check `reports/latest_key_insights.md` for your analysis results.
