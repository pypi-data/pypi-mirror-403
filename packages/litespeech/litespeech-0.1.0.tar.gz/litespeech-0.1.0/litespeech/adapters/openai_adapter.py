"""OpenAI stream adapter."""

from collections.abc import AsyncIterator
from typing import Any

from litespeech.adapters.base import StreamAdapter


class OpenAIStreamAdapter(StreamAdapter):
    """
    Adapter for OpenAI chat completion streams.

    Handles both:
    - openai.AsyncStream[ChatCompletionChunk]
    - openai.Stream[ChatCompletionChunk] (sync wrapped in async)
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """
        Check if stream is an OpenAI completion stream.

        Detects by checking module name and class attributes.
        """
        stream_type = type(stream)
        module = getattr(stream_type, "__module__", "")

        # Check for openai module
        if "openai" not in module:
            return False

        # Check for Stream or AsyncStream class names
        class_name = stream_type.__name__
        if "Stream" in class_name:
            return True

        # Check for _iterator attribute (openai SDK pattern)
        if hasattr(stream, "_iterator"):
            return True

        return False

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Convert OpenAI stream to token stream.

        Args:
            stream: OpenAI AsyncStream[ChatCompletionChunk]

        Yields:
            Text tokens from delta.content
        """
        async for chunk in stream:
            # Handle ChatCompletionChunk structure
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and choice.delta:
                    content = getattr(choice.delta, "content", None)
                    if content:
                        yield content
            # Handle dict-like structure (in case of raw API response)
            elif isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content


class OpenAIResponsesStreamAdapter(StreamAdapter):
    """
    Adapter for OpenAI Responses API streams (new format).

    Handles openai beta responses streams with different event structure.
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """Check if stream is an OpenAI Responses stream."""
        stream_type = type(stream)
        module = getattr(stream_type, "__module__", "")

        if "openai" not in module:
            return False

        # Check for responses-specific patterns
        class_name = stream_type.__name__
        return "Response" in class_name and "Stream" in class_name

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Convert OpenAI Responses stream to token stream.

        Args:
            stream: OpenAI responses stream

        Yields:
            Text tokens
        """
        async for event in stream:
            # Handle different event types
            event_type = getattr(event, "type", None)

            if event_type == "content_part.delta":
                delta = getattr(event, "delta", None)
                if delta:
                    text = getattr(delta, "text", None)
                    if text:
                        yield text

            elif event_type == "text.delta":
                text = getattr(event, "text", None)
                if text:
                    yield text
