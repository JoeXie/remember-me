"""Memory manager - orchestrates storage and embedding operations."""

import logging
from dataclasses import dataclass
from typing import Any

from qdrant_client.http.exceptions import UnexpectedResponse

from ..config import get_config
from ..memory_store import MemoryStore, get_memory_store
from .exceptions import NotFoundError, QdrantOfflineError, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class StatusInfo:
    """System status information."""
    collection: str
    count: int
    host: str
    port: int
    connected: bool


class MemoryManager:
    """High-level memory management interface.

    Wraps MemoryStore with Pydantic-like validation, error translation,
    and consistent logging.
    """

    def __init__(self, store: MemoryStore | None = None):
        self._store = store
        self._config = get_config()

    @property
    def store(self) -> MemoryStore:
        """Lazy initialization of MemoryStore."""
        if self._store is None:
            self._store = get_memory_store()
        return self._store

    def add_memory(
        self,
        text: str,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a new memory.

        Args:
            text: Memory content text
            user_id: User identifier (uses DEFAULT_USER_ID if not provided)
            agent_id: Agent/session identifier

        Returns:
            Memory dict with id, data, userId, hash, createdAt, runId

        Raises:
            ValidationError: If text is empty
            QdrantOfflineError: If Qdrant is unreachable
        """
        if not text or not text.strip():
            raise ValidationError("Memory text cannot be empty")

        try:
            memory = self.store.add_memory(
                text=text,
                user_id=user_id,
                agent_id=agent_id,
            )
            logger.info(f"Memory added: {memory.id}")
            return memory.to_dict()
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def search_memories(
        self,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search memories by semantic similarity.

        Args:
            query: Search query text
            user_id: User identifier (uses DEFAULT_USER_ID if not provided)
            agent_id: Filter by agent/session
            limit: Maximum results to return (default 5)

        Returns:
            SearchResult dict with results list and count

        Raises:
            ValidationError: If query is empty or limit out of range
            QdrantOfflineError: If Qdrant is unreachable
        """
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100")

        try:
            result = self.store.search_memories(
                query=query,
                user_id=user_id,
                agent_id=agent_id,
                limit=limit,
            )
            logger.info(f"Search '{query[:30]}...' returned {result.count} results")
            return result.to_dict()
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def get_memory(self, memory_id: str) -> dict[str, Any] | None:
        """Get a memory by ID.

        Args:
            memory_id: Memory UUID

        Returns:
            Memory dict or None if not found

        Raises:
            QdrantOfflineError: If Qdrant is unreachable
        """
        try:
            memory = self.store.get_memory(memory_id)
            if memory is None:
                return None
            return memory.to_dict()
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def update_memory(
        self,
        memory_id: str,
        text: str,
    ) -> dict[str, Any] | None:
        """Update memory content.

        Args:
            memory_id: Memory UUID
            text: New memory content

        Returns:
            Updated memory dict or None if not found

        Raises:
            ValidationError: If text is empty
            QdrantOfflineError: If Qdrant is unreachable
        """
        if not text or not text.strip():
            raise ValidationError("Memory text cannot be empty")

        try:
            memory = self.store.update_memory(memory_id, text=text)
            if memory is None:
                return None
            logger.info(f"Memory updated: {memory.id}")
            return memory.to_dict()
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID.

        Args:
            memory_id: Memory UUID

        Returns:
            True if deleted, False if not found

        Raises:
            QdrantOfflineError: If Qdrant is unreachable
        """
        try:
            result = self.store.delete_memory(memory_id)
            if result:
                logger.info(f"Memory deleted: {memory_id}")
            return result
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def delete_all_memories(
        self,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> int:
        """Delete all memories for a user.

        Args:
            user_id: User identifier (uses DEFAULT_USER_ID if not provided)
            agent_id: Optional agent filter

        Returns:
            Number of memories deleted

        Raises:
            QdrantOfflineError: If Qdrant is unreachable
        """
        try:
            count = self.store.delete_all_memories(user_id=user_id, agent_id=agent_id)
            logger.info(f"Deleted {count} memories for user {user_id or 'default'}")
            return count
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e

    def get_status(self) -> StatusInfo:
        """Get system status and memory count.

        Returns:
            StatusInfo with connection and collection details

        Raises:
            QdrantOfflineError: If Qdrant is unreachable
        """
        try:
            # Ensure collection exists and get count
            self.store._ensure_collection()
            results = self.store.client.scroll(
                collection_name=self._config.qdrant.collection_name,
                limit=0,
            )
            count = len(results.points) if results.points else 0

            return StatusInfo(
                collection=self._config.qdrant.collection_name,
                count=count,
                host=self._config.qdrant.host,
                port=self._config.qdrant.port,
                connected=True,
            )
        except (ConnectionError, OSError, UnexpectedResponse) as e:
            raise QdrantOfflineError(
                self._config.qdrant.host,
                self._config.qdrant.port,
            ) from e


_memory_manager: MemoryManager | None = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
