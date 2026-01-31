"""REPL (Read-Eval-Print Loop) for interactive mode.

This module provides the main interactive loop for the CLI.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from henchman.cli.commands import CommandContext, CommandRegistry, parse_command
from henchman.cli.commands.builtins import get_builtin_commands
from henchman.cli.console import OutputRenderer
from henchman.cli.input import create_session, expand_at_references, is_slash_command
from henchman.core.agent import Agent
from henchman.core.events import AgentEvent, EventType
from henchman.core.session import Session, SessionManager, SessionMessage
from henchman.providers.base import ModelProvider, ToolCall
from henchman.tools.registry import ToolRegistry

if TYPE_CHECKING:
    from henchman.config.schema import Settings


@dataclass
class ReplConfig:
    """Configuration for the REPL.

    Attributes:
        prompt: The prompt string to display.
        system_prompt: System prompt for the agent.
        auto_save: Whether to auto-save sessions on exit.
        history_file: Path to history file.
        base_tool_iterations: Base limit for tool iterations per turn.
        max_tool_calls_per_turn: Maximum tool calls allowed per turn.
    """

    prompt: str = "❯ "
    system_prompt: str = ""
    auto_save: bool = True
    history_file: Path | None = None
    base_tool_iterations: int = 25
    max_tool_calls_per_turn: int = 100


class Repl:
    """Interactive REPL for the CLI.

    The Repl class orchestrates the main interaction loop, connecting
    the Agent, InputHandler, OutputRenderer, and command system.

    Example:
        >>> provider = DeepSeekProvider(api_key="...")
        >>> repl = Repl(provider=provider)
        >>> await repl.run()
    """

    def __init__(
        self,
        provider: ModelProvider,
        console: Console | None = None,
        config: ReplConfig | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize the REPL.

        Args:
            provider: Model provider for LLM interactions.
            console: Rich console for output.
            config: REPL configuration.
            settings: Application settings for context limits, etc.
        """
        self.provider = provider
        self.console = console or Console()
        self.config = config or ReplConfig()
        self.settings = settings
        self.renderer = OutputRenderer(console=self.console)

        # Initialize tool registry with built-in tools
        self.tool_registry = ToolRegistry()
        self._register_builtin_tools()

        # Determine max_tokens from settings
        # Apply compaction_threshold to get the actual limit
        max_tokens = 0
        model_name: str | None = None
        if settings:
            context = settings.context
            if context.max_tokens > 0:
                # Apply threshold: compact when we reach threshold% of max
                max_tokens = int(context.max_tokens * context.compaction_threshold)

        # Get model name from provider if available
        if hasattr(provider, "default_model"):
            model_name = provider.default_model

        # Initialize agent
        self.agent = Agent(
            provider=provider,
            tool_registry=self.tool_registry,
            system_prompt=self.config.system_prompt,
            base_tool_iterations=self.config.base_tool_iterations,
            max_tokens=max_tokens,
            model=model_name,
        )

        # Initialize command registry
        self.command_registry = CommandRegistry()
        for cmd in get_builtin_commands():
            self.command_registry.register(cmd)

        self.running = False

        # Initialize PromptSession
        history_file = self.config.history_file or Path.home() / ".henchman_history"
        self.prompt_session = create_session(
            history_file,
            bottom_toolbar=self._get_toolbar_status
        )

        # Session management (can be set externally for testing)
        self.session_manager: SessionManager | None = None
        self.session: Session | None = None

        # RAG system (set externally by app.py)
        self.rag_system: object | None = None

    def _get_toolbar_status(self) -> list[tuple[str, str]]:
        """Get status bar content."""
        from henchman.utils.tokens import TokenCounter

        status = []

        # Plan Mode
        plan_mode = self.session.plan_mode if self.session else False
        if plan_mode:
            status.append(("bg:yellow fg:black bold", " PLAN MODE "))
        else:
            status.append(("bg:blue fg:white bold", " CHAT "))

        # Tokens
        try:
            msgs = self.agent.get_messages_for_api()
            tokens = TokenCounter.count_messages(msgs)
            status.append(("", f" Tokens: ~{tokens} "))
        except Exception:
            pass

        return status

    def _register_builtin_tools(self) -> None:
        """Register built-in tools with the registry."""
        from henchman.tools.builtins import (
            AskUserTool,
            EditFileTool,
            GlobTool,
            GrepTool,
            LsTool,
            ReadFileTool,
            ShellTool,
            WebFetchTool,
            WriteFileTool,
        )

        tools = [
            AskUserTool(),
            ReadFileTool(),
            WriteFileTool(),
            EditFileTool(),
            LsTool(),
            GlobTool(),
            GrepTool(),
            ShellTool(),
            WebFetchTool(),
        ]
        for tool in tools:
            self.tool_registry.register(tool)

    async def run(self) -> None:
        """Run the main REPL loop.

        This method runs until the user exits with /quit, Ctrl+C, or Ctrl+D.
        """
        self.running = True
        self._print_welcome()

        try:
            while self.running:
                try:
                    user_input = await self._get_input()
                    should_continue = await self.process_input(user_input)
                    if not should_continue:
                        break
                except KeyboardInterrupt:
                    # In PromptSession, Ctrl-C raises KeyboardInterrupt
                    # We treat it as clearing the line or exiting if repeated
                    continue
                except EOFError:
                    self.console.print()
                    break
        finally:
            self.running = False
            self._auto_save_session()
            self._print_goodbye()

    def _print_welcome(self) -> None:
        """Print welcome message."""
        self.console.print(
            "[bold blue]Henchman-AI[/] - /help for commands, /quit to exit\n"
        )

    def _print_goodbye(self) -> None:
        """Print goodbye message."""
        self.console.print("[dim]Goodbye![/]")

    def _auto_save_session(self) -> None:
        """Auto-save the session if enabled and session has content."""
        if not self.config.auto_save:
            return
        if self.session_manager is None or self.session is None:
            return
        if len(self.session.messages) == 0:
            return

        self.session_manager.save(self.session)

    async def _get_input(self) -> str:
        """Get input from the user.

        Returns:
            User input string.

        Raises:
            KeyboardInterrupt: If user presses Ctrl+C.
            EOFError: If user presses Ctrl+D.
        """
        return await self.prompt_session.prompt_async(self.config.prompt)

    async def process_input(self, user_input: str) -> bool:
        """Process a single user input.

        Args:
            user_input: The user's input string.

        Returns:
            True to continue running, False to exit.
        """
        # Skip empty input
        stripped = user_input.strip()
        if not stripped:
            return True

        # Handle slash commands
        if is_slash_command(stripped):
            return await self._handle_command(stripped)

        # Expand @file references
        expanded = await expand_at_references(stripped)

        # Run through agent
        await self._run_agent(expanded)
        return True

    async def _handle_command(self, input_text: str) -> bool:
        """Handle a slash command.

        Args:
            input_text: The command input (with leading /).

        Returns:
            True to continue running, False to exit.
        """
        parsed = parse_command(input_text)
        if parsed is None:
            return True

        cmd_name, args = parsed

        # Special handling for /quit
        if cmd_name == "quit":
            return False

        # Special handling for /clear - clear agent history
        if cmd_name == "clear":
            self.agent.clear_history()
            self.renderer.console.clear()
            self.renderer.success("History cleared")
            return True

        # Try to execute the command
        cmd = self.command_registry.get(cmd_name)
        if cmd is None:
            self.renderer.error(f"Unknown command: /{cmd_name}")
            self.renderer.muted("Type /help for available commands")
            return True

        ctx = CommandContext(
            console=self.console,
            args=args,
            agent=self.agent,
            tool_registry=self.tool_registry,
            session=self.session,
            repl=self,
        )
        await cmd.execute(ctx)
        return True

    async def _run_agent(self, user_input: str) -> None:
        """Run the agent with user input.

        Args:
            user_input: The processed user input.
        """
        # Record user message to session
        if self.session is not None:
            self.session.messages.append(SessionMessage(role="user", content=user_input))

        # Collect assistant response - now also tracks tool calls for session
        assistant_content: list[str] = []

        try:
            await self._process_agent_stream(
                self.agent.run(user_input),
                assistant_content
            )
        except Exception as e:
            self.renderer.error(f"Error: {e}")

        # Session recording is now handled within _process_agent_stream
        # and _execute_tool_calls to properly capture tool calls and results

    async def _process_agent_stream(
        self,
        event_stream: AsyncIterator[AgentEvent],
        content_collector: list[str] | None = None
    ) -> None:
        """Process an agent event stream, handling tool calls properly.

        This method collects ALL tool calls from a single response before
        executing them, which is required by the OpenAI API.

        Args:
            event_stream: Async iterator of agent events.
            content_collector: Optional list to collect content for session.
        """
        # Check loop limits before processing (unless unlimited mode)
        if not self.agent.unlimited_mode:
            turn = self.agent.turn
            adaptive_limit = turn.get_adaptive_limit(self.config.base_tool_iterations)

            if turn.is_at_limit(self.config.base_tool_iterations):
                self.renderer.error(
                    f"Reached iteration limit ({adaptive_limit}). "
                    "Stopping to prevent infinite loop. Use /unlimited to bypass."
                )
                return

            if turn.tool_count >= self.config.max_tool_calls_per_turn:
                self.renderer.error(
                    f"Reached tool call limit ({self.config.max_tool_calls_per_turn}). "
                    "Stopping to prevent runaway execution."
                )
                return

            # Warn if spinning
            if turn.is_spinning() and turn.iteration > 2:
                self.renderer.warning(
                    "⚠ Possible loop detected: same tool calls or results repeating. "
                    f"Iteration {turn.iteration}/{adaptive_limit}"
                )

        pending_tool_calls: list[ToolCall] = []
        accumulated_content: list[str] = []

        async for event in event_stream:
            if event.type == EventType.CONTENT:
                # Stream content to console
                self.console.print(event.data, end="")
                if content_collector is not None and event.data:
                    content_collector.append(event.data)
                if event.data:
                    accumulated_content.append(event.data)

            elif event.type == EventType.THOUGHT:
                # Show thinking in muted style
                self.renderer.muted(f"[thinking] {event.data}")

            elif event.type == EventType.CONTEXT_COMPACTED:
                # Notify user that context was compacted
                self.renderer.warning(
                    "Context compacted: older messages summarized to fit model limits"
                )

            elif event.type == EventType.TOOL_CALL_REQUEST:
                # Collect tool call - don't execute yet!
                pending_tool_calls.append(event.data)

            elif event.type == EventType.FINISHED:
                self.console.print()

            elif event.type == EventType.ERROR:
                self.renderer.error(str(event.data))

        # After the stream ends, record assistant message to session
        # This captures both content-only responses and tool_calls
        if self.session is not None:
            if pending_tool_calls:
                # Convert ToolCall objects to dicts for session storage
                tool_calls_dicts = [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in pending_tool_calls
                ]
                self.session.messages.append(
                    SessionMessage(
                        role="assistant",
                        content="".join(accumulated_content) if accumulated_content else None,
                        tool_calls=tool_calls_dicts,
                    )
                )
            elif accumulated_content:
                # Content-only response (no tool calls)
                self.session.messages.append(
                    SessionMessage(role="assistant", content="".join(accumulated_content))
                )

        # Execute ALL pending tool calls
        if pending_tool_calls:
            await self._execute_tool_calls(pending_tool_calls, content_collector)

    async def _execute_tool_calls(
        self,
        tool_calls: list[ToolCall],
        content_collector: list[str] | None = None
    ) -> None:
        """Execute a batch of tool calls and continue the agent loop.

        Args:
            tool_calls: List of tool calls to execute.
            content_collector: Optional list to collect content for session.
        """
        # Increment iteration counter (one batch of tool calls = one iteration)
        self.agent.turn.increment_iteration()

        # Execute all tool calls and submit results
        for tool_call in tool_calls:
            if not isinstance(tool_call, ToolCall):
                continue

            self.renderer.muted(f"\n[tool] {tool_call.name}({tool_call.arguments})")

            # Execute the tool
            result = await self.tool_registry.execute(tool_call.name, tool_call.arguments)

            # Record tool call in turn state for loop detection
            self.agent.turn.record_tool_call(
                tool_call_id=tool_call.id,
                tool_name=tool_call.name,
                arguments=tool_call.arguments,
                result=result,
            )

            # Submit result to agent
            self.agent.submit_tool_result(tool_call.id, result.content)

            # Record tool result to session
            if self.session is not None:
                self.session.messages.append(
                    SessionMessage(
                        role="tool",
                        content=result.content,
                        tool_call_id=tool_call.id,
                    )
                )

            # Show result
            if result.success:
                self.renderer.muted(f"[result] {result.content[:200]}...")
            else:
                self.renderer.error(f"[error] {result.error}")

        # Show turn status after tool execution
        self._show_turn_status()

        # Add spacing after tool execution
        self.console.print()

        # Now that ALL results are submitted, continue the agent loop
        await self._process_agent_stream(
            self.agent.continue_with_tool_results(),
            content_collector
        )

    def _show_turn_status(self) -> None:
        """Display current turn status."""
        turn = self.agent.turn
        status = turn.get_status_string(
            base_limit=self.config.base_tool_iterations,
            max_tokens=self.agent.max_tokens,
        )

        # Color based on status
        if turn.is_spinning() or turn.is_approaching_limit(self.config.base_tool_iterations):
            self.renderer.warning(status)
        else:
            self.renderer.muted(status)

    async def _handle_agent_event(
        self, event: AgentEvent, content_collector: list[str] | None = None
    ) -> None:
        """Handle an event from the agent.

        DEPRECATED: Use _process_agent_stream instead for proper tool call handling.
        This method is kept for backwards compatibility with tests.

        Args:
            event: The agent event to handle.
            content_collector: Optional list to collect content for session recording.
        """
        if event.type == EventType.CONTENT:
            # Stream content to console
            self.console.print(event.data, end="")
            # Collect for session recording
            if content_collector is not None and event.data:
                content_collector.append(event.data)

        elif event.type == EventType.THOUGHT:
            # Show thinking in muted style
            self.renderer.muted(f"[thinking] {event.data}")

        elif event.type == EventType.TOOL_CALL_REQUEST:
            # NOTE: In the new flow, tool calls are batched and handled by
            # _process_agent_stream. This path is only for backwards compat.
            pass

        elif event.type == EventType.FINISHED:
            # Print newline after streaming content
            self.console.print()

        elif event.type == EventType.ERROR:
            self.renderer.error(str(event.data))  # pragma: no branch

    async def _handle_tool_call(self, tool_call: ToolCall) -> None:
        """Handle a single tool call from the agent.

        DEPRECATED: Use _execute_tool_calls for proper batched handling.
        This method is kept for backwards compatibility with tests.

        Args:
            tool_call: The tool call to execute.
        """
        if not isinstance(tool_call, ToolCall):
            return

        self.renderer.muted(f"\n[tool] {tool_call.name}({tool_call.arguments})")

        # Execute the tool
        result = await self.tool_registry.execute(tool_call.name, tool_call.arguments)

        # Submit result to agent
        self.agent.submit_tool_result(tool_call.id, result.content)

        # Show result
        if result.success:
            self.renderer.muted(f"[result] {result.content[:200]}...")
        else:
            self.renderer.error(f"[error] {result.error}")

        # NOTE: In the new flow, continue_with_tool_results is called
        # after ALL tool calls are processed. For backwards compat with
        # tests that call this method directly, we don't call continue here.
