"""Cartesia ASR provider implementation."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx
import websockets

logger = logging.getLogger(__name__)

from litespeech.providers.base import (
    ASRProvider,
    ASRResult,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError


class CartesiaASRProvider(ASRProvider):
    """
    Cartesia ASR provider with WebSocket streaming support.

    Features:
    - True streaming: audio-in, text-out via WebSocket
    - Batch transcription via HTTP API
    - Ink Whisper model
    """

    BASE_URL = "https://api.cartesia.ai"
    WS_URL = "wss://api.cartesia.ai"
    API_VERSION = "2025-04-16"

    DEFAULT_MODEL = "ink-whisper"

    def __init__(self, cartesia_api_key: str | None = None, **kwargs):
        """
        Initialize Cartesia ASR provider.

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
                tts_batch=False,
                tts_streaming=False,
                asr_batch=True,
                asr_streaming=True,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            supported_models=["ink-whisper"],
        )

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict[str, Any]:
        """Get audio specs for Cartesia."""
        return {
            "preferred": {"format": "wav"},
            "recommended_sample_rate": 16000,
        }

    def validate_language(self, language: str | None) -> str:
        """
        Validate language code for Cartesia.

        Cartesia accepts:
        - ISO-639-1 (2-letter) codes: 'en', 'es', 'fr', 'de', etc.
        - Special value: 'multilingual' for auto-detection

        Returns:
            Validated language code (defaults to 'multilingual' if None)
        """
        import re

        # Default to multilingual if not specified
        if language is None:
            return "multilingual"

        # Normalize
        language_normalized = language.lower().strip()

        # Allow special value
        if language_normalized == "multilingual":
            return language_normalized

        # Validate ISO-639-1 format (2-letter code)
        if not re.match(r"^[a-z]{2}$", language_normalized):
            raise ProviderError(
                f"Cartesia only accepts ISO-639-1 (2-letter) language codes.\n"
                f"Got: '{language}'\n"
                f"Valid examples: 'en', 'es', 'fr', 'de', 'ja', 'zh'\n"
                f"Use 'multilingual' for auto-detection",
                provider="cartesia",
            )

        return language_normalized

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "X-API-Key": self._api_key,
                    "Cartesia-Version": self.API_VERSION,
                },
                timeout=120.0,
            )
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def speech_to_text(
        self,
        audio: bytes,
        model: str | None = None,
        language: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Transcribe audio using HTTP API.

        Args:
            audio: Audio bytes
            model: Model ID (default: ink-whisper)
            language: Language code (e.g., "en")
            **kwargs: Additional options (timestamp_granularities, etc.)

        Returns:
            Transcribed text
        """
        model = model or self.DEFAULT_MODEL
        language = self.validate_language(language)

        client = await self._get_http_client()

        # Build multipart form data
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data: dict[str, Any] = {
            "model": model,
            "language": language,
        }

        # Add optional parameters
        if "timestamp_granularities" in kwargs:
            data["timestamp_granularities[]"] = kwargs["timestamp_granularities"]

        try:
            response = await client.post("/stt", files=files, data=data)
            response.raise_for_status()

            result = response.json()
            return result.get("text", "")

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

    async def speech_to_text_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        model: str | None = None,
        language: str | None = None,
        interim_results: bool = False,
        deduplicate: bool = True,
        **kwargs: Any,
    ) -> AsyncIterator[ASRResult]:
        """
        Stream audio to text using WebSocket API.

        Args:
            audio_stream: Async iterator of audio chunks (PCM)
            model: Model ID
            language: Language code
            interim_results: If False, only yield final transcripts.
                           If True, yield both interim and final (marked with is_final flag)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
            **kwargs: Additional options (encoding, sample_rate, etc.)

        Yields:
            ASRResult objects with text and is_final flag
        """
        model = model or self.DEFAULT_MODEL
        language = self.validate_language(language)
        encoding = kwargs.get("encoding", "pcm_s16le")
        sample_rate = kwargs.get("sample_rate", 16000)
        min_volume = kwargs.get("min_volume", 0.1)
        max_silence_duration = kwargs.get("max_silence_duration_secs", 1.5)

        # Normalize encoding - Cartesia uses specific encoding names
        # Map common encoding names to Cartesia's expected values
        if encoding in ("linear16", "pcm"):
            encoding = "pcm_s16le"

        # Build WebSocket URL (API key goes in headers, not URL)
        params = [
            f"model={model}",
            f"language={language}",
            f"encoding={encoding}",
            f"sample_rate={sample_rate}",
            f"min_volume={min_volume}",
            f"max_silence_duration_secs={max_silence_duration}",
        ]

        ws_url = f"{self.WS_URL}/stt/websocket?{'&'.join(params)}"

        # Authentication headers (same as HTTP API)
        headers = {
            "X-API-Key": self._api_key,
            "Cartesia-Version": self.API_VERSION,
        }

        logger.debug(f"Connecting to Cartesia WebSocket: {ws_url}")
        logger.debug(f"Audio format: encoding={encoding}, sample_rate={sample_rate}")
        redacted_headers = {k: "REDACTED" if k == "X-API-Key" else v for k, v in headers.items()}
        logger.debug(f"Headers: {redacted_headers}")

        try:
            async with websockets.connect(ws_url, additional_headers=headers) as ws:
                logger.debug("WebSocket connected successfully")
                result_queue: asyncio.Queue[ASRResult | None] = asyncio.Queue()
                last_text = ""

                async def send_audio() -> None:
                    """Send audio chunks to WebSocket."""
                    try:
                        logger.debug("Starting to send audio chunks...")
                        chunk_count = 0
                        total_bytes = 0
                        async for chunk in audio_stream:
                            if chunk:
                                chunk_count += 1
                                total_bytes += len(chunk)
                                logger.debug(f"Sending audio chunk {chunk_count} ({len(chunk)} bytes, total: {total_bytes} bytes)")
                                # Send raw audio bytes
                                await ws.send(chunk)

                        # Send finalize command
                        logger.debug(f"Sent {chunk_count} audio chunks ({total_bytes} bytes total), sending finalize")
                        await ws.send("finalize")
                        await ws.send("done")
                        logger.debug("Finalize and done sent")
                    except Exception as e:
                        logger.error(f"Error in send_audio: {e}")
                        await result_queue.put(None)
                        raise

                async def receive_text() -> None:
                    """Receive transcription from WebSocket."""
                    nonlocal last_text
                    try:
                        logger.debug("Starting to receive messages from WebSocket...")
                        message_count = 0
                        async for message in ws:
                            message_count += 1
                            # Skip binary messages
                            if isinstance(message, bytes):
                                logger.debug(f"Received binary message {message_count} ({len(message)} bytes), skipping")
                                continue

                            logger.debug(f"Received message {message_count}: {message[:300] if len(message) > 300 else message}")
                            data = json.loads(message)

                            msg_type = data.get("type")
                            logger.debug(f"Message type: {msg_type}")

                            if msg_type == "transcript":
                                text = data.get("text", "")
                                is_final = data.get("is_final", False)
                                logger.debug(f"Transcript: '{text}' (final={is_final}, interim_results={interim_results})")

                                if text:
                                    should_emit = True
                                    if deduplicate and text == last_text:
                                        should_emit = False
                                        logger.debug("Transcript unchanged, skipping (deduplicate=True)")

                                    if should_emit and (interim_results or is_final):
                                        logger.debug(f"Putting in queue: '{text}' (is_final={is_final})")
                                        await result_queue.put(ASRResult(text=text, is_final=is_final))

                                    if deduplicate:
                                        if is_final:
                                            last_text = ""
                                        else:
                                            last_text = text

                            elif msg_type == "flush_done":
                                logger.debug("Flush done received")
                                continue

                            elif msg_type == "error":
                                error_msg = data.get('message', 'Unknown')
                                logger.error(f"Cartesia error: {error_msg}")
                                raise StreamingError(f"Cartesia error: {error_msg}")

                        logger.debug(f"WebSocket message loop ended. Received {message_count} messages total")
                        await result_queue.put(None)
                    except Exception as e:
                        logger.error(f"Error in receive_text: {e}", exc_info=True)
                        await result_queue.put(None)
                        raise

                send_task = asyncio.create_task(send_audio())
                receive_task = asyncio.create_task(receive_text())

                logger.debug("Starting main yield loop...")
                try:
                    yield_count = 0
                    while True:
                        logger.debug("Waiting for result from queue...")
                        result = await result_queue.get()
                        if result is None:
                            logger.debug("Received None from queue, ending stream")
                            break
                        yield_count += 1
                        logger.debug(f"YIELDING result {yield_count}: text='{result.text}' is_final={result.is_final}")
                        yield result
                    logger.debug(f"Yielded {yield_count} results total")
                finally:
                    logger.debug("Cleaning up tasks...")
                    send_task.cancel()
                    receive_task.cancel()
                    try:
                        await send_task
                    except asyncio.CancelledError:
                        logger.debug("send_task cancelled")
                    try:
                        await receive_task
                    except asyncio.CancelledError:
                        logger.debug("receive_task cancelled")

        except websockets.exceptions.WebSocketException as e:
            logger.error(f"WebSocket exception: {e}")
            raise StreamingError(f"Cartesia WebSocket error: {str(e)}")
        except Exception as e:
            logger.error(f"Streaming exception: {e}", exc_info=True)
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"Cartesia streaming error: {str(e)}")
