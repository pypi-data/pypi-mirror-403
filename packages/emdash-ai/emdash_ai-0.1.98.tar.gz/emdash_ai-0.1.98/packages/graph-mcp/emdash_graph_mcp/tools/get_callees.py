"""Get callees tool - find all functions called by a specific function."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_callees",
    description=(
        "Find all functions called by a specific function. Use this to understand "
        "what dependencies a function has."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "qualified_name": {
                "type": "string",
                "description": "Qualified name of the function",
            },
        },
        "required": ["qualified_name"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_callees tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with qualified_name.

    Returns:
        Result dict with callees list and suggestions.
    """
    qualified_name = arguments["qualified_name"]

    query = """
        MATCH (f:Function {qualified_name: $qualified_name})-[:CALLS]->(callee:Function)
        RETURN callee.name as name,
               callee.qualified_name as qualified_name,
               callee.file_path as file_path,
               callee.is_method as is_method
        ORDER BY callee.name
    """

    try:
        callees = connection.execute(query, {"qualified_name": qualified_name})

        suggestions = []
        if callees:
            suggestions.append(f"This function calls {len(callees)} other functions.")
        else:
            suggestions.append(
                "No callees found. This is a leaf function with no dependencies."
            )

        return {
            "callees": callees,
            "count": len(callees),
            "suggestions": suggestions,
        }

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower():
            return {
                "error": "Code graph not available - codebase not indexed yet.",
                "suggestions": [
                    "Run 'emdash ingest <path>' to index the codebase first.",
                ],
            }
        return {"error": error_msg}
