from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Coroutine, Sequence, Type, TypeVar, cast
from uuid import UUID

from pydantic import BaseModel

from planar.logging import get_logger
from planar.rules.models import Rule
from planar.rules.rule_configuration import rule_configuration
from planar.rules.runner import EvaluateResponse, evaluate_rule
from planar.workflows.decorators import step
from planar.workflows.models import StepType
from planar.workflows.step_meta import RuleConfigMeta, set_step_metadata

logger = get_logger(__name__)

RULE_REGISTRY = {}

# Define type variables for input and output BaseModel types
T = TypeVar("T", bound=BaseModel)
U = TypeVar("U", bound=BaseModel)


@dataclass(slots=True)
class RuleBatchItemError:
    index: int
    input_item: Any
    error: Any


class RuleBatchEvaluationError(Exception):
    """Raised when a rule batch evaluation fails for one or more items."""

    failures: list[RuleBatchItemError]

    def __init__(self, failures: Sequence[RuleBatchItemError]):
        self.failures = list[RuleBatchItemError](failures)
        first_failure = self.failures[0]

        first_error = first_failure.error
        error_repr = (
            first_error.model_dump(mode="json")
            if isinstance(first_error, BaseModel)
            else str(first_error)
        )

        if len(self.failures) == 1:
            message = (
                f"Rule batch evaluation failed at index {first_failure.index}: "
                f"{error_repr}"
            )
        else:
            message = (
                f"Rule batch evaluation failed for {len(self.failures)} items; "
                f"first failure at index {first_failure.index}: {error_repr}"
            )

        super().__init__(message)


def serialize_for_rule_evaluation(obj: Any) -> Any:
    """
    Custom serializer that converts Pydantic model_dump() to a format that can be
    interpreted by the rule engine.
    """
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        # Zen rule engine throws an error if the datetime does not include timezone
        # ie. `"2025-05-27T00:21:44.802433" is not a "date-time"`
        return obj.isoformat() + "Z" if obj.tzinfo is None else obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_rule_evaluation(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_rule_evaluation(item) for item in obj]
    else:
        return obj


