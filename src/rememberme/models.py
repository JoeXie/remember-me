"""Data models for RememberMe MCP Server."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import hashlib
import uuid


@dataclass
class Memory:
    """Memory data model matching Qdrant payload structure."""

    id: str
    userId: str
    data: str
    hash: str
    createdAt: str
    runId: str | None = None
    updatedAt: str | None = None
    score: float | None = None

    @classmethod
    def create(
        cls,
        data: str,
        userId: str,
        runId: str | None = None,
    ) -> "Memory":
        """Create a new Memory instance with generated id, hash, and timestamp."""
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            userId=userId,
            data=data,
            hash=hashlib.md5(data.encode()).hexdigest(),
            createdAt=now,
            runId=runId,
        )

    def to_payload(self) -> dict[str, Any]:
        """Convert to Qdrant payload dict."""
        payload = {
            "userId": self.userId,
            "data": self.data,
            "hash": self.hash,
            "createdAt": self.createdAt,
        }
        if self.runId:
            payload["runId"] = self.runId
        if self.updatedAt:
            payload["updatedAt"] = self.updatedAt
        return payload

    @classmethod
    def from_payload(cls, id: str, payload: dict[str, Any], score: float | None = None) -> "Memory":
        """Create Memory instance from Qdrant payload."""
        return cls(
            id=id,
            userId=payload["userId"],
            data=payload["data"],
            hash=payload["hash"],
            createdAt=payload["createdAt"],
            runId=payload.get("runId"),
            updatedAt=payload.get("updatedAt"),
            score=score,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response dict."""
        result: dict[str, Any] = {
            "id": self.id,
            "data": self.data,
            "userId": self.userId,
            "hash": self.hash,
            "createdAt": self.createdAt,
        }
        if self.runId:
            result["runId"] = self.runId
        if self.updatedAt:
            result["updatedAt"] = self.updatedAt
        if self.score is not None:
            result["score"] = self.score
        return result


@dataclass
class SearchResult:
    """Search result container."""

    results: list[Memory]
    count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response dict."""
        return {
            "results": [r.to_dict() for r in self.results],
            "count": self.count,
        }
