# pylint: disable=duplicate-code
"""Model constants for GL AIP SDK.

Typed constants for popular AI models matching AIP Server's language_models.yaml keys.
"""

from __future__ import annotations

__all__ = [
    "ModelProvider",
    "OpenAI",
    "Anthropic",
    "Google",
    "AzureOpenAI",
    "DeepInfra",
    "DeepSeek",
    "Bedrock",
    "DEFAULT_MODEL",
]

# Note: DeepInfra provider changed to 'openai-compatible' for aip_agents compatibility


class ModelProvider:
    """Supported model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure-openai"
    GOOGLE = "google"
    DEEPINFRA = "deepinfra"
    DEEPSEEK = "deepseek"
    OPENAI_COMPATIBLE = "openai-compatible"
    BEDROCK = "bedrock"


class OpenAI:
    """OpenAI model constants."""

    GPT_4O_MINI = "openai/gpt-4o-mini"
    GPT_4O = "openai/gpt-4o"
    GPT_4_1 = "openai/gpt-4.1"
    GPT_4_1_NANO = "openai/gpt-4.1-nano"
    GPT_4_1_MINI = "openai/gpt-4.1-mini"
    GPT_5 = "openai/gpt-5"
    GPT_5_MINI = "openai/gpt-5-mini"
    GPT_5_NANO = "openai/gpt-5-nano"
    GPT_5_LOW = "openai/gpt-5-low"
    GPT_5_MINIMAL = "openai/gpt-5-minimal"
    GPT_5_MEDIUM = "openai/gpt-5-medium"
    GPT_5_HIGH = "openai/gpt-5-high"
    GPT_5_1 = "openai/gpt-5.1"
    GPT_5_1_LOW = "openai/gpt-5.1-low"
    GPT_5_1_MEDIUM = "openai/gpt-5.1-medium"
    GPT_5_1_HIGH = "openai/gpt-5.1-high"
    GPT_5_2 = "openai/gpt-5.2"
    GPT_5_2_LOW = "openai/gpt-5.2-low"
    GPT_5_2_MEDIUM = "openai/gpt-5.2-medium"
    GPT_5_2_HIGH = "openai/gpt-5.2-high"
    GPT_5_2_XHIGH = "openai/gpt-5.2-xhigh"
    GPT_4O_2024_11_20 = "openai/gpt-4o-2024-11-20"
    O4_MINI = "openai/o4-mini"


class Anthropic:
    """Anthropic model constants."""

    CLAUDE_3_5_SONNET_LATEST = "anthropic/claude-3-5-sonnet-latest"
    CLAUDE_3_7_SONNET_LATEST = "anthropic/claude-3-7-sonnet-latest"
    CLAUDE_SONNET_4_0 = "anthropic/claude-sonnet-4-0"
    CLAUDE_OPUS_4_0 = "anthropic/claude-opus-4-0"
    CLAUDE_OPUS_4_1 = "anthropic/claude-opus-4-1"
    CLAUDE_SONNET_4_5 = "anthropic/claude-sonnet-4-5"
    # DX Alias
    CLAUDE_3_5_SONNET = CLAUDE_3_5_SONNET_LATEST


class Google:
    """Google model constants."""

    GEMINI_2_5_FLASH = "google/gemini-2.5-flash"
    GEMINI_3_FLASH_PREVIEW = "google/gemini-3-flash-preview"
    GEMINI_3_PRO_PREVIEW = "google/gemini-3-pro-preview"
    GEMINI_2_5_PRO = "google/gemini-2.5-pro"


class AzureOpenAI:
    """Azure OpenAI model constants."""

    GPT_4O = "azure-openai/gpt-4o"
    GPT_4O_MINI = "azure-openai/gpt-4o-mini"
    GPT_4_1 = "azure-openai/gpt-4.1"


class DeepInfra:
    """DeepInfra model constants.

    Note: DeepInfra models use the openai-compatible driver internally,
    but we expose them with the 'deepinfra/' prefix for better DX.
    The SDK handles the mapping to 'openai-compatible/' automatically.
    """

    QWEN3_235B_A22B_INSTRUCT_2507 = "deepinfra/Qwen/Qwen3-235B-A22B-Instruct-2507"
    KIMI_K2_INSTRUCT = "deepinfra/moonshotai/Kimi-K2-Instruct"
    QWEN3_30B_A3B = "deepinfra/Qwen/Qwen3-30B-A3B"
    GLM_4_5_AIR = "deepinfra/zai-org/GLM-4.5-Air"
    QWEN3_32B = "deepinfra/Qwen/Qwen3-32B"
    QWEN3_NEXT_80B_A3B_THINKING = "deepinfra/Qwen/Qwen3-Next-80B-A3B-Thinking"
    QWEN3_NEXT_80B_A3B_INSTRUCT = "deepinfra/Qwen/Qwen3-Next-80B-A3B-Instruct"
    QWEN3_14B = "deepinfra/Qwen/Qwen3-14B"
    GLM_4_5 = "deepinfra/zai-org/GLM-4.5"


class DeepSeek:
    """DeepSeek model constants.

    Note: DeepSeek models use the openai-compatible driver internally,
    but we expose them with the 'deepseek/' prefix for better DX.
    The SDK handles the mapping to 'openai-compatible/' automatically.
    """

    DEEPSEEK_CHAT = "deepseek/deepseek-chat"
    DEEPSEEK_V3_1 = "deepseek/deepseek-ai/DeepSeek-V3.1"
    DEEPSEEK_V3_1_TERMINUS = "deepseek/deepseek-ai/DeepSeek-V3.1-Terminus"


class Bedrock:
    """AWS Bedrock model constants."""

    CLAUDE_SONNET_4_20250514_V1_0 = "bedrock/us.anthropic.claude-sonnet-4-20250514-v1:0"
    CLAUDE_3_5_HAIKU_20241022_V1_0 = "bedrock/us.anthropic.claude-3-5-haiku-20241022-v1:0"
    CLAUDE_SONNET_4_5_20250929_V1_0 = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    # DX Aliases
    ANTHROPIC_CLAUDE_SONNET_4 = CLAUDE_SONNET_4_20250514_V1_0
    ANTHROPIC_CLAUDE_3_5_HAIKU = CLAUDE_3_5_HAIKU_20241022_V1_0
    ANTHROPIC_CLAUDE_SONNET_4_5 = CLAUDE_SONNET_4_5_20250929_V1_0


# Default model selection
DEFAULT_MODEL = OpenAI.GPT_5_NANO
