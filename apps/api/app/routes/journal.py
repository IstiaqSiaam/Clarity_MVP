"""
Journal API endpoints
"""
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.database import get_database
from app.core.auth import RequiresAuth
from app.models.journal import (
    JournalEntryCreate,
    JournalEntryResponse,
    JournalEntryList,
    JournalEntryDocument,
)
from app.models.events import JournalEntryCreatedEvent
from app.services.queue import enqueue_analysis_job

router = APIRouter(prefix="/journal", tags=["Journal"])


@router.post(
    "",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new journal entry"
)
async def create_journal_entry(
    entry: JournalEntryCreate,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth
) -> JournalEntryResponse:
    """
    Create a new journal entry and enqueue it for NLP analysis.
    
    - **text**: The journal entry text (1-10000 characters)
    
    Returns the created entry with its ID and timestamps.
    Automatically enqueues the entry for sentiment analysis and theme extraction.
    
    Requires authentication.
    """
    # Get user_id from authenticated user
    user_id = str(current_user.id)
    
    # Create the document
    entry_doc = JournalEntryDocument(
        user_id=user_id,
        text=entry.text,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Insert into MongoDB
    result = await db.journal_entries.insert_one(
        entry_doc.model_dump(by_alias=True, exclude={"id"})
    )
    
    # Get the inserted document
    created_doc = await db.journal_entries.find_one({"_id": result.inserted_id})
    if not created_doc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve created entry"
        )
    
    # Convert to document model
    doc = JournalEntryDocument(**created_doc)
    
    # Create event for the queue
    event = JournalEntryCreatedEvent(
        entry_id=str(result.inserted_id),
        user_id=user_id,
        text=entry.text,
        created_at=doc.created_at
    )
    
    # Enqueue analysis job
    try:
        job_id = enqueue_analysis_job(event)
        print(f"✓ Enqueued analysis job {job_id} for entry {result.inserted_id}")
    except Exception as e:
        print(f"⚠ Failed to enqueue analysis job: {e}")
        # Don't fail the request if queue fails
    
    # Return response
    return JournalEntryResponse.from_document(doc)


@router.get(
    "",
    response_model=JournalEntryList,
    summary="Get paginated list of journal entries"
)
async def get_journal_entries(
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of entries per page")
) -> JournalEntryList:
    """
    Get a paginated list of journal entries for the current user.
    
    - **page**: Page number (starting from 1)
    - **page_size**: Number of entries per page (1-100)
    
    Returns entries ordered by creation date (newest first).
    
    Requires authentication.
    """
    # Get user_id from authenticated user
    user_id = str(current_user.id)
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Query filter
    query = {"user_id": user_id}
    
    # Get total count
    total = await db.journal_entries.count_documents(query)
    
    # Get paginated entries
    cursor = db.journal_entries.find(query).sort("created_at", -1).skip(skip).limit(page_size)
    entries_raw = await cursor.to_list(length=page_size)
    
    # Convert to response models
    entries = [
        JournalEntryResponse.from_document(JournalEntryDocument(**doc))
        for doc in entries_raw
    ]
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return JournalEntryList(
        entries=entries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get(
    "/{entry_id}",
    response_model=JournalEntryResponse,
    summary="Get a specific journal entry"
)
async def get_journal_entry(
    entry_id: str,
    db: Annotated[AsyncIOMotorDatabase, Depends(get_database)],
    current_user: RequiresAuth
) -> JournalEntryResponse:
    """
    Get a specific journal entry by ID.
    
    - **entry_id**: The MongoDB ObjectId of the entry
    
    Returns 404 if the entry doesn't exist or doesn't belong to the user.
    
    Requires authentication.
    """
    # Get user_id from authenticated user
    user_id = str(current_user.id)
    # Validate ObjectId
    if not ObjectId.is_valid(entry_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entry ID format"
        )
    
    # Find the entry
    entry_raw = await db.journal_entries.find_one({
        "_id": ObjectId(entry_id),
        "user_id": user_id
    })
    
    if not entry_raw:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entry {entry_id} not found"
        )
    
    # Convert and return
    doc = JournalEntryDocument(**entry_raw)
    return JournalEntryResponse.from_document(doc)
