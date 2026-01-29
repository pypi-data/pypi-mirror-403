"""Helpers for resolving configured agent models at runtime."""

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from pydantic_ai import models

from planar.ai.factories import (
    azure_openai_responses_model_factory,
    openai_responses_model_factory,
)
from planar.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - circular import guard
    from planar.config import PlanarConfig


logger = get_logger(__name__)


DEFAULT_MODEL_NAME = "openai:gpt-4o"
OPENAI_RESPONSES_FACTORY_KEY = "openai_responses"
AZURE_OPENAI_RESPONSES_FACTORY_KEY = "azure_openai_responses"


@dataclass(frozen=True)
class ConfiguredModelKey:
    """Reference to a named configured model."""

    name: str


class ModelProviderConfig(BaseModel):
    """Configuration for a shared provider instance."""

    factory: str
    options: dict[str, Any] = Field(default_factory=dict)


class ModelDefinition(BaseModel):
    """Provider-based model configuration."""

    provider: str
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def coerce_options(cls, values: dict[str, Any]) -> dict[str, Any]:
        options = values.get("options")
        if options is None:
            options = {}
        if isinstance(options, str):
            options = {"model": options}
        elif not isinstance(options, dict):
            raise ValueError(
                "ai_models.models options must be a mapping or string value."
            )
        values["options"] = options
        return values

    @model_validator(mode="after")
    def merge_into_options(self) -> "ModelDefinition":
        merged = dict(self.__pydantic_extra__ or {})
        merged.update(self.options)
        self.options = merged
        return self


class ModelEntrySpec(RootModel[str | ModelDefinition]):
    """Wrapper allowing either a provider-based model or a direct identifier."""

    root: str | ModelDefinition


