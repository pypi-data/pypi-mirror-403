"""OpenAI TTS provider implementation."""

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from litespeech.providers.base import (
    TTSProvider,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, UnsupportedOperationError


class OpenAITTSProvider(TTSProvider):
    """
    OpenAI TTS provider (batch only, no streaming support).

    Features:
    - Batch TTS via HTTP API
    - Multiple voice options
    - HD model available
    """

    BASE_URL = "https://api.openai.com"

    DEFAULT_MODEL = "tts-1"
    DEFAULT_VOICE = "alloy"

    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, openai_api_key: str | None = None, **kwargs):
        """
        Initialize OpenAI TTS provider.

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "openai",
                "openai_api_key must be provided or OPENAI_API_KEY env var must be set"
            )
        self._http_client: httpx.AsyncClient | None = None

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="openai",
            display_name="OpenAI TTS",
            capabilities=ProviderCapabilities(
                tts_batch=True,
                tts_streaming=False,  # OpenAI TTS does not support true streaming
                asr_batch=False,
                asr_streaming=False,
            ),
            connection_type=ConnectionType.HTTP,
            default_model=self.DEFAULT_MODEL,
            default_voice=self.DEFAULT_VOICE,
            supported_models=["tts-1", "tts-1-hd"],
            supported_voices=self.VOICES,
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
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
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech using HTTP API.

        Args:
            text: Text to convert (max 4096 characters)
            model: Model ID (tts-1 or tts-1-hd)
            voice: Voice name (alloy, echo, fable, onyx, nova, shimmer)
            language: Language code (ignored by OpenAI - language detected from text)
            output_format: Output format (mp3, opus, aac, flac, wav, pcm)
            **kwargs: Additional options (speed)

        Returns:
            Audio bytes
        """
        model = model or self.DEFAULT_MODEL
        voice = voice or self.DEFAULT_VOICE
        # Note: OpenAI TTS doesn't use language parameter - it auto-detects from text

        client = await self._get_http_client()

        payload: dict[str, Any] = {
            "model": model,
            "input": text,
            "voice": voice,
            "response_format": output_format,
        }

        # Add optional speed parameter
        if "speed" in kwargs:
            payload["speed"] = kwargs["speed"]

        try:
            response = await client.post("/v1/audio/speech", json=payload)
            response.raise_for_status()
            return response.content

        except httpx.HTTPStatusError as e:
            raise ProviderError(
                f"OpenAI API error: {e.response.text}",
                provider="openai",
                status_code=e.response.status_code,
            )
        except httpx.RequestError as e:
            raise ProviderError(
                f"OpenAI request error: {str(e)}",
                provider="openai",
            )

    async def text_to_speech_stream(
        self,
        text_stream: AsyncIterator[str],
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "pcm",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        OpenAI TTS does not support true streaming.

        This method raises UnsupportedOperationError.
        Use text_to_speech() for batch conversion.
        """
        raise UnsupportedOperationError(
            provider="openai",
            operation="tts_streaming",
        )
        # This is needed to make the type checker happy
        yield b""  # pragma: no cover
