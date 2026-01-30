# LiteSpeech Examples

This directory contains working examples demonstrating how to use LiteSpeech.

## Setup

1. **Install LiteSpeech:**
   ```bash
   pip install litespeech
   ```

2. **Set API Keys:**

   Each example requires API keys for the providers used. Set them as environment variables:

   ```bash
   # ElevenLabs (for TTS examples)
   export ELEVENLABS_API_KEY=your_elevenlabs_key

   # Deepgram (for ASR examples)
   export DEEPGRAM_API_KEY=your_deepgram_key

   # OpenAI (for LLM integration example)
   export OPENAI_API_KEY=your_openai_key
   ```

## Examples

### Text-to-Speech (TTS)

#### 1. **Batch TTS** - `tts_batch.py`
Convert text to speech and save to a file.
```bash
python tts_batch.py
```

#### 2. **Streaming TTS** - `tts_streaming.py`
Generate speech with streaming for low-latency applications.
```bash
python tts_streaming.py
```

#### 3. **LLM-to-TTS Streaming** - `tts_llm_streaming.py`
Pipe LLM output (OpenAI, Anthropic) directly to TTS in real-time.
```bash
python tts_llm_streaming.py
```

### Speech-to-Text (ASR)

#### 4. **Batch ASR** - `asr_batch.py`
Transcribe an audio file.
```bash
python asr_batch.py
```
**Note:** Update `audio_file` path in the script to point to your audio file.

#### 5. **Streaming ASR** - `asr_streaming.py`
Real-time transcription from microphone with interim results.
```bash
python asr_streaming.py
```
Requires: `pip install sounddevice`

## Provider-Specific Notes

### Switching Providers

All examples can be adapted to use different providers. Simply change the `provider` parameter:

**TTS Providers:**
- ElevenLabs: `elevenlabs/eleven_turbo_v2_5`
- Deepgram: `deepgram/aura`
- Cartesia: `cartesia/sonic-3`
- OpenAI: `openai/tts-1`
- Azure: `azure`

**ASR Providers:**
- Deepgram: `deepgram/nova-2`
- ElevenLabs: `elevenlabs` (streaming) or `elevenlabs/scribe_v1` (batch)
- Cartesia: `cartesia/ink-whisper`
- OpenAI: `openai/whisper-1`
- Azure: `azure`

### Example: Using Cartesia Instead

```python
# In tts_batch.py, change:
audio_bytes = await ls.text_to_speech(
    text=text,
    provider="cartesia/sonic-3",  # Changed
    voice="79a125e8-cd45-4c13-8a67-188112f4dd22",
    language="en",
)
```

## More Examples

For more complex examples (FastAPI integration, microphone handling, etc.), see:
- `basic/` - Additional basic examples
- `llm_integration/` - LLM integration patterns
- `servers/` - Server implementations (FastAPI, WebSocket)

## Troubleshooting

**ImportError: No module named 'litespeech'**
```bash
pip install litespeech
```

**AuthenticationError: API key not set**
```bash
# Make sure environment variable is set:
export ELEVENLABS_API_KEY=your_key_here
```

**Audio playback issues**
The examples save audio to files. To play audio:
```bash
# For MP3
ffplay output.mp3

# For PCM (raw audio)
ffplay -f s16le -ar 24000 -ac 1 output_streaming.pcm
```

## Documentation

For full documentation, see: [README.md](../README.md)
