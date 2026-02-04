"""
Embeddings Generation Module
Uses HuggingFace transformers to generate embeddings for text content.
"""
from typing import List, Union
from sentence_transformers import SentenceTransformer
from logger_config import get_logger

logger = get_logger(__name__)

class EmbeddingsGenerator:
    """Generates embeddings for text using HuggingFace SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Loading SentenceTransformer: {model_name}")
        try:
            self.model = SentenceTransformer(model_name)
            self.dim = self.model.get_sentence_embedding_dimension()
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def encode(self, text_input: Union[str, List[str]], batch_size: int = 32) -> Union[List[float], List[List[float]]]:
        """
        Encodes one or many strings into vectors.
        Returns a single list of floats if input is a string, or a list of lists if input is a list.
        """
        try:
            # convert_to_numpy=True is default; .tolist() handles both 1D and 2D arrays
            embeddings = self.model.encode(text_input, batch_size=batch_size)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise

    def encode_single(self, text: str) -> List[float]:
        """Kept for backward compatibility with search routes."""
        return self.encode(text)

    def get_embedding_dimension(self) -> int:
        return self.dim