"""
Chat routes - Send messages and get AI responses.
Orchestrates the complete chat flow with inference service.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import httpx
import os
from typing import Dict, Any

from database import get_db
from auth import get_current_user
import crud
from schemasx import ChatRequest, ChatResponse, MessageResponse
from database_models import User

router = APIRouter()

# Inference service configuration
INFERENCE_SERVICE_URL = os.getenv("INFERENCE_SERVICE_URL", "http://localhost:8001")
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY")


@router.post("/{session_id}", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response.
    
    Complete flow:
    1. Verify user owns conversation
    2. Get conversation history from DB
    3. Call inference service with full history
    4. Save BOTH user message and AI response to DB (single commit)
    5. Return both messages
    
    This avoids excess DB writes by batching the operations.
    """
    
    # Step 1: Verify conversation ownership
    conversation = crud.get_conversation_by_session_id(db, session_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Step 2: Get full conversation history
    existing_messages = crud.get_conversation_messages(db, conversation.id)
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in existing_messages
    ]
    
    # Add current user message to history for inference
    message_history.append({"role": "user", "content": request.message})
    
    # Step 3: Call inference service
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            inference_response = await client.post(
                f"{INFERENCE_SERVICE_URL}/inference/chat",
                json={
                    "messages": message_history,
                    "max_tokens": request.max_tokens or 512,
                    "temperature": request.temperature or 0.7
                },
                headers={
                    "X-API-Key": INFERENCE_API_KEY,
                    "Content-Type": "application/json"
                }
            )
            
            if inference_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Inference service error: {inference_response.status_code}"
                )
            
            ai_response_data = inference_response.json()
            ai_message_content = ai_response_data["response"]
            usage = ai_response_data.get("usage", {})
    
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Inference service timeout"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot connect to inference service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during inference: {str(e)}"
        )
    
    # Step 4: Save BOTH messages in a single transaction
    user_msg, assistant_msg = crud.create_message_pair(
        db,
        conversation_id=conversation.id,
        user_message=request.message,
        assistant_message=ai_message_content
    )
    
    # Step 5: Return both messages
    return ChatResponse(
        session_id=session_id,
        user_message=MessageResponse(
            id=user_msg.id,
            role=user_msg.role,
            content=user_msg.content,
            created_at=user_msg.created_at
        ),
        assistant_message=MessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            created_at=assistant_msg.created_at
        ),
        usage=usage
    )


@router.post("/{session_id}/stream")
async def send_message_streaming(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message with streaming response.
    
    Note: User message is saved immediately, AI response saved after stream completes.
    """
    
    # Verify conversation
    conversation = crud.get_conversation_by_session_id(db, session_id)
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message immediately
    user_msg = crud.create_message(
        db,
        conversation_id=conversation.id,
        role="user",
        content=request.message
    )
    
    # Get conversation history
    all_messages = crud.get_conversation_messages(db, conversation.id)
    message_history = [
        {"role": msg.role, "content": msg.content}
        for msg in all_messages
    ]
    
    # Stream response
    async def stream_generator():
        full_response = ""
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    f"{INFERENCE_SERVICE_URL}/inference/chat/stream",
                    json={
                        "messages": message_history,
                        "max_tokens": request.max_tokens or 512,
                        "temperature": request.temperature or 0.7
                    },
                    headers={
                        "X-API-Key": INFERENCE_API_KEY,
                        "Content-Type": "application/json"
                    }
                ) as response:
                    async for chunk in response.aiter_text():
                        full_response += chunk
                        yield chunk
        
        except Exception as e:
            yield f"\n[ERROR: {str(e)}]"
            return
        
        # After streaming completes, save AI response
        if full_response:
            crud.create_message(
                db,
                conversation_id=conversation.id,
                role="assistant",
                content=full_response
            )
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/plain"
    )
