import inspect
from dataclasses import dataclass
from typing import Any, Type, cast
from uuid import UUID

from pydantic import BaseModel
from pydantic_ai import models
from pydantic_ai.settings import ModelSettings

from planar.ai.agent_base import AgentBase
from planar.ai.agent_utils import (
    ModelSpec,
    create_tool_definition,
    extract_files_from_model,
    get_agent_config,
    render_template,
)
from planar.ai.model_registry import DEFAULT_MODEL_NAME, ConfiguredModelKey
from planar.ai.models import (
    AgentEventEmitter,
    AgentEventType,
    AgentRunResult,
    AssistantMessage,
    ModelMessage,
    SystemMessage,
    ToolCallResult,
    ToolDefinition,
    ToolMessage,
    ToolResponse,
    UserMessage,
)
from planar.ai.pydantic_ai import ModelRunResponse, model_run
from planar.logging import get_logger
from planar.session import get_config
from planar.utils import utc_now
from planar.workflows.models import StepType
from planar.workflows.notifications import agent_text, agent_think
from planar.workflows.step_meta import AgentConfigMeta, set_step_metadata

logger = get_logger(__name__)


class AgentWorkflowNotifier(AgentEventEmitter):
    def emit(self, event_type, data):
        match event_type:
            case AgentEventType.THINK:
                agent_think(str(data))
            case AgentEventType.TEXT:
                agent_text(str(data))
            case _:
                ...


