# apps/api/app/routes/search.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

from app.core.auth import RequiresAuth
from app.core.database import get_database

router = APIRouter(prefix="/search", tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(10, ge=1, le=100, description="Maximum number of results")
    filter_sentiment: Optional[str] = Field(None, description="Filter by sentiment: positive, negative, neutral")
    filter_themes: Optional[List[str]] = Field(None, description="Filter by specific themes")
    start_date: Optional[datetime] = Field(None, description="Filter entries from this date")
    end_date: Optional[datetime] = Field(None, description="Filter entries until this date")


class SearchResult(BaseModel):
    id: str
    text: str
    created_at: datetime
    sentiment: Optional[float] = None
    themes: Optional[List[str]] = None
    summary: Optional[str] = None
    relevance_score: float
    matched_terms: List[str]


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]
    search_time_ms: float


@router.post("", response_model=SearchResponse)
async def search_journal_entries(
    request: SearchRequest,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth
) -> SearchResponse:
    """
    Search journal entries using keyword matching and semantic filtering.
    
    Supports:
    - Keyword search in text, summary, and themes
    - Sentiment filtering
    - Theme filtering
    - Date range filtering
    - Relevance scoring
    """
    start_time = datetime.utcnow()
    user_id = str(current_user.id)
    
    # Build MongoDB query
    mongo_query: Dict[str, Any] = {"user_id": user_id}
    
    # Date range filter
    date_filter = {}
    if request.start_date:
        date_filter["$gte"] = request.start_date
    if request.end_date:
        date_filter["$lte"] = request.end_date
    if date_filter:
        mongo_query["created_at"] = date_filter
    
    # Sentiment filter
    if request.filter_sentiment:
        sentiment_ranges = {
            "positive": {"$gte": 0.2},
            "negative": {"$lte": -0.2},
            "neutral": {"$gte": -0.2, "$lte": 0.2}
        }
        if request.filter_sentiment in sentiment_ranges:
            mongo_query["analysis.sentiment"] = sentiment_ranges[request.filter_sentiment]
    
    # Theme filter
    if request.filter_themes:
        mongo_query["analysis.themes"] = {"$in": request.filter_themes}
    
    # Execute query
    collection = db.journal_entries
    cursor = collection.find(mongo_query)
    entries = await cursor.to_list(length=None)
    
    # Perform keyword matching and scoring
    search_terms = _extract_search_terms(request.query)
    scored_results = []
    
    for entry in entries:
        score, matched_terms = _calculate_relevance_score(
            entry,
            search_terms,
            request.query
        )
        
        if score > 0:  # Only include entries with matches
            analysis = entry.get("analysis", {})
            scored_results.append({
                "id": str(entry["_id"]),
                "text": entry["text"],
                "created_at": entry["created_at"],
                "sentiment": analysis.get("sentiment"),
                "themes": analysis.get("themes"),
                "summary": analysis.get("summary"),
                "relevance_score": score,
                "matched_terms": matched_terms
            })
    
    # Sort by relevance score
    scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    # Limit results
    results = scored_results[:request.max_results]
    
    # Calculate search time
    end_time = datetime.utcnow()
    search_time_ms = (end_time - start_time).total_seconds() * 1000
    
    return SearchResponse(
        query=request.query,
        total_results=len(scored_results),
        results=results,
        search_time_ms=round(search_time_ms, 2)
    )


def _extract_search_terms(query: str) -> List[str]:
    """Extract individual search terms from query."""
    # Remove special characters and convert to lowercase
    cleaned = re.sub(r'[^\w\s]', ' ', query.lower())
    # Split into words and filter out short words
    terms = [term for term in cleaned.split() if len(term) > 2]
    return terms


def _calculate_relevance_score(
    entry: dict,
    search_terms: List[str],
    original_query: str
) -> tuple[float, List[str]]:
    """
    Calculate relevance score for an entry based on keyword matching.
    
    Scoring system:
    - Exact phrase match in text: +10 points
    - Term match in text: +3 points per term
    - Term match in summary: +2 points per term
    - Term match in themes: +1 point per term
    - Case-insensitive matching
    """
    score = 0.0
    matched_terms = set()
    
    text = entry.get("text", "").lower()
    analysis = entry.get("analysis", {})
    summary = analysis.get("summary", "").lower() if analysis else ""
    themes = [t.lower() for t in analysis.get("themes", [])] if analysis else []
    
    # Check for exact phrase match
    if original_query.lower() in text:
        score += 10.0
        matched_terms.add(original_query)
    
    # Check individual terms
    for term in search_terms:
        # Match in text (highest weight)
        if term in text:
            score += 3.0
            matched_terms.add(term)
        
        # Match in summary
        if term in summary:
            score += 2.0
            matched_terms.add(term)
        
        # Match in themes
        for theme in themes:
            if term in theme or theme in term:
                score += 1.0
                matched_terms.add(term)
    
    return score, list(matched_terms)
