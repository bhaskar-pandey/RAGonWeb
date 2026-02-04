"""
Web Crawler Implementation
Uses Langchain's WebLoader for efficient content extraction.
"""
from typing import List, Tuple, Dict
from langchain_community.document_loaders import WebBaseLoader
from logger_config import get_logger

logger = get_logger(__name__)

class WebCrawler:
    """Web crawler using Langchain's WebLoader for content extraction."""

    def __init__(
        self,
        base_url: str,
        max_depth: int = 5, # Reserved for future recursive logic
        max_urls: int = 1000,
        timeout: int = 30,
        request_delay: float = 1.0,
        user_agent: str = None
    ):
        self.base_url = base_url
        self.max_urls = max_urls
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

        self.documents: List[Tuple[str, str]] = []
        self.failed_urls: List[str] = []

        logger.info(f"Initialized crawler for {base_url}")

    def crawl(self) -> List[Tuple[str, str]]:
        """Performs the crawl and returns processed content-url tuples."""
        logger.info(f"Starting crawl: {self.base_url}")

        try:
            loader = WebBaseLoader(
                web_paths=[self.base_url],
                requests_kwargs={"headers": {"User-Agent": self.user_agent}, "timeout": 30}
            )

            # Extract and process in a single pass
            raw_docs = loader.load()

            self.documents = [
                (doc.page_content[:5000], doc.metadata.get("source", self.base_url))
                for doc in raw_docs if doc.page_content.strip()
            ]

            logger.info(f"Successfully processed {len(self.documents)} documents.")

        except Exception as e:
            logger.error(f"Crawl failed for {self.base_url}: {e}")
            self.failed_urls.append(self.base_url)

        return self.documents

    def get_statistics(self) -> Dict:
        """Calculates crawl metrics."""
        doc_lengths = [len(doc[0]) for doc in self.documents]
        return {
            "visited_urls": len(self.documents),
            "failed_urls": len(self.failed_urls),
            "total_documents": len(self.documents),
            "avg_content_length": sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
        }