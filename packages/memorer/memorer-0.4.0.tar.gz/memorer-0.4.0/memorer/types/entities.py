"""
Entity types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from .common import PaginatedResponse


class Entity(BaseModel):
    """An entity in the knowledge graph."""

    id: str
    content: str
    type: str
    category: str | None = None
    importance: float = 0.5
    community_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class EntityUpdate(BaseModel):
    """
    Fields to update on an entity (PATCH semantics).

    - Omit fields you don't want to update
    - At least one field must be provided
    - Explicit null values are rejected
    """

    content: str | None = None
    type: str | None = None
    category: str | None = None
    importance: float | None = None

    @model_validator(mode="before")
    @classmethod
    def validate_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        update_fields = ["content", "type", "category", "importance"]
        for field in update_fields:
            if field in data and data[field] is None:
                raise ValueError(f"'{field}' cannot be null. Omit the field instead.")
        if not any(k in data and data[k] is not None for k in update_fields):
            raise ValueError("At least one field must be provided for update")
        return data


class Relationship(BaseModel):
    """A relationship between two entities."""

    id: str
    source_id: str
    target_id: str
    relationship_type: str
    weight: float = 1.0
    created_at: datetime | None = None
    metadata: dict[str, Any] | None = None


class EntityRelationships(BaseModel):
    """An entity's relationships."""

    entity_id: str
    incoming: list[Relationship] = Field(default_factory=list)
    outgoing: list[Relationship] = Field(default_factory=list)


class EntityList(PaginatedResponse):
    """A paginated list of entities."""

    entities: list[Entity] = Field(default_factory=list)

    def __iter__(self):
        """Iterate over entities."""
        return iter(self.entities)

    def __len__(self) -> int:
        """Number of entities in this page."""
        return len(self.entities)


class RelationshipList(PaginatedResponse):
    """A paginated list of relationships."""

    relationships: list[Relationship] = Field(default_factory=list)

    def __iter__(self):
        """Iterate over relationships."""
        return iter(self.relationships)

    def __len__(self) -> int:
        """Number of relationships in this page."""
        return len(self.relationships)


class DuplicateGroup(BaseModel):
    """A group of potentially duplicate entities."""

    entity_ids: list[str] = Field(default_factory=list)
    similarity_score: float = 0.0
    suggested_merge_target: str | None = None


class DuplicatesResponse(BaseModel):
    """Response from duplicate detection."""

    groups: list[DuplicateGroup] = Field(default_factory=list)
    total_groups: int = 0


class MergeResponse(BaseModel):
    """Response from entity merge operation."""

    merged_into: str
    merged_count: int = 0
    relationships_redirected: int = 0
    status: str = "success"
