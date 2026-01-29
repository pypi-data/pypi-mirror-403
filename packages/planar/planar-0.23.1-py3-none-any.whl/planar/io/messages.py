"""Message helpers for Planar IO display APIs."""

from collections.abc import Sequence
from typing import Any, cast

from pydantic import BaseModel

from planar.modeling.orm import PlanarBaseEntity
from planar.workflows.primitives import message

from ._base import _ensure_context, logger


class IOMessage(BaseModel):
    planar_type: str


class MarkdownMessage(IOMessage):
    """Structured payload for IO markdown display."""

    planar_type: str = "io.display.markdown"
    markdown: str


class TableMessage(IOMessage):
    """Structured payload for IO table display."""

    planar_type: str = "io.display.table"
    label: str
    data: list[dict[str, Any]]
    columns: list[str]
    search_enabled: bool
    sorting_enabled: bool


class ObjectMessage(IOMessage):
    """Structured payload for IO object display."""

    planar_type: str = "io.display.object"
    label: str
    data: dict[str, Any]


class IODisplay:
    async def markdown(self, markdown_text: str) -> None:
        await message(MarkdownMessage(markdown=markdown_text))
        logger.debug("io markdown message emitted")

    async def table(
        self,
        label: str,
        *,
        data: Sequence[dict[str, Any]] | Sequence[PlanarBaseEntity],
        columns: list[str] | None = None,
        search_enabled: bool = False,
        sorting_enabled: bool = False,
    ) -> None:
        """Display tabular data.

        Args:
            label: Human-readable title for the table.
            data: List of row dictionaries. Must be a materialized list (not generator).
                Each dict maps column names to JSON-serializable values
                (str, int, float, bool, None).
            columns: Explicit column ordering and selection. If None, inferred from
                first row's keys. Extra keys in subsequent rows are ignored unless
                explicitly listed. Also determines which columns are rendered.
            search_enabled: Enable client-side filtering.
            sorting_enabled: Enable client-side sorting by clicking column headers.
        """
        _ensure_context()

        if len(data) > 1000:
            raise ValueError("io.display.table supports up to 1000 rows")

        if not label or not label.strip():
            raise ValueError("label must be non-empty")

        # special check for when data is a list of dicts
        if data and isinstance(data[0], dict):
            for row in data:
                dict_row = cast(dict[str, Any], row)
                for key in dict_row.keys():
                    if not isinstance(key, str):
                        raise ValueError(
                            f"column names must be strings, got {type(key).__name__}"
                        )

        resolved_columns: list[str]
        if columns is not None:
            if not columns:
                raise ValueError("columns must not be empty when explicitly provided")
            for col in columns:
                if not isinstance(col, str):
                    raise ValueError(
                        f"column names must be strings, got {type(col).__name__}"
                    )
            resolved_columns = list(columns)
        elif data:
            if isinstance(data[0], dict):
                resolved_columns = list(data[0].keys())
            else:
                resolved_columns = list(data[0].model_dump().keys())
        else:
            resolved_columns = []

        # precaution to remove any duplicated column names
        # while preserving dictionary key ordering
        resolved_columns = list(dict.fromkeys(resolved_columns))

        normalized_data = [
            {
                col: row.get(col) if isinstance(row, dict) else getattr(row, col, None)
                for col in resolved_columns
            }
            for row in data
        ]

        await message(
            TableMessage(
                label=label,
                data=normalized_data,
                columns=resolved_columns,
                search_enabled=search_enabled,
                sorting_enabled=sorting_enabled,
            )
        )
        logger.debug(
            "io table message emitted",
            row_count=len(data),
            column_count=len(resolved_columns),
        )

    async def object(
        self,
        label: str,
        *,
        data: dict[str, Any] | PlanarBaseEntity,
        fields: list[str] | None = None,
    ) -> None:
        """Display a single object.

        Args:
            label: Human-readable title for the object display.
            data: A dictionary or PlanarBaseEntity instance to display.
            fields: Explicit field ordering and selection. If None, inferred from
                the object's keys. Determines which fields are rendered.
        """
        _ensure_context()

        if not label or not label.strip():
            raise ValueError("label must be non-empty")

        is_dict = isinstance(data, dict)

        if is_dict:
            for key in data.keys():
                if not isinstance(key, str):
                    raise ValueError(
                        f"field names must be strings, got {type(key).__name__}"
                    )

        resolved_fields: list[str]
        if fields is not None:
            if not fields:
                raise ValueError("fields must not be empty when explicitly provided")
            for field in fields:
                if not isinstance(field, str):
                    raise ValueError(
                        f"field names must be strings, got {type(field).__name__}"
                    )
            resolved_fields = list(fields)
        elif is_dict:
            resolved_fields = list(data.keys())
        else:
            resolved_fields = list(data.model_dump().keys())

        resolved_fields = list(dict.fromkeys(resolved_fields))

        if is_dict:
            dict_data = cast(dict[str, Any], data)
            normalized_data = {field: dict_data.get(field) for field in resolved_fields}
        else:
            normalized_data = {
                field: getattr(data, field, None) for field in resolved_fields
            }

        await message(
            ObjectMessage(
                label=label,
                data=normalized_data,
            )
        )
        logger.debug(
            "io object message emitted",
            field_count=len(resolved_fields),
        )


__all__ = ["IOMessage", "MarkdownMessage", "TableMessage", "ObjectMessage", "IODisplay"]
