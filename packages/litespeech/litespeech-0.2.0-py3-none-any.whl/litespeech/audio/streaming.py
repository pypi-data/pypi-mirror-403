"""Streaming audio utilities."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import TypeVar

T = TypeVar("T")


async def chunk_audio_stream(
    audio_stream: AsyncIterator[bytes],
    chunk_size: int = 4096,
) -> AsyncIterator[bytes]:
    """
    Normalize audio stream chunks to consistent size.

    Args:
        audio_stream: Input audio stream
        chunk_size: Target chunk size in bytes

    Yields:
        Audio chunks of approximately chunk_size bytes
    """
    buffer = bytearray()

    async for chunk in audio_stream:
        buffer.extend(chunk)

        while len(buffer) >= chunk_size:
            yield bytes(buffer[:chunk_size])
            buffer = buffer[chunk_size:]

    # Yield remaining data
    if buffer:
        yield bytes(buffer)


def chunk_audio_stream_sync(
    audio_stream: Iterator[bytes],
    chunk_size: int = 4096,
) -> Iterator[bytes]:
    """
    Synchronous version of chunk_audio_stream.

    Args:
        audio_stream: Input audio stream
        chunk_size: Target chunk size in bytes

    Yields:
        Audio chunks of approximately chunk_size bytes
    """
    buffer = bytearray()

    for chunk in audio_stream:
        buffer.extend(chunk)

        while len(buffer) >= chunk_size:
            yield bytes(buffer[:chunk_size])
            buffer = buffer[chunk_size:]

    # Yield remaining data
    if buffer:
        yield bytes(buffer)


async def merge_audio_streams(
    *streams: AsyncIterator[bytes],
) -> AsyncIterator[bytes]:
    """
    Merge multiple audio streams into one.

    Streams are processed sequentially - all data from first stream,
    then all data from second stream, etc.

    Args:
        *streams: Audio streams to merge

    Yields:
        Audio chunks from all streams in sequence
    """
    for stream in streams:
        async for chunk in stream:
            yield chunk


async def buffer_audio_stream(
    audio_stream: AsyncIterator[bytes],
    buffer_duration_ms: int = 100,
    sample_rate: int = 16000,
    bytes_per_sample: int = 2,
    channels: int = 1,
) -> AsyncIterator[bytes]:
    """
    Buffer audio stream to ensure minimum chunk duration.

    Useful for smoothing out irregular chunk sizes from providers.

    Args:
        audio_stream: Input audio stream
        buffer_duration_ms: Target buffer duration in milliseconds
        sample_rate: Audio sample rate
        bytes_per_sample: Bytes per sample (2 for 16-bit)
        channels: Number of audio channels

    Yields:
        Buffered audio chunks
    """
    bytes_per_ms = (sample_rate * bytes_per_sample * channels) // 1000
    target_size = buffer_duration_ms * bytes_per_ms

    buffer = bytearray()

    async for chunk in audio_stream:
        buffer.extend(chunk)

        while len(buffer) >= target_size:
            yield bytes(buffer[:target_size])
            buffer = buffer[target_size:]

    # Yield remaining data
    if buffer:
        yield bytes(buffer)


class AudioStreamQueue:
    """
    Async queue for managing audio stream data.

    Useful for bridging between producer/consumer patterns.
    """

    def __init__(self, maxsize: int = 0):
        """
        Initialize audio stream queue.

        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self._queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=maxsize)
        self._closed = False

    async def put(self, chunk: bytes) -> None:
        """Add audio chunk to queue."""
        if self._closed:
            raise RuntimeError("Cannot put to closed queue")
        await self._queue.put(chunk)

    def put_nowait(self, chunk: bytes) -> None:
        """Add audio chunk to queue without waiting."""
        if self._closed:
            raise RuntimeError("Cannot put to closed queue")
        self._queue.put_nowait(chunk)

    async def close(self) -> None:
        """Signal end of stream."""
        self._closed = True
        await self._queue.put(None)

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Iterate over audio chunks."""
        while True:
            chunk = await self._queue.get()
            if chunk is None:
                break
            yield chunk

    def __iter__(self) -> Iterator[bytes]:
        """Synchronous iteration (requires running event loop)."""
        loop = asyncio.get_event_loop()
        while True:
            chunk = loop.run_until_complete(self._queue.get())
            if chunk is None:
                break
            yield chunk
