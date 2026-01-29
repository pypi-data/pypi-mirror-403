"""Form builder support for Planar IO."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Generic, Literal, cast, overload

from pydantic import BaseModel, ConfigDict, create_model

from planar.files import PlanarFile
from planar.modeling.orm.planar_base_entity import PlanarBaseEntity

from ._base import _execute_io_human, _model_name, _slugify
from ._field_specs import (
    FieldSpec,
    ValueT,
    _boolean_field_spec,
    _date_field_spec,
    _entity_field_spec,
    _field_key,
    _select_multiple_field_spec,
    _select_single_field_spec,
    _table_field_spec,
    _text_field_spec,
    _upload_field_spec,
)
from .xplanar_models import FormProps, FormXPlanar


class _FormModelBase(BaseModel):
    model_config = ConfigDict()


@dataclass
class FormFieldHandle(Generic[ValueT]):
    _builder: "FormBuilder"
    _key: str

    def value(self) -> ValueT:
        return self._builder.get_value(self._key)

    @property
    def data(self) -> ValueT:
        return self.value()


class FormBuilder:
    def __init__(
        self,
        *,
        name: str,
        title: str | None,
        description: str | None,
        submit_label: str,
    ) -> None:
        self._name = name
        self._title = title or name
        self._description = description
        self._submit_label = submit_label
        self._fields: list[FieldSpec[Any]] = []
        self._field_keys: set[str] = set()
        self._submitted = False
        self._data: dict[str, Any] | None = None
        self._model: BaseModel | None = None
        self.input = _FormInputNamespace(self)
        self.select = _FormSelectNamespace(self)
        self.entity = _FormEntityNamespace(self)
        self.upload = _FormUploadNamespace(self)

    async def __aenter__(self) -> "FormBuilder":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            return False
        if not self._fields:
            raise ValueError("form must contain at least one field")
        await self._submit()
        return False

    def _register_key(self, key: str | None, label: str) -> str:
        candidate = _field_key(key, label, fallback=f"field{len(self._fields) + 1}")
        if candidate in self._field_keys:
            raise ValueError(f"duplicate form field key '{candidate}'")
        return candidate

    def _add_field(self, spec: FieldSpec[ValueT]) -> FormFieldHandle[ValueT]:
        if spec.key in self._field_keys:
            raise ValueError(f"duplicate form field key '{spec.key}'")
        self._fields.append(cast(FieldSpec[Any], spec))
        self._field_keys.add(spec.key)
        return cast(FormFieldHandle[ValueT], FormFieldHandle(self, spec.key))

    async def _submit(self) -> None:
        fields = {spec.key: (spec.annotation, spec.field_info) for spec in self._fields}
        model_name = _model_name(f"Form_{self._name}")
        create = cast(Callable[..., Any], create_model)
        output_model = cast(
            type[BaseModel],
            create(
                model_name,
                __base__=_FormModelBase,
                __module__=__name__,
                **fields,
            ),
        )
        form_metadata = FormXPlanar(
            component="io.form",
            props=FormProps(submit_label=self._submit_label),
        )
        output_model.model_config = ConfigDict(
            json_schema_extra={"x-planar": form_metadata.model_dump(exclude_none=True)}
        )

        suggested_payload = {
            spec.key: spec.suggested
            for spec in self._fields
            if spec.suggested is not None
        }
        payload = await _execute_io_human(
            kind=f"form.{_slugify(self._name) or 'form'}",
            label=self._title,
            help_text=self._description,
            output_model=output_model,
            suggested_data=suggested_payload or None,
        )
        model = output_model.model_validate(payload)
        raw = model.model_dump(mode="json")
        data: dict[str, Any] = {}
        for spec in self._fields:
            data[spec.key] = spec.postprocess(raw[spec.key])
        self._data = data
        self._model = model
        self._submitted = True

    def get_value(self, key: str) -> Any:
        if not self._submitted or self._data is None:
            raise RuntimeError("form values are not available until the form completes")
        return self._data[key]

    @property
    def data(self) -> dict[str, Any]:
        if not self._submitted or self._data is None:
            raise RuntimeError("form values are not available until the form completes")
        return dict(self._data)

    @property
    def model(self) -> BaseModel:
        if not self._submitted or self._model is None:
            raise RuntimeError("form values are not available until the form completes")
        return self._model


class _FormInputNamespace:
    def __init__(self, builder: FormBuilder) -> None:
        self._builder = builder

    def text(
        self,
        label: str,
        *,
        key: str | None = None,
        default: str | None = None,
        help_text: str | None = None,
        placeholder: str | None = None,
        multiline: bool = False,
    ) -> FormFieldHandle[str]:
        actual_key = self._builder._register_key(key, label)
        spec = _text_field_spec(
            key=actual_key,
            label=label,
            default=default,
            help_text=help_text,
            placeholder=placeholder,
            multiline=multiline,
        )
        return self._builder._add_field(spec)

    def boolean(
        self,
        label: str,
        *,
        key: str | None = None,
        default: bool = False,
        help_text: str | None = None,
    ) -> FormFieldHandle[bool]:
        actual_key = self._builder._register_key(key, label)
        spec = _boolean_field_spec(
            key=actual_key,
            label=label,
            default=default,
            help_text=help_text,
        )
        return self._builder._add_field(spec)

    def date(
        self,
        label: str,
        *,
        key: str | None = None,
        default: date | None = None,
        help_text: str | None = None,
        min_date: date | None = None,
        max_date: date | None = None,
    ) -> FormFieldHandle[date]:
        actual_key = self._builder._register_key(key, label)
        spec = _date_field_spec(
            key=actual_key,
            label=label,
            default=default,
            help_text=help_text,
            min_date=min_date,
            max_date=max_date,
        )
        return self._builder._add_field(spec)

    def table(
        self,
        label: str,
        *,
        data: Sequence[dict[str, Any]],
        key: str | None = None,
        columns: list[str] | None = None,
        delete_enabled: bool = False,
        search_enabled: bool = True,
        help_text: str | None = None,
    ) -> FormFieldHandle[list[dict[str, Any]]]:
        """Add an editable table field to the form.

        Args:
            label: Display label for the table.
            data: Initial data as a sequence of dicts. Each dict represents a row.
            key: Unique form field key. Defaults to slugified label.
            columns: Columns to display (visibility only). If None, all columns
                from the data are shown. The return value always includes all
                columns, not just visible ones.
            delete_enabled: Allow users to delete rows. Defaults to False.
            search_enabled: Enable search/filter functionality. Defaults to True.
            help_text: Help text displayed below the table.

        Returns:
            FormFieldHandle for accessing the edited table data.

        Raises:
            ValueError: If label is empty, data is empty, data exceeds 50 rows,
                columns reference non-existent fields, or columns contain duplicates.
        """
        actual_key = self._builder._register_key(key, label)
        spec = _table_field_spec(
            key=actual_key,
            label=label,
            data=data,
            columns=columns,
            delete_enabled=delete_enabled,
            search_enabled=search_enabled,
            help_text=help_text,
        )
        return self._builder._add_field(spec)


class _FormSelectNamespace:
    def __init__(self, builder: FormBuilder) -> None:
        self._builder = builder

    def single(
        self,
        label: str,
        options: Sequence[str],
        *,
        key: str | None = None,
        default: str | None = None,
        help_text: str | None = None,
        search: bool = False,
    ) -> FormFieldHandle[str]:
        actual_key = self._builder._register_key(key, label)
        spec = _select_single_field_spec(
            key=actual_key,
            label=label,
            options=options,
            default=default,
            help_text=help_text,
            search=search,
        )
        return self._builder._add_field(spec)

    def multiple(
        self,
        label: str,
        options: Sequence[str],
        *,
        key: str | None = None,
        default: Sequence[str] | None = None,
        max_selections: int | None = None,
        help_text: str | None = None,
        search: bool = False,
    ) -> FormFieldHandle[list[str]]:
        actual_key = self._builder._register_key(key, label)
        spec = _select_multiple_field_spec(
            key=actual_key,
            label=label,
            options=options,
            default=default,
            max_selections=max_selections,
            help_text=help_text,
            search=search,
        )
        return self._builder._add_field(spec)


class _FormEntityNamespace:
    def __init__(self, builder: FormBuilder) -> None:
        self._builder = builder

    @overload
    def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        key: str | None = None,
        display_field: str | None = None,
        default: Any = None,
        multiple: Literal[False] = False,
        help_text: str | None = None,
    ) -> FormFieldHandle[str]: ...

    @overload
    def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        key: str | None = None,
        display_field: str | None = None,
        default: Any = None,
        multiple: Literal[True],
        help_text: str | None = None,
    ) -> FormFieldHandle[list[str]]: ...

    def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        key: str | None = None,
        display_field: str | None = None,
        default: Any = None,
        multiple: bool = False,
        help_text: str | None = None,
    ) -> FormFieldHandle[str] | FormFieldHandle[list[str]]:
        actual_key = self._builder._register_key(key, label)
        spec = _entity_field_spec(
            key=actual_key,
            label=label,
            entity=entity,
            display_field=display_field,
            default=default,
            multiple=multiple,
            help_text=help_text,
        )
        handle = self._builder._add_field(spec)
        if multiple:
            return cast(FormFieldHandle[list[str]], handle)
        return cast(FormFieldHandle[str], handle)


class _FormUploadNamespace:
    def __init__(self, builder: FormBuilder) -> None:
        self._builder = builder

    def file(
        self,
        label: str,
        *,
        key: str | None = None,
        accept: Sequence[str] | None = None,
        max_size_mb: int | None = None,
        help_text: str | None = None,
    ) -> FormFieldHandle[PlanarFile]:
        actual_key = self._builder._register_key(key, label)
        spec = _upload_field_spec(
            key=actual_key,
            label=label,
            accept=accept,
            max_size_mb=max_size_mb,
            help_text=help_text,
        )
        return self._builder._add_field(spec)


__all__ = ["FormBuilder", "FormFieldHandle"]
