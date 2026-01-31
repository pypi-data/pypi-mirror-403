"""Get community members tool - list all members of a specific community."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_community_members",
    description=(
        "Get all members of a specific code community. "
        "Use this after get_communities to explore what code belongs to a cluster."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "community_id": {
                "type": "integer",
                "description": "The community ID to get members for",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum members to return (default: 50)",
                "default": 50,
            },
        },
        "required": ["community_id"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_community_members tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with community_id and limit.

    Returns:
        Result dict with community members.
    """
    community_id = arguments["community_id"]
    limit = arguments.get("limit", 50)

    # Query for members of the specified community
    # We query each node type separately to get the type info
    queries = [
        ("Function", """
            MATCH (n:Function)
            WHERE n.community = $community_id
            RETURN n.qualified_name AS qualified_name,
                   n.name AS name,
                   n.file_path AS file_path,
                   'Function' AS node_type
            LIMIT $limit
        """),
        ("Class", """
            MATCH (n:Class)
            WHERE n.community = $community_id
            RETURN n.qualified_name AS qualified_name,
                   n.name AS name,
                   n.file_path AS file_path,
                   'Class' AS node_type
            LIMIT $limit
        """),
        ("File", """
            MATCH (n:File)
            WHERE n.community = $community_id
            RETURN n.file_path AS qualified_name,
                   n.file_path AS name,
                   n.file_path AS file_path,
                   'File' AS node_type
            LIMIT $limit
        """),
    ]

    try:
        members = []
        for node_type, query in queries:
            try:
                results = connection.execute(query, {"community_id": community_id, "limit": limit})
                for r in results:
                    members.append({
                        "qualified_name": r.get("qualified_name") or r.get("name"),
                        "name": r.get("name"),
                        "file_path": r.get("file_path"),
                        "node_type": r.get("node_type", node_type),
                    })
            except Exception:
                # Skip if node type doesn't exist
                continue

        # Sort by node type and name
        members.sort(key=lambda x: (x["node_type"], x["name"] or ""))

        # Limit total results
        members = members[:limit]

        suggestions = []
        if members:
            # Count by type
            type_counts = {}
            for m in members:
                t = m["node_type"]
                type_counts[t] = type_counts.get(t, 0) + 1
            type_summary = ", ".join(f"{c} {t}s" for t, c in type_counts.items())
            suggestions.append(
                f"Community {community_id} contains: {type_summary}. "
                "Use expand_node to explore any member."
            )
        else:
            suggestions.append(
                f"No members found for community {community_id}. "
                "Use get_communities to see available communities."
            )

        return {
            "community_id": community_id,
            "members": members,
            "count": len(members),
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
