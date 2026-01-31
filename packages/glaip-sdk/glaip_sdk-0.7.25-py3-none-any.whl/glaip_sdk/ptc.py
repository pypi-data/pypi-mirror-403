"""Programmatic Tool Calling (PTC) configuration for local SDK runs.

This module provides the PTC class for configuring sandboxed code execution
in local agent runs. PTC enables agents to call execute_ptc_code and use MCP
tools programmatically in an E2B sandbox.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import Any

from glaip_sdk.exceptions import ValidationError


class PTC:
    """Configuration for Programmatic Tool Calling in local runs.

    PTC allows agents to execute Python code in a sandboxed E2B environment
    with access to registered MCP tools. This is only supported for local
    runs (local=True) and requires the glaip-sdk[local] installation.

    Example:
        >>> from glaip_sdk.ptc import PTC
        >>> from glaip_sdk.agents import Agent
        >>>
        >>> ptc = PTC(enabled=True)
        >>> agent = Agent(
        ...     name="ptc_demo",
        ...     instruction="Use execute_ptc_code for multi-tool workflows.",
        ...     mcps=[my_mcp],
        ...     ptc=ptc,
        ... )
        >>> agent.run("Analyze the repo", local=True)

    Custom timeouts and prompts:
        >>> ptc = PTC(
        ...     enabled=True,
        ...     sandbox_timeout=180.0,
        ...     prompt={"mode": "full", "include_example": False},
        ... )

    Args:
        enabled: Whether PTC is enabled. Must be True to activate PTC.
            When False, all other fields are ignored (toggle-friendly).
        sandbox_timeout: Maximum execution time in seconds for sandbox code.
            Defaults to 120.0 seconds.
        prompt: Prompt configuration for PTC tool description.
            Can be a dict with "mode" and "include_example" keys.
            Defaults to None (uses aip-agents default).
        custom_tools: NOT SUPPORTED in v1. Raises ValidationError if provided
            when enabled=True.
        ptc_packages: NOT SUPPORTED in v1. Raises ValidationError if provided
            when enabled=True.

    Raises:
        ValidationError: If custom_tools or ptc_packages are provided when
            enabled=True (v1 only supports MCP tools).
    """

    def __init__(
        self,
        *,
        enabled: bool = False,
        sandbox_timeout: float = 120.0,
        prompt: dict[str, Any] | None = None,
        custom_tools: list[Any] | None = None,
        ptc_packages: list[str] | None = None,
    ):
        """Initialize PTC configuration.

        Args:
            enabled: Whether PTC is enabled. Must be True to activate.
            sandbox_timeout: Sandbox execution timeout in seconds.
            prompt: Prompt configuration dict.
            custom_tools: Custom tools (NOT SUPPORTED in v1).
            ptc_packages: Sandbox packages (NOT SUPPORTED in v1).

        Raises:
            ValidationError: If unsupported features are used when enabled=True.
        """
        self.enabled = enabled
        self.sandbox_timeout = sandbox_timeout
        self.prompt = prompt
        self._custom_tools = custom_tools
        self._ptc_packages = ptc_packages

        if self.enabled:
            self._validate_v1_constraints()

    def _validate_v1_constraints(self) -> None:
        """Validate that v1-unsupported features are not used.

        Raises:
            ValidationError: If custom_tools or ptc_packages are provided.
        """
        if self._custom_tools is not None:
            msg = (
                "PTC custom_tools are not supported in v1. "
                "Only MCP tools are available in the sandbox. "
                "Please remove the custom_tools parameter or wait for "
                "custom tool support in a future release."
            )
            raise ValidationError(msg)

        if self._ptc_packages is not None:
            msg = (
                "PTC ptc_packages are not supported in v1. "
                "The sandbox uses a fixed template to maintain local/remote parity. "
                "Please remove the ptc_packages parameter or wait for "
                "package installation support in a future release."
            )
            raise ValidationError(msg)

    def to_dict(self) -> dict[str, Any]:
        """Convert PTC config to dictionary format.

        Returns:
            Dictionary representation of PTC config.
        """
        result: dict[str, Any] = {
            "enabled": self.enabled,
        }

        if self.enabled:
            result["sandbox_timeout"] = self.sandbox_timeout
            if self.prompt is not None:
                result["prompt"] = self.prompt

        return result

    def __repr__(self) -> str:
        """Return string representation of PTC config."""
        if not self.enabled:
            return "PTC(enabled=False)"

        parts = [f"enabled={self.enabled}"]
        if abs(self.sandbox_timeout - 120.0) > 1e-9:
            parts.append(f"sandbox_timeout={self.sandbox_timeout}")
        if self.prompt is not None:
            parts.append(f"prompt={self.prompt!r}")

        return f"PTC({', '.join(parts)})"
