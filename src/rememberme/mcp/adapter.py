"""MCP adapter - wraps MemoryManager for MCP protocol."""

from __future__ import annotations

import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from ..core.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)

APP_NAME = "rememberme"
VERSION = "0.2.0"


def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server(APP_NAME)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available MCP tools."""
        return [
            Tool(
                name="add_memory",
                description="""Save important information to long-term memory.

## When to Use
- User stated preferences ('User prefers dark mode')
- Personal context ('User is learning Rust', 'User works on payments team')
- Project patterns ('API endpoint at /api/v2', 'Uses PostgreSQL for this project')
- Agreed decisions ('Team decided to use Docker for deployment')
- Constraints ('Budget is tight', 'Deadline is end of month')
- Lessons learned ('Don't use library X, it caused issues')

## Post-Response Storage Pattern (IMPORTANT)
After responding to user, EVALUATE whether new facts should be stored:
1. Did user share personal context? → Store it
2. Did we make a technical decision? → Store it
3. Did user express a preference? → Store it
4. Did user correct previous information? → Update existing memory

## Deduplication
Search before adding if the info seems routine. Prefer UPDATING existing memories when finding conflicting info. Store each distinct piece as a separate memory with clear, searchable text.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Memory content - write clear, searchable statement (e.g., 'User prefers dark mode theme')."},
                        "user_id": {"type": "string", "description": "User identifier (optional, uses default if not set)."},
                        "agent_id": {"type": "string", "description": "Session/run identifier for grouping related memories."},
                        "metadata": {"type": "object", "description": "Additional metadata (runId supported)."},
                    },
                    "required": ["text"],
                },
            ),
            Tool(
                name="search_memories",
                description="""Query stored memories to retrieve relevant context.

## Pre-Execution Recall Pattern (IMPORTANT)
BEFORE responding to user, search for relevant memories based on context:
1. User asks about skills/capabilities? → Search 'user programming language', 'user technical skills'
2. User mentions location/environment? → Search 'user city', 'user location', 'user timezone'
3. User asks about preferences? → Search 'user preference', 'user coding preference'
4. User references past decisions? → Search 'user decision', 'user project choice'
5. User asks about project context? → Search 'user project framework', 'user project database'

## Triggers
- When starting new tasks (check 'has user worked on this before?')
- Before giving advice on topics from past sessions
- When user references something you don't recall
- After any significant decision or preference is stated

## Proactive Early Search
At session start, consider searching 'user preferences', 'project architecture', 'agreed approach' to build context.

Use lower limits (1-3) for specific lookups, higher limits (5-10) for broad context.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query (e.g., 'user coding preferences', 'database setup decisions')."},
                        "user_id": {"type": "string", "description": "User identifier to scope search to specific user."},
                        "agent_id": {"type": "string", "description": "Optional session filter to find memories from current run."},
                        "limit": {"type": "integer", "description": "Max results (default: 5, increase for broader context).", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="get_memory",
                description="""Retrieve a specific memory by its ID.

## When to Use
- You have a memory ID from a previous search result
- After adding a memory and need to verify or get full details
- User asks for details about a specific memory they referenced
- After update/delete operations to confirm results

## Pre-Execution Recall
Usually you'll use search_memories first to find relevant memories. Use get_memory when you already have an ID and need full details.

Returns full memory details including metadata, timestamps, and the stored content.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "The memory ID to retrieve."},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="update_memory",
                description="""Update an existing memory when information changes or needs correction.

## When to Use
- Same fact changes ('User now prefers light mode instead of dark')
- More precise info becomes available ('Project uses PostgreSQL 16, not 15')
- User corrects previous information
- Correcting errors in stored facts

## Post-Response Correction Pattern
After responding, if user provides CORRECTIONS or UPDATED information:
1. Search for existing memory on the topic
2. If found → UPDATE the existing memory
3. If not found → ADD new memory (don't force update on genuinely new topics)

## Storage Decision
- ADD NEW for genuinely new topics
- UPDATE existing when same fact changes
- If unsure, prefer ADD - storing multiple perspectives is safer than losing context

The text field replaces content entirely; metadata (runId) preserves linkage.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID to update (from get_memory or search results)."},
                        "text": {"type": "string", "description": "Updated memory content - replaces previous text entirely."},
                        "metadata": {"type": "object", "description": "Metadata updates (only runId supported for linkage to new sessions)."},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="delete_memory",
                description="""Remove a specific memory when it is no longer relevant, was stored in error, or user requests deletion.

## When to Use
- User requests deletion ('Forget what I said about X')
- Old version redundant after update
- Something stored by mistake
- User explicitly asks to 'forget' or 'delete' specific information

## Privacy
Honor all deletion requests promptly. User privacy is paramount.

## Cleanup Pattern
After post-response storage evaluation, if a memory is found to be:
- Redundant with newly updated version
- Incorrectly stored
- No longer relevant

→ Delete the old/incorrect memory to maintain clean memory store.""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Memory ID to delete."},
                    },
                    "required": ["id"],
                },
            ),
            Tool(
                name="delete_all_memories",
                description="""Bulk delete all memories for a user, optionally filtered to a specific session.

## Use Cases
- User starts fresh on a project ('Clear all my memories')
- Complete privacy wipe requested
- Abandoned/debug session cleanup
- User explicitly requests full memory reset

## Caution
Destructive and irreversible. Confirm with user if request seems broad.

Without agent_id: deletes ALL user memories
With agent_id: deletes only that session's memories

## Pre-Deletion Recommendation
Before bulk delete, consider:
1. Informing user how many memories will be deleted
2. Confirming they want to proceed
3. Suggesting targeted delete if they only want to remove specific memories""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "User identifier (optional, uses default if not set)."},
                        "agent_id": {"type": "string", "description": "Optional: delete only memories from this specific session/run."},
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle tool calls via MemoryManager."""
        try:
            manager = get_memory_manager()

            if name == "add_memory":
                result = manager.add_memory(
                    text=arguments["text"],
                    user_id=arguments.get("user_id"),
                    agent_id=arguments.get("agent_id"),
                )

            elif name == "search_memories":
                result = manager.search_memories(
                    query=arguments["query"],
                    user_id=arguments.get("user_id"),
                    agent_id=arguments.get("agent_id"),
                    limit=arguments.get("limit", 5),
                )

            elif name == "get_memory":
                result = manager.get_memory(arguments["id"])
                if result is None:
                    result = {"error": "Memory not found"}

            elif name == "update_memory":
                result = manager.update_memory(
                    memory_id=arguments["id"],
                    text=arguments.get("text"),
                )
                if result is None:
                    result = {"error": "Memory not found"}

            elif name == "delete_memory":
                success = manager.delete_memory(arguments["id"])
                result = {"success": success, "id": arguments["id"]}

            elif name == "delete_all_memories":
                deleted_count = manager.delete_all_memories(
                    user_id=arguments.get("user_id"),
                    agent_id=arguments.get("agent_id"),
                )
                result = {"success": True, "deleted_count": deleted_count}

            else:
                result = {"error": f"Unknown tool: {name}"}

            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

        except Exception as e:
            logger.exception(f"Error handling tool {name}")
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


async def run_mcp_mode() -> None:
    """Run the MCP server."""
    from ..config import get_config
    config = get_config()
    logger.info(f"Starting RememberMe MCP Server v{VERSION}")
    logger.info(f"Qdrant: {config.qdrant.host}:{config.qdrant.port}/{config.qdrant.collection_name}")

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
