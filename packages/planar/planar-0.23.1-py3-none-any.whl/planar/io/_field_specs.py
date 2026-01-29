"""Field specification builders shared across IO helpers."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, Callable, Generic, TypeVar, cast

from pydantic import BaseModel, Field, create_model

from planar.files import PlanarFile
from planar.modeling.field_helpers import EntityField
from planar.modeling.orm.planar_base_entity import PlanarBaseEntity

from ._base import _execute_io_human, _model_name, _slugify
from .xplanar_models import (
    EntitySelectProps,
    EntitySelectXPlanar,
    InputBooleanProps,
    InputBooleanXPlanar,
    InputDateProps,
    InputDateXPlanar,
    InputTableProps,
    InputTableXPlanar,
    InputTextProps,
    InputTextXPlanar,
    SelectMultipleProps,
    SelectMultipleXPlanar,
    SelectOption,
    SelectSingleProps,
    SelectSingleXPlanar,
    UploadFileProps,
    UploadFileXPlanar,
)

MAX_TABLE_ROWS = 50

T_co = TypeVar("T_co", covariant=True)
ValueT = TypeVar("ValueT")
ResultT = TypeVar("ResultT")


@dataclass
class FieldSpec(Generic[T_co]):
    annotation: Any
    field_info: Any
    postprocess: Callable[[Any], T_co]
    suggested: Any | None = None
    key: str = "value"


def _xplanar_extra(model: BaseModel) -> dict[str, Any]:
    return {"x-planar": model.model_dump(exclude_none=True)}


def _field_key(
    suggested_key: str | None, label: str, *, fallback: str = "field"
) -> str:
    if suggested_key:
        return suggested_key
    slug = _slugify(label)
    return slug or fallback


def _normalize_options(options: Sequence[str]) -> list[str]:
    normalized = [str(option) for option in options]
    if not normalized:
        raise ValueError("options must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("options must be unique")
    return normalized


def _validate_single_default(default: str | None, options: Sequence[str]) -> str | None:
    if default is None:
        return None
    if default not in options:
        raise ValueError("default must be one of the provided options")
    return default


def _validate_multiple_default(
    default: Sequence[str] | None,
    options: Sequence[str],
    *,
    max_selections: int | None,
) -> list[str] | None:
    if default is None:
        return None
    normalized = [str(item) for item in default]
    invalid = [item for item in normalized if item not in options]
    if invalid:
        raise ValueError("default selections must be present in options")
    if len(set(normalized)) != len(normalized):
        raise ValueError("default selections must be unique")
    if max_selections is not None and len(normalized) > max_selections:
        raise ValueError("default selections exceed max_selections")
    return normalized


def _normalize_entity_default(
    default: Any,
    *,
    multiple: bool,
) -> str | list[str] | None:
    if default is None:
        return None

    def to_identifier(value: Any) -> str:
        if isinstance(value, PlanarBaseEntity):
            if value.id is None:
                raise ValueError("entity default must have an id")
            return str(value.id)
        return str(value)

    if multiple:
        if isinstance(default, (str, bytes)):
            raise ValueError(
                "multiple defaults must be provided as a sequence of identifiers"
            )
        normalized = [to_identifier(item) for item in default]
        if len(set(normalized)) != len(normalized):
            raise ValueError("default selections must be unique")
        return normalized

    return to_identifier(default)


def _text_field_spec(
    *,
    label: str,
    default: str | None,
    help_text: str | None,
    placeholder: str | None,
    multiline: bool,
    key: str = "value",
) -> FieldSpec[str]:
    props = InputTextProps(
        label=label,
        multiline=multiline,
        placeholder=placeholder,
        help_text=help_text,
        default=default,
    )
    metadata = InputTextXPlanar(component="io.input.text", props=props)

    field_info = Field(
        default=default if default is not None else ...,
        title=label,
        description=help_text,
        json_schema_extra=_xplanar_extra(metadata),
    )
    return FieldSpec(
        key=key,
        annotation=str,
        field_info=field_info,
        postprocess=str,
        suggested=default,
    )


def _boolean_field_spec(
    *,
    label: str,
    default: bool,
    help_text: str | None,
    key: str = "value",
) -> FieldSpec[bool]:
    props = InputBooleanProps(label=label, default=default, help_text=help_text)
    metadata = InputBooleanXPlanar(component="io.input.boolean", props=props)

    field_info = Field(
        default=default,
        title=label,
        description=help_text,
        json_schema_extra=_xplanar_extra(metadata),
    )
    return FieldSpec(
        key=key,
        annotation=bool,
        field_info=field_info,
        postprocess=bool,
        suggested=default,
    )


def _validate_date_constraints(
    default: date | None,
    min_date: date | None,
    max_date: date | None,
) -> None:
    """Validate date constraints are consistent."""
    if min_date is not None and max_date is not None and min_date > max_date:
        raise ValueError("min_date must not be after max_date")
    if default is not None:
        if min_date is not None and default < min_date:
            raise ValueError("default must not be before min_date")
        if max_date is not None and default > max_date:
            raise ValueError("default must not be after max_date")


def _date_field_spec(
    *,
    label: str,
    key: str = "value",
    default: date | None = None,
    help_text: str | None = None,
    min_date: date | None = None,
    max_date: date | None = None,
) -> FieldSpec[date]:
    _validate_date_constraints(default, min_date, max_date)

    props = InputDateProps(
        label=label,
        default=default,
        help_text=help_text,
        min_date=min_date,
        max_date=max_date,
    )
    metadata = InputDateXPlanar(component="io.input.date", props=props)

    # Build json_schema_extra with x-planar metadata and JSON Schema min/max
    extra = _xplanar_extra(metadata)
    if min_date is not None:
        extra["minimum"] = min_date.isoformat()
    if max_date is not None:
        extra["maximum"] = max_date.isoformat()

    field_info = Field(
        default=default if default is not None else ...,
        title=label,
        description=help_text,
        ge=min_date,
        le=max_date,
        json_schema_extra=extra,
    )

    return FieldSpec(
        key=key,
        suggested=default,
        annotation=date,
        field_info=field_info,
        postprocess=lambda raw: date.fromisoformat(raw),
    )


def _select_single_field_spec(
    *,
    label: str,
    options: Sequence[str],
    default: str | None,
    help_text: str | None,
    search: bool,
    key: str = "value",
) -> FieldSpec[str]:
    normalized_options = _normalize_options(options)
    selected_default = _validate_single_default(default, normalized_options)

    props = SelectSingleProps(
        label=label,
        options=[
            SelectOption(label=option, value=option) for option in normalized_options
        ],
        search=search,
        help_text=help_text,
        default=selected_default,
    )
    metadata = SelectSingleXPlanar(component="io.select.single", props=props)

    extra = _xplanar_extra(metadata)
    extra["enum"] = normalized_options

    field_info = Field(
        default=selected_default if selected_default is not None else ...,
        title=label,
        description=help_text,
        json_schema_extra=extra,
    )

    return FieldSpec(
        key=key,
        annotation=str,
        field_info=field_info,
        postprocess=str,
        suggested=selected_default,
    )


def _select_multiple_field_spec(
    *,
    label: str,
    options: Sequence[str],
    default: Sequence[str] | None,
    max_selections: int | None,
    help_text: str | None,
    search: bool,
    key: str = "value",
) -> FieldSpec[list[str]]:
    normalized_options = _normalize_options(options)
    if max_selections is not None and max_selections <= 0:
        raise ValueError("max_selections must be positive")
    selected_default = _validate_multiple_default(
        default,
        normalized_options,
        max_selections=max_selections,
    )

    props = SelectMultipleProps(
        label=label,
        options=[
            SelectOption(label=option, value=option) for option in normalized_options
        ],
        search=search,
        help_text=help_text,
        default=selected_default,
        max_selections=max_selections,
    )
    metadata = SelectMultipleXPlanar(component="io.select.multiple", props=props)

    extra = _xplanar_extra(metadata)
    extra["items"] = {"type": "string", "enum": normalized_options}

    field_info = Field(
        default=selected_default if selected_default is not None else ...,
        title=label,
        description=help_text,
        json_schema_extra=extra,
    )

    return FieldSpec(
        key=key,
        annotation=list[str],
        field_info=field_info,
        postprocess=lambda value: [str(choice) for choice in value],
        suggested=selected_default,
    )


def _entity_field_spec(
    *,
    label: str,
    entity: type[PlanarBaseEntity],
    display_field: str | None,
    default: Any,
    multiple: bool,
    help_text: str | None,
    key: str = "value",
) -> FieldSpec[str] | FieldSpec[list[str]]:
    normalized_default = _normalize_entity_default(default, multiple=multiple)
    props = EntitySelectProps(
        label=label,
        entity=entity.__name__,
        multiple=multiple,
        display_field=display_field,
        help_text=help_text,
        default=normalized_default,
    )
    metadata = EntitySelectXPlanar(component="io.entity.select", props=props)

    entity_field = EntityField(
        entity=entity,
        display_field=display_field,
        description=help_text,
    )
    extra = _xplanar_extra(metadata)

    if multiple:
        field_info = Field(
            default=normalized_default if normalized_default is not None else ...,
            title=label,
            description=help_text,
            json_schema_extra=extra,
        )
        annotation = Annotated[list[str], entity_field]
        return FieldSpec(
            key=key,
            annotation=annotation,
            field_info=field_info,
            postprocess=lambda value: [str(choice) for choice in value],
            suggested=normalized_default,
        )

    field_info = Field(
        default=normalized_default if normalized_default is not None else ...,
        title=label,
        description=help_text,
        json_schema_extra=extra,
    )
    annotation = Annotated[str, entity_field]
    return FieldSpec(
        key=key,
        annotation=annotation,
        field_info=field_info,
        postprocess=str,
        suggested=normalized_default,
    )


def _upload_field_spec(
    *,
    label: str,
    accept: Sequence[str] | None,
    max_size_mb: int | None,
    help_text: str | None,
    key: str = "value",
) -> FieldSpec[PlanarFile]:
    if max_size_mb is not None and max_size_mb <= 0:
        raise ValueError("max_size_mb must be positive")

    props = UploadFileProps(
        label=label,
        accept=[str(item) for item in accept] if accept is not None else None,
        max_size_mb=max_size_mb,
        help_text=help_text,
    )
    metadata = UploadFileXPlanar(component="io.upload.file", props=props)

    field_info = Field(
        default=...,
        title=label,
        description=help_text,
        json_schema_extra=_xplanar_extra(metadata),
    )

    return FieldSpec(
        key=key,
        annotation=PlanarFile,
        field_info=field_info,
        postprocess=lambda value: PlanarFile.model_validate(value),
    )


def _validate_table_params(
    label: str,
    data: Sequence[Any],
    columns: list[str] | None,
) -> None:
    """Validate common table parameters for both dict and entity data."""
    if not label or not label.strip():
        raise ValueError("label must be non-empty")
    if not data:
        raise ValueError("data must not be empty")
    if len(data) > MAX_TABLE_ROWS:
        raise ValueError(f"data exceeds maximum of {MAX_TABLE_ROWS} rows")
    if columns is not None and len(columns) != len(set(columns)):
        raise ValueError("columns must not contain duplicates")


def _infer_dict_columns(
    data: Sequence[dict[str, Any]],
    columns: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Determine all columns and visible columns from data and columns parameter."""
    # Get all unique columns from all rows, preserving order
    all_columns = list(dict.fromkeys(key for row in data for key in row.keys()))
    visible_columns = list(columns) if columns else all_columns

    if columns is not None:
        missing = set(visible_columns) - set(all_columns)
        if missing:
            raise ValueError(f"columns not found in data: {missing}")

    return (all_columns, visible_columns)


