import asyncio
import hashlib
import inspect
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable, get_type_hints

from croniter import croniter
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col

from planar.cron_expression_normalizer import normalize_cron
from planar.db.db import PlanarSession
from planar.logging import get_logger
from planar.session import get_session, session_context
from planar.utils import utc_now
from planar.workflows import orchestrator
from planar.workflows.models import Workflow, WorkflowStatus
from planar.workflows.serialization import serialize_args
from planar.workflows.wrappers import CronSchedule, WorkflowWrapper

logger = get_logger(__name__)


def validate_cron_args_kwargs(
    workflow_wrapper: WorkflowWrapper,
    args: tuple,
    kwargs: dict,
) -> None:
    """
    Validate that the provided args and kwargs match the workflow function signature.

    This validates:
    1. The correct number of arguments
    2. No unknown keyword arguments
    3. Type compatibility when types can be determined

    Args:
        workflow_wrapper: The workflow wrapper containing the function
        args: Positional arguments to validate
        kwargs: Keyword arguments to validate

    Raises:
        TypeError: If the args/kwargs don't match the function signature
        ValueError: If type validation fails
    """
    # Get the original function from the wrapper
    func = workflow_wrapper.original_fn
    sig = inspect.signature(func)

    # Try to bind the arguments to check if they match the signature
    try:
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
    except TypeError as e:
        raise TypeError(
            f"Invalid arguments for @cron decorator on {workflow_wrapper.function_name}: {e}"
        ) from e

    # Get type hints for additional validation
    type_hints = get_type_hints(func)

    # Check positional arguments against type hints
    param_names = list(sig.parameters.keys())
    for i, arg_value in enumerate(args):
        if i < len(param_names):
            param_name = param_names[i]
            param_hint = type_hints.get(param_name)

            # Skip validation if no type hint or if the value is None
            if param_hint is None or arg_value is None:
                continue

            # For basic type checking, we can validate primitive types
            # Note: Full type validation would require more sophisticated checking
            # This provides basic validation for common cases
            if param_hint in (int, float, str, bool):
                if not isinstance(arg_value, param_hint):
                    raise ValueError(
                        f"Argument '{param_name}' expects type {param_hint.__name__}, "
                        f"got {type(arg_value).__name__} in @cron decorator for {workflow_wrapper.function_name}"
                    )

    # Check keyword arguments against type hints
    for key, val in kwargs.items():
        param_hint = type_hints.get(key)

        # Skip validation if no type hint or if the value is None
        if param_hint is None or val is None:
            continue

        # Basic type checking for primitive types
        if param_hint in (int, float, str, bool):
            if not isinstance(val, param_hint):
                raise ValueError(
                    f"Keyword argument '{key}' expects type {param_hint.__name__}, "
                    f"got {type(val).__name__} in @cron decorator for {workflow_wrapper.function_name}"
                )


def _compute_idempotency_key_suffix(
    function_name: str, cron_expr: str, args: tuple, kwargs: dict
) -> str:
    """
    Compute a deterministic key for a cron schedule.

    This key is used to identify and deduplicate scheduled workflow runs.
    """
    serialized_args, serialized_kwargs = serialize_args(lambda: None, args, kwargs)
    key_data = f"{function_name}:{serialized_args}:{serialized_kwargs}"
    return f"{cron_expr}:{hashlib.sha256(key_data.encode()).hexdigest()}"


