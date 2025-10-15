"""
Conversation routes - manage chat conversations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
import crud
from schemasx import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse
)
from database_models import User
from config import SYSTEM_PROMPT

router = APIRouter()


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation.
    
    Automatically creates a system message with the AI prompt.
    """
    conversation = crud.create_conversation(
        db,
        user_id=current_user.id,
        title=conv_data.title
    )
    
    # Create system message
    crud.create_message(
        db,
        conversation_id=conversation.id,
        role="system",
        content=SYSTEM_PROMPT
    )
    
    return ConversationResponse(
        id=conversation.id,
        session_id=conversation.session_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=1
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all user conversations.
    
    Returns conversations sorted by most recently updated.
    """
    conversations = crud.get_user_conversations(db, current_user.id, limit)
    
    conv_responses = []
    for conv in conversations:
        messages = crud.get_conversation_messages(db, conv.id)
        conv_responses.append(
            ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(messages)
            )
        )
    
    return ConversationListResponse(
        conversations=conv_responses,
        total=len(conv_responses)
    )


@router.get("/{session_id}", response_model=ConversationResponse)
async def get_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with message count."""
    conversation = crud.get_conversation_by_session_id(db, session_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = crud.get_conversation_messages(db, conversation.id)
    
    return ConversationResponse(
        id=conversation.id,
        session_id=conversation.session_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(messages)
    )


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages in a conversation.
    
    Returns messages in chronological order.
    """
    conversation = crud.get_conversation_by_session_id(db, session_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = crud.get_conversation_messages(db, conversation.id)
    return messages


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    
    This action cannot be undone.
    """
    conversation = crud.get_conversation_by_session_id(db, session_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    crud.delete_conversation(db, session_id)
