"""Get impact analysis tool - analyze potential impact of changing a file."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_impact_analysis",
    description=(
        "Analyze the potential impact of changing a file. Shows affected functions, "
        "dependent files, and risk level. Use this before making changes."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to analyze",
            },
        },
        "required": ["file_path"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_impact_analysis tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with file_path.

    Returns:
        Result dict with impact analysis and suggestions.
    """
    file_path = arguments["file_path"]

    try:
        # Get functions in this file and their callers
        callers_result = connection.execute("""
            MATCH (f:File)-[:CONTAINS_FUNCTION]->(func:Function)
            WHERE f.path ENDS WITH $file_path
            OPTIONAL MATCH (caller:Function)-[:CALLS]->(func)
            RETURN func.name as function_name,
                   func.qualified_name as qualified_name,
                   collect(DISTINCT caller.qualified_name) as called_by
        """, {"file_path": file_path})

        functions_impact = []
        total_callers = set()
        for r in callers_result:
            callers = [c for c in r["called_by"] if c is not None]
            total_callers.update(callers)
            functions_impact.append({
                "name": r["function_name"],
                "qualified_name": r["qualified_name"],
                "caller_count": len(callers),
            })

        # Get exported names
        func_names = connection.execute("""
            MATCH (f:File)-[:CONTAINS_FUNCTION]->(entity:Function)
            WHERE f.path ENDS WITH $file_path
            RETURN DISTINCT entity.name as name
        """, {"file_path": file_path})

        class_names = connection.execute("""
            MATCH (f:File)-[:CONTAINS_CLASS]->(entity:Class)
            WHERE f.path ENDS WITH $file_path
            RETURN DISTINCT entity.name as name
        """, {"file_path": file_path})

        exported_names = [r["name"] for r in func_names] + [r["name"] for r in class_names]

        # Find files that import these names
        dependent_files = []
        if exported_names:
            dependents_result = connection.execute("""
                MATCH (other:File)-[:IMPORTS]->(m:Module)
                WHERE any(name IN $exported_names WHERE m.name CONTAINS name)
                RETURN DISTINCT other.path as file_path
            """, {"exported_names": exported_names})
            dependent_files = [r["file_path"] for r in dependents_result]

        # Calculate risk level
        caller_count = len(total_callers)
        if caller_count > 10:
            risk_level = "high"
        elif caller_count > 3:
            risk_level = "medium"
        else:
            risk_level = "low"

        suggestions = []
        if risk_level == "high":
            suggestions.append("High risk: This file has many dependents. Test thoroughly!")
        elif risk_level == "medium":
            suggestions.append("Medium risk: Some dependents will be affected.")
        else:
            suggestions.append("Low risk: Limited impact expected.")

        if caller_count > 0:
            suggestions.append(f"Functions in this file are called {caller_count} times.")

        return {
            "file_path": file_path,
            "functions": functions_impact,
            "total_callers": caller_count,
            "dependent_files": dependent_files,
            "risk_level": risk_level,
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
