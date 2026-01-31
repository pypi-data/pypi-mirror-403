# AI SDK Stopping Criteria Comparison: Vercel AI SDK vs LangChain

This document compares the stopping criteria between **Vercel AI SDK's `generateText`** and **LangChain's Agent Loop**.

---

## Executive Summary

| Aspect | Vercel AI SDK | LangChain |
|--------|---------------|-----------|
| **Primary Stop Mechanism** | `finishReason` from model | `AgentFinish` from output parser |
| **Loop Control** | `stopWhen` predicates | `max_iterations` + `max_execution_time` |
| **Default Max Steps** | 1 (single step) | 15 iterations |
| **Time Limits** | Not built-in | `max_execution_time` parameter |
| **Tool Loop Detection** | `finishReason === "tool-calls"` | `tool_calls` in AIMessage |
| **Early Stopping** | Via `stopWhen` conditions | `early_stopping_method` ("force"/"generate") |

---

## 1. Core Loop Architecture

### Vercel AI SDK (`generateText`)

```
┌─────────────────────────────────────────────────────────┐
│                    generateText Loop                     │
├─────────────────────────────────────────────────────────┤
│  1. Send prompt to model                                │
│  2. Receive response with finishReason                  │
│  3. If finishReason === "tool-calls":                   │
│     → Execute tools                                     │
│     → Append results to conversation                    │
│     → Check stopWhen conditions                         │
│     → If not stopped, go to step 1                      │
│  4. If finishReason !== "tool-calls":                   │
│     → Return final result                               │
└─────────────────────────────────────────────────────────┘
```

### LangChain Agent Loop

```
┌─────────────────────────────────────────────────────────┐
│                  AgentExecutor Loop                      │
├─────────────────────────────────────────────────────────┤
│  1. Call agent with current state                       │
│  2. Parse output to AgentAction or AgentFinish          │
│  3. If AgentAction:                                     │
│     → Execute tool                                      │
│     → Add to intermediate_steps                         │
│     → Check iteration/time limits                       │
│     → If under limits, go to step 1                     │
│  4. If AgentFinish:                                     │
│     → Return return_values immediately                  │
│  5. If limits exceeded:                                 │
│     → Apply early_stopping_method                       │
│     → Return stopped response                           │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Stopping Conditions Deep Dive

### Vercel AI SDK Stopping Conditions

| Condition | Stops Loop? | Description |
|-----------|-------------|-------------|
| `finishReason: "stop"` | ✅ Yes | Model completed naturally |
| `finishReason: "tool-calls"` | ❌ No | Model requests tool execution, loop continues |
| `finishReason: "length"` | ⚠️ Configurable | Token limit reached; can auto-continue with `experimental_continueSteps` |
| `finishReason: "content-filter"` | ✅ Yes | Safety policy violation |
| `finishReason: "error"` | ✅ Yes | Generation error |
| `finishReason: "other"` | ✅ Yes | Unmapped provider reason |
| `stopWhen` condition met | ✅ Yes | Custom predicate satisfied |

**stopWhen Examples:**
```typescript
// Stop after 5 steps
stopWhen: stepCountIs(5)

// Stop when specific tool is called
stopWhen: hasToolCall('finalAnswer')

