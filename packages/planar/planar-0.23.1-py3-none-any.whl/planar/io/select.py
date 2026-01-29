"""Select helpers for Planar IO."""

from collections.abc import Sequence

from ._base import _ensure_context
from ._field_specs import (
    _execute_single_field,
    _select_multiple_field_spec,
    _select_single_field_spec,
)


class IOSelect:
    async def single(
        self,
        label: str,
        options: Sequence[str],
        *,
        default: str | None = None,
        help_text: str | None = None,
        search: bool = False,
    ) -> str:
        _ensure_context()
        spec = _select_single_field_spec(
            key="value",
            label=label,
            options=options,
            default=default,
            help_text=help_text,
            search=search,
        )
        return await _execute_single_field(
            spec,
            kind="select.single",
            model_suffix="SelectSingle",
            label=label,
            help_text=help_text,
        )

    async def multiple(
        self,
        label: str,
        options: Sequence[str],
        *,
        default: Sequence[str] | None = None,
        max_selections: int | None = None,
        help_text: str | None = None,
        search: bool = False,
    ) -> list[str]:
        _ensure_context()
        spec = _select_multiple_field_spec(
            label=label,
            options=options,
            default=default,
            max_selections=max_selections,
            help_text=help_text,
            search=search,
        )
        return await _execute_single_field(
            spec,
            kind="select.multiple",
            model_suffix="SelectMultiple",
            label=label,
            help_text=help_text,
        )


__all__ = ["IOSelect"]
