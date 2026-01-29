from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field

from planar.db import PlanarInternalBase
from planar.modeling.mixins import TimestampMixin, timestamp_column
from planar.modeling.mixins.uuid_primary_key import UUIDPrimaryKeyMixin


class EvalSetInputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"


class EvalSetOutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    NONE = "none"


class EvalRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"


class EvalCaseStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvalSet(
    UUIDPrimaryKeyMixin,
    PlanarInternalBase,
    TimestampMixin,
    table=True,
):
    """Persisted collection of canonical evaluation cases."""

    name: str = Field(index=True, unique=True)
    description: str | None = None
    input_format: EvalSetInputFormat
    output_format: EvalSetOutputFormat = Field(default=EvalSetOutputFormat.NONE)


class EvalCase(
    UUIDPrimaryKeyMixin,
    PlanarInternalBase,
    TimestampMixin,
    table=True,
):
    """Individual test case tied to an evaluation set."""

    eval_set_id: UUID = Field(
        foreign_key="planar.eval_set.id",
        index=True,
    )
    input_payload: dict[str, Any] | str = Field(sa_column=Column(JSON, nullable=False))
    expected_output: dict[str, Any] | str | None = Field(
        default=None, sa_column=Column(JSON)
    )


class EvalRun(
    UUIDPrimaryKeyMixin,
    PlanarInternalBase,
    TimestampMixin,
    table=True,
):
    """Represents an evaluation run execution against a specific agent configuration."""

    agent_name: str = Field(index=True)
    suite_id: UUID = Field(foreign_key="planar.eval_suite.id", index=True)
    agent_config_id: UUID | None = Field(
        foreign_key="planar.object_configuration.id", index=True, default=None
    )
    eval_set_id: UUID = Field(foreign_key="planar.eval_set.id", index=True)
    status: EvalRunStatus = Field(default=EvalRunStatus.PENDING, index=True)
    total_cases: int
    error: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    started_at: datetime | None = timestamp_column(nullable=True)
    completed_at: datetime | None = timestamp_column(nullable=True, default=None)


class EvalCaseResult(
    UUIDPrimaryKeyMixin,
    PlanarInternalBase,
    TimestampMixin,
    table=True,
):
    """Per-case execution result for an evaluation run."""

    __table_args__ = (
        UniqueConstraint(
            "run_id",
            "eval_case_id",
            name="uq_eval_case_result_run_case",
        ),
    )

    run_id: UUID = Field(foreign_key="planar.eval_run.id", index=True)
    eval_case_id: UUID = Field(foreign_key="planar.eval_case.id", index=True)
    input_payload: dict[str, Any] | str = Field(sa_column=Column(JSON, nullable=False))
    expected_output: dict[str, Any] | str | None = Field(
        default=None, sa_column=Column(JSON)
    )
    agent_output: dict[str, Any] | str = Field(sa_column=Column(JSON, nullable=False))
    agent_reasoning: str | None = None
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    scorer_results: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    duration_ms: int
    status: EvalCaseStatus = Field(index=True)
    error: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class EvalSuite(
    UUIDPrimaryKeyMixin,
    PlanarInternalBase,
    TimestampMixin,
    table=True,
):
    """Configuration binding agents, eval sets, and scorers for evaluations."""

    __table_args__ = (
        UniqueConstraint(
            "agent_name",
            "name",
            name="uq_eval_suite_agent_name",
        ),
    )

    name: str = Field(index=True)
    agent_name: str = Field(index=True)
    eval_set_id: UUID = Field(foreign_key="planar.eval_set.id", index=True)
    concurrency: int = Field(default=4)
    scorers: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
