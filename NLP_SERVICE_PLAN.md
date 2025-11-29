# NLP Service Implementation Plan

## ✅ IMPLEMENTED - External NLP API Integration

**Status:** The NLP service is now fully integrated with your external API at `http://36.255.68.49:5000/analyze`

### Implementation Details

**External API Endpoint:** `http://36.255.68.49:5000/analyze`  
**Request Format:**
```json
{
  "text": "Journal entry text to analyze"
}
```

**Response Format:**
```json
{
  "sentiment": "POSITIVE (1.0)" | "NEGATIVE (1.0)" | "NEUTRAL (0.5)",
  "themes": ["theme1", "theme2", "theme3", ...],
  "summary": "AI-generated summary of the text"
}
```

**Sentiment Mapping:**
- `"POSITIVE (x)"` → **+0.8** (positive sentiment)
- `"NEGATIVE (x)"` → **-0.8** (negative sentiment)  
- `"NEUTRAL (x)"` → **0.0** (neutral sentiment)

### Test Results

✅ **Positive Entry Test:**
```
Input: "Today was wonderful! Accomplished goals, family time, feeling grateful..."
Output:
  - Sentiment: 0.80
  - Themes: happiness, gratitude, achievement, family, positive_emotions
  - Processing time: ~19s
```

✅ **Negative Entry Test:**
```
Input: "Terrible day. Everything went wrong. Stressed, anxious, depressed..."
Output:
  - Sentiment: -0.80
  - Themes: work, conflict, stress, anxiety, emotional_distress
  - Processing time: ~18s
```

### Error Handling

The integration includes robust error handling:
- ⏱️ **Timeout**: 30 seconds (configurable via `NLP_API_TIMEOUT`)
- 🔄 **Fallback**: Returns neutral sentiment (0.0) and generic themes on failure
- 📝 **Logging**: All errors logged to worker console
- ✅ **Graceful degradation**: Journal entries still saved even if analysis fails

---

## 🎯 What Does the NLP Service Do?

The NLP service is a **background worker** that analyzes journal entries to provide intelligent insights to users. It processes text asynchronously to avoid blocking the API during journal creation.

### Core Purpose
Transform raw journal text into actionable psychological and emotional insights for users tracking their mental health and personal growth.

---

## 📊 What We Get From NLP Analysis

### 1. **Sentiment Score** (Float: -1.0 to 1.0)
Measures the emotional tone of the journal entry.

**Examples:**
```
Text: "Today was terrible. I felt overwhelmed and anxious all day."
→ Sentiment: -0.8 (very negative)

Text: "Had an okay day, nothing special happened."
→ Sentiment: 0.0 (neutral)

Text: "Amazing day! Accomplished all my goals and felt fantastic!"
→ Sentiment: 0.9 (very positive)
```

**Use Cases:**
- 📈 Mood tracking over time
- 📊 Visualize emotional trends
- ⚠️ Alert therapists/coaches if sentiment drops significantly
- 🎯 Correlate mood with activities, sleep, etc.

---

### 2. **Themes** (Array of strings)
Identifies key topics and concepts discussed in the entry.

**Examples:**
```
Text: "Went to the gym today and finished my project at work."
→ Themes: ["exercise", "work", "productivity", "achievement"]

Text: "Feeling anxious about my relationship. Had an argument with my partner."
→ Themes: ["anxiety", "relationships", "conflict", "emotional_distress"]

Text: "Grateful for my family. Spent quality time with my kids."
→ Themes: ["gratitude", "family", "parenting", "positive_emotions"]
```

**Use Cases:**
- 🏷️ Tag entries automatically
- 🔍 Search by theme ("Show me all entries about work stress")
- 📊 Track which life areas get most attention
- 🎯 Help therapists identify recurring concerns
- 💡 Suggest journaling prompts based on underrepresented themes

---

### 3. **Summary** (String, ~100-200 chars)
AI-generated concise summary of the entry.

