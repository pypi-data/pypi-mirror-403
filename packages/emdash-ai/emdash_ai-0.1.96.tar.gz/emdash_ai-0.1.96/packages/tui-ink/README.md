# @emdash/tui-ink

Ink-based TUI for emdash with **native text selection support**.

## Why Ink?

This TUI is built with [Ink](https://github.com/vadimdemedes/ink) (React for CLIs) instead of Python's Textual because:

- **Text selection works** - Ink doesn't capture mouse events, so your terminal handles selection natively
- **Proven approach** - Claude Code, Gatsby CLI, and Prisma use Ink
- **Copy/paste just works** - Select text with your mouse, copy with Cmd+C

## Usage

```bash
# Start the Ink TUI
em --ink-tui

# Or from npm
cd packages/tui-ink
npm start
```

## Development

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Watch mode
npm run watch

# Development with tsx (no build needed)
npm run dev
```

## Architecture

```
┌─────────────────────────────────────────┐
│  Ink TUI (Node.js/TypeScript)           │
│  - React components                      │
│  - Keyboard-only (no mouse capture)     │
│  - Text selection via terminal          │
└───────────────┬─────────────────────────┘
                │ JSON over stdin/stdout
┌───────────────┴─────────────────────────┐
│  Python Backend                          │
│  - SSE stream handling                   │
│  - Agent communication                   │
│  - Existing emdash infrastructure        │
└─────────────────────────────────────────┘
```

## Protocol

Communication between Python and Ink uses JSON over stdin/stdout:

### Python → Ink (Events)

```json
{"type": "init", "data": {"model": "claude-sonnet", "mode": "code", "cwd": "/path"}}
{"type": "thinking", "data": {"content": "..."}}
{"type": "response", "data": {"content": "..."}}
{"type": "tool_start", "data": {"name": "Read", "args": {...}}}
{"type": "tool_result", "data": {"name": "Read", "success": true}}
{"type": "ask_choice_questions", "data": {"questions": [...]}}
{"type": "plan_mode_requested", "data": {"reason": "..."}}
```

### Ink → Python (Messages)

```json
{"type": "user_input", "data": {"content": "user message"}}
{"type": "choice_answer", "data": {"selected": "option1"}}
{"type": "plan_approval", "data": {"approved": true}}
{"type": "cancel", "data": {}}
{"type": "quit", "data": {}}
```

## Components

- `App.tsx` - Main application component
- `components/`
  - `Message.tsx` - Chat message display with markdown
  - `Spinner.tsx` - Loading indicator
  - `Input.tsx` - User input with cursor
  - `ChoicePrompt.tsx` - Interactive option selector
  - `ApprovalPrompt.tsx` - Plan approval dialog
  - `StatusBar.tsx` - Model/mode/session info
  - `TypingIndicator.tsx` - Multiuser typing status
- `protocol.ts` - TypeScript types for JSON protocol
