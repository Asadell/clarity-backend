import google.generativeai as genai
from ..core.logger import get_logger

logger = get_logger(__name__)

class EmbeddingService:
    def __init__(self, query_emb_manager, batch_emb_manager):
        self.query_emb_manager = query_emb_manager
        self.batch_emb_manager = batch_emb_manager
        # Using gemini-embedding-001 as requested (3072 dims)
        self.model_name = "models/gemini-embedding-001" 

    async def generate_query_embedding(self, text: str) -> list[float]:
        def _call_api():
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="RETRIEVAL_QUERY"
            )
            return result['embedding']

        return self.query_emb_manager.execute_with_fallback(_call_api)

    async def generate_batch_embedding(self, texts: list[str]) -> list[list[float]]:
        # Gemini API supports batch embedding, but python lib might need loop or specific batch method
        # The 'embed_content' can take a list of contents? No, usually single or specific batch method.
        # genai.embed_content actually returns a Dict.
        # For batch, better to loop or check library support.
        # To be safe and maximize success rate with round robin, loop might be better or small batches.
        # We will implement simple loop for now to use the manager's fallback per item or per batch.
        
        embeddings = []
        for text in texts:
            def _call_api():
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                return result['embedding']
            
            emb = self.batch_emb_manager.execute_with_fallback(_call_api)
            embeddings.append(emb)
            
        return embeddings