**Examples:**
```
Original (500 words):
"Today I woke up early and went for a run. The weather was perfect, 
and I felt energized. At work, I completed the quarterly report ahead 
of schedule. My manager praised my work. In the evening, I cooked 
dinner for my family and we watched a movie together..."

Summary:
"Had a productive day with morning exercise, completed work project 
early, and enjoyed quality family time in the evening."
```

**Use Cases:**
- 📝 Quick overview in entry list
- 🔎 Faster browsing through past entries
- 📱 Mobile app preview
- 📊 Generate weekly/monthly reports
- 💬 Share highlights without exposing full text

---

## 🔄 How It Works (Current Flow)

```
1. User creates journal entry
   ↓
2. API saves to MongoDB
   ↓
3. API enqueues "JournalEntryCreatedEvent" to Redis
   ↓
4. NLP Worker picks up job from queue
   ↓
5. NLP Worker analyzes text (CURRENTLY PLACEHOLDER)
   ↓
6. NLP Worker returns "AnalysisCompletedEvent"
   ↓
7. Store results in database (TODO)
   ↓
8. Show insights to user in UI (TODO)
```

---

## 🚀 Implementation Options

### Option A: OpenAI API (Recommended for MVP)
**Pros:**
- ✅ Fastest to implement
- ✅ High quality results
- ✅ No infrastructure needed
- ✅ Handles sentiment, themes, summaries in one call

**Cons:**
- ❌ Costs money (~$0.002 per entry)
- ❌ Requires internet connection
- ❌ Data leaves your servers (privacy concern)

**Cost Estimate:**
- 100 entries/day × 30 days = 3,000 entries/month
- ~$6/month for basic usage

**Implementation:**
```python
import openai

def analyze_with_openai(text: str) -> dict:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": "You are a mental health journal analyst..."
        }, {
            "role": "user",
            "content": f"Analyze this journal entry:\n\n{text}"
        }],
        functions=[{
            "name": "journal_analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "sentiment": {"type": "number", "minimum": -1, "maximum": 1},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"}
                }
            }
        }],
        function_call={"name": "journal_analysis"}
    )
    return response.choices[0].message.function_call.arguments
```

---

### Option B: Hugging Face Transformers (Local/Open Source)
**Pros:**
- ✅ Free (after initial setup)
- ✅ Data stays private
- ✅ No per-request costs
- ✅ Works offline

**Cons:**
- ❌ Requires GPU for good performance
- ❌ More complex setup
- ❌ Needs separate models for each task
- ❌ Lower quality than GPT-4

**Models Needed:**
1. **Sentiment**: `cardiffnlp/twitter-roberta-base-sentiment-latest`
2. **Themes**: `facebook/bart-large-mnli` (zero-shot classification)
3. **Summary**: `facebook/bart-large-cnn`

**Implementation:**
```python
from transformers import pipeline

# Load models once at startup
sentiment_analyzer = pipeline("sentiment-analysis", 
    model="cardiffnlp/twitter-roberta-base-sentiment-latest")
theme_classifier = pipeline("zero-shot-classification",
    model="facebook/bart-large-mnli")
summarizer = pipeline("summarization",
    model="facebook/bart-large-cnn")

def analyze_with_transformers(text: str) -> dict:
    # Sentiment
    sentiment_result = sentiment_analyzer(text)[0]
    sentiment_score = convert_to_scale(sentiment_result)
    
    # Themes
    candidate_themes = ["work", "family", "health", "relationships", 
                       "anxiety", "happiness", "stress", "achievement"]
    theme_result = theme_classifier(text, candidate_themes)
    themes = theme_result["labels"][:5]  # Top 5
    
    # Summary
    summary = summarizer(text, max_length=150, min_length=50)[0]["summary_text"]
    
    return {
        "sentiment": sentiment_score,
        "themes": themes,
        "summary": summary
    }
```

---

### Option C: Hybrid Approach (Best for Production)
**Strategy:**
- Use local models for sentiment (fast, cheap)
- Use OpenAI for themes + summary (complex, better quality)
- Fall back to local if API unavailable

---

## 📦 What Needs to Be Stored

After analysis completes, we need to **store results** so the frontend can display them.

