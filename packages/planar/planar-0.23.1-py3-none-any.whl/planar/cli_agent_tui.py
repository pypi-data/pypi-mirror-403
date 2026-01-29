"""Minimal Rich-based renderer for the Planar CLI agent session."""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Literal, Sequence, cast

from prompt_toolkit import PromptSession
from prompt_toolkit.filters import is_done
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.shortcuts import choice as prompt_choice
from prompt_toolkit.styles import Style
from rich.console import Console, RenderableType
from rich.markdown import Markdown
from rich.status import Status
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

_PROMPT_PLACEHOLDER = "Extend the Planar workflow with..."
_FOLLOW_UP_PROMPT = "Provide the next instruction (or type 'exit' to finish)"
_PERMISSION_FEEDBACK_PLACEHOLDER = "Share feedback or press Enter to skip"
ACTIONS_HELP_TEXT = "Enter the number of an option · press Enter to submit"

PermissionChoice = Literal["allow", "allow_with_updates", "deny"]

_CHOICE_STYLE = Style.from_dict(
    {
        "prompt": "bold",
        "selected-option": "bold cyan",
    }
)


def _format_tool_payload(
    tool_name: str, payload: object, *, language_hint: str | None = None
) -> RenderableType:
    """Return a renderable for a tool payload."""
    if payload is None:
        return Text("(no payload)", style="dim")

    if isinstance(payload, str):
        if language_hint:
            return Syntax(payload, language_hint, theme="ansi_dark", word_wrap=True)
        return Text(payload)

    if isinstance(payload, (bytes, bytearray)):
        return Syntax(
            payload.decode("utf-8", errors="replace"), language_hint or "text"
        )

    if tool_name == "Edit" and isinstance(payload, dict):
        return Syntax(payload.get("file_path", ""), "text", theme="ansi_dark")

    try:
        serialized = json.dumps(payload, indent=2, sort_keys=True)
    except TypeError:
        return Text(repr(payload), style="grey50")

    return Syntax(serialized, "json", theme="ansi_dark", word_wrap=True)


