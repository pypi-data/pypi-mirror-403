"""
Common types shared across the SDK.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Scope(str, Enum):
    """Memory scope levels."""

    USER = "user"
    PROJECT = "project"
    ORGANIZATION = "organization"


class MemorySource(str, Enum):
    """Source of a memory."""

    DIRECT = "direct"
    DERIVED = "derived"
    INFERRED = "inferred"


class RetrievalPath(str, Enum):
    """How results were retrieved."""

    CACHE = "cache"
    GRAPH = "graph"
    VECTOR = "vector"
    HYBRID = "hybrid"
    UNIFIED = "unified"


class TimingBreakdown(BaseModel):
    """Detailed timing information for a query."""

    embedding_ms: float = 0.0
    cache_check_ms: float = 0.0
    complexity_routing_ms: float = 0.0
    hybrid_search_ms: float = 0.0
    reranking_ms: float = 0.0
    community_enrichment_ms: float = 0.0
    graph_reasoning_ms: float = 0.0
    context_assembly_ms: float = 0.0
    total_ms: float = 0.0


class Pagination(BaseModel):
    """Pagination information."""

    total: int = 0
    limit: int = 50
    offset: int = 0
    has_next: bool = False


class PaginatedResponse(BaseModel):
    """Base class for paginated responses."""

    pagination: Pagination = Field(default_factory=Pagination)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()


class HealthStatus(BaseModel):
    """API health status."""

    status: str
    version: str | None = None
    environment: str | None = None
