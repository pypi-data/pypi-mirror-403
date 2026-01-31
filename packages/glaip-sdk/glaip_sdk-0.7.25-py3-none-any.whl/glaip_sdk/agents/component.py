"""Agent Component for Glaip SDK.

This module provides the AgentComponent class, which wraps an Agent
to be used as a reusable component in pipelines.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gllm_core.schema import Chunk, Component
from gllm_core.utils import LoggerManager

if TYPE_CHECKING:
    from glaip_sdk.agents import Agent

logger = LoggerManager().get_logger(__name__)


class AgentComponent(Component):
    """A Component that wraps a GL Agent for pipeline integration.

    This component acts as a bridge between structured pipeline state
    and the natural language interface of an Agent. It compiles inputs
    (query, context, history) into a prompt and executes the agent.
    """

    def __init__(self, agent: Agent) -> None:
        """Initialize the AgentComponent.

        Args:
            agent: The Agent instance to wrap.
        """
        super().__init__()
        self.agent = agent

    def _format_context(self, context: list[Chunk | str | dict[str, Any] | Any] | None) -> str:
        """Format the context list into a string.

        Supports Chunk objects (extracting content), strings, and dicts.

        Args:
            context: List of context items.

        Returns:
            Formatted context string.
        """
        if not context:
            return ""

        formatted_items = []
        for item in context:
            if isinstance(item, Chunk):
                content = item.content
            elif isinstance(item, dict):
                content = str(item)
            else:
                content = str(item)
            formatted_items.append(f"- {content}")

        return "\n".join(formatted_items)

    def _format_history(self, history: list[Any] | None) -> str:
        """Format the chat history into a string.

        Supports gllm_inference Message objects and dicts.

        Args:
            history: List of history items.

        Returns:
            Formatted history string.
        """
        if not history:
            return "No previous history."

        # Try to use gllm_inference schema if available for robust handling
        try:
            from gllm_inference.schema import Message  # noqa: PLC0415
        except ImportError:
            Message = None

        formatted_items = []
        for item in history:
            if Message and isinstance(item, Message):
                # Message object has role and contents (list)
                role = item.role.capitalize()
                # Use standard content property if available, or join contents
                content = getattr(item, "content", None)
                if content is None and hasattr(item, "contents"):
                    content = "\n".join([str(c) for c in item.contents])
                formatted_items.append(f"{role}: {content}")
            elif isinstance(item, dict):
                role = str(item.get("role", "User")).capitalize()
                content = str(item.get("content", ""))
                formatted_items.append(f"{role}: {content}")
            else:
                formatted_items.append(str(item))
        return "\n".join(formatted_items)

    def _compile_prompt(
        self,
        query: str,
        context: list[Any] | None,
        chat_history: list[Any] | None,
    ) -> str:
        """Compile the raw inputs into a single text prompt.

        Args:
            query: The user query.
            context: List of context items.
            chat_history: List of conversation history items.

        Returns:
            The compiled prompt string.
        """
        parts = []

        if chat_history:
            history_str = self._format_history(chat_history)
            parts.append(f"Conversation History:\n{history_str}\n")

        if context:
            context_str = self._format_context(context)
            parts.append(f"Context:\n{context_str}\n")

        parts.append(f"{query}\n")

        return "\n".join(parts)

    async def run_agent(
        self,
        query: str,
        context: list[Chunk | Any] | None = None,
        chat_history: list[Any] | None = None,
        runtime_config: dict[str, Any] | None = None,
        run_kwargs: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the agent with the provided context and history.

        This method is the main entry point for the component logic.

        Args:
            query: The user's input string.
            context: List of retrieved documents/chunks or data.
            chat_history: List of previous conversation turns.
            runtime_config: Optional configuration.
            run_kwargs: Optional payload for advanced agent execution parameters.

        Returns:
            The raw response dictionary from the agent.
        """
        if not query:
            raise ValueError("Query is required")

        logger.info("Compiling prompt for agent: %s", self.agent.name)

        prompt = self._compile_prompt(
            query=query,
            context=context,
            chat_history=chat_history,
        )

        params = (run_kwargs or {}).copy()
        if runtime_config:
            params["runtime_config"] = runtime_config

        last_chunk = {}

        try:
            async for chunk in self.agent.arun(message=prompt, **params):
                if isinstance(chunk, dict):
                    last_chunk = chunk
                    if chunk.get("event_type") == "final_response":
                        return chunk
        except Exception as e:
            raise RuntimeError(f"AgentComponent '{self.agent.name}' failed during execution: {e}") from e

        return last_chunk

    def _extract_content_string(self, result: Any) -> str:
        """Extract the content string from the agent response.

        Assumes the result is always a string or a dictionary containing a content field.

        Args:
            result: The agent response (dict or string).

        Returns:
            The content string extracted from the response.
        """
        if isinstance(result, dict):
            content = result.get("content")
            if content is not None:
                return str(content)
            return str(result)

        return str(result) if result is not None else ""

    async def _run(self, **kwargs: Any) -> str:
        """Execute the component logic.

        Args:
            **kwargs: Keyword arguments including query, context, chat_history,
                        runtime_config, and run_kwargs. All execution control parameters
                        (e.g., local, verbose, temperature, etc.) must be provided via
                        run_kwargs dict.

        Returns:
            The content string extracted from the response.
        """
        # Extract standard component inputs
        query = kwargs.pop("query", None)
        context = kwargs.pop("context", None)
        chat_history = kwargs.pop("chat_history", None)
        runtime_config = kwargs.pop("runtime_config", None)
        run_kwargs = kwargs.pop("run_kwargs", None)

        # Ignore any remaining unrecognized kwargs for API consistency
        # All execution parameters must be provided via run_kwargs

        result = await self.run_agent(
            query=query,  # type: ignore[arg-type]
            context=context,
            chat_history=chat_history,
            runtime_config=runtime_config,
            run_kwargs=run_kwargs,
        )

        return self._extract_content_string(result)
