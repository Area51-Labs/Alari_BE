"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== USER SCHEMAS ====================

class UserCreate(BaseModel):
    """User registration."""
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
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_id: int


# ==================== CONVERSATION SCHEMAS ====================

class ConversationCreate(BaseModel):
    """Create conversation."""
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """Conversation response."""
    id: int
    session_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: List[ConversationResponse]
    total: int


# ==================== MESSAGE SCHEMAS ====================

class MessageCreate(BaseModel):
    """Create message."""
    role: str  # 'system', 'user', 'assistant'
    content: str
    keywords: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== GOAL SCHEMAS ====================

class GoalCreate(BaseModel):
    """Create goal."""
    title: str = Field(max_length=255)
    description: Optional[str] = None
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    """Update goal."""
    title: Optional[str] = None
    description: Optional[str] = None
    target_date: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|abandoned)$")


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


class GoalListResponse(BaseModel):
    """List of goals."""
    goals: List[GoalResponse]
    total: int


# ==================== CHECK-IN SCHEMAS ====================

class CheckInCreate(BaseModel):
    """Create check-in."""
    progress_note: Optional[str] = None
    completed: bool = False


class CheckInUpdate(BaseModel):
    """Update check-in."""
    progress_note: Optional[str] = None
    completed: Optional[bool] = None


class CheckInResponse(BaseModel):
    """Check-in response."""
    id: int
    goal_id: int
    check_in_date: datetime
    progress_note: Optional[str] = None
    completed: bool
    
    class Config:
        from_attributes = True


class CheckInListResponse(BaseModel):
    """List of check-ins."""
    check_ins: List[CheckInResponse]
    total: int

class ChatRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7


class ChatResponse(BaseModel):
    """Complete chat response with both messages."""
    session_id: str
    user_message: MessageResponse
    assistant_message: MessageResponse
    usage: Dict[str, Any] = {}