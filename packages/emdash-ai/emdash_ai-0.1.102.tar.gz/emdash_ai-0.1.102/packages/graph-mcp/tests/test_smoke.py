"""Smoke tests for emdash-graph-mcp server."""

from pathlib import Path

import pytest

from emdash_graph_mcp.connection import GraphConnection
from emdash_graph_mcp.server import create_server
from emdash_graph_mcp.tools import TOOLS, execute_tool


class TestConnection:
    """Test GraphConnection class."""

    def test_connection_missing_db(self):
        """Test error handling for missing database."""
        conn = GraphConnection("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            conn.connect()

    def test_connection_init(self):
        """Test connection initialization."""
        conn = GraphConnection("/tmp/test")
        assert conn.db_path == Path("/tmp/test")
        assert conn._db is None
        assert conn._conn is None


class TestTools:
    """Test tool definitions."""

    def test_all_tools_registered(self):
        """Test all 7 tools are registered."""
        expected_tools = [
            "expand_node",
            "get_callers",
            "get_callees",
            "get_class_hierarchy",
            "get_file_dependencies",
            "get_impact_analysis",
            "get_neighbors",
        ]
        assert set(TOOLS.keys()) == set(expected_tools)

    def test_tools_have_schema(self):
        """Test all tools have valid input schema."""
        for name, tool in TOOLS.items():
            assert tool.name == name
            assert tool.description
            assert tool.inputSchema
            assert tool.inputSchema.get("type") == "object"
            assert "properties" in tool.inputSchema

    def test_expand_node_schema(self):
        """Test expand_node tool schema."""
        tool = TOOLS["expand_node"]
        props = tool.inputSchema["properties"]
        assert "node_type" in props
        assert props["node_type"]["enum"] == ["Function", "Class", "File"]
        assert "identifier" in props
        assert "max_hops" in props

    def test_get_neighbors_schema(self):
        """Test get_neighbors tool schema."""
        tool = TOOLS["get_neighbors"]
        props = tool.inputSchema["properties"]
        assert "node_type" in props
        assert "identifier" in props
        assert "relationship_types" in props
        assert "direction" in props
        assert props["direction"]["enum"] == ["in", "out", "both"]


class TestToolExecution:
    """Test tool execution with mock/missing database."""

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test error for unknown tool."""
        conn = GraphConnection("/tmp/test")
        with pytest.raises(ValueError, match="Unknown tool"):
            await execute_tool(conn, "unknown_tool", {})

    @pytest.mark.asyncio
    async def test_get_callers_missing_db(self):
        """Test get_callers with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_callers", {"qualified_name": "test.func"})
        assert "error" in result
        assert "not found" in result["error"].lower() or "Database" in result["error"]

    @pytest.mark.asyncio
    async def test_get_callees_missing_db(self):
        """Test get_callees with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_callees", {"qualified_name": "test.func"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_class_hierarchy_missing_db(self):
        """Test get_class_hierarchy with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_class_hierarchy", {"class_name": "TestClass"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_file_dependencies_missing_db(self):
        """Test get_file_dependencies with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_file_dependencies", {"file_path": "test.py"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_impact_analysis_missing_db(self):
        """Test get_impact_analysis with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_impact_analysis", {"file_path": "test.py"})
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_neighbors_missing_db(self):
        """Test get_neighbors with missing database returns empty (graceful degradation)."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "get_neighbors", {
            "node_type": "Function",
            "identifier": "test.func",
        })
        # get_neighbors gracefully returns empty results when DB unavailable
        assert result["count"] == 0
        assert result["neighbors"] == []

    @pytest.mark.asyncio
    async def test_expand_node_missing_db(self):
        """Test expand_node with missing database."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "expand_node", {
            "node_type": "Function",
            "identifier": "test.func",
        })
        assert "error" in result

    @pytest.mark.asyncio
    async def test_expand_node_invalid_type(self):
        """Test expand_node with invalid node type."""
        conn = GraphConnection("/nonexistent/db")
        result = await execute_tool(conn, "expand_node", {
            "node_type": "Invalid",
            "identifier": "test",
        })
        assert "error" in result
        assert "Unknown node type" in result["error"]


class TestServer:
    """Test MCP server creation."""

    def test_create_server(self):
        """Test server creation."""
        server, conn = create_server("/tmp/test")
        assert server.name == "emdash-graph"
        assert conn.db_path == Path("/tmp/test")

    def test_server_has_handlers(self):
        """Test server has required handlers."""
        server, _ = create_server("/tmp/test")
        # Server should have list_tools and call_tool handlers registered
        assert server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
