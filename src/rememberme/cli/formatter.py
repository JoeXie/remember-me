"""Output formatters for CLI results."""

from abc import ABC, abstractmethod
from typing import Any


class OutputFormatter(ABC):
    """Base class for output formatters."""

    @abstractmethod
    def format_memory(self, memory: dict[str, Any]) -> str:
        """Format a single memory for output."""
        pass

    @abstractmethod
    def format_search(self, result: dict[str, Any]) -> str:
        """Format search results for output."""
        pass

    @abstractmethod
    def format_status(self, status: dict[str, Any]) -> str:
        """Format status info for output."""
        pass


class JsonFormatter(OutputFormatter):
    """JSON output formatter for programmatic use."""

    def format_memory(self, memory: dict[str, Any]) -> str:
        import json
        return json.dumps(memory, indent=2, ensure_ascii=False)

    def format_search(self, result: dict[str, Any]) -> str:
        import json
        return json.dumps(result, indent=2, ensure_ascii=False)

    def format_status(self, status: dict[str, Any]) -> str:
        import json
        return json.dumps(status, indent=2, ensure_ascii=False)


class MarkdownFormatter(OutputFormatter):
    """Markdown output formatter for human-readable output."""

    def format_memory(self, memory: dict[str, Any]) -> str:
        lines = [
            f"**{memory.get('data', '')}**",
            "",
            f"- ID: `{memory.get('id')}`",
            f"- User: `{memory.get('userId')}`",
        ]
        if memory.get("runId"):
            lines.append(f"- Session: `{memory.get('runId')}`")
        if memory.get("score") is not None:
            lines.append(f"- Score: `{memory.get('score'):.4f}`")
        lines.append(f"- Created: `{memory.get('createdAt')}`")
        if memory.get("updatedAt"):
            lines.append(f"- Updated: `{memory.get('updatedAt')}`")
        return "\n".join(lines)

    def format_search(self, result: dict[str, Any]) -> str:
        results = result.get("results", [])
        count = result.get("count", len(results))

        if not results:
            return "_No results found_"

        lines = [f"## Search Results ({count} found)", ""]
        for i, memory in enumerate(results, 1):
            lines.append(f"{i}. {self._memory_summary(memory)}")
        return "\n".join(lines)

    def format_status(self, status: dict[str, Any]) -> str:
        connected = status.get("connected", False)
        lines = [
            "## RememberMe Status",
            "",
            f"- **Qdrant**: {'`Connected`' if connected else '`Disconnected`'}",
            f"  - Host: `{status.get('host')}:{status.get('port')}`",
            f"  - Collection: `{status.get('collection')}`",
            f"- **Memories**: `{status.get('count', 0)}` stored",
        ]
        return "\n".join(lines)

    def _memory_summary(self, memory: dict[str, Any]) -> str:
        """One-line memory summary."""
        text = memory.get("data", "")
        # Truncate long text
        if len(text) > 60:
            text = text[:57] + "..."
        score = memory.get("score")
        score_str = f" (score: {score:.4f})" if score is not None else ""
        return f"**{text}**{score_str}"


def get_formatter(format_type: str) -> OutputFormatter:
    """Get formatter by name.

    Args:
        format_type: "json" or "markdown" (default)

    Returns:
        OutputFormatter instance
    """
    if format_type == "json":
        return JsonFormatter()
    return MarkdownFormatter()
