"""
Streaming ASR (speech-to-text) example.

This example shows how to transcribe streaming audio in real-time.
"""

import asyncio
from pathlib import Path
from collections.abc import AsyncIterator

from litespeech import LiteSpeech


async def simulate_microphone_stream(
    audio_path: Path,
    chunk_size: int = 4096,
    delay: float = 0.1,
) -> AsyncIterator[bytes]:
    """
    Simulate a microphone stream by reading an audio file in chunks.

    In a real application, this would read from an actual microphone.
    """
    audio_data = audio_path.read_bytes()

    # Skip WAV header if present (44 bytes)
    if audio_data[:4] == b"RIFF":
        audio_data = audio_data[44:]

    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i : i + chunk_size]
        yield chunk
        await asyncio.sleep(delay)  # Simulate real-time streaming


async def main():
    ls = LiteSpeech()

    # For this example, you need a WAV audio file with PCM audio
    # 16-bit, 16kHz, mono is ideal for most ASR providers
    audio_path = Path("sample_audio.wav")

    if not audio_path.exists():
        print(f"Please provide a WAV audio file at: {audio_path}")
        print("For best results, use 16-bit, 16kHz, mono PCM audio.")
        return

    print("Streaming ASR with Deepgram...")
    print("-" * 40)

    # Create audio stream
    audio_stream = simulate_microphone_stream(audio_path)

    # Transcribe with interim results
    async for text in ls.speech_to_text_stream(
        audio_stream=audio_stream,
        provider="deepgram/nova-2",
        language="en",
        interim_results=True,
        encoding="linear16",
        sample_rate=16000,
    ):
        print(f"\r{text}", end="", flush=True)

    print("\n" + "-" * 40)
    print("Done!")


async def stream_with_elevenlabs():
    """Example streaming with ElevenLabs Scribe."""
    ls = LiteSpeech()

    audio_path = Path("sample_audio.wav")
    if not audio_path.exists():
        print("Please provide sample_audio.wav")
        return

    print("\nStreaming ASR with ElevenLabs Scribe...")
    print("-" * 40)

    audio_stream = simulate_microphone_stream(audio_path)

    async for text in ls.speech_to_text_stream(
        audio_stream=audio_stream,
        provider="elevenlabs/scribe_v1",
        language="en",
        interim_results=True,
        audio_format="pcm_16000",
    ):
        print(f"\r{text}", end="", flush=True)

    print("\n" + "-" * 40)


async def stream_with_cartesia():
    """Example streaming with Cartesia."""
    ls = LiteSpeech()

    audio_path = Path("sample_audio.wav")
    if not audio_path.exists():
        print("Please provide sample_audio.wav")
        return

    print("\nStreaming ASR with Cartesia...")
    print("-" * 40)

    audio_stream = simulate_microphone_stream(audio_path)

    async for text in ls.speech_to_text_stream(
        audio_stream=audio_stream,
        provider="cartesia/ink-whisper",
        language="en",
        interim_results=True,
        encoding="pcm_s16le",
        sample_rate=16000,
    ):
        print(f"\r{text}", end="", flush=True)

    print("\n" + "-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(stream_with_elevenlabs())
    # asyncio.run(stream_with_cartesia())
