"""Tests for configuration."""

import os
import pytest
from unittest.mock import patch


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {
            "EMBEDDING_API_KEY": "test-key",
        }, clear=True):
            from rememberme.config import Config

            config = Config()

            assert config.qdrant.host == "localhost"
            assert config.qdrant.port == 6333
            assert config.qdrant.collection_name == "memories"
            assert config.embedding.model == "doubao-embedding-vision"
            assert config.embedding.dimensions == 2048
            assert config.server.default_user_id == "user_peanut"
            assert config.server.log_level == "INFO"

    def test_custom_values(self):
        """Test custom configuration values."""
        with patch.dict(os.environ, {
            "EMBEDDING_API_KEY": "test-key",
            "QDRANT_HOST": "custom-host",
            "QDRANT_PORT": "6334",
            "QDRANT_COLLECTION_NAME": "custom-collection",
            "EMBEDDING_DIMENSIONS": "1024",
            "DEFAULT_USER_ID": "custom-user",
        }, clear=True):
            from rememberme.config import Config

            config = Config()

            assert config.qdrant.host == "custom-host"
            assert config.qdrant.port == 6334
            assert config.qdrant.collection_name == "custom-collection"
            assert config.embedding.dimensions == 1024
            assert config.server.default_user_id == "custom-user"

    def test_missing_embedding_api_key(self):
        """Test that missing EMBEDDING_API_KEY raises error."""
        with patch.dict(os.environ, {}, clear=True):
            from rememberme.config import Config

            with pytest.raises(ValueError, match="EMBEDDING_API_KEY"):
                Config()

    def test_qdrant_api_key_optional(self):
        """Test that QDRANT_API_KEY is optional."""
        with patch.dict(os.environ, {
            "EMBEDDING_API_KEY": "test-key",
            "QDRANT_API_KEY": "",
        }, clear=True):
            from rememberme.config import Config

            config = Config()
            assert config.qdrant.api_key is None
