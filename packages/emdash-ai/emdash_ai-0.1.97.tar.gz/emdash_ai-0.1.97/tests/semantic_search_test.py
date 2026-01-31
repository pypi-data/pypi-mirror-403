#!/usr/bin/env python3
"""Script to search for semantic query and report results."""

from rich.console import Console
from rich.table import Table

from emdash.graph.connection import get_connection
from emdash.planning.similarity import SimilaritySearch

console = Console()


def text_search_code(connection, keywords: list[str], limit: int = 20) -> list[dict]:
    """Text-based search for code entities using keywords."""
    results = []
    
    with connection.session() as session:
        for keyword in keywords:
            # Search functions
            result = session.run("""
                MATCH (f:Function)
                WHERE toLower(f.name) CONTAINS toLower($kw)
                   OR toLower(f.docstring) CONTAINS toLower($kw)
                   OR toLower(f.qualified_name) CONTAINS toLower($kw)
                RETURN 'Function' as type,
                       f.name as name,
                       f.qualified_name as qualified_name,
                       f.docstring as docstring,
                       f.file_path as file_path,
                       $kw as matched_keyword
                LIMIT $limit
            """, kw=keyword, limit=limit)
            results.extend([dict(r) for r in result])
            
            # Search classes
            result = session.run("""
                MATCH (c:Class)
                WHERE toLower(c.name) CONTAINS toLower($kw)
                   OR toLower(c.docstring) CONTAINS toLower($kw)
                   OR toLower(c.qualified_name) CONTAINS toLower($kw)
                RETURN 'Class' as type,
                       c.name as name,
                       c.qualified_name as qualified_name,
                       c.docstring as docstring,
                       c.file_path as file_path,
                       $kw as matched_keyword
                LIMIT $limit
            """, kw=keyword, limit=limit)
            results.extend([dict(r) for r in result])
    
    # Deduplicate by qualified_name
    seen = set()
    unique_results = []
    for r in results:
        qn = r.get("qualified_name", "")
        if qn not in seen:
            seen.add(qn)
            unique_results.append(r)
    
    return unique_results[:limit]


def text_search_prs(connection, keywords: list[str], limit: int = 20) -> list[dict]:
    """Text-based search for PRs using keywords."""
    results = []
    
    with connection.session() as session:
        for keyword in keywords:
            result = session.run("""
                MATCH (pr:PullRequest)
                WHERE toLower(pr.title) CONTAINS toLower($kw)
                   OR toLower(pr.description) CONTAINS toLower($kw)
                RETURN pr.number as number,
                       pr.title as title,
                       pr.description as description,
                       pr.author as author,
                       pr.state as state,
                       pr.labels as labels,
                       pr.files_changed as files_changed,
                       $kw as matched_keyword
                LIMIT $limit
            """, kw=keyword, limit=limit)
            results.extend([dict(r) for r in result])
    
    # Deduplicate by PR number
    seen = set()
    unique_results = []
    for r in results:
        num = r.get("number")
        if num not in seen:
            seen.add(num)
            unique_results.append(r)
    
    return unique_results[:limit]