class AIModelsConfig(BaseModel):
    """Top-level configuration for model registry models."""

    default: str | None = None
    providers: dict[str, ModelProviderConfig] = Field(default_factory=dict)
    models: dict[str, ModelEntrySpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def default_refers_to_entry(self) -> "AIModelsConfig":
        if self.default and self.default not in self.models:
            raise ValueError("ai_models.default must reference a declared model.")
        return self

    def first_entry(self) -> ModelEntrySpec | None:
        for value in self.models.values():
            return value
        return None

    def default_entry(self) -> ModelEntrySpec | None:
        if self.default and self.default in self.models:
            return self.models[self.default]
        return self.first_entry()

    def resolve_model_spec(self, key: str) -> ModelEntrySpec:
        try:
            return self.models[key]
        except KeyError:
            raise ValueError(
                f"Configured model '{key}' not found. Check ai_models.models."
            )


class ModelRegistry:
    """Resolves configured models defined in PlanarConfig.ai_models."""

    def __init__(self, config: "PlanarConfig"):
        self._config = config
        self._cache: dict[str, models.Model] = {}
        self._default_model: models.Model | None = None
        self._factories: dict[str, Callable[..., Any]] = {}
        self._register_builtin_factories()

    async def resolve(self, key: ConfiguredModelKey | None) -> models.Model:
        """Return a resolved model for the provided key or default configuration."""

        if key:
            logger.debug("resolving configured model", model_key=key.name)
            return await self._resolve_named_model(key.name)

        logger.debug("resolving default configured model")
        return await self._resolve_default_model()

    async def _resolve_named_model(self, key: str) -> models.Model:
        if key in self._cache:
            return self._cache[key]

        spec = self._get_named_spec(key)
        model = await self._instantiate_spec(spec, key)
        self._cache[key] = model
        return model

    async def _resolve_default_model(self) -> models.Model:
        if self._default_model:
            return self._default_model

        spec = None
        ai_models_config = self._config.ai_models
        if ai_models_config:
            spec = ai_models_config.default_entry()

        model = await self._instantiate_spec(spec, "default")
        self._default_model = model
        return model

    def _get_named_spec(self, key: str) -> ModelEntrySpec:
        ai_models_config = self._config.ai_models
        if not ai_models_config:
            logger.warning("requested configured model key missing", model_key=key)
            raise ValueError(
                f"Configured model '{key}' not found. Check your "
                "PlanarConfig.ai_models models."
            )
        return ai_models_config.resolve_model_spec(key)

    async def _instantiate_spec(
        self, spec: ModelEntrySpec | None, label: str
    ) -> models.Model:
        if not spec:
            logger.debug(
                "no configured model spec provided, falling back to default",
                fallback_model=DEFAULT_MODEL_NAME,
            )
            return models.infer_model(DEFAULT_MODEL_NAME)

        value = spec.root
        if isinstance(value, str):
            return models.infer_model(value)

        if isinstance(value, ModelDefinition):
            return await self._instantiate_model_definition(value, label)

        raise ValueError(
            f"Invalid model configuration for '{label}'. Expected string or ModelDefinition."
        )

    async def _instantiate_model_definition(
        self, model_def: ModelDefinition, label: str
    ) -> models.Model:
        ai_models_config = self._config.ai_models
        if not ai_models_config or model_def.provider not in ai_models_config.providers:
            logger.warning(
                "requested model provider missing",
                provider=model_def.provider,
                model_label=label,
            )
            raise ValueError(
                f"Provider '{model_def.provider}' not found. "
                "Check ai_models.providers configuration."
            )

        provider = ai_models_config.providers[model_def.provider]
        merged_options = {**provider.options, **model_def.options}
        return await self._call_factory_by_name(provider.factory, merged_options, label)

    def _build_factory_kwargs(
        self, factory: Callable[..., Any], options: dict[str, Any]
    ) -> dict[str, Any]:
        sig = inspect.signature(factory)
        kwargs: dict[str, Any] = {}

        accepts_var_kwargs = any(
            param.kind == inspect.Parameter.VAR_KEYWORD
            for param in sig.parameters.values()
        )

        if "options" in sig.parameters or accepts_var_kwargs:
            kwargs["options"] = options
        if "config" in sig.parameters or accepts_var_kwargs:
            kwargs["config"] = self._config
        return kwargs

    def _register_builtin_factories(self) -> None:
        self.register_factory(
            OPENAI_RESPONSES_FACTORY_KEY, openai_responses_model_factory
        )
        self.register_factory(
            AZURE_OPENAI_RESPONSES_FACTORY_KEY, azure_openai_responses_model_factory
        )
        # Backwards-compatible aliases for configs that still point to dotted paths
        self.register_factory(
            "planar.ai.factories.openai_responses_model_factory",
            openai_responses_model_factory,
        )
        self.register_factory(
            "planar.ai.factories.azure_openai_responses_model_factory",
            azure_openai_responses_model_factory,
        )

    def register_factory(self, name: str, factory: Callable[..., Any]) -> None:
        if not name:
            raise ValueError("Factory name must be a non-empty string.")
        existing = self._factories.get(name)
        if existing and existing is not factory:
            logger.warning(
                "overriding configured model factory",
                factory_key=name,
                previous=self._factory_name(existing),
                new=self._factory_name(factory),
            )
        self._factories[name] = factory

    def _get_factory(self, name: str) -> Callable[..., Any]:
        factory = self._factories.get(name)
        if factory:
            return factory
        logger.warning("unregistered model factory requested", factory_key=name)
        raise ValueError(
            f"Factory '{name}' is not registered. Call PlanarApp.register_model_factory "
            "before resolving configured models."
        )

    async def _call_factory_by_name(
        self, factory_key: str, options: dict[str, Any], label: str
    ) -> models.Model:
        factory = self._get_factory(factory_key)
        logger.debug(
            "invoking configured model factory",
            factory=factory_key,
            model_label=label,
        )
        kwargs = self._build_factory_kwargs(factory, options)
        result = factory(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        if not isinstance(result, models.Model):
            raise TypeError(
                f"Configured model factory '{factory_key}' must return a "
                "pydantic_ai.models.Model instance."
            )
        return result

    @staticmethod
    def _factory_name(factory: Callable[..., Any]) -> str:
        if hasattr(factory, "__name__"):
            return factory.__name__  # type: ignore[attr-defined]
        return factory.__class__.__name__
