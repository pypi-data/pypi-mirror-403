"""Deepgram ASR provider implementation."""

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator
from typing import Any

import httpx
import websockets

from litespeech.providers.base import (
    ASRProvider,
    ASRResult,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError

logger = logging.getLogger(__name__)


class DeepgramASRProvider(ASRProvider):
    """
    Deepgram ASR provider with WebSocket streaming support.

    Features:
    - True streaming: audio-in, text-out via WebSocket
    - Batch transcription via HTTP API
    - Multiple Nova models
    """

    BASE_URL = "https://api.deepgram.com"
    WS_URL = "wss://api.deepgram.com"

    DEFAULT_MODEL = "nova-2"

    def __init__(self, deepgram_api_key: str | None = None, **kwargs):
        """
        Initialize Deepgram ASR provider.

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
            display_name="Deepgram",
            capabilities=ProviderCapabilities(
                tts_batch=False,
                tts_streaming=False,
                asr_batch=True,
                asr_streaming=True,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            supported_models=[
                "nova-3",
                "nova-2",
                "nova-2-general",
                "nova-2-meeting",
                "nova-2-phonecall",
                "nova-2-medical",
                "enhanced",
                "base",
            ],
        )

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict[str, Any]:
        """Get audio specs for Deepgram."""
        return {
            "preferred": {"format": "wav"},
            "recommended_sample_rate": 16000,
        }

    def validate_language(self, language: str | None) -> str:
        """
        Validate language code for Deepgram.

        Deepgram accepts:
        - ISO-639-1 (2-letter) codes: 'en', 'es', 'fr', etc.
        - ISO-639-3 (3-letter) codes: 'eng', 'spa', 'fra', etc.
        - BCP-47 codes with dialect: 'en-US', 'es-MX', etc.
        - Special value: 'multi' for multilingual auto-detection

        Returns:
            Validated language code (defaults to 'multi' if None)
        """
        import re

        # Default to multi for multilingual if not specified
        if language is None:
            return "multi"

        # Preserve original for BCP-47 validation
        original_language = language
        language_normalized = language.lower().strip()

        # Allow special value
        if language_normalized == "multi":
            return language_normalized

        # Validate formats
        iso_639_1 = re.compile(r"^[a-z]{2}$")  # en, es, fr
        iso_639_3 = re.compile(r"^[a-z]{3}$")  # eng, spa, fra
        bcp_47 = re.compile(r"^[a-z]{2}-[A-Z]{2}$")  # en-US, es-MX

        # Check BCP-47 format (case-sensitive)
        if "-" in original_language:
            parts = original_language.split("-")
            if len(parts) == 2:
                lang_part = parts[0].lower()
                region_part = parts[1].upper()
                reconstructed = f"{lang_part}-{region_part}"
                if bcp_47.match(reconstructed):
                    return reconstructed

        # Check ISO formats
        if iso_639_1.match(language_normalized) or iso_639_3.match(language_normalized):
            return language_normalized

        # Invalid format
        raise ProviderError(
            f"Deepgram accepts ISO-639-1, ISO-639-3, or BCP-47 language codes.\n"
            f"Got: '{original_language}'\n"
            f"Valid examples: 'en', 'eng', 'en-US', 'es-MX'\n"
            f"Use 'multi' for multilingual auto-detection",
            provider="deepgram",
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Token {self._api_key}"},
                timeout=120.0,  # Longer timeout for transcription
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
            model: Model ID (default: nova-2)
            language: Language code (e.g., "en")
            **kwargs: Additional options (punctuate, diarize, smart_format, etc.)

        Returns:
            Transcribed text
        """
        model = model or self.DEFAULT_MODEL
        language = self.validate_language(language)

        client = await self._get_http_client()

        params: dict[str, Any] = {
            "model": model,
            "language": language,
        }

        # Add common options with defaults
        params["punctuate"] = kwargs.get("punctuate", True)
        params["smart_format"] = kwargs.get("smart_format", True)

        # Add optional parameters
        for opt in ["diarize", "detect_language", "paragraphs", "utterances", "encoding", "sample_rate"]:
            if opt in kwargs:
                params[opt] = kwargs[opt]

        try:
            response = await client.post(
                "/v1/listen",
                content=audio,
                params=params,
                headers={"Content-Type": "audio/wav"},  # Default, will be overridden if needed
            )
            response.raise_for_status()

            result = response.json()
            # Extract transcript from response
            channels = result.get("results", {}).get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
                if alternatives:
                    return alternatives[0].get("transcript", "")

            return ""

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
            audio_stream: Async iterator of audio chunks
            model: Model ID
            language: Language code
            interim_results: If False, only yield final transcripts.
                           If True, yield both interim and final (marked with is_final flag)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
            **kwargs: Additional options (encoding, sample_rate, channels, etc.)

        Yields:
            ASRResult objects with text and is_final flag
        """
        model = model or self.DEFAULT_MODEL
        language = self.validate_language(language)

        encoding = kwargs.get("encoding", "linear16")
        sample_rate = kwargs.get("sample_rate", 16000)
        channels = kwargs.get("channels", 1)

        # Build WebSocket URL with parameters
        params = [
            f"model={model}",
            f"encoding={encoding}",
            f"sample_rate={sample_rate}",
            f"channels={channels}",
            f"interim_results={str(interim_results).lower()}",
            "punctuate=true",
            "smart_format=true",
            f"language={language}",
        ]

        for opt in ["diarize", "vad_events", "endpointing"]:
            if opt in kwargs:
                params.append(f"{opt}={str(kwargs[opt]).lower()}")

        ws_url = f"{self.WS_URL}/v1/listen?{'&'.join(params)}"

        logger.debug(f"Connecting to Deepgram WebSocket: {ws_url}")
        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"Authorization": f"Token {self._api_key}"},
            ) as ws:
                logger.debug("WebSocket connected successfully")
                result_queue: asyncio.Queue[ASRResult | None] = asyncio.Queue()
                last_transcript = ""

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
                                await ws.send(chunk)

                        # Send close message
                        logger.debug(f"Sent {chunk_count} audio chunks ({total_bytes} bytes total), sending CloseStream")
                        await ws.send(json.dumps({"type": "CloseStream"}))
                        logger.debug("CloseStream sent")
                    except Exception as e:
                        logger.error(f"Error in send_audio: {e}")
                        await result_queue.put(None)
                        raise

                async def receive_text() -> None:
                    """Receive transcription from WebSocket."""
                    nonlocal last_transcript
                    try:
                        logger.debug("Starting to receive messages from WebSocket...")
                        message_count = 0
                        async for message in ws:
                            message_count += 1
                            logger.debug(f"Received message {message_count}: {message[:300] if len(message) > 300 else message}")
                            data = json.loads(message)

                            msg_type = data.get("type")
                            logger.debug(f"Message type: {msg_type}")

                            if msg_type == "Results":
                                channel = data.get("channel", {})
                                alternatives = channel.get("alternatives", [])
                                logger.debug(f"Results: {len(alternatives)} alternatives")

                                if alternatives:
                                    transcript = alternatives[0].get("transcript", "")
                                    is_final = data.get("is_final", False)
                                    logger.debug(f"Transcript: '{transcript}' (final={is_final}, interim_results={interim_results})")

                                    if transcript:
                                        if interim_results or is_final:
                                            # Conditionally deduplicate
                                            should_emit = True
                                            if deduplicate:
                                                if transcript != last_transcript:
                                                    logger.debug(f"NEW TRANSCRIPT! Putting in queue: '{transcript}' (is_final={is_final})")
                                                    if is_final:
                                                        last_transcript = ""
                                                    else:
                                                        last_transcript = transcript
                                                else:
                                                    logger.debug("Transcript unchanged, skipping (deduplicate=True)")
                                                    should_emit = False
                                            else:
                                                logger.debug(f"Putting in queue: '{transcript}' (is_final={is_final}, deduplicate=False)")

                                            if should_emit:
                                                await result_queue.put(ASRResult(text=transcript, is_final=is_final))
                                        else:
                                            logger.debug(f"Skipping interim result (interim_results={interim_results})")

                            elif msg_type == "Metadata":
                                logger.debug(f"Metadata: {data}")
                                continue
                            elif msg_type == "UtteranceEnd":
                                logger.debug("UtteranceEnd received")
                                # Reset for next utterance
                                last_transcript = ""

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
            raise StreamingError(f"Deepgram WebSocket error: {str(e)}")
        except Exception as e:
            logger.error(f"Streaming exception: {e}", exc_info=True)
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"Deepgram streaming error: {str(e)}")