// Multiple conditions (stops on ANY match)
stopWhen: [stepCountIs(10), hasToolCall('complete')]
```

### LangChain Stopping Conditions

| Condition | Stops Loop? | Description |
|-----------|-------------|-------------|
| `AgentFinish` returned | ✅ Yes | Agent reached final answer |
| `AgentAction` returned | ❌ No | Agent wants to use a tool, loop continues |
| `max_iterations` reached | ✅ Yes | Default: 15 iterations |
| `max_execution_time` exceeded | ✅ Yes | Wall clock time limit |
| `tool_calls` empty (LangGraph) | ✅ Yes | No more tools to call |
| Custom stop condition | ✅ Yes | Via agent configuration |

**AgentExecutor Configuration:**
```python
AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=15,           # Hard limit on iterations
    max_execution_time=60,       # 60 seconds wall clock time
    early_stopping_method="force"  # or "generate"
)
```

---

## 3. Key Differences

### 3.1 Stop Signal Source

| SDK | Stop Signal Source |
|-----|-------------------|
| **Vercel AI SDK** | Model's `finishReason` in API response (provider-level) |
| **LangChain** | Output parser's interpretation of model text (application-level) |

**Implication:** Vercel relies on the model provider to signal completion, while LangChain parses the model's text output to determine if it's an action or final answer.

### 3.2 Default Behavior

| SDK | Default Loop Behavior |
|-----|----------------------|
| **Vercel AI SDK** | Runs **1 step** by default (no looping without `stopWhen`) |
| **LangChain** | Runs up to **15 iterations** by default |

**Implication:** Vercel is opt-in for multi-step; LangChain is multi-step by default with a safety limit.

### 3.3 Time-Based Stopping

| SDK | Time Limit Support |
|-----|-------------------|
| **Vercel AI SDK** | ❌ No built-in time limit |
| **LangChain** | ✅ `max_execution_time` parameter |

**Implication:** LangChain provides wall-clock time protection; Vercel requires custom implementation.

### 3.4 Graceful Termination

| SDK | Graceful Stop Mechanism |
|-----|------------------------|
| **Vercel AI SDK** | Loop simply ends, returns accumulated results |
| **LangChain** | `early_stopping_method="generate"` makes one final LLM call |

**Implication:** LangChain can generate a proper summary when hitting limits; Vercel returns whatever was accumulated.

### 3.5 Tool Call Detection

| SDK | How Tool Calls Are Detected |
|-----|----------------------------|
| **Vercel AI SDK** | `finishReason === "tool-calls"` from provider |
| **LangChain** | `tool_calls` array in AIMessage / AgentAction from parser |

---

## 4. Handling Edge Cases

### Infinite Loop Prevention

| SDK | Prevention Mechanism |
|-----|---------------------|
| **Vercel AI SDK** | `stopWhen: stepCountIs(N)` - explicit step limit |
| **LangChain** | `max_iterations=15` (default) + `max_execution_time` |

### Token Limit Reached Mid-Generation

| SDK | Behavior |
|-----|----------|
| **Vercel AI SDK** | `experimental_continueSteps` auto-continues generation across steps |
| **LangChain** | Depends on model; may truncate or error |

### Tool Execution Errors

| SDK | Behavior |
|-----|----------|
| **Vercel AI SDK** | Errors propagate; can be caught with try/catch |
| **LangChain** | `handle_parsing_errors=True` attempts recovery; can cause loops |

---

## 5. Code Examples

### Vercel AI SDK - Multi-Step with Stopping

```typescript
import { generateText, stepCountIs } from 'ai';

const result = await generateText({
  model: openai('gpt-4'),
  prompt: 'Research and summarize the latest AI news',
  tools: {
    search: searchTool,
    summarize: summarizeTool,
  },
  stopWhen: stepCountIs(5), // Stop after 5 steps max
  onStepFinish: (step) => {
    console.log(`Step ${step.stepNumber}: ${step.finishReason}`);
  },
});

// Result contains all steps
console.log(result.steps); // Array of all executed steps
console.log(result.text);  // Final combined text
```

### LangChain - AgentExecutor with Limits

```python
from langchain.agents import AgentExecutor, create_react_agent

executor = AgentExecutor(
    agent=create_react_agent(llm, tools, prompt),
    tools=tools,
    max_iterations=10,           # Stop after 10 iterations
    max_execution_time=120,      # Stop after 2 minutes
    early_stopping_method="generate",  # Generate final response on limit
    return_intermediate_steps=True,
    verbose=True,
)

result = executor.invoke({"input": "Research and summarize the latest AI news"})

