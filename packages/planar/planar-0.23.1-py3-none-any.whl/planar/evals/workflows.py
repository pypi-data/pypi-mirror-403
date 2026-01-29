import json
from datetime import datetime
from time import perf_counter
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from planar.ai.agent import Agent
from planar.ai.models import AgentRunResult
from planar.evals.models import EvalCaseStatus, EvalRunStatus
from planar.evals.schemas import (
    EvalCaseResultCreate,
    EvalRunUpdate,
    EvalScorerConfig,
)
from planar.evals.scorers import scorer_registry
from planar.evals.service import (
    get_run,
    get_suite,
    list_eval_cases,
    record_case_result,
    update_run,
)
from planar.exceptions import ErrorDetails, NotFoundError
from planar.logging import get_logger
from planar.object_registry import ObjectRegistry
from planar.utils import utc_now
from planar.workflows import gather
from planar.workflows.decorators import step, workflow

logger = get_logger(__name__)


def _get_agent(agent_name: str) -> Agent:
    registry = ObjectRegistry.get_instance()
    try:
        agent = registry.get_agent(agent_name)
    except ValueError as exc:
        raise NotFoundError("agent not found") from exc
    return agent


def coerce_agent_input(agent: Agent, payload: dict[str, Any] | str) -> BaseModel | str:
    input_type = agent.input_type

    if isinstance(input_type, type) and issubclass(input_type, BaseModel):
        # input_type is a BaseModel subclass (the class itself, not an instance)
        if not isinstance(payload, dict):
            raise ValueError(
                f"Input value must be a dict compatible with {input_type}, but got {type(payload)}."
                f"\n\nExpected schem properties: {json.dumps(input_type.model_json_schema()['properties'], indent=2)}"
            )
        try:
            return input_type.model_validate(payload)
        except Exception as exc:
            logger.warning(
                "failed to coerce payload into agent input type",
                agent_name=agent.name,
                payload_type=type(payload),
            )
            raise ValueError(
                f"Agent input must be of type {input_type}, but got {type(payload)}"
            ) from exc
    elif isinstance(input_type, type) and input_type is str:
        return str(payload)
    elif input_type is None:
        return str(payload)
    else:
        raise ValueError(
            f"Input value must be a dict or string, but got {type(payload)}"
        )


class EvalRunExecutionContext(BaseModel):
    run_id: UUID
    agent_name: str
    suite_id: UUID
    eval_set_id: UUID
    agent_config_id: UUID | None
    status: EvalRunStatus
    scorers: list[EvalScorerConfig]
    concurrency: int


class EvalCaseContext(BaseModel):
    id: UUID
    input_payload: dict[str, Any] | str
    expected_output: dict[str, Any] | str | None


@step()
async def load_run_context_step(run_id: UUID) -> EvalRunExecutionContext:
    run = await get_run(run_id)
    suite = await get_suite(run.suite_id)
    scorer_configs = [
        EvalScorerConfig.model_validate(scorer) for scorer in suite.scorers
    ]
    return EvalRunExecutionContext(
        run_id=run.id,
        agent_name=run.agent_name,
        suite_id=run.suite_id,
        eval_set_id=run.eval_set_id,
        agent_config_id=run.agent_config_id,
        status=run.status,
        scorers=scorer_configs,
        concurrency=suite.concurrency,
    )


@step()
async def list_eval_cases_step(eval_set_id: UUID) -> list[EvalCaseContext]:
    cases = await list_eval_cases(eval_set_id)
    return [
        EvalCaseContext(
            id=case.id,
            input_payload=case.input_payload,
            expected_output=case.expected_output,
        )
        for case in cases
    ]


@step()
async def mark_run_status_step(
    run_id: UUID,
    status: EvalRunStatus,
    *,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    error: ErrorDetails | None = None,
) -> None:
    await update_run(
        run_id,
        EvalRunUpdate(
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            error=error,
        ),
    )


@step()
async def run_eval_case_step(
    run_context: EvalRunExecutionContext,
    case: EvalCaseContext,
) -> EvalCaseStatus:
    case_start = perf_counter()

    try:
        agent = _get_agent(run_context.agent_name)
        agent_input = coerce_agent_input(agent, case.input_payload)
        agent_result: AgentRunResult[Any] = await agent.run_step(
            agent_input, config_id=run_context.agent_config_id
        )
        if isinstance(agent_result.output, BaseModel):
            agent_output = agent_result.output.model_dump(mode="json")
        else:
            agent_output = str(agent_result.output)

        scorer_results: dict[str, Any] = {}
        passed = True
        for scorer_config in run_context.scorers:
            definition = scorer_registry.get(scorer_config.scorer_name)
            result = await definition.run(
                input_payload=case.input_payload,
                expected_output=case.expected_output,
                agent_output=agent_output,
                agent_reasoning=None,
                settings=scorer_config.settings,
            )
            scorer_results[scorer_config.name] = result
            passed = passed and result.passed

        status = EvalCaseStatus.PASSED if passed else EvalCaseStatus.FAILED
        duration_ms = int((perf_counter() - case_start) * 1000)
        await record_case_result(
            EvalCaseResultCreate(
                run_id=run_context.run_id,
                eval_case_id=case.id,
                input_payload=case.input_payload,
                expected_output=case.expected_output,
                agent_output=agent_output,
                agent_reasoning=None,
                tool_calls=[],
                scorer_results=scorer_results,
                duration_ms=duration_ms,
                status=status,
                error=None,
            )
        )
        return status

    except Exception as exc:
        logger.exception(
            "eval case execution failed",
            run_id=str(run_context.run_id),
            case_id=str(case.id),
        )

        error_details = ErrorDetails.from_exception(exc)

        duration_ms = int((perf_counter() - case_start) * 1000)

        await record_case_result(
            EvalCaseResultCreate(
                run_id=run_context.run_id,
                eval_case_id=case.id,
                input_payload=case.input_payload,
                expected_output=case.expected_output,
                agent_output={},
                agent_reasoning=None,
                tool_calls=[],
                scorer_results={},
                duration_ms=duration_ms,
                status=EvalCaseStatus.FAILED,
                error=error_details,
            )
        )

        return EvalCaseStatus.FAILED


@workflow(name="planar.eval.execute_run")
async def execute_eval_run(run_id: UUID) -> None:
    run_context = await load_run_context_step(run_id)
    if run_context.status != EvalRunStatus.PENDING:
        raise ValueError(f"run is not pending: {run_context.status}")

    await mark_run_status_step(
        run_id,
        EvalRunStatus.RUNNING,
        started_at=utc_now(),
        completed_at=None,
    )

    try:
        cases = await list_eval_cases_step(run_context.eval_set_id)
        case_statuses: list[EvalCaseStatus] = []

        concurrency = run_context.concurrency
        for i in range(0, len(cases), concurrency):
            batch = cases[i : i + concurrency]
            batch_statuses = await gather(
                *[run_eval_case_step(run_context, case) for case in batch]
            )
            case_statuses.extend(batch_statuses)

        any_failed = any(status == EvalCaseStatus.FAILED for status in case_statuses)
        run_status = EvalRunStatus.FAILED if any_failed else EvalRunStatus.SUCCEEDED

        await mark_run_status_step(
            run_id,
            run_status,
            completed_at=utc_now(),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("eval run failed", run_id=str(run_id))

        error_details = ErrorDetails.from_exception(exc)

        await mark_run_status_step(
            run_id,
            EvalRunStatus.FAILED,
            completed_at=utc_now(),
            error=error_details,
        )
        raise exc
