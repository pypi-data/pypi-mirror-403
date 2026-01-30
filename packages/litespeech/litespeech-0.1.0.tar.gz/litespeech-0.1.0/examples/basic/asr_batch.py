"""
Basic batch ASR (speech-to-text) example.

This example shows how to transcribe audio files using the batch API.
"""

import asyncio
from pathlib import Path

from litespeech import LiteSpeech


async def main():
    ls = LiteSpeech()

    # For this example, you need an audio file
    # You can use any audio file in a supported format (mp3, wav, etc.)
    audio_path = Path("sample_audio.mp3")

    if not audio_path.exists():
        print(f"Please provide an audio file at: {audio_path}")
        print("You can use any audio file for testing.")
        return

    print(f"Transcribing {audio_path}...")

    # Transcribe with Deepgram
    print("\n1. Using Deepgram Nova-2:")
    text = await ls.speech_to_text(
        audio=audio_path,
        provider="deepgram/nova-2",
        language="en",
        punctuate=True,
        smart_format=True,
    )
    print(f"Transcript: {text}")

    # Transcribe with ElevenLabs Scribe
    print("\n2. Using ElevenLabs Scribe:")
    text = await ls.speech_to_text(
        audio=audio_path,
        provider="elevenlabs/scribe_v1",
        language="en",
    )
    print(f"Transcript: {text}")

    # Transcribe with Cartesia
    print("\n3. Using Cartesia Ink Whisper:")
    text = await ls.speech_to_text(
        audio=audio_path,
        provider="cartesia/ink-whisper",
        language="en",
    )
    print(f"Transcript: {text}")

    # Transcribe with OpenAI Whisper
    print("\n4. Using OpenAI Whisper:")
    text = await ls.speech_to_text(
        audio=audio_path,
        provider="openai/whisper-1",
        language="en",
    )
    print(f"Transcript: {text}")


async def transcribe_from_bytes():
    """Example transcribing from bytes instead of file path."""
    ls = LiteSpeech()

    audio_path = Path("sample_audio.mp3")
    if not audio_path.exists():
        print("Please provide sample_audio.mp3 for this example")
        return

    # Read audio as bytes
    audio_bytes = audio_path.read_bytes()

    # Transcribe from bytes
    text = await ls.speech_to_text(
        audio=audio_bytes,
        provider="deepgram/nova-2",
        language="en",
    )
    print(f"Transcript from bytes: {text}")


# Sync usage example
def sync_example():
    """Example using the synchronous interface."""
    ls = LiteSpeech()

    audio_path = Path("sample_audio.mp3")
    if not audio_path.exists():
        print("Please provide sample_audio.mp3 for this example")
        return

    # Use the sync interface
    text = ls.sync.speech_to_text(
        audio=audio_path,
        provider="deepgram/nova-2",
        language="en",
    )
    print(f"Sync transcript: {text}")


if __name__ == "__main__":
    asyncio.run(main())
