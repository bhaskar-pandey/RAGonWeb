"""
Data Models for Database Operations
"""
from typing import List
from pydantic import BaseModel, Field


class DocumentData(BaseModel):
    """Schema for document data to be stored in Milvus."""
    content: str = Field(..., description="Document content text")
    content_vector: List[float] = Field(..., description="Embedding vector of content")
    content_url: str = Field(..., description="Source URL of the document")


class SearchResult(BaseModel):
    """Schema for search results."""
    content: str
    content_url: str
    distance: float = Field(..., description="Similarity distance score")
    similarity_score: float = Field(
        ...,
        description="Similarity score (0-1, higher is more similar)"
    )


class SearchQuery(BaseModel):
    """Schema for search queries."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")


class SearchResponse(BaseModel):
    """Response model for search endpoint including the LLM-generated answer and the list of raw results."""
    answer: str = Field(..., description="LLM generated answer to the query based on retrieved documents")
    results: List[SearchResult] = Field(..., description="List of individual search results used as context for the answer")
