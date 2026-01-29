from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm.strategy_options import joinedload, selectinload
from sqlmodel import exists, select

from planar.human.exceptions import TaskNotFound, TaskNotPending, UserNotFound
from planar.human.models import (
    Assignment,
    HumanTask,
    HumanTaskStatus,
    TaskFilters,
    TaskGroupScope,
    TaskScope,
    TaskUserScope,
)
from planar.logging import get_logger
from planar.security.auth_context import require_principal
from planar.security.authorization import (
    AssignmentResource,
    HumanTaskAction,
    HumanTaskResource,
    UserResource,
    validate_authorization_for,
)
from planar.session import get_session
from planar.user.models import IDPGroup, IDPUser
from planar.utils import utc_now

logger = get_logger(__name__)


def _no_op(existing_assignment: Assignment | None, user_id: UUID | None) -> bool:
    # Task is being assigned to the current assignee -> no-op
    if out := existing_assignment and existing_assignment.assignee_id == user_id:
        return out
    # Unassigned task is being unassigned -> no-op
    if out := not existing_assignment and not user_id:
        return out
    return False


BASE_TASK_QUERY = (
    select(HumanTask)
    .options(
        joinedload(HumanTask.assignment)
        .joinedload(Assignment.assignee)
        .selectinload(IDPUser.groups)  # pyright: ignore[reportArgumentType]
    )
    .options(
        joinedload(HumanTask.assignment)
        .joinedload(Assignment.assignor)
        .selectinload(IDPUser.groups)  # pyright: ignore[reportArgumentType]
    )
    .options(
        joinedload(HumanTask.scope).selectinload(TaskScope.groups)  # pyright: ignore[reportArgumentType]
    )
    .options(
        joinedload(HumanTask.scope).selectinload(TaskScope.users)  # pyright: ignore[reportArgumentType]
    )
)


async def query_task(task_id: UUID) -> HumanTask:
    """Query a task by ID."""
    session = get_session()

    task_result = await session.exec(BASE_TASK_QUERY.where(HumanTask.id == task_id))
    task = task_result.first()
    if not task:
        logger.warning("human task not found", task_id=task_id)
        raise TaskNotFound(task_id)

    return task


async def query_tasks(
    filters: TaskFilters | None,
    *,
    are_unassigned: bool = False,
    assigned_to: UUID | None = None,
    scoped_to_user: UUID | None = None,
    scoped_to_group: UUID | None = None,
) -> list[HumanTask]:
    """Query `HumanTask`s based on a set of filters."""
    if (
        bool(are_unassigned)
        + bool(assigned_to)
        + bool(scoped_to_user)
        + bool(scoped_to_group)
    ) != 1:
        raise ValueError(
            "must provide exactly one of are_unassigned, assigned_to, scoped_to_user, or scoped_to_group"
        )

    session = get_session()

    task_query = BASE_TASK_QUERY

    if filters:
        task_query = task_query.where(*filters.to_query())

    if assigned_to:
        task_query = task_query.where(
            HumanTask.assignment.has(Assignment.assignee_id == assigned_to)  # pyright: ignore[reportArgumentType]
        )
    elif scoped_to_user:
        task_query = task_query.where(
            HumanTask.scope.has(
                or_(
                    TaskScope.users.any(IDPUser.id == scoped_to_user),  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
                    TaskScope.groups.any(  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
                        IDPGroup.users.any(IDPUser.id == scoped_to_user)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
                    ),
                )
            )
        )
    elif scoped_to_group:
        task_query = task_query.where(
            HumanTask.scope.has(TaskScope.groups.any(IDPGroup.id == scoped_to_group))  # pyright: ignore[reportAttributeAccessIssue, reportUnknownArgumentType, reportUnknownMemberType]
        )
    else:
        task_query = task_query.where(~HumanTask.assignment.has())

    task_result = await session.exec(task_query)
    return list(task_result.all())


