#!/usr/bin/env python3
"""Smoke test to verify usage data is included in SSE events.

This test checks that raw_response with token usage is included in:
- THINKING events
- RESPONSE events  
- SESSION_END events

Run with: python tests/smoke_test_usage_data.py

Requires server running on localhost:8765 (or specify --url)
"""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx


@dataclass
class UsageTestResult:
    """Result of usage data verification."""
    
    success: bool = False
    events_received: int = 0
    thinking_events: int = 0
    thinking_with_usage: int = 0
    thinking_with_cost: int = 0
    response_events: int = 0
    response_with_usage: int = 0
    response_with_cost: int = 0
    session_end_events: int = 0
    session_end_with_usage: int = 0
    session_end_with_cost: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    errors: list[str] = field(default_factory=list)


def parse_sse_events(response_text: str) -> list[dict]:
    """Parse SSE events from response text."""
    events = []
    current_event_type = None
    
    for line in response_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(":"):
            # Comment/ping
            continue
        if line.startswith("event:"):
            current_event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_str = line[5:].strip()
            if data_str == "[DONE]":
                continue
            try:
                data = json.loads(data_str)
                data["_event_type"] = current_event_type
                events.append(data)
            except json.JSONDecodeError:
                pass
    
    return events


def test_usage_data(base_url: str, message: str = "Say hello") -> UsageTestResult:
    """Test that usage data is included in SSE events.
    
    Args:
        base_url: Server base URL (e.g., http://localhost:8765)
        message: Message to send to the agent
        
    Returns:
        UsageTestResult with verification details
    """
    result = UsageTestResult()
    
    try:
        # Make chat request
        print(f"\n{'='*60}")
        print(f"Testing usage data in SSE events")
        print(f"URL: {base_url}/api/agent/chat")
        print(f"Message: {message}")
        print("-" * 60)
        
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{base_url}/api/agent/chat",
                json={"message": message},
                headers={"Accept": "text/event-stream"},
            )
            
            if response.status_code != 200:
                result.errors.append(f"HTTP {response.status_code}: {response.text[:200]}")
                return result
            
            # Parse SSE events
            events = parse_sse_events(response.text)
            result.events_received = len(events)
            
            print(f"\nReceived {len(events)} events")
            
            # Analyze events
            for event in events:
                event_type = event.get("_event_type", "").lower()
                
                if event_type == "thinking":
                    result.thinking_events += 1
                    if "raw_response" in event:
                        result.thinking_with_usage += 1
                        raw = event["raw_response"]
                        print(f"  THINKING: raw_response present")
                        print(f"    input_tokens: {raw.get('input_tokens')}")
                        print(f"    output_tokens: {raw.get('output_tokens')}")
                        if "cost" in raw:
                            result.thinking_with_cost += 1
                            print(f"    cost: ${raw.get('cost'):.6f}")
                        else:
                            print(f"    cost: MISSING!")
                    else:
                        print(f"  THINKING: NO raw_response!")
                        
                elif event_type == "response":
                    result.response_events += 1
                    if "raw_response" in event:
                        result.response_with_usage += 1
                        raw = event["raw_response"]
                        print(f"  RESPONSE: raw_response present")
                        print(f"    input_tokens: {raw.get('input_tokens')}")
                        print(f"    output_tokens: {raw.get('output_tokens')}")
                        if "cost" in raw:
                            result.response_with_cost += 1
                            print(f"    cost: ${raw.get('cost'):.6f}")
                        else:
                            print(f"    cost: MISSING!")
                    else:
                        # Check if it's a status=start event (no usage expected)
                        if event.get("status") != "start":
                            print(f"  RESPONSE: NO raw_response!")
                        
                elif event_type == "session_end":
                    result.session_end_events += 1
                    if "raw_response" in event:
                        result.session_end_with_usage += 1
                        raw = event["raw_response"]
                        result.total_input_tokens = raw.get("input_tokens", 0)
                        result.total_output_tokens = raw.get("output_tokens", 0)
                        print(f"  SESSION_END: raw_response present")
                        print(f"    total input_tokens: {result.total_input_tokens}")
                        print(f"    total output_tokens: {result.total_output_tokens}")
                        if "cost" in raw:
                            result.session_end_with_cost += 1
                            result.total_cost = raw.get("cost", 0.0)
                            print(f"    total cost: ${result.total_cost:.6f}")
                        else:
                            print(f"    cost: MISSING!")
                    else:
                        print(f"  SESSION_END: NO raw_response!")
            
            # Determine success
            # We expect at least session_end to have usage data AND cost
            if result.session_end_with_usage > 0 and result.session_end_with_cost > 0:
                result.success = True
                # Also check response events (may not have thinking events for simple queries)
                if result.response_events > 0 and result.response_with_usage == 0:
                    result.errors.append("RESPONSE events missing raw_response")
                    result.success = False
                if result.response_events > 0 and result.response_with_cost == 0:
                    result.errors.append("RESPONSE events missing cost")
                    result.success = False
            else:
                if result.session_end_with_usage == 0:
                    result.errors.append("SESSION_END event missing raw_response")
                if result.session_end_with_cost == 0:
                    result.errors.append("SESSION_END event missing cost")
                
    except httpx.ConnectError as e:
        result.errors.append(f"Connection failed: {e}")
    except Exception as e:
        result.errors.append(f"Error: {e}")
        
    return result


def check_server_running(base_url: str) -> bool:
    """Check if server is running."""
    try:
        response = httpx.get(f"{base_url}/api/health", timeout=5.0)
        return response.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Test usage data in SSE events")
    parser.add_argument(
        "--url",
        default="http://localhost:8765",
        help="Server base URL (default: http://localhost:8765)",
    )
    parser.add_argument(
        "--message",
        default="Say hello briefly",
        help="Message to send to agent",
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start server if not running",
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("SMOKE TEST: Usage Data in SSE Events")
    print("=" * 60)
    
    # Check if server is running
    if not check_server_running(args.url):
        if args.start_server:
            print(f"\nServer not running. Starting server...")
            # Start server in background
            proc = subprocess.Popen(
                ["uv", "run", "emdash-core", "--port", "8765"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for server to start
            for _ in range(30):
                time.sleep(1)
                if check_server_running(args.url):
                    print("Server started successfully")
                    break
            else:
                print("Failed to start server")
                return 1
        else:
            print(f"\nServer not running at {args.url}")
            print("Start the server or use --start-server flag")
            return 1
    
    # Run test
    result = test_usage_data(args.url, args.message)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Events received: {result.events_received}")
    print(f"THINKING events: {result.thinking_events} (with usage: {result.thinking_with_usage}, with cost: {result.thinking_with_cost})")
    print(f"RESPONSE events: {result.response_events} (with usage: {result.response_with_usage}, with cost: {result.response_with_cost})")
    print(f"SESSION_END events: {result.session_end_events} (with usage: {result.session_end_with_usage}, with cost: {result.session_end_with_cost})")
    print(f"Total tokens: {result.total_input_tokens} input, {result.total_output_tokens} output")
    print(f"Total cost: ${result.total_cost:.6f}")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")
    
    print("\n" + "=" * 60)
    if result.success:
        print("✅ TEST PASSED: Usage data and cost are present in SSE events")
        return 0
    else:
        print("❌ TEST FAILED: Usage data or cost missing from SSE events")
        return 1


if __name__ == "__main__":
    sys.exit(main())
