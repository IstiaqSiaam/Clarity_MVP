# apps/api/app/routes/analytics.py
from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any, Annotated
from datetime import datetime, timedelta
from collections import Counter
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.auth import RequiresAuth
from app.core.database import get_database

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/mood-trend")
async def get_mood_trend(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get mood trend over specified number of days.
    
    Returns daily average sentiment scores and entry counts.
    """
    user_id = str(current_user.id)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query journal entries with analysis
    collection = db.journal_entries
    cursor = collection.find({
        "user_id": user_id,
        "created_at": {"$gte": start_date, "$lte": end_date},
        "analysis": {"$exists": True, "$ne": None}
    }).sort("created_at", 1)
    
    entries = await cursor.to_list(length=None)
    
    # Group by date
    daily_data: Dict[str, List[float]] = {}
    for entry in entries:
        date_key = entry["created_at"].strftime("%Y-%m-%d")
        sentiment = entry.get("analysis", {}).get("sentiment", 0.0)
        
        if date_key not in daily_data:
            daily_data[date_key] = []
        daily_data[date_key].append(sentiment)
    
    # Calculate daily averages
    trend_data = []
    for date_str in sorted(daily_data.keys()):
        sentiments = daily_data[date_str]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        trend_data.append({
            "date": date_str,
            "average_sentiment": round(avg_sentiment, 2),
            "entry_count": len(sentiments),
            "mood_label": _get_mood_label(avg_sentiment)
        })
    
    # Calculate overall statistics
    all_sentiments = [s for sentiments in daily_data.values() for s in sentiments]
    overall_avg = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0.0
    
    return {
        "period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days
        },
        "overall_statistics": {
            "average_sentiment": round(overall_avg, 2),
            "total_entries": len(entries),
            "entries_with_analysis": len(all_sentiments),
            "mood_label": _get_mood_label(overall_avg)
        },
        "daily_trend": trend_data
    }


@router.get("/themes")
async def get_theme_analysis(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get theme analysis over specified number of days.
    
    Returns most common themes and their frequency.
    """
    user_id = str(current_user.id)
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Query journal entries with analysis
    collection = db.journal_entries
    cursor = collection.find({
        "user_id": user_id,
        "created_at": {"$gte": start_date, "$lte": end_date},
        "analysis": {"$exists": True, "$ne": None}
    })
    
    entries = await cursor.to_list(length=None)
    
    # Collect all themes
    all_themes = []
    positive_themes = []
    negative_themes = []
    neutral_themes = []
    
    for entry in entries:
        analysis = entry.get("analysis", {})
        themes = analysis.get("themes", [])
        sentiment = analysis.get("sentiment", 0.0)
        
        all_themes.extend(themes)
        
        # Categorize by sentiment
        if sentiment > 0.3:
            positive_themes.extend(themes)
        elif sentiment < -0.3:
            negative_themes.extend(themes)
        else:
            neutral_themes.extend(themes)
    
    # Count theme frequencies
    theme_counter = Counter(all_themes)
    positive_counter = Counter(positive_themes)
    negative_counter = Counter(negative_themes)
    
    return {
        "period": {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "days": days
        },
        "statistics": {
            "total_entries": len(entries),
            "total_themes": len(all_themes),
            "unique_themes": len(theme_counter)
        },
        "top_themes": [
            {"theme": theme, "count": count, "percentage": round(count / len(all_themes) * 100, 1)}
            for theme, count in theme_counter.most_common(10)
        ] if all_themes else [],
        "positive_themes": [
            {"theme": theme, "count": count}
            for theme, count in positive_counter.most_common(5)
        ] if positive_themes else [],
        "negative_themes": [
            {"theme": theme, "count": count}
            for theme, count in negative_counter.most_common(5)
        ] if negative_themes else [],
        "theme_distribution": {
            "positive": len(positive_themes),
            "negative": len(negative_themes),
            "neutral": len(neutral_themes)
        }
    }


def _get_mood_label(sentiment: float) -> str:
    """Convert sentiment score to mood label."""
    if sentiment >= 0.6:
        return "very_positive"
    elif sentiment >= 0.2:
        return "positive"
    elif sentiment >= -0.2:
        return "neutral"
    elif sentiment >= -0.6:
        return "negative"
    else:
        return "very_negative"
