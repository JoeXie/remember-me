# RememberMe - CLI + MCP Server

A dual-mode tool providing long-term memory management for Claude Code and other MCP clients. Features both a CLI interface for direct commands and an MCP server for programmatic access.

Built on Qdrant vector database with semantic search and user/session isolation.

## Features

- **Dual-Mode**: CLI commands + MCP server integration
- **Semantic Search** - Natural language queries using vector similarity
- **Multi-User Support** - User memory isolation via `userId`
- **Session Tracking** - Associate memories with specific agent sessions via `runId`
- **Content Deduplication** - MD5 hash to detect duplicate memories
- **Auto-Vectorization** - OpenAI-compatible embedding service integration

## Quick Start

```bash
# Install
pip install -e .

# CLI usage
rememberme add "User prefers dark mode"
rememberme search "preferences" --limit 5
rememberme status

# MCP mode (for Claude Code)
python -m rememberme
```

## Installation

This guide walks you through setting up RememberMe from downloading the repository to your first command.

### Prerequisites

- **Python 3.10+**
- **Qdrant** (vector database) - [Install via Docker](https://qdrant.tech/documentation/guides/)
- **Embedding API** (OpenAI-compatible) - e.g., Doubao, OpenAI, LocalAI

### Step 1: Clone the Repository

```bash
git clone https://github.com/JoeXie/remember-me.git
cd remember-me
```

Or download and extract the archive from GitHub.

### Step 2: Install Dependencies

```bash
pip install -e .
```

This installs RememberMe in development mode and creates the `rememberme` command.

### Step 3: Configure Environment

Copy the example env file and edit with your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Required: Your embedding API credentials
EMBEDDING_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3

# Required: Embedding model configuration
EMBEDDING_MODEL=doubao-embedding-vision
EMBEDDING_DIMENSIONS=2048

# Optional: Qdrant connection (defaults shown)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=memories

# Optional: Default user ID
DEFAULT_USER_ID=user_default
```

### Step 4: Start Qdrant

Make sure Qdrant is running:

```bash
# Using Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant

# Or using Podman
podman run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Step 5: Verify Installation

Check that everything is connected:

```bash
rememberme status
```

Expected output:
```
## RememberMe Status

- **Qdrant**: `Connected`
  - Host: `localhost:6333`
  - Collection: `memories`
- **Memories**: `0` stored
```

### Step 6: Try Your First Command

```bash
# Add a memory
rememberme add "User prefers dark mode theme"

# Search memories
rememberme search "preferences"

# Get help
rememberme --help
```

### Troubleshooting

| Issue | Solution |
|-------|----------|
| `QdrantOfflineError` | Ensure Qdrant is running (`docker run -p 6333:6333 qdrant/qdrant`) |
| `ValidationError` | Check `EMBEDDING_API_KEY` and `OPENAI_BASE_URL` in `.env` |
| Command not found | Re-run `pip install -e .` to create the `rememberme` command |
| Collection error | RememberMe auto-creates the collection on first run |

## CLI Commands

```bash
# Add a new memory
rememberme add "User prefers dark mode"

# Search memories
rememberme search "user preferences"
rememberme search "project decisions" --limit 10

# Check status
rememberme status

# Delete a memory
rememberme delete <memory_id>

# Delete all memories
rememberme delete-all --force

# JSON output (for programmatic use)
rememberme add "text" --json
rememberme search "query" --json
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--user-id` | User ID scope (defaults to DEFAULT_USER_ID env var) |
| `--debug` | Enable debug logging |

## Architecture

```
                    Dual-Mode Entry
                  ┌─────────────────┐
                  │  __main__.py    │
                  │  auto-detects   │
                  └────────┬────────┘
                           │
          ┌────────────────┼────────────────┐
          │                                 │
          ▼                                 ▼
    ┌───────────┐                    ┌─────────────┐
    │  CLI Mode │                    │ MCP Mode    │
    │  (Click)  │                    │ (stdio)     │
    └─────┬─────┘                    └──────┬──────┘
          │                                 │
          ▼                                 │
    MemoryManager                           │
    (core/memory_manager.py)                │
          │                                 │
          └────────────────┼────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │     MemoryStore         │
              │   (Qdrant operations)   │
              └─────────────────────────┘
```

## MCP Server Integration

### Method 1: Using claude code command

```bash
# Add MCP server
claude mcp add rememberme -- python -m rememberme

# Or specify working directory
claude mcp add rememberme -- bash -c "cd /path/to/RememberMe && python -m rememberme"
```

### Method 2: Manual configuration (persistent)

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "rememberme": {
      "command": "python",
      "args": ["-m", "rememberme"],
      "env": {
        "QDRANT_HOST": "<HOST>",
        "QDRANT_PORT": "<PORT>",
        "EMBEDDING_API_KEY": "<YOUR_API_KEY>",
        "EMBEDDING_MODEL": "<EMBEDDING_MODEL>",
        "EMBEDDING_DIMENSIONS": "<EMBEDDING_DIMENSIONS>",
        "OPENAI_BASE_URL": "<OPENAI_BASE_URL>",
        "DEFAULT_USER_ID": "<DEFAULT_USER_ID>"
      }
    }
  }
}
```

### Available MCP Tools

- `add_memory` - Add a memory
- `search_memories` - Semantic search
- `get_memory` - Get a single memory
- `update_memory` - Update a memory
- `delete_memory` - Delete a memory
- `delete_all_memories` - Clear all memories

## OpenClaw Skill Integration

For OpenClaw agents, install the RememberMe skill to enable auto-recall and auto-storage:

```bash
# Install skill from local repository
/skill install path/to/RememberMe/skills/using-rememberme-cli --always true
```

**Important:** When installing, set `always: true` to enable automatic pre-execution recall and post-response storage on every conversation.

The skill provides:
- **Auto-Recall**: Automatically searches memory before responding based on context
- **Auto-Storage**: Evaluates and stores new facts after responding

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_HOST` | Qdrant server address | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `QDRANT_COLLECTION_NAME` | Collection name | `memories` |
| `QDRANT_API_KEY` | Qdrant API key | - |
| `EMBEDDING_API_KEY` | Embedding API key | **Required** |
| `EMBEDDING_MODEL` | Embedding model (OpenAI compatible) | `doubao-embedding-vision` |
| `EMBEDDING_DIMENSIONS` | Vector dimensions | `2048` |
| `OPENAI_BASE_URL` | Embedding API endpoint | Required |
| `DEFAULT_USER_ID` | Default user ID | `user_default` |
| `LOG_LEVEL` | Log level | `INFO` |

