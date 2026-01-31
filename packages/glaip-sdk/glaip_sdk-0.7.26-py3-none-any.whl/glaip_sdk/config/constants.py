"""Configuration constants for the AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

# Lazy import cache for DEFAULT_MODEL to avoid circular dependency
_DEFAULT_MODEL: str | None = None


def __getattr__(name: str) -> str:
    """Lazy import DEFAULT_MODEL from models.constants to avoid circular dependency.

    Note: Prefer importing DEFAULT_MODEL directly from glaip_sdk.models.constants
    as it is the canonical source. This re-export exists for backward compatibility.
    """
    if name in ("DEFAULT_MODEL", "SDK_DEFAULT_MODEL"):
        global _DEFAULT_MODEL
        if _DEFAULT_MODEL is None:
            from glaip_sdk.models.constants import (  # noqa: PLC0415
                DEFAULT_MODEL as _MODEL,
            )

            _DEFAULT_MODEL = _MODEL
        return _DEFAULT_MODEL
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


DEFAULT_AGENT_RUN_TIMEOUT = 300

# User agent and version
SDK_NAME = "glaip-sdk"

# Reserved names that cannot be used for agents/tools
RESERVED_NAMES = {
    "system",
    "admin",
    "root",
    "test",
    "example",
    "demo",
    "sample",
}

# Agent creation/update constants
DEFAULT_AGENT_TYPE = "config"
DEFAULT_AGENT_FRAMEWORK = "langchain"
DEFAULT_AGENT_VERSION = "1.0"
DEFAULT_AGENT_PROVIDER = "openai"

# Tool creation/update constants
DEFAULT_TOOL_TYPE = "custom"
DEFAULT_TOOL_FRAMEWORK = "langchain"
DEFAULT_TOOL_VERSION = "1.0"

# MCP creation/update constants
DEFAULT_MCP_TYPE = "server"
DEFAULT_MCP_TRANSPORT = "stdio"

# Default error messages
DEFAULT_ERROR_MESSAGE = "Unknown error"

# Agent configuration fields used for CLI args and payload building
AGENT_CONFIG_FIELDS = (
    "name",
    "instruction",
    "model",
    "tools",
    "agents",
    "mcps",
    "timeout",
)
