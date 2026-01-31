"""Data models for Rail Engine SDK."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    """Data model for ingestion payload."""

    EventId: str
    EngineId: str
    ProjectId: str
    Body: str  # JSON stringified document
    CustomerKey: Optional[str] = None


class IngestionResponse(BaseModel):
    """Response from ingestion endpoint."""

    success: bool
    event_id: Optional[str] = None
    message: Optional[str] = None


class EmbeddingResponse(BaseModel):
    """Response model for embeddings."""

    EventId: str
    ProjectId: str
    EngineId: str
    CustomerKey: Optional[str] = None
    Embeddings: List[float]
    VectorStore: str
    EmbeddingsConfig: Dict[str, Any]


class StorageDocumentResponse(BaseModel):
    """Response model for storage documents."""

    EngineDocumentId: str
    EventId: str
    ProjectId: str
    EngineId: str
    CustomerKey: Optional[str] = None
    Content: str  # JSON stringified content
    Version: int
    DateCreated: datetime
    DateUpdated: Optional[datetime] = None


class PaginatedStorageResponse(BaseModel):
    """Paginated response for storage document queries."""

    Items: List[StorageDocumentResponse]
    PageNumber: int
    PageSize: int
    TotalCount: int
    TotalPages: int


class SearchSimilarRequest(BaseModel):
    """Request model for similar embeddings search."""

    VectorStore: str
    Query: Optional[str] = None
    Embedding: Optional[List[float]] = None
    Top: int = Field(default=10, ge=1, le=100)
    Threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class SearchSimilarResponse(BaseModel):
    """Response model for similar embeddings search."""

    Items: List[EmbeddingResponse]
    Count: int


class IndexingSearchRequest(BaseModel):
    """Request model for indexing search."""

    ProjectId: str
    EngineId: str
    Query: Dict[str, Any]


class IndexingSearchResponse(BaseModel):
    """Response model for indexing search."""

    Items: List[Dict[str, Any]]
    Count: int
