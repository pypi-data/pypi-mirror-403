"""Get file dependencies tool - find imports and files that depend on a file."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_file_dependencies",
    description=(
        "Get the import relationships for a file - what it imports and what imports it. "
        "Use this to understand module dependencies."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file (can be partial path)",
            },
        },
        "required": ["file_path"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_file_dependencies tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with file_path.

    Returns:
        Result dict with imports, imported_by, and suggestions.
    """
    file_path = arguments["file_path"]

    try:
        # Get files this file imports
        imports_query = """
            MATCH (f:File)-[:IMPORTS]->(m:Module)
            WHERE f.path ENDS WITH $file_path
            RETURN m.name as module_name,
                   m.is_external as is_external
        """
        imports = connection.execute(imports_query, {"file_path": file_path})

        # Get files that import modules from this file - functions
        func_result = connection.execute("""
            MATCH (f:File)-[:CONTAINS_FUNCTION]->(entity:Function)
            WHERE f.path ENDS WITH $file_path
            WITH entity.qualified_name as qn
            MATCH (other:File)-[:IMPORTS]->(m:Module)
            WHERE m.name CONTAINS qn OR m.import_path CONTAINS qn
            RETURN DISTINCT other.path as file_path
        """, {"file_path": file_path})

        # Get files that import modules from this file - classes
        class_result = connection.execute("""
            MATCH (f:File)-[:CONTAINS_CLASS]->(entity:Class)
            WHERE f.path ENDS WITH $file_path
            WITH entity.qualified_name as qn
            MATCH (other:File)-[:IMPORTS]->(m:Module)
            WHERE m.name CONTAINS qn OR m.import_path CONTAINS qn
            RETURN DISTINCT other.path as file_path
        """, {"file_path": file_path})

        imported_by = list(set(
            [r["file_path"] for r in func_result] +
            [r["file_path"] for r in class_result]
        ))

        suggestions = []
        if imports:
            suggestions.append(
                f"Imports {len(imports)} modules. Check these for reusable functionality."
            )
        if imported_by:
            suggestions.append(
                f"Imported by {len(imported_by)} files. Changes here may affect them."
            )

        return {
            "file_path": file_path,
            "imports": imports,
            "imported_by": imported_by,
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
