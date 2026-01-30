"""Anthropic stream adapter."""

from collections.abc import AsyncIterator
from typing import Any

from litespeech.adapters.base import StreamAdapter


class AnthropicStreamAdapter(StreamAdapter):
    """
    Adapter for Anthropic message streams.

    Handles:
    - anthropic.AsyncMessageStream
    - anthropic.MessageStream
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """
        Check if stream is an Anthropic message stream.

        Detects by checking module name.
        """
        stream_type = type(stream)
        module = getattr(stream_type, "__module__", "")

        # Check for anthropic module
        if "anthropic" not in module:
            return False

        # Check for MessageStream pattern
        class_name = stream_type.__name__
        if "MessageStream" in class_name or "Stream" in class_name:
            return True

        # Check for stream manager pattern
        if hasattr(stream, "__aiter__"):
            return True

        return False

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Convert Anthropic stream to token stream.

        Args:
            stream: Anthropic message stream

        Yields:
            Text tokens from content_block_delta events
        """
        # Handle different Anthropic stream types

        # Direct iteration over events
        async for event in stream:
            # Handle event objects
            event_type = getattr(event, "type", None)

            if event_type == "content_block_delta":
                delta = getattr(event, "delta", None)
                if delta:
                    text = getattr(delta, "text", None)
                    if text:
                        yield text

            # Handle text_delta specifically
            elif event_type == "text_delta":
                text = getattr(event, "text", None)
                if text:
                    yield text

            # Handle dict-like events (raw API)
            elif isinstance(event, dict):
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    text = delta.get("text")
                    if text:
                        yield text


class AnthropicTextStreamAdapter(StreamAdapter):
    """
    Adapter for Anthropic text streams (convenience wrapper).

    Handles streams that directly yield text via .text_stream.
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """Check if stream has text_stream attribute."""
        return hasattr(stream, "text_stream")

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Iterate over text_stream.

        Args:
            stream: Object with text_stream attribute

        Yields:
            Text chunks
        """
        async for text in stream.text_stream:
            yield text
