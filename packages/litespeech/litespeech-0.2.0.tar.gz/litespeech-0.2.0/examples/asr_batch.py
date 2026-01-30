"""
Batch Speech-to-Text Example

This example demonstrates how to transcribe an audio file using LiteSpeech.

Requirements:
    pip install litespeech

Setup:
    Set your API key as an environment variable:
    export DEEPGRAM_API_KEY=your_api_key_here
"""

import asyncio
from litespeech import LiteSpeech


async def main():
    # Initialize LiteSpeech
    ls = LiteSpeech()

    # Path to your audio file
    audio_file = "recording.mp3"  # Replace with your audio file

    print(f"🎤 Transcribing {audio_file}...")

    # Transcribe audio
    text = await ls.speech_to_text(
        audio=audio_file,
        provider="deepgram/nova-2",
        language="en",
        # Optional Deepgram-specific parameters:
        punctuate=True,
        smart_format=True,
    )

    print("\n📝 Transcription:")
    print("-" * 60)
    print(text)
    print("-" * 60)


if __name__ == "__main__":
    asyncio.run(main())