### Option 1: MongoDB Collection (Recommended)
```javascript
// New collection: journal_analyses
{
  _id: ObjectId("..."),
  entry_id: ObjectId("507f1f77bcf86cd799439011"),  // Link to journal_entries
  user_id: "3",
  sentiment: 0.75,
  themes: ["productivity", "achievement", "positive_mood"],
  summary: "User had a productive day...",
  analyzed_at: ISODate("2025-11-02T15:30:00Z")
}
```

### Option 2: Embed in Journal Entry (Simpler)
```javascript
// Updated journal_entries collection
{
  _id: ObjectId("507f1f77bcf86cd799439011"),
  user_id: "3",
  text: "Today was amazing...",
  created_at: ISODate("2025-11-02T10:00:00Z"),
  
  // Add analysis field
  analysis: {
    sentiment: 0.75,
    themes: ["productivity", "achievement"],
    summary: "User had a productive day...",
    analyzed_at: ISODate("2025-11-02T15:30:00Z")
  }
}
```

**I recommend Option 2** (embed) for MVP - simpler queries and fewer joins.

---

## 🎨 What Users See

### Journal Entry Card
```
┌─────────────────────────────────────────┐
│ 📅 November 2, 2025                     │
│                                         │
│ Today was amazing! I accomplished...    │
│                                         │
│ 😊 Sentiment: Very Positive (0.85)     │
│ 🏷️ productivity · achievement · work   │
│ 📝 Summary: "Productive day with..."   │
│                                         │
│ [Read Full Entry]                       │
└─────────────────────────────────────────┘
```

### Dashboard/Analytics
```
📊 Mood Trends (Last 30 Days)
  ┌────────────────────────┐
  │    📈 Sentiment Graph  │
  │  1.0 ┤      ╱╲         │
  │  0.5 ┤   ╱╲╱  ╲        │
  │  0.0 ┼──╱─────╲─╲──    │
  │ -0.5 ┤                 │
  └────────────────────────┘

🏷️ Most Common Themes
  1. work (15 entries)
  2. family (12 entries)
  3. anxiety (8 entries)
  4. exercise (6 entries)

💡 Insights
  • Your mood improves on days you exercise
  • Work-related stress peaks on Mondays
  • Family time correlates with positive sentiment
```

---

## ✅ Implementation Checklist

For Real NLP Implementation:

### Phase 1: Choose & Integrate Model
- [ ] Decide: OpenAI vs Transformers vs Hybrid
- [ ] Add dependencies to `pyproject.toml`
- [ ] Set up API keys or download models
- [ ] Implement `analyze_text()` function
- [ ] Test with sample entries

### Phase 2: Store Results
- [ ] Update MongoDB schema (add `analysis` field)
- [ ] Create `store_analysis_results()` function
- [ ] Update journal GET endpoints to include analysis
- [ ] Test retrieval with analysis data

### Phase 3: Error Handling
- [ ] Handle API failures gracefully
- [ ] Retry failed analyses
- [ ] Log errors to monitoring system
- [ ] Set timeouts for long-running analyses

### Phase 4: Optimization
- [ ] Cache common themes
- [ ] Batch process multiple entries
- [ ] Add rate limiting for API calls
- [ ] Monitor costs (if using OpenAI)

---

## 🔧 Example Implementation (OpenAI)

Here's what the real implementation would look like:

