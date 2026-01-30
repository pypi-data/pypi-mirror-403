"""Base provider interface for LiteSpeech."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class ConnectionType(str, Enum):
    """Connection type for provider implementation."""

    SDK = "sdk"
    WEBSOCKET = "websocket"
    HTTP = "http"


@dataclass
class ProviderCapabilities:
    """Capabilities of a provider."""

    tts_batch: bool = False
    tts_streaming: bool = False
    asr_batch: bool = False
    asr_streaming: bool = False


@dataclass
class ProviderInfo:
    """Information about a provider."""

    name: str
    display_name: str
    capabilities: ProviderCapabilities
    connection_type: ConnectionType = ConnectionType.HTTP
    default_model: str | None = None
    default_voice: str | None = None
    supported_models: list[str] = field(default_factory=list)
    supported_voices: list[str] = field(default_factory=list)


@dataclass
class ASRResult:
    """Result from speech-to-text streaming."""

    text: str
    is_final: bool


class BaseProvider(ABC):
    """
    Abstract base class for all providers.

    Each provider must implement:
    - Provider info with capability flags
    - API client initialization
    - TTS/ASR methods (batch and/or streaming)

    Each provider handles its own credential management:
    - Accepts provider-specific parameters in __init__
    - Falls back to environment variables if parameters not provided
    - Validates its own requirements and raises AuthenticationError if needed
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize provider with API key.

        Args:
            api_key: API key for the provider (falls back to environment variable)
        """
        self._api_key = api_key

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Get provider information and capabilities."""
        pass

    @property
    def name(self) -> str:
        """Get provider name."""
        return self.info.name

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        return self.info.capabilities

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict[str, Any]:
        """
        Get audio format specifications for this provider/model.

        Override this to specify preferred/recommended audio formats.
        Used for format validation and conversion.

        NOTE: This is a classmethod so it can be called without instantiation.

        Args:
            model: Optional model ID to get model-specific specs

        Returns:
            Dict with audio specs, e.g.:
            {
                "preferred": {"format": "wav", "sample_rate": 16000},
                "recommended_sample_rate": 16000,
                "supported_formats": ["wav", "mp3"],
            }
        """
        return {}

    async def close(self) -> None:
        """Close any open connections. Override if needed."""
        pass

    async def __aenter__(self) -> "BaseProvider":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class TTSProvider(BaseProvider):
    """Base class for Text-to-Speech providers."""

    @abstractmethod
    async def text_to_speech(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech (batch mode).

        Args:
            text: Text to convert
            model: Model ID to use
            voice: Voice ID to use
            output_format: Output audio format
            **kwargs: Additional provider-specific options

        Returns:
            Audio bytes
        """
        pass

    @abstractmethod
    async def text_to_speech_stream(
        self,
        text_stream: AsyncIterator[str],
        model: str | None = None,
        voice: str | None = None,
        output_format: str = "pcm_16000",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Convert text stream to speech stream.

        Args:
            text_stream: Async iterator of text chunks
            model: Model ID to use
            voice: Voice ID to use
            output_format: Output audio format (raw PCM recommended for streaming)
            **kwargs: Additional provider-specific options

        Yields:
            Audio chunks
        """
        pass


class ASRProvider(BaseProvider):
    """Base class for Automatic Speech Recognition providers."""

    @abstractmethod
    async def speech_to_text(
        self,
        audio: bytes,
        model: str | None = None,
        language: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Convert speech to text (batch mode).

        Args:
            audio: Audio bytes
            model: Model ID to use
            language: Language code (e.g., "en")
            **kwargs: Additional provider-specific options

        Returns:
            Transcribed text
        """
        pass

    @abstractmethod
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
        Convert speech stream to text stream.

        Args:
            audio_stream: Async iterator of audio chunks
            model: Model ID to use
            language: Language code
            interim_results: Whether to yield partial/interim results (if False, only final results)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
                        Set to False if you want every message from the provider
            **kwargs: Additional provider-specific options

        Yields:
            ASRResult objects with text and is_final flag
        """
        pass

    def validate_language(self, language: str | None) -> str | None:
        """
        Validate and normalize language code for this provider.

        Override this method in provider implementations to:
        - Validate language code format (ISO-639-1, ISO-639-3, BCP-47, etc.)
        - Set default language when None is provided
        - Raise ProviderError for invalid codes

        Default implementation: No validation, returns language as-is.

        Args:
            language: Language code to validate (can be None)

        Returns:
            Validated/normalized language code, or None

        Raises:
            ProviderError: If language code is invalid for this provider
        """
        return language


class FullProvider(TTSProvider, ASRProvider):
    """Base class for providers that support both TTS and ASR."""

    pass
