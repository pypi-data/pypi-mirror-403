"""
Streaming Text-to-Speech Example

This example demonstrates streaming TTS where audio chunks are generated
and saved as they arrive, enabling low-latency applications.

Requirements:
    pip install litespeech

Setup:
    Set your API key as an environment variable:
    export ELEVENLABS_API_KEY=your_api_key_here
"""

import asyncio
from litespeech import LiteSpeech


async def main():
    # Initialize LiteSpeech
    ls = LiteSpeech()

    text = """
    This is a streaming text-to-speech demonstration using LiteSpeech.
    Audio chunks are generated and saved in real-time.
    This enables low-latency voice applications.
    """

    print("🔊 Streaming speech...")

    # Collect audio chunks
    audio_chunks = []
    chunk_count = 0

    async for chunk in ls.text_to_speech_stream(
        text=text,
        provider="elevenlabs/eleven_turbo_v2_5",
        voice="JBFqnCBsd6RMkjVDRZzb",
        output_format="pcm_24000",
    ):
        audio_chunks.append(chunk)
        chunk_count += 1
        print(f"  Chunk {chunk_count}: {len(chunk):,} bytes", end="\r")

    print(f"\n✅ Received {chunk_count} chunks")

    # Save complete audio
    complete_audio = b"".join(audio_chunks)
    with open("output_streaming.pcm", "wb") as f:
        f.write(complete_audio)

    print(f"✅ Audio saved to output_streaming.pcm ({len(complete_audio):,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