```python
# apps/nlp_service/nlp/worker/jobs.py
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ANALYSIS_PROMPT = """You are an expert mental health journal analyst. 
Analyze the following journal entry and provide:
1. Sentiment score from -1.0 (very negative) to 1.0 (very positive)
2. Key themes/topics (5-10 themes)
3. A brief summary (100-150 words)

Focus on emotional state, life domains, and psychological patterns."""

def analyze_journal_entry(event_data: dict) -> dict:
    """Analyze a journal entry using OpenAI"""
    
    text = event_data.get("text", "")
    entry_id = event_data.get("entry_id")
    user_id = event_data.get("user_id")
    
    print(f"📝 Analyzing journal entry: {entry_id}")
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": ANALYSIS_PROMPT},
                {"role": "user", "content": text}
            ],
            functions=[{
                "name": "journal_analysis",
                "description": "Structured analysis of a journal entry",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sentiment": {
                            "type": "number",
                            "description": "Sentiment from -1 to 1",
                            "minimum": -1,
                            "maximum": 1
                        },
                        "themes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key themes (5-10)"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary (100-150 words)"
                        }
                    },
                    "required": ["sentiment", "themes", "summary"]
                }
            }],
            function_call={"name": "journal_analysis"}
        )
        
        # Parse response
        analysis = json.loads(
            response.choices[0].message.function_call.arguments
        )
        
        result = {
            "entry_id": entry_id,
            "user_id": user_id,
            "sentiment": analysis["sentiment"],
            "themes": analysis["themes"],
            "summary": analysis["summary"]
        }
        
        print(f"✓ Analysis complete for entry {entry_id}")
        print(f"  Sentiment: {result['sentiment']:.2f}")
        print(f"  Themes: {', '.join(result['themes'][:3])}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Analysis failed for entry {entry_id}: {e}")
        # Return neutral fallback
        return {
            "entry_id": entry_id,
            "user_id": user_id,
            "sentiment": 0.0,
            "themes": ["journal"],
            "summary": text[:200]
        }
```

---

## 💰 Cost Considerations

### OpenAI Pricing (GPT-3.5-turbo)
- Input: $0.50 per 1M tokens
- Output: $1.50 per 1M tokens
- Average entry: ~300 tokens input + 150 tokens output
- **Cost per entry: ~$0.0002**

### Monthly Estimates
| Users | Entries/Day | Entries/Month | Monthly Cost |
|-------|-------------|---------------|--------------|
| 10    | 10          | 3,000         | $0.60        |
| 100   | 10          | 30,000        | $6.00        |
| 1,000 | 10          | 300,000       | $60.00       |

**Verdict:** Very affordable for MVP and early growth.

---

## ✅ Current Implementation (External API)

### Configuration

The NLP service is now integrated with an external API. Configuration is done via environment variables:

**Environment Variables:**
```bash
# In docker-compose.yml or .env
NLP_API_URL=http://36.255.68.49:5000/analyze  # External NLP API endpoint
NLP_API_TIMEOUT=30  # Timeout in seconds (default: 30)
```

### Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /journal
       ▼
┌─────────────────┐
│   API Service   │
└────┬────────────┘
     │ 1. Save to MongoDB
     │ 2. Enqueue to Redis
     ▼
┌─────────────────┐
│ Redis Queue     │
│ (nlp queue)     │
└────┬────────────┘
     │
     ▼
┌─────────────────┐
│  NLP Worker     │
│  (RQ)           │
└────┬────────────┘
     │ HTTP POST
     ▼
┌─────────────────┐
│ External NLP    │
│ API Service     │
│ (36.255.68.49)  │
└────┬────────────┘
     │ Analysis result
     ▼
┌─────────────────┐
│  Job Result     │
│  (Redis)        │
└─────────────────┘
```

### Performance Metrics

Based on actual tests:
- ⏱️ **Average processing time**: 18-20 seconds per entry
- 📊 **Queue**: Redis RQ with background processing
- 🔄 **Retry logic**: Built-in RQ retry on failure
- 💾 **Result storage**: Kept for 24 hours (86400 seconds)

### File Changes

**Modified Files:**
1. `apps/nlp_service/nlp/worker/jobs.py` - Integrated external API with httpx
   - `analyze_text()` - Async HTTP call to external API
   - `parse_sentiment()` - Converts API format to -1 to 1 scale
   - Error handling for timeouts, HTTP errors, network failures

---

## 🎯 Next Steps

Now that NLP analysis is working, the recommended next steps are:

1. ✅ **NLP Integration** - DONE!
2. **Store analysis results** - Update MongoDB schema to include analysis field
3. **Update GET /journal endpoints** to return analysis data
4. **Build frontend display** - Show sentiment, themes, and summaries in UI
5. **Add analytics dashboard** - Mood trends, theme analysis, insights
