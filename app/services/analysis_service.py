from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..core.models import Chat, AnalysisResult
from ..prompts.analysis_prompts import QUICK_REPLY_PROMPT, CONFLICT_PROMPT, PATTERN_PROMPT, QUESTION_PROMPT
from ..core.logger import get_logger
import json

logger = get_logger(__name__)

import google.generativeai as genai

class AnalysisService:
    def __init__(self, embedding_service, analysis_manager):
        self.embedding_service = embedding_service
        self.analysis_manager = analysis_manager
        # Models are now pre-initialized in the manager

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
        def _call_api(model_config):
            # Use the pre-initialized model from model_config
            model = model_config['model']
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            try:
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response.text}")
                raise e

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
        
        def _call_api(model_config):
            model = model_config['model']
            response = model.generate_content(prompt)
            return {
                "answer": response.text,
                "question": question
            }

        result = self.analysis_manager.execute_with_fallback(_call_api)
        # await self._save_result(db, user_uuid, contact_id, "question", result)
        return result

    async def generate_key_questions(self, db: AsyncSession, user_uuid: str, contact_id: str):
        # 1. Get History (Limit 200 for maximum context - we want REAL quotes)
        history = await self._get_history(db, user_uuid, contact_id, limit=200)
        
        # 2. Get Contact Details (Name, Duration)
        # For now using placeholder. In production, fetch from Contact table.
        partner_name = "Pasangan"
        
        # 3. Get Conflict Analysis for Context (Score & Level)
        # Using placeholders for speed. Could call analyze_conflict if needed.
        conflict_context = {
            "score": "Unknown",
            "level": "Unknown"
        }
        
        # 4. Format Prompt
        from ..prompts.analysis_prompts import KEY_QUESTIONS_PROMPT
        
        # We need to ensure the format arguments match the prompt's expectations
        prompt = KEY_QUESTIONS_PROMPT.format(
            partner_name=partner_name,
            relationship_duration="Unknown",
            conflict_score=conflict_context["score"],
            conflict_level=conflict_context["level"],
            history=history
        )
        
        result = await self._generate_analysis(prompt)
        return result
