"""PTC adapter for local runner integration.

This module provides validation and normalization of PTC configuration
for use in the local LangGraph runner. It ensures PTC is configured
correctly and rejects unsupported configuration sources.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glaip_sdk.exceptions import ValidationError

if TYPE_CHECKING:
    from glaip_sdk.ptc import PTC


def validate_ptc_for_local_run(
    agent_ptc: PTC | None,
    agent_config_ptc: Any | None,
    runtime_config_ptc: Any | None,
) -> PTC | None:
    """Validate PTC configuration for local runs.

    Args:
        agent_ptc: PTC object from Agent.ptc parameter.
        agent_config_ptc: PTC from agent_config (should be None for local).
        runtime_config_ptc: PTC from runtime_config (should be None for v1).

    Returns:
        Validated PTC object if enabled, None otherwise.

    Raises:
        ValidationError: If agent_config.ptc or runtime_config.ptc are provided,
            or if agent_ptc is not a PTC instance when provided.
    """
    if agent_config_ptc is not None:
        msg = (
            "PTC configuration via agent_config.ptc is not supported for local runs. "
            "Please configure PTC using the Agent.ptc parameter instead: "
            "Agent(name='...', ptc=PTC(enabled=True), ...)"
        )
        raise ValidationError(msg)

    if runtime_config_ptc is not None:
        msg = (
            "PTC configuration via runtime_config.ptc is not supported in v1. "
            "PTC configuration must be set at Agent initialization time using "
            "the Agent.ptc parameter and cannot be overridden at runtime. "
            "This preserves local/remote parity and prevents ambiguous precedence."
        )
        raise ValidationError(msg)

    if agent_ptc is None:
        return None

    from glaip_sdk.ptc import PTC  # noqa: PLC0415

    if not isinstance(agent_ptc, PTC):
        msg = (
            f"Agent.ptc must be a PTC instance, got {type(agent_ptc).__name__}. "
            "Example: Agent(name='...', ptc=PTC(enabled=True), ...)"
        )
        raise ValidationError(msg)

    if not agent_ptc.enabled:
        return None

    return agent_ptc


def normalize_ptc_for_aip_agents(ptc: PTC | None) -> Any:
    """Normalize PTC config for aip-agents LangGraphReactAgent.

    Args:
        ptc: Validated PTC object or None.

    Returns:
        PTCSandboxConfig for aip-agents or None if PTC disabled.
    """
    if ptc is None or not ptc.enabled:
        return None

    from aip_agents.ptc import PromptConfig, PTCSandboxConfig  # noqa: PLC0415

    # Build PromptConfig if prompt dict is provided.
    prompt_config = None
    if ptc.prompt is not None:
        prompt_config = PromptConfig(**ptc.prompt)

    return PTCSandboxConfig(
        enabled=ptc.enabled,
        sandbox_timeout=ptc.sandbox_timeout,
        prompt=prompt_config,
    )
