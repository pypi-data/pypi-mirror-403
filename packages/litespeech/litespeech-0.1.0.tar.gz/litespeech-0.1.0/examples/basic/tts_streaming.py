"""
Streaming TTS example.

This example shows how to stream text-to-speech audio in real-time.
"""

import asyncio
from pathlib import Path

from litespeech import LiteSpeech


async def main():
    ls = LiteSpeech()

    print("Streaming TTS with ElevenLabs...")

    # Collect audio chunks for this example (in real use, you'd play them)
    audio_chunks = []

    async for chunk in ls.text_to_speech_stream(
        text="Hello! This is a streaming TTS example. The audio is generated in chunks as the text is processed, allowing for very low latency playback. This is ideal for voice assistants and real-time applications.",
        provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
        output_format="pcm_16000",  # Raw PCM for streaming
    ):
        audio_chunks.append(chunk)
        print(f"Received chunk: {len(chunk)} bytes")

    # Combine chunks and save
    all_audio = b"".join(audio_chunks)
    print(f"\nTotal audio: {len(all_audio)} bytes")

    # Save as raw PCM (can be converted to WAV for playback)
    output_path = Path("output_stream.pcm")
    output_path.write_bytes(all_audio)
    print(f"Saved raw PCM to {output_path}")


async def stream_with_cartesia():
    """Example streaming with Cartesia."""
    ls = LiteSpeech()

    print("\nStreaming TTS with Cartesia...")

    audio_chunks = []
    async for chunk in ls.text_to_speech_stream(
        text="Cartesia also supports streaming TTS. This enables real-time audio generation for interactive applications.",
        provider="cartesia/sonic-3",
        output_format="pcm_s16le",
        sample_rate=16000,
    ):
        audio_chunks.append(chunk)
        print(f"Received chunk: {len(chunk)} bytes")

    all_audio = b"".join(audio_chunks)
    Path("output_stream_cartesia.pcm").write_bytes(all_audio)
    print("Saved to output_stream_cartesia.pcm")


async def stream_with_deepgram():
    """Example streaming with Deepgram."""
    ls = LiteSpeech()

    print("\nStreaming TTS with Deepgram Aura...")

    audio_chunks = []
    async for chunk in ls.text_to_speech_stream(
        text="Deepgram Aura provides high-quality streaming TTS with very low latency. Perfect for conversational AI.",
        provider="deepgram/aura-asteria-en",
        output_format="linear16",
        sample_rate=24000,
    ):
        audio_chunks.append(chunk)
        print(f"Received chunk: {len(chunk)} bytes")

    all_audio = b"".join(audio_chunks)
    Path("output_stream_deepgram.pcm").write_bytes(all_audio)
    print("Saved to output_stream_deepgram.pcm")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(stream_with_cartesia())
    asyncio.run(stream_with_deepgram())
