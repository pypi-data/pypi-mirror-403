"""Audio format detection utilities."""

import io
import struct
from pathlib import Path
from typing import BinaryIO

from litespeech.audio.types import AudioFormat, AudioInfo
from litespeech.exceptions import AudioFormatError


# File signature (magic bytes) for common audio formats
AUDIO_SIGNATURES: dict[bytes, AudioFormat] = {
    b"ID3": AudioFormat.MP3,
    b"\xff\xfb": AudioFormat.MP3,
    b"\xff\xfa": AudioFormat.MP3,
    b"\xff\xf3": AudioFormat.MP3,
    b"\xff\xf2": AudioFormat.MP3,
    b"RIFF": AudioFormat.WAV,
    b"fLaC": AudioFormat.FLAC,
    b"OggS": AudioFormat.OGG,
    b"\x1aE\xdf\xa3": AudioFormat.WEBM,  # EBML header (WebM/MKV)
}


def detect_audio_format(audio: bytes | str | Path | BinaryIO) -> AudioInfo:
    """
    Auto-detect audio format, sample rate, channels, and duration.

    Args:
        audio: Audio data as bytes, file path, or file-like object

    Returns:
        AudioInfo with detected properties

    Raises:
        AudioFormatError: If format cannot be detected
    """
    # Get bytes from various input types
    if isinstance(audio, (str, Path)):
        path = Path(audio)
        if not path.exists():
            raise AudioFormatError(f"Audio file not found: {path}")
        with open(path, "rb") as f:
            data = f.read()
        file_size = path.stat().st_size
    elif isinstance(audio, bytes):
        data = audio
        file_size = len(data)
    else:
        # File-like object
        pos = audio.tell()
        data = audio.read()
        audio.seek(pos)
        file_size = len(data)

    if len(data) < 12:
        raise AudioFormatError("Audio data too small to detect format")

    # Detect format from magic bytes
    audio_format = _detect_format_from_magic(data)

    # Extract detailed info based on format
    if audio_format == AudioFormat.WAV:
        return _parse_wav_header(data, file_size)
    elif audio_format == AudioFormat.MP3:
        return _parse_mp3_header(data, file_size)
    elif audio_format == AudioFormat.FLAC:
        return _parse_flac_header(data, file_size)
    elif audio_format == AudioFormat.OGG:
        return AudioInfo(
            format=audio_format,
            sample_rate=48000,  # Common default, actual parsing would require more work
            channels=2,
            file_size=file_size,
        )
    else:
        # Return basic info for unknown formats
        return AudioInfo(
            format=audio_format or "unknown",
            sample_rate=16000,  # Assume common default
            channels=1,
            file_size=file_size,
        )


def _detect_format_from_magic(data: bytes) -> AudioFormat | None:
    """Detect audio format from magic bytes."""
    for signature, fmt in AUDIO_SIGNATURES.items():
        if data.startswith(signature):
            return fmt

    # Check for MP3 sync word anywhere in first few bytes (might have ID3 tag)
    if b"\xff\xfb" in data[:10] or b"\xff\xfa" in data[:10]:
        return AudioFormat.MP3

    return None


def _parse_wav_header(data: bytes, file_size: int) -> AudioInfo:
    """Parse WAV file header to extract audio info."""
    try:
        # RIFF header: "RIFF" + size + "WAVE"
        if data[0:4] != b"RIFF" or data[8:12] != b"WAVE":
            raise AudioFormatError("Invalid WAV file format")

        # Find fmt chunk
        pos = 12
        while pos < len(data) - 8:
            chunk_id = data[pos : pos + 4]
            chunk_size = struct.unpack("<I", data[pos + 4 : pos + 8])[0]

            if chunk_id == b"fmt ":
                # Parse fmt chunk
                audio_format_code = struct.unpack("<H", data[pos + 8 : pos + 10])[0]
                channels = struct.unpack("<H", data[pos + 10 : pos + 12])[0]
                sample_rate = struct.unpack("<I", data[pos + 12 : pos + 16])[0]
                byte_rate = struct.unpack("<I", data[pos + 16 : pos + 20])[0]
                bits_per_sample = struct.unpack("<H", data[pos + 22 : pos + 24])[0]

                # Calculate duration from data chunk if available
                duration = None
                data_pos = pos + 8 + chunk_size
                while data_pos < len(data) - 8:
                    data_chunk_id = data[data_pos : data_pos + 4]
                    data_chunk_size = struct.unpack("<I", data[data_pos + 4 : data_pos + 8])[0]
                    if data_chunk_id == b"data":
                        if byte_rate > 0:
                            duration = data_chunk_size / byte_rate
                        break
                    data_pos += 8 + data_chunk_size

                return AudioInfo(
                    format=AudioFormat.WAV,
                    sample_rate=sample_rate,
                    channels=channels,
                    bit_depth=bits_per_sample,
                    duration=duration,
                    bitrate=byte_rate * 8,
                    file_size=file_size,
                )

            pos += 8 + chunk_size

        raise AudioFormatError("Could not find fmt chunk in WAV file")

    except struct.error as e:
        raise AudioFormatError(f"Error parsing WAV header: {e}")


