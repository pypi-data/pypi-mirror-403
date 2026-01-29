from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ColumnElement, text
from sqlalchemy.orm.base import Mapped
from sqlmodel import JSON, Column, Field, Index, Relationship

from planar.db import PlanarInternalBase
from planar.modeling.mixins import TimestampMixin
from planar.modeling.mixins.auditable import AuditableMixin
from planar.modeling.mixins.uuid_primary_key import UUIDPrimaryKeyMixin
from planar.user.models import IDPGroup, IDPUser


class HumanTaskStatus(str, Enum):
    """Status values for human tasks."""

    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class UserScope(BaseModel):
    ids: set[UUID]


class GroupScope(BaseModel):
    ids: set[UUID]


Scope = UserScope | GroupScope


class TaskFilters(BaseModel):
    status: HumanTaskStatus | None = None
    workflow_id: UUID | None = None
    name: str | None = None

    def to_query(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if self.status:
            conditions.append(HumanTask.status == self.status)  # pyright: ignore[reportArgumentType]
        if self.workflow_id:
            conditions.append(HumanTask.workflow_id == self.workflow_id)  # pyright: ignore[reportArgumentType]
        if self.name:
            conditions.append(HumanTask.name == self.name)  # pyright: ignore[reportArgumentType]
        return conditions


class Assignment(
    UUIDPrimaryKeyMixin, AuditableMixin, PlanarInternalBase, TimestampMixin, table=True
):
    """
    Assign a HumanTask a DRI.

    We handle re-assignments by creating a new `Assignment` and disabling the old one
    to maintain history for display in the UI.
    """

    __table_args__ = (
        Index(
            "ix_one_active_assignment_per_task",
            "task_id",
            unique=True,
            postgresql_where="disabled_at IS NULL",
            sqlite_where=text("disabled_at IS NULL"),
        ),
    )

    task_id: UUID = Field(foreign_key="human_task.id", index=True)
    assignee_id: UUID = Field(foreign_key="idp_user.id", index=True)
    assignee: Mapped[IDPUser] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Assignment.assignee_id]"}
    )

    disabled_at: datetime | None = Field(default=None, index=True)

    assignor_id: UUID | None = Field(
        default=None, foreign_key="idp_user.id", index=True
    )
    assignor: Mapped[IDPUser | None] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Assignment.assignor_id]"}
    )


class TaskUserScope(PlanarInternalBase, TimestampMixin, table=True):
    task_scope_id: UUID = Field(primary_key=True, foreign_key="task_scope.id")
    user_id: UUID = Field(primary_key=True, foreign_key="idp_user.id")


class TaskGroupScope(PlanarInternalBase, TimestampMixin, table=True):
    task_scope_id: UUID = Field(primary_key=True, foreign_key="task_scope.id")
    group_id: UUID = Field(primary_key=True, foreign_key="idp_group.id")


class TaskScope(
    UUIDPrimaryKeyMixin, AuditableMixin, PlanarInternalBase, TimestampMixin, table=True
):
    """
    Defines the set of `IDPUser`s (either directly or via groups) that can see/self-assign the Task.

    We handle re-scopes by creating a new `TaskScope` and disabling the old one
    to maintain history for display in the UI.
    """

    __table_args__ = (
        Index(
            "ix_one_active_scope_per_task",
            "task_id",
            unique=True,
            postgresql_where="disabled_at IS NULL",
            sqlite_where=text("disabled_at IS NULL"),
        ),
    )

    task_id: UUID = Field(foreign_key="human_task.id", index=True)
    disabled_at: datetime | None = Field(default=None, index=True)

    users: list[IDPUser] = Relationship(link_model=TaskUserScope)
    groups: list[IDPGroup] = Relationship(link_model=TaskGroupScope)


class HumanTask(
    UUIDPrimaryKeyMixin, AuditableMixin, PlanarInternalBase, TimestampMixin, table=True
):
    """
    Database model for human tasks that require input from a human operator.

    Extends UUIDPrimaryKeyMixin which provides:
    - id: Primary key

    Extends AuditableMixin which provides:
    - created_by, updated_by: Audit fields

    And TimeStampMixin which provides:
    - created_at, updated_at: Timestamp fields
    """

    __table_args__ = (
        Index("ix_pending_tasks", "id", postgresql_where="status = 'PENDING'"),
    )

    # Task identifying information
    name: str = Field(index=True)
    title: str
    description: str | None = None

    # Workflow association
    workflow_id: UUID = Field(index=True)
    workflow_name: str

    # Input data for context
    input_schema: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    input_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    message: str | None = Field(default=None)

    # Schema for expected output
    output_schema: dict[str, Any] = Field(sa_column=Column(JSON))
    output_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Suggested data for the form (optional)
    suggested_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    # Task status
    status: HumanTaskStatus = Field(default=HumanTaskStatus.PENDING)

    # Active assignment and scope (where disabled_at IS NULL)
    assignment: Mapped[Assignment | None] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(HumanTask.id == Assignment.task_id, Assignment.disabled_at.is_(None))",
            "uselist": False,
            "viewonly": True,
        }
    )

    scope: Mapped[TaskScope | None] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(HumanTask.id == TaskScope.task_id, TaskScope.disabled_at.is_(None))",
            "uselist": False,
            "viewonly": True,
        }
    )

    # Disabled assignments
    past_assignments: Mapped[list[Assignment]] = Relationship(
        sa_relationship_kwargs={
            "primaryjoin": "and_(HumanTask.id == Assignment.task_id, Assignment.disabled_at.isnot(None))",
            "uselist": True,
            "viewonly": True,
        }
    )

    # Completion tracking
    completed_by: str | None = None
    completed_at: datetime | None = None

    # Time constraints
    deadline: datetime | None = None


class HumanTaskResult[TOutput: BaseModel](BaseModel):
    """Result of a completed human task."""

    task_id: UUID
    output: TOutput
    completed_at: datetime
