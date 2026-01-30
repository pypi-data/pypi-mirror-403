"""Provider registry for LiteSpeech."""

from dataclasses import dataclass
from typing import Type

from litespeech.providers.base import (
    BaseProvider,
    TTSProvider,
    ASRProvider,
)
from litespeech.exceptions import ProviderNotFoundError
from litespeech.utils.logging import get_logger


@dataclass
class ParsedProviderString:
    """Parsed provider string components."""

    provider: str
    model: str | None = None
    voice: str | None = None


def parse_provider_string(provider_str: str) -> ParsedProviderString:
    """
    Parse provider string into components.

    Format: provider/model[/voice]

    Examples:
        - "elevenlabs/eleven_turbo_v2_5/adam" -> provider=elevenlabs, model=eleven_turbo_v2_5, voice=adam
        - "deepgram/nova-2" -> provider=deepgram, model=nova-2, voice=None
        - "openai" -> provider=openai, model=None, voice=None

    Args:
        provider_str: Provider string in format "provider/model[/voice]"

    Returns:
        ParsedProviderString with extracted components
    """
    parts = provider_str.split("/")
    return ParsedProviderString(
        provider=parts[0].lower(),
        model=parts[1] if len(parts) > 1 else None,
        voice=parts[2] if len(parts) > 2 else None,
    )


class ProviderRegistry:
    """
    Central registry for provider discovery and routing.

    The registry ONLY handles:
    - Registration of provider classes
    - Routing provider names to provider classes

    All credential management is handled by individual providers.
    """

    def __init__(self) -> None:
        self._tts_providers: dict[str, Type[TTSProvider]] = {}
        self._asr_providers: dict[str, Type[ASRProvider]] = {}
        self._logger = get_logger()

    def register_tts(self, name: str, provider_class: Type[TTSProvider]) -> None:
        """
        Register a TTS provider.

        Args:
            name: Provider name (e.g., "elevenlabs")
            provider_class: Provider class to register
        """
        self._tts_providers[name.lower()] = provider_class
        self._logger.debug(f"Registered TTS provider: {name}")

    def register_asr(self, name: str, provider_class: Type[ASRProvider]) -> None:
        """
        Register an ASR provider.

        Args:
            name: Provider name (e.g., "deepgram")
            provider_class: Provider class to register
        """
        self._asr_providers[name.lower()] = provider_class
        self._logger.debug(f"Registered ASR provider: {name}")

    def get_tts_provider_class(self, provider_str: str) -> Type[TTSProvider]:
        """
        Get TTS provider class by provider string.

        Args:
            provider_str: Provider string (e.g., "elevenlabs/eleven_turbo_v2_5")

        Returns:
            TTSProvider class

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        parsed = parse_provider_string(provider_str)
        provider_name = parsed.provider.lower()

        if provider_name not in self._tts_providers:
            raise ProviderNotFoundError(f"TTS provider not found: {provider_name}")

        return self._tts_providers[provider_name]

    def get_asr_provider_class(self, provider_str: str) -> Type[ASRProvider]:
        """
        Get ASR provider class by provider string.

        Args:
            provider_str: Provider string (e.g., "deepgram/nova-2")

        Returns:
            ASRProvider class

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        parsed = parse_provider_string(provider_str)
        provider_name = parsed.provider.lower()

        if provider_name not in self._asr_providers:
            raise ProviderNotFoundError(f"ASR provider not found: {provider_name}")

        return self._asr_providers[provider_name]

    def supports_tts_streaming(self, provider_str: str) -> bool:
        """Check if provider supports streaming TTS."""
        try:
            provider_class = self.get_tts_provider_class(provider_str)
            # Instantiate with empty kwargs to check capabilities
            provider = provider_class(**{})
            return provider.capabilities.tts_streaming
        except (ProviderNotFoundError, Exception):
            return False

    def supports_tts_batch(self, provider_str: str) -> bool:
        """Check if provider supports batch TTS."""
        try:
            provider_class = self.get_tts_provider_class(provider_str)
            provider = provider_class(**{})
            return provider.capabilities.tts_batch
        except (ProviderNotFoundError, Exception):
            return False

    def supports_asr_streaming(self, provider_str: str) -> bool:
        """Check if provider supports streaming ASR."""
        try:
            provider_class = self.get_asr_provider_class(provider_str)
            provider = provider_class(**{})
            return provider.capabilities.asr_streaming
        except (ProviderNotFoundError, Exception):
            return False

    def supports_asr_batch(self, provider_str: str) -> bool:
        """Check if provider supports batch ASR."""
        try:
            provider_class = self.get_asr_provider_class(provider_str)
            provider = provider_class(**{})
            return provider.capabilities.asr_batch
        except (ProviderNotFoundError, Exception):
            return False

    def list_tts_providers(self) -> list[str]:
        """List all registered TTS providers."""
        return list(self._tts_providers.keys())

    def list_asr_providers(self) -> list[str]:
        """List all registered ASR providers."""
        return list(self._asr_providers.keys())


# Global registry instance
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry, creating if necessary."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
        _register_builtin_providers(_registry)
    return _registry


def _register_builtin_providers(registry: ProviderRegistry) -> None:
    """Register all built-in providers."""
    # Import and register providers
    # TTS providers
    try:
        from litespeech.providers.tts.elevenlabs import ElevenLabsTTSProvider

        registry.register_tts("elevenlabs", ElevenLabsTTSProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.tts.deepgram import DeepgramTTSProvider

        registry.register_tts("deepgram", DeepgramTTSProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.tts.cartesia import CartesiaTTSProvider

        registry.register_tts("cartesia", CartesiaTTSProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.tts.openai import OpenAITTSProvider

        registry.register_tts("openai", OpenAITTSProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.tts.azure import AzureTTSProvider

        registry.register_tts("azure", AzureTTSProvider)
    except ImportError:
        pass

    # ASR providers
    try:
        from litespeech.providers.asr.deepgram import DeepgramASRProvider

        registry.register_asr("deepgram", DeepgramASRProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.asr.elevenlabs import ElevenLabsASRProvider

        registry.register_asr("elevenlabs", ElevenLabsASRProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.asr.cartesia import CartesiaASRProvider

        registry.register_asr("cartesia", CartesiaASRProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.asr.openai import OpenAIASRProvider

        registry.register_asr("openai", OpenAIASRProvider)
    except ImportError:
        pass

    try:
        from litespeech.providers.asr.azure import AzureASRProvider

        registry.register_asr("azure", AzureASRProvider)
    except ImportError:
        pass
