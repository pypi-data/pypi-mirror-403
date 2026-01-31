"""Get communities tool - find code clusters/modules in the graph."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_communities",
    description=(
        "Get code communities (clusters) detected in the codebase. "
        "Communities are groups of closely related code entities. "
        "Useful for understanding code organization and module boundaries."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum communities to return (default: 10)",
                "default": 10,
            },
            "include_members": {
                "type": "boolean",
                "description": "Include sample member names in results (default: false)",
                "default": False,
            },
        },
        "required": [],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_communities tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with limit and include_members.

    Returns:
        Result dict with communities and their sizes.
    """
    limit = arguments.get("limit", 10)
    include_members = arguments.get("include_members", False)

    try:
        # Check if community property exists
        check_query = """
            MATCH (n)
            WHERE n.community IS NOT NULL
            RETURN count(n) AS cnt
        """
        check_result = connection.execute(check_query, {})
        has_communities = check_result and check_result[0]["cnt"] > 0

        if not has_communities:
            return {
                "communities": [],
                "count": 0,
                "note": "Community detection has not been run on this codebase.",
                "suggestions": [
                    "Run 'emdash analyze --communities' to detect code communities.",
                ],
            }

        # Get community sizes and sample members
        query = """
            MATCH (n)
            WHERE n.community IS NOT NULL
            WITH n.community AS community_id, collect(n.qualified_name) AS members
            RETURN community_id, size(members) AS size, members[0..5] AS sample_members
            ORDER BY size DESC
            LIMIT $limit
        """

        results = connection.execute(query, {"limit": limit})

        communities = []
        for r in results:
            comm = {
                "community_id": r["community_id"],
                "size": r["size"],
            }
            if include_members:
                comm["sample_members"] = [m for m in r.get("sample_members", []) if m]
            communities.append(comm)

        suggestions = []
        if communities:
            largest = communities[0]
            suggestions.append(
                f"Largest community ({largest['community_id']}) has {largest['size']} members. "
                "Use get_community_members to see all members."
            )
        else:
            suggestions.append("No communities detected.")

        return {
            "communities": communities,
            "count": len(communities),
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
