# RememberMe MCP Server

An MCP server providing long-term memory management for Claude Code and other MCP clients. Built on Qdrant vector database, supporting semantic search and memory updates.

## Features

- **Semantic Search** - Natural language queries using vector similarity
- **Multi-User Support** - User memory isolation via `userId`
- **Session Tracking** - Associate memories with specific agent sessions via `runId`
- **Content Deduplication** - MD5 hash to detect duplicate memories
- **Auto-Vectorization** - OpenAI-compatible embedding service integration

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Claude Code   │────▶│   Qdrant MCP    │────▶│   Qdrant DB     │
│   (MCP Client) │     │     Server      │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Installation

```bash
cd src/rememberme
pip install -e .
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QDRANT_HOST` | Qdrant server address | `<HOST>` (e.g. `localhost`) |
| `QDRANT_PORT` | Qdrant port | `<PORT>` (e.g. `6333`) |
| `QDRANT_COLLECTION_NAME` | Collection name | `memories` |
| `QDRANT_API_KEY` | Qdrant API key | - |
| `EMBEDDING_API_KEY` | Embedding API key | **Required** |
| `EMBEDDING_MODEL` | Embedding model (OpenAI compatible) | `<EMBEDDING_MODEL>` (e.g. `doubao-embedding-vision`) |
| `EMBEDDING_DIMENSIONS` | Vector dimensions | `<EMBEDDING_DIMENSIONS>` (e.g. `2048`) |
| `OPENAI_BASE_URL` | Embedding API endpoint | `<OPENAI_BASE_URL>` (e.g. `https://ark.cn-beijing.volces.com/api/coding/v3`) |
| `DEFAULT_USER_ID` | Default user ID | `<DEFAULT_USER_ID>` (e.g. `user_peanut`) |
| `LOG_LEVEL` | Log level | `INFO` |

> **Placeholder Note**: `<PLACEHOLDER>` format indicates customizable parameters. Replace with actual values during deployment.

## Claude Code Integration

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

### Verify Connection

After configuration, run in Claude Code:

```
/mcp list
```

You should see `rememberme` server enabled.

### Available Tools

Once enabled, Claude Code can directly use these memory management tools:
- `add_memory` - Add a memory
- `search_memories` - Semantic search
- `get_memory` - Get a single memory
- `update_memory` - Update a memory
- `delete_memory` - Delete a memory
- `delete_all_memories` - Clear all memories

### Start Server

```bash
python -m rememberme
```

### MCP Tools

#### add_memory

Add a new memory.

```json
{
  "text": "User prefers Go language for backend development",
  "user_id": "<USER_ID>",
  "agent_id": "agent:main:<UUID>"
}
```

#### search_memories

Semantic memory search.

```json
{
  "query": "What programming language does the user prefer",
  "user_id": "<USER_ID>",
  "limit": 5
}
```

#### get_memory

Get a memory by ID.

```json
{
  "id": "<MEMORY_UUID>"
}
```

#### update_memory

Update memory content.

```json
{
  "id": "<MEMORY_UUID>",
  "text": "Updated content"
}
```

#### delete_memory

Delete a specific memory.

```json
{
  "id": "<MEMORY_UUID>"
}
```

#### delete_all_memories

Delete all memories for a user.

```json
{
  "user_id": "<USER_ID>"
}
```

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

## Run Tests

```bash
cd tests
pip install pytest pytest-asyncio
pytest
```

## Project Structure

```
src/rememberme/
├── __init__.py          # Package init
├── __main__.py          # MCP server entry
├── config.py            # Configuration management
├── models.py            # Data models
├── embeddings.py        # Embedding service
├── memory_store.py      # Qdrant operations
├── pyproject.toml       # Dependencies
└── .env.example         # Environment template

tests/
├── __init__.py
├── test_models.py       # Data model tests
├── test_config.py       # Configuration tests
└── test_embeddings.py  # Embedding service tests
```

## License

MIT
