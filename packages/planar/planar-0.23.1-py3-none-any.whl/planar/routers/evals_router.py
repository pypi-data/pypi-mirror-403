from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from planar.evals.exceptions import EvalConflictError, EvalNotFoundError
from planar.evals.schemas import (
    AddEvalCasePayload,
    EvalCaseRead,
    EvalSetCreate,
    EvalSetRead,
    EvalSetUpdate,
    EvalSetWithCases,
    ScorerMetadata,
    UpdateEvalCasePayload,
)
from planar.evals.scorers import scorer_registry
from planar.evals.service import (
    add_eval_case,
    create_eval_set,
    delete_eval_case,
    list_eval_cases,
    list_eval_sets,
    update_eval_case,
    update_eval_set,
)
from planar.logging import get_logger
from planar.security.authorization import (
    EvalAction,
    EvalSetResource,
    EvalSuiteResource,
    validate_authorization_for,
)

logger = get_logger(__name__)


class EvalSetCreateRequest(EvalSetCreate):
    cases: list[AddEvalCasePayload] = Field(default_factory=list)


def create_eval_router() -> APIRouter:
    router = APIRouter(tags=["Evaluations"])

    @router.get(
        "/scorers",
        response_model=list[ScorerMetadata],
    )
    async def list_scorer_definitions():
        """List all available scorer types with their settings schemas."""
        validate_authorization_for(EvalSuiteResource(), EvalAction.EVAL_SUITE_READ)
        scorer_defs = scorer_registry.list_scorers()
        return [
            ScorerMetadata(
                name=scorer_def.name,
                description=scorer_def.description,
                settings_schema=scorer_def.get_settings_json_schema(),
            )
            for scorer_def in scorer_defs
        ]

    @router.post(
        "/sets",
        response_model=EvalSetWithCases,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_eval_set_route(
        payload: EvalSetCreateRequest,
    ):
        """Create an eval set and optional initial cases."""
        validate_authorization_for(EvalSetResource(), EvalAction.EVAL_SET_WRITE)
        try:
            eval_set = await create_eval_set(payload)
            # TODO: Add cases in bulk
            for case_payload in payload.cases:
                await add_eval_case(eval_set.id, case_payload)
        except EvalConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(exc)
            ) from exc

        cases = await list_eval_cases(eval_set.id)
        case_reads = [EvalCaseRead.model_validate(case) for case in cases]
        return EvalSetWithCases(
            id=eval_set.id,
            name=eval_set.name,
            description=eval_set.description,
            input_format=eval_set.input_format,
            output_format=eval_set.output_format,
            created_at=eval_set.created_at,
            updated_at=eval_set.updated_at,
            cases=case_reads,
        )

    @router.get(
        "/sets",
        response_model=list[EvalSetRead],
    )
    async def list_eval_sets_route():
        """List eval sets available (global scope)."""
        validate_authorization_for(EvalSetResource(), EvalAction.EVAL_SET_READ)
        eval_sets = await list_eval_sets()
        return eval_sets

    @router.patch(
        "/sets/{eval_set_id}",
        response_model=EvalSetRead,
    )
    async def update_eval_set_route(eval_set_id: UUID, payload: EvalSetUpdate):
        """Update eval set metadata."""
        validate_authorization_for(
            EvalSetResource(eval_set_id=str(eval_set_id)), EvalAction.EVAL_SET_WRITE
        )
        try:
            eval_set = await update_eval_set(eval_set_id, payload)
        except EvalNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        return eval_set

    @router.get(
        "/sets/{eval_set_id}/cases",
        response_model=list[EvalCaseRead],
    )
    async def list_cases(eval_set_id: UUID):
        validate_authorization_for(
            EvalSetResource(eval_set_id=str(eval_set_id)), EvalAction.EVAL_SET_READ
        )
        cases = await list_eval_cases(eval_set_id)
        return cases

    @router.post(
        "/sets/{eval_set_id}/cases",
        response_model=EvalCaseRead,
        status_code=status.HTTP_201_CREATED,
    )
    async def add_case(eval_set_id: UUID, payload: AddEvalCasePayload):
        validate_authorization_for(
            EvalSetResource(eval_set_id=str(eval_set_id)), EvalAction.EVAL_SET_WRITE
        )
        try:
            case = await add_eval_case(eval_set_id, payload)
        except EvalNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        return case

    @router.patch(
        "/sets/{eval_set_id}/cases/{case_id}",
        response_model=EvalCaseRead,
    )
    async def update_case(
        eval_set_id: UUID, case_id: UUID, payload: UpdateEvalCasePayload
    ):
        validate_authorization_for(
            EvalSetResource(eval_set_id=str(eval_set_id)), EvalAction.EVAL_SET_WRITE
        )
        try:
            case = await update_eval_case(case_id, payload)
        except EvalNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc
        return case

    @router.delete(
        "/sets/{eval_set_id}/cases/{case_id}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def delete_case(eval_set_id: UUID, case_id: UUID):
        validate_authorization_for(
            EvalSetResource(eval_set_id=str(eval_set_id)), EvalAction.EVAL_SET_WRITE
        )
        try:
            await delete_eval_case(case_id)
        except EvalNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc

    return router
