import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Sequence
from unittest.mock import patch

import pytest
from claude_agent_sdk import (
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)
from claude_agent_sdk.types import PermissionUpdate
from typer.testing import CliRunner

from planar import cli_agent
from planar.cli import app


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


class _TTY:
    def isatty(self) -> bool:
        return True


def test_agent_merges_tools_and_dirs(cli_runner: CliRunner, tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def fake_options(**kwargs: Any) -> dict[str, Any]:
        captured["options"] = kwargs
        return kwargs

    async def fake_execute(
        prompt_text: str,
        options: dict[str, Any],
        session_name: str,
        *,
        permission_mode: str,
        allowed_tools: Sequence[str],
        tui: Any,
    ) -> int:
        captured["prompt"] = prompt_text
        captured["session_name"] = session_name
        captured["options_obj"] = options
        captured["permission_mode"] = permission_mode
        captured["allowed_tools_runtime"] = list(allowed_tools)
        captured["tui"] = tui
        return 0

    extra_dir = tmp_path / "exposed"
    extra_dir.mkdir()

    with (
        patch.dict(
            os.environ, {"PLANAR_CONFIG_HOME": str(tmp_path / "config")}, clear=False
        ),
        patch("planar.cli_agent.ClaudeAgentOptions", side_effect=fake_options),
        patch("planar.cli_agent._execute_agent", new=fake_execute),
    ):
        result = cli_runner.invoke(
            app,
            [
                "agent",
                "scaffold a workflow",
                "--allow-tool",
                "Glob",
                "--deny-tool",
                "Bash",
                "--add-dir",
                str(extra_dir),
            ],
        )

    assert result.exit_code == 0
    assert captured["prompt"].strip() == "scaffold a workflow"

    options = captured["options"]
    assert options["permission_mode"] == "plan"
    assert options["allowed_tools"] == [
        "Read",
        "Task",
        "Glob",
    ]
    assert options["add_dirs"] == [extra_dir.resolve()]
    assert options["system_prompt"]
    assert captured["permission_mode"] == "plan"
    assert captured["allowed_tools_runtime"] == options["allowed_tools"]
    assert captured["tui"] is not None
    assert options["can_use_tool"] is not None


def test_agent_interactive_prompt_uses_tui() -> None:
    captured: dict[str, Any] = {}

    class FakeTUI:
        def __init__(self, *_: Any, **__: Any) -> None:
            self.banner_calls = 0
            self.banner_instructions: list[str | None] = []
            self.prompt_messages: list[str] = []
            self.status_messages: list[str] = []
            self.plan_confirmations: list[str] = []
            self.closed = False

        async def show_banner(self, instruction: str | None = None) -> None:
            self.banner_calls += 1
            self.banner_instructions.append(instruction)

        async def prompt_for_initial(self, instruction: str) -> str:
            self.prompt_messages.append(instruction)
            return "build me a workflow"

        async def prompt_for_follow_up(self) -> str:
            return "done"

        async def render_user_prompt(
            self, _prompt_text: str, *, follow_up: bool = False
        ) -> None:
            return

        async def show_status(self, message: str, *, style: str = "") -> None:
            self.status_messages.append(message)

        async def clear_status(self) -> None:
            return

        async def render_permission_request(
            self, tool_name: str, payload: object, suggestions: Sequence[Any]
        ) -> None:
            return

        async def confirm_exit_plan(self, plan_text: str) -> str:
            self.plan_confirmations.append(plan_text)
            return "allow"

        async def prompt_permission_choice(
            self, tool_name: str, *, allow_updates: bool
        ) -> str:
            return "allow"

        async def prompt_for_permission_feedback(self, tool_name: str) -> str:
            return ""

        async def log_text(self, _text: str, *, style: str | None = None) -> None:
            return

        async def render_assistant_text(self, _text: str) -> None:
            return

        async def render_tool_use(self, *_: Any, **__: Any) -> None:
            return

        async def render_session_result(self, *_: Any, **__: Any) -> None:
            return

        async def render_changed_files(self, *_: Any, **__: Any) -> None:
            return

        async def render_plan_preview(self, *_: Any, **__: Any) -> None:
            return

        async def close(self) -> None:
            self.closed = True

    fake_tui = FakeTUI()

    async def fake_execute(
        prompt_text: str,
        options: Any,
        session_name: str,
        *,
        permission_mode: str,
        allowed_tools: Sequence[str],
        tui: Any,
    ) -> int:
        captured["prompt"] = prompt_text
        captured["tui"] = tui
        captured["options"] = options
        return 0

    with (
        patch("planar.cli_agent.AgentTUI", return_value=fake_tui),
        patch("planar.cli_agent._execute_agent", new=fake_execute),
        patch("planar.cli_agent.sys.stdin", _TTY()),
    ):
        cli_agent.agent_command(None, None, None, None, None)

    assert captured["prompt"] == "build me a workflow"
    assert captured["tui"] is fake_tui
    assert fake_tui.banner_calls == 1
    assert fake_tui.banner_instructions == [
        "Describe what you want the Planar agent to build"
    ]
    assert fake_tui.prompt_messages == [
        "Describe what you want the Planar agent to build"
    ]
    options = captured["options"]
    assert hasattr(options, "can_use_tool")
    assert options.can_use_tool is not None


class _PlanCallbackTUI:
    def __init__(self) -> None:
        self.exit_plan_decision: str = "allow"
        self.tool_decision: str = "allow"
        self.feedback_message = ""
        self.confirm_calls: list[str] = []
        self.permission_requests: list[tuple[str, object, list[Any]]] = []
        self.feedback_calls = 0
        self.logged: list[tuple[str, str | None]] = []
        self.permission_choice_calls: list[str] = []
        self.permission_choice_allow_updates: list[bool] = []
        self.closed = False

    async def show_banner(self, instruction: str | None = None) -> None:
        return

    async def render_user_prompt(
        self, _prompt_text: str, *, follow_up: bool = False
    ) -> None:
        return

    async def prompt_for_initial(self, _instruction: str) -> str:
        return ""

    async def prompt_for_follow_up(self) -> str:
        return ""

    async def show_status(self, *_: Any, **__: Any) -> None:
        return

    async def clear_status(self) -> None:
        return

    async def render_assistant_text(self, *_: Any, **__: Any) -> None:
        return

    async def render_tool_use(self, *_: Any, **__: Any) -> None:
        return

    async def render_permission_request(
        self,
        tool_name: str,
        payload: object,
        suggestions: Sequence[Any],
    ) -> None:
        self.permission_requests.append((tool_name, payload, list(suggestions)))

    async def render_session_result(self, *_: Any, **__: Any) -> None:
        return

    async def render_changed_files(self, *_: Any, **__: Any) -> None:
        return

    async def render_plan_preview(self, *_: Any, **__: Any) -> None:
        return

    async def log_text(self, text: str, *, style: str | None = None) -> None:
        self.logged.append((text, style))

    async def confirm_exit_plan(self, plan_text: str) -> str:
        self.confirm_calls.append(plan_text)
        return self.exit_plan_decision

    async def prompt_permission_choice(
        self, tool_name: str, *, allow_updates: bool
    ) -> str:
        self.permission_choice_calls.append(tool_name)
        self.permission_choice_allow_updates.append(allow_updates)
        return self.tool_decision

    async def prompt_for_permission_feedback(self, tool_name: str) -> str:
        self.feedback_calls += 1
        return self.feedback_message

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_exit_plan_permission_allow_flow() -> None:
    captured: dict[str, Any] = {}
    fake_tui = _PlanCallbackTUI()
    fake_tui.exit_plan_decision = "allow"

    def fake_options(**kwargs: Any) -> SimpleNamespace:
        captured["options_kwargs"] = kwargs
        return SimpleNamespace(**kwargs)

    async def fake_execute(
        prompt_text: str,
        options: Any,
        session_name: str,
        *,
        permission_mode: str,
        allowed_tools: Sequence[str],
        tui: Any,
    ) -> int:
        captured["options_obj"] = options
        captured["tui"] = tui
        return 0

    with (
        patch("planar.cli_agent.AgentTUI", return_value=fake_tui),
        patch("planar.cli_agent.ClaudeAgentOptions", side_effect=fake_options),
        patch("planar.cli_agent._execute_agent", new=fake_execute),
    ):
        await cli_agent._agent_command_async(
            prompt="implement feature",
            file=None,
            allow_tool=(),
            deny_tool=(),
            add_dir=(),
        )

    callback = captured["options_kwargs"]["can_use_tool"]
    assert callback is not None

    context = ToolPermissionContext(
        suggestions=[
            PermissionUpdate(type="setMode", mode="acceptEdits", destination="session")
        ]
    )

    result = await callback("ExitPlanMode", {"plan": "Step 1"}, context)
    assert isinstance(result, PermissionResultAllow)
    assert result.updated_permissions is None
    assert fake_tui.permission_requests
    req_tool, req_payload, req_suggestions = fake_tui.permission_requests[0]
    assert req_tool == "ExitPlanMode"
    assert req_payload == {"plan": "Step 1"}
    assert req_suggestions and req_suggestions[0]["type"] == "setMode"
    assert fake_tui.feedback_calls == 0
    assert fake_tui.confirm_calls == ["Step 1"]
    assert fake_tui.permission_choice_calls == []
    assert fake_tui.permission_choice_allow_updates == []
    assert fake_tui.closed


@pytest.mark.asyncio
async def test_exit_plan_feedback_included_on_deny() -> None:
    captured: dict[str, Any] = {}
    fake_tui = _PlanCallbackTUI()
    fake_tui.exit_plan_decision = "deny"
    fake_tui.feedback_message = "Need more detail before implementation"

    def fake_options(**kwargs: Any) -> SimpleNamespace:
        captured["options_kwargs"] = kwargs
        return SimpleNamespace(**kwargs)

    async def fake_execute(
        prompt_text: str,
        options: Any,
        session_name: str,
        *,
        permission_mode: str,
        allowed_tools: Sequence[str],
        tui: Any,
    ) -> int:
        captured["options_obj"] = options
        captured["tui"] = tui
        return 0

    with (
        patch("planar.cli_agent.AgentTUI", return_value=fake_tui),
        patch("planar.cli_agent.ClaudeAgentOptions", side_effect=fake_options),
        patch("planar.cli_agent._execute_agent", new=fake_execute),
    ):
        await cli_agent._agent_command_async(
            prompt="implement feature",
            file=None,
            allow_tool=(),
            deny_tool=(),
            add_dir=(),
        )

    callback = captured["options_kwargs"]["can_use_tool"]
    assert callback is not None

    context = ToolPermissionContext(suggestions=[])
    result = await callback("ExitPlanMode", {"plan": "Plan overview"}, context)
    assert isinstance(result, PermissionResultDeny)
    assert result.message == fake_tui.feedback_message
    assert fake_tui.permission_requests
    deny_tool, deny_payload, deny_suggestions = fake_tui.permission_requests[0]
    assert deny_tool == "ExitPlanMode"
    assert deny_payload == {"plan": "Plan overview"}
    assert deny_suggestions == []
    assert fake_tui.feedback_calls == 1
    assert fake_tui.confirm_calls == ["Plan overview"]
    assert fake_tui.permission_choice_calls == []
    assert fake_tui.permission_choice_allow_updates == []
    assert fake_tui.closed


@pytest.mark.asyncio
async def test_general_tool_permission_updates_applied_on_approval() -> None:
    captured: dict[str, Any] = {}
    fake_tui = _PlanCallbackTUI()
    fake_tui.tool_decision = "allow_with_updates"

    def fake_options(**kwargs: Any) -> SimpleNamespace:
        captured["options_kwargs"] = kwargs
        return SimpleNamespace(**kwargs)

    async def fake_execute(
        prompt_text: str,
        options: Any,
        session_name: str,
        *,
        permission_mode: str,
        allowed_tools: Sequence[str],
        tui: Any,
    ) -> int:
        captured["options_obj"] = options
        captured["tui"] = tui
        return 0

    with (
        patch("planar.cli_agent.AgentTUI", return_value=fake_tui),
        patch("planar.cli_agent.ClaudeAgentOptions", side_effect=fake_options),
        patch("planar.cli_agent._execute_agent", new=fake_execute),
    ):
        await cli_agent._agent_command_async(
            prompt="implement feature",
            file=None,
            allow_tool=(),
            deny_tool=(),
            add_dir=(),
        )

    callback = captured["options_kwargs"]["can_use_tool"]
    assert callback is not None

    context = ToolPermissionContext(
        suggestions=[
            PermissionUpdate(
                type="addDirectories",
                directories=["/tmp"],
                destination="session",
            )
        ]
    )

    result = await callback("Write", {"file_path": "foo.txt"}, context)
    assert isinstance(result, PermissionResultAllow)
    assert result.updated_permissions is not None
    assert result.updated_permissions[0].type == "addDirectories"
    assert fake_tui.permission_requests
    request_tool, request_payload, request_suggestions = fake_tui.permission_requests[0]
    assert request_tool == "Write"
    assert request_payload == {"file_path": "foo.txt"}
    assert request_suggestions and request_suggestions[0]["type"] == "addDirectories"
    assert fake_tui.feedback_calls == 0
    assert fake_tui.permission_choice_calls == ["Write"]
    assert fake_tui.permission_choice_allow_updates == [True]
    assert fake_tui.closed
