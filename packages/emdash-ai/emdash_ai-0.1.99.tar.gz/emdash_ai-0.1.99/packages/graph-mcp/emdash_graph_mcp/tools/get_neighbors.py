"""Get neighbors tool - find immediate neighbors of any node."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_neighbors",
    description=(
        "Get immediate neighbors of a node via specific relationship types. "
        "Use this for flexible graph exploration."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "node_type": {
                "type": "string",
                "enum": ["Function", "Class", "File"],
                "description": "Type of the starting node",
            },
            "identifier": {
                "type": "string",
                "description": "Qualified name, path, or name of the node",
            },
            "relationship_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["CALLS", "INHERITS_FROM", "CONTAINS_FUNCTION", "CONTAINS_CLASS", "HAS_METHOD", "IMPORTS"],
                },
                "description": "Types of relationships to traverse",
            },
            "direction": {
                "type": "string",
                "enum": ["in", "out", "both"],
                "default": "both",
                "description": "Direction to traverse",
            },
            "limit": {
                "type": "integer",
                "default": 50,
                "description": "Maximum number of neighbors",
            },
        },
        "required": ["node_type", "identifier"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_neighbors tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments.

    Returns:
        Result dict with neighbors and suggestions.
    """
    node_type = arguments["node_type"]
    identifier = arguments["identifier"]
    relationship_types = arguments.get(
        "relationship_types",
        ["CALLS", "INHERITS_FROM", "CONTAINS_FUNCTION", "CONTAINS_CLASS", "HAS_METHOD"],
    )
    direction = arguments.get("direction", "both")
    limit = arguments.get("limit", 50)

    try:
        neighbors = []
        seen = set()

        # Build identifier match based on node type
        if node_type == "File":
            id_match = "(n.path = $identifier OR n.path ENDS WITH $identifier)"
        else:
            id_match = "(n.qualified_name = $identifier OR n.name = $identifier)"

        # Query each relationship type separately (Kuzu doesn't support | in rel types)
        for rel_type in relationship_types:
            if len(neighbors) >= limit:
                break

            remaining = limit - len(neighbors)

            # Build queries based on direction
            queries = []
            if direction in ("out", "both"):
                queries.append(f"""
                    MATCH (n:{node_type})-[:{rel_type}]->(neighbor)
                    WHERE {id_match}
                    RETURN DISTINCT
                        label(neighbor) as type,
                        neighbor.name as name,
                        COALESCE(neighbor.qualified_name, neighbor.path) as qualified_name,
                        COALESCE(neighbor.file_path, neighbor.path) as file_path
                    LIMIT $limit
                """)

            if direction in ("in", "both"):
                queries.append(f"""
                    MATCH (neighbor)-[:{rel_type}]->(n:{node_type})
                    WHERE {id_match}
                    RETURN DISTINCT
                        label(neighbor) as type,
                        neighbor.name as name,
                        COALESCE(neighbor.qualified_name, neighbor.path) as qualified_name,
                        COALESCE(neighbor.file_path, neighbor.path) as file_path
                    LIMIT $limit
                """)

            for query in queries:
                if len(neighbors) >= limit:
                    break
                try:
                    results = connection.execute(
                        query,
                        {"identifier": identifier, "limit": remaining},
                    )
                    for r in results:
                        # Deduplicate by qualified_name
                        key = r.get("qualified_name") or r.get("name")
                        if key and key not in seen:
                            seen.add(key)
                            r["relationship"] = rel_type
                            neighbors.append(r)
                            if len(neighbors) >= limit:
                                break
                except Exception:
                    # Skip relationship types that don't exist
                    continue

        suggestions = []
        if neighbors:
            by_type = {}
            for n in neighbors:
                t = n.get("type", "Unknown")
                by_type[t] = by_type.get(t, 0) + 1

            type_summary = ", ".join(f"{v} {k}s" for k, v in by_type.items())
            suggestions.append(f"Found: {type_summary}")
        else:
            suggestions.append(
                "No neighbors found. Try different relationship types or check the identifier."
            )

        return {
            "node_type": node_type,
            "identifier": identifier,
            "neighbors": neighbors,
            "count": len(neighbors),
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
