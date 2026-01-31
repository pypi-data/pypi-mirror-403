"""Guardrail serialization logic.

This module provides functionality to serialize GuardrailManager and its engines
into the JSON format expected by the GL AIP backend. This keeps the serialization
logic within the SDK rather than polluting the core aip-agents logic.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glaip_sdk.guardrails import (
        GuardrailManager,
        NemoGuardrailEngine,
        PhraseMatcherEngine,
    )


def _serialize_phrase_matcher(engine: PhraseMatcherEngine) -> dict[str, Any]:
    """Serialize a PhraseMatcherEngine configuration."""
    config: dict[str, Any] = {}

    # Extract config from BaseGuardrailEngineConfig
    if hasattr(engine, "config") and engine.config:
        config.update(engine.config.model_dump())

    # Extract specific fields
    if hasattr(engine, "banned_phrases"):
        config["banned_phrases"] = engine.banned_phrases

    return config


def _serialize_nemo(engine: NemoGuardrailEngine) -> dict[str, Any]:
    """Serialize a NemoGuardrailEngine configuration."""
    config: dict[str, Any] = {}

    # Extract config from BaseGuardrailEngineConfig
    if hasattr(engine, "config") and engine.config:
        config.update(engine.config.model_dump())

    # Extract specific fields
    nemo_fields = [
        "topic_safety_mode",
        "allowed_topics",
        "denied_topics",
        "include_core_restrictions",
        "core_restriction_categories",
        "config_dict",
        "denial_phrases",
    ]
    for field in nemo_fields:
        if hasattr(engine, field):
            val = getattr(engine, field)
            if val is not None:
                config[field] = val

    return config


def serialize_guardrail_manager(manager: GuardrailManager) -> dict[str, Any]:
    """Serialize a GuardrailManager into the backend JSON format.

    Args:
        manager: The GuardrailManager instance to serialize.

    Returns:
        A dictionary matching the agent_config.guardrails schema.
    """
    try:
        from glaip_sdk.guardrails import NemoGuardrailEngine, PhraseMatcherEngine  # noqa: PLC0415
    except ImportError:
        enabled = getattr(manager, "enabled", True)
        return {"enabled": enabled, "engines": []}

    engines_config = []

    if hasattr(manager, "engines"):
        for engine in manager.engines:
            if isinstance(engine, PhraseMatcherEngine):
                engines_config.append({"type": "phrase_matcher", "config": _serialize_phrase_matcher(engine)})
            elif isinstance(engine, NemoGuardrailEngine):
                engines_config.append({"type": "nemo", "config": _serialize_nemo(engine)})
            # Unknown engines are skipped.

    enabled = getattr(manager, "enabled", True)
    return {"enabled": enabled, "engines": engines_config}
