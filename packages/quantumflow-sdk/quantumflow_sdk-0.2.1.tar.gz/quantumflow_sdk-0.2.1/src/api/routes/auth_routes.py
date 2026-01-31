"""
Authentication Routes.

Endpoints for user registration, login, and API key management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.auth import (
    get_db_session,
    get_current_user,
    get_current_active_user,
    create_access_token,
    authenticate_user,
    create_user,
    create_api_key_for_user,
    TokenResponse,
    UserResponse,
    APIKeyResponse,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from db import crud
from db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== Request Models ==============

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class CreateAPIKeyRequest(BaseModel):
    """Create API key request."""
    name: str
    scopes: Optional[list[str]] = None


class APIKeyCreatedResponse(BaseModel):
    """Response when API key is created (includes full key)."""
    id: str
    name: str
    key: str  # Only returned once!
    prefix: str
    message: str = "Save this key securely - it won't be shown again"


# ============== Routes ==============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db_session),
):
    """
    Register a new user account.
    """
    # Check if email exists
    existing = crud.get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = create_user(db, request.email, request.password, request.name)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        tier=user.tier,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session),
):
    """
    Login and get JWT access token.
    """
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Update last login
    crud.update_user_login(db, user)

    # Create token
    token = create_access_token(str(user.id))

    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current user profile.
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        name=current_user.name,
        tier=current_user.tier,
        is_active=current_user.is_active,
    )


@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    Get current user's usage statistics.
    """
    usage = crud.get_user_usage(db, current_user.id)
    monthly = crud.get_monthly_usage(db, current_user.id)

    return {
        "user_id": str(current_user.id),
        "tier": current_user.tier,
        "monthly_quota": current_user.monthly_quota,
        "monthly_used": monthly,
        "monthly_remaining": max(0, current_user.monthly_quota - monthly),
        "all_time": usage,
    }


# ============== API Key Management ==============

@router.post("/keys", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    Create a new API key.

    The full key is only returned once - save it securely!
    """
    key_record, raw_key = create_api_key_for_user(
        db, current_user.id, request.name, request.scopes
    )

    return APIKeyCreatedResponse(
        id=str(key_record.id),
        name=key_record.name,
        key=raw_key,
        prefix=key_record.prefix,
    )


@router.get("/keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    List all API keys for current user.
    """
    keys = crud.get_user_api_keys(db, current_user.id)

    return [
        APIKeyResponse(
            id=str(k.id),
            name=k.name,
            prefix=k.prefix,
            created_at=k.created_at,
            last_used=k.last_used,
            is_active=k.is_active,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
):
    """
    Revoke an API key.
    """
    from uuid import UUID

    try:
        uuid_key_id = UUID(key_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID")

    # Verify key belongs to user
    keys = crud.get_user_api_keys(db, current_user.id)
    if not any(k.id == uuid_key_id for k in keys):
        raise HTTPException(status_code=404, detail="API key not found")

    success = crud.revoke_api_key(db, uuid_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key revoked", "key_id": key_id}
