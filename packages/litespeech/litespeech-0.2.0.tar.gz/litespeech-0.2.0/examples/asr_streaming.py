"""
Streaming Speech-to-Text Example

This example demonstrates real-time transcription from microphone input
with interim results (partial transcripts as you speak).

Requirements:
    pip install litespeech sounddevice

Setup:
    Set your API key as an environment variable:
    export DEEPGRAM_API_KEY=your_api_key_here
"""

import asyncio
import queue
from collections.abc import AsyncIterator
import sounddevice as sd
from litespeech import LiteSpeech


# Audio configuration
SAMPLE_RATE = 16000
CHANNELS = 1


async def microphone_stream() -> AsyncIterator[bytes]:
    """Stream audio from microphone in real-time."""
    # Use thread-safe queue for audio chunks
    audio_queue = queue.Queue()

    def audio_callback(indata, frames, time, status):
        """Callback for sounddevice to capture audio."""
        if status:
            print(f"[Audio Status] {status}")
        # Copy data (sounddevice reuses buffers)
        audio_queue.put(indata.copy().tobytes())

    # Open microphone stream
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        callback=audio_callback,
    )

    with stream:
        while True:
            try:
                chunk = audio_queue.get(timeout=0.1)
                yield chunk
            except queue.Empty:
                await asyncio.sleep(0.01)
                continue


async def main():
    # Initialize LiteSpeech
    ls = LiteSpeech()

    print("🎤 Starting real-time transcription...")
    print("Speak into your microphone. Press Ctrl+C to stop.\n")

    try:
        async for result in ls.speech_to_text_stream(
            audio_stream=microphone_stream(),
            provider="deepgram/nova-2",
            language="en",
            sample_rate=SAMPLE_RATE,
            channels=CHANNELS,
            encoding="linear16",
            interim_results=True,  # Get partial transcripts
        ):
            if result.is_final:
                # Final transcript (committed)
                print(f"\n✓ {result.text}")
            else:
                # Interim transcript (may change)
                print(f"\r  {result.text}...", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\n👋 Stopping transcription...")


if __name__ == "__main__":
    asyncio.run(main())
