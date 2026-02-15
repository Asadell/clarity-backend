import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from typing import Dict, Any, List
from .config import settings
from .logger import get_logger
from ..services.embedding_service import EmbeddingService
from ..services.chat_service import ChatService
from ..services.analysis_service import AnalysisService

logger = get_logger(__name__)

class SpecializedModelManager:
    def __init__(self, api_keys: List[str], function_name: str, model_name: str = None):
        self.api_keys = api_keys
        self.function_name = function_name
        self.model_name = model_name  # e.g., 'gemini-3-flash-preview' or None for embedding
        self.models = []  # Store pre-initialized model instances
        self.current_index = 0
        
        self._initialize_models()
        
    def _initialize_models(self):
        """Pre-initialize all models with their respective API keys at startup"""
        logger.info(f"Pre-initializing {len(self.api_keys)} models for {self.function_name}...")
        
        for i, key in enumerate(self.api_keys):
            try:
                # Configure genai with this specific key
                genai.configure(api_key=key)
                
                # Create model instance if needed (for chat/analysis)
                if self.model_name:
                    model = genai.GenerativeModel(self.model_name)
                    self.models.append({
                        'key': key,
                        'model': model,
                        'key_suffix': key[-4:]
                    })
                else:
                    # For embedding, just store the key (embedding uses genai.embed_content)
                    self.models.append({
                        'key': key,
                        'model': None,
                        'key_suffix': key[-4:]
                    })
                    
                logger.info(f"✓ Model {i+1}/{len(self.api_keys)} initialized for {self.function_name}")
            except Exception as e:
                logger.error(f"✗ Model {i+1} failed for {self.function_name}: {e}")
        
        if not self.models:
            logger.warning(f"No valid models initialized for {self.function_name}!")

    def get_next_model(self):
        """Get next pre-initialized model in rotation"""
        if not self.models:
            raise ValueError(f"No available models for {self.function_name}")
            
        model_config = self.models[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.models)
        return model_config
        
    def execute_with_fallback(self, func):
        """
        Execute a function with pre-initialized model rotation.
        func should accept a model_config dict with 'key' and 'model' fields.
        
        When a 429 quota exceeded error occurs, immediately switch to the next pre-initialized model.
        """
        attempts = 0
        max_attempts = len(self.models)
        
        while attempts < max_attempts:
            model_config = self.get_next_model()
            try:
                # Configure genai with the key (needed for embedding and other operations)
                genai.configure(api_key=model_config['key'])
                # Pass the pre-initialized model to the function
                return func(model_config)
            except google_exceptions.ResourceExhausted as e:
                # 429 Quota Exceeded - immediately try next model
                logger.warning(f"{self.function_name} quota exceeded with key ...{model_config['key_suffix']}")
                attempts += 1
                continue
            except Exception as e:
                logger.warning(f"{self.function_name} failed with key ...{model_config['key_suffix']}: {e}")
                attempts += 1
        
        raise RuntimeError(f"All models failed for {self.function_name}")


class DIContainer:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        
    def register(self, name: str, service: Any):
        self._services[name] = service
        
    def get(self, name: str) -> Any:
        return self._services.get(name)
        
    def init_services(self):
        logger.info("Initializing services...")
        
        # Initialize specialized managers with model names
        # Embedding managers don't need model_name (they use genai.embed_content directly)
        query_emb_manager = SpecializedModelManager(
            settings.QUERY_EMBEDDING_KEYS, 
            "QueryEmbedding",
            model_name=None
        )
        batch_emb_manager = SpecializedModelManager(
            settings.BATCH_EMBEDDING_KEYS, 
            "BatchEmbedding",
            model_name=None
        )
        
        # Chat and Analysis managers need GenerativeModel instances
        chat_response_manager = SpecializedModelManager(
            settings.CHAT_RESPONSE_KEYS, 
            "ChatResponse",
            model_name='gemini-3-flash-preview'
        )
        analysis_manager = SpecializedModelManager(
            settings.ANALYSIS_KEYS, 
            "Analysis",
            model_name='gemini-3-flash-preview'
        )
        
        self.register("query_emb_manager", query_emb_manager)
        self.register("batch_emb_manager", batch_emb_manager)
        self.register("chat_response_manager", chat_response_manager)
        self.register("analysis_manager", analysis_manager)
        
        # Initialize Services
        embedding_service = EmbeddingService(query_emb_manager, batch_emb_manager)
        self.register("embedding_service", embedding_service)
        
        chat_service = ChatService(embedding_service, chat_response_manager)
        self.register("chat_service", chat_service)
        
        analysis_service = AnalysisService(embedding_service, analysis_manager)
        self.register("analysis_service", analysis_service)
        
        logger.info("Services initialized successfully")

container = DIContainer()
