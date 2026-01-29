import asyncio
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

import typer
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ClaudeSDKError,
    CLINotFoundError,
    PermissionResultAllow,
    PermissionResultDeny,
    ProcessError,
    ResultMessage,
    TextBlock,
    ToolPermissionContext,
    ToolUseBlock,
)
from claude_agent_sdk.types import PermissionUpdate

from planar.cli_agent_tui import AgentTUI
from planar.docs_catalog import render_docs_index
from planar.logging import get_logger

logger = get_logger(__name__)

DEFAULT_ALLOWED_TOOLS = (
    "Read",
    # "Write",
    # "Edit",
    # "MultiEdit",
    "Task",
)


ENV_PASSTHROUGH_KEYS = (
    "PLANAR_ENV",
    "PLANAR_CONFIG",
    "PLANAR_ENTRY_POINT",
)


def _get_system_prompt() -> str:
    docs_overview = render_docs_index()
    return f"""
You are an expert coding agent that can read and modify files in the current repository.
You are experienced in the Planar framework and can use it to build and modify Planar apps.

## Commands

- Type checking: `uv run pyright`
- Format code: `uv run ruff format`

## Tooling

- Always use `uv` to run commands rather than `python` or `pip`

## Code Style

- Preserve existing code style and formatting.
- Imports: stdlib first, third-party, then local modules (alphabetical within groups)
- Avoid importing in the middle of a file, import at the top of the file unless there's a good reason, example:
    - Large optional dependencies (ie. AI providers)
- Use type hints for all function parameters and return values
- Optional and Union type hints should use `T | None` style
- Classes use PascalCase, functions/variables use snake_case
- Error handling: catch specific exceptions, use assert for invariants
- Return types use string literals for self-references (e.g., `def method(self) -> "Class":`)
- Use f-strings for string formatting
- Write docstrings for public methods (parameters, return values, raised exceptions)
- Single responsibility classes with clear public/private method separation
- NEVER use `from __future__ import annotations` as python 3.12+ doesn't require it and can cause issues with type introspection
- Keep lines under 100 characters (E501 is ignored in ruff.toml)
- Don't overly comment every line of body of code, only comment on complex logic or edge cases where the reader might not understand the intent. The code should be self-documenting.
- IMPORTANT: Don't sprinkle obvious comments everywhere!

## Persistence

- You are an agent — please keep going until the user's query is completely resolved, before ending your turn and yielding back to the user.
- Only terminate your turn when you are sure that the problem is solved.
- Let the user know if they are asking for something that is not possible.

## Documentation

The following matches the output of `uv run planar docs`. When you need deeper detail, run
`uv run planar docs <section>` (or `planar docs <section>` if you already have an environment)
to fetch the specific document on demand.

{docs_overview}
"""


def _compute_allowed_tools(
    allow_overrides: Sequence[str],
    deny_overrides: Sequence[str],
) -> list[str]:
    deny_set = {tool for tool in deny_overrides}
    allowed: list[str] = [
        tool for tool in DEFAULT_ALLOWED_TOOLS if tool not in deny_set
    ]
    for tool in allow_overrides:
        if tool in deny_set or tool in allowed:
            continue
        allowed.append(tool)
    return allowed


def _resolve_additional_dirs(directories: Sequence[Path]) -> list[str | Path]:
    resolved: list[str | Path] = []
    for directory in directories:
        dir_path = directory.expanduser().resolve()
        if not dir_path.exists():
            typer.secho(f"Additional directory not found: {dir_path}", err=True)
            raise typer.Exit(code=1)
        if not dir_path.is_dir():
            typer.secho(f"Additional path is not a directory: {dir_path}", err=True)
            raise typer.Exit(code=1)
        resolved.append(dir_path)
    return resolved


def _normalize_permission_suggestions(
    suggestions: Sequence[object],
) -> tuple[list[PermissionUpdate], list[object]]:
    normalized: list[PermissionUpdate] = []
    render_payload: list[object] = []

    for suggestion in suggestions:
        if isinstance(suggestion, PermissionUpdate):
            normalized.append(suggestion)
            render_payload.append(suggestion.to_dict())
        else:
            render_payload.append(suggestion)

    return normalized, render_payload


