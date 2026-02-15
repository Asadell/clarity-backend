from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from ..core.models import Chat, User
from ..prompts.chat_prompts import CHAT_SYSTEM_PROMPT
from ..core.logger import get_logger
import json

logger = get_logger(__name__)

import google.generativeai as genai

class ChatService:
    def __init__(self, embedding_service, chat_response_manager):
        self.embedding_service = embedding_service
        self.chat_response_manager = chat_response_manager
        # Models are now pre-initialized in the manager

    async def _get_context(self, db: AsyncSession, user_uuid: str, contact_id: str, query_embedding: list[float], limit: int = 5) -> str:
        # Vector search using pgvector
        # Operator <-> is L2 distance, <=> is cosine distance, <#> is negative inner product
        # Usually cosine distance <=> is best for embeddings. Lower is better/closer.
        
        stmt = select(Chat).where(
            Chat.user_uuid == user_uuid,
            Chat.contact_id == contact_id
        ).order_by(
            Chat.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        result = await db.execute(stmt)
        chats = result.scalars().all()
        
        context_parts = []
        for chat in chats:
            context_parts.append(f"[{chat.sender}]: {chat.message}")
            
        return "\n".join(context_parts)

    async def _save_message(self, db: AsyncSession, user_uuid: str, contact_id: str, message: str, sender: str, embedding: list[float] = None):
        new_chat = Chat(
            user_uuid=user_uuid,
            contact_id=contact_id,
            message=message,
            sender=sender,
            embedding=embedding
        )
        db.add(new_chat)
        await db.commit()
        await db.refresh(new_chat)
        return new_chat

    async def chat(self, db: AsyncSession, user_uuid: str, contact_id: str, message: str) -> str:
        logger.info(f"Processing chat for user {user_uuid} with contact {contact_id}")
        
        # 1. Generate embedding for user message
        query_embedding = await self.embedding_service.generate_query_embedding(message)
        
        # 2. Save user message first (so it's in history, but maybe exclude from this query context?)
        # Conventionally, we save it.
        await self._save_message(db, user_uuid, contact_id, message, "user", query_embedding)
        
        # 3. Retrieve context
        # We might want to exclude the just-saved message if it appears (distance 0).
        # But `limit` and logic usually handles it.
        context_str = await self._get_context(db, user_uuid, contact_id, query_embedding)
        
        # 4. Generate Response
        prompt = CHAT_SYSTEM_PROMPT.format(context=context_str, message=message)
        
        def _call_chat_api(model_config):
            # Use pre-initialized model from model_config
            model = model_config['model']
            response = model.generate_content(prompt)
            return response.text

        response_text = self.chat_response_manager.execute_with_fallback(_call_chat_api)
        
        # 5. Generate embedding for AI response (Batch/Document type)
        # We treat AI response as a document for future retrieval.
        response_embedding_list = await self.embedding_service.generate_batch_embedding([response_text])
        response_embedding = response_embedding_list[0]
        
        # 6. Save AI Response
        await self._save_message(db, user_uuid, contact_id, response_text, "ai", response_embedding)
        
        return response_text
