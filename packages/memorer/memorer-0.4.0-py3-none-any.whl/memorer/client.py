"""
Memorer SDK Client

Main client classes for interacting with the Memorer API.
"""

from __future__ import annotations

from typing import Any

from memorer._config import ClientConfig
from memorer._http import HTTPClient
from memorer.resources import (
    EntitiesResource,
    GraphResource,
    KnowledgeResource,
    MemoriesResource,
)
from memorer.types import ConsolidationReport, Document, HealthStatus, IngestResponse, QueryResponse


class UserClient:
    """
    A scoped client for a specific end-user.

    All operations on this client are automatically scoped to the user.
    This is the recommended way to handle multi-tenancy.

    Example:
        >>> client = Memorer(api_key="mem_sk_...")
        >>> user = client.for_user("end-user-123")
        >>> user.remember("User likes coffee")
        >>> results = user.recall("preferences")
    """

    def __init__(self, http: HTTPClient, owner_id: str) -> None:
        self._http = http
        self._owner_id = owner_id

        self.knowledge = KnowledgeResource(http, owner_id=owner_id)
        self.memories = MemoriesResource(http, owner_id=owner_id)
        self.entities = EntitiesResource(http, owner_id=owner_id)

    @property
    def owner_id(self) -> str:
        """The user ID this client is scoped to."""
        return self._owner_id

    def remember(
        self,
        content: str | dict[str, Any] | Document | list[str | dict[str, Any] | Document],
    ) -> IngestResponse:
        """
        Remember something - ingest content into memory.

        Args:
            content: What to remember. Can be:
                - A string
                - A dict with 'content' key
                - A Document object
                - A list of any of the above

        Returns:
            IngestResponse with counts of created items

        Example:
            >>> user.remember("User prefers dark mode")
            >>> user.remember(["First memory", "Second memory"])
        """
        return self.knowledge.ingest(content)

    def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        use_emotional_ranking: bool = True,
        use_graph_reasoning: bool = False,
        graph_max_hops: int = 3,
    ) -> QueryResponse:
        """
        Recall knowledge - query the memory.

        Args:
            query: What to recall
            top_k: Number of results (default: 10)
            use_emotional_ranking: Apply emotional scoring (default: True)
            use_graph_reasoning: Enable multi-hop traversal (default: False)
            graph_max_hops: Maximum traversal depth (default: 3)

        Returns:
            QueryResponse with results and assembled context

        Example:
            >>> results = user.recall("what are user preferences?")
            >>> print(results.context)
        """
        return self.knowledge.query(
            query,
            top_k=top_k,
            use_emotional_ranking=use_emotional_ranking,
            use_graph_reasoning=use_graph_reasoning,
            graph_max_hops=graph_max_hops,
        )

    def forget(self, memory_id: str) -> None:
        """
        Forget a memory (soft delete).

        Args:
            memory_id: UUID of the memory to forget
        """
        self.memories.delete(memory_id)


class Memorer:
    """
    Memorer SDK Client.

    The main entry point for interacting with the Memorer API.

    Example:
        >>> from memorer import Memorer, Document
        >>>
        >>> client = Memorer(api_key="mem_sk_...")
        >>> user = client.for_user("end-user-123")
        >>>
        >>> # Remember
        >>> user.remember("User prefers dark mode")
        >>>
        >>> # Recall
        >>> results = user.recall("what are user preferences?")
        >>> print(results.context)

    Attributes:
        knowledge: Knowledge graph operations (query, ingest, stats)
        entities: Entity CRUD operations
        memories: Memory management operations
        graph: Graph operations (communities, duplicates, merge)
    """

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        """
        Initialize the Memorer client.

        Args:
            api_key: Your Memorer API key (required).
            timeout: Request timeout in seconds (default: 30)
            max_retries: Max retries for transient failures (default: 2)

        Example:
            >>> client = Memorer(api_key="mem_sk_...")
        """
        self._config = ClientConfig(
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries,
        )

        self._http = HTTPClient(self._config)

        self.knowledge = KnowledgeResource(self._http)
        self.entities = EntitiesResource(self._http)
        self.memories = MemoriesResource(self._http)
        self.graph = GraphResource(self._http)

    def for_user(self, owner_id: str) -> UserClient:
        """
        Create a scoped client for a specific end-user.

        This is the recommended way to handle multi-tenancy. All operations
        on the returned client are automatically scoped to the user.

        Args:
            owner_id: Unique identifier for the end-user

        Returns:
            UserClient scoped to the specified user

        Example:
            >>> user = client.for_user("end-user-123")
            >>> user.remember("User likes coffee")
            >>> results = user.recall("preferences")
        """
        return UserClient(self._http, owner_id)

    def consolidate(self, *, dry_run: bool = True, threshold_percentile: float = 30.0) -> ConsolidationReport:
        """
        Run adaptive forgetting to consolidate memories.

        Args:
            dry_run: Preview changes without making them (default: True)
            threshold_percentile: Percentile below which to soft-delete

        Returns:
            ConsolidationReport with consolidation results
        """
        return self.memories.consolidate(dry_run=dry_run, threshold_percentile=threshold_percentile)

    def health(self) -> HealthStatus:
        """Check API health status."""
        response = self._http.get("/health")
        return HealthStatus(**response)

    def close(self) -> None:
        """Close the client and release resources."""
        self._http.close()

    def __enter__(self) -> Memorer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
