import subprocess
import json
from openai import OpenAI

API_KEY = "fw_7a9rjPEQZiv5P9baVM8mMs"

SYSTEM_PROMPT = """You are a senior software architect with direct access to a knowledge graph of a codebase.

CRITICAL RULES:
1. You MUST use the tools to explore - do NOT just describe what to do. Actually CALL the tools and analyze results.
2. NEVER give time estimates (no "2-3 days", "1 week", etc.). Focus on WHAT needs to be done, not how long.
3. Act as a strict architect: identify what ALREADY EXISTS before suggesting anything new.

Your approach:
1. FIRST: Search for existing implementations related to the user's request
2. SECOND: Expand and trace what you find to understand current state
3. THIRD: Identify gaps - what's missing vs what already exists
4. FOURTH: Be STRICT - only recommend additions that are truly necessary

When planning features or changes:
- Point out existing code that can be reused or extended
- Be specific about which files/functions already handle parts of the requirement
- Clearly separate "already implemented" from "needs to be added"
- Question whether new code is needed - prefer extending existing patterns
- If something exists, say "This is already implemented in X" rather than suggesting to build it

Available tools:
- semantic_search: Find code by meaning
- text_search: Find code by exact name
- expand_node: Get full context of a function/class/file
- get_callers/get_callees: Trace relationships
- get_class_hierarchy: Get inheritance tree
- get_file_dependencies: Get imports/dependents
- get_impact_analysis: Assess change impact
- get_top_pagerank: Find important code
- get_communities: Find code clusters
- get_file_history: Get commit history
- find_similar_prs: Find related PRs

OUTPUT FORMAT for implementation plans:
1. **Already Exists**: List existing implementations found
2. **Gaps Identified**: What's specifically missing
3. **Recommended Changes**: Minimal additions needed (no time estimates)
4. **Files to Modify**: Specific paths

Be thorough in exploration. Be strict in recommendations."""

# Test 1: OpenAI-compatible SDK
print("=" * 50)
print("Test 1: OpenAI SDK")
print("=" * 50)

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.fireworks.ai/inference/v1"
)

response = client.chat.completions.create(
    model="accounts/fireworks/models/glm-4p7",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "which llm model are you"}
    ]
)

print(response.choices[0].message.content)

# Test 2: curl via subprocess
print("\n" + "=" * 50)
print("Test 2: curl")
print("=" * 50)

curl_result = subprocess.run([
    "curl", "--request", "POST",
    "--url", "https://api.fireworks.ai/inference/v1/chat/completions",
    "-H", "Accept: application/json",
    "-H", "Content-Type: application/json",
    "-H", f"Authorization: Bearer {API_KEY}",
    "--data", json.dumps({
        "model": "accounts/fireworks/models/minimax-m2p1",
        "max_tokens": 4096,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": "which llm model are you"
            }
        ]
    }),
    "-s"
], capture_output=True, text=True)

result = json.loads(curl_result.stdout)
print(result.get("choices", [{}])[0].get("message", {}).get("content", curl_result.stdout))
