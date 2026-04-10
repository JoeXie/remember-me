"""Embedding service for vector generation."""

import logging
from typing import Any

import httpx

from .config import get_config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings via OpenAI-compatible API."""

    def __init__(self) -> None:
        self._config = get_config()
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._config.embedding.base_url,
                headers={
                    "Authorization": f"Bearer {self._config.embedding.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = self.embed_batch([text])
        return embeddings[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        payload: dict[str, Any] = {
            "model": self._config.embedding.model,
            "input": texts,
        }

        for attempt in range(3):
            try:
                response = self.client.post("/embeddings", json=payload)
                response.raise_for_status()
                result = response.json()

                embeddings = [item["embedding"] for item in result["data"]]
                logger.debug(f"Generated {len(embeddings)} embeddings")
                return embeddings

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == 2:
                    raise
            except Exception as e:
                logger.warning(f"Embedding error on attempt {attempt + 1}: {e}")
                if attempt == 2:
                    raise

        return []

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
