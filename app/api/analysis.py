from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.db import get_db
from ..core.di import container
from pydantic import BaseModel, UUID4
from typing import Optional, Dict, Any

router = APIRouter()

class AnalysisRequest(BaseModel):
    user_uuid: UUID4
    contact_id: str
    question: Optional[str] = None # For question mode

@router.post("/analysis/quick-reply")
async def generate_quick_reply(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    service = container.get("analysis_service")
    return await service.generate_quick_reply(db, request.user_uuid, request.contact_id)

@router.post("/analysis/conflict")
async def analyze_conflict(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    service = container.get("analysis_service")
    return await service.analyze_conflict(db, request.user_uuid, request.contact_id)

@router.post("/analysis/pattern")
async def detect_pattern(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    service = container.get("analysis_service")
    return await service.detect_pattern(db, request.user_uuid, request.contact_id)

@router.post("/analysis/question")
async def answer_question(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    if not request.question:
        raise HTTPException(status_code=400, detail="Question is required for this mode")
    service = container.get("analysis_service")
    return await service.answer_question(db, request.user_uuid, request.contact_id, request.question)
