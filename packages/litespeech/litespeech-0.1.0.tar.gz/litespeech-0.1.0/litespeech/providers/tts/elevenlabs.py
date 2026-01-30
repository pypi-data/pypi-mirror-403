"""ElevenLabs TTS provider implementation."""

import asyncio
import base64
import json
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx
import websockets

from litespeech.providers.base import (
    TTSProvider,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError


class ElevenLabsTTSProvider(TTSProvider):
    """
    ElevenLabs TTS provider with WebSocket streaming support.

    Features:
    - True streaming: text-in, audio-out via WebSocket
    - Batch TTS via HTTP API
    - Multiple voice options
    """

    BASE_URL = "https://api.elevenlabs.io"
    WS_URL = "wss://api.elevenlabs.io"

    DEFAULT_MODEL = "eleven_turbo_v2_5"
    DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"  # George

    def __init__(self, elevenlabs_api_key: str | None = None, **kwargs):
        """
        Initialize ElevenLabs TTS provider.

        Args:
            elevenlabs_api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "elevenlabs",
                "elevenlabs_api_key must be provided or ELEVENLABS_API_KEY env var must be set"
            )
        self._http_client: httpx.AsyncClient | None = None

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="elevenlabs",
            display_name="ElevenLabs",
            capabilities=ProviderCapabilities(
                tts_batch=True,
                tts_streaming=True,
                asr_batch=False,
                asr_streaming=False,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            default_voice=self.DEFAULT_VOICE,
            supported_models=[
                "eleven_turbo_v2_5",
                "eleven_multilingual_v2",
                "eleven_monolingual_v1",
            ],
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"xi-api-key": self._api_key},
                timeout=60.0,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def text_to_speech(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "mp3_44100_128",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech using HTTP API.

        Args:
            text: Text to convert
            model: Model ID (default: eleven_turbo_v2_5)
            voice: Voice ID (default: George)
            language: Language code (e.g., "en", "es", "fr")
            output_format: Output format (default: mp3_44100_128)
            **kwargs: Additional options (voice_settings, etc.)

        Returns:
            Audio bytes
        """
        model = model or self.DEFAULT_MODEL
        voice = voice or self.DEFAULT_VOICE

        client = await self._get_http_client()

        payload: dict[str, Any] = {
            "text": text,
            "model_id": model,
        }

        # Add optional parameters
        if language is not None:
            payload["language_code"] = language
        if "voice_settings" in kwargs:
            payload["voice_settings"] = kwargs["voice_settings"]

        try:
            response = await client.post(
                f"/v1/text-to-speech/{voice}",
                json=payload,
                params={"output_format": output_format},
            )
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"ElevenLabs API error: {e.response.text}",
                provider="elevenlabs",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ProviderError(
                f"ElevenLabs request error: {str(e)}",
                provider="elevenlabs",
            )

    async def text_to_speech_stream(
        self,
        text_stream: AsyncIterator[str],
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "pcm_16000",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream text to speech using WebSocket API.

        Args:
            text_stream: Async iterator of text chunks
            model: Model ID (default: eleven_turbo_v2_5)
            voice: Voice ID (default: George)
            language: Language code (e.g., "en", "es", "fr")
            output_format: Output format (default: pcm_16000 for low latency)
            **kwargs: Additional options (voice_settings, etc.)

        Yields:
            Audio chunks
        """
        model = model or self.DEFAULT_MODEL
        voice = voice or self.DEFAULT_VOICE

        # Build WebSocket URL with query parameters
        ws_url = (
            f"{self.WS_URL}/v1/text-to-speech/{voice}/stream-input"
            f"?model_id={model}"
            f"&output_format={output_format}"
        )

        # Add language if provided
        if language is not None:
            ws_url += f"&language_code={language}"

        # Voice settings
        voice_settings = kwargs.get("voice_settings", {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0,
            "use_speaker_boost": True,
        })

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"xi-api-key": self._api_key},
            ) as ws:
                # Send initialization message
                init_message = {
                    "text": " ",
                    "voice_settings": voice_settings,
                    "generation_config": {
                        "chunk_length_schedule": [120, 160, 250, 290],
                    },
                }
                await ws.send(json.dumps(init_message))

                # Create tasks for sending and receiving
                audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

                async def send_text() -> None:
                    """Send text chunks to WebSocket."""
                    try:
                        async for chunk in text_stream:
                            if chunk:
                                message = {
                                    "text": chunk,
                                    "try_trigger_generation": True,
                                }
                                await ws.send(json.dumps(message))

                        # Send close signal
                        await ws.send(json.dumps({"text": ""}))
                    except Exception as e:
                        await audio_queue.put(None)
                        raise

                async def receive_audio() -> None:
                    """Receive audio chunks from WebSocket."""
                    try:
                        async for message in ws:
                            data = json.loads(message)

                            if data.get("audio"):
                                audio_bytes = base64.b64decode(data["audio"])
                                await audio_queue.put(audio_bytes)

                            if data.get("isFinal"):
                                break

                        await audio_queue.put(None)
                    except Exception as e:
                        await audio_queue.put(None)
                        raise

                # Start send task
                send_task = asyncio.create_task(send_text())
                receive_task = asyncio.create_task(receive_audio())

                # Yield audio chunks
                try:
                    while True:
                        audio_chunk = await audio_queue.get()
                        if audio_chunk is None:
                            break
                        yield audio_chunk
                finally:
                    send_task.cancel()
                    receive_task.cancel()
                    try:
                        await send_task
                    except asyncio.CancelledError:
                        pass
                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        pass

        except websockets.exceptions.WebSocketException as e:
            raise StreamingError(f"ElevenLabs WebSocket error: {str(e)}")
        except Exception as e:
            raise StreamingError(f"ElevenLabs streaming error: {str(e)}")

    async def text_to_speech_stream_simple(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        output_format: str = "pcm_16000",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream TTS for a single text string.

        Convenience method that wraps text in an async iterator.

        Args:
            text: Text to convert
            model: Model ID
            voice: Voice ID
            output_format: Output format
            **kwargs: Additional options

        Yields:
            Audio chunks
        """

        async def text_generator() -> AsyncIterator[str]:
            yield text

        async for chunk in self.text_to_speech_stream(
            text_generator(),
            model=model,
            voice=voice,
            output_format=output_format,
            **kwargs,
        ):
            yield chunk
