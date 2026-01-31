"""Get callers tool - find all functions that call a specific function."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_callers",
    description=(
        "Find all functions that call a specific function. Use this to understand "
        "who depends on this function and how it's used."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "qualified_name": {
                "type": "string",
                "description": "Qualified name of the function (e.g., 'module.Class.method')",
            },
        },
        "required": ["qualified_name"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_callers tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with qualified_name.

    Returns:
        Result dict with callers list and suggestions.
    """
    qualified_name = arguments["qualified_name"]

    query = """
        MATCH (caller:Function)-[:CALLS]->(f:Function {qualified_name: $qualified_name})
        RETURN caller.name as name,
               caller.qualified_name as qualified_name,
               caller.file_path as file_path,
               caller.is_method as is_method
        ORDER BY caller.name
    """

    try:
        callers = connection.execute(query, {"qualified_name": qualified_name})

        suggestions = []
        if callers:
            suggestions.append(
                f"Found {len(callers)} callers. Use expand_node to explore any of them."
            )
        else:
            suggestions.append(
                "No callers found. This might be an entry point or unused function."
            )

        return {
            "callers": callers,
            "count": len(callers),
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