## Data Format

Payload structure stored in Qdrant:

```json
{
  "userId": "<USER_ID>",
  "data": "Memory content",
  "hash": "<MD5_HASH>",
  "createdAt": "<TIMESTAMP>",
  "runId": "agent:main:<UUID>"
}
```

## Project Structure

```
src/rememberme/
├── __main__.py          # Dual-mode entry (CLI + MCP auto-detect)
├── config.py            # Configuration management
├── models.py            # Data models
├── embeddings.py        # Embedding service
├── memory_store.py      # Qdrant operations
│
├── core/                # Core business logic
│   ├── __init__.py
│   ├── exceptions.py    # Custom exceptions
│   └── memory_manager.py
│
├── cli/                 # CLI interface
│   ├── __init__.py
│   ├── commands.py      # Click commands
│   ├── formatter.py    # Output formatters
│   └── lazy.py          # Lazy imports
│
├── mcp/                 # MCP adapter
│   ├── __init__.py
│   └── adapter.py       # MCP server
│
└── skill/               # OpenClaw skill
    └── manage_personal_memory.py

skills/                   # OpenClaw skills (distributed separately)
└── using-rememberme-cli/
    └── SKILL.md

tests/
├── test_models.py
├── test_config.py
└── test_embeddings.py
```

## Run Tests

```bash
pytest tests/
```

## License

MIT
