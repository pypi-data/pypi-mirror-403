"""Prebuilt factories for composing configured agent models."""

import os
from typing import TYPE_CHECKING, Any

from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from planar.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from planar.config import PlanarConfig


logger = get_logger(__name__)

DEFAULT_ENDPOINT_ENV = "AZURE_OPENAI_ENDPOINT"
DEFAULT_DEPLOYMENT_ENV = "AZURE_OPENAI_DEPLOYMENT"
DEFAULT_AZURE_API_KEY_ENV = "AZURE_OPENAI_API_KEY"
DEFAULT_AZURE_SCOPE = "https://cognitiveservices.azure.com/.default"

DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

__all__ = [
    "azure_openai_responses_model_factory",
    "openai_responses_model_factory",
]


async def azure_openai_responses_model_factory(
    options: dict[str, Any] | None = None, *, config: "PlanarConfig | None" = None
) -> OpenAIResponsesModel:
    """
    Construct an `OpenAIResponsesModel` backed by an Azure OpenAI deployment.

    If no API key is supplied the factory falls back to `DefaultAzureCredential`
    and fetches AAD tokens for the Azure OpenAI scope.

    Args:
        options: Factory options supplied from PlanarConfig. Supported keys:
            - endpoint / endpoint_env: Endpoint URL string or environment variable name.
            - deployment / deployment_env: Deployment name or env variable.
            - api_key / api_key_env / static_api_key: Static API key or env variable name.
            - token_scope / token_scope_env: Override the Azure AD scope used with DefaultAzureCredential.
            - managed_identity_client_id / managed_identity_client_id_env: Client ID for User Assigned Identity.
        config: Active PlanarConfig (unused but accepted for parity with custom factories).

    Returns:
        Configured OpenAIResponsesModel instance.

    Raises:
        ValueError: if endpoint or deployment cannot be resolved, or if Azure AD auth is
            requested but azure-identity is unavailable.
    """

    del config  # present for API compatibility
    opts = options or {}

    endpoint = opts.get("endpoint") or _read_env(
        opts.get("endpoint_env", DEFAULT_ENDPOINT_ENV)
    )
    if not endpoint:
        raise ValueError(
            "Azure OpenAI endpoint is not configured. "
            "Provide 'endpoint' or set the environment variable defined by 'endpoint_env'."
        )

    deployment = opts.get("deployment") or _read_env(
        opts.get("deployment_env", DEFAULT_DEPLOYMENT_ENV)
    )
    if not deployment:
        raise ValueError(
            "Azure OpenAI deployment is not configured. "
            "Provide 'deployment' or set the environment variable defined by 'deployment_env'."
        )

    api_key = opts.get("api_key") or _read_env(
        opts.get("api_key_env")
        or opts.get("static_api_key")
        or DEFAULT_AZURE_API_KEY_ENV
    )

    token_scope = DEFAULT_AZURE_SCOPE
    if "token_scope" in opts:
        token_scope = opts["token_scope"]
    elif "token_scope_env" in opts:
        token_scope = _read_env(opts["token_scope_env"]) or DEFAULT_AZURE_SCOPE

    base_url = endpoint.rstrip("/") + "/openai/v1/"
    client_kwargs: dict[str, Any] = {"base_url": base_url}

    if api_key:
        auth_method = "api_key"
        client_kwargs["api_key"] = api_key
    else:
        auth_method = "azure_ad"
        managed_identity_client_id = opts.get(
            "managed_identity_client_id"
        ) or _read_env(opts.get("managed_identity_client_id_env"))
        credential = _create_default_credential(managed_identity_client_id)

        async def token_provider_async() -> str:
            token = await credential.get_token(token_scope)
            return token.token

        client_kwargs["api_key"] = token_provider_async

    logger.debug(
        "building azure openai responses model",
        deployment=deployment,
        endpoint=endpoint,
        auth_method=auth_method,
    )

    client = AsyncOpenAI(**client_kwargs)
    provider = OpenAIProvider(openai_client=client)
    return OpenAIResponsesModel(deployment, provider=provider)


async def openai_responses_model_factory(
    options: dict[str, Any] | None = None, *, config: "PlanarConfig | None" = None
) -> OpenAIResponsesModel:
    """
    Construct an OpenAI Responses API model using OpenAI's public cloud.

    Args:
        options: Factory settings. Supported keys:
            - model / model_env: model identifier (defaults to gpt-4o).
            - api_key / api_key_env: overrides for authentication (defaults to OPENAI_API_KEY).
            - base_url / base_url_env: optional custom base URL (for proxies).
            - organization / organization_env: optional organization id.
        config: Active PlanarConfig (unused but accepted to align with factory signature).

    Returns:
        Configured OpenAIResponsesModel.

    Raises:
        ValueError: if the API key cannot be resolved.
    """

    del config
    opts = options or {}
    model_name = (
        opts.get("model") or _read_env(opts.get("model_env")) or DEFAULT_OPENAI_MODEL
    )
    api_key = opts.get("api_key") or _read_env(
        opts.get("api_key_env", DEFAULT_OPENAI_API_KEY_ENV)
    )
    if not api_key:
        raise ValueError(
            "OpenAI API key is not configured. Provide 'api_key' or set 'api_key_env'."
        )

    base_url = opts.get("base_url") or _read_env(opts.get("base_url_env"))
    organization = opts.get("organization") or _read_env(opts.get("organization_env"))

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    if organization:
        client_kwargs["organization"] = organization

    logger.debug(
        "building openai responses model",
        model_name=model_name,
        has_custom_base_url=bool(base_url),
    )

    client = AsyncOpenAI(**client_kwargs)
    provider = OpenAIProvider(openai_client=client)
    return OpenAIResponsesModel(model_name, provider=provider)


def _read_env(env_name: str | None) -> str | None:
    if not env_name:
        return None
    return os.environ.get(env_name)


def _create_default_credential(managed_identity_client_id: str | None = None):
    try:
        from azure.identity.aio import DefaultAzureCredential
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ValueError(
            "azure-identity is required for Azure AD authentication. "
            "Install the 'planar[azure]' extra or provide an API key via "
            "'api_key'/'api_key_env'."
        ) from exc

    credential_kwargs = {}
    if managed_identity_client_id:
        credential_kwargs["managed_identity_client_id"] = managed_identity_client_id

    credential = DefaultAzureCredential(**credential_kwargs)
    return credential
