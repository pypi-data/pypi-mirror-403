"""Get top PageRank tool - find most central/important code entities."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="get_top_pagerank",
    description=(
        "Get the most central/important code entities by connectivity. "
        "Identifies code that is most connected and depended upon. "
        "High-ranking entities are often critical infrastructure. "
        "Falls back to degree centrality if PageRank not computed."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["Function", "Class", "File", "all"],
                "description": "Type of entity to analyze (default: all)",
                "default": "all",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 10)",
                "default": 10,
            },
        },
        "required": [],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute get_top_pagerank tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments with entity_type and limit.

    Returns:
        Result dict with top entities by centrality.
    """
    entity_type = arguments.get("entity_type", "all")
    limit = arguments.get("limit", 10)

    try:
        # First check if pagerank property exists
        check_query = """
            MATCH (n)
            WHERE n.pagerank IS NOT NULL
            RETURN count(n) AS cnt
        """
        check_result = connection.execute(check_query, {})
        has_pagerank = check_result and check_result[0]["cnt"] > 0

        if has_pagerank:
            # Use PageRank
            if entity_type == "all":
                query = """
                    MATCH (n)
                    WHERE n.pagerank IS NOT NULL
                    RETURN n.qualified_name AS qualified_name,
                           n.name AS name,
                           n.file_path AS file_path,
                           n.pagerank AS score
                    ORDER BY n.pagerank DESC
                    LIMIT $limit
                """
            else:
                query = f"""
                    MATCH (n:{entity_type})
                    WHERE n.pagerank IS NOT NULL
                    RETURN n.qualified_name AS qualified_name,
                           n.name AS name,
                           n.file_path AS file_path,
                           n.pagerank AS score
                    ORDER BY n.pagerank DESC
                    LIMIT $limit
                """
            metric = "pagerank"
        else:
            # Fall back to degree centrality (count of relationships)
            if entity_type == "all":
                # Query functions by call count
                query = """
                    MATCH (f:Function)
                    OPTIONAL MATCH (f)<-[:CALLS]-(caller:Function)
                    WITH f, count(caller) AS in_degree
                    WHERE in_degree > 0
                    RETURN f.qualified_name AS qualified_name,
                           f.name AS name,
                           f.file_path AS file_path,
                           in_degree AS score
                    ORDER BY in_degree DESC
                    LIMIT $limit
                """
            elif entity_type == "Function":
                query = """
                    MATCH (f:Function)
                    OPTIONAL MATCH (f)<-[:CALLS]-(caller:Function)
                    WITH f, count(caller) AS in_degree
                    WHERE in_degree > 0
                    RETURN f.qualified_name AS qualified_name,
                           f.name AS name,
                           f.file_path AS file_path,
                           in_degree AS score
                    ORDER BY in_degree DESC
                    LIMIT $limit
                """
            elif entity_type == "Class":
                query = """
                    MATCH (c:Class)
                    OPTIONAL MATCH (c)<-[:INHERITS]-(child:Class)
                    OPTIONAL MATCH (c)-[:CONTAINS]->(m:Function)
                    WITH c, count(DISTINCT child) + count(DISTINCT m) AS score
                    WHERE score > 0
                    RETURN c.qualified_name AS qualified_name,
                           c.name AS name,
                           c.file_path AS file_path,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                """
            else:  # File
                query = """
                    MATCH (f:File)
                    OPTIONAL MATCH (f)-[:CONTAINS]->(entity)
                    WITH f, count(entity) AS score
                    RETURN f.file_path AS qualified_name,
                           f.file_path AS name,
                           f.file_path AS file_path,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                """
            metric = "degree"

        results = connection.execute(query, {"limit": limit})

        entities = [
            {
                "qualified_name": r.get("qualified_name") or r.get("name"),
                "name": r.get("name"),
                "file_path": r.get("file_path"),
                "score": r.get("score", 0),
            }
            for r in results
        ]

        suggestions = []
        if entities:
            top = entities[0]
            suggestions.append(
                f"Most central: '{top['name']}' with {metric} score {top['score']}. "
                "Use expand_node or get_callers to explore."
            )
        else:
            suggestions.append(
                "No entities found. Make sure the codebase has been indexed."
            )

        return {
            "entities": entities,
            "count": len(entities),
            "metric": metric,
            "note": None if has_pagerank else "PageRank not computed, using degree centrality",
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
