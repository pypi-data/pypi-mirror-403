"""
Knowledge graph resource for queries and ingestion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from memorer.resources._base import BaseResource
from memorer.types import (
    Document,
    GraphCommunity,
    GraphEdge,
    GraphNode,
    GraphVisualization,
    IngestResponse,
    KnowledgeStats,
    QueryComplexity,
    QueryResponse,
    QueryResult,
    ReasoningChain,
    RelationshipList,
    TimingBreakdown,
)
from memorer.types.entities import Relationship

if TYPE_CHECKING:
    from memorer._http import HTTPClient


def _normalize_documents(
    documents: list[str] | list[dict[str, Any]] | list[Document],
) -> list[dict[str, Any]]:
    """Normalize document input to list of dicts."""
    result: list[dict[str, Any]] = []
    for doc in documents:
        if isinstance(doc, str):
            result.append({"content": doc})
        elif isinstance(doc, Document):
            result.append(doc.model_dump(exclude_none=True))
        else:
            result.append(doc)
    return result


def _parse_query_response(response: dict[str, Any]) -> QueryResponse:
    """Parse raw response into QueryResponse."""
    results = [QueryResult(**r) for r in response.get("results", [])]

    reasoning_chains = None
    if response.get("reasoning_chains"):
        reasoning_chains = [ReasoningChain(**c) for c in response["reasoning_chains"]]

    timing = None
    if response.get("timing"):
        timing = TimingBreakdown(**response["timing"])

    return QueryResponse(
        results=results,
        context=response.get("context", ""),
        query_complexity=response.get("query_complexity", "simple"),
        cache_hit=response.get("cache_hit", False),
        result_count=response.get("result_count", len(results)),
        reasoning_chains=reasoning_chains,
        timing=timing,
    )


class KnowledgeResource(BaseResource):
    """
    Knowledge graph operations.

    Query, ingest, and manage the knowledge graph.

    Example:
        >>> results = client.knowledge.query("what are user preferences?")
        >>> print(results.context)
        >>> for r in results:
        ...     print(f"{r.content} (score: {r.relevance_score})")
    """

    def query(
        self,
        query: str,
        *,
        top_k: int = 10,
        use_cache: bool = True,
        use_rerank: bool = True,
        use_emotional_ranking: bool = True,
        use_graph_reasoning: bool = False,
        graph_max_hops: int = 3,
        graph_beam_width: int = 5,
        include_community_context: bool = False,
        filter_by_community_id: str | None = None,
        complexity_override: QueryComplexity | None = None,
    ) -> QueryResponse:
        """
        Query the knowledge graph.

        Requires using client.for_user() to scope to an owner.

        Args:
            query: The search query
            top_k: Number of results to return (default: 10)
            use_cache: Enable semantic cache (default: True)
            use_rerank: Enable cross-encoder reranking (default: True)
            use_emotional_ranking: Apply emotional scoring (default: True)
            use_graph_reasoning: Enable multi-hop graph traversal (default: False)
            graph_max_hops: Maximum traversal depth (default: 3)
            graph_beam_width: Beam search width (default: 5)
            include_community_context: Enrich with community data (default: False)
            filter_by_community_id: Filter by specific community
            complexity_override: Override complexity classification ("simple", "medium", or "complex")

        Returns:
            QueryResponse with results, context, and metadata

        Raises:
            ValueError: If not using a scoped client (client.for_user())

        Example:
            >>> user = client.for_user("user-123")
            >>> results = user.knowledge.query(
            ...     "what does the user prefer?",
            ...     use_graph_reasoning=True,
            ... )
            >>> print(results.context)  # Assembled context for LLM
        """
        if not self._owner_id:
            raise ValueError(
                "owner_id is required. Use client.for_user(owner_id) to create a scoped client."
            )

        data: dict[str, Any] = {
            "query": query,
            "owner_id": self._owner_id,
            "top_k": top_k,
            "use_cache": use_cache,
            "use_rerank": use_rerank,
            "use_emotional_ranking": use_emotional_ranking,
            "use_graph_reasoning": use_graph_reasoning,
            "graph_max_hops": graph_max_hops,
            "graph_beam_width": graph_beam_width,
            "include_community_context": include_community_context,
        }
        if filter_by_community_id:
            data["filter_by_community_id"] = filter_by_community_id
        if complexity_override:
            data["complexity_override"] = complexity_override

        response = self._post("/v1/knowledge/query", json_data=data)
        return _parse_query_response(response)

    def ingest(
        self,
        documents: str | dict[str, Any] | Document | list[str | dict[str, Any] | Document],
    ) -> IngestResponse:
        """
        Ingest documents into the knowledge graph.

        Entity and relationship extraction is handled automatically.
        Requires using client.for_user() to scope to an owner.

        Args:
            documents: Content to ingest. Can be:
                - A string
                - A dict with 'content' key
                - A Document object
                - A list of any of the above

        Returns:
            IngestResponse with counts of created items

        Raises:
            ValueError: If not using a scoped client (client.for_user())

        Example:
            >>> user = client.for_user("user-123")
            >>> user.knowledge.ingest([
            ...     "User prefers dark mode",
            ...     "Meeting scheduled for Friday",
            ... ])
        """
        if not self._owner_id:
            raise ValueError(
                "owner_id is required. Use client.for_user(owner_id) to create a scoped client."
            )

        if isinstance(documents, (str, dict, Document)):
            doc_list: list[Any] = [documents]
        else:
            doc_list = list(documents)

        normalized = _normalize_documents(doc_list)

        data: dict[str, Any] = {
            "documents": normalized,
            "owner_id": self._owner_id,
            "extraction_config": {
                "extract_entities": True,
            },
        }

        response = self._post("/v1/knowledge/ingest", json_data=data)
        return IngestResponse(**response)

    def relationships(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> RelationshipList:
        """
        List relationships in the knowledge graph.

        Args:
            limit: Maximum number to return (default: 100)
            offset: Pagination offset

        Returns:
            RelationshipList with relationships
        """
        params: dict[str, int] = {"limit": limit, "offset": offset}
        response = self._get("/v1/knowledge/relationships", params=params)
        relationships = [Relationship(**r) for r in response.get("relationships", [])]
        return RelationshipList(relationships=relationships)

    def graph(
        self,
        *,
        limit: int = 500,
        include_embeddings: bool = False,
    ) -> GraphVisualization:
        """
        Get full graph data for visualization.

        Compatible with D3.js, vis.js, Cytoscape, etc.

        Args:
            limit: Maximum number of nodes (default: 500)
            include_embeddings: Include embedding vectors (default: False)

        Returns:
            GraphVisualization with nodes, edges, and communities
        """
        params: dict[str, Any] = {"limit": limit, "include_embeddings": include_embeddings}
        response = self._get("/v1/knowledge/graph", params=params)

        nodes = [GraphNode(**n) for n in response.get("nodes", [])]
        edges = [GraphEdge(**e) for e in response.get("edges", [])]
        communities = [GraphCommunity(**c) for c in response.get("communities", [])]

        stats = None
        if response.get("stats"):
            stats = KnowledgeStats(**response["stats"])

        return GraphVisualization(
            nodes=nodes,
            edges=edges,
            communities=communities,
            stats=stats,
        )
