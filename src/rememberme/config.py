"""Configuration management for RememberMe MCP Server."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class QdrantConfig:
    """Qdrant database configuration."""

    host: str
    port: int
    collection_name: str
    api_key: str | None


@dataclass
class EmbeddingConfig:
    """Embedding service configuration."""

    api_key: str
    model: str
    dimensions: int
    base_url: str


@dataclass
class ServerConfig:
    """Server configuration."""

    default_user_id: str
    log_level: str


class Config:
    """Main configuration class that loads from environment variables."""

    def __init__(self) -> None:
        self.qdrant = QdrantConfig(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            collection_name=os.getenv("QDRANT_COLLECTION_NAME", "memories"),
            api_key=os.getenv("QDRANT_API_KEY") or None,
        )

        self.embedding = EmbeddingConfig(
            api_key=self._require_env("EMBEDDING_API_KEY"),
            model=os.getenv("EMBEDDING_MODEL", "doubao-embedding-vision"),
            dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "2048")),
            base_url=os.getenv("OPENAI_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3"),
        )

        self.server = ServerConfig(
            default_user_id=os.getenv("DEFAULT_USER_ID", "user_peanut"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def _require_env(self, key: str) -> str:
        """Get required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value


_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
