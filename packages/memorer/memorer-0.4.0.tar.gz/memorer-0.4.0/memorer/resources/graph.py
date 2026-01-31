"""
Graph operations resource - communities, duplicates, merge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from memorer.resources._base import BaseResource
from memorer.types import (
    DuplicatesResponse,
    GraphCommunity,
    MergeResponse,
)

if TYPE_CHECKING:
    from memorer._http import HTTPClient


class GraphResource(BaseResource):
    """
    Graph operations.

    Community detection, duplicate finding, and entity merging.

    Example:
        >>> communities = client.graph.communities()
        >>> for c in communities:
        ...     print(f"{c.label}: {c.entity_count} entities")
    """

    def communities(self, *, limit: int = 20) -> list[GraphCommunity]:
        """
        List detected communities in the knowledge graph.

        Communities are groups of related entities detected via graph algorithms.

        Args:
            limit: Maximum number to return (default: 20)

        Returns:
            List of GraphCommunity objects
        """
        response = self._get("/v1/knowledge/communities", params={"limit": limit})
        return [GraphCommunity(**c) for c in response.get("communities", [])]

    def detect_communities(self, *, resolution: float = 1.0) -> dict[str, Any]:
        """
        Run community detection on the knowledge graph.

        This is a background operation that groups related entities
        using the Louvain algorithm.

        Args:
            resolution: Resolution parameter (higher = more communities)

        Returns:
            Status response with message
        """
        return self._post(
            "/v1/knowledge/communities/detect",
            params={"resolution": resolution},
        )

    def find_duplicates(
        self,
        *,
        threshold: float = 0.90,
        limit: int = 50,
    ) -> DuplicatesResponse:
        """
        Find potential duplicate entities based on semantic similarity.

        Args:
            threshold: Similarity threshold (0.0-1.0, higher = more strict)
            limit: Maximum number of duplicate groups to return

        Returns:
            DuplicatesResponse with found duplicate groups

        Example:
            >>> dupes = client.graph.find_duplicates(threshold=0.95)
            >>> for group in dupes.groups:
            ...     print(f"Duplicates: {group.entity_ids}")
        """
        params: dict[str, Any] = {"threshold": threshold, "limit": limit}
        response = self._get("/v1/knowledge/deduplication/find-duplicates", params=params)
        return DuplicatesResponse(**response)

    def merge(
        self,
        keep_entity_id: str,
        merge_entity_id: str,
    ) -> MergeResponse:
        """
        Merge two duplicate entities.

        Keeps one entity and soft-deletes the other.
        Relationships are redirected to the kept entity.

        Args:
            keep_entity_id: ID of entity to keep
            merge_entity_id: ID of entity to merge (will be deleted)

        Returns:
            MergeResponse with merge details

        Example:
            >>> result = client.graph.merge(
            ...     keep_entity_id="uuid-to-keep",
            ...     merge_entity_id="uuid-to-merge"
            ... )
            >>> print(f"Redirected {result.relationships_redirected} relationships")
        """
        response = self._post(
            "/v1/knowledge/deduplication/merge",
            json_data={
                "keep_entity_id": keep_entity_id,
                "merge_entity_id": merge_entity_id,
            },
        )
        return MergeResponse(**response)
