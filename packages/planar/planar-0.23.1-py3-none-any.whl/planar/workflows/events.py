"""
Event system for workflow engine.

This module provides functions for emitting and checking events that workflows
might be waiting for.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, cast
from uuid import UUID, uuid4

from sqlmodel import col, select, update

from planar.logging import get_logger
from planar.session import get_session
from planar.utils import utc_now
from planar.workflows.context import get_context
from planar.workflows.decorators import step
from planar.workflows.models import Workflow, WorkflowEvent
from planar.workflows.orchestrator import WorkflowOrchestrator
from planar.workflows.primitives import get_deadline
from planar.workflows.step_core import Suspend, suspend_workflow
from planar.workflows.tracing import trace

logger = get_logger(__name__)


async def emit_event(
    event_key: str,
    payload: Optional[Dict[str, Any]] = None,
    workflow_id: Optional[UUID] = None,
) -> tuple[WorkflowEvent, int]:
    """
    Emit a new event that workflows might be waiting for.

    Args:
        event_key: The event identifier
        payload: Optional data to include with the event
        workflow_id: Optional workflow ID if the event is targeted at a specific workflow

    Returns:
        The created event record
    """
    logger.debug(
        "emitting event",
        event_key=event_key,
        workflow_id=str(workflow_id),
        payload_keys=list(payload.keys()) if payload else None,
    )
    await trace("enter", event_key=event_key)
    session = get_session()

    select_condition = col(Workflow.waiting_for_event) == event_key
    if workflow_id:
        select_condition &= col(Workflow.id) == workflow_id
    update_query = (
        update(Workflow)
        .where(select_condition)
        .values(waiting_for_event=None, wakeup_at=None)
        .returning(col(Workflow.id))
    )

    async def transaction():
        # Update affected events
        workflow_ids = (await session.exec(cast(Any, update_query))).all()
        logger.info(
            "event woke up workflows", event_key=event_key, count=len(workflow_ids)
        )
        await trace(
            "wake-affected-workflows", event_key=event_key, count=len(workflow_ids)
        )
        # Create the event record
        event = WorkflowEvent(
            id=uuid4(),
            event_key=event_key,
            workflow_id=workflow_id,
            payload=payload or {},
        )
        session.add(event)
        logger.debug("event record created", event_key=event_key, event_id=event.id)
        await trace("add-event-record", event_key=event_key)

        return event, workflow_ids

    event, workflow_ids = await session.run_transaction(transaction)
    await trace("commit", event_key=event_key)
    logger.info("event committed to database", event_key=event_key, event_id=event.id)

    if workflow_ids and WorkflowOrchestrator.is_set():
        logger.debug("requesting orchestrator poll due to event", event_key=event_key)
        WorkflowOrchestrator.get().poll_soon()

    await trace("return", event_key=event_key)
    return event, len(workflow_ids)


async def check_event_exists(
    event_key: str, since: Optional[datetime] = None, workflow_id: Optional[UUID] = None
) -> bool:
    """
    Check if an event with the given key exists, optionally after a specific time.

    Args:
        event_key: The event identifier
        since: Only consider events after this time
        workflow_id: Optional workflow ID to check for workflow-specific events

    Returns:
        True if a matching event exists, False otherwise
    """
    logger.debug(
        "checking if event exists",
        event_key=event_key,
        since=since,
    )
    session = get_session()

    # Start building the query
    query = select(WorkflowEvent).where(WorkflowEvent.event_key == event_key)

    # If a timestamp is provided, only check for events after that time
    if since:
        query = query.where(WorkflowEvent.timestamp > since)

    # If a workflow ID is provided, check for events specific to that workflow
    # or global events (no workflow ID)
    if workflow_id:
        query = query.where(
            (col(WorkflowEvent.workflow_id) == workflow_id)
            | (col(WorkflowEvent.workflow_id).is_(None))
        )

    # Execute the query and check if any result exists
    event = (await session.exec(query)).first()
    exists = event is not None
    logger.debug("event exists check result", event_key=event_key, exists=exists)
    return exists


async def get_latest_event(
    event_key: str, since: Optional[datetime] = None, workflow_id: Optional[UUID] = None
) -> Optional[WorkflowEvent]:
    """
    Get the most recent event with the given key.

    Args:
        event_key: The event identifier
        since: Only consider events after this time
        workflow_id: Optional workflow ID to check for workflow-specific events

    Returns:
        The most recent matching event, or None if no match found
    """
    logger.debug(
        "getting latest event",
        event_key=event_key,
        since=since,
    )
    session = get_session()

    # Start building the query
    query = select(WorkflowEvent).where(WorkflowEvent.event_key == event_key)

    # If a timestamp is provided, only check for events after that time
    if since:
        query = query.where(WorkflowEvent.timestamp > since)

    # If a workflow ID is provided, check for events specific to that workflow
    # or global events (no workflow ID)
    if workflow_id:
        query = query.where(
            (col(WorkflowEvent.workflow_id) == workflow_id)
            | (col(WorkflowEvent.workflow_id).is_(None))
        )

    # Order by timestamp descending and get the first (most recent) result
    query = query.order_by(col(WorkflowEvent.timestamp).desc())

    # Execute the query and return the first result (or None)
    event = (await session.exec(query)).first()
    if event:
        logger.debug(
            "latest event found",
            event_key=event_key,
            event_id=event.id,
            timestamp=event.timestamp,
        )
    else:
        logger.debug("no event found with given criteria", event_key=event_key)
    return event


@step(display_name="Wait for event")
async def wait_for_event(
    event_key: str,
    max_wait_time: float = -1,
) -> Dict[str, Any]:
    """
    Creates a durable step that waits for a specific event to be emitted.

    Args:
        event_key: The event identifier to wait for
        max_wait_time: Maximum time to wait in seconds (-1 for indefinite)

    Returns:
        The event payload as a dictionary
    """
    logger.debug("waiting for event", event_key=event_key, max_wait_time=max_wait_time)
    await trace("enter", event_key=event_key)

    # Get workflow context
    ctx = get_context()
    workflow_id = ctx.workflow.id

    deadline = None
    if max_wait_time >= 0:
        deadline = await get_deadline(max_wait_time)
        logger.debug(
            "calculated deadline for event", event_key=event_key, deadline=deadline
        )
        await trace(
            "deadline",
            event_key=event_key,
            max_wait_time=max_wait_time,
            deadline=deadline,
        )

    async def transaction():
        # Check if the event already exists
        event_exists = await check_event_exists(event_key, workflow_id=workflow_id)
        logger.debug(
            "event exists check for workflow",
            event_key=event_key,
            exists=event_exists,
        )
        await trace("check-event-exists", event_key=event_key, exists=event_exists)

        if event_exists:
            # Event exists, get the event data and continue execution immediately
            event = await get_latest_event(event_key, workflow_id=workflow_id)
            logger.info(
                "event already exists, proceeding with payload",
                event_key=event_key,
                payload=event.payload if event else None,
            )
            await trace("existing-event", event_key=event_key)
            return event.payload if event and event.payload else {}

        # If deadline has passed, raise an exception
        now = utc_now()
        if deadline is not None and now > deadline:
            logger.warning(
                "timeout waiting for event",
                event_key=event_key,
                deadline=deadline,
                current_time=now,
            )
            await trace("deadline-timeout", event_key=event_key)
            raise ValueError(f"Timeout waiting for event ${event_key}")

        logger.info(
            "event not found, suspending workflow",
            event_key=event_key,
        )
        return suspend_workflow(
            interval=timedelta(seconds=max_wait_time) if max_wait_time > 0 else None,
            event_key=event_key,
        )

    session = get_session()
    result = await session.run_transaction(transaction)
    if isinstance(result, Suspend):
        # Suspend until event is emitted
        logger.debug(
            "workflow suspended, waiting for event",
            event_key=event_key,
        )
        await trace("suspend", event_key=event_key)
        await (
            result
        )  # This will re-raise the Suspend object's exception or re-enter the generator
        assert False, "Suspend should never return normally"  # Should not be reached
    logger.info(
        "event received or processed for workflow",
        event_key=event_key,
        result=result,
    )
    return result
