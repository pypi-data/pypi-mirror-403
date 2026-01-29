"""Entity selection helpers for Planar IO."""

from typing import Any, Literal, overload

from planar.modeling.orm.planar_base_entity import PlanarBaseEntity

from ._base import _ensure_context
from ._field_specs import _entity_field_spec, _execute_single_field


class IOEntity:
    @overload
    async def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        display_field: str | None = None,
        default: Any = None,
        multiple: Literal[False] = False,
        help_text: str | None = None,
    ) -> str: ...

    @overload
    async def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        display_field: str | None = None,
        default: Any = None,
        multiple: Literal[True],
        help_text: str | None = None,
    ) -> list[str]: ...

    async def select(
        self,
        label: str,
        *,
        entity: type[PlanarBaseEntity],
        display_field: str | None = None,
        default: Any = None,
        multiple: bool = False,
        help_text: str | None = None,
    ) -> str | list[str]:
        _ensure_context()
        spec = _entity_field_spec(
            label=label,
            entity=entity,
            display_field=display_field,
            default=default,
            multiple=multiple,
            help_text=help_text,
        )
        suffix = "EntitySelectMultiple" if multiple else "EntitySelect"
        return await _execute_single_field(
            spec,
            kind="entity.select",
            model_suffix=suffix,
            label=label,
            help_text=help_text,
        )


__all__ = ["IOEntity"]
