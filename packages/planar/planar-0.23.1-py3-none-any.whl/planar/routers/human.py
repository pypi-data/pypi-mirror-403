"""
Human tasks API router for Planar workflows.

This module provides API routes for managing human task instances,
including task listing, completion, cancellation, and retrieval.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel

from planar.human import api
from planar.human.exceptions import TaskNotFound, TaskNotPending, UserNotFound
from planar.human.human import (
    HumanTask,
    HumanTaskStatus,
    cancel_human_task,
    complete_human_task,
    get_human_task,
    get_human_tasks,
)
from planar.human.models import TaskFilters
from planar.logging import get_logger
from planar.security.authorization import (
    HumanTaskAction,
    HumanTaskResource,
    validate_authorization_for,
)

logger = get_logger(__name__)


class CompleteTaskRequest(BaseModel):
    """Request model for completing a human task."""

    output_data: dict[str, Any]
    completed_by: str | None = None


class CancelTaskRequest(BaseModel):
    """Request model for cancelling a human task."""

    reason: str = "cancelled"
    cancelled_by: str | None = None


def filter_tasks_auth(tasks: list[HumanTask]) -> list[HumanTask]:
    authorized_tasks: list[HumanTask] = []
    for task in tasks:
        try:
            validate_authorization_for(
                HumanTaskResource.from_human_task(task),
                HumanTaskAction.TASK_VIEW,
            )
            authorized_tasks.append(task)
        except HTTPException as e:
            if e.status_code != 403:
                raise

    return authorized_tasks


def create_human_task_routes() -> APIRouter:
    router = APIRouter(tags=["Human Tasks"])

    """Register human task routes on the provided router and return it."""

    @router.get("/", response_model=list[HumanTask])
    async def list_human_tasks(
        status: HumanTaskStatus | None = None,
        workflow_id: UUID | None = None,
        name: str | None = None,
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        """
        List human tasks with optional filtering.

        Args:
            status: Filter by task status
            workflow_id: Filter by workflow ID
            name: Filter by task name
            limit: Maximum number of tasks to return
            offset: Pagination offset
        """
        try:
            return await get_human_tasks(
                status=status,
                workflow_id=workflow_id,
                name=name,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/assigned/user/{user_id}", response_model=list[HumanTask])
    async def tasks_assigned_to_user(user_id: UUID, filters: TaskFilters = Depends()):
        """List human tasks assigned to a user."""
        try:
            tasks = await api.query_tasks(assigned_to=user_id, filters=filters)
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/unassigned", response_model=list[HumanTask])
    async def unassigned_tasks(filters: TaskFilters = Depends()):
        """List tasks with no active assignment."""
        try:
            tasks = await api.query_tasks(are_unassigned=True, filters=filters)
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/orphaned-scope")
    async def orphaned_scope_tasks():
        try:
            tasks = await api.orphaned_scope_tasks()
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/orphaned-assignment")
    async def orphaned_assignment_tasks():
        try:
            tasks = await api.orphaned_assignment_tasks()
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/scoped/user/{user_id}", response_model=list[HumanTask])
    async def tasks_scoped_to_user(user_id: UUID, filters: TaskFilters = Depends()):
        """List human tasks scoped to a user, meaning that the user is in Scope.users or is in a group in Scope.groups."""
        try:
            tasks = await api.query_tasks(scoped_to_user=user_id, filters=filters)
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/scoped/group/{group_id}", response_model=list[HumanTask])
    async def tasks_scoped_to_group(group_id: UUID, filters: TaskFilters = Depends()):
        """List human tasks scoped to a group, ignoring user-targeted scopes."""
        try:
            tasks = await api.query_tasks(scoped_to_group=group_id, filters=filters)
            return filter_tasks_auth(tasks)
        except Exception as e:
            logger.exception("error listing human tasks")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{task_id}", response_model=HumanTask)
    async def get_task(task_id: UUID):
        """
        Get a human task by its ID.

        Args:
            task_id: The ID of the task to retrieve
        """
        try:
            task = await api.query_task(task_id)
        except HTTPException:
            raise
        except TaskNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.exception("error getting human task", task_id=task_id)
            raise HTTPException(status_code=500, detail=str(e))

        validate_authorization_for(
            HumanTaskResource.from_human_task(task),
            HumanTaskAction.TASK_VIEW,
        )
        return task

    @router.post("/{task_id}/complete", response_model=HumanTask)
    async def complete_task(task_id: UUID, request: CompleteTaskRequest = Body(...)):
        """
        Complete a human task with the provided output data.

        Args:
            task_id: The ID of the task to complete
            request: The completion data
        """
        try:
            await complete_human_task(
                task_id=task_id,
                output_data=request.output_data,
                completed_by=request.completed_by,
            )

            # Fetch the updated task to return
            task = await get_human_task(task_id)
            if not task:  # Should not happen if complete_human_task succeeded
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            logger.info("human task completed successfully", task_id=task_id)
            return task
        except ValueError as e:
            logger.exception("valueerror completing task", task_id=task_id)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception("exception completing task", task_id=task_id)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{task_id}/cancel", response_model=HumanTask)
    async def cancel_task(task_id: UUID, request: CancelTaskRequest = Body(...)):
        """
        Cancel a pending human task.

        Args:
            task_id: The ID of the task to cancel
            request: The cancellation details
        """
        try:
            await cancel_human_task(
                task_id=task_id,
                reason=request.reason,
                cancelled_by=request.cancelled_by,
            )

            # Fetch the updated task to return
            task = await get_human_task(task_id)
            if not task:  # Should not happen if cancel_human_task succeeded
                logger.warning(
                    "human task not found after cancellation attempt", task_id=task_id
                )
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            logger.info("human task cancelled successfully", task_id=task_id)
            return task
        except ValueError as e:
            logger.exception("valueerror cancelling task", task_id=task_id)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception("exception cancelling task", task_id=task_id)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{task_id}/reassign", response_model=HumanTask)
    async def reassign_task_endpoint(
        task_id: UUID, user_id: UUID = Body(..., embed=True)
    ):
        """
        Reassign a pending human task to a different user.

        Args:
            task_id: The ID of the task to reassign
            user_id: The ID of the user to assign the task to
        """
        try:
            await api.reassign_task(task_id, user_id)

            # Fetch the updated task to return
            task = await get_human_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            return task
        except HTTPException:
            raise
        except TaskNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except UserNotFound as e:
            raise HTTPException(status_code=401, detail=str(e))
        except TaskNotPending as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/{task_id}/unassign", response_model=HumanTask)
    async def unassign_task_endpoint(task_id: UUID):
        """
        Unassign a pending human task.

        Args:
            task_id: The ID of the task to unassign
        """
        try:
            await api.reassign_task(task_id, None)

            # Fetch the updated task to return
            task = await get_human_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

            return task
        except HTTPException:
            raise
        except TaskNotFound as e:
            raise HTTPException(status_code=404, detail=str(e))
        except UserNotFound as e:
            raise HTTPException(status_code=401, detail=str(e))
        except TaskNotPending as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
