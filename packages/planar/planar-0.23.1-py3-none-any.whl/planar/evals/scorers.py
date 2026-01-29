import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from pydantic import BaseModel, Field, ValidationError
from pydantic_ai.models import KnownModelName

from planar.ai.models import PlanarModelSettings, SystemMessage, UserMessage
from planar.ai.pydantic_ai import model_run
from planar.evals.schemas import EvalScorerConfig, ScorerResultPayload


class ScorerRegistryError(Exception):
    """Base error for scorer registry operations."""


class ScorerNotRegisteredError(ScorerRegistryError):
    """Raised when a scorer name has not been registered."""


class ScorerSettingsValidationError(ScorerRegistryError):
    """Raised when scorer settings fail validation."""


_ScorerSettings = TypeVar("_ScorerSettings", bound=BaseModel)


ScorerCallable = Callable[
    [
        dict[str, Any] | str,
        dict[str, Any] | str | None,
        dict[str, Any] | str,
        str | None,
        _ScorerSettings | None,
    ],
    Awaitable[ScorerResultPayload],
]


@dataclass(slots=True)
class ScorerDefinition:
    name: str
    description: str
    scorer_fn: ScorerCallable
    settings_model: type[BaseModel] | None = None

    def validate_settings(
        self, settings: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if not self.settings_model:
            return settings
        try:
            model = self.settings_model.model_validate(settings or {})
        except ValidationError as exc:
            raise ScorerSettingsValidationError(str(exc)) from exc
        return model.model_dump(mode="json")

    def get_settings_json_schema(self) -> dict[str, Any] | None:
        """Generate JSON Schema from the settings model."""
        if not self.settings_model:
            return None
        return self.settings_model.model_json_schema()

    async def run(
        self,
        *,
        input_payload: dict[str, Any] | str,
        expected_output: dict[str, Any] | str | None,
        agent_output: dict[str, Any] | str,
        agent_reasoning: str | None,
        settings: dict[str, Any] | None,
    ) -> ScorerResultPayload:
        parsed_settings: BaseModel | None = None
        if self.settings_model:
            parsed_settings = self.settings_model.model_validate(settings or {})
        elif settings is not None:
            raise ValueError("Scorer settings are not expected")

        return await self.scorer_fn(
            input_payload,
            expected_output,
            agent_output,
            agent_reasoning,
            parsed_settings,
        )


class ScorerRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, ScorerDefinition] = {}

    def register(self, definition: ScorerDefinition) -> None:
        self._definitions[definition.name] = definition

    def get(self, scorer_name: str) -> ScorerDefinition:
        try:
            return self._definitions[scorer_name]
        except KeyError as exc:
            raise ScorerNotRegisteredError(scorer_name) from exc

    def list_scorers(self) -> list[ScorerDefinition]:
        return list(self._definitions.values())

    def sanitize_config(self, config: EvalScorerConfig) -> EvalScorerConfig:
        definition = self.get(config.scorer_name)
        validated = definition.validate_settings(config.settings)
        return EvalScorerConfig(
            name=config.name,
            scorer_name=config.scorer_name,
            settings=validated,
        )

    def sanitize_config_to_dict(self, config: EvalScorerConfig) -> dict[str, Any]:
        sanitized = self.sanitize_config(config)
        return sanitized.model_dump(mode="json")


scorer_registry = ScorerRegistry()


def _format_payload(value: dict[str, Any] | str | None) -> str:
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)


def extract_field_path(value: dict[str, Any] | str, field_path: str | None) -> Any:
    """Extract a value from a nested dict using dot-notation path."""
    if field_path is None:
        return value

    # Parse JSON string if needed
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None

    if not isinstance(value, dict):
        return None

    # Navigate through the path
    parts = field_path.split(".")
    current = value
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None

    return current


class ExactMatchSettings(BaseModel):
    field_path: str | None = Field(
        default=None,
        description="Optional dot-notation path to extract a specific field for comparison (e.g., 'product_name' or 'nested.field')",
    )


async def exact_match_scorer(
    input_payload: dict[str, Any] | str,
    expected_output: dict[str, Any] | str | None,
    agent_output: dict[str, Any] | str,
    agent_reasoning: str | None,
    settings: ExactMatchSettings | None,
) -> ScorerResultPayload:
    if settings is None:
        settings = ExactMatchSettings()

    # If field_path is specified, extract the specific field from both outputs
    if settings.field_path:
        expected_value = (
            extract_field_path(expected_output, settings.field_path)
            if expected_output is not None
            else None
        )
        actual_value = extract_field_path(agent_output, settings.field_path)

        passed = expected_value == actual_value
    else:
        # Default behavior: compare entire outputs
        passed = expected_output is not None and agent_output == expected_output

    return ScorerResultPayload(score=1.0 if passed else 0.0, passed=passed)


class CaseInsensitiveSettings(BaseModel):
    trim_whitespace: bool = Field(default=True)