#### Decorator
def rule(*, description: str):
    def _get_input_and_return_types(
        func: Callable,
    ) -> tuple[Type[BaseModel], Type[BaseModel]]:
        """
        Validates that a rule method has proper type annotations.
        Returns a tuple of (input_type, return_type).
        """

        # Get function parameters using inspect module
        signature = inspect.signature(func)
        params = list(signature.parameters.keys())

        if len(params) != 1 or "self" in params:
            err_msg = (
                "@rule method must have exactly one input argument (and cannot be self)"
            )
            logger.warning(
                "rule definition error", function_name=func.__name__, error=err_msg
            )
            raise ValueError(err_msg)

        # Check for missing annotations using signature
        missing_annotations = [
            p
            for p in params
            if signature.parameters[p].annotation == inspect.Parameter.empty
        ]
        if missing_annotations:
            err_msg = (
                f"Missing annotations for parameters: {', '.join(missing_annotations)}"
            )
            logger.warning(
                "rule definition error", function_name=func.__name__, error=err_msg
            )
            raise ValueError(err_msg)

        if signature.return_annotation == inspect.Signature.empty:
            err_msg = "@rule method must have a return type annotation"
            logger.warning(
                "rule definition error", function_name=func.__name__, error=err_msg
            )
            raise ValueError(err_msg)

        param_name = params[0]
        input_type = signature.parameters[param_name].annotation
        return_type = signature.return_annotation

        # Ensure both input and return types are pydantic BaseModels
        if not issubclass(input_type, BaseModel):
            err_msg = f"Input type {input_type.__name__} must be a pydantic BaseModel"
            logger.warning(
                "rule definition error", function_name=func.__name__, error=err_msg
            )
            raise ValueError(err_msg)
        if not issubclass(return_type, BaseModel):
            err_msg = f"Return type {return_type.__name__} must be a pydantic BaseModel"
            logger.warning(
                "rule definition error", function_name=func.__name__, error=err_msg
            )
            raise ValueError(err_msg)

        return input_type, return_type

    def decorator(func: Callable[[T], U]) -> Callable[[T], Coroutine[Any, Any, U]]:
        input_type, return_type = _get_input_and_return_types(func)

        rule = Rule(
            name=func.__name__,
            description=description,
            input=input_type,
            output=return_type,
        )

        RULE_REGISTRY[func.__name__] = rule
        logger.debug("registered rule", rule_name=func.__name__)

        async def _get_active_config():
            override_result = await rule_configuration.read_configs_with_default(
                func.__name__, rule.to_config()
            )

            active_config = next(
                (config for config in override_result if config.active), None
            )

            if not active_config:
                raise ValueError(
                    f"No active configuration found for rule {func.__name__}"
                )

            logger.debug(
                "active config for rule",
                rule_name=func.__name__,
                version=active_config.version,
            )

            return active_config

        def _execute_default_batch(input_items: list[T]) -> list[U]:
            results: list[U] = []
            failures: list[RuleBatchItemError] = []
            for index, item in enumerate(input_items):
                try:
                    result = func(item)
                except Exception as exc:
                    logger.exception(
                        "rule batch item execution failed",
                        rule_name=func.__name__,
                        index=index,
                    )
                    failures.append(
                        RuleBatchItemError(index=index, input_item=item, error=exc)
                    )
                    continue

                if not isinstance(result, return_type):
                    message = f"Expected {return_type.__name__} but got {type(result).__name__}"
                    logger.error(
                        "rule batch output type mismatch",
                        rule_name=func.__name__,
                        index=index,
                        message=message,
                    )
                    failures.append(
                        RuleBatchItemError(
                            index=index,
                            input_item=item,
                            error=TypeError(message),
                        )
                    )
                    continue

                results.append(cast(U, result))

            if failures:
                raise RuleBatchEvaluationError(failures)

            return results

        def _execute_jdm_batch(active_config, input_items: list[T]) -> list[U]:
            results: list[U] = []
            failures: list[RuleBatchItemError] = []
            for index, item in enumerate(input_items):
                serialized_input = serialize_for_rule_evaluation(item.model_dump())
                evaluation_response = evaluate_rule(
                    active_config.data.jdm, serialized_input
                )
                if isinstance(evaluation_response, EvaluateResponse):
                    result_model = return_type.model_validate(
                        evaluation_response.result
                    )
                    results.append(cast(U, result_model))
                    continue

                logger.warning(
                    "rule batch evaluation error",
                    rule_name=func.__name__,
                    index=index,
                    message=evaluation_response.message,
                )
                failures.append(
                    RuleBatchItemError(
                        index=index,
                        input_item=item,
                        error=evaluation_response,
                    )
                )

            if failures:
                raise RuleBatchEvaluationError(failures)

            return results

        @step(step_type=StepType.RULE)
        @wraps(func)
        async def wrapper(input: T) -> U:
            logger.debug(
                "executing rule", rule_name=func.__name__, input_type=type(input)
            )

            active_config = await _get_active_config()

            set_step_metadata(
                RuleConfigMeta(
                    config_id=active_config.id,
                    config_version=active_config.version,
                )
            )

            if active_config.version == 0:
                logger.debug(
                    "using default python implementation for rule",
                    rule_name=func.__name__,
                )
                # default implementation
                return func(input)
            else:
                logger.debug(
                    "using jdm override for rule",
                    version=active_config.version,
                    rule_name=func.__name__,
                )
                serialized_input = serialize_for_rule_evaluation(input.model_dump())
                evaluation_response = evaluate_rule(
                    active_config.data.jdm, serialized_input
                )
                if isinstance(evaluation_response, EvaluateResponse):
                    result_model = return_type.model_validate(
                        evaluation_response.result
                    )
                    return cast(U, result_model)
                else:
                    logger.warning(
                        "rule evaluation error",
                        rule_name=func.__name__,
                        message=evaluation_response.message,
                    )
                    raise Exception(evaluation_response.message)

        async def _batch_impl(input_items: list[T]) -> list[U]:
            batch_size = len(input_items)
            logger.debug(
                "executing rule batch",
                rule_name=func.__name__,
                batch_size=batch_size,
            )

            active_config = await _get_active_config()

            set_step_metadata(
                RuleConfigMeta(
                    config_id=active_config.id,
                    config_version=active_config.version,
                )
            )

            if not input_items:
                return []

            if active_config.version == 0:
                return _execute_default_batch(input_items)

            return _execute_jdm_batch(active_config, input_items)

        _batch_impl.__name__ = f"{func.__name__}_batch"
        batch_wrapper = step(
            step_type=StepType.RULE,
            return_type=list[return_type],
        )(_batch_impl)

        wrapper.__rule__ = rule  # type: ignore

        step_wrapper = wrapper
        step_wrapper.batch = batch_wrapper  # type: ignore[attr-defined]

        return step_wrapper

    return decorator