def cron[**P, T, U, R](
    cron_expr: str,
    window: timedelta | None = None,
    start_time: datetime | None = None,
    args: tuple = (),
    kwargs: dict = {},
):
    """
    Decorator to schedule a workflow to run on a cron schedule.

    This decorator can only be applied to WorkflowWrapper instances (functions
    decorated with @workflow()). It can be stacked multiple times to create
    multiple schedules for the same workflow.

    Args:
        cron_expr: A cron expression string (e.g., '*/5 * * * *' for every 5 minutes)
        window: Maximum time interval from current date to look back for missed runs.
            - If None and start_time is specified, window is set to now - start_time
            - If None and start_time is not specified, defaults to 50 seconds
            - If specified and start_time is specified, window is min(window, now - start_time)
        start_time: Optional start date for when the workflow should start scheduling.
            Affects the computation of the window.
        args: Positional arguments to pass to the workflow function
        kwargs: Keyword arguments to pass to the workflow function

    Example:
        @cron('*/5 * * * *', args=(10,))  # run every 5 minutes with arg=10
        @cron('0 15 * * *', args=(100,), window=timedelta(days=7))  # daily at 15:00, catch up to 7 days
        @cron('0 0 * * *', window=timedelta(hours=1))  # midnight, catch up to 1 hour
        @cron('0 0 * * *', start_time=datetime(2025, 1, 1))  # start scheduling from Jan 1, 2025
        @workflow()
        async def my_workflow(input: int):
            ...
    """

    def decorator(
        workflow_wrapper: WorkflowWrapper[P, T, U, R],
    ) -> WorkflowWrapper[P, T, U, R]:
        if not isinstance(workflow_wrapper, WorkflowWrapper):
            raise TypeError(
                "@cron() decorator can only be applied to @workflow() decorated functions"
            )

        # Validate that args and kwargs match the workflow function signature
        validate_cron_args_kwargs(workflow_wrapper, args, kwargs)

        # Convert timezone-aware start_time to timezone-naive UTC
        normalized_start_time = start_time
        if (
            normalized_start_time is not None
            and normalized_start_time.tzinfo is not None
        ):
            # Convert to UTC and strip timezone info for database storage
            normalized_start_time = normalized_start_time.astimezone(UTC).replace(
                tzinfo=None
            )

        # Validate cron expression
        normalized_cron_expr = normalize_cron(cron_expr)
        logger.debug(
            "normalized cron expression",
            original=cron_expr,
            normalized=normalized_cron_expr,
        )

        # Compute the cron key for this schedule
        idempotency_key_suffix = _compute_idempotency_key_suffix(
            workflow_wrapper.function_name, normalized_cron_expr, args, kwargs
        )

        # Add this schedule to the wrapper
        schedule = CronSchedule(
            cron_expr=normalized_cron_expr,
            args=list(args),
            kwargs=kwargs,
            idempotency_key_suffix=idempotency_key_suffix,
            window=window,
            start_time=normalized_start_time,
        )
        workflow_wrapper.cron_schedules.append(schedule)

        logger.debug(
            "registered cron schedule",
            function_name=workflow_wrapper.function_name,
            cron_expr=normalized_cron_expr,
            idempotency_key_suffix=idempotency_key_suffix,
        )

        return workflow_wrapper

    return decorator


def get_prev_run_time(cron_expr: str, base_time: datetime) -> datetime | None:
    cron = croniter(cron_expr, start_time=base_time)
    return cron.get_prev(datetime)


async def sync_schedules_step(
    engine: AsyncEngine,
    workflow_wrappers: list[WorkflowWrapper],
    orchestrator: orchestrator.WorkflowOrchestrator,
    *,
    now: datetime | None = None,
) -> int:
    """
    Execute a single scheduling synchronization pass.

    Args:
        engine: Database engine used for the session context.
        workflow_wrappers: Registered workflow wrappers to inspect for schedules.
        orchestrator: Workflow orchestrator to notify when new work is available.
        now: Optional timestamp to use for scheduling decisions. Defaults to utc_now().

    Returns:
        The number of scheduled workflow runs inserted during this pass.
    """
    async with session_context(engine):
        session = get_session()
        current_time = now or utc_now()
        count = await sync_scheduled_workflows(session, workflow_wrappers, current_time)
        if count > 0:
            assert session.in_transaction()
            await session.commit()
            orchestrator.poll_soon()
        return count


async def sync_schedules_forever(
    engine: AsyncEngine,
    workflow_wrappers: list[WorkflowWrapper],
    orchestrator: orchestrator.WorkflowOrchestrator,
    *,
    interval_seconds: float = 30.0,
    sleep_fn: Callable[[float], Awaitable[None]] = asyncio.sleep,
    should_continue: Callable[[], bool] | None = None,
    now_fn: Callable[[], datetime] = utc_now,
):
    """Run the scheduling sync loop every 30 seconds."""
    continue_check = should_continue or (lambda: True)
    while continue_check():
        try:
            await sync_schedules_step(
                engine,
                workflow_wrappers,
                orchestrator,
                now=now_fn(),
            )
        except Exception:
            logger.exception("error during scheduling sync")
            # Continue the loop even if an error occurs
        await sleep_fn(interval_seconds)


