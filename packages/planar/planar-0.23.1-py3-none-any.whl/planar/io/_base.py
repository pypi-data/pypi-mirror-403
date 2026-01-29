"""Shared helpers and context utilities for the Planar IO package."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from planar.human import Human
from planar.logging import get_logger
from planar.workflows.context import get_context

logger = get_logger("planar.io")


def _ensure_context() -> None:
    try:
        get_context()
    except RuntimeError as exc:  # pragma: no cover - defensive guard
        raise RuntimeError(
            "IO helper must be used from within a running workflow"
        ) from exc


def _slugify(value: str) -> str:
    slug = []
    for char in value.lower():
        if char.isalnum():
            slug.append(char)
        elif char in {" ", "-", "_"}:
            slug.append("-")
    result = "".join(slug).strip("-")
    if not result:
        return "empty"
    return result[:48]


def _task_name(kind: str, label: str | None) -> str:
    label_slug = _slugify(label) if label else "field"
    return f"io::{kind}::{label_slug}"


def _model_name(kind: str) -> str:
    return f"IO{kind}Response_{uuid4().hex[:8]}"


def _build_prompt(label: str, help_text: str | None) -> str:
    prompt_lines = [label]
    if help_text:
        prompt_lines.append(help_text)
    return "\n\n".join(prompt_lines)


async def _execute_io_human(
    *,
    kind: str,
    label: str,
    help_text: str | None,
    output_model: type[BaseModel],
    suggested_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    human = Human(
        name=_task_name(kind, label),
        title=label,
        description=help_text,
        output_type=output_model,
    )
    suggestion_model = None
    if suggested_data:
        suggestion_model = output_model.model_construct(
            _fields_set=set(suggested_data.keys()),
            **suggested_data,
        )

    result = await human(
        message=_build_prompt(label, help_text),
        suggested_data=suggestion_model,
    )
    payload = result.output.model_dump(mode="json")
    logger.debug("io value received", task_id=result.task_id, kind=kind)
    return payload


__all__ = [
    "logger",
    "_build_prompt",
    "_ensure_context",
    "_execute_io_human",
    "_model_name",
    "_slugify",
    "_task_name",
]
