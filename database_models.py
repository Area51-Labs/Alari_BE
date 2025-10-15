"""
Database models for the Alari motivational chatbot application.
SQLAlchemy ORM models for PostgreSQL database.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    """User model for storing user authentication and profile information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    user_name = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation model for tracking chat sessions."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)  # Optional conversation title
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Message model for storing individual chat messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # system, user, assistant
    content = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=True)  # Extracted keywords for search/analytics
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Goal(Base):
    """Goal model for user goal tracking."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    target_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active")  # active, completed, abandoned
    streak_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="goals")
    check_ins = relationship("GoalCheckIn", back_populates="goal", cascade="all, delete-orphan", order_by="GoalCheckIn.check_in_date.desc()")


class GoalCheckIn(Base):
    """Goal check-in model for tracking daily/periodic progress."""
    __tablename__ = "goal_check_ins"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False)
    check_in_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    progress_note = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)  # Did they complete the goal for this day?

    # Relationships
    goal = relationship("Goal", back_populates="check_ins")
