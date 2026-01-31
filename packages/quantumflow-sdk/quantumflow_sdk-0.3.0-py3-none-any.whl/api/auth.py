"""
Authentication for QuantumFlow API.

Supports:
- API Key authentication
- JWT tokens for user sessions
- Database-backed user management
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from db import crud
from db.models import User, APIKey as APIKeyModel


# Configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_SCHEME = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: str
    exp: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: Optional[str]
    tier: str
    is_active: bool

    class Config:
        from_attributes = True


class APIKeyResponse(BaseModel):
    """API key response (without full key)."""
    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


# ============== JWT Functions ==============

def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=user_id, exp=payload.get("exp"))
    except JWTError:
        return None


# ============== Auth Dependencies ==============

def get_db_session():
    """Get database session."""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    bearer: Optional[object] = Security(BEARER_SCHEME),
    db: Session = Depends(get_db_session),
) -> User:
    """
    Get the current authenticated user.

    Supports both API Key and Bearer token authentication.
    Returns the User object from database.
    """
    # Try API Key first
    if api_key:
        key_record = crud.get_api_key(db, api_key)
        if key_record:
            crud.update_api_key_usage(db, key_record)
            user = crud.get_user(db, key_record.user_id)
            if user and user.is_active:
                return user

    # Try Bearer token
    if bearer and hasattr(bearer, 'credentials'):
        token_data = verify_token(bearer.credentials)
        if token_data:
            try:
                user_id = UUID(token_data.user_id)
                user = crud.get_user(db, user_id)
                if user and user.is_active:
                    return user
            except ValueError:
                pass

    # Fallback: Allow dev key in development
    if api_key == "qf_dev_key_123" and os.getenv("ENV", "development") == "development":
        # Create or get dev user
        dev_user = crud.get_user_by_email(db, "dev@quantumflow.local")
        if not dev_user:
            dev_user = crud.create_user(db, "dev@quantumflow.local", "devpassword", "Dev User")
        return dev_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_user(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    bearer: Optional[object] = Security(BEARER_SCHEME),
    db: Session = Depends(get_db_session),
) -> Optional[User]:
    """Get user if authenticated, None otherwise."""
    try:
        return await get_current_user(api_key, bearer, db)
    except HTTPException:
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user


async def check_user_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db_session),
) -> User:
    """Check if user is within their usage quota."""
    if not crud.check_quota(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly API quota exceeded. Please upgrade your plan.",
        )
    return current_user


# ============== Helper Functions ==============

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    return crud.authenticate_user(db, email, password)


def create_user(db: Session, email: str, password: str, name: Optional[str] = None) -> User:
    """Create a new user."""
    return crud.create_user(db, email, password, name)


def create_api_key_for_user(
    db: Session,
    user_id: UUID,
    name: str,
    scopes: Optional[list[str]] = None,
) -> tuple[APIKeyModel, str]:
    """Create API key for user. Returns (key_record, raw_key)."""
    return crud.create_api_key(db, user_id, name, scopes)
