"""Guardrails package for content filtering and safety checks.

This package provides modular guardrail engines and managers for filtering
harmful content in AI agent interactions. All components support lazy loading
from aip-agents to maintain Principle VII compliance.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aip_agents.guardrails.engines.nemo import NemoGuardrailEngine
    from aip_agents.guardrails.engines.phrase_matcher import PhraseMatcherEngine
    from aip_agents.guardrails.manager import GuardrailManager
    from aip_agents.guardrails.schemas import GuardrailMode


class ImportableName(StrEnum):
    """Names of the importable attributes."""

    GUARDRAIL_MANAGER = "GuardrailManager"
    PHRASE_MATCHER_ENGINE = "PhraseMatcherEngine"
    NEMO_GUARDRAIL_ENGINE = "NemoGuardrailEngine"
    GUARDRAIL_MODE = "GuardrailMode"


# Lazy loading support - components are only imported when actually used
_LAZY_IMPORTS = {}


def __getattr__(name: str) -> Any:
    """Lazy import to avoid eager loading of optional aip-agents dependency.

    This function is called by Python when an attribute is not found in the module.
    It performs the import from aip_agents.guardrails at runtime.

    Args:
        name: The name of the attribute to get.

    Returns:
        The attribute value from aip_agents.

    Raises:
        AttributeError: If the attribute doesn't exist.
        ImportError: If aip-agents is not installed but a component is accessed.
    """
    if name in _LAZY_IMPORTS:
        return _LAZY_IMPORTS[name]

    if name == ImportableName.GUARDRAIL_MANAGER:
        from aip_agents.guardrails.manager import GuardrailManager  # noqa: PLC0415

        _LAZY_IMPORTS[name] = GuardrailManager
        return GuardrailManager

    if name == ImportableName.PHRASE_MATCHER_ENGINE:
        from aip_agents.guardrails.engines.phrase_matcher import (  # noqa: PLC0415
            PhraseMatcherEngine,
        )

        _LAZY_IMPORTS[name] = PhraseMatcherEngine
        return PhraseMatcherEngine

    if name == ImportableName.NEMO_GUARDRAIL_ENGINE:
        from aip_agents.guardrails.engines.nemo import NemoGuardrailEngine  # noqa: PLC0415

        _LAZY_IMPORTS[name] = NemoGuardrailEngine
        return NemoGuardrailEngine

    if name == ImportableName.GUARDRAIL_MODE:
        from aip_agents.guardrails.schemas import GuardrailMode  # noqa: PLC0415

        _LAZY_IMPORTS[name] = GuardrailMode
        return GuardrailMode

    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
