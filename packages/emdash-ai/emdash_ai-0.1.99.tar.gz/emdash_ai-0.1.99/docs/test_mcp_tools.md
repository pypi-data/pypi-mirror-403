#!/usr/bin/env python3
"""
Test script to check what tools are available from the GitHub MCP server.
This will help us identify the correct tool name for creating PR reviews.
"""

import os
import sys
from emdash.agent.mcp.client import GitHubMCPClient
from emdash.core.config import get_config

def main():
    """List all available MCP tools."""
    print("GitHub MCP Server Tool Availability Test")
    print("=" * 50)
    
    # Check configuration
    config = get_config()
    print(f"GitHub token configured: {config.mcp.is_available}")
    print(f"GitHub repo: {config.mcp.github_repo}")
    print(f"Toolsets: {config.mcp.toolsets}")
    print(f"Read-only mode: {config.mcp.read_only}")
    print()
    
    if not config.mcp.is_available:
        print("❌ GitHub token not configured. Set GITHUB_TOKEN environment variable.")
        return
    
    try:
        # Create MCP client
        client = GitHubMCPClient()
        
        if not client.is_available:
            print("❌ GitHub MCP server binary not found.")
            print("Please install github-mcp-server from:")
            print("https://github.com/github/github-mcp-server/releases")
            return
        
        print("Starting MCP server...")
        client.start()
        
        print("Listing available tools...")
        tools = client.list_tools()
        
        print(f"\n📋 Found {len(tools)} tools:")
        print("-" * 50)
        
        for tool in tools:
            print(f"🔧 {tool.name}")
            print(f"   Description: {tool.description}")
            print(f"   Category: {tool.name.split('_')[0] if '_' in tool.name else 'general'}")
            print()
        
        # Look specifically for review-related tools
        print("🔍 Review-related tools:")
        print("-" * 30)
        review_tools = [t for t in tools if 'review' in t.name.lower()]
        if review_tools:
            for tool in review_tools:
                print(f"✅ {tool.name}: {tool.description}")
        else:
            print("❌ No review-related tools found")
        
        # Look for pull request tools
        print("\n🔍 Pull request tools:")
        print("-" * 30)
        pr_tools = [t for t in tools if 'pull' in t.name.lower() or 'pr' in t.name.lower()]
        if pr_tools:
            for tool in pr_tools:
                print(f"✅ {tool.name}: {tool.description}")
        else:
            print("❌ No pull request tools found")
        
        client.stop()
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()