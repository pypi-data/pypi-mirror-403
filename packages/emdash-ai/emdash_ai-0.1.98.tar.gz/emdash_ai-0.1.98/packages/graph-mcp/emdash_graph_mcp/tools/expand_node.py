"""Expand node tool - get full context for a node."""

from typing import Any

from mcp.types import Tool

from ..connection import GraphConnection


TOOL = Tool(
    name="expand_node",
    description=(
        "Expand from a starting node to get its complete context including call graph, "
        "inheritance, and related entities. Use this after finding a relevant entity "
        "to understand its full context."
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
                "description": "Qualified name for Function/Class, or path for File",
            },
            "max_hops": {
                "type": "integer",
                "default": 2,
                "description": "Maximum relationship depth to traverse",
            },
        },
        "required": ["node_type", "identifier"],
    },
)


async def execute(connection: GraphConnection, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute expand_node tool.

    Args:
        connection: Graph database connection.
        arguments: Tool arguments.

    Returns:
        Result dict with expanded graph and suggestions.
    """
    node_type = arguments["node_type"]
    identifier = arguments["identifier"]
    max_hops = arguments.get("max_hops", 2)

    try:
        if node_type == "Function":
            return await _expand_function(connection, identifier, max_hops)
        elif node_type == "Class":
            return await _expand_class(connection, identifier, max_hops)
        elif node_type == "File":
            return await _expand_file(connection, identifier, max_hops)
        else:
            return {
                "error": f"Unknown node type: {node_type}",
                "suggestions": ["Use Function, Class, or File as node_type"],
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


async def _expand_function(connection: GraphConnection, qualified_name: str, max_hops: int) -> dict[str, Any]:
    """Expand from a function node."""
    # Get the root function
    result = connection.execute("""
        MATCH (f:Function {qualified_name: $qualified_name})
        OPTIONAL MATCH (f)<-[:CALLS]-(caller:Function)
        OPTIONAL MATCH (f)-[:CALLS]->(callee:Function)
        OPTIONAL MATCH (c:Class)-[:HAS_METHOD]->(f)
        OPTIONAL MATCH (file:File)-[:CONTAINS_FUNCTION]->(f)
        RETURN f as func,
               collect(DISTINCT caller) as callers,
               collect(DISTINCT callee) as callees,
               c as parent_class,
               file
    """, {"qualified_name": qualified_name})

    if not result:
        return {"error": f"Function not found: {qualified_name}"}

    record = result[0]
    func = record.get("func") or {}
    callers = [c for c in (record.get("callers") or []) if c]
    callees = [c for c in (record.get("callees") or []) if c]
    parent_class = record.get("parent_class")
    file_node = record.get("file")

    # Build root node
    root_node = {
        "type": "Function",
        "name": func.get("name"),
        "qualified_name": func.get("qualified_name"),
        "file_path": func.get("file_path"),
        "docstring": func.get("docstring"),
        "line_start": func.get("line_start"),
        "line_end": func.get("line_end"),
    }

    # Build call graph
    call_graph = []
    for caller in callers:
        call_graph.append({
            "caller": caller.get("name"),
            "caller_qualified": caller.get("qualified_name"),
            "callee": func.get("name"),
            "callee_qualified": func.get("qualified_name"),
        })
    for callee in callees:
        call_graph.append({
            "caller": func.get("name"),
            "caller_qualified": func.get("qualified_name"),
            "callee": callee.get("name"),
            "callee_qualified": callee.get("qualified_name"),
        })

    # Collect functions
    functions = [root_node]
    for c in callers + callees:
        functions.append({
            "name": c.get("name"),
            "qualified_name": c.get("qualified_name"),
            "file_path": c.get("file_path"),
            "docstring": c.get("docstring"),
        })

    # Collect classes
    classes = []
    inheritance = []
    if parent_class:
        classes.append({
            "name": parent_class.get("name"),
            "qualified_name": parent_class.get("qualified_name"),
            "file_path": parent_class.get("file_path"),
            "docstring": parent_class.get("docstring"),
        })
        inheritance = _get_class_hierarchy(connection, parent_class.get("qualified_name"))

    # Collect files
    files = []
    if file_node:
        files.append({
            "path": file_node.get("path"),
            "name": file_node.get("name"),
        })

    suggestions = []
    if call_graph:
        suggestions.append(
            f"Found {len(call_graph)} call relationships. "
            "Use get_callers or get_callees for deeper analysis."
        )
    if classes:
        suggestions.append(
            f"Found {len(classes)} related classes. "
            "Use get_class_hierarchy to explore inheritance."
        )

    return {
        "root_node": root_node,
        "functions": functions,
        "classes": classes,
        "files": files,
        "call_graph": call_graph[:50],
        "inheritance": inheritance,
        "imports": [],
        "summary": {
            "function_count": len(functions),
            "class_count": len(classes),
            "file_count": len(files),
            "call_count": len(call_graph),
        },
        "suggestions": suggestions,
    }


async def _expand_class(connection: GraphConnection, qualified_name: str, max_hops: int) -> dict[str, Any]:
    """Expand from a class node."""
    result = connection.execute("""
        MATCH (c:Class {qualified_name: $qualified_name})
        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Function)
        OPTIONAL MATCH (c)-[:INHERITS_FROM]->(parent:Class)
        OPTIONAL MATCH (child:Class)-[:INHERITS_FROM]->(c)
        OPTIONAL MATCH (file:File)-[:CONTAINS_CLASS]->(c)
        RETURN c as cls,
               collect(DISTINCT m) as methods,
               collect(DISTINCT parent) as parents,
               collect(DISTINCT child) as children,
               file
    """, {"qualified_name": qualified_name})

    if not result:
        return {"error": f"Class not found: {qualified_name}"}

    record = result[0]
    cls = record.get("cls") or {}
    methods = [m for m in (record.get("methods") or []) if m]
    parents = [p for p in (record.get("parents") or []) if p]
    children = [c for c in (record.get("children") or []) if c]
    file_node = record.get("file")

    # Build root node
    root_node = {
        "type": "Class",
        "name": cls.get("name"),
        "qualified_name": cls.get("qualified_name"),
        "file_path": cls.get("file_path"),
        "docstring": cls.get("docstring"),
    }

    # Build classes list
    classes = [root_node]
    for p in parents:
        classes.append({
            "name": p.get("name"),
            "qualified_name": p.get("qualified_name"),
            "file_path": p.get("file_path"),
            "docstring": p.get("docstring"),
        })
    for c in children:
        classes.append({
            "name": c.get("name"),
            "qualified_name": c.get("qualified_name"),
            "file_path": c.get("file_path"),
            "docstring": c.get("docstring"),
        })

    # Build inheritance
    inheritance = []
    for p in parents:
        inheritance.append({
            "child": cls.get("name"),
            "child_qualified": cls.get("qualified_name"),
            "parent": p.get("name"),
            "parent_qualified": p.get("qualified_name"),
        })
    for c in children:
        inheritance.append({
            "child": c.get("name"),
            "child_qualified": c.get("qualified_name"),
            "parent": cls.get("name"),
            "parent_qualified": cls.get("qualified_name"),
        })

    # Build functions list from methods
    functions = []
    for m in methods:
        functions.append({
            "name": m.get("name"),
            "qualified_name": m.get("qualified_name"),
            "file_path": m.get("file_path"),
            "docstring": m.get("docstring"),
        })

    # Collect files
    files = []
    if file_node:
        files.append({
            "path": file_node.get("path"),
            "name": file_node.get("name"),
        })

    suggestions = []
    if methods:
        suggestions.append(f"Found {len(methods)} methods in this class.")
    if parents or children:
        suggestions.append(
            f"Inheritance: {len(parents)} parents, {len(children)} children."
        )

    return {
        "root_node": root_node,
        "functions": functions,
        "classes": classes,
        "files": files,
        "call_graph": [],
        "inheritance": inheritance,
        "imports": [],
        "summary": {
            "function_count": len(functions),
            "class_count": len(classes),
            "file_count": len(files),
            "call_count": 0,
        },
        "suggestions": suggestions,
    }


async def _expand_file(connection: GraphConnection, file_path: str, max_hops: int) -> dict[str, Any]:
    """Expand from a file node."""
    result = connection.execute("""
        MATCH (f:File)
        WHERE f.path ENDS WITH $file_path OR f.path = $file_path
        OPTIONAL MATCH (f)-[:CONTAINS_CLASS]->(cls:Class)
        OPTIONAL MATCH (f)-[:CONTAINS_FUNCTION]->(func:Function)
        OPTIONAL MATCH (f)-[:IMPORTS]->(m:Module)
        RETURN f as file,
               collect(DISTINCT cls) as classes,
               collect(DISTINCT func) as functions,
               collect(DISTINCT m) as imports
    """, {"file_path": file_path})

    if not result:
        return {"error": f"File not found: {file_path}"}

    record = result[0]
    file_node = record.get("file") or {}
    file_classes = [c for c in (record.get("classes") or []) if c]
    file_functions = [f for f in (record.get("functions") or []) if f]
    file_imports = [m for m in (record.get("imports") or []) if m]

    # Build root node
    root_node = {
        "type": "File",
        "name": file_node.get("name"),
        "path": file_node.get("path"),
    }

    # Build classes list
    classes = []
    for c in file_classes:
        classes.append({
            "name": c.get("name"),
            "qualified_name": c.get("qualified_name"),
            "file_path": c.get("file_path"),
            "docstring": c.get("docstring"),
        })

    # Build functions list
    functions = []
    for f in file_functions:
        functions.append({
            "name": f.get("name"),
            "qualified_name": f.get("qualified_name"),
            "file_path": f.get("file_path"),
            "docstring": f.get("docstring"),
        })

    # Build imports list
    imports = []
    for m in file_imports:
        imports.append({
            "module": m.get("name"),
            "is_external": m.get("is_external", False),
        })

    # Files list
    files = [{
        "path": file_node.get("path"),
        "name": file_node.get("name"),
    }]

    suggestions = []
    if functions:
        suggestions.append(f"Contains {len(functions)} functions.")
    if classes:
        suggestions.append(f"Contains {len(classes)} classes.")
    if imports:
        suggestions.append(f"Imports {len(imports)} modules.")

    return {
        "root_node": root_node,
        "functions": functions,
        "classes": classes,
        "files": files,
        "call_graph": [],
        "inheritance": [],
        "imports": imports,
        "summary": {
            "function_count": len(functions),
            "class_count": len(classes),
            "file_count": len(files),
            "call_count": 0,
        },
        "suggestions": suggestions,
    }


def _get_class_hierarchy(connection: GraphConnection, qualified_name: str) -> list[dict[str, Any]]:
    """Get inheritance hierarchy for a class."""
    inheritance = []

    # Get ancestors
    result = connection.execute("""
        MATCH (c:Class {qualified_name: $qualified_name})
        OPTIONAL MATCH (c)-[:INHERITS_FROM*1..3]->(ancestor:Class)
        WITH c, collect(DISTINCT ancestor) as ancestors
        UNWIND ancestors as a
        RETURN c.name as child, a.name as parent
    """, {"qualified_name": qualified_name})

    for record in result:
        if record.get("child") and record.get("parent"):
            inheritance.append({
                "child": record["child"],
                "parent": record["parent"],
            })

    # Get descendants
    result = connection.execute("""
        MATCH (c:Class {qualified_name: $qualified_name})
        OPTIONAL MATCH (descendant:Class)-[:INHERITS_FROM*1..3]->(c)
        WITH c, collect(DISTINCT descendant) as descendants
        UNWIND descendants as d
        RETURN d.name as child, c.name as parent
    """, {"qualified_name": qualified_name})

    for record in result:
        if record.get("child") and record.get("parent"):
            inheritance.append({
                "child": record["child"],
                "parent": record["parent"],
            })

    return inheritance
