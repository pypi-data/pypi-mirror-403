from collections.abc import Coroutine as CoroutineABC
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Generic
from uuid import UUID

from pydantic import BaseModel

from planar.utils import P, R, T, U
from planar.workflows.models import Workflow


class WorkflowCallMetadata(BaseModel):
    function_name: str
    args: tuple
    kwargs: dict


class BoundWorkflowCall(CoroutineABC[Any, Any, R], Generic[R]):
    """Coroutine-compatible wrapper that keeps workflow call metadata."""

    def __init__(
        self,
        *,
        coroutine_factory: Callable[[], Coroutine[Any, Any, R]],
        metadata: WorkflowCallMetadata,
    ) -> None:
        self._coroutine_factory = coroutine_factory
        self._metadata = metadata
        self._coroutine: Coroutine[Any, Any, R] | None = None

    @property
    def metadata(self) -> WorkflowCallMetadata:
        return self._metadata

    def _ensure_coroutine(self) -> Coroutine[Any, Any, R]:
        if self._coroutine is None:
            self._coroutine = self._coroutine_factory()
        return self._coroutine

    def to_coroutine(self) -> Coroutine[Any, Any, R]:
        """Expose the underlying coroutine for interop scenarios."""

        return self._ensure_coroutine()

    def __await__(self):
        return self._ensure_coroutine().__await__()

    def send(self, value: Any) -> Any:
        return self._ensure_coroutine().send(value)

    def throw(self, typ, val=None, tb=None):  # type: ignore[override]
        coroutine = self._ensure_coroutine()

        if val is None and tb is None:
            return coroutine.throw(typ)
        if tb is None:
            return coroutine.throw(typ, val)
        return coroutine.throw(typ, val, tb)

    def close(self) -> None:
        # The coroutine is guaranteed to exist by the time ``close`` is called in normal
        # Task execution, but we guard here to behave sensibly if ``close`` is invoked
        # manually before the coroutine is awaited.
        if self._coroutine is not None:
            self._coroutine.close()


@dataclass(kw_only=True)
class Wrapper(Generic[P, T, U, R]):
    original_fn: Callable[P, Coroutine[T, U, R]]
    wrapped_fn: Callable[P, Coroutine[T, U, R]]
    __doc__: str | None

    def __post_init__(self):
        self.__doc__ = self.original_fn.__doc__

    @property
    def name(self):
        return self.wrapped_fn.__name__

    @property
    def __name__(self):
        return self.original_fn.__name__


@dataclass
class CronSchedule:
    """Represents a single cron schedule for a workflow."""

    cron_expr: str
    args: list
    kwargs: dict
    idempotency_key_suffix: str
    window: timedelta | None
    start_time: datetime | None = None


@dataclass(kw_only=True)
class WorkflowWrapper(Wrapper[P, T, U, R]):
    function_name: str
    start: Callable[P, Coroutine[T, U, Workflow]]
    start_step: Callable[P, Coroutine[T, U, UUID]]
    wait_for_completion: Callable[[UUID], Coroutine[T, U, R]]
    is_interactive: bool
    cron_schedules: list[CronSchedule] = field(default_factory=list)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> BoundWorkflowCall[R]:
        metadata = WorkflowCallMetadata(
            function_name=self.function_name, args=args, kwargs=kwargs
        )
        return BoundWorkflowCall(
            coroutine_factory=lambda: self.wrapped_fn(*args, **kwargs),
            metadata=metadata,
        )


@dataclass(kw_only=True)
class StepWrapper(Wrapper[P, T, U, R]):
    wrapper: Callable[P, Coroutine[T, U, R]]
    auto_workflow: WorkflowWrapper[P, T, U, R]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> BoundWorkflowCall[R]:
        metadata = WorkflowCallMetadata(
            function_name=self.auto_workflow.function_name,
            args=args,
            kwargs=kwargs,
        )
        return BoundWorkflowCall(
            coroutine_factory=lambda: self.wrapped_fn(*args, **kwargs),
            metadata=metadata,
        )
