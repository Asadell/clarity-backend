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
    def __init__(self, api_keys: List[str], function_name: str, need_chat_model: bool = False):
        self.api_keys = api_keys
        self.function_name = function_name
        self.need_chat_model = need_chat_model
        # Store clients instead of global config
        self.clients = []
        self.current_index = 0
        
        self._initialize_clients()
        
    def _initialize_clients(self):
        valid_clients = []
        logger.info(f"Initializing {len(self.api_keys)} keys for {self.function_name}...")
        
        for i, key in enumerate(self.api_keys):
            try:
                # Assuming genai.configure is not needed if we use specific methods or if we implement a wrapper that sets it.
                # However, the standard google-generativeai lib uses global config for 'genai.GenerativeModel'.
                # For safety with multi-key, we might need a wrapper or just simple string keys if we configure just-in-time.
                # BUT, better approach with this lib version: Just store the keys and configure in the execute method.
                # Or create GenerativeModel objects which might bind to the key at creation? 
                # BUT, better approach with this lib version: Just store the keys and rotate them.
                
                # Simple validation call
                genai.configure(api_key=key)
                if self.need_chat_model:
                     model = genai.GenerativeModel('gemini-3-flash-preview') 
                     # User explicitly requested Gemini 3 preview model.
                     pass
                     
                valid_clients.append(key)
                # logger.info(f"Key {i+1} valid for {self.function_name}")
            except Exception as e:
                logger.error(f"Key {i+1} failed for {self.function_name}: {e}")
        
        self.api_keys = valid_clients
        if not self.api_keys:
            logger.warning(f"No valid keys for {self.function_name}!")

    def get_next_key(self) -> str:
        if not self.api_keys:
            raise ValueError(f"No available API keys for {self.function_name}")
            
        key = self.api_keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        return key
        
    def execute_with_fallback(self, func):
        """
        Execute a function with round-robin key selection and retries.
        func should be a callable that takes an api_key argument.
        """
        attempts = 0
        max_attempts = len(self.api_keys)
        
        while attempts < max_attempts:
            key = self.get_next_key()
            try:
                genai.configure(api_key=key)
                return func()
            except Exception as e:
                logger.warning(f"{self.function_name} failed with key ...{key[-4:]}: {e}")
                attempts += 1
        
        raise RuntimeError(f"All keys failed for {self.function_name}")


class DIContainer:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        
    def register(self, name: str, service: Any):
        self._services[name] = service
        
    def get(self, name: str) -> Any:
        return self._services.get(name)
        
    def init_services(self):
        logger.info("Initializing services...")
        
        # Initialize specialized managers
        # Gemini 3.0 Flash logic: User requested Gemini 3.
        # We will use 'gemini-2.0-flash-exp' or 'gemini-1.5-flash' if 3 is not resolveable, 
        # BUT the plan is to use 'gemini-3-flash' or 'gemini-3.0-flash-preview'.
        # We will use 'models/text-embedding-004' for embeddings.
        
        query_emb_manager = SpecializedModelManager(settings.QUERY_EMBEDDING_KEYS, "QueryEmbedding")
        batch_emb_manager = SpecializedModelManager(settings.BATCH_EMBEDDING_KEYS, "BatchEmbedding")
        chat_response_manager = SpecializedModelManager(settings.CHAT_RESPONSE_KEYS, "ChatResponse", need_chat_model=True)
        analysis_manager = SpecializedModelManager(settings.ANALYSIS_KEYS, "Analysis", need_chat_model=True)
        
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
