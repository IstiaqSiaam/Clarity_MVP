# apps/nlp_service/nlp/worker/jobs.py
import os
import asyncio
import httpx
from typing import Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# External NLP API configuration
NLP_API_URL = os.getenv("NLP_API_URL", "http://36.255.68.49:5000/analyze")
NLP_API_TIMEOUT = int(os.getenv("NLP_API_TIMEOUT", "30"))  # seconds

# MongoDB configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://clarity:clarity@mongo:27017/clarity")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "clarity")


def parse_sentiment(sentiment_str: str) -> float:
    """
    Parse sentiment string from API to float score.
    
    API returns: "POSITIVE (1.0)", "NEGATIVE (1.0)", "NEUTRAL (0.5)"
    We need to return: -1.0 to 1.0 scale
    
    Args:
        sentiment_str: Sentiment string from API (e.g., "POSITIVE (1.0)")
        
    Returns:
        Float between -1.0 and 1.0
    """
    sentiment_str = sentiment_str.upper()
    
    if "POSITIVE" in sentiment_str:
        return 0.8  # Positive sentiment
    elif "NEGATIVE" in sentiment_str:
        return -0.8  # Negative sentiment
    elif "NEUTRAL" in sentiment_str:
        return 0.0  # Neutral
    else:
        # Fallback: try to extract number from parentheses
        try:
            import re
            match = re.search(r'\(([0-9.]+)\)', sentiment_str)
            if match:
                score = float(match.group(1))
                # Assume it's already normalized or normalize it
                if "NEGATIVE" in sentiment_str:
                    return -abs(score)
                return score
        except:
            pass
    
    return 0.0  # Default to neutral if parsing fails


async def analyze_text(text: str) -> dict:
    """
    Call external NLP API to analyze text.
    
    Args:
        text: Journal entry text to analyze
        
    Returns:
        dict with sentiment, themes, summary
    """
    try:
        async with httpx.AsyncClient(timeout=NLP_API_TIMEOUT) as client:
            response = await client.post(
                NLP_API_URL,
                json={"text": text},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse the response
            sentiment_str = data.get("sentiment", "NEUTRAL (0.0)")
            sentiment_score = parse_sentiment(sentiment_str)
            
            return {
                "sentiment": sentiment_score,
                "themes": data.get("themes", []),
                "summary": data.get("summary", text[:200])
            }
            
    except httpx.TimeoutException:
        print(f"⚠️ NLP API timeout after {NLP_API_TIMEOUT}s")
        return {
            "sentiment": 0.0,
            "themes": ["journal"],
            "summary": text[:200]
        }
    except httpx.HTTPError as e:
        print(f"⚠️ NLP API HTTP error: {e}")
        return {
            "sentiment": 0.0,
            "themes": ["journal"],
            "summary": text[:200]
        }
    except Exception as e:
        print(f"⚠️ NLP API unexpected error: {e}")
        return {
            "sentiment": 0.0,
            "themes": ["journal"],
            "summary": text[:200]
        }


def analyze_text_sync(text: str) -> dict:
    """RQ-friendly synchronous wrapper"""
    return asyncio.run(analyze_text(text))


async def store_analysis_in_mongodb(entry_id: str, analysis_data: dict) -> bool:
    """
    Store analysis results in MongoDB.
    
    Args:
        entry_id: Journal entry ID
        analysis_data: Analysis results (sentiment, themes, summary)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[MONGO_DB_NAME]
        collection = db.journal_entries
        
        # Prepare analysis document
        analysis_doc = {
            "sentiment": analysis_data.get("sentiment", 0.0),
            "themes": analysis_data.get("themes", []),
            "summary": analysis_data.get("summary", ""),
            "analyzed_at": datetime.utcnow()
        }
        
        # Update the journal entry
        result = await collection.update_one(
            {"_id": ObjectId(entry_id)},
            {"$set": {
                "analysis": analysis_doc,
                "updated_at": datetime.utcnow()
            }}
        )
        
        client.close()
        
        if result.modified_count > 0:
            print(f"✓ Stored analysis in MongoDB for entry {entry_id}")
            return True
        else:
            print(f"⚠️ Entry {entry_id} not found in MongoDB")
            return False
            
    except Exception as e:
        print(f"❌ Failed to store analysis in MongoDB: {e}")
        return False


def store_analysis_sync(entry_id: str, analysis_data: dict) -> bool:
    """Synchronous wrapper for storing analysis"""
    return asyncio.run(store_analysis_in_mongodb(entry_id, analysis_data))


def analyze_journal_entry(event_data: dict) -> dict:
    """
    Analyze a journal entry from the queue using external NLP API.
    Then store the results in MongoDB.
    
    Args:
        event_data: JournalEntryCreatedEvent data
        
    Returns:
        Analysis results (sentiment, themes, summary)
    """
    entry_id = event_data.get("entry_id")
    user_id = event_data.get("user_id")
    text = event_data.get("text", "")
    
    print(f"📝 Analyzing journal entry: {entry_id}")
    print(f"   Text preview: {text[:100]}...")
    print(f"   Calling NLP API: {NLP_API_URL}")
    
    # Call external NLP service
    analysis = analyze_text_sync(text)
    
    # Prepare result payload (AnalysisCompletedEvent)
    result = {
        "entry_id": entry_id,
        "user_id": user_id,
        "sentiment": analysis.get("sentiment", 0.0),
        "themes": analysis.get("themes", ["general"]),
        "summary": analysis.get("summary", text[:200])
    }
    
    print(f"✓ Analysis complete for entry {entry_id}")
    print(f"  Sentiment: {result['sentiment']:.2f}")
    print(f"  Themes: {', '.join(result['themes'][:5])}")
    print(f"  Summary: {result['summary'][:80]}...")
    
    # Store results in MongoDB
    print(f"💾 Storing analysis in MongoDB...")
    store_success = store_analysis_sync(entry_id, result)
    
    if not store_success:
        print(f"⚠️ Warning: Analysis completed but not stored in MongoDB")
    
    return result
