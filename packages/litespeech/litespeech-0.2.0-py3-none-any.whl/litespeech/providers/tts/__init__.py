"""TTS provider implementations."""

from litespeech.providers.tts.elevenlabs import ElevenLabsTTSProvider
from litespeech.providers.tts.deepgram import DeepgramTTSProvider
from litespeech.providers.tts.cartesia import CartesiaTTSProvider
from litespeech.providers.tts.openai import OpenAITTSProvider

# Azure is an optional dependency
try:
    from litespeech.providers.tts.azure import AzureTTSProvider
except ImportError:
    AzureTTSProvider = None  # type: ignore
    import warnings
    warnings.warn(
        "Azure Speech SDK not installed. Azure TTS provider will not be available. "
        "Install with: pip install litespeech[azure]",
        ImportWarning,
        stacklevel=2
    )

__all__ = [
    "ElevenLabsTTSProvider",
    "DeepgramTTSProvider",
    "CartesiaTTSProvider",
    "OpenAITTSProvider",
    "AzureTTSProvider",
]
