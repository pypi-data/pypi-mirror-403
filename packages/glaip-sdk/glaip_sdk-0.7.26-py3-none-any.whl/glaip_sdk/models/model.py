"""Model configuration class for GL AIP SDK.

Provides a structured way to specify models, credentials, and hyperparameters
for local execution.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class Model(BaseModel):
    """Model configuration class for local execution.

    Bundles model identity with credentials and hyperparameters.
    """

    id: str
    credentials: dict[str, Any] | str | None = None
    hyperparameters: dict[str, Any] | None = None
    base_url: str | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate model ID format.

        Args:
            v: Model identifier string.

        Returns:
            Validated model identifier in 'provider/model' format.

        Raises:
            ValueError: If model format is invalid.
        """
        from glaip_sdk.models._validation import _validate_model  # noqa: PLC0415

        return _validate_model(v)

    def to_aip_agents_format(self) -> tuple[str, dict[str, Any]]:
        """Convert Model to aip_agents format.

        Converts provider/model format to driver/model format for aip_agents.
        For custom models with base_url, uses format: openai-compatible/base_url:model_name

        Returns:
            Tuple of (model_string, agent_config_dict).
        """
        if "/" not in self.id:
            return self.id, {}

        parts = self.id.split("/", 1)
        provider = parts[0]
        model_name = parts[1]

        config = self._build_agent_config(provider)
        model_string = self._build_model_string(provider, model_name, config)

        return model_string, config

    def _build_agent_config(self, provider: str) -> dict[str, Any]:
        """Build agent config dict from Model attributes.

        Args:
            provider: Provider name extracted from model id.

        Returns:
            Configuration dict with credentials, hyperparameters, and base_url.
        """
        config: dict[str, Any] = {}

        if self.credentials:
            if isinstance(self.credentials, str):
                config["lm_api_key"] = self.credentials
            elif isinstance(self.credentials, dict):
                config["lm_credentials"] = self.credentials

        if self.hyperparameters:
            config["lm_hyperparameters"] = self.hyperparameters

        base_url = self._resolve_base_url(provider)
        if base_url:
            config["lm_base_url"] = base_url

        return config

    def _resolve_base_url(self, provider: str) -> str | None:
        """Resolve base URL for the provider.

        Uses centralized provider configurations to determine base_url.
        Users can override by explicitly setting base_url attribute.

        Args:
            provider: Provider name from model ID (e.g., "deepinfra").

        Returns:
            Base URL string or None.

        Examples:
            >>> model = Model(id="deepinfra/Qwen/Qwen3-30B")
            >>> model._resolve_base_url("deepinfra")
            "https://api.deepinfra.com/v1/openai"
        """
        if self.base_url:
            return self.base_url

        # Get base_url from provider config
        from glaip_sdk.models._provider_mappings import get_base_url  # noqa: PLC0415

        base_url = get_base_url(provider)
        if base_url:
            return base_url

        return None

    def _build_model_string(self, provider: str, model_name: str, config: dict[str, Any]) -> str:
        """Build normalized model string for aip_agents.

        Converts provider names to their driver implementations for local execution.

        Conversion strategy:
        1. Custom models with base_url: Use colon format (openai-compatible/{base_url}:{model_name})
           This allows aip_agents to parse base_url and model_name separately.
        2. Standard providers: Map to driver and use slash format (driver/{model_name})
           aip_agents will handle provider/model format internally.

        Args:
            provider: Provider name from model ID (e.g., "deepinfra", "openai").
            model_name: Model name after provider prefix.
            config: Agent config dict (may contain base_url).

        Returns:
            Normalized model string in provider/model format with driver name.

        Examples:
            >>> _build_model_string("deepinfra", "Qwen/Qwen3-30B", {})
            "openai-compatible/Qwen/Qwen3-30B"
            >>> _build_model_string("openai", "gpt-4o", {})
            "openai/gpt-4o"
        """
        from glaip_sdk.models._provider_mappings import get_driver  # noqa: PLC0415

        # Map provider to driver (e.g., deepinfra → openai-compatible)
        driver = get_driver(provider)

        if provider == "custom":
            base_url = config.get("lm_base_url")
            if base_url:
                return f"{driver}/{base_url}:{model_name}"

        # Standard case: driver with slash format
        # aip_agents will handle provider/model format internally
        return f"{driver}/{model_name}"

    def __repr__(self) -> str:
        """Return string representation of Model.

        Note: Credentials are masked to avoid leaking secrets in logs.
        Hyperparameters and base_url are shown if present.
        """
        creds_repr = "***" if self.credentials else "None"
        return (
            f"Model(id={self.id!r}, "
            f"credentials={creds_repr}, "
            f"hyperparameters={self.hyperparameters!r}, "
            f"base_url={self.base_url!r})"
        )