@dataclass
class Agent[
    TInput: BaseModel | str,
    TOutput: BaseModel | str,
    TToolContext,
](AgentBase[TInput, TOutput, TToolContext]):
    model: models.KnownModelName | models.Model | ConfiguredModelKey | None = None

    async def run_step(
        self,
        input_value: TInput,
        config_id: UUID | None = None,
    ) -> AgentRunResult[TOutput]:
        """Execute the agent with the provided inputs.

        Args:
            input_value: The primary input value to the agent, can be a string or Pydantic model
            config_id: Optional configuration identifier to execute with

        Returns:
            AgentRunResult containing the agent's response
        """
        if self.event_emitter:
            event_emitter = self.event_emitter
        else:
            event_emitter = AgentWorkflowNotifier()
        logger.debug(
            "agent run_step called", agent_name=self.name, input_type=type(input_value)
        )
        result = None

        config_record = await get_agent_config(
            self.name,
            self.to_config(),
            config_id=config_id,
        )
        config = config_record.data
        logger.debug(
            "agent using config",
            agent_name=self.name,
            config_version=config_record.version,
            config_id=str(config_record.id),
        )

        input_map: dict[str, str | dict[str, Any]] = {}

        files = extract_files_from_model(input_value)
        logger.debug(
            "extracted files from input for agent",
            num_files=len(files),
            agent_name=self.name,
        )
        match input_value:
            case BaseModel():
                if self.input_type and not isinstance(input_value, self.input_type):
                    logger.warning(
                        "input value type mismatch for agent",
                        agent_name=self.name,
                        expected_type=self.input_type,
                        got_type=type(input_value),
                    )
                    raise ValueError(
                        f"Input value must be of type {self.input_type}, but got {type(input_value)}"
                    )
                input_map["input"] = cast(BaseModel, input_value).model_dump()
            case str():
                input_map["input"] = input_value
            case _:
                logger.warning(
                    "unexpected input value type for agent",
                    agent_name=self.name,
                    type=type(input_value),
                    expected_type=self.input_type,
                )
                raise ValueError(
                    f"Unexpected input value type for agent: {type(input_value)}, expected: {self.input_type or str}"
                )

        # Add built-in variables
        # TODO: Make deterministic or step
        built_in_vars = {
            "datetime_now": utc_now().isoformat(),
            "date_today": utc_now().date().isoformat(),
        }
        input_map.update(built_in_vars)

        # Format the prompts with the provided arguments using Jinja templates
        try:
            formatted_system_prompt = (
                render_template(config.system_prompt, input_map)
                if config.system_prompt
                else ""
            )
            formatted_user_prompt = (
                render_template(config.user_prompt, input_map)
                if config.user_prompt
                else ""
            )
        except ValueError as e:
            logger.exception("error formatting prompts for agent", agent_name=self.name)
            raise ValueError(f"Missing required parameter for prompt formatting: {e}")

        model = await self._resolve_model_instance()

        # Apply model parameters if specified
        model_settings = None
        if config.model_parameters:
            model_settings = config.model_parameters

        # Prepare structured messages
        messages: list[ModelMessage] = []
        if formatted_system_prompt:
            messages.append(SystemMessage(content=formatted_system_prompt))

        if formatted_user_prompt:
            messages.append(UserMessage(content=formatted_user_prompt, files=files))

        # Prepare tools if provided
        tool_definitions = None
        if self.tools:
            tool_definitions = [create_tool_definition(tool) for tool in self.tools]

        # Determine output type for the agent call
        # Pass the Pydantic model type if output_type is a subclass of BaseModel,
        # otherwise pass None (indicating string output is expected).
        output_type: Type[BaseModel] | None = None
        # Use issubclass safely by checking if output_type is a type first
        if inspect.isclass(self.output_type) and issubclass(
            self.output_type, BaseModel
        ):
            output_type = cast(Type[BaseModel], self.output_type)

        # Execute the LLM call
        max_turns = config.max_turns

        # We use this inner function to pass "model" and "event_emitter",
        # which are not serializable as step parameters.
        async def agent_run_step(
            model_spec: ModelSpec,
            messages: list[ModelMessage],
            turns_left: int,
            tools: list[ToolDefinition] | None = None,
            output_type: Type[BaseModel] | None = None,
        ):
            logger.debug(
                "agent running",
                agent_name=self.name,
                model=model_spec,
                model_settings=model_settings,
                output_type=output_type,
            )
            if output_type is None:
                return await model_run(
                    model=model,
                    max_extra_turns=turns_left,
                    model_settings=model_settings,
                    messages=messages,
                    tools=tools or [],
                    event_handler=cast(Any, event_emitter),
                )
            else:
                return await model_run(
                    model=model,
                    max_extra_turns=turns_left,
                    model_settings=model_settings,
                    messages=messages,
                    output_type=output_type,
                    tools=tools or [],
                    event_handler=cast(Any, event_emitter),
                )

        model_spec = ModelSpec(
            model_id=str(model),
            parameters=cast(ModelSettings, model_settings or {}),
        )
        result = None
        logger.debug(
            "agent performing multi-turn completion with tools",
            agent_name=self.name,
            max_turns=max_turns,
        )
        turns_left = max_turns
        while turns_left > 0:
            turns_left -= 1
            logger.debug("agent turn", agent_name=self.name, turns_left=turns_left)

            # Get model response
            run_response = await self.as_step_if_durable(
                agent_run_step,
                step_type=StepType.AGENT,
                return_type=ModelRunResponse[output_type or str],
            )(
                model_spec=model_spec,
                messages=messages,
                turns_left=turns_left,
                output_type=output_type,
                tools=tool_definitions or [],
            )
            response = run_response.response
            turns_left -= run_response.extra_turns_used

            # Emit response event if event_emitter is provided
            if event_emitter:
                event_emitter.emit(AgentEventType.RESPONSE, response.content)

            # If no tool calls or last turn, return content
            if not response.tool_calls or turns_left == 0:
                logger.debug(
                    "agent completion: no tool calls or last turn",
                    agent_name=self.name,
                    has_content=response.content is not None,
                )
                result = response.content
                break

            # Process tool calls
            logger.debug(
                "agent received tool calls",
                agent_name=self.name,
                num_tool_calls=len(response.tool_calls),
            )
            assistant_message = AssistantMessage(
                content=None,
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_message)

            # Execute each tool and add tool responses to messages
            for tool_call_idx, tool_call in enumerate(response.tool_calls):
                logger.debug(
                    "agent processing tool call",
                    agent_name=self.name,
                    tool_call_index=tool_call_idx + 1,
                    tool_call_id=tool_call.id,
                    tool_call_name=tool_call.name,
                )
                # Find the matching tool function
                tool_fn = next(
                    (t for t in self.tools if t.__name__ == tool_call.name),
                    None,
                )

                if not tool_fn:
                    tool_result = f"Error: Tool '{tool_call.name}' not found."
                    logger.warning(
                        "tool not found for agent",
                        tool_name=tool_call.name,
                        agent_name=self.name,
                    )
                else:
                    # Execute the tool with the provided arguments
                    tool_result = await self.as_step_if_durable(
                        tool_fn,
                        step_type=StepType.TOOL_CALL,
                        display_name=tool_call.name,
                    )(**tool_call.arguments)
                    logger.info(
                        "tool executed by agent",
                        tool_name=tool_call.name,
                        agent_name=self.name,
                        result_type=type(tool_result),
                    )

                # Create a tool response
                tool_response = ToolResponse(
                    tool_call_id=tool_call.id or "call_1", content=str(tool_result)
                )

                # Emit tool response event if event_emitter is provided
                if event_emitter:
                    event_emitter.emit(
                        AgentEventType.TOOL_RESPONSE,
                        ToolCallResult(
                            tool_call_id=tool_call.id or "call_1",
                            tool_call_name=tool_call.name,
                            content=tool_result,
                        ),
                    )

                tool_message = ToolMessage(
                    content=tool_response.content,
                    tool_call_id=tool_response.tool_call_id or "call_1",
                )
                messages.append(tool_message)

            # Continue to next turn

        if result is None:
            logger.warning(
                "agent completed tool interactions but result is none",
                agent_name=self.name,
                expected_type=self.output_type,
            )
            raise ValueError(
                f"Expected result of type {self.output_type} but got none after tool interactions."
            )

        if event_emitter:
            event_emitter.emit(AgentEventType.COMPLETED, result)

        set_step_metadata(
            AgentConfigMeta(
                config_id=config_record.id, config_version=config_record.version
            )
        )
        logger.info(
            "agent completed",
            agent_name=self.name,
            final_result_type=type(result),
        )
        return AgentRunResult[TOutput](output=cast(TOutput, result))

    def get_model_str(self) -> str:
        """Return a string identifier without forcing model resolution."""

        value = self.model
        match value:
            case models.Model():
                return self._format_model_identifier(value)
            case ConfiguredModelKey() as key:
                return key.name
            case str():
                return value
            case None:
                try:
                    config = get_config()
                except LookupError:
                    return DEFAULT_MODEL_NAME

                ai_models_config = config.ai_models
                if ai_models_config:
                    if ai_models_config.default:
                        return ai_models_config.default
                    if ai_models_config.models:
                        for key in ai_models_config.models.keys():
                            return key

                return DEFAULT_MODEL_NAME
            case _:
                return str(value)

    async def _resolve_model_instance(self) -> models.Model:
        match self.model:
            case models.Model() as configured_model:
                return configured_model
            case ConfiguredModelKey() as key:
                config = self._require_config()
                return await config.get_model_registry().resolve(key)
            case str() as model_name:
                return models.infer_model(model_name)
            case None:
                config = self._require_config()
                return await config.get_model_registry().resolve(None)
            case other:
                return models.infer_model(str(other))

    @staticmethod
    def _require_config():
        try:
            return get_config()
        except LookupError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(
                "Planar config is not available. Ensure agent execution happens within a PlanarApp context."
            ) from exc

    @staticmethod
    def _format_model_identifier(model: models.Model) -> str:
        model_name = getattr(model, "model_name", None)
        provider_name = getattr(model, "provider_name", None)
        if provider_name is None:
            provider = getattr(model, "_provider", None)
            provider_name = getattr(provider, "name", None)
        if provider_name is None:
            provider_name = getattr(model, "system", None)
        if model_name and provider_name:
            return f"{provider_name}:{model_name}"
        if model_name:
            return str(model_name)
        return str(model)
