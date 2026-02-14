from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.db import get_db
from ..core.models import User, Chat, AnalysisResult
from pydantic import BaseModel, UUID4
from datetime import datetime

router = APIRouter()

class UserValidateRequest(BaseModel):
    uuid: UUID4

class UserStats(BaseModel):
    uuid: UUID4
    chat_count: int
    analysis_count: int
    created_at: datetime

@router.post("/users/validate")
async def validate_user(request: UserValidateRequest, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.uuid == request.uuid))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(uuid=request.uuid)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    return {"status": "valid", "uuid": user.uuid}

@router.get("/users/{uuid}/stats", response_model=UserStats)
async def get_user_stats(uuid: UUID4, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.uuid == uuid))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Count chats
    chat_result = await db.execute(select(func.count()).where(Chat.user_uuid == uuid))
    chat_count = chat_result.scalar()
    
    # Count specific analyses
    analysis_result = await db.execute(select(func.count()).where(AnalysisResult.user_uuid == uuid))
    analysis_count = analysis_result.scalar()
    
    return UserStats(
        uuid=user.uuid,
        chat_count=chat_count,
        analysis_count=analysis_count,
        created_at=user.created_at
    )
