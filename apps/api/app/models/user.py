"""
User database models and schemas
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
import enum


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# Enums
class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserType(str, enum.Enum):
    INDIVIDUAL = "individual"
    THERAPIST = "therapist"
    COACH = "coach"
    TEAM = "team"


# SQLAlchemy ORM Model
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    user_type: Mapped[str] = mapped_column(SQLEnum(UserType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    plan: Mapped[str] = mapped_column(SQLEnum(PlanType), default=PlanType.FREE, nullable=False)
    
    @property
    def type(self) -> str:
        """Alias for user_type to match Pydantic schema"""
        return self.user_type
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email}, type={self.user_type}, plan={self.plan})>"


# Pydantic Models
class UserSignup(BaseModel):
    """Schema for user signup"""
    name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=72, description="User password (8-72 characters)")
    type: UserType = Field(..., description="User type: individual, therapist, coach, or team")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="User ID")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User email")
    type: UserType = Field(..., description="User type")
    plan: str = Field(..., description="User subscription plan")
    created_at: datetime = Field(..., description="Account creation timestamp")


class SignupResponse(BaseModel):
    """Schema for signup response (no tokens)"""
    message: str = Field(..., description="Success message")
    user: UserResponse = Field(..., description="Created user information")


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str = Field(..., description="JWT refresh token")


class TokenData(BaseModel):
    """Schema for JWT token payload data"""
    user_id: int = Field(..., description="User ID from token")
    email: str = Field(..., description="User email from token")
    token_type: str = Field(..., description="Token type (access or refresh)")