# Result contains final output and intermediate steps
print(result["output"])
print(result["intermediate_steps"])
```

---

## 6. When to Use Which

### Use Vercel AI SDK When:
- You want **explicit control** over when the loop continues
- You're building **streaming** applications
- You need **provider-level finish reasons**
- You want **minimal default iterations** (safety-first)
- You're in a **TypeScript/JavaScript** environment

### Use LangChain When:
- You need **time-based limits** out of the box
- You want **graceful termination** with generated summaries
- You need **intermediate step tracking** built-in
- You're building **complex multi-agent** workflows
- You want **legacy compatibility** with established patterns

---

## 7. Summary Table

| Feature | Vercel AI SDK | LangChain |
|---------|---------------|-----------|
| **Language** | TypeScript/JavaScript | Python/JavaScript |
| **Loop Trigger** | `stopWhen` parameter | Always loops (AgentExecutor) |
| **Max Steps Default** | 1 | 15 |
| **Time Limit** | Not built-in | `max_execution_time` |
| **Stop Detection** | Model's `finishReason` | Parser's `AgentFinish` |
| **Graceful Stop** | No | `early_stopping_method="generate"` |
| **Tool Loop Signal** | `finishReason: "tool-calls"` | `AgentAction` / `tool_calls[]` |
| **Step Tracking** | `result.steps[]` | `intermediate_steps[]` |
| **Continuation** | `experimental_continueSteps` | Not built-in |
| **Modern Architecture** | `generateText` + `stopWhen` | LangGraph + `create_react_agent` |

---

## References

### Vercel AI SDK
- [AI SDK Documentation](https://ai-sdk.dev/docs)
- [generateText Reference](https://ai-sdk.dev/docs/reference/ai-sdk-core/generate-text)
- [Agents Loop Control](https://ai-sdk.dev/docs/agents/loop-control)
- [AI SDK 6 Release](https://vercel.com/blog/ai-sdk-6)

### LangChain
- [LangChain Agents Documentation](https://docs.langchain.com/oss/python/langchain/agents)
- [AgentExecutor API Reference](https://python.langchain.com/api_reference/langchain/agents/langchain.agents.agent.AgentExecutor.html)
- [Max Iterations Guide](https://python.langchain.com/docs/modules/agents/how_to/max_iterations/)
- [LangGraph Agents](https://reference.langchain.com/python/langgraph/agents/)

---

## 8. Implementation Plan for emdash.dev

This section outlines specific changes to implement enhanced stopping criteria in the emdash.dev codebase.

### 8.1 Current State Analysis

**Files involved:**
| File | Current Stopping Logic |
|------|----------------------|
| `packages/core-ts/src/agent/runner.ts:98` | `maxSteps: this.maxIterations` only |
| `packages/core-ts/src/agent/subagent.ts:34-38` | Per-type limits: explore=20, plan=30, bash=10 |
| `packages/core-ts/src/research/controller.ts:105` | `while (feedback.requiresRevision && iterations < maxIterations)` |
| `packages/core-ts/src/config.ts:20` | Default `maxIterations: 100` |

**What's missing:**
- No `finishReason` tracking in `AgentResult`
- No time-based limits
- No conditional stopping (e.g., stop on specific tool call)
- No graceful termination when limits are hit
- No visibility into why the loop stopped

### 8.2 Implementation Tasks

#### Phase 1: Add `finishReason` Tracking (Low effort, High value)

**Goal:** Know why the agent stopped.

**Changes to `runner.ts`:**

```typescript
// 1. Update AgentResult interface (line 28)
export interface AgentResult {
  response: string;
  toolCalls: ToolCallRecord[];
  usage: { promptTokens: number; completionTokens: number };
  iterations: number;
  finishReason: 'stop' | 'tool-calls' | 'length' | 'content-filter' | 'error' | 'max-steps';  // NEW
  stoppedEarly: boolean;  // NEW: true if hit maxSteps while model wanted more
}

// 2. Track finishReason from result (after line 135)
const wasForciblyStopped = result.finishReason === 'tool-calls';

if (wasForciblyStopped) {
  this.logger.warn(
    { iterations, maxIterations: this.maxIterations },
    'Agent hit maxSteps while still requesting tools'
  );
}

