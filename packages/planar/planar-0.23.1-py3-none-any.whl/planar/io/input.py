"""Input helpers for the Planar IO facade."""

from collections.abc import Sequence
from datetime import date
from typing import Any

from ._base import _ensure_context
from ._field_specs import (
    _boolean_field_spec,
    _date_field_spec,
    _execute_single_field,
    _table_field_spec,
    _text_field_spec,
)


class IOInput:
    async def text(
        self,
        label: str,
        *,
        default: str | None = None,
        help_text: str | None = None,
        placeholder: str | None = None,
        multiline: bool = False,
    ) -> str:
        _ensure_context()
        spec = _text_field_spec(
            label=label,
            default=default,
            help_text=help_text,
            placeholder=placeholder,
            multiline=multiline,
        )
        return await _execute_single_field(
            spec,
            kind="input.text",
            model_suffix="Text",
            label=label,
            help_text=help_text,
        )

    async def boolean(
        self,
        label: str,
        *,
        default: bool = False,
        help_text: str | None = None,
    ) -> bool:
        _ensure_context()
        spec = _boolean_field_spec(
            label=label,
            default=default,
            help_text=help_text,
        )
        return await _execute_single_field(
            spec,
            kind="input.boolean",
            model_suffix="Boolean",
            label=label,
            help_text=help_text,
        )

    async def date(
        self,
        label: str,
        *,
        default: date | None = None,
        help_text: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> date:
        _ensure_context()
        spec = _date_field_spec(
            label=label,
            default=default,
            help_text=help_text,
            min_date=min_date,
            max_date=max_date,
        )
        return await _execute_single_field(
            spec,
            kind="input.date",
            model_suffix="Date",
            label=label,
            help_text=help_text,
        )

    async def table(
        self,
        label: str,
        *,
        data: Sequence[dict[str, Any]],
        columns: list[str] | None = None,
        delete_enabled: bool = False,
        search_enabled: bool = True,
        help_text: str | None = None,
    ) -> list[dict[str, Any]]:
        """Edit a table of data.

        Creates a human task that allows users to edit tabular data. The user can
        modify cell values and optionally delete rows.

        Args:
            label: Display label for the table.
            data: Initial data as a sequence of dicts.
                Each item represents a row.
            columns: Columns to display (visibility only). If None, all columns from
                the data are shown. The return value always includes all columns,
                not just visible ones.
            delete_enabled: Allow users to delete rows. Defaults to False.
            search_enabled: Enable search/filter functionality. Defaults to True.
            help_text: Help text displayed below the table.

        Returns:
            The edited data as a list of dicts, including all original columns/fields.

        Raises:
            ValueError: If label is empty, data is empty, data exceeds 50 rows,
                columns reference non-existent fields, or columns contain duplicates.
        """
        _ensure_context()
        spec = _table_field_spec(
            label=label,
            data=data,
            columns=columns,
            delete_enabled=delete_enabled,
            search_enabled=search_enabled,
            help_text=help_text,
        )
        return await _execute_single_field(
            spec,
            kind="input.table",
            model_suffix="Table",
            label=label,
            help_text=help_text,
        )


__all__ = ["IOInput"]
