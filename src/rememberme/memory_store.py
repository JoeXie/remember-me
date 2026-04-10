"""Memory store for Qdrant operations."""

import logging
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from .config import get_config
from .embeddings import get_embedding_service
from .models import Memory, SearchResult

logger = logging.getLogger(__name__)


class MemoryStore:
    """Memory storage operations with Qdrant."""

    def __init__(self) -> None:
        self._config = get_config()
        self._client: QdrantClient | None = None
        self._embedding_service = get_embedding_service()

    @property
    def client(self) -> QdrantClient:
        """Get or create Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(
                host=self._config.qdrant.host,
                port=self._config.qdrant.port,
                api_key=self._config.qdrant.api_key,
            )
        return self._client

    def _ensure_collection(self) -> None:
        """Ensure the collection exists with correct configuration."""
        collection_name = self._config.qdrant.collection_name

        try:
            self.client.get_collection(collection_name)
            logger.debug(f"Collection '{collection_name}' already exists")
        except Exception:
            logger.info(f"Creating collection '{collection_name}'")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=self._config.embedding.dimensions,
                    distance=models.Distance.COSINE,
                ),
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100,
                ),
            )
            logger.info(f"Collection '{collection_name}' created successfully")

    def add_memory(
        self,
        text: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> Memory:
        """Add a new memory."""
        self._ensure_collection()

        user_id = user_id or self._config.server.default_user_id
        run_id = agent_id

        memory = Memory.create(
            data=text,
            userId=user_id,
            runId=run_id,
        )

        vector = self._embedding_service.embed_single(text)

        self.client.upsert(
            collection_name=self._config.qdrant.collection_name,
            points=[
                models.PointStruct(
                    id=memory.id,
                    vector=vector,
                    payload=memory.to_payload(),
                )
            ],
        )

        logger.info(f"Added memory {memory.id} for user {user_id}")
        return memory

    def search_memories(
        self,
        query: str,
        user_id: str | None = None,
        agent_id: str | None = None,
        limit: int = 5,
    ) -> SearchResult:
        """Search memories by semantic similarity."""
        self._ensure_collection()

        user_id = user_id or self._config.server.default_user_id
        vector = self._embedding_service.embed_single(query)

        filter_conditions = [models.FieldCondition(key="userId", match=models.MatchValue(value=user_id))]

        if agent_id:
            filter_conditions.append(models.FieldCondition(key="runId", match=models.MatchValue(value=agent_id)))

        search_filter = models.Filter(must=filter_conditions)

        results = self.client.query_points(
            collection_name=self._config.qdrant.collection_name,
            query=vector,
            query_filter=search_filter,
            limit=limit,
        )

        memories = [Memory.from_payload(point.id, point.payload, point.score) for point in results.points]

        logger.info(f"Search found {len(memories)} results for query '{query[:50]}...'")
        return SearchResult(results=memories, count=len(memories))

    def get_memory(self, memory_id: str) -> Memory | None:
        """Get a memory by ID."""
        try:
            results = self.client.retrieve(
                collection_name=self._config.qdrant.collection_name,
                ids=[memory_id],
            )

            if not results:
                return None

            point = results[0]
            return Memory.from_payload(point.id, point.payload)

        except Exception as e:
            logger.warning(f"Failed to get memory {memory_id}: {e}")
            return None

    def update_memory(
        self,
        memory_id: str,
        text: str | None = None,
        metadata: dict | None = None,
    ) -> Memory | None:
        """Update an existing memory."""
        existing = self.get_memory(memory_id)
        if not existing:
            return None

        if text is not None:
            existing.data = text
            existing.hash = existing.hash
            existing.updatedAt = datetime.now(timezone.utc).isoformat()
        elif metadata:
            if "runId" in metadata:
                existing.runId = metadata["runId"]
            if "updatedAt" not in existing.to_payload():
                existing.updatedAt = datetime.now(timezone.utc).isoformat()

        if text is not None:
            vector = self._embedding_service.embed_single(text)
        else:
            vector = self._embedding_service.embed_single(existing.data)

        self.client.upsert(
            collection_name=self._config.qdrant.collection_name,
            points=[
                models.PointStruct(
                    id=existing.id,
                    vector=vector,
                    payload=existing.to_payload(),
                )
            ],
        )

        logger.info(f"Updated memory {memory_id}")
        return existing

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        try:
            self.client.delete(
                collection_name=self._config.qdrant.collection_name,
                points_selector=models.PointIdsList(points=[memory_id]),
            )
            logger.info(f"Deleted memory {memory_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete memory {memory_id}: {e}")
            return False

    def delete_all_memories(
        self,
        user_id: str | None = None,
        agent_id: str | None = None,
    ) -> int:
        """Delete all memories for a user (optionally filtered by agent)."""
        user_id = user_id or self._config.server.default_user_id

        filter_conditions = [models.FieldCondition(key="userId", match=models.MatchValue(value=user_id))]

        if agent_id:
            filter_conditions.append(models.FieldCondition(key="runId", match=models.MatchValue(value=agent_id)))

        search_filter = models.Filter(must=filter_conditions)

        results = self.client.scroll(
            collection_name=self._config.qdrant.collection_name,
            scroll_filter=search_filter,
            limit=100,
        )

        if not results.points:
            return 0

        point_ids = [point.id for point in results.points]

        self.client.delete(
            collection_name=self._config.qdrant.collection_name,
            points_selector=models.PointIdsList(points=point_ids),
        )

        logger.info(f"Deleted {len(point_ids)} memories for user {user_id}")
        return len(point_ids)


_memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
