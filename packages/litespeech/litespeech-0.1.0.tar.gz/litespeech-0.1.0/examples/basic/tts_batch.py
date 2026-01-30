"""
Basic batch TTS example.

This example shows how to convert text to speech using the batch API.
"""

import asyncio
from pathlib import Path

from litespeech import LiteSpeech


async def main():
    # Initialize client (uses environment variables for API keys)
    ls = LiteSpeech()

    # Basic TTS with ElevenLabs
    print("Converting text to speech with ElevenLabs...")
    audio = await ls.text_to_speech(
        text="Hello! This is a test of the LiteSpeech library. It provides a unified interface for text-to-speech across multiple providers.",
        provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",  # George voice
        output_format="mp3_44100_128",
    )

    # Save to file
    output_path = Path("output_elevenlabs.mp3")
    output_path.write_bytes(audio)
    print(f"Saved to {output_path}")

    # TTS with Deepgram Aura
    print("\nConverting text to speech with Deepgram Aura...")
    audio = await ls.text_to_speech(
        text="Hello! This is Deepgram Aura speaking. LiteSpeech makes it easy to switch between providers.",
        provider="deepgram/aura-asteria-en",
        output_format="mp3",
    )

    output_path = Path("output_deepgram.mp3")
    output_path.write_bytes(audio)
    print(f"Saved to {output_path}")

    # TTS with Cartesia
    print("\nConverting text to speech with Cartesia...")
    audio = await ls.text_to_speech(
        text="Hello! This is Cartesia's Sonic model. The unified API makes integration seamless.",
        provider="cartesia/sonic-3",
        output_format="wav",
    )

    output_path = Path("output_cartesia.wav")
    output_path.write_bytes(audio)
    print(f"Saved to {output_path}")

    # TTS with OpenAI
    print("\nConverting text to speech with OpenAI...")
    audio = await ls.text_to_speech(
        text="Hello! This is OpenAI's text-to-speech. Same API, different provider.",
        provider="openai/tts-1/alloy",
        output_format="mp3",
    )

    output_path = Path("output_openai.mp3")
    output_path.write_bytes(audio)
    print(f"Saved to {output_path}")

    print("\nDone! All audio files saved.")


# Sync usage example
def sync_example():
    """Example using the synchronous interface."""
    ls = LiteSpeech()

    # Use the sync interface
    audio = ls.sync.text_to_speech(
        text="This is using the synchronous interface.",
        provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
        output_format="mp3_44100_128",
    )

    Path("output_sync.mp3").write_bytes(audio)
    print("Saved sync example to output_sync.mp3")


if __name__ == "__main__":
    asyncio.run(main())
    # sync_example()
