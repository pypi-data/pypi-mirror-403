"""Get area importance tool - find most important directories by file count."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_area_importance",
    description=(
        "Get importance metrics for areas of the codebase. "
        "Shows which directories have the most files and code entities. "
        "Useful for understanding code organization and finding hot spots."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of areas to return (default: 15)",
                "default": 15,
            },
        },
        "required": [],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_area_importance tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with limit.

    Returns:
        Result dict with areas and their metrics.
    """
    limit = arguments.get("limit", 15)

    # Get files and their directories
    # We'll process directories in Python since complex string ops in Kuzu can be tricky
    query = """
        MATCH (f:File)
        WHERE f.file_path IS NOT NULL
        RETURN f.file_path AS file_path
    """

    try:
        results = connection.execute(query, {})

        # Process directories in Python
        dir_counts: dict[str, int] = {}
        for r in results:
            path = r["file_path"]
            if "/" in path:
                # Get parent directory (remove filename)
                parts = path.rsplit("/", 1)
                if len(parts) > 1:
                    directory = parts[0]
                    # Also count parent directories for hierarchy
                    dir_counts[directory] = dir_counts.get(directory, 0) + 1
            else:
                dir_counts["."] = dir_counts.get(".", 0) + 1

        # Sort by count and limit
        sorted_dirs = sorted(dir_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        areas = [
            {"directory": d, "file_count": c}
            for d, c in sorted_dirs
        ]

        suggestions = []
        if areas:
            top_dir = areas[0]["directory"]
            suggestions.append(
                f"Top area is '{top_dir}' with {areas[0]['file_count']} files. "
                "Use get_file_dependencies to explore relationships."
            )
        else:
            suggestions.append(
                "No areas found. Make sure the codebase has been indexed."
            )

        return {
            "areas": areas,
            "count": len(areas),
            "suggestions": suggestions,
        }

    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
            return {
                "error": "Code graph not available - codebase not indexed yet.",
                "suggestions": [
                    "Run 'emdash index <path>' to index the codebase first.",
                ],
            }
        return {"error": error_msg}
