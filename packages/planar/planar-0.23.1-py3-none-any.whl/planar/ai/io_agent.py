"""IO-enabled agent that exposes workflow IO tools to language models."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar

from planar.ai.agent import Agent
from planar.io import IO

IO_AGENT_TOOL_PROMPT = """You can interact with the human operator via dedicated IO tools:
- use `display_markdown(message)` to show formatted content in the UI.
- use `display_table(label, data, columns=None, search_enabled=False, sorting_enabled=False)` to show tabular data. Pass data as a list of dicts.
- use `display_object(label, data, fields=None)` to show a single object's details. Pass data as a dict.
- use `request_text_input(label, help_text=None, placeholder=None)` to ask the operator for text.
- use `request_confirmation(short_title, prompt, confirm_label="Confirm", cancel_label="Cancel")` when you need a yes/no answer.
- use `request_table_input(label, data, columns=None, delete_enabled=False, search_enabled=True, help_text=None)` to let the operator edit tabular data. Returns the edited list of dicts.
Prefer showing context with markdown, tables, or object displays and ask concise, clear questions when requesting input."""


async def display_markdown(message: str) -> str:
    """Render markdown for the human operator."""
    await IO.display.markdown(message)
    return "Displayed markdown to the operator."


async def display_table(
    label: str,
    data: Sequence[dict[str, Any]],
    columns: Optional[list[str]] = None,
    search_enabled: bool = False,
    sorting_enabled: bool = False,
) -> str:
    """Display tabular data to the human operator.

    Args:
        label: Title for the table.
        data: List of row dicts mapping column names to values.
        columns: Optional column ordering/selection. If None, inferred from first row.
        search_enabled: Enable client-side filtering.
        sorting_enabled: Enable client-side sorting.
    """
    await IO.display.table(
        label,
        data=data,
        columns=columns,
        search_enabled=search_enabled,
        sorting_enabled=sorting_enabled,
    )
    return f"Displayed table '{label}' with {len(data)} rows to the operator."


async def display_object(
    label: str,
    data: dict[str, Any],
    fields: Optional[list[str]] = None,
) -> str:
    """Display a single object's details to the human operator.

    Args:
        label: Title for the object display.
        data: Dict mapping field names to values.
        fields: Optional field ordering/selection. If None, inferred from dict keys.
    """
    await IO.display.object(
        label,
        data=data,
        fields=fields,
    )
    return f"Displayed object '{label}' to the operator."


async def request_text_input(
    label: str,
    help_text: Optional[str] = None,
    placeholder: Optional[str] = None,
) -> str:
    """Prompt the operator for textual input."""
    return await IO.input.text(
        label,
        help_text=help_text,
        placeholder=placeholder,
    )


async def request_confirmation(
    short_title: str,
    prompt: str,
    confirm_label: str = "Confirm",
    cancel_label: str = "Cancel",
) -> bool:
    """Ask the operator to confirm or decline an action."""
    return await IO.input.boolean(
        short_title,
        help_text=f"{prompt}. Confirm with '{confirm_label}' or cancel with '{cancel_label}'.",
        default=False,
    )


async def request_table_input(
    label: str,
    data: Sequence[dict[str, Any]],
    columns: Optional[list[str]] = None,
    delete_enabled: bool = False,
    search_enabled: bool = True,
    help_text: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Present editable tabular data to the operator and return the edited result.

    Args:
        label: Title for the table.
        data: List of row dicts mapping column names to values.
        columns: Optional column ordering/selection. If None, inferred from first row.
            Columns not listed here are hidden but preserved in the returned data.
        delete_enabled: Allow the operator to delete rows.
        search_enabled: Enable client-side filtering.
        help_text: Optional description shown to the operator.
    """
    return await IO.input.table(
        label,
        data=list(data),
        columns=columns,
        delete_enabled=delete_enabled,
        search_enabled=search_enabled,
        help_text=help_text,
    )


_DEFAULT_IO_TOOLS: tuple[Callable[..., Any], ...] = (
    display_markdown,
    display_table,
    display_object,
    request_text_input,
    request_confirmation,
    request_table_input,
)


TInput = TypeVar("TInput", bound=Any)
TOutput = TypeVar("TOutput", bound=Any)
TDeps = TypeVar("TDeps", bound=Any)


@dataclass
class IOAgent(Agent[TInput, TOutput, TDeps]):
    """Agent variant that comes pre-wired with IO display/input tools."""

    def __post_init__(self) -> None:
        super().__post_init__()
        existing = {tool.__name__ for tool in self.tools}
        for tool in _DEFAULT_IO_TOOLS:
            if tool.__name__ not in existing:
                self.tools.append(tool)
        if IO_AGENT_TOOL_PROMPT not in self.system_prompt:
            if self.system_prompt:
                self.system_prompt = f"{IO_AGENT_TOOL_PROMPT}\n\n{self.system_prompt}"
            else:
                self.system_prompt = IO_AGENT_TOOL_PROMPT
