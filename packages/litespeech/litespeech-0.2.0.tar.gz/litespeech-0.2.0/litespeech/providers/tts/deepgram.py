"""Deepgram TTS provider implementation."""

import asyncio
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


class DeepgramTTSProvider(TTSProvider):
    """
    Deepgram Aura TTS provider with WebSocket streaming support.

    Features:
    - True streaming: text-in, audio-out via WebSocket
    - Batch TTS via HTTP API
    - Multiple Aura voice models
    """

    BASE_URL = "https://api.deepgram.com"
    WS_URL = "wss://api.deepgram.com"

    DEFAULT_MODEL = "aura-asteria-en"

    def __init__(self, deepgram_api_key: str | None = None, **kwargs):
        """
        Initialize Deepgram TTS provider.

        Args:
            deepgram_api_key: Deepgram API key (defaults to DEEPGRAM_API_KEY env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "deepgram",
                "deepgram_api_key must be provided or DEEPGRAM_API_KEY env var must be set"
            )
        self._http_client: httpx.AsyncClient | None = None

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="deepgram",
            display_name="Deepgram Aura",
            capabilities=ProviderCapabilities(
                tts_batch=True,
                tts_streaming=True,
                tts_input_streaming=True,  # Supports text_stream from LLMs
                asr_batch=False,
                asr_streaming=False,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            supported_models=[
                "aura-asteria-en",
                "aura-luna-en",
                "aura-stella-en",
                "aura-athena-en",
                "aura-hera-en",
                "aura-orion-en",
                "aura-arcas-en",
                "aura-perseus-en",
                "aura-angus-en",
                "aura-orpheus-en",
                "aura-helios-en",
                "aura-zeus-en",
                "aura-2-thalia-en",
            ],
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Token {self._api_key}"},
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
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech using HTTP API.

        Note: Deepgram uses format "model-voice-language" (e.g., "aura-asteria-en").

        Args:
            text: Text to convert
            model: Model/series name (e.g., "aura") or full identifier (e.g., "aura-asteria-en")
            voice: Voice name (e.g., "asteria"). Combined with model and language if all provided.
            language: Language code (e.g., "en"). Combined with model and voice if all provided.
            output_format: Output encoding (linear16, mp3, opus, flac, etc.)
            **kwargs: Additional options (sample_rate, container, etc.)

        Returns:
            Audio bytes
        """
        # Deepgram uses combined model-voice-language as identifier
        # Examples: "aura-asteria-en", "aura-luna-en"
        # Priority: Combine all provided parts
        if model and voice and language:
            # Full specification: "aura" + "asteria" + "en" = "aura-asteria-en"
            final_model = f"{model}-{voice}-{language}"
        elif model and voice:
            # Model and voice without language: "aura-asteria"
            final_model = f"{model}-{voice}"
        elif voice and language:
            # Voice and language without model: "asteria-en"
            final_model = f"{voice}-{language}"
        elif model:
            # Just model (could be full like "aura-asteria-en" or partial like "aura")
            final_model = model
        elif voice:
            # Just voice
            final_model = voice
        else:
            # Use default
            final_model = self.DEFAULT_MODEL

        client = await self._get_http_client()

        params: dict[str, Any] = {
            "model": final_model,
            "encoding": output_format if output_format != "wav" else "linear16",
        }

        # Add optional parameters
        if "sample_rate" in kwargs:
            params["sample_rate"] = kwargs["sample_rate"]
        if "container" in kwargs:
            params["container"] = kwargs["container"]
        elif output_format == "wav":
            params["container"] = "wav"

        try:
            response = await client.post(
                "/v1/speak",
                json={"text": text},
                params=params,
            )
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"Deepgram API error: {e.response.text}",
                provider="deepgram",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ProviderError(
                f"Deepgram request error: {str(e)}",
                provider="deepgram",
            )

    async def text_to_speech_stream(
        self,
        text_stream: AsyncIterator[str],
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "linear16",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream text to speech using WebSocket API.

        Note: Deepgram uses format "model-voice-language" (e.g., "aura-asteria-en").

        Args:
            text_stream: Async iterator of text chunks
            model: Model/series name (e.g., "aura") or full identifier (e.g., "aura-asteria-en")
            voice: Voice name (e.g., "asteria"). Combined with model and language if all provided.
            language: Language code (e.g., "en"). Combined with model and voice if all provided.
            output_format: Output encoding (linear16 recommended for streaming)
            **kwargs: Additional options (sample_rate, etc.)

        Yields:
            Audio chunks (binary)
        """
        # Deepgram uses combined model-voice-language as identifier
        # Examples: "aura-asteria-en", "aura-luna-en"
        # Priority: Combine all provided parts
        if model and voice and language:
            # Full specification: "aura" + "asteria" + "en" = "aura-asteria-en"
            final_model = f"{model}-{voice}-{language}"
        elif model and voice:
            # Model and voice without language: "aura-asteria"
            final_model = f"{model}-{voice}"
        elif voice and language:
            # Voice and language without model: "asteria-en"
            final_model = f"{voice}-{language}"
        elif model:
            # Just model (could be full like "aura-asteria-en" or partial like "aura")
            final_model = model
        elif voice:
            # Just voice
            final_model = voice
        else:
            # Use default
            final_model = self.DEFAULT_MODEL

        sample_rate = kwargs.get("sample_rate", 24000)

        # Build WebSocket URL
        ws_url = (
            f"{self.WS_URL}/v1/speak"
            f"?model={final_model}"
            f"&encoding={output_format}"
            f"&sample_rate={sample_rate}"
        )

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"Authorization": f"Token {self._api_key}"},
            ) as ws:
                audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()

                async def send_text() -> None:
                    """Send text chunks to WebSocket."""
                    try:
                        async for chunk in text_stream:
                            if chunk:
                                message = {"type": "Speak", "text": chunk}
                                await ws.send(json.dumps(message))

                        # Flush and close
                        await ws.send(json.dumps({"type": "Flush"}))
                        await ws.send(json.dumps({"type": "Close"}))
                    except Exception:
                        await audio_queue.put(None)
                        raise

                async def receive_audio() -> None:
                    """Receive audio chunks from WebSocket."""
                    try:
                        async for message in ws:
                            # Binary messages are audio data
                            if isinstance(message, bytes):
                                await audio_queue.put(message)
                            else:
                                # JSON message (metadata, flushed, etc.)
                                data = json.loads(message)
                                if data.get("type") == "Flushed":
                                    continue
                                if data.get("type") == "Warning":
                                    continue

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
            raise StreamingError(f"Deepgram WebSocket error: {str(e)}")
        except Exception as e:
            raise StreamingError(f"Deepgram streaming error: {str(e)}")

    async def text_to_speech_stream_simple(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        output_format: str = "linear16",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Stream TTS for a single text string.

        Args:
            text: Text to convert
            model: Model/voice name
            voice: Alias for model
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
