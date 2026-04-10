"""Tests for data models."""

import pytest
from datetime import datetime, timezone

from rememberme.models import Memory, SearchResult


class TestMemory:
    """Tests for Memory model."""

    def test_create_memory(self):
        """Test creating a new memory."""
        memory = Memory.create(
            data="Test memory content",
            userId="user_test",
            runId="agent:test:123",
        )

        assert memory.id is not None
        assert memory.data == "Test memory content"
        assert memory.userId == "user_test"
        assert memory.runId == "agent:test:123"
        assert memory.hash is not None
        assert memory.createdAt is not None
        assert memory.updatedAt is None

    def test_create_memory_without_run_id(self):
        """Test creating memory without runId."""
        memory = Memory.create(
            data="Simple memory",
            userId="user_simple",
        )

        assert memory.runId is None
        assert memory.data == "Simple memory"

    def test_to_payload(self):
        """Test converting memory to payload."""
        memory = Memory.create(
            data="Payload test",
            userId="user_payload",
            runId="agent:payload:456",
        )

        payload = memory.to_payload()

        assert payload["userId"] == "user_payload"
        assert payload["data"] == "Payload test"
        assert payload["runId"] == "agent:payload:456"
        assert "hash" in payload
        assert "createdAt" in payload
        assert "updatedAt" not in payload

    def test_from_payload(self):
        """Test creating memory from payload."""
        payload = {
            "userId": "user_from_payload",
            "data": "Restored memory",
            "hash": "abc123",
            "createdAt": "2026-04-10T00:00:00.000Z",
            "runId": "agent:restore:789",
        }

        memory = Memory.from_payload("test-id-123", payload)

        assert memory.id == "test-id-123"
        assert memory.userId == "user_from_payload"
        assert memory.data == "Restored memory"
        assert memory.runId == "agent:restore:789"

    def test_to_dict(self):
        """Test converting memory to API response dict."""
        memory = Memory.create(
            data="Dict test",
            userId="user_dict",
        )
        memory.score = 0.95

        result = memory.to_dict()

        assert result["id"] == memory.id
        assert result["data"] == "Dict test"
        assert result["score"] == 0.95
        assert "userId" in result
        assert "hash" in result

    def test_hash_is_consistent(self):
        """Test that same content produces same hash."""
        memory1 = Memory.create(data="Same content", userId="user1")
        memory2 = Memory.create(data="Same content", userId="user2")

        assert memory1.hash == memory2.hash

    def test_different_content_different_hash(self):
        """Test that different content produces different hash."""
        memory1 = Memory.create(data="Content A", userId="user1")
        memory2 = Memory.create(data="Content B", userId="user1")

        assert memory1.hash != memory2.hash


class TestSearchResult:
    """Tests for SearchResult."""

    def test_search_result_to_dict(self):
        """Test converting search result to dict."""
        memory = Memory.create(data="Search result", userId="user_search")
        memory.score = 0.85

        search_result = SearchResult(results=[memory], count=1)
        result = search_result.to_dict()

        assert result["count"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["data"] == "Search result"
        assert result["results"][0]["score"] == 0.85
