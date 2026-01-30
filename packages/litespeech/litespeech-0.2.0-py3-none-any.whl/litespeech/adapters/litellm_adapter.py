"""LiteLLM stream adapter."""

from collections.abc import AsyncIterator
from typing import Any

from litespeech.adapters.base import StreamAdapter


class LiteLLMStreamAdapter(StreamAdapter):
    """
    Adapter for LiteLLM completion streams.

    LiteLLM provides a unified interface across providers,
    but the stream format follows OpenAI's pattern.
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """
        Check if stream is a LiteLLM stream.

        Detects by checking module name.
        """
        stream_type = type(stream)
        module = getattr(stream_type, "__module__", "")

        # Check for litellm module
        if "litellm" in module:
            return True

        # LiteLLM often wraps other providers' streams
        # Check for CustomStreamWrapper
        class_name = stream_type.__name__
        if "CustomStreamWrapper" in class_name:
            return True

        return False

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Convert LiteLLM stream to token stream.

        LiteLLM streams follow OpenAI's format with choices[0].delta.content

        Args:
            stream: LiteLLM completion stream

        Yields:
            Text tokens
        """
        async for chunk in stream:
            # Handle ModelResponse objects
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, "delta"):
                    delta = choice.delta
                    content = getattr(delta, "content", None)
                    if content:
                        yield content
                # Some versions use message instead of delta
                elif hasattr(choice, "message"):
                    message = choice.message
                    content = getattr(message, "content", None)
                    if content:
                        yield content

            # Handle dict-like chunks
            elif isinstance(chunk, dict):
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content

            # Handle raw string chunks (some LiteLLM modes)
            elif isinstance(chunk, str):
                yield chunk
