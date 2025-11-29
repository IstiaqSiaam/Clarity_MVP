"""
Authentication API endpoints
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.auth import RequiresAuth
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import (
    User,
    UserSignup,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    SignupResponse,
    PlanType,
    UserType
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def signup(
    user_data: UserSignup,
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> SignupResponse:
    """
    Register a new user account.
    
    - **name**: User's full name (2-255 characters)
    - **email**: Valid email address (must be unique)
    - **password**: Password (8-72 characters)
    - **type**: User type (individual, therapist, coach, or team)
    
    Returns user information only. Use /auth/login to get tokens.
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_pw,
        user_type=user_data.type,
        plan=PlanType.FREE
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Prepare response (no tokens)
    user_response = UserResponse.model_validate(new_user)
    
    return SignupResponse(
        message="Account created successfully. Please login to continue.",
        user=user_response
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user"
)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> TokenResponse:
    """
    Authenticate a user and return JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    
    Returns JWT access and refresh tokens upon successful authentication.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    # Verify user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    
    # Prepare response
    user_response = UserResponse.model_validate(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token"
)
async def refresh(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> TokenResponse:
    """
    Refresh an access token using a refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new JWT access and refresh tokens.
    """
    # Decode and verify refresh token
    token_payload = decode_token(token_data.refresh_token)
    
    if not token_payload or token_payload.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists
    result = await db.execute(
        select(User).where(User.id == token_payload.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    
    # Prepare response
    user_response = UserResponse.model_validate(user)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user"
)
async def get_current_user_info(
    current_user: RequiresAuth
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Requires valid JWT access token in Authorization header.
    """
    return UserResponse.model_validate(current_user)
