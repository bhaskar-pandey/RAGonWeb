from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
from src.crawler import WebCrawler
from src.embeddings import EmbeddingsGenerator
from src.database import MilvusClient
from config import settings
from logger_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/ingest", responses={404: {"description": "Not found"}})

# --- Models ---

class IngestRequest(BaseModel):
    base_url: Optional[str] = settings.BASE_URL
    max_depth: Optional[int] = settings.CRAWL_MAX_DEPTH
    max_urls: Optional[int] = settings.CRAWL_MAX_URLS
    chunk_size: Optional[int] = 1000

class IngestResponse(BaseModel):
    status: str
    message: str
    task_id: str

# --- Logic Helpers ---

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    if not text: return []
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

def prepare_documents(raw_docs: List[Tuple[str, str]], base_url: str, chunk_size: int) -> List[Dict]:
    """Flattens raw docs into a list of chunked document dictionaries."""
    prepared = []
    for content, url in raw_docs:
        chunks = chunk_text(content, chunk_size)
        prepared.extend([
            {"content": c, "content_url": url, "chunk_index": i, "source_base": base_url}
            for i, c in enumerate(chunks)
        ])
    return prepared

# --- Core Task ---

def process_ingestion(base_url: str, max_depth: int, max_urls: int, chunk_size: int):
    client = None
    try:
        logger.info(f"Starting ingestion: {base_url}")

        # 1. Crawl
        crawler = WebCrawler(
            base_url=base_url, max_depth=max_depth, max_urls=max_urls,
            timeout=settings.CRAWL_TIMEOUT, request_delay=settings.REQUEST_DELAY,
            user_agent=settings.USER_AGENT
        )
        raw_docs = crawler.crawl()
        if not raw_docs: return logger.warning("No documents found.")

        # 2. Prepare & Chunk all data
        all_docs = prepare_documents(raw_docs, base_url, chunk_size)

        # 3. Process & Embed in batches
        embedder = EmbeddingsGenerator(model_name=settings.EMBEDDING_MODEL)
        client = MilvusClient()

        batch_size = 50
        for i in range(0, len(all_docs), batch_size):
            batch = all_docs[i : i + batch_size]
            contents = [d["content"] for d in batch]

            vectors = embedder.encode(contents, batch_size=settings.BATCH_SIZE)

            for doc, vec in zip(batch, vectors):
                doc["content_vector"] = vec

            client.insert_documents(batch)
            logger.info(f"Indexed batch {(i//batch_size)+1}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
    finally:
        if client: client.close()

# --- Routes ---

@router.post("", response_model=IngestResponse)
async def ingest_documents(req: IngestRequest, bg_tasks: BackgroundTasks):
    bg_tasks.add_task(process_ingestion, req.base_url, req.max_depth, req.max_urls, req.chunk_size)
    return IngestResponse(
        status="accepted",
        message="Ingestion started.",
        task_id=f"ingest_{req.base_url}"
    )