"""
Search Routes
Handles semantic search and RAG generation with optimized memory management.
"""
import os
from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Depends

from src.embeddings import EmbeddingsGenerator
from src.database import MilvusClient, models
from src.llm.gemini_client import GeminiClient
from config import settings
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/search", responses={404: {"description": "Not found"}})

# --- Dependency Injection ---

_embedder = None

def get_embedder() -> EmbeddingsGenerator:
    """Singleton pattern for the embedding model to save RAM."""
    global _embedder
    if _embedder is None:
        _embedder = EmbeddingsGenerator()
    return _embedder

# --- Helper Logic ---

def build_rag_prompt(query: str, search_results: List[models.SearchResult]) -> str:
    """Constructs the prompt by joining retrieved document snippets."""
    context_parts = [
        f"SOURCE: {r.content_url}\nCONTENT: {r.content[:1000]}"
        for r in search_results
    ]
    context_text = "\n\n".join(context_parts)
    return (
        f"You are a helpful assistant. Use the context below to answer.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

# --- Routes ---

@router.post("", response_model=models.SearchResponse)
def search_documents(
    request: models.SearchQuery,
    embedder: Annotated[EmbeddingsGenerator, Depends(get_embedder)]
) -> models.SearchResponse:
    """
    Executes semantic search and generates an answer using RAG.
    Runs in a thread pool (sync def) to handle blocking AI/DB calls efficiently.
    """
    db = MilvusClient()
    try:
        # 1. Semantic Search
        logger.info(f"Querying: {request.query}")
        vector = embedder.encode_single(request.query)
        hits = db.search(query_vector=vector, top_k=request.top_k)

        # 2. Map Results
        results = [
            models.SearchResult(
                content=h["content"],
                content_url=h["content_url"],
                distance=h.get("distance", 0.0),
                similarity_score=h.get("similarity_score", 0.0)
            ) for h in hits
        ]

        if not results:
            return models.SearchResponse(answer="No relevant context found.", results=[])

        # 3. Generate RAG Answer
        prompt = build_rag_prompt(request.query, results)
        api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY

        try:
            answer = GeminiClient(api_key=api_key).generate(prompt=prompt)
        except Exception as e:
            logger.error(f"LLM Failure: {e}")
            answer = "The search found relevant documents, but the AI failed to generate a summary."

        return models.SearchResponse(answer=answer, results=results)

    except Exception as e:
        logger.error(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal search failure.")
    finally:
        db.close()