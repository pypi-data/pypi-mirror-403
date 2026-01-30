"""OpenAI ASR (Whisper) provider implementation."""

import os
from collections.abc import AsyncIterator
from typing import Any

import httpx

from litespeech.providers.base import (
    ASRProvider,
    ASRResult,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, UnsupportedOperationError


class OpenAIASRProvider(ASRProvider):
    """
    OpenAI Whisper ASR provider (batch only, no streaming support).

    Features:
    - Batch transcription via HTTP API
    - Multiple language support
    - Translation capability
    """

    BASE_URL = "https://api.openai.com"

    DEFAULT_MODEL = "whisper-1"

    def __init__(self, openai_api_key: str | None = None, **kwargs):
        """
        Initialize OpenAI ASR provider.

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
            display_name="OpenAI Whisper",
            capabilities=ProviderCapabilities(
                tts_batch=False,
                tts_streaming=False,
                asr_batch=True,
                asr_streaming=False,  # Whisper does not support streaming
            ),
            connection_type=ConnectionType.HTTP,
            default_model=self.DEFAULT_MODEL,
            supported_models=["whisper-1"],
        )

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict[str, Any]:
        """Get audio specs for OpenAI Whisper."""
        return {
            "preferred": {"format": "mp3"},  # OpenAI prefers MP3
            "recommended_sample_rate": 16000,
            "supported_formats": ["mp3", "wav", "m4a", "webm"],
        }

    def validate_language(self, language: str | None) -> str | None:
        """
        Validate language code for OpenAI Whisper.

        OpenAI Whisper accepts:
        - ISO-639-1 (2-letter) codes: 'en', 'es', 'fr', etc.
        - Some ISO-639-3 (3-letter) codes: 'eng', 'spa', etc.
        - None for auto-detection

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
            f"OpenAI Whisper requires ISO-639-1 (2-letter) language codes.\n"
            f"Got: '{language}'\n"
            f"Valid examples: 'en', 'es', 'fr', 'zh', 'ja'\n"
            f"Omit language parameter for auto-detection",
            provider="openai",
        )

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
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
        Transcribe audio using Whisper API.

        Args:
            audio: Audio bytes (max 25MB)
            model: Model ID (default: whisper-1)
            language: Language code in ISO-639-1 format
            **kwargs: Additional options (prompt, response_format, temperature)

        Returns:
            Transcribed text
        """
        model = model or self.DEFAULT_MODEL
        language = self.validate_language(language)

        client = await self._get_http_client()

        # Build multipart form data
        files = {"file": ("audio.mp3", audio, "audio/mpeg")}
        data: dict[str, Any] = {"model": model}

        if language:
            data["language"] = language

        # Add optional parameters
        if "prompt" in kwargs:
            data["prompt"] = kwargs["prompt"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]

        try:
            response = await client.post(
                "/v1/audio/transcriptions",
                files=files,
                data=data,
            )
            response.raise_for_status()

            # Response format depends on response_format parameter
            if kwargs.get("response_format") in ("json", "verbose_json", None):
                result = response.json()
                return result.get("text", "")
            else:
                return response.text

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

    async def translate(
        self,
        audio: bytes,
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Translate audio to English using Whisper API.

        Args:
            audio: Audio bytes (max 25MB)
            model: Model ID (default: whisper-1)
            **kwargs: Additional options (prompt, response_format, temperature)

        Returns:
            Translated English text
        """
        model = model or self.DEFAULT_MODEL

        client = await self._get_http_client()

        files = {"file": ("audio.mp3", audio, "audio/mpeg")}
        data: dict[str, Any] = {"model": model}

        # Add optional parameters
        if "prompt" in kwargs:
            data["prompt"] = kwargs["prompt"]
        if "response_format" in kwargs:
            data["response_format"] = kwargs["response_format"]
        if "temperature" in kwargs:
            data["temperature"] = kwargs["temperature"]

        try:
            response = await client.post(
                "/v1/audio/translations",
                files=files,
                data=data,
            )
            response.raise_for_status()

            if kwargs.get("response_format") in ("json", "verbose_json", None):
                result = response.json()
                return result.get("text", "")
            else:
                return response.text

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
        OpenAI Whisper does not support streaming.

        This method raises UnsupportedOperationError.
        Use speech_to_text() for batch transcription.
        """
        raise UnsupportedOperationError(
            provider="openai",
            operation="asr_streaming",
        )
        # This is needed to make the type checker happy
        yield ASRResult(text="", is_final=True)  # pragma: no cover
