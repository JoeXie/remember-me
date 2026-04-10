"""MCP Server entry point for RememberMe."""

import json
import logging
import sys

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import get_config
from .memory_store import get_memory_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

APP_NAME = "rememberme"
VERSION = "0.1.0"

server = Server(APP_NAME)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="add_memory",
            description="Add a new memory to the store",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Memory content text"},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "agent_id": {"type": "string", "description": "Agent/Run identifier"},
                    "metadata": {"type": "object", "description": "Additional metadata"},
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="search_memories",
            description="Search memories by semantic similarity",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "user_id": {"type": "string", "description": "User identifier"},
                    "agent_id": {"type": "string", "description": "Agent/Run identifier"},
                    "limit": {"type": "integer", "description": "Max results to return", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_memory",
            description="Get a memory by its ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Memory ID"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="update_memory",
            description="Update an existing memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Memory ID to update"},
                    "text": {"type": "string", "description": "New memory content"},
                    "metadata": {"type": "object", "description": "Metadata updates"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="delete_memory",
            description="Delete a memory by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Memory ID to delete"},
                },
                "required": ["id"],
            },
        ),
        Tool(
            name="delete_all_memories",
            description="Delete all memories for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "User identifier"},
                    "agent_id": {"type": "string", "description": "Agent/Run identifier"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        memory_store = get_memory_store()

        if name == "add_memory":
            memory = memory_store.add_memory(
                text=arguments["text"],
                user_id=arguments.get("user_id"),
                agent_id=arguments.get("agent_id"),
                metadata=arguments.get("metadata"),
            )
            result = memory.to_dict()

        elif name == "search_memories":
            result = memory_store.search_memories(
                query=arguments["query"],
                user_id=arguments.get("user_id"),
                agent_id=arguments.get("agent_id"),
                limit=arguments.get("limit", 5),
            ).to_dict()

        elif name == "get_memory":
            memory = memory_store.get_memory(arguments["id"])
            if memory is None:
                result = {"error": "Memory not found"}
            else:
                result = memory.to_dict()

        elif name == "update_memory":
            memory = memory_store.update_memory(
                memory_id=arguments["id"],
                text=arguments.get("text"),
                metadata=arguments.get("metadata"),
            )
            if memory is None:
                result = {"error": "Memory not found"}
            else:
                result = memory.to_dict()

        elif name == "delete_memory":
            success = memory_store.delete_memory(arguments["id"])
            result = {"success": success, "id": arguments["id"]}

        elif name == "delete_all_memories":
            deleted_count = memory_store.delete_all_memories(
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


async def main() -> None:
    """Run the MCP server."""
    config = get_config()
    logger.info(f"Starting RememberMe MCP Server v{VERSION}")
    logger.info(f"Qdrant: {config.qdrant.host}:{config.qdrant.port}/{config.qdrant.collection_name}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
