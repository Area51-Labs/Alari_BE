"""
Pydantic models for the user backend.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from passlib.context import CryptContext


class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(min_length=8)
    user_name: Optional[str] = None


class UserResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    user_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int


class LoginRequest(BaseModel):
    """Login request (alternative to form)."""
    email: str
    password: str


class ConversationCreate(BaseModel):
    """Create conversation request."""
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Create message request."""
    role: str  # 'user' or 'assistant'
    content: str
    keywords: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    role: str
    content: str
    keywords: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class GoalCreate(BaseModel):
    """Create goal request."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    """Update goal request."""
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[str] = None  # 'active', 'completed', 'abandoned'
    streak_count: Optional[int] = None


class GoalResponse(BaseModel):
    """Goal response."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: str
    streak_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CheckInCreate(BaseModel):
    """Create goal check-in request."""
    progress_note: Optional[str] = None
    completed: bool = False


class CheckInResponse(BaseModel):
    """Goal check-in response."""
    id: int
    goal_id: int
    check_in_date: datetime
    progress_note: Optional[str] = None
    completed: bool
    
    class Config:
        from_attributes = True
