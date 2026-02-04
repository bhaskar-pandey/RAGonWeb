"""
Health Check Routes
"""
from fastapi import APIRouter, HTTPException
from src.database import MilvusClient
from logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/health", responses={404: {"description": "Not found"}})


@router.get("")
async def health_check():
    """Check API and database health status."""
    try:
        # Try to connect to Milvus
        milvus_client = MilvusClient()
        stats = milvus_client.get_collection_stats()
        milvus_client.close()

        return {
            "status": "healthy",
            "database": "operational",
            "collection_stats": stats,
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {str(e)}"
        )
