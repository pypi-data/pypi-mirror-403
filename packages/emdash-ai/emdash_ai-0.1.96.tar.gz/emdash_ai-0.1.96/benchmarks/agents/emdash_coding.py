"""Harbor-compatible wrapper for emdash coding agent."""

import json
import os
from pathlib import Path
import sys

# Add parent to path for local emdash import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from harbor import BaseAgent, BaseEnvironment

# Import provider for LLM calls - use OpenAI directly if custom base URL is set
from openai import OpenAI


def get_llm_client(model_name: str):
    """Get LLM client - uses custom OpenAI-compatible API if OPENAI_BASE_URL is set."""
    base_url = os.getenv('OPENAI_BASE_URL')
    api_key = os.getenv('OPENAI_API_KEY')

    if base_url and api_key:
        # Use custom OpenAI-compatible API
        return OpenAI(base_url=base_url, api_key=api_key), model_name

    # Fall back to emdash provider
    from emdash_core.agent.providers import get_provider
    provider = get_provider(model_name)
    return provider, model_name


class EmdashCodingAgent(BaseAgent):
    """Harbor-compatible agent that executes coding tasks.

    This agent uses the emdash LLM provider to generate commands
    and executes them via Harbor's environment.exec() method.
    """

    SYSTEM_PROMPT = """You are an expert software engineer. You will be given a coding task.
Your goal is to complete the task by executing shell commands.

Rules:
1. First, explore the codebase to understand the structure (ls, cat, find)
2. Read relevant files to understand what needs to be done
3. Make changes using these methods (heredocs do NOT work):
   - For small files: echo 'line1' > file.py && echo 'line2' >> file.py
   - For Python scripts: Write to a temp file then run it
   - For larger content: Use base64 encoding
4. Run any tests or verification commands
5. When done, output "TASK COMPLETE" on its own line

IMPORTANT: Heredocs (<<EOF) do NOT work in this environment. Never use them.

For each step, output a command to execute using this format:
```execute
your command here
```

For multi-line commands, put them all inside the code block:
```execute
echo '#!/usr/bin/env python3' > /tmp/script.py
echo 'import json' >> /tmp/script.py
echo 'print("hello")' >> /tmp/script.py
python3 /tmp/script.py
```

After seeing the command output, decide your next action.
Continue until the task is complete or you determine it cannot be done.
"""

    def __init__(self, logs_dir=None, model_name: str = None, **kwargs):
        """Initialize the agent.

        Args:
            logs_dir: Directory for agent logs (passed by Harbor)
            model_name: Model to use (passed by Harbor via -m flag)
            **kwargs: Additional arguments from Harbor
        """
        super().__init__(logs_dir=logs_dir, **kwargs)
        self._model_name = model_name or os.getenv(
            'EMDASH_MODEL', 'accounts/fireworks/models/minimax-m2p1'
        )
        self._logs_dir = logs_dir

    def name(self) -> str:
        return "emdash-coding"

    def version(self) -> str:
        return "1.0.0"

    def _extract_command(self, message: str) -> str | None:
        """Extract command from assistant message.

        Supports two formats:
        1. ```execute\\ncommand(s)\\n``` - Multi-line code block (preferred)
        2. EXECUTE: command - Legacy single-line format

        Returns the command string or None if no command found.
        """
        import re

        # Clean up any XML-like artifacts that might leak from the model
        message = re.sub(r'</?\w+_?\w*>', '', message)

        # Try code block format first: ```execute\n...\n```
        # Match ```execute or ```bash or just ``` followed by execute keyword
        code_block_pattern = r'```(?:execute|bash|sh)?\s*\n(.*?)```'
        matches = re.findall(code_block_pattern, message, re.DOTALL | re.IGNORECASE)

        if matches:
            # Take the first code block that looks like a command
            for match in matches:
                command = match.strip()
                if command:
                    return command

        # Fall back to legacy EXECUTE: format (single line)
        for line in message.split('\n'):
            line = line.strip()
            if line.startswith("EXECUTE:"):
                command = line.split("EXECUTE:", 1)[1].strip()
                if command:
                    return command

        return None

    async def setup(self, environment=None, **kwargs) -> list[str]:
        """Commands to run in container before agent execution."""
        return []  # No setup needed - we execute via environment.exec()

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment = None,
        context=None,
        **kwargs
    ) -> None:
        """Execute the coding task using LLM and environment.exec().

        Args:
            instruction: The task/instruction to execute
            environment: Harbor environment for command execution
            context: AgentContext to populate with results
        """
        if environment is None:
            raise ValueError("environment is required for execution")

        # Initialize LLM client
        client, model = get_llm_client(self._model_name)
        use_openai_client = isinstance(client, OpenAI)

        # Build conversation
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {instruction}\n\nStart by exploring the current directory."}
        ]

        max_iterations = 50
        trajectory = []

        for i in range(max_iterations):
            # Get LLM response
            if use_openai_client:
                response = client.chat.completions.create(model=model, messages=messages)
                assistant_message = response.choices[0].message.content or ""
            else:
                response = client.chat(messages)
                assistant_message = response.content or ""

            # Add to trajectory
            trajectory.append({"role": "assistant", "content": assistant_message})
            messages.append({"role": "assistant", "content": assistant_message})

            # Check if task is complete
            if "TASK COMPLETE" in assistant_message:
                break

            # Extract command to execute - supports both formats:
            # 1. ```execute\ncommand\n``` (preferred, multi-line)
            # 2. EXECUTE: command (legacy, single-line)
            command = self._extract_command(assistant_message)

            if not command:
                # No command found, ask for clarification
                messages.append({
                    "role": "user",
                    "content": "Please provide a command in a ```execute code block, or say 'TASK COMPLETE' if done."
                })
                continue

            # Execute command in container
            try:
                result = await environment.exec(command)
                output = result.stdout if hasattr(result, 'stdout') else str(result)
                stderr = result.stderr if hasattr(result, 'stderr') else ""

                if stderr:
                    output = f"{output}\n\nSTDERR:\n{stderr}"

            except Exception as e:
                output = f"Error executing command: {e}"

            # Add result to conversation
            trajectory.append({"role": "command", "command": command, "output": output})
            messages.append({
                "role": "user",
                "content": f"Command output:\n```\n{output[:10000]}\n```\n\nContinue with the task."
            })

        # Save trajectory to file for debugging
        # Try multiple ways to find the logs directory
        logs_dir = None

        # Check instance, kwargs, context
        if self._logs_dir:
            logs_dir = self._logs_dir
        elif 'logs_dir' in kwargs:
            logs_dir = kwargs['logs_dir']
        elif context and hasattr(context, 'logs_dir') and context.logs_dir:
            logs_dir = context.logs_dir

        if logs_dir:
            trajectory_path = Path(logs_dir) / "trajectory.json"
        else:
            # Fallback - save to cwd/agent_trajectory.json
            trajectory_path = Path.cwd() / "agent_trajectory.json"

        try:
            trajectory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(trajectory_path, 'w') as f:
                json.dump({
                    "model": self._model_name,
                    "instruction": instruction,
                    "iterations": len(trajectory),
                    "trajectory": trajectory
                }, f, indent=2, default=str)
            print(f"Trajectory saved to: {trajectory_path}")
        except Exception as e:
            print(f"Warning: Could not save trajectory to {trajectory_path}: {e}")

        # Populate context with trajectory if available
        if context and hasattr(context, 'trajectory'):
            context.trajectory = trajectory
