"""
Anthropic Claude to TTS integration example.

This example shows how to pipe Claude output directly to TTS
for real-time voice assistant applications.
"""

import asyncio
from pathlib import Path

# Note: You need to install anthropic: pip install anthropic
try:
    from anthropic import AsyncAnthropic
except ImportError:
    print("Please install anthropic: pip install anthropic")
    exit(1)

from litespeech import LiteSpeech


async def main():
    """Stream Claude output to ElevenLabs TTS."""
    # Initialize clients
    anthropic = AsyncAnthropic()
    ls = LiteSpeech()

    print("Generating response from Claude and streaming to TTS...")
    print("-" * 50)

    # Get streaming response from Claude
    async with anthropic.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Tell me a short, interesting fact about the ocean."},
        ],
    ) as stream:
        # Pipe directly to TTS (LiteSpeech auto-detects Anthropic stream)
        audio_chunks = []

        async for audio_chunk in ls.text_to_speech_stream(
            text_stream=stream,  # Pass Anthropic stream directly!
            provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
            output_format="pcm_16000",
        ):
            audio_chunks.append(audio_chunk)
            print(".", end="", flush=True)

    print("\n" + "-" * 50)

    # Save combined audio
    all_audio = b"".join(audio_chunks)
    output_path = Path("output_claude_to_tts.pcm")
    output_path.write_bytes(all_audio)
    print(f"Saved {len(all_audio)} bytes to {output_path}")


async def using_text_stream():
    """Alternative: use text_stream for direct text iteration."""
    anthropic = AsyncAnthropic()
    ls = LiteSpeech()

    print("\nUsing text_stream with Claude...")

    async with anthropic.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "What's the deepest point in the ocean?"},
        ],
    ) as stream:
        # Use text_stream for simpler iteration
        audio_chunks = []

        async for chunk in ls.text_to_speech_stream(
            text_stream=stream.text_stream,  # Use text_stream attribute
            provider="cartesia/sonic-3",
            output_format="pcm_s16le",
        ):
            audio_chunks.append(chunk)
            print(".", end="", flush=True)

    all_audio = b"".join(audio_chunks)
    Path("output_claude_text_stream.pcm").write_bytes(all_audio)
    print(f"\nSaved {len(all_audio)} bytes")


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(using_text_stream())
