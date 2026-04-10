"""Tests for embedding service."""

import pytest
from unittest.mock import patch, MagicMock

from rememberme.embeddings import EmbeddingService


class TestEmbeddingService:
    """Tests for EmbeddingService."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = MagicMock()
        config.embedding.api_key = "test-key"
        config.embedding.model = "doubao-embedding-vision"
        config.embedding.dimensions = 2048
        config.embedding.base_url = "http://test-api.example.com/v1"
        return config

    @pytest.fixture
    def mock_response(self):
        """Mock successful API response."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 2048},
                {"embedding": [0.2] * 2048},
            ]
        }
        return response

    def test_embed_single(self, mock_config, mock_response):
        """Test single text embedding."""
        with patch("rememberme.embeddings.get_config", return_value=mock_config):
            with patch("httpx.Client.post", return_value=mock_response):
                service = EmbeddingService()
                result = service.embed_single("test text")

                assert len(result) == 2048
                assert result[0] == 0.1

    def test_embed_batch(self, mock_config, mock_response):
        """Test batch embedding."""
        with patch("rememberme.embeddings.get_config", return_value=mock_config):
            with patch("httpx.Client.post", return_value=mock_response):
                service = EmbeddingService()
                result = service.embed_batch(["text1", "text2"])

                assert len(result) == 2
                assert len(result[0]) == 2048
                assert len(result[1]) == 2048

    def test_embed_empty_batch(self, mock_config):
        """Test empty batch returns empty list."""
        with patch("rememberme.embeddings.get_config", return_value=mock_config):
            service = EmbeddingService()
            result = service.embed_batch([])

            assert result == []

    def test_embed_retry_on_error(self, mock_config, mock_response):
        """Test retry mechanism on API error."""
        mock_error_response = MagicMock()
        mock_error_response.status_code = 500

        with patch("rememberme.embeddings.get_config", return_value=mock_config):
            with patch("httpx.Client.post", side_effect=[Exception("Error"), Exception("Error"), mock_response]) as mock_post:
                service = EmbeddingService()
                result = service.embed_single("test")

                assert mock_post.call_count == 3
                assert len(result) == 2048
