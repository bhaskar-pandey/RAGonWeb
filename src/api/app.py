"""
FastAPI Application Factory
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from .routes import health, ingest, search
from ..embeddings import EmbeddingsGenerator


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    embedder = EmbeddingsGenerator(model_name=settings.EMBEDDING_MODEL)

    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(ingest.router, tags=["ingest"])
    app.include_router(search.router, tags=["search"])


    return app
