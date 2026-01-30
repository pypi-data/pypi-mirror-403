"""ASR provider implementations."""

# Try to import each provider, skip if dependencies not installed

try:
    from litespeech.providers.asr.deepgram import DeepgramASRProvider
except ImportError:
    DeepgramASRProvider = None  # type: ignore

try:
    from litespeech.providers.asr.elevenlabs import ElevenLabsASRProvider
except ImportError:
    ElevenLabsASRProvider = None  # type: ignore

try:
    from litespeech.providers.asr.cartesia import CartesiaASRProvider
except ImportError:
    CartesiaASRProvider = None  # type: ignore

try:
    from litespeech.providers.asr.openai import OpenAIASRProvider
except ImportError:
    OpenAIASRProvider = None  # type: ignore

try:
    from litespeech.providers.asr.azure import AzureASRProvider
except ImportError:
    AzureASRProvider = None  # type: ignore
    import warnings
    warnings.warn(
        "Azure Speech SDK not installed. Azure ASR provider will not be available. "
        "Install with: pip install litespeech[azure]",
        ImportWarning,
        stacklevel=2
    )

__all__ = [
    "DeepgramASRProvider",
    "ElevenLabsASRProvider",
    "CartesiaASRProvider",
    "OpenAIASRProvider",
    "AzureASRProvider",
]