async def case_insensitive_match_scorer(
    input_payload: dict[str, Any] | str,
    expected_output: dict[str, Any] | str | None,
    agent_output: dict[str, Any] | str,
    agent_reasoning: str | None,
    settings: CaseInsensitiveSettings | None,
) -> ScorerResultPayload:
    # TODO: Support dict case insensitive matching
    if not isinstance(expected_output, str) or not isinstance(agent_output, str):
        return ScorerResultPayload(score=0.0, passed=False)

    if settings is None:
        settings = CaseInsensitiveSettings()

    def _normalize(value: str) -> str:
        normalized = value.lower()
        if settings.trim_whitespace:
            normalized = normalized.strip()
        return normalized

    passed = _normalize(agent_output) == _normalize(expected_output)
    return ScorerResultPayload(score=1.0 if passed else 0.0, passed=passed)


class NumericToleranceSettings(BaseModel):
    abs_tol: float = Field(default=0.0, ge=0.0)


async def numeric_tolerance_scorer(
    input_payload: dict[str, Any] | str,
    expected_output: dict[str, Any] | str | None,
    agent_output: dict[str, Any] | str,
    agent_reasoning: str | None,
    settings: NumericToleranceSettings | None,
) -> ScorerResultPayload:
    if not isinstance(agent_output, (int, float, str)):
        return ScorerResultPayload(score=0.0, passed=False)
    if expected_output is None or not isinstance(expected_output, (int, float, str)):
        return ScorerResultPayload(score=0.0, passed=False)

    try:
        expected_value = float(expected_output)
        actual_value = float(agent_output)
    except (TypeError, ValueError):
        return ScorerResultPayload(score=0.0, passed=False)

    if settings is None:
        settings = NumericToleranceSettings()

    difference = abs(actual_value - expected_value)
    passed = difference <= settings.abs_tol
    score = 1.0 if passed else max(0.0, 1.0 - difference)
    return ScorerResultPayload(score=score, passed=passed)


LLM_JUDGE_SYSTEM_PROMPT = (
    "You are an impartial evaluation judge. Score the agent output using the rubric "
    "provided. Consider both correctness and faithfulness to the ground truth. "
    "Return JSON with fields 'score' (0-1) and 'reasoning'."
)


class LlmJudgeResponse(BaseModel):
    score: float = Field(
        description="Judge-assigned score (expected to be between 0 and 1).",
        ge=0,
        le=1,
    )
    reasoning: str


class LlmJudgeSettings(BaseModel):
    rubric: str = Field(
        description="Instructions for how the judge should evaluate the agent output.",
        json_schema_extra={"format": "textarea"},
    )
    judge_model: KnownModelName = Field(
        default="openai:gpt-4.1",
        description="LLM used to perform the evaluation.",
    )
    passing_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score threshold required for the case to pass.",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for the judge model.",
    )


async def llm_judge_scorer(
    input_payload: dict[str, Any] | str,
    expected_output: dict[str, Any] | str | None,
    agent_output: dict[str, Any] | str,
    agent_reasoning: str | None,
    settings: LlmJudgeSettings | None,
) -> ScorerResultPayload:
    if settings is None:
        raise ValueError("llm_judge scorer requires settings")

    expected_formatted = _format_payload(expected_output)
    agent_formatted = _format_payload(agent_output)
    rubric = settings.rubric.strip()

    if not rubric:
        raise ValueError("llm_judge scorer requires a non-empty rubric")

    user_message = (
        "Evaluate the agent output using the rubric.\n\n"
        f"Rubric:\n{rubric}\n\n"
        f"Expected output:\n{expected_formatted}\n\n"
        f"Agent output:\n{agent_formatted}\n\n"
        "Respond with JSON containing 'score' (a float between 0 and 1) and "
        "'reasoning' explaining the judgement."
    )

    model_settings: PlanarModelSettings | None = cast(
        PlanarModelSettings, {"temperature": settings.temperature}
    )

    response = await model_run(
        model=settings.judge_model,
        max_extra_turns=0,
        model_settings=model_settings,
        messages=[
            SystemMessage(content=LLM_JUDGE_SYSTEM_PROMPT),
            UserMessage(content=user_message),
        ],
        output_type=LlmJudgeResponse,
    )

    judge_result = response.response.content
    if judge_result is None:
        return ScorerResultPayload(
            score=0.0,
            passed=False,
            details={"reasoning": "Judge model did not return a score."},
        )

    score = max(0.0, min(1.0, judge_result.score))
    passed = score >= settings.passing_threshold
    details = {"reasoning": judge_result.reasoning}
    return ScorerResultPayload(score=score, passed=passed, details=details)


scorer_registry.register(
    ScorerDefinition(
        name="exact_match",
        description="Exact equality comparison",
        scorer_fn=exact_match_scorer,
        settings_model=ExactMatchSettings,
    )
)

scorer_registry.register(
    ScorerDefinition(
        name="case_insensitive_match",
        description="Case-insensitive string equality",
        scorer_fn=case_insensitive_match_scorer,
        settings_model=CaseInsensitiveSettings,
    )
)

scorer_registry.register(
    ScorerDefinition(
        name="numeric_tolerance",
        description="Numeric comparison within an absolute tolerance",
        scorer_fn=numeric_tolerance_scorer,
        settings_model=NumericToleranceSettings,
    )
)

scorer_registry.register(
    ScorerDefinition(
        name="llm_judge",
        description="LLM-as-a-judge with rubric driven scoring",
        scorer_fn=llm_judge_scorer,
        settings_model=LlmJudgeSettings,
    )
)
