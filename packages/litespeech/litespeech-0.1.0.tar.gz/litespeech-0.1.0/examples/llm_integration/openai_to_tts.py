"""
OpenAI LLM to TTS integration example.

This example shows how to pipe OpenAI GPT output directly to TTS
for real-time voice assistant applications.
"""

import asyncio
from pathlib import Path

# Note: You need to install openai: pip install openai
try:
    from openai import AsyncOpenAI
except ImportError:
    print("Please install openai: pip install openai")
    exit(1)

from litespeech import LiteSpeech


async def main():
    """Stream GPT-4 output to ElevenLabs TTS."""
    # Initialize clients
    openai = AsyncOpenAI()
    ls = LiteSpeech()

    print("Generating response from GPT-4 and streaming to TTS...")
    print("-" * 50)

    # Get streaming response from GPT-4
    llm_stream = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant. Keep responses concise.",
            },
            {"role": "user", "content": "Tell me a short, interesting fact about space."},
        ],
        stream=True,
    )

    # Pipe directly to TTS (LiteSpeech auto-detects OpenAI stream)
    audio_chunks = []
    text_buffer = ""

    async for audio_chunk in ls.text_to_speech_stream(
        text_stream=llm_stream,  # Pass OpenAI stream directly!
        provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
        output_format="pcm_16000",
    ):
        audio_chunks.append(audio_chunk)
        print(".", end="", flush=True)

    print("\n" + "-" * 50)

    # Save combined audio
    all_audio = b"".join(audio_chunks)
    output_path = Path("output_llm_to_tts.pcm")
    output_path.write_bytes(all_audio)
    print(f"Saved {len(all_audio)} bytes to {output_path}")


async def stream_to_deepgram():
    """Stream GPT-4 output to Deepgram Aura."""
    openai = AsyncOpenAI()
    ls = LiteSpeech()

    print("\nStreaming GPT-4 to Deepgram Aura...")

    llm_stream = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "What's the weather like on Mars?"},
        ],
        stream=True,
    )

    audio_chunks = []
    async for chunk in ls.text_to_speech_stream(
        text_stream=llm_stream,
        provider="deepgram/aura-asteria-en",
        output_format="linear16",
        sample_rate=24000,
    ):
        audio_chunks.append(chunk)
        print(".", end="", flush=True)

    all_audio = b"".join(audio_chunks)
    Path("output_gpt_to_deepgram.pcm").write_bytes(all_audio)
    print(f"\nSaved {len(all_audio)} bytes")


async def stream_to_cartesia():
    """Stream GPT-4 output to Cartesia."""
    openai = AsyncOpenAI()
    ls = LiteSpeech()

    print("\nStreaming GPT-4 to Cartesia...")

    llm_stream = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Explain quantum entanglement in simple terms."},
        ],
        stream=True,
    )

    audio_chunks = []
    async for chunk in ls.text_to_speech_stream(
        text_stream=llm_stream,
        provider="cartesia/sonic-3",
        output_format="pcm_s16le",
        sample_rate=16000,
    ):
        audio_chunks.append(chunk)
        print(".", end="", flush=True)

    all_audio = b"".join(audio_chunks)
    Path("output_gpt_to_cartesia.pcm").write_bytes(all_audio)
    print(f"\nSaved {len(all_audio)} bytes")


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(stream_to_deepgram())
    # asyncio.run(stream_to_cartesia())
