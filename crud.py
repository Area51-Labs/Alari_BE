"""
CRUD operations for all database models.
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database_models import User, Conversation, Message, Goal, GoalCheckIn


# ==================== USER CRUD ====================

def create_user(db: Session, email: str, hashed_password: str, user_name: Optional[str] = None) -> User:
    """Create a new user."""
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        user_name=user_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


# ==================== CONVERSATION CRUD ====================

def create_conversation(db: Session, user_id: int, title: Optional[str] = None) -> Conversation:
    """Create a new conversation."""
    session_id = f"conv-{uuid.uuid4().hex}"
    db_conversation = Conversation(
        user_id=user_id,
        session_id=session_id,
        title=title
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_conversation_by_session_id(db: Session, session_id: str) -> Optional[Conversation]:
    """Get conversation by session ID."""
    return db.query(Conversation).filter(Conversation.session_id == session_id).first()


def get_user_conversations(db: Session, user_id: int, limit: int = 50) -> List[Conversation]:
    """Get all conversations for a user."""
    return db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).limit(limit).all()


def delete_conversation(db: Session, session_id: str) -> bool:
    """Delete a conversation."""
    conversation = get_conversation_by_session_id(db, session_id)
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False


def update_conversation_timestamp(db: Session, conversation_id: int):
    """Update conversation's updated_at timestamp."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = datetime.now(timezone.utc)
        db.commit()


# ==================== MESSAGE CRUD ====================

def create_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    keywords: Optional[List[str]] = None
) -> Message:
    """Create a new message."""
    db_message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        keywords=keywords
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Update conversation timestamp
    update_conversation_timestamp(db, conversation_id)
    
    return db_message


def get_conversation_messages(db: Session, conversation_id: int) -> List[Message]:
    """Get all messages for a conversation."""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()


# ==================== GOAL CRUD ====================

def create_goal(
    db: Session,
    user_id: int,
    title: str,
    description: Optional[str] = None,
    target_date: Optional[datetime] = None
) -> Goal:
    """Create a new goal."""
    db_goal = Goal(
        user_id=user_id,
        title=title,
        description=description,
        target_date=target_date,
        status="active"
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


def get_user_goals(db: Session, user_id: int, status: Optional[str] = None) -> List[Goal]:
    """Get all goals for a user."""
    query = db.query(Goal).filter(Goal.user_id == user_id)
    if status:
        query = query.filter(Goal.status == status)
    return query.order_by(Goal.created_at.desc()).all()


def get_goal_by_id(db: Session, goal_id: int) -> Optional[Goal]:
    """Get a goal by ID."""
    return db.query(Goal).filter(Goal.id == goal_id).first()


def update_goal(db: Session, goal_id: int, update_data: dict) -> Optional[Goal]:
    """Update a goal."""
    goal = get_goal_by_id(db, goal_id)
    if goal:
        for key, value in update_data.items():
            if value is not None:
                setattr(goal, key, value)
        goal.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(goal)
    return goal


def delete_goal(db: Session, goal_id: int) -> bool:
    """Delete a goal."""
    goal = get_goal_by_id(db, goal_id)
    if goal:
        db.delete(goal)
        db.commit()
        return True
    return False


# ==================== GOAL CHECK-IN CRUD ====================

def create_goal_checkin(
    db: Session,
    goal_id: int,
    progress_note: Optional[str] = None,
    completed: bool = False
) -> GoalCheckIn:
    """Create a new check-in."""
    db_checkin = GoalCheckIn(
        goal_id=goal_id,
        progress_note=progress_note,
        completed=completed
    )
    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)
    
    # Update goal streak if completed
    if completed:
        goal = get_goal_by_id(db, goal_id)
        if goal:
            goal.streak_count += 1
            goal.updated_at = datetime.now(timezone.utc)
            db.commit()
    
    return db_checkin


def get_goal_checkins(db: Session, goal_id: int, limit: int = 30) -> List[GoalCheckIn]:
    """Get check-ins for a goal."""
    return db.query(GoalCheckIn).filter(
        GoalCheckIn.goal_id == goal_id
    ).order_by(GoalCheckIn.check_in_date.desc()).limit(limit).all()


def get_checkin_by_id(db: Session, checkin_id: int) -> Optional[GoalCheckIn]:
    """Get a check-in by ID."""
    return db.query(GoalCheckIn).filter(GoalCheckIn.id == checkin_id).first()


def update_checkin(
    db: Session,
    checkin_id: int,
    progress_note: Optional[str] = None,
    completed: Optional[bool] = None
) -> Optional[GoalCheckIn]:
    """Update a check-in."""
    checkin = get_checkin_by_id(db, checkin_id)
    if checkin:
        if progress_note is not None:
            checkin.progress_note = progress_note
        if completed is not None:
            checkin.completed = completed
        db.commit()
        db.refresh(checkin)
    return checkin


def delete_checkin(db: Session, checkin_id: int) -> bool:
    """Delete a check-in."""
    checkin = get_checkin_by_id(db, checkin_id)
    if checkin:
        db.delete(checkin)
        db.commit()
        return True
    return False
