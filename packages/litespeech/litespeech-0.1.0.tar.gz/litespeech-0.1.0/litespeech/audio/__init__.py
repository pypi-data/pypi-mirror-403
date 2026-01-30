"""Audio processing utilities for LiteSpeech."""

from litespeech.audio.types import AudioFormat, AudioInfo
from litespeech.audio.specs import get_provider_spec
from litespeech.audio.detection import detect_audio_format
from litespeech.audio.conversion import convert_audio, convert_to_provider_format
from litespeech.audio.validation import validate_audio, ValidationResult
from litespeech.audio.inspector import inspect_audio, print_audio_info, AudioInspector

__all__ = [
    "AudioFormat",
    "AudioInfo",
    "get_provider_spec",
    "detect_audio_format",
    "convert_audio",
    "convert_to_provider_format",
    "validate_audio",
    "ValidationResult",
    "inspect_audio",
    "print_audio_info",
    "AudioInspector",
]