async def _run_agent_session(
    client: ClaudeSDKClient,
    tui: AgentTUI,
    *,
    write_tool_names: set[str],
    changed_files: set[str],
) -> bool:
    async for message in client.receive_messages():
        if isinstance(message, AssistantMessage):
            for block in getattr(message, "content", []):
                if isinstance(block, TextBlock):
                    await tui.render_assistant_text(block.text)
                elif isinstance(block, ToolUseBlock):
                    tool_name = getattr(block, "name", "")
                    tool_payload = getattr(block, "input", None)
                    if tool_name in write_tool_names:
                        file_path = (
                            tool_payload.get("file_path")
                            if isinstance(tool_payload, dict)
                            else None
                        )
                        if file_path:
                            changed_files.add(str(file_path))
                    await tui.render_tool_use(tool_name, tool_payload)
        elif isinstance(message, ResultMessage):
            duration_ms = getattr(message, "duration_ms", None)
            total_cost = getattr(message, "total_cost_usd", None)
            await tui.render_session_result(
                duration_ms=duration_ms,
                total_cost=total_cost,
            )
            return True
    return False


async def _execute_agent(
    prompt_text: str,
    options: ClaudeAgentOptions,
    session_name: str,
    *,
    tui: AgentTUI,
) -> int:
    current_prompt = prompt_text
    changed_files: set[str] = set()
    write_tool_names = {"Write", "Edit", "MultiEdit"}

    exit_code = 0

    await tui.show_banner()
    await tui.render_user_prompt(current_prompt)

    try:
        async with ClaudeSDKClient(options=options) as client:
            while True:
                await client.query(current_prompt)
                stream_active = await _run_agent_session(
                    client,
                    tui,
                    write_tool_names=write_tool_names,
                    changed_files=changed_files,
                )

                if not stream_active:
                    break

                follow_up_prompt = await tui.prompt_for_follow_up()
                if follow_up_prompt.strip().lower() in {"exit", "quit"}:
                    await tui.log_text("ending session", style="grey50")
                    break

                current_prompt = follow_up_prompt
                await tui.render_user_prompt(current_prompt, follow_up=True)
    except KeyboardInterrupt:
        exit_code = 130
        logger.info("agent interrupted", session_name=session_name)
        typer.echo("Interrupted. Agent stopped.")
    except CLINotFoundError:
        exit_code = 1
        typer.secho(
            "Claude Code CLI not found. Install it following the Claude Code SDK instructions.",
            err=True,
        )
    except ProcessError as exc:
        exit_code = 1
        stderr = getattr(exc, "stderr", "")
        process_code = getattr(exc, "exit_code", None)
        typer.secho(
            f"Claude Code process failed (code {process_code}): {stderr}",
            err=True,
        )
    except ClaudeSDKError as exc:
        exit_code = 1
        typer.secho(f"Claude SDK error: {exc}", err=True)
    except Exception as exc:  # pragma: no cover - defensive
        exit_code = 1
        typer.secho(f"Unexpected error: {exc}", err=True)
    finally:
        if exit_code == 0 and changed_files:
            await tui.render_changed_files(sorted(changed_files))
    return exit_code


def agent_command(
    prompt: str | None = typer.Argument(
        None,
        help="Describe what you want the Planar agent to build.",
    ),
    file: Path | None = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to a file whose contents will be used as the agent prompt.",
    ),
    allow_tool: list[str] | None = typer.Option(
        None,
        "--allow-tool",
        help="Additional Claude tools to allow (repeatable).",
    ),
    deny_tool: list[str] | None = typer.Option(
        None,
        "--deny-tool",
        help="Claude tools to remove from the default allow list (repeatable).",
    ),
    add_dir: list[Path] | None = typer.Option(
        None,
        "--add-dir",
        help="Additional directories the agent can access.",
    ),
) -> None:
    asyncio.run(
        _agent_command_async(
            prompt=prompt,
            file=file,
            allow_tool=tuple(allow_tool or ()),
            deny_tool=tuple(deny_tool or ()),
            add_dir=tuple(add_dir or ()),
        )
    )


