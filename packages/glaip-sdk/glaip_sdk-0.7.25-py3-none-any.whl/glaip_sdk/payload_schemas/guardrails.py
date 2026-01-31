"""Guardrail payload schemas for API communication.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field


class GuardrailEnginePayload(BaseModel):
    """Payload schema for a single guardrail engine configuration.

    This model defines the structure for individual safety engines (e.g., phrase_matcher, nemo)
    when communicating with the GL AIP backend.
    """

    type: str = Field(..., description="The type of guardrail engine (e.g., 'phrase_matcher', 'nemo')")
    config: Mapping[str, Any] = Field(..., description="Engine-specific configuration parameters")


class GuardrailPayload(BaseModel):
    """Payload schema for global guardrail settings.

    This model acts as the container for all guardrail configurations within the agent_config.
    """

    enabled: bool = Field(default=True, description="Global toggle to enable or disable all guardrails")
    engines: Sequence[GuardrailEnginePayload] = Field(
        default_factory=list,
        description="List of configured guardrail engines",
    )
