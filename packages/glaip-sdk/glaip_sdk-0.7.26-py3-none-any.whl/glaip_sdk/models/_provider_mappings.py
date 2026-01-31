"""Provider configuration for model name standardization.

This module centralizes provider configurations, including how provider names
map to server implementations and their base URLs for local execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

__all__ = ["PROVIDERS", "ProviderConfig", "get_driver", "get_base_url"]


class ProviderConfig:
    """Configuration for a model provider.

    Defines how a provider is referenced in SDK constants and how it maps to
    the underlying driver implementation and API endpoints.
    """

    def __init__(
        self,
        name: str,
        driver: str,
        base_url: str | None = None,
    ):
        """Initialize provider configuration.

        Args:
            name: User-facing provider name used in SDK constants (e.g., "deepinfra").
            driver: Driver implementation name in language_models.yaml (e.g., "openai-compatible").
            base_url: Base URL for the provider's API (required for local execution).
        """
        self.name = name
        self.driver = driver
        self.base_url = base_url


# Centralized provider configurations
# Key: provider name (used in SDK constants)
# Value: ProviderConfig with driver mapping and base URL
PROVIDERS: dict[str, ProviderConfig] = {
    "deepinfra": ProviderConfig(
        name="deepinfra",
        driver="openai-compatible",
        base_url="https://api.deepinfra.com/v1/openai",
    ),
    "deepseek": ProviderConfig(
        name="deepseek",
        driver="openai-compatible",
        base_url="https://api.deepseek.com",
    ),
    "custom": ProviderConfig(
        name="custom",
        driver="openai-compatible",
        base_url=None,  # User-provided via Model.base_url
    ),
}


def get_driver(provider: str) -> str:
    """Get driver name for a given provider.

    Maps SDK provider names to their underlying driver implementations.
    For providers not in the config, returns the provider name unchanged
    (assumes provider name matches driver name).

    Args:
        provider: Provider name from SDK constants (e.g., "deepinfra", "openai").

    Returns:
        Driver name (e.g., "openai-compatible" for deepinfra, "openai" for openai).

    Examples:
        >>> get_driver("deepinfra")
        "openai-compatible"
        >>> get_driver("openai")
        "openai"
    """
    config = PROVIDERS.get(provider)
    return config.driver if config else provider


def get_base_url(provider: str) -> str | None:
    """Get default base URL for a provider.

    Returns the configured base URL for local execution, if available.

    Args:
        provider: Provider name from SDK constants (e.g., "deepinfra").

    Returns:
        Base URL string, or None if no config exists or no base_url configured.

    Examples:
        >>> get_base_url("deepinfra")
        "https://api.deepinfra.com/v1/openai"
        >>> get_base_url("openai")
        None
    """
    config = PROVIDERS.get(provider)
    return config.base_url if config else None
