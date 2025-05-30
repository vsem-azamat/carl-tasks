"""
Centralized prompt templates for YouTube Comments Analysis Pipeline.
All LLM prompts are defined here to keep the main code clean.
"""

# Batch comment analysis prompt
BATCH_COMMENT_ANALYSIS_PROMPT = """
You are an expert YouTube comment analyst. Analyze the following {comment_count} YouTube comments.
For each comment, provide a JSON analysis with these fields:
- sentiment: "positive", "negative", or "neutral"
- topics: list of 1-3 main topics (concise strings)
- pain_points: list of specific criticisms (empty list if none)
- advantages: list of specific praises (empty list if none)
- recommendations_for_creator: list of actionable suggestions (empty list if none)
- is_relevant_feedback: boolean (true if substantive feedback, false if simple greeting/spam)

Comments to analyze:
{comments_text}

Respond with a JSON array containing exactly {comment_count} objects, one for each comment in order.
Each object should have all the required fields. Example format:
[
    {{
        "sentiment": "positive",
        "topics": ["content quality"],
        "pain_points": [],
        "advantages": ["great explanation"],
        "recommendations_for_creator": [],
        "is_relevant_feedback": true
    }},
    ...
]
"""

# Audience profile analysis prompt
AUDIENCE_PROFILE_PROMPT = """
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

# Audience insights report prompt
AUDIENCE_INSIGHTS_REPORT_PROMPT = """
You are an expert audience analyst for YouTube channels. Based on the aggregated audience analysis data 
from multiple videos, provide comprehensive insights about the channel's overall audience.

Aggregated Audience Data:
{audience_data}

Individual Video Audience Analyses:
{video_analyses}

Please provide a detailed audience insights report that includes:

1. **Channel Audience Overview**: Overall demographic and behavioral characteristics
2. **Language and Geographic Distribution**: Detailed analysis of audience linguistic diversity
3. **Engagement Patterns**: How different language groups engage with content
4. **Audience Loyalty and Quality**: Analysis of feedback quality and community health
5. **Content Preferences by Audience Segment**: What different audience segments prefer
6. **Growth and Engagement Opportunities**: Specific recommendations for audience development
7. **Cultural and Regional Insights**: What the language distribution tells us about audience culture

Focus on actionable insights that can help with content strategy, community building, and channel growth.
Respond in {output_language} with clear headings and specific data-driven insights.
"""

# Key insights report prompt (focused and concise)
KEY_INSIGHTS_REPORT_PROMPT = """
Based on the video comment analyses provided, generate a concise strategic report focused on key insights and actionable recommendations only.

VIDEO ANALYSES:
{video_summaries}

Please create a report in {output_language} with the following structure:
1. EXECUTIVE SUMMARY (3-5 key findings)
2. TOP 3 STRATEGIC RECOMMENDATIONS
3. CONTENT PERFORMANCE HIGHLIGHTS (most successful content types)
4. CRITICAL AREAS FOR IMPROVEMENT (top 3 issues to address)

Keep the report concise and focused on actionable insights. Maximum 1500 words.
"""

# Comprehensive report generation prompt
COMPREHENSIVE_REPORT_PROMPT = """
You are an experienced YouTube channel analyst preparing a comprehensive strategic report for a content creator.
You have access to detailed comment analysis data from multiple videos and audience insights.

VIDEO ANALYSIS DATA:
```json
{video_summaries_json}
```

AUDIENCE INSIGHTS:
```
{audience_insights}
```

ANALYSIS CONFIGURATION:
- Analysis Model: {analysis_model}
- Videos Analyzed: {videos_analyzed}
- Language Filter: {language_filter}
- Minimum Comment Length: {min_length} characters

Your task is to create a comprehensive strategic report that combines both content analysis and audience insights.
Structure your report as follows:

## EXECUTIVE SUMMARY
- Key findings and overall channel performance
- Primary strengths and areas for improvement
- Top 3 strategic recommendations

## CONTENT ANALYSIS
### Overall Performance Across Videos
- Sentiment trends and patterns
- Most engaging content types and topics
- Common themes in viewer feedback

### Content Strengths
- What content consistently performs well
- Specific examples from the data
- Audience praise patterns

### Areas for Content Improvement
- Recurring criticisms and pain points
- Content gaps identified by viewers
- Technical or presentation issues

## AUDIENCE ANALYSIS
[Integrate the audience insights here, but make it flow with the overall report]

## STRATEGIC RECOMMENDATIONS
### Content Strategy
- Specific content creation recommendations
- Topics and formats to focus on
- Content issues to address

### Audience Development
- Recommendations for growing and engaging different audience segments
- Language and cultural considerations
- Community building strategies

### Production and Quality
- Technical improvements suggested by viewers
- Presentation and format recommendations

## ACTION PLAN
- Immediate actions to take (next 30 days)
- Medium-term improvements (3-6 months)
- Long-term strategic goals (6+ months)

Make the report actionable, specific, and data-driven. Include relevant statistics and examples.
Respond in {output_language}.
"""
