"""Cartesia TTS provider implementation."""

import asyncio
import base64
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any
import uuid

import httpx
import websockets

from litespeech.providers.base import (
    TTSProvider,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError

logger = logging.getLogger(__name__)


class CartesiaTTSProvider(TTSProvider):
    """
    Cartesia TTS provider with WebSocket streaming support.

    Features:
    - True streaming: text-in, audio-out via WebSocket
    - Batch TTS via HTTP API
    - Multiple voice options with emotion control
    """

    BASE_URL = "https://api.cartesia.ai"
    WS_URL = "wss://api.cartesia.ai"
    API_VERSION = "2025-04-16"

    DEFAULT_MODEL = "sonic-3"
    DEFAULT_VOICE = "79a125e8-cd45-4c13-8a67-188112f4dd22"  # Default voice

    def __init__(self, cartesia_api_key: str | None = None, **kwargs):
        """
        Initialize Cartesia TTS provider.

        Args:
            cartesia_api_key: Cartesia API key (defaults to CARTESIA_API_KEY env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = cartesia_api_key or os.getenv("CARTESIA_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "cartesia",
                "cartesia_api_key must be provided or CARTESIA_API_KEY env var must be set"
            )
        self._http_client: httpx.AsyncClient | None = None

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="cartesia",
            display_name="Cartesia",
            capabilities=ProviderCapabilities(
                tts_batch=True,
                tts_streaming=True,
                asr_batch=False,
                asr_streaming=False,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            default_voice=self.DEFAULT_VOICE,
            supported_models=["sonic-3", "sonic-2", "sonic"],
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "X-API-Key": self._api_key,
                    "Cartesia-Version": self.API_VERSION,
                },
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
        output_format: str = "wav",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech using HTTP API.

        Args:
            text: Text to convert
            model: Model ID (default: sonic-3)
            voice: Voice ID (default: uses default voice)
            language: Language code (e.g., "en", "es", "fr") - default: "en"
            output_format: Output format (wav, mp3, raw)
            **kwargs: Additional options (sample_rate, generation_config)

        Returns:
            Audio bytes
        """
        model = model or self.DEFAULT_MODEL
        voice = voice or self.DEFAULT_VOICE
        sample_rate = kwargs.get("sample_rate", 44100)
        language = language or "en"

        client = await self._get_http_client()

        # Build output format spec
        if output_format == "wav":
            output_format_spec = {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": sample_rate,
            }
        elif output_format == "mp3":
            output_format_spec = {
                "container": "mp3",
                "sample_rate": sample_rate,
                "bit_rate": kwargs.get("bit_rate", 128000),
            }
        else:
            # Raw PCM
            output_format_spec = {
                "container": "raw",
                "encoding": kwargs.get("encoding", "pcm_s16le"),
                "sample_rate": sample_rate,
            }

        payload: dict[str, Any] = {
            "model_id": model,
            "transcript": text,
            "voice": {"mode": "id", "id": voice},
            "output_format": output_format_spec,
            "language": language,
        }

        # Add generation config if provided
        if "generation_config" in kwargs:
            payload["generation_config"] = kwargs["generation_config"]

        try:
            response = await client.post("/tts/bytes", json=payload)
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"Cartesia API error: {e.response.text}",
                provider="cartesia",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ProviderError(
                f"Cartesia request error: {str(e)}",
                provider="cartesia",
            )

    async def text_to_speech_stream(
        self,
        text_stream: AsyncIterator[str],
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "pcm_s16le",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream text to speech using WebSocket API.

        Args:
            text_stream: Async iterator of text chunks
            model: Model ID (default: sonic-3)
            voice: Voice ID (default: uses default voice)
            language: Language code (e.g., "en", "es", "fr") - default: "en"
            output_format: Output encoding (pcm_s16le recommended for streaming)
            **kwargs: Additional options (sample_rate, etc.)

        Yields:
            Audio chunks
        """
        model = model or self.DEFAULT_MODEL
        voice = voice or self.DEFAULT_VOICE
        sample_rate = kwargs.get("sample_rate", 16000)
        language = language or "en"

        # Build WebSocket URL
        ws_url = (
            f"{self.WS_URL}/tts/websocket"
            f"?api_key={self._api_key}"
            f"&cartesia_version={self.API_VERSION}"
        )

        # Generate unique context ID
        context_id = str(uuid.uuid4())

        try:
            async with websockets.connect(ws_url) as ws:
                audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

                async def send_text() -> None:
                    """Send text chunks to WebSocket."""
                    try:
                        first_chunk = True
                        async for chunk in text_stream:
                            if chunk:
                                message = {
                                    "model_id": model,
                                    "transcript": chunk,
                                    "voice": {"mode": "id", "id": voice},
                                    "language": language,
                                    "context_id": context_id,
                                    "output_format": {
                                        "container": "raw",
                                        "encoding": output_format,
                                        "sample_rate": sample_rate,
                                    },
                                    "continue": True,  # All chunks expect more input
                                }
                                logger.debug(f"Sending to Cartesia: {json.dumps({**message, 'transcript': message['transcript'][:50] + '...' if len(message['transcript']) > 50 else message['transcript']})}")
                                await ws.send(json.dumps(message))
                                first_chunk = False

                        # Send final message with continue=false to close the context
                        final_message = {
                            "model_id": model,
                            "transcript": "",  # Empty transcript is allowed
                            "voice": {"mode": "id", "id": voice},
                            "language": language,
                            "context_id": context_id,
                            "output_format": {
                                "container": "raw",
                                "encoding": output_format,
                                "sample_rate": sample_rate,
                            },
                            "continue": False,  # Signal end of context
                        }
                        logger.debug("Sending final message to close Cartesia context")
                        await ws.send(json.dumps(final_message))

                    except Exception:
                        await audio_queue.put(None)
                        raise

                async def receive_audio() -> None:
                    """Receive audio chunks from WebSocket."""
                    try:
                        async for message in ws:
                            data = json.loads(message)

                            # Check for our context
                            if data.get("context_id") != context_id:
                                continue

                            msg_type = data.get("type")

                            if msg_type == "chunk" and data.get("data"):
                                audio_bytes = base64.b64decode(data["data"])
                                await audio_queue.put(audio_bytes)
                            elif msg_type == "done":
                                break
                            elif msg_type == "error":
                                # Log full error for debugging
                                error_msg = data.get('message', 'Unknown error')
                                logger.error(f"Cartesia error response: {data}")
                                raise StreamingError(
                                    f"Cartesia error: {error_msg}\nFull response: {data}"
                                )

                        await audio_queue.put(None)
                    except Exception:
                        await audio_queue.put(None)
                        raise

                send_task = asyncio.create_task(send_text())
                receive_task = asyncio.create_task(receive_audio())

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
            raise StreamingError(f"Cartesia WebSocket error: {str(e)}")
        except Exception as e:
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"Cartesia streaming error: {str(e)}")

    async def text_to_speech_stream_simple(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        output_format: str = "pcm_s16le",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream TTS for a single text string.

        Args:
            text: Text to convert
            model: Model ID
            voice: Voice ID
            output_format: Output encoding
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