async def sync_scheduled_workflows(
    session: PlanarSession,
    workflow_wrappers: list[WorkflowWrapper],
    now: datetime,
) -> int:
    """
    Synchronize scheduled workflow runs with the database.

    This function schedules workflows that have missed their run times within
    the configured window period. It creates workflow entries for all missed
    runs to allow catch-up processing.

    Args:
        session: Database session
        workflow_wrappers: List of registered workflow wrappers to check for schedules
        now: Current time

    Returns:
        The number of scheduled workflow runs inserted.
    """
    logger.debug("syncing scheduled workflows")
    # normalize now to timezone-naive UTC
    if now.tzinfo is not None:
        now = now.astimezone(UTC).replace(tzinfo=None)

    all_schedules: list[tuple[WorkflowWrapper, CronSchedule]] = []

    for workflow_wrapper in workflow_wrappers:
        schedules = workflow_wrapper.cron_schedules
        if not schedules:
            continue

        for schedule in schedules:
            all_schedules.append((workflow_wrapper, schedule))

    inserted_count = 0
    # Get last run times for all schedules in a single query
    scheduled_runs: list[Workflow] = []

    for workflow_wrapper, schedule in all_schedules:
        start_time = schedule.start_time
        computed_window = schedule.window
        if start_time is not None:
            time_since_start = now - start_time
            if computed_window is None:
                # If window is None and start_time is specified, window is now - start_time
                computed_window = time_since_start
            else:
                # If window is not None and start_time is specified, window is min(window, now - start_time)
                computed_window = min(computed_window, time_since_start)
        elif computed_window is None:
            # If window is None and start_time is not specified, default to 50 seconds
            computed_window = timedelta(seconds=50)

        # Ensure window is non-negative (handles case when start_time is in the future)
        computed_window = max(computed_window, timedelta(seconds=0))

        # Determine the earliest time we should consider for scheduling
        earliest_time = now - computed_window

        # Get the most recent run time that should have occurred before or at now
        most_recent_due = get_prev_run_time(schedule.cron_expr, now)

        # Check if we have any runs to schedule
        if not most_recent_due or most_recent_due < earliest_time:
            # No runs to schedule
            continue

        # Schedule all missed runs from earliest_time to most_recent_due
        # Work backwards from most_recent_due to earliest_time
        runs_to_schedule = []
        temp_time = most_recent_due

        while temp_time and temp_time >= earliest_time:
            # Skip if this is the last run we already executed
            runs_to_schedule.append(temp_time)
            temp_time = get_prev_run_time(schedule.cron_expr, temp_time)

        # Reverse to get chronological order
        runs_to_schedule.reverse()

        # Create workflow entries for all runs to schedule
        for run_time in runs_to_schedule:
            scheduled_runs.append(
                Workflow(
                    function_name=workflow_wrapper.function_name,
                    idempotency_key=f"{int(run_time.timestamp())}:{schedule.idempotency_key_suffix}",
                    scheduled_time=run_time,
                    args=schedule.args,
                    kwargs=schedule.kwargs,
                    status=WorkflowStatus.PENDING,
                )
            )

            logger.debug(
                "scheduling workflow run",
                function_name=workflow_wrapper.function_name,
                cron_expr=schedule.cron_expr,
                scheduled_time=run_time,
            )

    # Insert scheduled runs
    if scheduled_runs:
        stmt = session.insert_or_ignore(
            Workflow,
            scheduled_runs,
            conflict_columns=["idempotency_key"],
        ).returning(col(Workflow.id))
        result = (await session.exec(stmt)).all()
        inserted_count = len(result)
        logger.info("inserted scheduled workflow runs", count=inserted_count)
    else:
        logger.debug("no scheduled runs to insert")

    logger.debug("scheduled workflow sync completed")
    return inserted_count
