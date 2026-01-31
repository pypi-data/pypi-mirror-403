"""MCP server for emdash graph traversal tools."""

import argparse
import asyncio
import json
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .connection import GraphConnection
from .tools import TOOLS, execute_tool


def create_server(db_path: str, server_url: Optional[str] = None) -> tuple[Server, GraphConnection]:
    """Create MCP server with graph tools.

    Args:
        db_path: Path to Kuzu database directory.
        server_url: Optional emdash server URL for HTTP proxy mode.

    Returns:
        Tuple of (Server, GraphConnection).
    """
    server = Server("emdash-graph")
    connection = GraphConnection(db_path, server_url=server_url)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available graph traversal tools."""
        return list(TOOLS.values())

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Execute a graph traversal tool."""
        result = await execute_tool(connection, name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    return server, connection


async def run_server(db_path: str, server_url: Optional[str] = None):
    """Run the MCP server with stdio transport.

    Args:
        db_path: Path to Kuzu database directory.
        server_url: Optional emdash server URL for HTTP proxy mode.
    """
    server, connection = create_server(db_path, server_url=server_url)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EmDash Graph MCP Server - Graph traversal tools over Kuzu"
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to Kuzu database directory (e.g., .emdash/kuzu_db)",
    )
    parser.add_argument(
        "--server-url",
        help="Optional emdash server URL (e.g., http://localhost:8765). "
             "If provided, queries will be proxied through the server to avoid DB locks. "
             "If not provided, will attempt to auto-discover from port file.",
    )
    args = parser.parse_args()

    asyncio.run(run_server(args.db_path, server_url=args.server_url))


if __name__ == "__main__":
    main()
