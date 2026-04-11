"""Core exceptions for RememberMe."""


class MemoryError(Exception):
    """Base exception for memory operations."""
    pass


class QdrantOfflineError(MemoryError):
    """Raised when Qdrant is unreachable."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        super().__init__(
            f"Cannot connect to Qdrant at {host}:{port}. "
            "Please ensure Qdrant is running. "
            "Hint: docker run -p 6333:6333 qdrant/qdrant"
        )


class ValidationError(MemoryError):
    """Raised when input validation fails."""
    pass


class NotFoundError(MemoryError):
    """Raised when a memory is not found."""
    pass
