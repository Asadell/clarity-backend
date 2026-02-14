from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="user", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    contact_id = Column(String, nullable=False, index=True)
    contact_name = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'ai'
    embedding = Column(Vector(3072))  # Gemini embedding-001 dimension (3072)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)
    contact_id = Column(String, nullable=True)
    mode = Column(String, nullable=False, index=True)  # 'quick-reply', 'conflict', 'pattern', 'question'
    input_data = Column(JSONB, nullable=True)
    result = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analysis_results")
