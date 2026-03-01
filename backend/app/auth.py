"""
Authentication utilities for Adaptive OST
Handles JWT tokens and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_user_by_id

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

# Security scheme
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    """Token payload data"""
    user_id: int | None = None


def get_secret_key() -> str:
    """Get or generate secret key for JWT"""
    settings = get_settings()
    # Use a combination of available keys as secret, or a default for development
    secret = settings.groq_api_key or settings.openai_api_key or "adaptive-ost-dev-secret-key-change-in-production"
    return secret[:32] + "adaptive-ost-auth"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData | None:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(user_id=user_id)
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict | None:
    """
    Get current user from JWT token.
    Returns None if no token or invalid token (allows optional auth).
    """
    if not credentials:
        return None
    
    token_data = decode_token(credentials.credentials)
    if not token_data or not token_data.user_id:
        return None
    
    user = await get_user_by_id(token_data.user_id)
    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Require authentication - raises 401 if not authenticated.
    Use this for protected endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_token(credentials.credentials)
    if not token_data or not token_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await get_user_by_id(token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user
