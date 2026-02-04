"""
Main Entry Point
Run the FastAPI server or CLI operations.
"""
from src.api import create_app
from config import settings
from logger_config import get_logger
import uvicorn

logger = get_logger(__name__)


def run_server():
    """Run FastAPI server."""
    logger.info("Starting FastAPI server")
    app = create_app()

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