return {
  response: result.text,
  toolCalls,
  usage: totalUsage,
  iterations,
  finishReason: wasForciblyStopped ? 'max-steps' : result.finishReason,
  stoppedEarly: wasForciblyStopped,
};
```

**Changes to `subagent.ts`:**

```typescript
// Update SubAgentResult (line 40)
export interface SubAgentResult {
  success: boolean;
  response: string;
  findings?: string[];
  filesExplored?: string[];
  toolCalls?: number;
  error?: string;
  stoppedEarly?: boolean;  // NEW
  finishReason?: string;   // NEW
}
```

---

#### Phase 2: Add Time-Based Limits (Medium effort, Medium value)

**Goal:** Prevent runaway executions.

**Changes to `config.ts`:**

```typescript
// Add to ConfigSchema (line 20)
maxIterations: z.coerce.number().default(100),
maxExecutionTimeMs: z.coerce.number().default(300000),  // NEW: 5 minutes default
```

**Changes to `runner.ts`:**

```typescript
// Add to AgentRunnerOptions (line 9)
export interface AgentRunnerOptions {
  // ... existing
  maxExecutionTimeMs?: number;  // NEW
}

// In run() method, add timeout tracking (after line 91)
const startTime = Date.now();
const maxTime = this.maxExecutionTimeMs ?? this.config.maxExecutionTimeMs ?? 300000;

// In onStepFinish callback (around line 99)
onStepFinish: (step) => {
  iterations++;

  // Check time limit
  const elapsed = Date.now() - startTime;
  if (elapsed > maxTime) {
    this.logger.warn({ elapsed, maxTime }, 'Agent exceeded time limit');
    // Note: AI SDK doesn't support mid-loop abort, so this is informational
    // Consider throwing to abort, or track for reporting
  }
  // ... rest of callback
}
```

**Alternative: AbortController approach:**

```typescript
// More robust time limiting with AbortController
const controller = new AbortController();
const timeout = setTimeout(() => controller.abort(), maxTime);

try {
  const result = await generateText({
    // ... options
    abortSignal: controller.signal,  // If AI SDK supports it
  });
} finally {
  clearTimeout(timeout);
}
```

---

#### Phase 3: Add Conditional Stopping (Medium effort, High value)

**Goal:** Stop when a specific tool is called (e.g., `task_complete`).

**Option A: Using AI SDK v6 `stopWhen` (requires upgrade)**

```typescript
import { generateText, stepCountIs, hasToolCall } from 'ai';

const result = await generateText({
  // ... options
  stopWhen: [
    stepCountIs(this.maxIterations),
    hasToolCall('task_complete'),
  ],
});
```

**Option B: Custom implementation (works with current AI SDK v4)**

```typescript
// Add to AgentRunnerOptions
export interface AgentRunnerOptions {
  // ... existing
  stopOnTools?: string[];  // NEW: tool names that signal completion
}

// In run() method
let shouldStop = false;

onStepFinish: (step) => {
  // ... existing logic

  if (step.toolCalls && this.stopOnTools?.length) {
    for (const call of step.toolCalls) {
      if (this.stopOnTools.includes(call.toolName)) {
        this.logger.info({ tool: call.toolName }, 'Stop tool called');
        shouldStop = true;
        // Note: Can't actually stop mid-loop in AI SDK v4
        // This would need a custom loop implementation
      }
    }
  }
}
```

---

#### Phase 4: Custom Loop for Full Control (High effort, High value)

**Goal:** Replace AI SDK's internal loop with custom implementation for full control.

**New file: `packages/core-ts/src/agent/loop.ts`**

```typescript
import { generateText } from 'ai';
import type { CoreMessage } from 'ai';

export interface LoopOptions {
  maxSteps: number;
  maxExecutionTimeMs: number;
  stopOnTools?: string[];
  onStep?: (step: StepInfo) => void;
}

export interface StepInfo {
  stepNumber: number;
  finishReason: string;
  toolCalls: string[];
  elapsedMs: number;
}

export type StopReason =
  | 'natural'        // Model finished
  | 'max-steps'      // Hit step limit
  | 'timeout'        // Hit time limit
  | 'stop-tool'      // Stop tool called
  | 'error';         // Error occurred