def _normalize_table_rows(
    data: Sequence[dict[str, Any]],
    all_columns: list[str],
) -> list[dict[str, Any]]:
    """Normalize rows to ensure all have the same columns.

    Missing keys in any row are filled with None values.
    """
    normalized: list[dict[str, Any]] = []
    for row in data:
        normalized_row = {col: row.get(col) for col in all_columns}
        normalized.append(normalized_row)
    return normalized


def _table_field_spec(
    *,
    label: str,
    data: Sequence[dict[str, Any]],
    columns: list[str] | None,
    delete_enabled: bool,
    search_enabled: bool,
    help_text: str | None,
    key: str = "value",
) -> FieldSpec[list[dict[str, Any]]]:
    _validate_table_params(label, data, columns)

    # Validate dict keys are strings
    for row in data:
        for k in row.keys():
            if not isinstance(k, str):
                raise ValueError("column names must be strings")

    all_columns, visible_columns = _infer_dict_columns(data, columns)

    props = InputTableProps(
        label=label,
        columns=visible_columns,
        delete_enabled=delete_enabled,
        search_enabled=search_enabled,
        help_text=help_text,
    )
    metadata = InputTableXPlanar(component="io.input.table", props=props)

    # Normalize data for suggested_data (ensure all rows have all columns)
    normalized_data = _normalize_table_rows(data, all_columns)

    # Build the complete json_schema_extra with array schema and x-planar
    # Populate properties schema with inferred columns (each allows any JSON value)
    properties_schema = {col: {} for col in all_columns}
    extra: dict[str, Any] = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": properties_schema,
            "additionalProperties": False,
        },
        "maxItems": MAX_TABLE_ROWS,
        "x-planar": metadata.model_dump(exclude_none=True),
    }

    field_info = Field(
        default=...,
        title=label,
        description=help_text,
        json_schema_extra=extra,
    )

    return FieldSpec(
        key=key,
        annotation=list[dict[str, Any]],
        field_info=field_info,
        postprocess=lambda rows: rows,
        suggested=normalized_data if normalized_data else None,
    )


async def _execute_single_field(
    spec: FieldSpec[ResultT],
    *,
    kind: str,
    model_suffix: str,
    label: str,
    help_text: str | None,
) -> ResultT:
    field_definitions: dict[str, tuple[Any, Any]] = {
        spec.key: (spec.annotation, spec.field_info)
    }
    create = cast(Callable[..., Any], create_model)
    output_model = cast(
        type[BaseModel],
        create(
            _model_name(model_suffix),
            __module__=__name__,
            **field_definitions,
        ),
    )
    suggested_payload = None
    if spec.suggested is not None:
        suggested_payload = {spec.key: spec.suggested}

    payload = await _execute_io_human(
        kind=kind,
        label=label,
        help_text=help_text,
        output_model=output_model,
        suggested_data=suggested_payload,
    )
    return spec.postprocess(payload[spec.key])


__all__ = [
    "FieldSpec",
    "MAX_TABLE_ROWS",
    "ResultT",
    "T_co",
    "ValueT",
    "_boolean_field_spec",
    "_date_field_spec",
    "_entity_field_spec",
    "_execute_single_field",
    "_field_key",
    "_select_multiple_field_spec",
    "_select_single_field_spec",
    "_text_field_spec",
    "_upload_field_spec",
]
