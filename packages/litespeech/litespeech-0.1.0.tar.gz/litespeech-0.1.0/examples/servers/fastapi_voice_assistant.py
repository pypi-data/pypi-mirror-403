"""
FastAPI Voice Assistant WebSocket Server.

This example shows how to build a real-time voice assistant
using FastAPI WebSockets with LiteSpeech.

Run with: uvicorn fastapi_voice_assistant:app --reload

Client sends: Audio chunks (binary)
Server sends: Audio chunks (binary) + Text updates (JSON)
"""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# Note: Install required packages:
# pip install fastapi uvicorn openai litespeech

try:
    from openai import AsyncOpenAI
except ImportError:
    print("Please install openai: pip install openai")

from litespeech import LiteSpeech

app = FastAPI(title="Voice Assistant")
ls = LiteSpeech()
openai_client = AsyncOpenAI()


# Simple HTML client for testing
HTML_CLIENT = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Assistant</title>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 50px auto; }
        button { padding: 10px 20px; font-size: 16px; margin: 5px; }
        #transcript { padding: 20px; background: #f0f0f0; min-height: 100px; }
        #status { color: #666; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Voice Assistant Demo</h1>
    <button id="start">Start Recording</button>
    <button id="stop" disabled>Stop</button>
    <p id="status">Click Start to begin</p>
    <div id="transcript"></div>

    <script>
        let ws, mediaRecorder, audioContext;

        document.getElementById('start').onclick = async () => {
            ws = new WebSocket('ws://localhost:8000/voice-assistant');
            ws.binaryType = 'arraybuffer';

            audioContext = new AudioContext({sampleRate: 16000});

            ws.onmessage = async (e) => {
                if (e.data instanceof ArrayBuffer) {
                    playAudio(e.data);
                } else {
                    const data = JSON.parse(e.data);
                    if (data.type === 'transcript') {
                        document.getElementById('transcript').innerText = data.text;
                    } else if (data.type === 'status') {
                        document.getElementById('status').innerText = data.message;
                    }
                }
            };

            const stream = await navigator.mediaDevices.getUserMedia({audio: true});
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0 && ws.readyState === 1) ws.send(e.data);
            };
            mediaRecorder.start(100);

            document.getElementById('start').disabled = true;
            document.getElementById('stop').disabled = false;
            document.getElementById('status').innerText = 'Recording...';
        };

        document.getElementById('stop').onclick = () => {
            mediaRecorder.stop();
            ws.close();
            document.getElementById('start').disabled = false;
            document.getElementById('stop').disabled = true;
            document.getElementById('status').innerText = 'Stopped';
        };

        function playAudio(data) {
            const buffer = audioContext.createBuffer(1, data.byteLength/2, 16000);
            const channel = buffer.getChannelData(0);
            const view = new Int16Array(data);
            for (let i = 0; i < view.length; i++) channel[i] = view[i] / 32768;
            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start();
        }
    </script>
</body>
</html>
"""


@app.get("/")
async def get_client():
    """Serve the test HTML client."""
    return HTMLResponse(HTML_CLIENT)


@app.websocket("/voice-assistant")
async def voice_assistant_endpoint(websocket: WebSocket):
    """
    Full-duplex voice assistant over WebSocket.

    Flow:
    1. Receive audio from client
    2. Transcribe with ASR (Deepgram)
    3. Generate response with LLM (GPT-4)
    4. Stream response audio back with TTS (ElevenLabs)
    """
    await websocket.accept()

    try:
        # Queues for audio flow
        audio_input_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        audio_output_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

        async def receive_audio():
            """Receive audio chunks from client."""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    await audio_input_queue.put(data)
            except WebSocketDisconnect:
                await audio_input_queue.put(None)

        async def send_audio():
            """Send audio chunks to client."""
            while True:
                chunk = await audio_output_queue.get()
                if chunk is None:
                    break
                await websocket.send_bytes(chunk)

        async def process_pipeline():
            """ASR -> LLM -> TTS pipeline."""

            # Create async generator from queue
            async def audio_generator() -> AsyncIterator[bytes]:
                while True:
                    chunk = await audio_input_queue.get()
                    if chunk is None:
                        break
                    yield chunk

            # ASR: Transcribe audio
            await websocket.send_json({"type": "status", "message": "Listening..."})

            user_text = ""
            async for text in ls.speech_to_text_stream(
                audio_stream=audio_generator(),
                provider="deepgram/nova-2",
                language="en",
                interim_results=False,
                encoding="linear16",
                sample_rate=16000,
            ):
                user_text = text
                await websocket.send_json({"type": "transcript", "text": f"You: {text}"})

                # Simple end-of-speech detection
                if text.strip().endswith((".", "!", "?")):
                    break

            if not user_text.strip():
                await websocket.send_json({"type": "status", "message": "No speech detected"})
                await audio_output_queue.put(None)
                return

            # LLM: Generate response
            await websocket.send_json({"type": "status", "message": "Thinking..."})

            llm_stream = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Keep responses brief and conversational."},
                    {"role": "user", "content": user_text},
                ],
                stream=True,
            )

            # TTS: Stream response audio
            await websocket.send_json({"type": "status", "message": "Speaking..."})

            response_text = ""
            async for audio_chunk in ls.text_to_speech_stream(
                text_stream=llm_stream,
                provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
                output_format="pcm_16000",
            ):
                await audio_output_queue.put(audio_chunk)

            await audio_output_queue.put(None)
            await websocket.send_json({"type": "status", "message": "Done"})

        # Run tasks concurrently
        await asyncio.gather(
            receive_audio(),
            send_audio(),
            process_pipeline(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


@app.websocket("/asr-only")
async def asr_only_endpoint(websocket: WebSocket):
    """ASR-only endpoint: Audio in -> Text out."""
    await websocket.accept()

    try:
        async def audio_generator() -> AsyncIterator[bytes]:
            while True:
                try:
                    data = await websocket.receive_bytes()
                    yield data
                except WebSocketDisconnect:
                    break

        async for text in ls.speech_to_text_stream(
            audio_stream=audio_generator(),
            provider="deepgram/nova-2",
            interim_results=True,
        ):
            await websocket.send_json({
                "type": "transcript",
                "text": text,
                "is_final": text.endswith((".", "!", "?")),
            })

    except WebSocketDisconnect:
        pass


@app.websocket("/tts-only")
async def tts_only_endpoint(websocket: WebSocket):
    """TTS-only endpoint: Text in -> Audio out."""
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        text = data.get("text", "")

        async for audio_chunk in ls.text_to_speech_stream(
            text=text,
            provider="elevenlabs/eleven_turbo_v2_5/JBFqnCBsd6RMkjVDRZzb",
            output_format="pcm_16000",
        ):
            await websocket.send_bytes(audio_chunk)

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
