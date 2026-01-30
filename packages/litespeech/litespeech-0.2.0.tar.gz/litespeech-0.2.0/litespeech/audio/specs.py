"""Provider audio specifications."""

from typing import Any, TypedDict


class AudioSpec(TypedDict, total=False):
    """Audio specification for a provider."""

    formats: list[str]
    sample_rates: list[int] | str
    channels: str
    encoding: str
    max_size: int
    preferred: dict[str, Any]
    output_formats: list[str]
    streaming_format: str
    recommended_sample_rate: int
    recommended_channels: int
    supported_formats: list[str]


def get_provider_spec(provider_model: str) -> AudioSpec | None:
    """
    Get audio specification for a provider/model combination.

    Calls the provider's get_audio_specs() classmethod dynamically.

    Args:
        provider_model: Provider and model string (e.g., "deepgram/nova-2")

    Returns:
        AudioSpec dict or None if provider not found
    """
    from litespeech.providers.registry import get_registry

    registry = get_registry()
    provider_name = provider_model.split("/")[0]
    model = provider_model.split("/")[1] if "/" in provider_model else None

    # Try TTS providers first
    provider_class = registry._tts_providers.get(provider_name.lower())
    # If not found, try ASR providers
    if not provider_class:
        provider_class = registry._asr_providers.get(provider_name.lower())

    if provider_class:
        return provider_class.get_audio_specs(model)  # type: ignore

    return None
