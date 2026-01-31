"""Get class hierarchy tool - find inheritance relationships."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_class_hierarchy",
    description=(
        "Get the inheritance tree for a class, including parent classes and child classes. "
        "Use this to understand class relationships and polymorphism."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "Class name or qualified name",
            },
        },
        "required": ["class_name"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_class_hierarchy tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with class_name.

    Returns:
        Result dict with parents, children, and suggestions.
    """
    class_name = arguments["class_name"]

    try:
        # Get parent classes
        parents_query = """
            MATCH (c:Class)-[:INHERITS_FROM]->(parent:Class)
            WHERE c.name = $class_name OR c.qualified_name = $class_name
            RETURN parent.name as name,
                   parent.qualified_name as qualified_name,
                   parent.file_path as file_path
        """
        parents = connection.execute(parents_query, {"class_name": class_name})

        # Get child classes
        children_query = """
            MATCH (child:Class)-[:INHERITS_FROM]->(c:Class)
            WHERE c.name = $class_name OR c.qualified_name = $class_name
            RETURN child.name as name,
                   child.qualified_name as qualified_name,
                   child.file_path as file_path
        """
        children = connection.execute(children_query, {"class_name": class_name})

        suggestions = []
        if parents:
            suggestions.append(
                f"Inherits from {len(parents)} parent class(es). "
                "Check parent classes for shared functionality."
            )
        if children:
            suggestions.append(
                f"Has {len(children)} child class(es). "
                "These override or extend this class."
            )

        return {
            "class_name": class_name,
            "parents": parents,
            "children": children,
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
