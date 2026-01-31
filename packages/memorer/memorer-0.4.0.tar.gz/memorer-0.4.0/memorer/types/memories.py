"""
Memory types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import MemorySource, PaginatedResponse


class Memory(BaseModel):
    """A memory in the system."""

    id: str
    content: str
    type: str
    category: str | None = None
    importance: float = 0.5
    source: MemorySource = MemorySource.DIRECT
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class DerivedMemory(Memory):
    """A memory derived from other memories."""

    derived_from: list[str] = Field(default_factory=list)
    derivation_reason: str | None = None


class MemoryList(PaginatedResponse):
    """A paginated list of memories."""

    memories: list[Memory] = Field(default_factory=list)

    def __iter__(self):
        """Iterate over memories."""
        return iter(self.memories)

    def __len__(self) -> int:
        """Number of memories in this page."""
        return len(self.memories)


class MemoryStats(BaseModel):
    """Memory statistics."""

    total_memories: int = 0
    direct_memories: int = 0
    derived_memories: int = 0
    relationships: int = 0


class Episode(BaseModel):
    """A temporal grouping of memories."""

    id: str
    start_time: datetime
    end_time: datetime
    entity_count: int = 0
    entity_ids: list[str] = Field(default_factory=list)
    summary: str | None = None
    created_at: datetime | None = None


class EpisodeList(PaginatedResponse):
    """A paginated list of episodes."""

    episodes: list[Episode] = Field(default_factory=list)

    def __iter__(self):
        """Iterate over episodes."""
        return iter(self.episodes)

    def __len__(self) -> int:
        """Number of episodes in this page."""
        return len(self.episodes)


class ConsolidationReport(BaseModel):
    """Report from memory consolidation."""

    status: str = "success"
    dry_run: bool = True
    entities_evaluated: int = 0
    entities_soft_deleted: int = 0
    entities_hard_deleted: int = 0
    memory_reduction_pct: float = 0.0
