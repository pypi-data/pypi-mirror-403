"""
LiteSpeech - Unified SDK for speech operations (ASR/TTS).

Provides a consistent interface across multiple providers with first-class
support for streaming and real-time conversational AI pipelines.
"""

# Setup logging first (reads LITESPEECH_LOG_LEVEL environment variable)
from litespeech.utils import debug  # noqa: F401

from litespeech.client import LiteSpeech
from litespeech.version import __version__
from litespeech.providers.base import ASRResult
from litespeech.exceptions import (
    LiteSpeechError,
    ProviderError,
    StreamingError,
    AudioFormatError,
    AuthenticationError,
    ProviderNotFoundError,
    UnsupportedOperationError,
)

__all__ = [
    "LiteSpeech",
    "__version__",
    "ASRResult",
    "LiteSpeechError",
    "ProviderError",
    "StreamingError",
    "AudioFormatError",
    "AuthenticationError",
    "ProviderNotFoundError",
    "UnsupportedOperationError",
]
