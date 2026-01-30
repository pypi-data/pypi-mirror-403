"""Base stream adapter interface."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class StreamAdapter(ABC):
    """
    Abstract base class for LLM stream adapters.

    Adapters convert provider-specific LLM completion streams
    into plain text token streams.
    """

    @classmethod
    @abstractmethod
    def can_handle(cls, stream: Any) -> bool:
        """
        Check if this adapter can handle the given stream.

        Args:
            stream: The stream object to check

        Returns:
            True if this adapter can handle the stream
        """
        pass

    @abstractmethod
    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """
        Convert provider-specific stream to token stream.

        Args:
            stream: The LLM completion stream

        Yields:
            Text tokens/chunks
        """
        pass


class PassthroughAdapter(StreamAdapter):
    """
    Adapter that passes through string async iterators as-is.

    Used when the input is already a plain string stream.
    """

    @classmethod
    def can_handle(cls, stream: Any) -> bool:
        """Check if stream is an async iterator of strings."""
        return hasattr(stream, "__aiter__") and hasattr(stream, "__anext__")

    async def adapt(self, stream: Any) -> AsyncIterator[str]:
        """Pass through the stream."""
        async for chunk in stream:
            if isinstance(chunk, str):
                yield chunk
            else:
                yield str(chunk)
