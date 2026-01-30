"""
LLM-to-TTS Streaming Example

This example demonstrates how to pipe LLM output directly to TTS,
creating a voice assistant that speaks as the LLM generates text.

Requirements:
    pip install litespeech openai

Setup:
    export ELEVENLABS_API_KEY=your_elevenlabs_key
    export OPENAI_API_KEY=your_openai_key
"""

import asyncio
from openai import AsyncOpenAI
from litespeech import LiteSpeech


async def main():
    # Initialize clients
    openai = AsyncOpenAI()
    ls = LiteSpeech()

    print("🤖 Asking GPT-4...")

    # Create LLM stream
    llm_stream = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": "Tell me a short interesting fact about space."}
        ],
        stream=True,
    )

    print("🔊 Converting to speech in real-time...")

    # Pipe LLM output directly to TTS
    audio_chunks = []
    async for audio_chunk in ls.text_to_speech_stream(
        text_stream=llm_stream,  # Auto-detects OpenAI stream!
        provider="elevenlabs/eleven_turbo_v2_5",
        voice="JBFqnCBsd6RMkjVDRZzb",
        output_format="pcm_24000",
    ):
        audio_chunks.append(audio_chunk)
        print(".", end="", flush=True)

    print(f"\n✅ Generated {len(audio_chunks)} audio chunks")

    # Save complete audio
    complete_audio = b"".join(audio_chunks)
    with open("llm_output.pcm", "wb") as f:
        f.write(complete_audio)

    print(f"✅ Audio saved to llm_output.pcm ({len(complete_audio):,} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
