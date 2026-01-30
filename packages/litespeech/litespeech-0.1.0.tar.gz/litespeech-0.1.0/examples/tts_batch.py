"""
Batch Text-to-Speech Example

This example demonstrates how to convert text to speech using LiteSpeech
and save the result to a file.

Requirements:
    pip install litespeech

Setup:
    Set your API key as an environment variable:
    export ELEVENLABS_API_KEY=your_api_key_here
"""

import asyncio
from litespeech import LiteSpeech


async def main():
    # Initialize LiteSpeech (reads API key from environment)
    ls = LiteSpeech()

    # Text to convert
    text = """
    Hello! This is a demonstration of LiteSpeech text-to-speech.
    The quick brown fox jumps over the lazy dog.
    """

    print("🔊 Generating speech...")

    # Generate speech
    audio_bytes = await ls.text_to_speech(
        text=text,
        provider="elevenlabs/eleven_turbo_v2_5",
        voice="JBFqnCBsd6RMkjVDRZzb",  # George voice
        output_format="mp3_44100_128",
    )

    # Save to file
    with open("output.mp3", "wb") as f:
        f.write(audio_bytes)

    print(f"✅ Audio saved to output.mp3 ({len(audio_bytes):,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
