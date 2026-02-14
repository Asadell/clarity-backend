from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..core.db import get_db
from ..core.models import Chat
from ..core.di import container
from pydantic import BaseModel, UUID4
from typing import List, Optional

router = APIRouter()

class ChatRequest(BaseModel):
    user_uuid: UUID4
    contact_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    
class MessageSchema(BaseModel):
    id: int
    sender: str
    message: str
    created_at: str

@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    chat_service = container.get("chat_service")
    response_text = await chat_service.chat(db, request.user_uuid, request.contact_id, request.message)
    return ChatResponse(response=response_text)

@router.get("/chat/{user_uuid}/{contact_id}/history", response_model=List[MessageSchema])
async def get_chat_history(user_uuid: UUID4, contact_id: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    # Retrieve history
    stmt = select(Chat).where(
        Chat.user_uuid == user_uuid,
        Chat.contact_id == contact_id
    ).order_by(desc(Chat.created_at)).limit(limit)
    
    result = await db.execute(stmt)
    chats = result.scalars().all()
    
    # Return in chronological order
    history = []
    for chat in reversed(chats):
        history.append(MessageSchema(
            id=chat.id,
            sender=chat.sender,
            message=chat.message,
            created_at=chat.created_at.isoformat()
        ))
        
    return history