def _parse_mp3_header(data: bytes, file_size: int) -> AudioInfo:
    """Parse MP3 file header to extract audio info."""
    # Skip ID3v2 tag if present
    offset = 0
    if data[0:3] == b"ID3":
        # ID3v2 tag size is stored in bytes 6-9 as syncsafe integer
        size = (
            (data[6] & 0x7F) << 21
            | (data[7] & 0x7F) << 14
            | (data[8] & 0x7F) << 7
            | (data[9] & 0x7F)
        )
        offset = 10 + size

    # Find sync word
    while offset < len(data) - 4:
        if data[offset] == 0xFF and (data[offset + 1] & 0xE0) == 0xE0:
            break
        offset += 1
    else:
        # Default values if we can't parse
        return AudioInfo(
            format=AudioFormat.MP3,
            sample_rate=44100,
            channels=2,
            file_size=file_size,
        )

    # Parse frame header
    header = struct.unpack(">I", data[offset : offset + 4])[0]

    # Extract fields from header
    version = (header >> 19) & 0x03
    layer = (header >> 17) & 0x03
    bitrate_index = (header >> 12) & 0x0F
    sample_rate_index = (header >> 10) & 0x03
    channel_mode = (header >> 6) & 0x03

    # Sample rate table (MPEG1, MPEG2, MPEG2.5)
    sample_rates = {
        0: [44100, 22050, 11025],
        1: [48000, 24000, 12000],
        2: [32000, 16000, 8000],
    }

    # Version index to table index
    version_to_index = {3: 0, 2: 1, 0: 2}  # MPEG1, MPEG2, MPEG2.5

    try:
        sr_table_index = version_to_index.get(version, 0)
        sample_rate = sample_rates.get(sample_rate_index, [44100])[sr_table_index]
    except (KeyError, IndexError):
        sample_rate = 44100

    # Channel mode: 0=stereo, 1=joint stereo, 2=dual channel, 3=mono
    channels = 1 if channel_mode == 3 else 2

    return AudioInfo(
        format=AudioFormat.MP3,
        sample_rate=sample_rate,
        channels=channels,
        file_size=file_size,
    )


def _parse_flac_header(data: bytes, file_size: int) -> AudioInfo:
    """Parse FLAC file header to extract audio info."""
    try:
        # Skip "fLaC" marker
        if data[0:4] != b"fLaC":
            raise AudioFormatError("Invalid FLAC file format")

        # First metadata block should be STREAMINFO
        block_header = data[4]
        block_type = block_header & 0x7F

        if block_type != 0:  # STREAMINFO
            # Return defaults
            return AudioInfo(
                format=AudioFormat.FLAC,
                sample_rate=44100,
                channels=2,
                file_size=file_size,
            )

        block_size = struct.unpack(">I", b"\x00" + data[5:8])[0]

        # STREAMINFO is 34 bytes
        streaminfo = data[8 : 8 + 34]

        # Sample rate is 20 bits starting at byte 10
        sample_rate = (
            (streaminfo[10] << 12) | (streaminfo[11] << 4) | ((streaminfo[12] & 0xF0) >> 4)
        )

        # Channels is 3 bits
        channels = ((streaminfo[12] & 0x0E) >> 1) + 1

        # Bits per sample is 5 bits
        bits_per_sample = ((streaminfo[12] & 0x01) << 4) | ((streaminfo[13] & 0xF0) >> 4) + 1

        # Total samples is 36 bits
        total_samples = ((streaminfo[13] & 0x0F) << 32) | struct.unpack(">I", streaminfo[14:18])[0]

        duration = total_samples / sample_rate if sample_rate > 0 else None

        return AudioInfo(
            format=AudioFormat.FLAC,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=bits_per_sample,
            duration=duration,
            file_size=file_size,
        )

    except (struct.error, IndexError) as e:
        return AudioInfo(
            format=AudioFormat.FLAC,
            sample_rate=44100,
            channels=2,
            file_size=file_size,
        )
