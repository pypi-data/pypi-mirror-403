"""Claude API client wrapper with tool use support."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from anthropic import AsyncAnthropic

from .config import Config
from .session_manager import Message
from .tools import FolderTools

if TYPE_CHECKING:
    from .scheduler.tools import SchedulerTools


SYSTEM_PROMPT_TEMPLATE = """You are {user_name}'s personal assistant with access to their "second brain" folder.
This folder contains notes, logs, goals, and documentation.

Your role:
- Answer questions based on the folder contents
- Help {user_name} remember things they've documented
- Provide insights from the data
- Be direct and concise
- Don't be pushy or patronizing

TOOL USAGE:
- Use most tools immediately without asking for permission
- Don't say "I'm going to use X tool" - just do it
- The user trusts you to take action autonomously
{confirmation_tools_section}
CRITICAL RULES - DO NOT HALLUCINATE ACTIONS:
1. When modifying files: MUST use write_file tool. Never claim "I've added X" without calling it.
2. When scheduling tasks: MUST use schedule_task tool. Never claim "I've scheduled X" without calling it.
3. When listing tasks: MUST use list_tasks tool. Never make up task IDs or statuses.
4. If a tool call fails or you didn't call it, say so honestly.
5. If write_file requires confirmation, wait for user to confirm before claiming success.

You have tools to interact with the folder:
- list_files: See what files are available
- read_file: Read specific files
- search_files: Find files containing text
- write_file: Create or update files

You have WEB tools for researching online (if available):
- web_search: Search the web using DuckDuckGo
- web_fetch: Fetch and extract content from a URL

You have a TASK SCHEDULER for autonomous background execution:
- schedule_task: Create tasks that run in the background
- list_tasks: See scheduled tasks and their status
- cancel_task: Cancel a running or pending task
- get_task_results: Check results of a task

You have a send_message tool to send messages directly to the user.
Use it in scheduled tasks for greetings, reminders, and notifications.

USE THE SCHEDULER when the user asks for:
- Time-limited tasks: "search for 5 minutes", "try for an hour"
- Iteration-limited tasks: "try 1000 times", "check 50 names"
- Repeating tasks: "check every hour", "monitor daily"
- Delayed tasks: "remind me in 30 minutes", "check this later"
- Cron schedules: "every day at 9am", "weekly on Monday"

The scheduler runs tasks autonomously in the background, sends progress updates,
and generates a summary when complete. You DO have planning and scheduling capabilities.

FORMATTING:
- Messages are rendered with Telegram HTML. Use these tags for formatting:
  <b>bold</b>, <i>italic</i>, <code>inline code</code>, <pre>code block</pre>
- Do NOT use Markdown formatting (no **, no __, no ```). Use HTML tags instead.
- Plain text without tags is fine for simple responses.

Start by exploring the folder if you need to find information.
Be selective - don't read everything, focus on what the user asks.
"""


class ClaudeClient:
    """Wrapper for Claude API interactions with tool support."""

    MAX_TOOL_ITERATIONS = 10  # Prevent infinite loops

    def __init__(
        self,
        config: Config,
        scheduler_tools: SchedulerTools | None = None,
    ):
        self.config = config
        self.client = AsyncAnthropic(api_key=config.anthropic_api_key)
        self.tools = FolderTools(config, scheduler_tools=scheduler_tools)

    def _build_system_prompt(self) -> str:
        """Build system prompt with dynamic tool confirmation section."""
        confirmation_tools = self.tools.get_tools_requiring_confirmation()

        if confirmation_tools:
            tools_list = ", ".join(confirmation_tools)
            confirmation_section = (
                f"- EXCEPTION: Ask for confirmation before using: {tools_list}\n"
            )
        else:
            confirmation_section = ""

        return SYSTEM_PROMPT_TEMPLATE.format(
            user_name=self.config.user_name,
            confirmation_tools_section=confirmation_section,
        )

    async def chat(
        self,
        user_message: str,
        context: str,
        history: list[Message],
        on_tool_use: Callable[[str], Awaitable[None]] | None = None,
        chat_id: int = 0,
        user_id: int = 0,
    ) -> tuple[str, list[str]]:
        """Send a message to Claude and get a response.

        Args:
            user_message: The user's message
            context: Legacy parameter, now unused (kept for backward compatibility)
            history: Conversation history
            on_tool_use: Optional async callback called when tools are being used.
                         Receives the tool name as argument. Useful for progress updates.
            chat_id: Telegram chat ID (for scheduler tools)
            user_id: Telegram user ID (for scheduler tools)

        Returns:
            Tuple of (Claude's text response, list of tools used)
        """
        system = self._build_system_prompt()

        # Build messages list from history
        messages: list[dict[str, Any]] = []
        for msg in history:
            messages.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                }
            )

        # Add the new user message
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        # Get tool definitions
        tool_definitions = self.tools.get_tool_definitions()

        # Track tools used (deterministic, for appending to response)
        tools_used: list[str] = []

        # Agentic loop
        response = None
        for _ in range(self.MAX_TOOL_ITERATIONS):
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=system,
                messages=messages,  # type: ignore[arg-type]
                tools=tool_definitions,  # type: ignore[arg-type]
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool use blocks
                tool_results: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type == "tool_use":
                        # Track tool usage (deterministic)
                        tools_used.append(block.name)
                        # Notify caller that we're using a tool
                        if on_tool_use:
                            await on_tool_use(block.name)
                        result = await self.tools.execute_async(  # type: ignore[arg-type]
                            block.name,
                            block.input,
                            chat_id=chat_id,
                            user_id=user_id,
                        )
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        )

                # Add assistant response and tool results to messages
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.content,  # type: ignore[arg-type]
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": tool_results,
                    }
                )

            else:
                # No more tool use - done
                break

        # Extract text from final response
        if response is None:
            return "", tools_used

        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "\n".join(text_parts) if text_parts else "", tools_used