export async function runAgentLoop(options: LoopOptions): Promise<{
  messages: CoreMessage[];
  stopReason: StopReason;
  steps: StepInfo[];
}> {
  const startTime = Date.now();
  const steps: StepInfo[] = [];
  let messages: CoreMessage[] = [...options.initialMessages];

  for (let step = 0; step < options.maxSteps; step++) {
    // Check time limit
    const elapsed = Date.now() - startTime;
    if (elapsed > options.maxExecutionTimeMs) {
      return { messages, stopReason: 'timeout', steps };
    }

    // Single step (maxSteps: 1)
    const result = await generateText({
      ...options.generateOptions,
      messages,
      maxSteps: 1,
    });

    const stepInfo: StepInfo = {
      stepNumber: step + 1,
      finishReason: result.finishReason,
      toolCalls: result.toolCalls?.map(c => c.toolName) ?? [],
      elapsedMs: Date.now() - startTime,
    };
    steps.push(stepInfo);
    options.onStep?.(stepInfo);

    // Check for stop tool
    if (options.stopOnTools?.some(t => stepInfo.toolCalls.includes(t))) {
      return { messages, stopReason: 'stop-tool', steps };
    }

    // Check for natural completion
    if (result.finishReason !== 'tool-calls') {
      return { messages, stopReason: 'natural', steps };
    }

    // Continue loop - append results to messages
    messages = [...messages, ...result.responseMessages];
  }

  return { messages, stopReason: 'max-steps', steps };
}
```

---

### 8.3 Priority Order

| Priority | Task | Effort | Value | Files Changed |
|----------|------|--------|-------|---------------|
| **1** | Add `finishReason` to `AgentResult` | Low | High | `runner.ts`, `subagent.ts` |
| **2** | Log warning when hitting maxSteps | Low | Medium | `runner.ts` |
| **3** | Add `maxExecutionTimeMs` config | Low | Medium | `config.ts`, `runner.ts` |
| **4** | Add `stopOnTools` option | Medium | High | `runner.ts` |
| **5** | Upgrade to AI SDK v6 for `stopWhen` | Medium | High | `package.json`, `runner.ts` |
| **6** | Custom loop for full control | High | High | New `loop.ts` |

---

### 8.4 Quick Wins (Implement Today)

**1. Track `finishReason` in result:**
```typescript
// runner.ts line 145
return {
  response: result.text,
  toolCalls,
  usage: totalUsage,
  iterations,
  finishReason: result.finishReason,  // ADD THIS
  stoppedEarly: result.finishReason === 'tool-calls',  // ADD THIS
};
```

**2. Warn on forced stop:**
```typescript
// runner.ts after line 135
if (result.finishReason === 'tool-calls') {
  this.logger.warn(
    { iterations, maxSteps: this.maxIterations },
    'Hit maxSteps limit - agent wanted to continue'
  );
}
```

**3. Add to subagent result:**
```typescript
// subagent.ts line 98
return {
  success: true,
  response: result.response,
  filesExplored: this.extractFilesExplored(result),
  findings: this.extractFindings(result),
  toolCalls: result.toolCalls.length,
  stoppedEarly: result.stoppedEarly,  // ADD THIS
};
```

---

### 8.5 Testing Strategy

```typescript
// Test cases for stopping criteria
describe('AgentRunner stopping criteria', () => {
  it('should track finishReason in result', async () => {
    const result = await runner.run('simple question');
    expect(result.finishReason).toBeDefined();
    expect(['stop', 'tool-calls', 'length']).toContain(result.finishReason);
  });

  it('should mark stoppedEarly when hitting maxSteps', async () => {
    const runner = new AgentRunner({ maxIterations: 1 });
    const result = await runner.run('complex task requiring many steps');
    if (result.finishReason === 'tool-calls') {
      expect(result.stoppedEarly).toBe(true);
    }
  });

  it('should respect time limits', async () => {
    const runner = new AgentRunner({ maxExecutionTimeMs: 100 });
    const start = Date.now();
    await runner.run('slow task');
    expect(Date.now() - start).toBeLessThan(200); // Some buffer
  });
});
```
