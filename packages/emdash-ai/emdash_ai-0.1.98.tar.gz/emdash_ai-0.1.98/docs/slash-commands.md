# Slash Commands

Talk to emdash like a colleague. Slash commands are simple shortcuts that let you navigate, explore, and control your coding sessions without breaking your flow.

## Getting Started

Once you're in the emdash agent, just type `/` followed by what you want to do. It's that simple.

```
> /plan
Switched to plan mode. Ready to explore and strategize.
```

## Work Your Way

### Switch Between Modes

Sometimes you want to think. Sometimes you want to build. Emdash adapts to you.

| Command | What it does |
|---------|--------------|
| `/plan` | Enter planning mode - explore ideas, map out your approach |
| `/code` | Enter coding mode - make changes, write code |
| `/mode` | See which mode you're currently in |

### Understand Your Codebase

Get the big picture without digging through files.

| Command | What it does |
|---------|--------------|
| `/projectmd` | Generate a clear overview of your entire project architecture |
| `/research [question]` | Deep dive into any topic - "How does auth work?" |
| `/pr [link or number]` | Review any pull request in detail |

### Stay Organized

Keep track of what you're working on.

| Command | What it does |
|---------|--------------|
| `/todos` | See your current task list |
| `/todo-add [task]` | Add something to your list |
| `/status` | Quick health check on your project |
| `/context` | See what emdash is currently focused on |

### Save Your Progress

Pick up right where you left off.

| Command | What it does |
|---------|--------------|
| `/session` | Open the session menu |
| `/session save [name]` | Save your current session |
| `/session load [name]` | Load a previous session |
| `/session list` | See all your saved sessions |
| `/reset` | Start fresh |

### Make It Yours

Customize emdash to fit your workflow.

| Command | What it does |
|---------|--------------|
| `/agents` | Create and manage custom AI agents |
| `/rules` | Set guidelines for how the agent behaves |
| `/skills` | Add reusable capabilities |
| `/hooks` | Set up automations that trigger on events |
| `/registry` | Browse community-contributed tools |

### Verify Your Work

Build confidence that things work correctly.

| Command | What it does |
|---------|--------------|
| `/verify` | Run checks on your current work |
| `/verify-loop [task]` | Keep running until everything passes |

### Helpful Utilities

| Command | What it does |
|---------|--------------|
| `/auth` | Connect to GitHub |
| `/doctor` | Diagnose any issues |
| `/help` | See all available commands |
| `/quit` | Exit the agent |

## Quick Tips

**Use `@` to reference files** - Type `@filename` in your prompt to pull in context from any file.

**Multi-line input** - Press `Alt+Enter` to write longer prompts across multiple lines.

**Auto-complete** - Hit `Ctrl+Space` to see command suggestions.

**Paste images** - `Ctrl+V` lets you paste screenshots directly into the conversation.

## Example Workflows

### Starting a New Feature

```
> /plan
> I want to add user notifications to the app
> /research How do other parts of the app handle real-time updates?
> /projectmd
> /code
> /verify-loop Add email notification when order is placed
```

### Reviewing a PR

```
> /pr 142
> What are the potential issues with this approach?
> /research How does our error handling work?
```

### Picking Up Where You Left Off

```
> /session list
> /session load refactor-auth
> /todos
> Let's continue with the OAuth implementation
```

---

Slash commands are designed to feel natural. You don't need to memorize them all - just type `/help` whenever you need a reminder.
