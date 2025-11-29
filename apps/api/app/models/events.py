"""
Event payload models for message queue
"""
from datetime import datetime
from pydantic import BaseModel, Field


class JournalEntryCreatedEvent(BaseModel):
    """Event published when a journal entry is created"""
    entry_id: str = Field(..., description="Journal entry ID")
    user_id: str = Field(..., description="User ID who created the entry")
    text: str = Field(..., description="Journal entry text")
    created_at: datetime = Field(..., description="Creation timestamp")


class AnalysisCompletedEvent(BaseModel):
    """Event published when NLP analysis is completed"""
    entry_id: str = Field(..., description="Journal entry ID")
    user_id: str = Field(..., description="User ID")
    sentiment: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 to 1")
    themes: list[str] = Field(..., description="Identified themes in the entry")
    summary: str = Field(..., description="Generated summary of the entry")
