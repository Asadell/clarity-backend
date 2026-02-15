import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_TITLE: str = "Clarity Couple API"
    APP_VERSION: str = "1.0.0"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://clarity:clarity123@localhost:5433/claritydb")
    
    # Gemini API Keys (40 total)
    # 1-10: Query Embedding (Search)
    # 11-20: Batch Embedding (Indexing)
    # 21-30: Chat Response (RAG Generation)
    # 31-40: Analysis Modes
    GEMINI_API_KEY_1: str | None = None
    GEMINI_API_KEY_2: str | None = None
    GEMINI_API_KEY_3: str | None = None
    GEMINI_API_KEY_4: str | None = None
    GEMINI_API_KEY_5: str | None = None
    GEMINI_API_KEY_6: str | None = None
    GEMINI_API_KEY_7: str | None = None
    GEMINI_API_KEY_8: str | None = None
    GEMINI_API_KEY_9: str | None = None
    GEMINI_API_KEY_10: str | None = None
    GEMINI_API_KEY_11: str | None = None
    GEMINI_API_KEY_12: str | None = None
    GEMINI_API_KEY_13: str | None = None
    GEMINI_API_KEY_14: str | None = None
    GEMINI_API_KEY_15: str | None = None
    GEMINI_API_KEY_16: str | None = None
    GEMINI_API_KEY_17: str | None = None
    GEMINI_API_KEY_18: str | None = None
    GEMINI_API_KEY_19: str | None = None
    GEMINI_API_KEY_20: str | None = None
    GEMINI_API_KEY_21: str | None = None
    GEMINI_API_KEY_22: str | None = None
    GEMINI_API_KEY_23: str | None = None
    GEMINI_API_KEY_24: str | None = None
    GEMINI_API_KEY_25: str | None = None
    GEMINI_API_KEY_26: str | None = None
    GEMINI_API_KEY_27: str | None = None
    GEMINI_API_KEY_28: str | None = None
    GEMINI_API_KEY_29: str | None = None
    GEMINI_API_KEY_30: str | None = None
    GEMINI_API_KEY_31: str | None = None
    GEMINI_API_KEY_32: str | None = None
    GEMINI_API_KEY_33: str | None = None
    GEMINI_API_KEY_34: str | None = None
    GEMINI_API_KEY_35: str | None = None
    GEMINI_API_KEY_36: str | None = None
    GEMINI_API_KEY_37: str | None = None
    GEMINI_API_KEY_38: str | None = None
    GEMINI_API_KEY_39: str | None = None
    GEMINI_API_KEY_40: str | None = None
    
    @property
    def ALL_GEMINI_KEYS(self) -> List[str]:
        keys = []
        for i in range(1, 41):
            key = getattr(self, f"GEMINI_API_KEY_{i}")
            if key and key.strip():
                keys.append(key)
        return keys

    def _get_keys_for_group(self, group_idx: int) -> List[str]:
        """
        group_idx: 0=Query, 1=Batch, 2=Chat, 3=Analysis
        """
        all_keys = self.ALL_GEMINI_KEYS
        if not all_keys:
            return []
        
        # If we have 40 or more keys, use the legacy slicing
        if len(all_keys) >= 40:
            start = group_idx * 10
            return all_keys[start : start + 10]
        
        # If we have very few keys (less than 4), share all of them with everyone
        # to ensure every service has at least one key.
        if len(all_keys) < 4:
            return all_keys
            
        # Otherwise, partition them as fairly as possible
        part_size = len(all_keys) // 4
        start = group_idx * part_size
        # Last group gets the remainder
        end = (group_idx + 1) * part_size if group_idx < 3 else len(all_keys)
        return all_keys[start:end]

    @property
    def QUERY_EMBEDDING_KEYS(self) -> List[str]:
        return self._get_keys_for_group(0)

    @property
    def BATCH_EMBEDDING_KEYS(self) -> List[str]:
        return self._get_keys_for_group(1)

    @property
    def CHAT_RESPONSE_KEYS(self) -> List[str]:
        return self._get_keys_for_group(2)

    @property
    def ANALYSIS_KEYS(self) -> List[str]:
        return self._get_keys_for_group(3)

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
