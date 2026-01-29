from datetime import timedelta
from typing import Any, Awaitable, Literal, TypeVar, overload
from uuid import UUID

from planar.session import get_session
from planar.workflows.context import get_context, in_context
from planar.workflows.execution import get_workflow_wrapper
from planar.workflows.models import Workflow, WorkflowStatus
from planar.workflows.orchestrator import WorkflowOrchestrator
from planar.workflows.step_core import _step, suspend_workflow
from planar.workflows.wrappers import BoundWorkflowCall, WorkflowCallMetadata


@_step()
async def start_workflows_step(
    metadata_list: list[WorkflowCallMetadata], bind_parent: bool = True
) -> list[UUID]:
    ctx = get_context()
    ctx.disable_child_workflow_commits = True
    ids: list[UUID] = []

    if bind_parent:
        ctx.bind_parent_workflow = True

    for metadata in metadata_list:
        wrapper = get_workflow_wrapper(metadata.function_name)
        workflow = await wrapper.start(*metadata.args, **metadata.kwargs)
        ids.append(workflow.id)

    # Considering the current workflow will suspend (thus lose the context) it
    # is not necessary to reset the flag here. Leaving it only for documenting
    # intent that this is a temporary setting.
    ctx.bind_parent_workflow = False
    ctx.disable_child_workflow_commits = False
    return ids


async def _start_impl(
    *wf_calls: BoundWorkflowCall[Any], bind_parent: bool = False
) -> tuple[UUID, ...]:
    if not in_context():
        raise RuntimeError(
            "run_workflows must be called within a workflow execution context"
        )

    metadata_list: list[WorkflowCallMetadata] = [
        wf_call.metadata for wf_call in wf_calls
    ]

    workflow_ids = await start_workflows_step(metadata_list, bind_parent=bind_parent)

    if not bind_parent:
        orchestrator = WorkflowOrchestrator.get()
        orchestrator.poll_soon()

    return tuple(workflow_ids)


async def _gather_impl(
    *wf_calls: BoundWorkflowCall[Any], return_exceptions: bool = False
) -> tuple[Any, ...]:
    workflow_ids = await _start_impl(*wf_calls, bind_parent=True)

    # Fetch the first child workflow to determine its status. If it is still pending,
    # then that means we just executed the start step and should suspend.

    # We could have used the `suspend` step too, but we do this way to avoid
    # spamming steps whenever a child workflow is started.
    session = get_session()
    async with session.begin_read():
        first_child = await session.get(Workflow, workflow_ids[0])
    assert first_child

    orchestrator = WorkflowOrchestrator.get()

    if first_child.status == WorkflowStatus.PENDING:
        orchestrator.poll_soon()
        # Suspend for 0 seconds. Since the poll query only selects workflows that
        # have no children, suspending for 0 seconds mean this workflow will wakeup
        # as soon as all children finish
        await suspend_workflow(interval=timedelta(seconds=0))

    return_values = []

    for wf_id in workflow_ids:
        try:
            result = await orchestrator.wait_for_completion(wf_id)
        except Exception as e:
            if return_exceptions:
                result = e
            else:
                raise
        return_values.append(result)

    return tuple(return_values)


type _WCall[_T] = BoundWorkflowCall[_T]
type _GatherAwaitable[_T] = Awaitable[_T]

_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")


# Overload the gather function to provide better type hints for up to 6 parameters.
@overload
def gather(
    coro_or_future1: _WCall[_T1], /, *, return_exceptions: Literal[False] = False
) -> _GatherAwaitable[tuple[_T1]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> _GatherAwaitable[tuple[_T1, _T2]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> _GatherAwaitable[tuple[_T1, _T2, _T3]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> _GatherAwaitable[tuple[_T1, _T2, _T3, _T4]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    coro_or_future5: _WCall[_T5],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> _GatherAwaitable[tuple[_T1, _T2, _T3, _T4, _T5]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    coro_or_future5: _WCall[_T5],
    coro_or_future6: _WCall[_T6],
    /,
    *,
    return_exceptions: Literal[False] = False,
) -> _GatherAwaitable[tuple[_T1, _T2, _T3, _T4, _T5, _T6]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1], /, *, return_exceptions: bool
) -> _GatherAwaitable[tuple[_T1 | Exception]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    /,
    *,
    return_exceptions: bool,
) -> _GatherAwaitable[tuple[_T1 | Exception, _T2 | Exception]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    /,
    *,
    return_exceptions: bool,
) -> _GatherAwaitable[tuple[_T1 | Exception, _T2 | Exception, _T3 | Exception]]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    /,
    *,
    return_exceptions: bool,
) -> _GatherAwaitable[
    tuple[_T1 | Exception, _T2 | Exception, _T3 | Exception, _T4 | Exception]
]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    coro_or_future5: _WCall[_T5],
    /,
    *,
    return_exceptions: bool,
) -> _GatherAwaitable[
    tuple[
        _T1 | Exception,
        _T2 | Exception,
        _T3 | Exception,
        _T4 | Exception,
        _T5 | Exception,
    ]
]: ...
@overload
def gather(
    coro_or_future1: _WCall[_T1],
    coro_or_future2: _WCall[_T2],
    coro_or_future3: _WCall[_T3],
    coro_or_future4: _WCall[_T4],
    coro_or_future5: _WCall[_T5],
    coro_or_future6: _WCall[_T6],
    /,
    *,
    return_exceptions: bool,
) -> _GatherAwaitable[
    tuple[
        _T1 | Exception,
        _T2 | Exception,
        _T3 | Exception,
        _T4 | Exception,
        _T5 | Exception,
        _T6 | Exception,
    ]
]: ...


def gather(
    *wf_calls: BoundWorkflowCall[Any], return_exceptions: bool = False
) -> _GatherAwaitable[tuple[Any, ...]]:
    return _gather_impl(*wf_calls, return_exceptions=return_exceptions)


def start(*wf_calls: BoundWorkflowCall[Any]):
    return _start_impl(*wf_calls, bind_parent=False)
