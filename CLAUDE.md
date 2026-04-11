# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RememberMe is a CLI + MCP dual-mode tool for long-term memory management. It uses Qdrant vector database for semantic search and stores memories with user/session isolation.

## Commands

```bash
# MCP mode (stdio) - for Claude Code integration
python -m rememberme
python -m rememberme mcp

# CLI mode - direct commands
python -m rememberme --help
python -m rememberme add "memory text"
python -m rememberme search "query" --limit 5
python -m rememberme status

# Install in development mode
pip install -e .
```

### CLI Subcommands

| Command | Description |
|---------|-------------|
| `add TEXT` | Add a new memory |
| `search QUERY` | Search memories by semantic similarity |
| `status` | Check Qdrant connection and memory count |
| `delete ID` | Delete a memory by ID |
| `delete-all` | Delete all memories for current user |

## Architecture

```
                    Dual-Mode Entry (__main__.py)
                               |
          +--------------------+--------------------+
          |                                         |
          v                                         v
      CLI Mode                                   MCP Mode
   (Click commands)                          (stdio server)
          |                                         |
          v                                         v
   core/memory_manager.py               mcp/adapter.py
   (MemoryManager)                      (Server + tools)
          |                                         |
          +--------------------+--------------------+
                               |
                               v
                    memory_store.py (Qdrant)
                               |
                               v
                    embeddings.py (OpenAI-compatible)
```

### Module Structure

- `__main__.py` - Dual-entry router (auto-detects CLI vs MCP mode)
- `core/memory_manager.py` - High-level API wrapping MemoryStore
- `core/exceptions.py` - Custom exceptions (QdrantOfflineError, ValidationError)
- `cli/commands.py` - Click CLI command definitions
- `cli/formatter.py` - JSON/Markdown output formatters
- `cli/lazy.py` - Lazy imports for fast --help
- `mcp/adapter.py` - MCP Server adapter wrapping MemoryManager
- `memory_store.py` - Qdrant CRUD operations (internal use)
- `embeddings.py` - OpenAI-compatible embedding service (internal use)

### Data Model

`Memory` dataclass with these fields (note the camelCase naming for Qdrant compatibility):
- `id`: UUID string
- `userId`: user identifier for isolation
- `data`: memory content text
- `hash`: MD5 hash for deduplication
- `createdAt`: ISO 8601 timestamp
- `runId`: optional agent session identifier (format: `agent:{type}:{uuid}`)
- `updatedAt`: optional, set only on updates
- `score`: search similarity score (only in search results)

### Configuration

Environment variables (see `.env.example`):
- `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION_NAME`
- `EMBEDDING_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSIONS`, `OPENAI_BASE_URL`
- `DEFAULT_USER_ID`
- Collection auto-creates on first start with HNSW index (m=16, ef_construct=100)

### MCP Tool Guidelines

The tool descriptions in `mcp/adapter.py` embed usage guidelines for when to query, save, update, and delete memories. These are loaded by Claude Code on MCP connect and should guide memory behavior.

## Documentation Rules

**Sync README with code changes**: As features evolve, the `README.md` and `README-CN.md` files must be updated alongside the code. When adding new commands, modules, configuration options, or changing existing functionality, update both:
- `README.md` (English)
- `README-CN.md` (Chinese)

This applies to:
- New CLI commands or options
- New MCP tools
- New environment variables or configuration
- Changes to architecture or module structure
- New dependencies or installation requirements

## Skills (for OpenClaw)

The `skills/` directory contains skill definitions for OpenClaw integration:

- `skills/using-rememberme-cli/SKILL.md` - OpenClaw skill for using rememberme CLI commands

**Note**: These skills are for OpenClaw (external agents), not for Claude Code itself. Claude Code uses the MCP tools directly via `mcp/adapter.py`.
