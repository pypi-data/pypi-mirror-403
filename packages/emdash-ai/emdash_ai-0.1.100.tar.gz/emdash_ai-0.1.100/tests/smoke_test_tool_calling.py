#!/usr/bin/env python3
"""Smoke test to verify tool calling works across different models.

This test checks if LLM models actually invoke tools when asked to explore code.
Run with: python tests/smoke_test_tool_calling.py
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emdash.agent.providers import get_provider
from emdash.agent.providers.factory import DEFAULT_MODEL
from emdash.agent.toolkit import AgentToolkit


@dataclass
class ToolCallResult:
    """Result of a tool calling test."""
    model: str
    provider: str
    tool_calls_made: int
    tools_called: list[str] = field(default_factory=list)
    response_content: str = ""
    error: Optional[str] = None


def test_agent_runner(model: str, query: str) -> dict:
    """Test the full AgentRunner to see if it uses tools.

    Returns dict with iteration info and tool usage.
    """
    from emdash.agent.runner import AgentRunner
    from emdash.graph.connection import close_connection

    print(f"\n{'='*60}")
    print(f"Testing AgentRunner with: {model}")
    print(f"Query: {query}")
    print("-" * 60)

    # Ensure clean connection state
    close_connection()

    # Track tool calls via a wrapper
    tool_calls_log = []

    runner = AgentRunner(model=model, verbose=True, max_iterations=5)

    # Monkey-patch to track tool calls
    original_execute = runner._execute_tool_call
    def tracking_execute(tool_call):
        tool_calls_log.append({
            "name": tool_call.name,
            "args": tool_call.arguments[:200] if tool_call.arguments else ""
        })
        return original_execute(tool_call)
    runner._execute_tool_call = tracking_execute

    try:
        response = runner.run(query)
        print(f"\nFinal response length: {len(response)}")
        print(f"Tool calls made: {len(tool_calls_log)}")
        for tc in tool_calls_log:
            print(f"  - {tc['name']}")
        return {
            "success": True,
            "tool_calls": len(tool_calls_log),
            "tools": [tc["name"] for tc in tool_calls_log],
            "response_preview": response[:300] if response else ""
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e), "tool_calls": 0, "tools": []}


def test_tool_calling(model: str, query: str = "Search for authentication code") -> ToolCallResult:
    """Test if a model makes tool calls when given tools.

    Args:
        model: Model identifier (e.g., "haiku", "minimax", "gpt-4o-mini")
        query: Query that should trigger tool usage

    Returns:
        ToolCallResult with details about tool calling behavior
    """
    result = ToolCallResult(model=model, provider="", tool_calls_made=0)

    try:
        # Initialize provider and toolkit
        provider = get_provider(model)
        result.provider = getattr(provider, "_provider", "unknown")

        toolkit = AgentToolkit(enable_session=False)
        tools = toolkit.get_all_schemas()

        # Build messages
        messages = [
            {
                "role": "system",
                "content": "You are a code exploration agent. Use the provided tools to search and analyze code. Always use tools - do not just describe what you would do."
            },
            {
                "role": "user",
                "content": query
            }
        ]

        print(f"\n{'='*60}")
        print(f"Testing: {model} (provider: {result.provider})")
        print(f"Query: {query}")
        print(f"Tools available: {len(tools)}")
        print("-" * 60)

        # Make the API call
        response = provider.chat(messages, tools=tools)

        # Check for tool calls
        if response.tool_calls:
            result.tool_calls_made = len(response.tool_calls)
            result.tools_called = [tc.name for tc in response.tool_calls]
            print(f"✅ Tool calls made: {result.tool_calls_made}")
            for tc in response.tool_calls:
                print(f"   - {tc.name}: {tc.arguments[:100]}...")
        else:
            print(f"❌ No tool calls made")

        # Capture response content
        result.response_content = response.content or ""
        if result.response_content:
            preview = result.response_content[:200].replace("\n", " ")
            print(f"Response preview: {preview}...")

    except Exception as e:
        result.error = str(e)
        print(f"❌ Error: {e}")

    return result


def main():
    """Run smoke tests across multiple models."""
    print("=" * 60)
    print("SMOKE TEST: Tool Calling Verification")
    print("=" * 60)
    print(f"\nDefault model: {DEFAULT_MODEL}")

    # Models to test - comment out any you don't have API keys for
    models_to_test = [
        DEFAULT_MODEL,  # Current default (minimax)
        # "haiku",      # Claude Haiku - uncomment if you have ANTHROPIC_API_KEY
        # "sonnet",     # Claude Sonnet
        # "gpt-4o-mini",# GPT-4o Mini - uncomment if you have OPENAI_API_KEY
    ]

    # Check for available API keys and add models
    if os.environ.get("ANTHROPIC_API_KEY"):
        if "haiku" not in models_to_test:
            models_to_test.append("haiku")
    if os.environ.get("OPENAI_API_KEY"):
        if "gpt-4o-mini" not in models_to_test:
            models_to_test.append("gpt-4o-mini")

    # Test query that should trigger tool usage
    test_query = "Search for functions related to authentication or login"

    results: list[ToolCallResult] = []

    for model in models_to_test:
        try:
            result = test_tool_calling(model, test_query)
            results.append(result)
        except Exception as e:
            print(f"\n❌ Failed to test {model}: {e}")
            results.append(ToolCallResult(model=model, provider="error", tool_calls_made=0, error=str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"{'Model':<40} {'Provider':<12} {'Tool Calls':<12} {'Status'}")
    print("-" * 76)

    for r in results:
        status = "✅ PASS" if r.tool_calls_made > 0 else "❌ FAIL"
        if r.error:
            status = f"⚠️  ERROR: {r.error[:20]}..."
        print(f"{r.model:<40} {r.provider:<12} {r.tool_calls_made:<12} {status}")
        if r.tools_called:
            print(f"   Tools: {', '.join(r.tools_called)}")

    # Verdict
    print("\n" + "=" * 60)
    working_models = [r for r in results if r.tool_calls_made > 0]
    failing_models = [r for r in results if r.tool_calls_made == 0 and not r.error]

    if failing_models:
        print("⚠️  MODELS NOT CALLING TOOLS:")
        for r in failing_models:
            print(f"   - {r.model}")
            if r.response_content:
                print(f"     Response: {r.response_content[:100]}...")

    if working_models:
        print("\n✅ MODELS WITH WORKING TOOL CALLS:")
        for r in working_models:
            print(f"   - {r.model} ({r.tool_calls_made} calls)")

    # Return exit code based on default model behavior
    default_result = next((r for r in results if r.model == DEFAULT_MODEL), None)
    if default_result and default_result.tool_calls_made == 0:
        print(f"\n🚨 DEFAULT MODEL ({DEFAULT_MODEL}) IS NOT CALLING TOOLS!")
        print("   This confirms the suspected issue.")
        return 1

    return 0


def test_agent_runner_main():
    """Test the full agent runner flow."""
    print("\n" + "=" * 60)
    print("AGENT RUNNER TEST")
    print("=" * 60)

    query = "What functions handle user input validation?"

    # Test with default model
    print(f"\nTesting default model: {DEFAULT_MODEL}")
    result = test_agent_runner(DEFAULT_MODEL, query)

    print("\n" + "-" * 60)
    print(f"Result: {'✅ PASS' if result['tool_calls'] > 0 else '❌ FAIL - NO TOOL CALLS'}")
    if result.get("tools"):
        print(f"Tools used: {', '.join(result['tools'])}")
    if result.get("error"):
        print(f"Error: {result['error']}")

    return result["tool_calls"] > 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", action="store_true", help="Test full AgentRunner")
    parser.add_argument("--provider", action="store_true", help="Test provider directly (default)")
    args = parser.parse_args()

    if args.runner:
        success = test_agent_runner_main()
        sys.exit(0 if success else 1)
    else:
        sys.exit(main())
