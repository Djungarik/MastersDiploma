"""
Authentication Router
Handles user registration, login, and profile
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from datetime import timedelta

from app.database import get_user_by_email, create_user
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_auth,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()


# Request/Response Models
class UserRegister(BaseModel):
    """Registration request"""
    email: EmailStr
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserLogin(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data response (no password)"""
    id: int
    email: str
    username: str
    is_active: bool


class TokenResponse(BaseModel):
    """Login response with token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister) -> TokenResponse:
    """
    Register a new user account.
    Returns access token on success.
    """
    # Check if email already exists
    existing_user = await get_user_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with hashed password
    hashed_password = get_password_hash(data.password)
    user = await create_user(
        email=data.email,
        username=data.username,
        hashed_password=hashed_password
    )
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    print(f"New user registered: {user['email']}")
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin) -> TokenResponse:
    """
    Login with email and password.
    Returns access token on success.
    """
    # Find user by email
    user = await get_user_by_email(data.email)
    print(f"Login attempt for: {data.email}")
    print(f"   User found: {user is not None}")
    
    if not user:
        print("   User not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Debug: show stored hash
    print(f"   Stored hash: {user['hashed_password'][:20] if user.get('hashed_password') else 'NONE'}...")
    
    # Verify password
    try:
        password_valid = verify_password(data.password, user["hashed_password"])
        print(f"   Password valid: {password_valid}")
    except Exception as e:
        print(f"   Password verification error: {e}")
        password_valid = False
    
    if not password_valid:
        print("   Password mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    print(f"User logged in: {user['email']}")
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            username=user["username"],
            is_active=user["is_active"],
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_auth)) -> UserResponse:
    """
    Get current authenticated user's profile.
    Requires valid JWT token.
    """
    return UserResponse(
        id=user["id"],
        email=user["email"],
        username=user["username"],
        is_active=user["is_active"],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(user: dict = Depends(require_auth)) -> MessageResponse:
    """
    Logout current user.
    Note: With JWT, logout is handled client-side by removing the token.
    This endpoint is for logging/tracking purposes.
    """
    print(f"User logged out: {user['email']}")
    return MessageResponse(message="Successfully logged out")