@dataclass
class AgentTUI:
    """Rich-based CLI helper for rendering agent interactions."""

    session_name: str
    permission_mode: str
    allowed_tools: Sequence[str]
    workspace: str
    console: Console = field(default_factory=lambda: Console(soft_wrap=True))
    _tool_invocations: int = field(default=0, init=False)
    _started: bool = field(default=False, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)
    _status: Status | None = field(default=None, init=False, repr=False)
    _io_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)
    _banner_rendered: bool = field(default=False, init=False, repr=False)
    _multiline_key_bindings: KeyBindings | None = field(
        default=None, init=False, repr=False
    )

    async def __aenter__(self) -> "AgentTUI":
        await self.start()
        return self

    async def __aexit__(self, _exc_type, _exc, _tb) -> None:
        await self.close()

    async def start(self) -> None:
        if self._started:
            return
        self._started = True

    async def close(self) -> None:
        if not self._started or self._closed:
            return
        await self.clear_status()
        self._closed = True

    async def show_banner(self, instruction: str | None = None) -> None:
        await self._ensure_started()
        if self._banner_rendered:
            return
        tools_text = ", ".join(self.allowed_tools) if self.allowed_tools else "(none)"
        metadata = Table.grid(padding=(0, 1))
        metadata.add_column(style="grey58", no_wrap=True)
        metadata.add_column()
        metadata.add_row("workspace", Text(self.workspace, style="cyan"))
        mode_style = "green" if self.permission_mode == "plan" else "yellow"
        metadata.add_row("mode", Text(self.permission_mode, style=mode_style))
        metadata.add_row("tools", Text(tools_text, style="yellow"))
        metadata.add_row("session", Text(self.session_name, style="magenta"))

        async with self._io_lock:
            self._stop_status()
            self.console.print()
            self.console.print(Text("PLANAR AGENT", style="bold cyan"))
            self.console.print()
            self.console.print(metadata)
            self.console.print()
        self._banner_rendered = True

    async def render_user_prompt(
        self, prompt_text: str, *, follow_up: bool = False
    ) -> None:
        title = "user" if not follow_up else "user (follow-up)"
        content = (
            Text(prompt_text)
            if prompt_text.strip()
            else Text("(no prompt)", style="dim")
        )
        await self._print_entry(
            title,
            content,
            prefix=">",
            title_style="cyan",
        )
        await self.show_status("thinking…", style="magenta")

    async def render_assistant_text(self, text: str) -> None:
        await self.clear_status()
        content = Markdown(text) if text.strip() else Text("(no response)", style="dim")
        await self._print_entry(
            "assistant",
            content,
            prefix="<",
            title_style="green",
        )

    async def render_tool_use(self, tool_name: str, payload: object) -> None:
        await self.clear_status()
        if tool_name == "ExitPlanMode":
            return
        self._tool_invocations += 1
        language_hint = "bash" if tool_name.lower() == "bash" else None
        renderable = _format_tool_payload(
            tool_name,
            payload,
            language_hint=language_hint,
        )
        await self._print_entry(
            f"tool {self._tool_invocations}: {tool_name}",
            renderable,
            prefix="-",
            title_style="yellow",
        )

    async def render_permission_request(
        self,
        tool_name: str,
        payload: object,
        suggestions: Sequence[object],
    ) -> None:
        await self.clear_status()
        table = Table.grid(padding=(0, 1))
        table.add_column(style="grey58", no_wrap=True)
        table.add_column()
        table.add_row("tool", Text(tool_name, style="yellow"))
        table.add_row("payload", _format_tool_payload(tool_name, payload))
        suggestions_renderable = (
            _format_tool_payload(
                "permission-suggestions", list(suggestions), language_hint="json"
            )
            if suggestions
            else Text("(no suggestions)", style="dim")
        )
        table.add_row("suggestions", suggestions_renderable)
        await self._print_entry(
            "permission request",
            table,
            prefix="!",
            title_style="yellow",
        )

    async def render_session_result(
        self,
        *,
        duration_ms: int | None,
        total_cost: float | None,
    ) -> None:
        await self.clear_status()
        table = Table.grid(padding=(0, 1))
        table.add_column(style="grey58", no_wrap=True)
        table.add_column(justify="right")
        table.add_row(
            "duration", f"{duration_ms} ms" if duration_ms is not None else "–"
        )
        table.add_row("cost", f"${total_cost:.4f}" if total_cost is not None else "–")
        await self._print_entry(
            "session summary",
            table,
            prefix="=",
            title_style="cyan",
        )

    async def render_changed_files(self, files: Sequence[str]) -> None:
        if not files:
            return
        table = Table.grid()
        table.add_column()
        for file_path in files:
            table.add_row(Text(file_path, style="green"))
        await self._print_entry(
            "changed files",
            table,
            prefix="+",
            title_style="green",
        )

    async def render_plan_preview(self, plan_text: str) -> None:
        if not plan_text.strip():
            return
        await self._print_entry(
            "proposed plan",
            Markdown(plan_text),
            prefix="~",
            title_style="yellow",
        )

    async def show_status(self, message: str, *, style: str = "grey50") -> None:
        await self._ensure_started()
        async with self._io_lock:
            self._stop_status()
            self._status = Status(
                message,
                console=self.console,
                spinner="dots",
                spinner_style=style,
            )
            self._status.start()

    async def clear_status(self) -> None:
        await self._ensure_started()
        async with self._io_lock:
            self._stop_status()

    async def log_text(self, text: str, *, style: str | None = None) -> None:
        await self._print_entry(
            text,
            None,
            prefix="-",
            title_style=style,
            spacer=True,
            leading_space=True,
        )

    async def prompt_for_initial(self, instruction: str) -> str:
        return await self._prompt_input(
            instruction,
            placeholder=_PROMPT_PLACEHOLDER,
            multiline=True,
        )

    async def prompt_for_follow_up(self) -> str:
        return await self._prompt_input(
            _FOLLOW_UP_PROMPT,
            placeholder="",
            multiline=True,
        )

    async def confirm_exit_plan(self, plan_text: str) -> PermissionChoice:
        await self.clear_status()
        if plan_text.strip():
            await self.render_plan_preview(plan_text)

        choice = await self._prompt_options(
            "Approve plan execution?",
            options=[
                ("yes – execute plan", "allow"),
                ("no – stay in plan mode", "deny"),
            ],
        )
        if choice == "allow":
            await self.log_text("exiting plan mode", style="green")
            return "allow"
        await self.log_text("staying in plan mode", style="yellow")
        return "deny"

    async def prompt_permission_choice(
        self, tool_name: str, *, allow_updates: bool
    ) -> PermissionChoice:
        options: list[tuple[str, PermissionChoice]] = [
            ("yes – allow tool use", "allow")
        ]
        if allow_updates:
            options.append(
                ("yes – allow and apply suggested permissions", "allow_with_updates")
            )
        options.append(("no – provide feedback", "deny"))

        choice = await self._prompt_options(f"{tool_name} permission?", options=options)
        if choice == "allow":
            await self.log_text(f"approved {tool_name}", style="green")
            return "allow"
        if choice == "allow_with_updates":
            await self.log_text(
                f"approved {tool_name} with suggested permissions",
                style="green",
            )
            return "allow_with_updates"
        await self.log_text(f"denied {tool_name}", style="yellow")
        return "deny"

    async def prompt_for_permission_feedback(self, tool_name: str) -> str:
        return await self._prompt_input(
            f"{tool_name} feedback (optional)",
            placeholder=_PERMISSION_FEEDBACK_PLACEHOLDER,
            multiline=True,
        )

    async def _prompt_input(
        self,
        message: str,
        *,
        placeholder: str,
        multiline: bool,
    ) -> str:
        await self._ensure_started()
        helper_text = (
            "Press Enter to submit · Ctrl+Enter or Ctrl+J for newline · Ctrl+C to cancel"
            if multiline
            else "Press Enter to submit · Ctrl+C to cancel"
        )

        async with self._io_lock:
            self._stop_status()
            self.console.print()
            self.console.print(Text(message, style="bold"))
            if placeholder:
                self.console.print(Text(placeholder, style="grey58"))
            self.console.print(Text(helper_text, style="grey35"))
            self.console.print(Text(self._prompt_metadata_line(), style="grey35"))
            self.console.print()

        return await self._read_line("> ", multiline=multiline)

    async def _prompt_options(
        self,
        message: str,
        *,
        options: Sequence[tuple[str, str]],
        helper_text: str | None = None,
    ) -> str:
        if not options:
            raise ValueError("options are required")
        await self._ensure_started()

        helper = helper_text or ACTIONS_HELP_TEXT
        message_lines = [message]
        if helper:
            message_lines.append(helper)
        message_lines.append(self._prompt_metadata_line())
        prompt_message = "\n".join(message_lines)
        choice_options = [(value, label) for label, value in options]

        async with self._io_lock:
            self._stop_status()
            result = await asyncio.to_thread(
                self._prompt_choice_sync,
                prompt_message,
                choice_options,
            )
            self.console.print()
        return result

    async def _read_line(self, prompt: str, *, multiline: bool = False) -> str:
        key_bindings = self._get_multiline_key_bindings() if multiline else None
        return await asyncio.to_thread(self._prompt_sync, prompt, key_bindings)

    def _prompt_sync(self, prompt: str, key_bindings: KeyBindings | None) -> str:
        session = PromptSession(key_bindings=key_bindings, erase_when_done=True)
        return session.prompt(prompt)

    def _prompt_choice_sync(
        self,
        message: str,
        options: Sequence[tuple[str, str]],
    ) -> str:
        return prompt_choice(
            message=message,
            options=list(options),
            style=_CHOICE_STYLE,
            show_frame=cast(bool, ~is_done),
        )

    async def _print_entry(
        self,
        title: str,
        body: RenderableType | None,
        *,
        prefix: str,
        title_style: str | None = None,
        spacer: bool = True,
        leading_space: bool = False,
    ) -> None:
        await self._ensure_started()
        async with self._io_lock:
            self._stop_status()
            if leading_space:
                self.console.print()
            header = Text(prefix + " ", style="grey50")
            header.append(title, style=title_style)
            self.console.print(header)
            if body is not None:
                self.console.print(body)
            if spacer:
                self.console.print()

    async def _ensure_started(self) -> None:
        if not self._started:
            await self.start()

    def _stop_status(self) -> None:
        if self._status is None:
            return
        self._status.stop()
        self._status = None

    def _prompt_metadata_line(self) -> str:
        tools = ", ".join(self.allowed_tools) if self.allowed_tools else "(none)"
        return f"mode: {self.permission_mode} · tools: {tools}"

    def _get_multiline_key_bindings(self) -> KeyBindings:
        if self._multiline_key_bindings is not None:
            return self._multiline_key_bindings
        key_bindings = KeyBindings()

        def _insert_newline(event: KeyPressEvent) -> None:
            event.current_buffer.insert_text("\n")

        key_bindings.add("c-j")(_insert_newline)
        try:
            key_bindings.add("c-enter")(_insert_newline)
        except ValueError:
            # Some terminals do not distinguish ctrl+enter; ignore if unsupported.
            pass

        self._multiline_key_bindings = key_bindings
        return key_bindings
