#!/usr/bin/env python3
"""Test the SemanticSearchTool from agent tools to see if it finds embeddings in Neo4j."""

from rich.console import Console
from rich.table import Table
import json

from emdash.graph.connection import get_connection
from emdash.agent.tools.search import SemanticSearchTool, TextSearchTool, FindSimilarPRsTool

console = Console()


def main():
    query = "home page improver CMS entities index"
    
    console.print()
    console.print("[bold cyan]Testing Agent Semantic Search Tools[/bold cyan]")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print()
    
    # Connect to Neo4j
    connection = get_connection()
    connection.connect()
    
    # Test 1: SemanticSearchTool
    console.print("[bold]1. SemanticSearchTool (Vector Search)[/bold]")
    console.print("-" * 50)
    
    semantic_tool = SemanticSearchTool(connection)
    result = semantic_tool.execute(
        query=query,
        entity_types=["Function", "Class"],
        limit=15,
        min_score=0.3,
    )
    
    console.print(f"[bold]Success:[/bold] {result.success}")
    console.print(f"[bold]Error:[/bold] {result.error or 'None'}")
    
    if result.data:
        console.print(f"[bold]Count:[/bold] {result.data.get('count', 0)}")
        results = result.data.get("results", [])
        if results:
            table = Table(title="Semantic Search Results")
            table.add_column("Type", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Score", style="yellow")
            table.add_column("File Path", style="dim", max_width=40)
            
            for r in results[:10]:
                table.add_row(
                    r.get("type", ""),
                    r.get("name", ""),
                    f"{r.get('score', 0):.3f}",
                    (r.get("file_path", "") or "")[-40:],
                )
            console.print(table)
        else:
            console.print("[yellow]No results found[/yellow]")
    
    if result.suggestions:
        console.print("[bold]Suggestions:[/bold]")
        for s in result.suggestions:
            console.print(f"  - {s}")
    
    console.print()
    
    # Test 2: TextSearchTool (for comparison)
    console.print("[bold]2. TextSearchTool (Text Match)[/bold]")
    console.print("-" * 50)
    
    text_tool = TextSearchTool(connection)
    # Search for individual keywords
    for keyword in ["homepage", "improver", "CMS"]:
        result = text_tool.execute(
            query=keyword,
            entity_types=["Function", "Class"],
            limit=5,
        )
        
        console.print(f"[bold]Keyword: '{keyword}'[/bold] - Found: {result.data.get('count', 0)}")
        results = result.data.get("results", [])
        if results:
            for r in results[:3]:
                console.print(f"  • [{r.get('type')}] {r.get('name')}")
    
    console.print()
    
    # Test 3: FindSimilarPRsTool
    console.print("[bold]3. FindSimilarPRsTool (Vector Search on PRs)[/bold]")
    console.print("-" * 50)
    
    pr_tool = FindSimilarPRsTool(connection)
    result = pr_tool.execute(
        description=query,
        limit=10,
    )
    
    console.print(f"[bold]Success:[/bold] {result.success}")
    console.print(f"[bold]Error:[/bold] {result.error or 'None'}")
    
    if result.data:
        console.print(f"[bold]Count:[/bold] {result.data.get('count', 0)}")
        results = result.data.get("results", [])
        if results:
            table = Table(title="Similar PRs")
            table.add_column("PR #", style="cyan")
            table.add_column("Title", style="green", max_width=45)
            table.add_column("Score", style="yellow")
            table.add_column("State", style="dim")
            
            for pr in results[:10]:
                title = pr.get("title", "")
                if len(title) > 45:
                    title = title[:42] + "..."
                table.add_row(
                    str(pr.get("number", "")),
                    title,
                    f"{pr.get('score', 0):.3f}",
                    pr.get("state", ""),
                )
            console.print(table)
        else:
            console.print("[yellow]No PRs found[/yellow]")
    
    if result.suggestions:
        console.print("[bold]Suggestions:[/bold]")
        for s in result.suggestions:
            console.print(f"  - {s}")
    
    console.print()
    console.print("[bold green]✓ Agent tools test complete![/bold green]")
    console.print()
    
    # Summary
    console.print("[bold]Summary:[/bold]")
    console.print("  • Semantic search uses Neo4j vector index (requires embeddings)")
    console.print("  • Text search uses string matching (works without embeddings)")
    console.print("  • If semantic search returns 0 results, run: emdash embed index")


if __name__ == "__main__":
    main()

