"""Audio format conversion utilities."""

import io
import struct
from typing import Any

from litespeech.audio.types import AudioFormat, AudioInfo
from litespeech.audio.detection import detect_audio_format
from litespeech.audio.specs import get_provider_spec
from litespeech.exceptions import AudioFormatError


def needs_conversion(current: AudioInfo, target: dict[str, Any]) -> bool:
    """
    Check if audio needs conversion to match target spec.

    Args:
        current: Current audio info
        target: Target specification dict with format, sample_rate, etc.

    Returns:
        True if conversion is needed
    """
    target_format = target.get("format")
    target_sample_rate = target.get("sample_rate")
    target_channels = target.get("channels")

    # Get format value from enum if needed
    current_format = current.format.value if isinstance(current.format, AudioFormat) else str(current.format)

    if target_format and current_format.lower() != str(target_format).lower():
        return True

    if target_sample_rate and current.sample_rate != target_sample_rate:
        return True

    if target_channels and current.channels != target_channels:
        return True

    return False


def convert_audio(
    audio: bytes,
    current_info: AudioInfo,
    target_format: str,
    target_sample_rate: int | None = None,
    target_channels: int | None = None,
) -> bytes:
    """
    Convert audio to target format.

    This is a basic implementation that handles common conversions.
    For full format support, install the 'audio' extra: pip install litespeech[audio]

    Args:
        audio: Input audio bytes
        current_info: Information about input audio
        target_format: Target format (e.g., "wav", "pcm")
        target_sample_rate: Target sample rate (optional)
        target_channels: Target channel count (optional)

    Returns:
        Converted audio bytes

    Raises:
        AudioFormatError: If conversion is not supported
    """
    # Use pydub if available for full conversion support
    try:
        from pydub import AudioSegment

        return _convert_with_pydub(
            audio, current_info, target_format, target_sample_rate, target_channels
        )
    except ImportError:
        pass

    # Basic built-in conversions
    target_format_lower = target_format.lower()

    # WAV to PCM
    if current_info.format == AudioFormat.WAV and target_format_lower in ("pcm", "raw"):
        return _wav_to_pcm(audio)

    # PCM to WAV
    if target_format_lower == "wav" and current_info.format in (AudioFormat.PCM, "pcm", "raw"):
        sample_rate = target_sample_rate or current_info.sample_rate
        channels = target_channels or current_info.channels
        bit_depth = current_info.bit_depth or 16
        return _pcm_to_wav(audio, sample_rate, channels, bit_depth)

    # If formats match and no resampling needed, return as-is
    # Extract format value from enum if needed
    current_format = current_info.format.value if isinstance(current_info.format, AudioFormat) else str(current_info.format)

    if current_format.lower() == target_format_lower:
        if (not target_sample_rate or current_info.sample_rate == target_sample_rate) and (
            not target_channels or current_info.channels == target_channels
        ):
            return audio

    # Build detailed error message
    reasons = []
    if current_format.lower() != target_format_lower:
        reasons.append(f"format mismatch: {current_format} → {target_format}")
    if target_sample_rate and current_info.sample_rate != target_sample_rate:
        reasons.append(f"sample rate mismatch: {current_info.sample_rate}Hz → {target_sample_rate}Hz")
    if target_channels and current_info.channels != target_channels:
        reasons.append(f"channel mismatch: {current_info.channels} → {target_channels}")

    raise AudioFormatError(
        f"Audio conversion needed but not supported with built-in converters.\n"
        f"  Current: {current_info.format} {current_info.sample_rate}Hz {current_info.channels}ch\n"
        f"  Target:  {target_format} {target_sample_rate or 'any'}Hz {target_channels or 'any'}ch\n"
        f"  Reason:  {', '.join(reasons)}\n\n"
        f"Solutions:\n"
        f"  1. Install pydub for full conversion: pip install litespeech[audio]\n"
        f"  2. Disable preprocessing: speech_to_text(..., preprocess=False)\n"
        f"  3. Convert audio beforehand to match target format"
    )


def convert_to_provider_format(
    audio: bytes,
    provider_model: str,
    preprocess: bool = True,
) -> bytes:
    """
    Convert audio to a provider's required format.

    Args:
        audio: Input audio bytes
        provider_model: Provider/model string (e.g., "deepgram/nova-2")
        preprocess: Whether to perform conversion (False to skip)

    Returns:
        Audio bytes in provider's preferred format
    """
    if not preprocess:
        return audio

    spec = get_provider_spec(provider_model)
    if not spec:
        return audio

    preferred = spec.get("preferred", {})
    if not preferred:
        return audio

    current = detect_audio_format(audio)

    if not needs_conversion(current, preferred):
        return audio

    return convert_audio(
        audio,
        current,
        target_format=preferred.get("format", str(current.format)),
        target_sample_rate=preferred.get("sample_rate"),
        target_channels=preferred.get("channels"),
    )


def _wav_to_pcm(wav_data: bytes) -> bytes:
    """Extract raw PCM data from WAV file."""
    # Find data chunk
    pos = 12  # Skip RIFF header
    while pos < len(wav_data) - 8:
        chunk_id = wav_data[pos : pos + 4]
        chunk_size = struct.unpack("<I", wav_data[pos + 4 : pos + 8])[0]

        if chunk_id == b"data":
            return wav_data[pos + 8 : pos + 8 + chunk_size]

        pos += 8 + chunk_size

    raise AudioFormatError("Could not find data chunk in WAV file")


def _pcm_to_wav(
    pcm_data: bytes,
    sample_rate: int,
    channels: int,
    bits_per_sample: int,
) -> bytes:
    """Convert raw PCM data to WAV format."""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8

    buffer = io.BytesIO()

    # RIFF header
    buffer.write(b"RIFF")
    buffer.write(struct.pack("<I", 36 + len(pcm_data)))
    buffer.write(b"WAVE")

    # fmt chunk
    buffer.write(b"fmt ")
    buffer.write(struct.pack("<I", 16))  # Chunk size
    buffer.write(struct.pack("<H", 1))  # Audio format (PCM)
    buffer.write(struct.pack("<H", channels))
    buffer.write(struct.pack("<I", sample_rate))
    buffer.write(struct.pack("<I", byte_rate))
    buffer.write(struct.pack("<H", block_align))
    buffer.write(struct.pack("<H", bits_per_sample))

    # data chunk
    buffer.write(b"data")
    buffer.write(struct.pack("<I", len(pcm_data)))
    buffer.write(pcm_data)

    return buffer.getvalue()


def _convert_with_pydub(
    audio: bytes,
    current_info: AudioInfo,
    target_format: str,
    target_sample_rate: int | None = None,
    target_channels: int | None = None,
) -> bytes:
    """Convert audio using pydub library."""
    from pydub import AudioSegment

    # Load audio
    audio_segment = AudioSegment.from_file(
        io.BytesIO(audio),
        format=str(current_info.format).lower(),
    )

    # Resample if needed
    if target_sample_rate and audio_segment.frame_rate != target_sample_rate:
        audio_segment = audio_segment.set_frame_rate(target_sample_rate)

    # Convert channels if needed
    if target_channels:
        if target_channels == 1 and audio_segment.channels != 1:
            audio_segment = audio_segment.set_channels(1)
        elif target_channels == 2 and audio_segment.channels != 2:
            audio_segment = audio_segment.set_channels(2)

    # Export to target format
    output = io.BytesIO()
    export_format = target_format.lower()

    # Handle PCM/raw format
    if export_format in ("pcm", "raw"):
        return audio_segment.raw_data

    audio_segment.export(output, format=export_format)
    return output.getvalue()
