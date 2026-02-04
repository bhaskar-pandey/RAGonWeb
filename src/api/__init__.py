"""
API Module
FastAPI application and route handlers.
"""
from .app import create_app
from .routes import health, ingest, search

__all__ = ["create_app"]