async def _agent_command_async(
    *,
    prompt: str | None,
    file: Path | None,
    allow_tool: tuple[str, ...],
    deny_tool: tuple[str, ...],
    add_dir: tuple[Path, ...],
) -> None:
    if prompt and file:
        typer.secho("Provide either PROMPT or --file, not both.", err=True)
        raise typer.Exit(code=2)

    needs_interactive_prompt = False
    if not prompt and not file:
        if not sys.stdin.isatty():
            typer.secho("A prompt is required when stdin is non-interactive.", err=True)
            raise typer.Exit(code=2)
        needs_interactive_prompt = True

    allowed_tools = _compute_allowed_tools(allow_tool, deny_tool)
    additional_dirs = _resolve_additional_dirs(add_dir)

    permission_mode = "plan"
    cwd = Path.cwd().resolve()
    session_name = f"{cwd.name}-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

    tui = AgentTUI(
        session_name=session_name,
        permission_mode=permission_mode,
        allowed_tools=allowed_tools,
        workspace=str(cwd),
    )

    prompt_text: str
    if file is not None:
        target = file.expanduser()
        if not target.is_file():
            typer.secho(f"Prompt file not found: {target}", err=True)
            raise typer.Exit(code=1)
        try:
            prompt_text = target.read_text(encoding="utf-8")
        except OSError as exc:
            typer.secho(f"Failed to read prompt file: {exc}", err=True)
            raise typer.Exit(code=1) from exc
    else:
        prompt_text = prompt or ""

    try:
        if needs_interactive_prompt:
            instruction_text = "Describe what you want the Planar agent to build"
            await tui.show_banner(instruction=instruction_text)
            while True:
                try:
                    prompt_text = await tui.prompt_for_initial(instruction_text)
                except EOFError as exc:
                    typer.secho("Prompt input aborted.", err=True)
                    raise typer.Exit(code=1) from exc
                except KeyboardInterrupt:
                    logger.info("agent prompt interrupted", session_name=session_name)
                    raise typer.Exit(code=130)

                if prompt_text.strip():
                    break

                await tui.log_text(
                    "Prompt content is empty. Provide some requirements for the agent.",
                    style="red",
                )
        elif not prompt_text.strip():
            typer.secho(
                "Prompt content is empty. Provide some requirements for the agent.",
                err=True,
            )
            raise typer.Exit(code=2)

        system_prompt = _get_system_prompt()

        env_passthrough = {
            key: value
            for key in ENV_PASSTHROUGH_KEYS
            if (value := os.environ.get(key)) is not None
        }

        async def tool_use_callback(
            tool_name: str,
            input_data: dict,
            context: ToolPermissionContext,
        ) -> PermissionResultAllow | PermissionResultDeny:
            # wrap in try/except since error doesn't propagate properly
            try:
                normalized_updates, render_payload = _normalize_permission_suggestions(
                    context.suggestions
                )

                await tui.render_permission_request(
                    tool_name,
                    input_data,
                    render_payload,
                )

                if tool_name == "ExitPlanMode":
                    plan_text = (
                        input_data.get("plan", "")
                        if isinstance(input_data, dict)
                        else ""
                    )
                    decision = await tui.confirm_exit_plan(plan_text)
                else:
                    decision = await tui.prompt_permission_choice(
                        tool_name,
                        allow_updates=bool(normalized_updates),
                    )

                match decision:
                    case "allow":
                        return PermissionResultAllow()
                    case "allow_with_updates":
                        await tui.log_text(
                            f"allowing {tool_name} with updates {normalized_updates}"
                        )
                        return PermissionResultAllow(
                            updated_permissions=normalized_updates
                        )
                    case "deny":
                        feedback = ""
                        try:
                            feedback = await tui.prompt_for_permission_feedback(
                                tool_name
                            )
                        except (KeyboardInterrupt, EOFError):
                            feedback = ""
                        message = feedback.strip() or f"User declined {tool_name}"
                        return PermissionResultDeny(message=message)
                    case _:
                        raise ValueError(f"Invalid decision: {decision}")
            except Exception as exc:
                await tui.log_text(f"error rendering permission request: {exc}")
                raise

        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            cwd=str(cwd),
            allowed_tools=allowed_tools,
            permission_mode=permission_mode,
            add_dirs=additional_dirs,
            # Not sure if these env vars will be useful, but let's keep them for now.
            env=env_passthrough,
            can_use_tool=tool_use_callback,
        )

        exit_code = await _execute_agent(
            prompt_text,
            options,
            session_name,
            tui=tui,
        )
        if exit_code != 0:
            raise typer.Exit(code=exit_code)
    finally:
        await tui.close()


__all__ = ["agent_command"]
