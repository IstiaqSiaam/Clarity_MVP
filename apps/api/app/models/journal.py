"""
Journal Entry Models and Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        from pydantic_core import core_schema
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_plain_validator_function(cls.validate),
        ])


# Analysis Models
class AnalysisResult(BaseModel):
    """NLP analysis results for a journal entry"""
    model_config = ConfigDict(from_attributes=True)
    
    sentiment: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1 (negative) to 1 (positive)")
    themes: List[str] = Field(..., description="Extracted themes/topics")
    summary: str = Field(..., description="AI-generated summary")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="When analysis was completed")


# MongoDB Document Model
class JournalEntryDocument(BaseModel):
    """Journal entry as stored in MongoDB"""
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="User ID who owns this entry")
    text: str = Field(..., min_length=1, max_length=10000, description="Journal entry text")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enc_blob: Optional[str] = Field(default=None, description="Encrypted blob for future use")
    analysis: Optional[AnalysisResult] = Field(default=None, description="NLP analysis results")


# Request/Response Schemas
class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry"""
    text: str = Field(..., min_length=1, max_length=10000, description="Journal entry text")


class JournalEntryUpdate(BaseModel):
    """Schema for updating a journal entry"""
    text: str = Field(..., min_length=1, max_length=10000, description="Updated journal entry text")


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(..., description="Entry ID")
    user_id: str = Field(..., description="User ID")
    text: str = Field(..., description="Journal entry text")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    enc_blob: Optional[str] = Field(default=None, description="Encrypted blob")
    analysis: Optional[AnalysisResult] = Field(default=None, description="NLP analysis results")

    @staticmethod
    def from_document(doc: JournalEntryDocument) -> "JournalEntryResponse":
        """Convert MongoDB document to response model"""
        return JournalEntryResponse(
            id=str(doc.id),
            user_id=doc.user_id,
            text=doc.text,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            enc_blob=doc.enc_blob,
            analysis=doc.analysis
        )


class JournalEntryList(BaseModel):
    """Paginated list of journal entries"""
    entries: list[JournalEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
