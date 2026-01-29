"""Internal metadata schemas and helpers for workflow steps."""

from contextvars import ContextVar
from typing import Annotated, Any, Dict, Literal, Type, cast, overload
from uuid import UUID

from pydantic import BaseModel, Discriminator, Tag, TypeAdapter


class HumanTaskMeta(BaseModel):
    """Metadata describing a human task associated with a step."""

    meta_type: Literal["human.task"] = "human.task"
    meta_version: Literal[1] = 1
    task_id: UUID


class AgentConfigMeta(BaseModel):
    """Metadata capturing which agent configuration was executed."""

    meta_type: Literal["agent.config"] = "agent.config"
    meta_version: Literal[1] = 1
    config_id: UUID
    config_version: int


class RuleConfigMeta(BaseModel):
    """Metadata capturing which rule configuration was executed."""

    meta_type: Literal["rule.config"] = "rule.config"
    meta_version: Literal[1] = 1
    config_id: UUID
    config_version: int


def _step_meta_discriminator(value: Any) -> str:
    """Return discriminator tag combining meta_type and meta_version."""
    if isinstance(value, dict):
        meta_type = value.get("meta_type")
        meta_version = value.get("meta_version")
    else:
        meta_type = getattr(value, "meta_type", None)
        meta_version = getattr(value, "meta_version", None)

    if meta_type is None or meta_version is None:
        raise ValueError(
            "Step metadata payload must include meta_type and meta_version"
        )

    return f"{meta_type}@{meta_version}"


StepMeta = Annotated[
    Annotated[HumanTaskMeta, Tag("human.task@1")]
    | Annotated[AgentConfigMeta, Tag("agent.config@1")]
    | Annotated[RuleConfigMeta, Tag("rule.config@1")],
    Discriminator(_step_meta_discriminator),
]

STEP_META_ADAPTER = TypeAdapter(StepMeta)


_STEP_META_VAR: ContextVar[StepMeta | None] = ContextVar(
    "planar_step_metadata", default=None
)


def set_step_metadata(meta: StepMeta | None) -> None:
    """Associate metadata with the currently executing workflow step."""
    _STEP_META_VAR.set(meta)


def get_step_metadata() -> StepMeta | None:
    """Fetch the metadata associated with the current workflow step, if any."""
    return _STEP_META_VAR.get()


def clear_step_metadata() -> None:
    """Clear metadata for the current workflow step."""
    _STEP_META_VAR.set(None)


@overload
def deserialize_step_metadata(
    payload: Dict[str, Any],
    meta_type: None = None,
) -> StepMeta: ...
@overload
def deserialize_step_metadata[T: StepMeta](
    payload: Dict[str, Any],
    meta_type: Type[T],
) -> T: ...


def deserialize_step_metadata[T: StepMeta](
    payload: Dict[str, Any], meta_type: Type[T] | None = None
) -> T | StepMeta:
    """Deserialize a stored metadata payload into a typed StepMeta instance."""
    meta = STEP_META_ADAPTER.validate_python(payload)
    if meta_type is not None:
        if not isinstance(meta, meta_type):
            raise ValueError(f"Unexpected step metadata type: {type(meta)}")
        return cast(T, meta)
    return meta
