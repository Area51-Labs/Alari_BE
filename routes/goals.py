"""
Goals routes - CRUD operations for user goals and check-ins.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user
import crud
from schemasx import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalListResponse,
    CheckInCreate,
    CheckInUpdate,
    CheckInResponse,
    CheckInListResponse
)
from database_models import User

router = APIRouter()


# ==================== GOAL ROUTES ====================

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new goal."""
    goal = crud.create_goal(
        db,
        user_id=current_user.id,
        title=goal_data.title,
        description=goal_data.description,
        target_date=goal_data.target_date
    )
    return goal


@router.get("", response_model=GoalListResponse)
async def list_goals(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all user goals.
    
    - **status**: Optional filter (active, completed, abandoned)
    """
    goals = crud.get_user_goals(db, current_user.id, status)
    
    return GoalListResponse(
        goals=goals,
        total=len(goals)
    )


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific goal."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: int,
    update_data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a goal's details."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Build update dict from non-None values
    update_dict = update_data.model_dump(exclude_unset=True)
    updated_goal = crud.update_goal(db, goal_id, update_dict)
    
    return updated_goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a goal and all its check-ins."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    crud.delete_goal(db, goal_id)


# ==================== CHECK-IN ROUTES ====================

@router.post("/{goal_id}/checkins", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    goal_id: int,
    checkin_data: CheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a check-in for a goal."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    checkin = crud.create_goal_checkin(
        db,
        goal_id=goal_id,
        progress_note=checkin_data.progress_note,
        completed=checkin_data.completed
    )
    
    return checkin


@router.get("/{goal_id}/checkins", response_model=CheckInListResponse)
async def list_checkins(
    goal_id: int,
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List check-ins for a goal."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    checkins = crud.get_goal_checkins(db, goal_id, limit)
    
    return CheckInListResponse(
        check_ins=checkins,
        total=len(checkins)
    )


@router.put("/{goal_id}/checkins/{checkin_id}", response_model=CheckInResponse)
async def update_checkin(
    goal_id: int,
    checkin_id: int,
    update_data: CheckInUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a check-in."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    checkin = crud.update_checkin(
        db,
        checkin_id=checkin_id,
        progress_note=update_data.progress_note,
        completed=update_data.completed
    )
    
    if not checkin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
    
    return checkin


@router.delete("/{goal_id}/checkins/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    goal_id: int,
    checkin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a check-in."""
    goal = crud.get_goal_by_id(db, goal_id)
    
    if not goal or goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    success = crud.delete_checkin(db, checkin_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Check-in not found"
        )
