"""ElevenLabs ASR provider implementation."""

import asyncio
import base64
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


class ElevenLabsASRProvider(ASRProvider):
    """
    ElevenLabs ASR provider with WebSocket streaming support.

    Features:
    - True streaming: audio-in, text-out via WebSocket
    - Batch transcription via HTTP API
    - Scribe model with diarization support
    """

    BASE_URL = "https://api.elevenlabs.io"
    WS_URL = "wss://api.elevenlabs.io"

    # Different models for batch vs streaming
    DEFAULT_BATCH_MODEL = "scribe_v1"
    DEFAULT_STREAMING_MODEL = "scribe_v2_realtime"

    # Model categorization
    BATCH_ONLY_MODELS = {"scribe_v1", "scribe_v1_experimental"}
    STREAMING_ONLY_MODELS = {"scribe_v2_realtime"}

    def __init__(self, elevenlabs_api_key: str | None = None, **kwargs):
        """
        Initialize ElevenLabs ASR provider.

        Args:
            elevenlabs_api_key: ElevenLabs API key (defaults to ELEVENLABS_API_KEY env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = elevenlabs_api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self._api_key:
            raise AuthenticationError("elevenlabs", "ELEVENLABS_API_KEY not set")
        self._http_client: httpx.AsyncClient | None = None

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="elevenlabs",
            display_name="ElevenLabs",
            capabilities=ProviderCapabilities(
                tts_batch=False,
                tts_streaming=False,
                asr_batch=True,
                asr_streaming=True,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_STREAMING_MODEL,
            supported_models=[
                "scribe_v1",  # Batch only
                "scribe_v1_experimental",  # Batch only
                "scribe_v2_realtime",  # Streaming only
            ],
        )

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict[str, Any]:
        """Get audio specs for ElevenLabs."""
        return {
            "preferred": {"format": "wav"},
            "recommended_sample_rate": 16000,
        }

    def validate_language(self, language: str | None) -> str | None:
        """
        Validate language code for ElevenLabs.

        ElevenLabs accepts:
        - ISO-639-1 (2-letter) codes: 'en', 'es', 'fr', etc.
        - ISO-639-3 (3-letter) codes: 'eng', 'spa', 'fra', etc.
        - None for auto-detection (90+ languages)

        Returns:
            Validated language code or None (auto-detection)
        """
        import re

        # None means auto-detection
        if language is None:
            return None

        language_normalized = language.lower().strip()

        # Validate formats
        iso_639_1 = re.compile(r"^[a-z]{2}$")  # en, es, fr
        iso_639_3 = re.compile(r"^[a-z]{3}$")  # eng, spa, fra

        if iso_639_1.match(language_normalized) or iso_639_3.match(language_normalized):
            return language_normalized

        # Invalid format
        raise ProviderError(
            f"ElevenLabs accepts ISO-639-1 or ISO-639-3 language codes.\n"
            f"Got: '{language}'\n"
            f"Valid examples: 'en', 'eng', 'es', 'spa'\n"
            f"Omit language parameter for auto-detection",
            provider="elevenlabs",
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"xi-api-key": self._api_key},
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
        Transcribe audio using HTTP API (batch mode).

        Args:
            audio: Audio bytes
            model: Model ID (default: scribe_v1)
            language: Language code (e.g., "en")
            **kwargs: Additional options (diarize, tag_audio_events, etc.)

        Returns:
            Transcribed text
        """
        model = model or self.DEFAULT_BATCH_MODEL

        # Validate model is suitable for batch mode
        if model in self.STREAMING_ONLY_MODELS:
            raise ProviderError(
                f"Model '{model}' is only available for streaming (WebSocket) mode.\n"
                f"For batch transcription, use: {', '.join(self.BATCH_ONLY_MODELS)}\n"
                f"Or call speech_to_text_stream() instead of speech_to_text()",
                provider="elevenlabs",
            )

        language = self.validate_language(language)

        client = await self._get_http_client()

        # Build multipart form data
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data: dict[str, Any] = {"model_id": model}

        if language:
            data["language_code"] = language

        # Add optional parameters
        for opt in ["diarize", "tag_audio_events", "num_speakers", "timestamps_granularity"]:
            if opt in kwargs:
                data[opt] = kwargs[opt]

        try:
            response = await client.post(
                "/v1/speech-to-text",
                files=files,
                data=data,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("text", "")

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
        Stream audio to text using WebSocket API (real-time mode).

        Args:
            audio_stream: Async iterator of audio chunks (PCM 16-bit)
            model: Model ID (default: scribe_v2_realtime)
            language: Language code
            interim_results: Whether to yield partial results (if False, only final results)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
            **kwargs: Additional options (audio_format, sample_rate, etc.)

        Yields:
            ASRResult objects with text and is_final flag
        """
        model = model or self.DEFAULT_STREAMING_MODEL

        # Validate model is suitable for streaming mode
        if model in self.BATCH_ONLY_MODELS:
            raise ProviderError(
                f"Model '{model}' is only available for batch (HTTP) mode.\n"
                f"For real-time streaming, use: {', '.join(self.STREAMING_ONLY_MODELS)}\n"
                f"Or call speech_to_text() for batch transcription instead.\n"
                f"Fix: Change provider=\"elevenlabs/{model}\" to provider=\"elevenlabs\" (uses {self.DEFAULT_STREAMING_MODEL})",
                provider="elevenlabs",
            )

        language = self.validate_language(language)

        sample_rate = kwargs.get("sample_rate", 16000)

        # ElevenLabs uses audio_format like "pcm_16000", "pcm_44100", etc.
        # If user provides encoding (like "linear16"), convert to audio_format
        encoding = kwargs.get("encoding", "linear16")

        # Map encoding + sample_rate to ElevenLabs audio_format
        if "audio_format" in kwargs:
            # User provided explicit audio_format
            audio_format = kwargs["audio_format"]
        else:
            # Build audio_format from encoding and sample_rate
            # ElevenLabs format: "pcm_SAMPLERATE"
            if encoding in ("linear16", "pcm", "pcm_s16le"):
                audio_format = f"pcm_{sample_rate}"
            elif encoding == "mulaw":
                audio_format = f"mulaw_{sample_rate}"
            else:
                # Default
                audio_format = f"pcm_{sample_rate}"

        # Build WebSocket URL
        params = [
            f"model_id={model}",
            f"audio_format={audio_format}",
        ]

        if language:
            params.append(f"language_code={language}")

        # Commit strategy: "manual" or "vad"
        commit_strategy = "vad" if kwargs.get("use_vad", True) else "manual"
        params.append(f"commit_strategy={commit_strategy}")

        if kwargs.get("include_timestamps", False):
            params.append("include_timestamps=true")

        ws_url = f"{self.WS_URL}/v1/speech-to-text/realtime?{'&'.join(params)}"

        logger.debug(f"Connecting to ElevenLabs WebSocket: {ws_url}")
        logger.debug(f"Audio format: {audio_format}, Sample rate: {sample_rate}")

        try:
            async with websockets.connect(
                ws_url,
                additional_headers={"xi-api-key": self._api_key},
            ) as ws:
                logger.debug("WebSocket connected successfully")
                result_queue: asyncio.Queue[ASRResult | None] = asyncio.Queue()
                last_text = ""

                async def send_audio() -> None:
                    """Send audio chunks to WebSocket."""
                    try:
                        chunk_count = 0
                        async for chunk in audio_stream:
                            if chunk:
                                chunk_count += 1
                                # Send audio as base64 encoded
                                message = {
                                    "message_type": "input_audio_chunk",
                                    "audio_base_64": base64.b64encode(chunk).decode(),
                                    "sample_rate": sample_rate,
                                }
                                if chunk_count == 1:
                                    logger.debug(f"Sending first audio chunk message: {json.dumps({k: v[:50] if k == 'audio_base_64' else v for k, v in message.items()})}")
                                await ws.send(json.dumps(message))

                        # Commit final audio
                        await ws.send(json.dumps({
                            "message_type": "input_audio_chunk",
                            "audio_base_64": "",
                            "commit": True,
                        }))
                    except Exception:
                        await result_queue.put(None)
                        raise

                async def receive_text() -> None:
                    """Receive transcription from WebSocket."""
                    nonlocal last_text
                    try:
                        async for message in ws:
                            data = json.loads(message)

                            msg_type = data.get("message_type")

                            if msg_type == "invalid_request":
                                error_msg = data.get("error", "Unknown error")
                                logger.error(f"ElevenLabs invalid_request: {error_msg}")
                                raise StreamingError(f"ElevenLabs invalid_request: {error_msg}")

                            elif msg_type == "partial_transcript":
                                if interim_results:
                                    text = data.get("text", "")
                                    if text:
                                        should_emit = True
                                        if deduplicate and text == last_text:
                                            should_emit = False
                                        if should_emit:
                                            await result_queue.put(ASRResult(text=text, is_final=False))
                                            if deduplicate:
                                                last_text = text

                            elif msg_type == "committed_transcript":
                                text = data.get("text", "")
                                if text:
                                    should_emit = True
                                    if deduplicate and text == last_text:
                                        should_emit = False
                                    if should_emit:
                                        await result_queue.put(ASRResult(text=text, is_final=True))
                                        if deduplicate:
                                            last_text = ""

                            elif msg_type == "committed_transcript_with_timestamps":
                                text = data.get("text", "")
                                if text:
                                    should_emit = True
                                    if deduplicate and text == last_text:
                                        should_emit = False
                                    if should_emit:
                                        await result_queue.put(ASRResult(text=text, is_final=True))
                                        if deduplicate:
                                            last_text = ""

                            elif msg_type == "session_started":
                                continue

                            elif msg_type in ("auth_error", "quota_exceeded", "rate_limited"):
                                raise StreamingError(f"ElevenLabs error: {msg_type}")

                        await result_queue.put(None)
                    except Exception:
                        await result_queue.put(None)
                        raise

                send_task = asyncio.create_task(send_audio())
                receive_task = asyncio.create_task(receive_text())

                try:
                    while True:
                        result = await result_queue.get()
                        if result is None:
                            break
                        yield result
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
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"ElevenLabs streaming error: {str(e)}")
