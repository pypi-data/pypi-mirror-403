"""Graph traversal and analytics tools for MCP server."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection

# Traversal tools
from .expand_node import TOOL as EXPAND_NODE_TOOL, execute as expand_node_execute
from .get_callers import TOOL as GET_CALLERS_TOOL, execute as get_callers_execute
from .get_callees import TOOL as GET_CALLEES_TOOL, execute as get_callees_execute
from .get_class_hierarchy import TOOL as GET_CLASS_HIERARCHY_TOOL, execute as get_class_hierarchy_execute
from .get_file_dependencies import TOOL as GET_FILE_DEPENDENCIES_TOOL, execute as get_file_dependencies_execute
from .get_impact_analysis import TOOL as GET_IMPACT_ANALYSIS_TOOL, execute as get_impact_analysis_execute
from .get_neighbors import TOOL as GET_NEIGHBORS_TOOL, execute as get_neighbors_execute

# Analytics tools
from .get_area_importance import TOOL as GET_AREA_IMPORTANCE_TOOL, execute as get_area_importance_execute
from .get_top_pagerank import TOOL as GET_TOP_PAGERANK_TOOL, execute as get_top_pagerank_execute
from .get_communities import TOOL as GET_COMMUNITIES_TOOL, execute as get_communities_execute
from .get_community_members import TOOL as GET_COMMUNITY_MEMBERS_TOOL, execute as get_community_members_execute


TOOLS: dict[str, Tool] = {
    # Traversal
    "expand_node": EXPAND_NODE_TOOL,
    "get_callers": GET_CALLERS_TOOL,
    "get_callees": GET_CALLEES_TOOL,
    "get_class_hierarchy": GET_CLASS_HIERARCHY_TOOL,
    "get_file_dependencies": GET_FILE_DEPENDENCIES_TOOL,
    "get_impact_analysis": GET_IMPACT_ANALYSIS_TOOL,
    "get_neighbors": GET_NEIGHBORS_TOOL,
    # Analytics
    "get_area_importance": GET_AREA_IMPORTANCE_TOOL,
    "get_top_pagerank": GET_TOP_PAGERANK_TOOL,
    "get_communities": GET_COMMUNITIES_TOOL,
    "get_community_members": GET_COMMUNITY_MEMBERS_TOOL,
}

HANDLERS = {
    # Traversal
    "expand_node": expand_node_execute,
    "get_callers": get_callers_execute,
    "get_callees": get_callees_execute,
    "get_class_hierarchy": get_class_hierarchy_execute,
    "get_file_dependencies": get_file_dependencies_execute,
    "get_impact_analysis": get_impact_analysis_execute,
    "get_neighbors": get_neighbors_execute,
    # Analytics
    "get_area_importance": get_area_importance_execute,
    "get_top_pagerank": get_top_pagerank_execute,
    "get_communities": get_communities_execute,
    "get_community_members": get_community_members_execute,
}


async def execute_tool(connection: GraphConnection, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a tool by name.

    Args:
        connection: Graph database connection.
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        Tool result dictionary.

    Raises:
        ValueError: If tool name is not found.
    """
    handler = HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    return await handler(connection, arguments)
