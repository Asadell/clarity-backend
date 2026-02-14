from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..core.models import Chat, AnalysisResult
from ..prompts.analysis_prompts import QUICK_REPLY_PROMPT, CONFLICT_PROMPT, PATTERN_PROMPT, QUESTION_PROMPT
from ..core.logger import get_logger
import json

logger = get_logger(__name__)

class AnalysisService:
    def __init__(self, embedding_service, analysis_manager):
        self.embedding_service = embedding_service
        self.analysis_manager = analysis_manager

    async def _get_history(self, db: AsyncSession, user_uuid: str, contact_id: str, limit: int = 20) -> str:
        stmt = select(Chat).where(
            Chat.user_uuid == user_uuid,
            Chat.contact_id == contact_id
        ).order_by(desc(Chat.created_at)).limit(limit)
        
        result = await db.execute(stmt)
        chats = result.scalars().all()
        # Reverse to chronological order
        chats = chats[::-1]
        
        history_parts = []
        for chat in chats:
            history_parts.append(f"[{chat.sender}]: {chat.message}")
            
        return "\n".join(history_parts)

    async def _save_result(self, db: AsyncSession, user_uuid: str, contact_id: str, mode: str, result: dict):
        new_result = AnalysisResult(
            user_uuid=user_uuid,
            contact_id=contact_id,
            mode=mode,
            result=result
        )
        db.add(new_result)
        await db.commit()
        await db.refresh(new_result)
        return new_result

    async def _generate_analysis(self, prompt: str) -> dict:
        def _call_api():
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-3-flash-preview')
            # Force JSON mode if possible or just parse text
            # Gemini 1.5 Pro and 2.0 Flash support response_mime_type='application/json'
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)

        return self.analysis_manager.execute_with_fallback(_call_api)

    async def generate_quick_reply(self, db: AsyncSession, user_uuid: str, contact_id: str):
        history = await self._get_history(db, user_uuid, contact_id, limit=20)
        prompt = QUICK_REPLY_PROMPT.format(history=history)
        result = await self._generate_analysis(prompt)
        # await self._save_result(db, user_uuid, contact_id, "quick-reply", result)
        return result

    async def analyze_conflict(self, db: AsyncSession, user_uuid: str, contact_id: str):
        history = await self._get_history(db, user_uuid, contact_id, limit=50)
        prompt = CONFLICT_PROMPT.format(history=history)
        result = await self._generate_analysis(prompt)
        # await self._save_result(db, user_uuid, contact_id, "conflict", result)
        return result

    async def detect_pattern(self, db: AsyncSession, user_uuid: str, contact_id: str):
        history = await self._get_history(db, user_uuid, contact_id, limit=100)
        prompt = PATTERN_PROMPT.format(history=history)
        result = await self._generate_analysis(prompt)
        # await self._save_result(db, user_uuid, contact_id, "pattern", result)
        return result

    async def answer_question(self, db: AsyncSession, user_uuid: str, contact_id: str, question: str):
        # RAG for specific question
        query_embedding = await self.embedding_service.generate_query_embedding(question)
        
        # Re-use ChatService retrieval logic or duplicate minimal logic here?
        # Duplicating minimal logic to avoid circular dependency if ChatService uses AnalysisService (unlikely but possible)
        # Or better: AnalysisService creates its own context retrieval.
        
        # Similar to ChatService._get_context but I'll implement it inline or helper
        # Actually I can't easily reuse without importing ChatService.
        # I'll duplicate the vector search logic for now or move it to a Repository.
        # Given simpler scope, duplicate is fine.
        
        stmt = select(Chat).where(
            Chat.user_uuid == user_uuid,
            Chat.contact_id == contact_id
        ).order_by(
            Chat.embedding.cosine_distance(query_embedding)
        ).limit(5)
        
        result = await db.execute(stmt)
        chats = result.scalars().all()
        context_parts = [f"[{c.sender}]: {c.message}" for c in chats]
        context_str = "\n".join(context_parts)
        
        prompt = QUESTION_PROMPT.format(context=context_str, question=question)
        
        def _call_api():
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-3-flash-preview')
            response = model.generate_content(prompt)
            return {"answer": response.text} # Wrap in logic to match signature

        result = self.analysis_manager.execute_with_fallback(_call_api)
        # await self._save_result(db, user_uuid, contact_id, "question", result)
        return result
