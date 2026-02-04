"""
Configuration settings for RAG application.
Loads environment variables and provides configuration across the application.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Milvus Configuration
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_DB_NAME: str = "barco"
    MILVUS_COLLECTION_NAME: str = "web_data"

    # Web Crawler Configuration
    BASE_URL: str = "https://www.barco.com"
    CRAWL_MAX_DEPTH: int = 5
    CRAWL_MAX_URLS: int = 1000
    CRAWL_TIMEOUT: int = 30
    REQUEST_DELAY: float = 1.0
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    # Embeddings Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "RAG API - Barco Web Data"
    API_DESCRIPTION: str = "Retrieval Augmented Generation API for Barco website data"
    API_VERSION: str = "1.0.0"

    # Batch Processing
    BATCH_SIZE: int = 32
    GOOGLE_API_KEY: str
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
