from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from planar.ai.models import AgentConfig
from planar.evals.models import (
    EvalCaseStatus,
    EvalRunStatus,
    EvalSetInputFormat,
    EvalSetOutputFormat,
)
from planar.exceptions import ErrorDetails
from planar.object_config.models import ObjectConfigurationBase


class AddEvalCasePayload(BaseModel):
    """Payload for adding a single case to an eval set."""

    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None = None


class UpdateEvalCasePayload(BaseModel):
    """Payload for updating an existing eval case."""

    input_payload: dict[str, Any] | str | None = None
    expected_output: dict[str, Any] | str | None = None


class EvalSetCreate(BaseModel):
    """Input payload for creating an evaluation set."""

    name: str
    description: str | None = None
    input_format: EvalSetInputFormat
    output_format: EvalSetOutputFormat = EvalSetOutputFormat.NONE


class EvalSetUpdate(BaseModel):
    """Input payload for updating an evaluation set."""

    description: str | None = None
    input_format: EvalSetInputFormat | None = None
    output_format: EvalSetOutputFormat | None = None


class EvalSetRead(BaseModel):
    """Serialized representation of an evaluation set."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    input_format: EvalSetInputFormat
    output_format: EvalSetOutputFormat
    created_at: datetime
    updated_at: datetime


class EvalCaseRead(BaseModel):
    """Serialized representation of an eval case."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    eval_set_id: UUID
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None
    created_at: datetime
    updated_at: datetime


class EvalSetWithCases(EvalSetRead):
    """Eval set representation including its ordered cases."""

    cases: list[EvalCaseRead]


class EvalScorerConfig(BaseModel):
    """Configuration linking a suite entry to a scorer implementation.

    The settings field accepts any dictionary and will be validated against
    the specific scorer's settings schema at runtime.
    """

    name: str
    scorer_name: str
    settings: dict[str, Any] | None = None


class EvalSuiteCreate(BaseModel):
    """Input payload for creating an evaluation suite."""

    name: str
    agent_name: str
    eval_set_id: UUID
    concurrency: Annotated[int, Field(ge=1)] = 4
    scorers: list[EvalScorerConfig] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_scorer_names(self) -> "EvalSuiteCreate":
        names = [scorer.name for scorer in self.scorers]
        if len(names) != len(set(names)):
            raise ValueError("scorer names must be unique within a suite")
        return self


class EvalSuiteUpdate(BaseModel):
    """Input payload for updating an evaluation suite."""

    eval_set_id: UUID | None = None
    concurrency: Annotated[int, Field(ge=1)] | None = None
    scorers: list[EvalScorerConfig] | None = None

    @model_validator(mode="after")
    def validate_unique_scorer_names(self) -> "EvalSuiteUpdate":
        if self.scorers is None:
            return self

        names = [scorer.name for scorer in self.scorers]
        if len(names) != len(set(names)):
            raise ValueError("scorer names must be unique within a suite")
        return self


class EvalSuiteRead(BaseModel):
    """Serialized representation of an evaluation suite."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    agent_name: str
    eval_set_id: UUID
    concurrency: int
    scorers: list[EvalScorerConfig]
    created_at: datetime
    updated_at: datetime


class EvalRunCreate(BaseModel):
    """Input payload for creating an evaluation run record."""

    agent_name: str
    suite_id: UUID
    agent_config_id: UUID | None = None


class EvalRunUpdate(BaseModel):
    """Input payload for updating an evaluation run."""

    status: EvalRunStatus | None = None
    total_cases: int | None = None
    error: ErrorDetails | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @field_validator("total_cases")
    @classmethod
    def validate_total_cases(cls, total_cases: int | None) -> int | None:
        if total_cases is None:
            return total_cases
        if total_cases < 0:
            raise ValueError("total_cases must be non-negative")
        return total_cases


class EvalRunRead(BaseModel):
    """Serialized representation of an evaluation run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_name: str
    suite_id: UUID
    agent_config_id: UUID | None = None
    eval_set_id: UUID
    status: EvalRunStatus
    total_cases: int
    error: ErrorDetails | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    agent_config: ObjectConfigurationBase[AgentConfig] | None = None


class ScorerResultPayload(BaseModel):
    """Serialized representation of a scorer result."""

    score: float
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)


class EvalCaseResultCreate(BaseModel):
    """Input payload for creating an evaluation case result."""

    run_id: UUID
    eval_case_id: UUID
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None
    agent_output: dict[str, Any] | str
    agent_reasoning: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    scorer_results: dict[str, ScorerResultPayload] = Field(default_factory=dict)
    duration_ms: int
    status: EvalCaseStatus
    error: ErrorDetails | None = None

    @field_validator("duration_ms")
    @classmethod
    def validate_duration(cls, duration_ms: int) -> int:
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        return duration_ms


class EvalCaseResultRead(BaseModel):
    """Serialized representation of an evaluation case result."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    eval_case_id: UUID
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None
    agent_output: dict[str, Any] | str
    agent_reasoning: str | None
    tool_calls: list[dict[str, Any]]
    scorer_results: dict[str, ScorerResultPayload]
    duration_ms: int
    status: EvalCaseStatus
    error: ErrorDetails | None = None
    created_at: datetime
    updated_at: datetime


class ScorerMetadata(BaseModel):
    """Metadata about an available scorer type."""

    name: str = Field(description="Unique identifier for the scorer")
    description: str = Field(
        description="Human-readable description of what the scorer does"
    )
    settings_schema: dict[str, Any] | None = Field(
        default=None,
        description="JSON Schema defining the scorer's configurable settings",
    )
