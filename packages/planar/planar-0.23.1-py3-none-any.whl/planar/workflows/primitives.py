from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Coroutine

from pydantic.main import BaseModel

from planar.logging import get_logger
from planar.utils import P, T, U, utc_now
from planar.workflows import step
from planar.workflows.models import StepType
from planar.workflows.step_core import suspend_workflow

logger = get_logger(__name__)


@step()
async def get_deadline(max_wait_time: float) -> datetime:
    return utc_now() + timedelta(seconds=max_wait_time)


@step(step_type=StepType.MESSAGE)
async def message(message: str | BaseModel):
    pass


def wait(
    poll_interval: float = 60.0,
    max_wait_time: float = 3600.0,
):
    """
    Creates a durable step that repeatedly checks a condition until it returns True.

    This decorator wraps a function that returns a boolean. The function will be
    called repeatedly until it returns True or until max_wait_time is reached.

    Args:
        poll_interval: How often to check the condition
        max_wait_time: Maximum time to wait before failing

    Returns:
        A decorator that converts a boolean-returning function into a step
        that waits for the condition to be true
    """

    def decorator(
        func: Callable[P, Coroutine[T, U, bool]],
    ) -> Callable[P, Coroutine[T, U, None]]:
        @step()
        @wraps(func)
        async def wait_step(*args: P.args, **kwargs: P.kwargs) -> None:
            logger.debug(
                "wait step called",
                func_name=func.__name__,
                poll_interval=poll_interval,
                max_wait_time=max_wait_time,
            )
            # Set up deadline for timeout
            deadline = None
            if max_wait_time >= 0:
                deadline = await get_deadline(max_wait_time)
                logger.debug(
                    "calculated deadline for wait step",
                    func_name=func.__name__,
                    deadline=deadline,
                )

            # Check the condition
            result = await func(*args, **kwargs)
            logger.debug(
                "condition check returned", func_name=func.__name__, result=result
            )

            # If condition is met, return immediately
            if result:
                logger.info("condition met, proceeding", func_name=func.__name__)
                return

            # If deadline has passed, raise an exception
            if deadline is not None and utc_now() > deadline:
                logger.warning(
                    "timeout waiting for condition to be met",
                    func_name=func.__name__,
                    deadline=deadline,
                )
                raise ValueError("Timeout waiting for condition to be met")

            # Otherwise, suspend the workflow to retry later
            logger.info(
                "condition not met, suspending",
                func_name=func.__name__,
                poll_interval_seconds=poll_interval,
            )
            await suspend_workflow(interval=timedelta(seconds=poll_interval))

        return wait_step

    return decorator