async def reassign_task(task_id: UUID, assign_to: UUID | None) -> None:
    """Reassign a PENDING human task to a different user, or unassign it."""
    logger.debug("reassigning human task", task_id=task_id, user_id=assign_to)

    session = get_session()

    task_query = await session.exec(
        select(HumanTask)
        .where(HumanTask.id == task_id)
        .options(
            joinedload(HumanTask.assignment)
            .joinedload(Assignment.assignee)
            .selectinload(IDPUser.groups)  # pyright: ignore[reportArgumentType]
        )
        .options(
            joinedload(HumanTask.assignment)
            .joinedload(Assignment.assignor)
            .selectinload(IDPUser.groups)  # pyright: ignore[reportArgumentType]
        )
        .options(
            joinedload(HumanTask.scope).selectinload(TaskScope.groups)  # pyright: ignore[reportArgumentType]
        )
        .options(
            joinedload(HumanTask.scope).selectinload(TaskScope.users)  # pyright: ignore[reportArgumentType]
        )
    )
    task = task_query.first()
    if not task:
        logger.warning("human task not found for reassignment", task_id=task_id)
        raise TaskNotFound(task_id)

    if task.status != HumanTaskStatus.PENDING:
        logger.warning(
            "attempt to reassign human task not in pending status",
            task_id=task_id,
            status=task.status,
        )
        raise TaskNotPending(task_id, task.status)

    existing_assignment = task.assignment
    if _no_op(existing_assignment, assign_to):
        return

    principal = require_principal()
    if principal.user is None:
        raise UserNotFound(principal.user_email)

    if assign_to:
        assign_to_user_result = await session.exec(
            select(IDPUser)
            .where(IDPUser.id == assign_to)
            .options(selectinload(IDPUser.groups))  # pyright: ignore[reportArgumentType]
        )
        assign_to_user = assign_to_user_result.one_or_none()
        if not assign_to_user:
            raise UserNotFound(str(assign_to))
        assignee = UserResource.from_user(assign_to_user)
    else:
        assignee = None

    proposed_assignment = AssignmentResource(
        task_id=str(task.id),
        assignee=assignee,
        assignor=principal.user,
    )

    validate_authorization_for(
        HumanTaskResource.from_human_task(task, proposed_assignment),
        HumanTaskAction.TASK_ASSIGN,
    )

    if existing_assignment:
        if existing_assignment.assignee_id == assign_to:
            raise Exception(
                "attempt to reassign task to current assignee (should be caught by _no_op)"
            )
        existing_assignment.disabled_at = utc_now()
        session.add(existing_assignment)

    if assign_to:
        new_assignment = Assignment(
            task_id=task_id,
            assignee_id=assign_to,
            assignor_id=UUID(principal.user.user_id),
        )
        session.add(new_assignment)
        logger.info("human task reassigned", user_id=assign_to, task_id=task_id)
    elif existing_assignment:
        # An unassignment is disabling the existing `Assignment` without replacing it.
        logger.info("human task unassigned", task_id=task_id)
    else:
        raise Exception(
            "attempt to unassign a unassigned task (should be caught by _no_op)"
        )

    await session.commit()


async def orphaned_scope_tasks() -> list[HumanTask]:
    """Find tasks with orphaned scope (no active users or groups)."""
    session = get_session()

    tasks_result = await session.exec(
        BASE_TASK_QUERY.filter(HumanTask.status == HumanTaskStatus.PENDING)  # pyright: ignore[reportArgumentType]
        .join(HumanTask.scope)
        .where(
            ~exists(
                select(1)
                .select_from(TaskUserScope)
                .join(IDPUser, TaskUserScope.user_id == IDPUser.id)  # pyright: ignore[reportArgumentType]
                .where(
                    TaskUserScope.task_scope_id == TaskScope.id,
                    IDPUser.disabled_at.is_(None),  # pyright: ignore[reportOptionalMemberAccess, reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
                )
            ),
            ~exists(
                select(1)
                .select_from(TaskGroupScope)
                .join(IDPGroup, TaskGroupScope.group_id == IDPGroup.id)  # pyright: ignore[reportArgumentType]
                .where(
                    TaskGroupScope.task_scope_id == TaskScope.id,
                    IDPGroup.disabled_at.is_(None),  # pyright: ignore[reportOptionalMemberAccess, reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
                    IDPGroup.num_members > 0,
                )
            ),
        )
    )

    return list(tasks_result.all())


async def orphaned_assignment_tasks() -> list[HumanTask]:
    """Find tasks assigned to disabled users."""
    session = get_session()

    tasks_result = await session.exec(
        BASE_TASK_QUERY.filter(HumanTask.status == HumanTaskStatus.PENDING)  # pyright: ignore[reportArgumentType]
        .join(HumanTask.assignment)
        .join(Assignment.assignee)
        .where(
            IDPUser.disabled_at.isnot(None),  # pyright: ignore[reportOptionalMemberAccess, reportUnknownMemberType, reportUnknownArgumentType, reportAttributeAccessIssue]
        )
    )

    return list(tasks_result.all())
