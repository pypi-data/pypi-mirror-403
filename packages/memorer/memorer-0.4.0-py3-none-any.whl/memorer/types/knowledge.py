"""
Knowledge graph types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .common import RetrievalPath, TimingBreakdown

QueryComplexity = Literal["simple", "medium", "complex"]


class Document(BaseModel):
    """A document to ingest into the knowledge graph."""

    content: str
    id: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, str] | None = None


class ReasoningStep(BaseModel):
    """A single step in a reasoning chain."""

    entity_id: str
    entity_name: str
    entity_type: str
    relationship: str | None = None
    confidence: float = 1.0
    pagerank_score: float | None = None


class ReasoningChain(BaseModel):
    """A multi-hop reasoning chain through the knowledge graph."""

    steps: list[ReasoningStep] = Field(default_factory=list)
    total_confidence: float = 1.0
    path_description: str | None = None


class Citation(BaseModel):
    """A citation to a source entity."""

    entity_id: str
    entity_name: str
    entity_type: str
    relevance_score: float = 1.0


class QueryResult(BaseModel):
    """A single result from a knowledge query."""

    id: str
    content: str
    type: str
    category: str | None = None
    importance: float = 0.5
    relevance_score: float = 0.0
    emotional_valence: float | None = None
    emotional_intensity: float | None = None
    community_id: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class QueryResponse(BaseModel):
    """Response from a knowledge query."""

    results: list[QueryResult] = Field(default_factory=list)
    context: str = ""
    query_complexity: str = "simple"
    cache_hit: bool = False
    result_count: int = 0
    reasoning_chains: list[ReasoningChain] | None = None
    citations: list[Citation] | None = None
    retrieval_path: RetrievalPath | None = None
    timing: TimingBreakdown | None = None

    def __iter__(self):
        """Iterate over results."""
        return iter(self.results)

    def __len__(self) -> int:
        """Number of results."""
        return len(self.results)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()


class IngestResponse(BaseModel):
    """Response from document ingestion."""

    entities_created: int = 0
    relationships_created: int = 0
    episodes_created: int = 0
    processing_time_ms: int = 0
    status: str = "success"


class KnowledgeStats(BaseModel):
    """Knowledge graph statistics."""

    total_entities: int = 0
    total_relationships: int = 0
    total_episodes: int = 0
    total_communities: int = 0
    cache_size: int = 0
    avg_importance: float = 0.0


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str
    label: str
    type: str
    importance: float = 0.5
    community_id: str | None = None
    metadata: dict[str, Any] | None = None


class GraphEdge(BaseModel):
    """An edge in the knowledge graph."""

    source: str
    target: str
    relationship: str
    weight: float = 1.0


class GraphCommunity(BaseModel):
    """A detected community in the knowledge graph."""

    id: str
    label: str
    summary: str | None = None
    entity_count: int = 0
    entity_ids: list[str] = Field(default_factory=list)


class GraphVisualization(BaseModel):
    """Full graph data for visualization."""

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    communities: list[GraphCommunity] = Field(default_factory=list)
    stats: KnowledgeStats | None = None
