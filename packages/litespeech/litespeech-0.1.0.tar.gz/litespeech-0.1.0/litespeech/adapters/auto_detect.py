"""Auto-detection logic for LLM streams."""

from collections.abc import AsyncIterator
from typing import Any

from litespeech.adapters.base import StreamAdapter, PassthroughAdapter
from litespeech.adapters.openai_adapter import OpenAIStreamAdapter, OpenAIResponsesStreamAdapter
from litespeech.adapters.anthropic_adapter import AnthropicStreamAdapter, AnthropicTextStreamAdapter
from litespeech.adapters.litellm_adapter import LiteLLMStreamAdapter

# Order matters - more specific adapters should come first
ADAPTERS: list[type[StreamAdapter]] = [
    AnthropicTextStreamAdapter,
    AnthropicStreamAdapter,
    OpenAIResponsesStreamAdapter,
    OpenAIStreamAdapter,
    LiteLLMStreamAdapter,
    PassthroughAdapter,  # Fallback for plain async iterators
]


def detect_adapter(stream: Any) -> StreamAdapter | None:
    """
    Detect the appropriate adapter for a stream.

    Args:
        stream: The stream to detect

    Returns:
        StreamAdapter instance or None if not detected
    """
    for adapter_class in ADAPTERS:
        if adapter_class.can_handle(stream):
            return adapter_class()

    return None


def is_llm_stream(obj: Any) -> bool:
    """
    Check if an object is a recognized LLM stream.

    Args:
        obj: Object to check

    Returns:
        True if object is a recognized LLM stream
    """
    # Check if any adapter (except passthrough) can handle it
    for adapter_class in ADAPTERS[:-1]:  # Exclude PassthroughAdapter
        if adapter_class.can_handle(obj):
            return True
    return False


async def detect_and_adapt(stream: Any) -> AsyncIterator[str]:
    """
    Auto-detect stream type and return adapted stream.

    This is the main entry point for stream adaptation.
    It detects the type of LLM stream and converts it to
    a plain async iterator of strings.

    Args:
        stream: The LLM completion stream or text stream

    Yields:
        Text tokens/chunks

    Raises:
        ValueError: If stream type cannot be detected

    Examples:
        >>> # OpenAI stream
        >>> openai_stream = await client.chat.completions.create(..., stream=True)
        >>> async for token in detect_and_adapt(openai_stream):
        ...     print(token, end="")

        >>> # Anthropic stream
        >>> anthropic_stream = await client.messages.create(..., stream=True)
        >>> async for token in detect_and_adapt(anthropic_stream):
        ...     print(token, end="")

        >>> # Plain string stream (passthrough)
        >>> async def my_stream():
        ...     yield "Hello"
        ...     yield " world"
        >>> async for token in detect_and_adapt(my_stream()):
        ...     print(token, end="")
    """
    # If already a plain string, yield it
    if isinstance(stream, str):

        async def single_string() -> AsyncIterator[str]:
            yield stream

        async for token in single_string():
            yield token
        return

    # Detect appropriate adapter
    adapter = detect_adapter(stream)

    if adapter is None:
        raise ValueError(
            f"Could not detect stream type for {type(stream)}. "
            "Expected OpenAI, Anthropic, LiteLLM stream, or AsyncIterator[str]."
        )

    # Adapt and yield
    async for token in adapter.adapt(stream):
        yield token


async def adapt_to_text_stream(
    text_or_stream: str | AsyncIterator[str] | Any,
) -> AsyncIterator[str]:
    """
    Convert various text inputs to a text stream.

    Handles:
    - Plain strings (yields as single chunk)
    - Async iterators (yields chunks)
    - LLM streams (auto-detected and adapted)

    Args:
        text_or_stream: Text string, async iterator, or LLM stream

    Yields:
        Text chunks
    """
    if isinstance(text_or_stream, str):
        yield text_or_stream
    elif hasattr(text_or_stream, "__aiter__"):
        # Check if it's an LLM stream that needs adaptation
        if is_llm_stream(text_or_stream):
            async for token in detect_and_adapt(text_or_stream):
                yield token
        else:
            # Plain async iterator
            async for chunk in text_or_stream:
                if isinstance(chunk, str):
                    yield chunk
                else:
                    yield str(chunk)
    else:
        raise ValueError(
            f"Expected string, async iterator, or LLM stream, got {type(text_or_stream)}"
        )
