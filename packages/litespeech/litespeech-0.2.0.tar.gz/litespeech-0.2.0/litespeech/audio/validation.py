"""Audio validation utilities."""

from dataclasses import dataclass, field
from typing import Any

from litespeech.audio.types import AudioInfo
from litespeech.audio.detection import detect_audio_format
from litespeech.audio.specs import get_provider_spec


@dataclass
class ValidationResult:
    """Result of audio validation."""

    valid: bool
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    audio_info: AudioInfo | None = None

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.valid


def validate_audio(
    audio: bytes,
    provider_model: str | None = None,
    max_size: int | None = None,
    max_duration: float | None = None,
    required_format: str | None = None,
    required_sample_rate: int | None = None,
) -> ValidationResult:
    """
    Validate audio data against requirements.

    Args:
        audio: Audio data bytes
        provider_model: Provider/model string to validate against its spec
        max_size: Maximum file size in bytes
        max_duration: Maximum duration in seconds
        required_format: Required audio format
        required_sample_rate: Required sample rate

    Returns:
        ValidationResult with validation status and any issues
    """
    issues: list[str] = []
    warnings: list[str] = []

    # Try to detect audio format
    try:
        audio_info = detect_audio_format(audio)
    except Exception as e:
        return ValidationResult(
            valid=False,
            issues=[f"Could not detect audio format: {e}"],
        )

    # Get provider spec if provided
    spec: dict[str, Any] = {}
    if provider_model:
        spec = get_provider_spec(provider_model) or {}

    # Check file size
    effective_max_size = max_size or spec.get("max_size")
    if effective_max_size and len(audio) > effective_max_size:
        issues.append(
            f"Audio size ({len(audio):,} bytes) exceeds maximum ({effective_max_size:,} bytes)"
        )

    # Check duration
    if max_duration and audio_info.duration and audio_info.duration > max_duration:
        issues.append(
            f"Audio duration ({audio_info.duration:.1f}s) exceeds maximum ({max_duration:.1f}s)"
        )

    # Check format
    if required_format:
        # Use .value to get string value from enum (e.g., AudioFormat.MP3.value = "mp3")
        format_str = audio_info.format.value if hasattr(audio_info.format, 'value') else str(audio_info.format)
        if format_str.lower() != required_format.lower():
            issues.append(f"Audio format '{audio_info.format}' does not match required '{required_format}'")
    elif spec.get("formats"):
        allowed_formats = [f.lower() for f in spec["formats"]]
        # Use .value to get string value from enum
        format_str = audio_info.format.value if hasattr(audio_info.format, 'value') else str(audio_info.format)
        if format_str.lower() not in allowed_formats:
            warnings.append(
                f"Audio format '{audio_info.format}' not in provider's supported formats: {allowed_formats}"
            )

    # Check sample rate
    if required_sample_rate:
        if audio_info.sample_rate != required_sample_rate:
            issues.append(
                f"Audio sample rate ({audio_info.sample_rate}) does not match required ({required_sample_rate})"
            )
    elif spec.get("sample_rates") and spec["sample_rates"] != "any":
        allowed_rates = spec["sample_rates"]
        if audio_info.sample_rate not in allowed_rates:
            warnings.append(
                f"Audio sample rate ({audio_info.sample_rate}) not in provider's supported rates: {allowed_rates}"
            )

    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        warnings=warnings,
        audio_info=audio_info,
    )


def validate_audio_stream_chunk(
    chunk: bytes,
    expected_format: str = "pcm",
    expected_sample_rate: int = 16000,
    expected_channels: int = 1,
    min_chunk_size: int = 320,  # 10ms of 16-bit mono 16kHz audio
) -> ValidationResult:
    """
    Validate an audio stream chunk.

    Args:
        chunk: Audio chunk bytes
        expected_format: Expected format (usually "pcm" for streaming)
        expected_sample_rate: Expected sample rate
        expected_channels: Expected number of channels
        min_chunk_size: Minimum expected chunk size in bytes

    Returns:
        ValidationResult with validation status
    """
    issues: list[str] = []
    warnings: list[str] = []

    if len(chunk) == 0:
        issues.append("Empty audio chunk")
        return ValidationResult(valid=False, issues=issues)

    if len(chunk) < min_chunk_size:
        warnings.append(f"Audio chunk smaller than expected ({len(chunk)} < {min_chunk_size} bytes)")

    # For PCM, check that size is aligned to sample size
    if expected_format.lower() == "pcm":
        bytes_per_sample = 2  # Assuming 16-bit
        expected_alignment = bytes_per_sample * expected_channels
        if len(chunk) % expected_alignment != 0:
            warnings.append(
                f"Audio chunk size ({len(chunk)}) not aligned to sample size ({expected_alignment})"
            )

    return ValidationResult(
        valid=len(issues) == 0,
        issues=issues,
        warnings=warnings,
        audio_info=AudioInfo(
            format=expected_format,
            sample_rate=expected_sample_rate,
            channels=expected_channels,
            file_size=len(chunk),
        ),
    )
