# LLM Providers Guide

This document describes how to use each supported LLM provider in Emdash, including configuration, tool call formats, and known quirks.

## Supported Providers

| Provider | Models | Tool Calling | Vision | Thinking |
|----------|--------|--------------|--------|----------|
| Anthropic | Claude Opus 4, Sonnet 4, Haiku 4.5 | Yes | Yes | Yes (Opus/Sonnet) |
| OpenAI | GPT-4o Mini | Yes | Yes | No |
| Fireworks | GLM-4P7, MiniMax M2P1 | Yes* | No | No |

*Fireworks models may output XML tool calls requiring special parsing.

---

## Anthropic Models

### Configuration

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Available Models

| Alias | Model ID | Context | Pricing (input/output per 1M) |
|-------|----------|---------|-------------------------------|
| `opus` | claude-opus-4-20250514 | 200K | $15.00 / $75.00 |
| `sonnet` | claude-sonnet-4 | 200K | $3.00 / $15.00 |
| `haiku` | claude-haiku-4-5 | 200K | $0.80 / $4.00 |

### Tool Call Format

Anthropic uses standard JSON tool calls:

```json
{
  "type": "tool_use",
  "id": "toolu_01XFDUDYJgAACzvnptvVoYEL",
  "name": "get_weather",
  "input": {"location": "San Francisco"}
}
```

### Features

- **Extended Thinking**: Opus and Sonnet support extended thinking mode
- **Vision**: All models support image inputs
- **Streaming**: Full streaming support

---

## OpenAI Models

### Configuration

```bash
export OPENAI_API_KEY="your-api-key"
```

### Available Models

| Alias | Model ID | Context | Pricing (input/output per 1M) |
|-------|----------|---------|-------------------------------|
| `gpt-4o-mini` | gpt-4o-mini | 128K | $0.15 / $0.60 |

### Tool Call Format

OpenAI uses standard JSON tool calls:

```json
{
  "id": "call_abc123",
  "type": "function",
  "function": {
    "name": "get_weather",
    "arguments": "{\"location\": \"San Francisco\"}"
  }
}
```

---

## Fireworks AI Models

### Configuration

```bash
export FIREWORKS_API_KEY="your-api-key"
```

### Available Models

| Alias | Model ID | Context | Pricing (input/output per 1M) |
|-------|----------|---------|-------------------------------|
| `glm-4p7` | accounts/fireworks/models/glm-4p7 | 128K | $0.60 / $2.20 |
| `minimax` | accounts/fireworks/models/minimax-m2p1 | 1M | $0.30 / $1.20 |

### Known Issues: XML Tool Calls

**MiniMax M2** and **GLM-4** models sometimes output XML-formatted tool calls instead of JSON. The Fireworks API cannot parse these, returning a 400 error. Emdash automatically handles this by extracting and parsing the XML from the error message.

#### MiniMax XML Format

```xml
<invoke name="get_weather">
<parameter name="location">San Francisco</parameter>
<parameter name="units">celsius</parameter>
</invoke>
```

#### GLM-4 XML Formats

**JSON inside tool_call tag:**
```xml
<tool_call>
{"name": "get_weather", "arguments": {"location": "San Francisco"}}
</tool_call>
```

**arg_key/arg_value format:**
```xml
<tool_call>get_weather
<arg_key>location</arg_key>
<arg_value>San Francisco</arg_value>
</tool_call>
```

### How XML Parsing Works

When Fireworks returns a 400 error containing XML tool calls:

1. The error message is captured (contains the raw XML)
2. `_parse_xml_tool_calls()` extracts tool calls using regex patterns
3. XML parameters are converted to a standard `ToolCall` object
4. The parsed tool calls are returned in a synthetic `LLMResponse`

**Detection patterns:**
- MiniMax: `<invoke name="...">` tags
- GLM-4: `<tool_call>` tags

**Code location:** `packages/core/emdash_core/agent/providers/openai_provider.py`

---

## Model Selection

### By Alias (Recommended)

```python
from emdash_core.agent.providers.models import ChatModel

model = ChatModel.from_string("haiku")      # Claude Haiku 4.5
model = ChatModel.from_string("sonnet")     # Claude Sonnet 4
model = ChatModel.from_string("minimax")    # MiniMax M2P1
model = ChatModel.from_string("glm-4p7")    # GLM-4P7
```

### By Full Name

```python
model = ChatModel.ANTHROPIC_CLAUDE_HAIKU_4
model = ChatModel.FIREWORKS_MINIMAX_M2P1
```

### By Provider:Model ID

```python
model = ChatModel.from_string("anthropic:claude-haiku-4-5")
model = ChatModel.from_string("fireworks:accounts/fireworks/models/glm-4p7")
```

---

## CLI Usage

### Coworker Agent

```bash
# Use default model (GLM-4P7)
co "send an email to user@example.com"

# Specify model
co --model haiku "summarize this document"
co --model minimax "search my calendar"
```

### Agent Command

```bash
em agent --model sonnet "Help me with this task"
em agent --model glm-4p7 "Create a presentation"
```

---

## Troubleshooting

### "string indices must be integers, not 'str'"

This error occurs when tool result data is a string instead of a dict. Fixed with defensive `isinstance(result.data, dict)` checks in:
- `base_agent.py:summarize_tool_result()`
- `base_agent.py:_handle_tool_calls()`
- `runner/utils.py:summarize_tool_result()`

### "JSON does not contain content for both 'name' and 'arguments'"

This is the Fireworks XML parsing error. The system automatically handles this by:
1. Detecting the error pattern
2. Extracting XML from the error message
3. Parsing tool calls and continuing execution

If you see this error propagate, check that the XML format matches one of the supported patterns.

### Model Not Found

Ensure you're using a valid alias or model ID:

```python
# List all models
from emdash_core.agent.providers.models import ChatModel
for model in ChatModel.list_all():
    print(f"{model['name']}: {model['model_id']}")
```

---

## Adding New Models

To add a new model, update `packages/core/emdash_core/agent/providers/models.py`:

```python
NEW_MODEL = ChatModelSpec(
    provider="provider_name",
    model_id="model-id",
    api_model="api-model-string",
    context_window=128000,
    max_output_tokens=16384,
    supports_tools=True,
    supports_vision=False,
    supports_thinking=False,
    description="Description of the model",
    input_price=0.50,
    output_price=1.50,
)
```

If the model uses non-standard tool call formats, add parsing logic to `_parse_xml_tool_calls()` in `openai_provider.py`.
