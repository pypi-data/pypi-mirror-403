"""Custom exceptions for LiteSpeech."""

from typing import Any


class LiteSpeechError(Exception):
    """Base exception for LiteSpeech."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProviderError(LiteSpeechError):
    """Provider-specific error."""

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, details)
        self.provider = provider
        self.status_code = status_code


class StreamingError(LiteSpeechError):
    """Streaming-related error."""

    pass


class AudioFormatError(LiteSpeechError):
    """Audio format/conversion error."""

    pass


class AuthenticationError(LiteSpeechError):
    """API key/authentication error."""

    def __init__(self, provider: str, message: str | None = None):
        msg = message or f"Authentication failed for provider: {provider}"
        super().__init__(msg)
        self.provider = provider


class ProviderNotFoundError(LiteSpeechError):
    """Provider not found in registry."""

    def __init__(self, provider: str):
        super().__init__(f"Provider not found: {provider}")
        self.provider = provider


class UnsupportedOperationError(LiteSpeechError):
    """Operation not supported by provider."""

    def __init__(self, provider: str, operation: str):
        super().__init__(f"Provider '{provider}' does not support operation: {operation}")
        self.provider = provider
        self.operation = operation