def main():
    query = "home page improver CMS entities index"
    # Extract individual keywords for text search
    keywords = ["home", "page", "improver", "CMS", "entities", "index"]
    
    console.print()
    console.print(f"[bold cyan]Semantic Search Test[/bold cyan]")
    console.print(f"[bold]Query:[/bold] {query}")
    console.print(f"[bold]Keywords:[/bold] {', '.join(keywords)}")
    console.print()
    
    # Connect to Neo4j
    connection = get_connection()
    connection.connect()
    
    # Initialize similarity search
    search = SimilaritySearch(connection)
    
    # Search for similar code (functions and classes) - semantic
    console.print("[bold]1. Semantic Search (Vector) - Functions and Classes...[/bold]")
    code_results = search.find_similar_code(
        query=query,
        entity_types=["Function", "Class"],
        limit=20,
        min_score=0.3,  # Lower threshold to get more results
    )
    
    if code_results:
        table = Table(title="Semantic Code Search Results")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Score", style="yellow")
        table.add_column("File Path", style="dim")
        table.add_column("Docstring", style="white", max_width=50)
        
        for result in code_results:
            docstring = result.get("docstring", "") or ""
            if len(docstring) > 50:
                docstring = docstring[:47] + "..."
            table.add_row(
                result.get("type", ""),
                result.get("name", result.get("qualified_name", "")),
                f"{result.get('score', 0):.3f}",
                result.get("file_path", ""),
                docstring,
            )
        
        console.print(table)
    else:
        console.print("[yellow]No semantic code results found (embeddings may not be indexed).[/yellow]")
    
    console.print()
    
    # Text-based search for code
    console.print("[bold]2. Text Search (Keywords) - Functions and Classes...[/bold]")
    text_code_results = text_search_code(connection, keywords, limit=20)
    
    if text_code_results:
        table = Table(title="Text-Based Code Search Results")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Keyword", style="yellow")
        table.add_column("File Path", style="dim")
        table.add_column("Docstring", style="white", max_width=50)
        
        for result in text_code_results:
            docstring = result.get("docstring", "") or ""
            if len(docstring) > 50:
                docstring = docstring[:47] + "..."
            table.add_row(
                result.get("type", ""),
                result.get("name", result.get("qualified_name", "")),
                result.get("matched_keyword", ""),
                result.get("file_path", ""),
                docstring,
            )
        
        console.print(table)
    else:
        console.print("[yellow]No text-based code results found.[/yellow]")
    
    console.print()
    
    # Search for similar PRs - semantic
    console.print("[bold]3. Semantic Search (Vector) - Pull Requests...[/bold]")
    pr_results = search.find_similar_prs(
        query=query,
        limit=10,
        min_score=0.3,
    )
    
    if pr_results:
        table = Table(title="Semantic PR Search Results")
        table.add_column("PR #", style="cyan")
        table.add_column("Title", style="green", max_width=50)
        table.add_column("Score", style="yellow")
        table.add_column("Author", style="dim")
        table.add_column("State", style="dim")
        
        for pr in pr_results:
            title = pr.get("title", "")
            if len(title) > 50:
                title = title[:47] + "..."
            table.add_row(
                str(pr.get("number", "")),
                title,
                f"{pr.get('score', 0):.3f}",
                pr.get("author", ""),
                pr.get("state", ""),
            )
        
        console.print(table)
    else:
        console.print("[yellow]No semantic PR results found (embeddings may not be indexed).[/yellow]")
    
    console.print()
    
    # Text-based search for PRs
    console.print("[bold]4. Text Search (Keywords) - Pull Requests...[/bold]")
    text_pr_results = text_search_prs(connection, keywords, limit=20)
    
    if text_pr_results:
        table = Table(title="Text-Based PR Search Results")
        table.add_column("PR #", style="cyan")
        table.add_column("Title", style="green", max_width=50)
        table.add_column("Keyword", style="yellow")
        table.add_column("Author", style="dim")
        table.add_column("State", style="dim")
        
        for pr in text_pr_results:
            title = pr.get("title", "")
            if len(title) > 50:
                title = title[:47] + "..."
            table.add_row(
                str(pr.get("number", "")),
                title,
                pr.get("matched_keyword", ""),
                pr.get("author", ""),
                pr.get("state", ""),
            )
        
        console.print(table)
    else:
        console.print("[yellow]No text-based PR results found.[/yellow]")
    
    console.print()
    console.print("[bold green]✓ Search complete![/bold green]")
    console.print()
    console.print("[dim]Note: Semantic search requires embeddings to be indexed.[/dim]")
    console.print("[dim]Run 'emdash embed index' to generate embeddings for better results.[/dim]")


if __name__ == "__main__":
    main()

