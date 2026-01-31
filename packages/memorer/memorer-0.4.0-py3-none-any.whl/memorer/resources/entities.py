"""
Entity CRUD resource.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from memorer.resources._base import BaseResource
from memorer.types import Entity, EntityList, EntityRelationships, EntityUpdate

if TYPE_CHECKING:
    from memorer._http import HTTPClient


class EntitiesResource(BaseResource):
    """
    Entity CRUD operations.

    List, create, update, and delete entities in the knowledge graph.

    Example:
        >>> entities = client.entities.list(type="person")
        >>> for e in entities:
        ...     print(f"{e.content} (importance: {e.importance})")
    """

    def list(
        self,
        *,
        owner_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        type: str | None = None,
    ) -> EntityList:
        """
        List entities in the knowledge graph.

        Args:
            owner_id: Filter by owner (optional)
            limit: Maximum number to return (default: 100)
            offset: Pagination offset
            type: Filter by entity type

        Returns:
            EntityList with entities
        """
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        oid = owner_id or self._owner_id
        if oid:
            params["owner_id"] = oid
        if type:
            params["type"] = type

        response = self._get("/v1/knowledge/entities", params=params)
        entities = [Entity(**e) for e in response.get("entities", [])]
        return EntityList(entities=entities)

    def get(self, entity_id: str) -> Entity:
        """
        Get a single entity by ID.

        Args:
            entity_id: UUID of the entity

        Returns:
            Entity object

        Raises:
            NotFoundError: If entity doesn't exist
        """
        response = self._get(f"/v1/knowledge/entities/{entity_id}")
        return Entity(**response)

    def update(self, entity_id: str, updates: EntityUpdate) -> Entity:
        """
        Update an entity.

        Args:
            entity_id: UUID of the entity
            updates: Fields to update (at least one required)

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity doesn't exist
            ValueError: If no fields provided in updates

        Example:
            >>> from memorer.types import EntityUpdate
            >>> entity = client.entities.update(
            ...     "entity-uuid",
            ...     EntityUpdate(importance=0.9)
            ... )
        """
        data = updates.model_dump(exclude_none=True)
        response = self._put(f"/v1/knowledge/entities/{entity_id}", json_data=data)
        return Entity(**response)

    def delete(self, entity_id: str) -> None:
        """
        Delete an entity (soft delete).

        Args:
            entity_id: UUID of the entity

        Raises:
            NotFoundError: If entity doesn't exist
        """
        self._delete(f"/v1/knowledge/entities/{entity_id}")

    def relationships(self, entity_id: str) -> EntityRelationships:
        """
        Get all relationships for an entity.

        Args:
            entity_id: UUID of the entity

        Returns:
            EntityRelationships with incoming and outgoing relationships

        Raises:
            NotFoundError: If entity doesn't exist

        Example:
            >>> rels = client.entities.relationships("entity-uuid")
            >>> print(f"Outgoing: {len(rels.outgoing)}")
            >>> print(f"Incoming: {len(rels.incoming)}")
        """
        response = self._get(f"/v1/knowledge/entities/{entity_id}/relationships")
        return EntityRelationships(**response)
