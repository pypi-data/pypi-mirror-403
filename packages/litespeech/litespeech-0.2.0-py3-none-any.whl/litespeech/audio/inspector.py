"""Audio file inspection utilities."""

import struct
from pathlib import Path
from typing import Any


class AudioInspector:
    """Inspect audio files and extract format parameters."""

    @staticmethod
    def inspect(file_path: str | Path) -> dict[str, Any]:
        """
        Inspect an audio file and return all settable parameters.

        Args:
            file_path: Path to audio file

        Returns:
            Dict with audio parameters and recommendations

        Example:
            >>> from litespeech.audio.inspector import AudioInspector
            >>> info = AudioInspector.inspect("audio.wav")
            >>> print(info)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Read first chunk to detect format
        with open(file_path, "rb") as f:
            header = f.read(12)
            f.seek(0)
            full_data = f.read()

        file_size = len(full_data)

        # Detect format
        if header[:4] == b"RIFF" and header[8:12] == b"WAVE":
            return AudioInspector._inspect_wav(full_data, file_path, file_size)
        elif header[:3] == b"ID3" or header[:2] == b"\xff\xfb":
            return AudioInspector._inspect_mp3(full_data, file_path, file_size)
        elif header[:4] == b"fLaC":
            return AudioInspector._inspect_flac(full_data, file_path, file_size)
        else:
            return {
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "format": "UNKNOWN",
                "error": "Unsupported or unknown audio format",
                "detected_header": header[:12].hex(),
            }

    @staticmethod
    def _inspect_wav(data: bytes, file_path: Path, file_size: int) -> dict[str, Any]:
        """Inspect WAV file."""
        try:
            # Find fmt chunk
            fmt_offset = data.find(b"fmt ")
            if fmt_offset == -1:
                raise ValueError("fmt chunk not found")

            # Parse fmt chunk
            # +0: "fmt " (4 bytes)
            # +4: chunk size (4 bytes)
            # +8: audio format (2 bytes) - 1 = PCM
            # +10: num channels (2 bytes)
            # +12: sample rate (4 bytes)
            # +16: byte rate (4 bytes)
            # +20: block align (2 bytes)
            # +22: bits per sample (2 bytes)

            chunk_size = struct.unpack("<I", data[fmt_offset+4:fmt_offset+8])[0]
            audio_format = struct.unpack("<H", data[fmt_offset+8:fmt_offset+10])[0]
            num_channels = struct.unpack("<H", data[fmt_offset+10:fmt_offset+12])[0]
            sample_rate = struct.unpack("<I", data[fmt_offset+12:fmt_offset+16])[0]
            byte_rate = struct.unpack("<I", data[fmt_offset+16:fmt_offset+20])[0]
            block_align = struct.unpack("<H", data[fmt_offset+20:fmt_offset+22])[0]
            bits_per_sample = struct.unpack("<H", data[fmt_offset+22:fmt_offset+24])[0]

            # Find data chunk
            data_offset = data.find(b"data")
            if data_offset != -1:
                data_size = struct.unpack("<I", data[data_offset+4:data_offset+8])[0]
                header_size = data_offset + 8
            else:
                data_size = file_size - 44  # Estimate
                header_size = 44

            # Calculate duration
            if byte_rate > 0:
                duration_seconds = data_size / byte_rate
            else:
                duration_seconds = 0

            # Determine encoding
            if audio_format == 1:
                encoding = "pcm"
                encoding_name = "PCM (Linear)"
            elif audio_format == 6:
                encoding = "alaw"
                encoding_name = "A-law"
            elif audio_format == 7:
                encoding = "mulaw"
                encoding_name = "μ-law"
            else:
                encoding = f"format_{audio_format}"
                encoding_name = f"Format {audio_format}"

            # Determine linear16 encoding for streaming
            if bits_per_sample == 16:
                streaming_encoding = "linear16"
            elif bits_per_sample == 8:
                streaming_encoding = "linear8"
            elif bits_per_sample == 24:
                streaming_encoding = "linear24"
            else:
                streaming_encoding = f"linear{bits_per_sample}"

            return {
                # File info
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "format": "WAV",

                # Audio format details
                "audio_format": encoding_name,
                "audio_format_code": audio_format,

                # Key parameters for LiteSpeech
                "sample_rate": sample_rate,
                "channels": num_channels,
                "bits_per_sample": bits_per_sample,
                "encoding": encoding,

                # Additional info
                "byte_rate": byte_rate,
                "block_align": block_align,
                "header_size": header_size,
                "audio_data_size": data_size,
                "duration_seconds": round(duration_seconds, 2),

                # Recommendations for streaming
                "streaming_params": {
                    "sample_rate": sample_rate,
                    "channels": num_channels,
                    "encoding": streaming_encoding,
                },

                # Usage example
                "usage_example": (
                    f"ls.speech_to_text_stream(\n"
                    f"    audio_stream=your_stream,\n"
                    f"    provider='deepgram/nova-3',\n"
                    f"    sample_rate={sample_rate},\n"
                    f"    channels={num_channels},\n"
                    f"    encoding='{streaming_encoding}',\n"
                    f")"
                ),
            }

        except Exception as e:
            return {
                "file_path": str(file_path),
                "file_size_bytes": file_size,
                "format": "WAV",
                "error": f"Failed to parse WAV: {str(e)}",
            }

    @staticmethod
    def _inspect_mp3(data: bytes, file_path: Path, file_size: int) -> dict[str, Any]:
        """Inspect MP3 file (basic)."""
        # MP3 inspection is complex - for now return basic info
        return {
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "format": "MP3",
            "note": "MP3 files should be converted to WAV/PCM for streaming ASR",
            "recommendation": "Use batch ASR (speech_to_text) or convert to WAV first",
        }

    @staticmethod
    def _inspect_flac(data: bytes, file_path: Path, file_size: int) -> dict[str, Any]:
        """Inspect FLAC file (basic)."""
        return {
            "file_path": str(file_path),
            "file_size_bytes": file_size,
            "format": "FLAC",
            "note": "FLAC files should be converted to WAV/PCM for streaming ASR",
            "recommendation": "Use batch ASR (speech_to_text) or convert to WAV first",
        }


def inspect_audio(file_path: str | Path) -> dict[str, Any]:
    """
    Inspect an audio file and print settable parameters.

    Args:
        file_path: Path to audio file

    Returns:
        Dict with audio parameters

    Example:
        >>> from litespeech.audio import inspect_audio
        >>> info = inspect_audio("harvard.wav")
        >>> print(f"Sample Rate: {info['sample_rate']}")
        >>> print(f"Channels: {info['channels']}")
    """
    return AudioInspector.inspect(file_path)


def print_audio_info(file_path: str | Path) -> None:
    """
    Inspect audio file and print formatted information.

    Args:
        file_path: Path to audio file

    Example:
        >>> from litespeech.audio import print_audio_info
        >>> print_audio_info("harvard.wav")
    """
    info = inspect_audio(file_path)

    print("=" * 70)
    print(f"📁 Audio File Inspection: {info['file_path']}")
    print("=" * 70)

    if "error" in info:
        print(f"\n❌ Error: {info['error']}")
        if "detected_header" in info:
            print(f"Detected header: {info['detected_header']}")
        return

    print(f"\n📊 File Information:")
    print(f"  • Format: {info['format']}")
    print(f"  • File Size: {info['file_size_bytes']:,} bytes ({info['file_size_bytes'] / 1024 / 1024:.2f} MB)")

    if info['format'] == 'WAV':
        print(f"\n🎵 Audio Properties:")
        print(f"  • Sample Rate: {info['sample_rate']:,} Hz")
        print(f"  • Channels: {info['channels']} ({'Mono' if info['channels'] == 1 else 'Stereo' if info['channels'] == 2 else f'{info['channels']}-channel'})")
        print(f"  • Bits per Sample: {info['bits_per_sample']}")
        print(f"  • Encoding: {info['audio_format']}")
        print(f"  • Duration: {info['duration_seconds']} seconds")

        print(f"\n⚙️  Parameters for LiteSpeech Streaming:")
        print(f"  • sample_rate = {info['sample_rate']}")
        print(f"  • channels = {info['channels']}")
        print(f"  • encoding = '{info['streaming_params']['encoding']}'")

        print(f"\n💡 Usage Example:")
        print(info['usage_example'])

    elif "note" in info:
        print(f"\n⚠️  Note: {info['note']}")
        print(f"💡 Recommendation: {info['recommendation']}")

    print("=" * 70)
