"""
Memorer SDK

Python SDK for Memorer - Intelligent Memory for AI Agents.

Quick Start:
    >>> from memorer import Memorer, Document
    >>>
    >>> client = Memorer(api_key="mem_sk_...")
    >>> user = client.for_user("end-user-123")
    >>>
    >>> # Remember
    >>> user.remember("User prefers dark mode")
    >>>
    >>> # Recall
    >>> results = user.recall("preferences")
    >>> print(results.context)

Full API Access:
    >>> client = Memorer(api_key="mem_sk_...")
    >>> entities = client.entities.list(type="person")
    >>> for e in entities:
    ...     print(f"{e.content} (importance: {e.importance})")
"""

from memorer.client import Memorer, UserClient
from memorer.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    MemorerError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    StreamingError,
    ValidationError,
)
from memorer.types import (
    Citation,
    ConsolidationReport,
    DerivedMemory,
    Document,
    DuplicateGroup,
    DuplicatesResponse,
    Entity,
    EntityList,
    EntityRelationships,
    EntityUpdate,
    Episode,
    EpisodeList,
    GraphCommunity,
    GraphEdge,
    GraphNode,
    GraphVisualization,
    HealthStatus,
    IngestResponse,
    KnowledgeStats,
    Memory,
    MemoryList,
    MemorySource,
    MemoryStats,
    MergeResponse,
    PaginatedResponse,
    Pagination,
    QueryResponse,
    QueryResult,
    ReasoningChain,
    ReasoningStep,
    Relationship,
    RelationshipList,
    RetrievalPath,
    Scope,
    TimingBreakdown,
)

__version__ = "0.4.0"

__all__ = [
    # Clients
    "Memorer",
    "UserClient",
    # Errors
    "MemorerError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "StreamingError",
    # Common types
    "HealthStatus",
    "MemorySource",
    "Pagination",
    "PaginatedResponse",
    "RetrievalPath",
    "Scope",
    "TimingBreakdown",
    # Knowledge types
    "Citation",
    "Document",
    "GraphCommunity",
    "GraphEdge",
    "GraphNode",
    "GraphVisualization",
    "IngestResponse",
    "KnowledgeStats",
    "QueryResponse",
    "QueryResult",
    "ReasoningChain",
    "ReasoningStep",
    # Memory types
    "ConsolidationReport",
    "DerivedMemory",
    "Episode",
    "EpisodeList",
    "Memory",
    "MemoryList",
    "MemoryStats",
    # Entity types
    "DuplicateGroup",
    "DuplicatesResponse",
    "Entity",
    "EntityList",
    "EntityRelationships",
    "EntityUpdate",
    "MergeResponse",
    "Relationship",
    "RelationshipList",
]
