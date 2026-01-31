"""
Memory management resource.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from memorer.resources._base import BaseResource
from memorer.types import (
    ConsolidationReport,
    DerivedMemory,
    Episode,
    EpisodeList,
    Memory,
    MemoryList,
    MemoryStats,
)

if TYPE_CHECKING:
    from memorer._http import HTTPClient


class MemoriesResource(BaseResource):
    """
    Memory management operations.

    List, retrieve, and manage memories.

    Example:
        >>> memories = client.memories.list(category="work")
        >>> for m in memories:
        ...     print(f"{m.type}: {m.content}")
    """

    def list(
        self,
        *,
        owner_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        category: str | None = None,
        type: str | None = None,
    ) -> MemoryList:
        """
        List all memories.

        Args:
            owner_id: Filter by owner (optional)
            limit: Maximum number to return (default: 50)
            offset: Pagination offset
            category: Filter by category (personal, work, etc.)
            type: Filter by type (fact, concept, etc.)

        Returns:
            MemoryList with memories
        """
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        oid = owner_id or self._owner_id
        if oid:
            params["owner_id"] = oid
        if category:
            params["category"] = category
        if type:
            params["type"] = type

        response = self._get("/v1/memories", params=params)
        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryList(memories=memories)

    def direct(
        self,
        *,
        owner_id: str | None = None,
        limit: int = 50,
        category: str | None = None,
    ) -> MemoryList:
        """
        List direct memories (user-stated facts).

        Direct memories are high-confidence facts explicitly provided by the user.

        Args:
            owner_id: Filter by owner (optional)
            limit: Maximum number to return
            category: Filter by category

        Returns:
            MemoryList with direct memories
        """
        params: dict[str, str | int] = {"limit": limit}
        oid = owner_id or self._owner_id
        if oid:
            params["owner_id"] = oid
        if category:
            params["category"] = category

        response = self._get("/v1/memories/direct", params=params)
        memories = [Memory(**m) for m in response.get("memories", [])]
        return MemoryList(memories=memories)

    def derived(
        self,
        *,
        owner_id: str | None = None,
        limit: int = 50,
    ) -> MemoryList:
        """
        List derived memories (AI-synthesized insights).

        Derived memories are inferences made by combining multiple direct memories.

        Args:
            owner_id: Filter by owner (optional)
            limit: Maximum number to return

        Returns:
            MemoryList with derived memories including derivation info
        """
        params: dict[str, str | int] = {"limit": limit}
        oid = owner_id or self._owner_id
        if oid:
            params["owner_id"] = oid

        response = self._get("/v1/memories/derived", params=params)
        memories = [DerivedMemory(**m) for m in response.get("memories", [])]
        return MemoryList(memories=memories)

    def get(self, memory_id: str) -> Memory:
        """
        Get a specific memory by ID.

        Args:
            memory_id: UUID of the memory

        Returns:
            Memory object

        Raises:
            NotFoundError: If memory doesn't exist
        """
        response = self._get(f"/v1/memories/{memory_id}")
        if response.get("derived_from"):
            return DerivedMemory(**response)
        return Memory(**response)

    def delete(self, memory_id: str) -> None:
        """
        Delete a memory (soft delete).

        Args:
            memory_id: UUID of the memory

        Raises:
            NotFoundError: If memory doesn't exist
        """
        self._delete(f"/v1/memories/{memory_id}")

    def stats(self) -> MemoryStats:
        """
        Get memory statistics.

        Returns:
            MemoryStats with counts of total, direct, and derived memories
        """
        response = self._get("/v1/memories/stats/summary")
        return MemoryStats(**response)

    def episodes(
        self,
        *,
        owner_id: str | None = None,
        limit: int = 20,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> EpisodeList:
        """
        List temporal episodes (time-windowed memory groups).

        Args:
            owner_id: Filter by owner (optional)
            limit: Maximum number to return
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            EpisodeList with episodes
        """
        params: dict[str, str | int] = {"limit": limit}
        oid = owner_id or self._owner_id
        if oid:
            params["owner_id"] = oid
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()

        response = self._get("/v1/memories/episodes", params=params)
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return EpisodeList(episodes=episodes)

    def create_episode(self, entity_ids: list[str]) -> EpisodeList:
        """
        Create a new episode from a list of entity IDs.

        Args:
            entity_ids: List of entity UUIDs to group into episode(s)

        Returns:
            EpisodeList with created episodes
        """
        response = self._post(
            "/v1/memories/episodes/create",
            json_data={"entity_ids": entity_ids},
        )
        episodes = [Episode(**e) for e in response.get("episodes", [])]
        return EpisodeList(episodes=episodes)

    def consolidate(
        self,
        *,
        dry_run: bool = True,
        threshold_percentile: float = 30.0,
    ) -> ConsolidationReport:
        """
        Run adaptive forgetting on memories.

        This consolidation process:
        1. Computes importance scores (recency + centrality + frequency)
        2. Soft-deletes low-importance memories (below threshold)
        3. Hard-deletes memories soft-deleted >30 days ago

        Args:
            dry_run: If True, preview changes without making them (default: True)
            threshold_percentile: Percentile below which to soft-delete (default: 30.0)

        Returns:
            ConsolidationReport with consolidation results

        Example:
            >>> # Preview what would be deleted
            >>> report = client.memories.consolidate(dry_run=True)
            >>> print(f"Would delete {report.entities_soft_deleted} memories")
            >>>
            >>> # Actually run consolidation
            >>> report = client.memories.consolidate(dry_run=False)
            >>> print(f"Reduced memory by {report.memory_reduction_pct}%")
        """
        response = self._post(
            "/v1/memories/consolidate",
            params={
                "dry_run": dry_run,
                "threshold_percentile": threshold_percentile,
            },
        )
        return ConsolidationReport(**response)
