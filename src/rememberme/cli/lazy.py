"""Lazy loading utilities to avoid loading heavy dependencies on --help."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

# Modules that are expensive to import (httpx, qdrant_client, etc.)
_HEAVY_MODULES = frozenset({
    "qdrant_client",
    "qdrant_client.http",
    "httpx",
    "openai",
    "anthropic",
})


def is_help_mode() -> bool:
    """Check if we're in --help mode (no heavy imports needed)."""
    return "--help" in sys.argv or "-h" in sys.argv


def lazy_import(name: str):
    """Lazily import a module, skipping if in --help mode.

    Use this decorator pattern:
        @lazy_import("qdrant_client")
        def some_function():
            from qdrant_client import QdrantClient
            ...
    """
    if is_help_mode() and name in _HEAVY_MODULES:
        return None
    from importlib import import_module
    return import_module(name)


class LazyLoader:
    """Deferred module loader for heavy dependencies."""

    _cache: dict[str, object] = {}

    @classmethod
    def load(cls, name: str):
        """Load a module, caching the result."""
        if name in cls._cache:
            return cls._cache[name]
        if is_help_mode() and name in _HEAVY_MODULES:
            return None
        from importlib import import_module
        module = import_module(name)
        cls._cache[name] = module
        return module

    @classmethod
    def clear_cache(cls):
        """Clear the module cache (useful for testing)."""
        cls._cache.clear()
