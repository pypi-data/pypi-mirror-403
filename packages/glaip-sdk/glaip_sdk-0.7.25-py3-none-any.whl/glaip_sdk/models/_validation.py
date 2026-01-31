"""Model validation utility for GL AIP SDK.

Validates model names in 'provider/model' format and provides
helpful error messages for invalid formats.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

import warnings
from typing import Any


def _validate_model(model: str) -> str:
    """Validate model format and deprecate bare names.

    Args:
        model: Model string to validate

    Returns:
        Normalized model string in provider/model format

    Raises:
        ValueError: If model format is invalid
    """
    if "/" not in model:
        warnings.warn(
            f"Bare model name '{model}' is deprecated. "
            f"Use 'provider/model' format (e.g., 'openai/{model}'). "
            f"This will be an error in v2.0. Use constants: from glaip_sdk.models import OpenAI",
            DeprecationWarning,
            stacklevel=2,
        )
        return f"openai/{model}"

    provider, model_name = model.split("/", 1)
    if not provider or not model_name:
        raise ValueError(
            f"Invalid model format: '{model}'. "
            f"Expected 'provider/model' format (e.g., 'openai/gpt-4o-mini'). "
            f"Use constants: from glaip_sdk.models import OpenAI; Agent(model=OpenAI.GPT_4O_MINI)."
        )
    return model


def convert_model_for_local_execution(model: str | Any) -> tuple[str, dict[str, Any]]:
    """Convert model to aip_agents format for local execution.

    Converts provider/model format appropriately for aip_agents.
    Handles both Model objects and string models.

    Args:
        model: Model object or string identifier.

    Returns:
        Tuple of (model_string, config_dict) where:
        - model_string: Model in format expected by aip_agents (provider/model)
        - config_dict: Configuration dict with credentials, hyperparameters, etc.
    """
    from glaip_sdk.models import Model  # noqa: PLC0415

    # Handle Model objects
    if isinstance(model, Model):
        return model.to_aip_agents_format()

    # Handle string models
    if isinstance(model, str):
        if "/" not in model:
            return model, {}

        parts = model.split("/", 1)
        provider = parts[0]
        model_name = parts[1]

        # Map provider to driver and get base_url from config
        from glaip_sdk.models._provider_mappings import (  # noqa: PLC0415
            get_base_url,
            get_driver,
        )

        driver = get_driver(provider)
        base_url = get_base_url(provider)

        config: dict[str, Any] = {}
        if base_url:
            config["lm_base_url"] = base_url

        # Return with driver name
        return f"{driver}/{model_name}", config

    # For other types (None, etc.), return as-is
    return model, {}


__all__ = ["_validate_model", "convert_model_for_local_execution"]
