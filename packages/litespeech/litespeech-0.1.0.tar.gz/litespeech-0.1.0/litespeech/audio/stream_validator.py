"""Audio stream validation and transformation utilities."""

from collections.abc import AsyncIterator
from typing import Any
import struct
import logging

logger = logging.getLogger(__name__)


class AudioStreamValidator:
    """
    Validates and transforms audio streams to match provider requirements.

    Handles:
    - WAV header detection and stripping
    - Parameter validation against provider specs
    - Format mismatch detection
    - Clear error messaging
    """

    def __init__(
        self,
        provider_name: str,
        user_sample_rate: int,
        user_channels: int,
        user_encoding: str,
        provider_spec: dict[str, Any] | None = None,
    ):
        """
        Initialize validator.

        Args:
            provider_name: Name of the provider (for error messages)
            user_sample_rate: Sample rate user claims the stream has
            user_channels: Number of channels user claims
            user_encoding: Encoding format user claims
            provider_spec: Provider's audio specifications
        """
        self.provider_name = provider_name
        self.user_sample_rate = user_sample_rate
        self.user_channels = user_channels
        self.user_encoding = user_encoding
        self.provider_spec = provider_spec or {}

        self.detected_format: dict[str, Any] | None = None
        self.has_warned = False

    def validate_against_provider(self) -> list[str]:
        """
        Validate user parameters against provider requirements.

        Returns:
            List of validation error/warning messages
        """
        issues = []

        # Check recommended sample rate
        if "recommended_sample_rate" in self.provider_spec:
            recommended = self.provider_spec["recommended_sample_rate"]
            if self.user_sample_rate != recommended:
                issues.append(
                    f"Sample rate {self.user_sample_rate}Hz may not be optimal. "
                    f"{self.provider_name} recommends {recommended}Hz for best results."
                )

        # Check if provider has strict requirements
        if "required_sample_rates" in self.provider_spec:
            allowed = self.provider_spec["required_sample_rates"]
            if self.user_sample_rate not in allowed:
                issues.append(
                    f"Sample rate {self.user_sample_rate}Hz is not supported. "
                    f"{self.provider_name} only accepts: {allowed}"
                )

        if "required_channels" in self.provider_spec:
            allowed = self.provider_spec["required_channels"]
            if self.user_channels not in allowed:
                issues.append(
                    f"Channel count {self.user_channels} is not supported. "
                    f"{self.provider_name} only accepts: {allowed}"
                )

        if "required_encodings" in self.provider_spec:
            allowed = self.provider_spec["required_encodings"]
            if self.user_encoding not in allowed:
                issues.append(
                    f"Encoding '{self.user_encoding}' is not supported. "
                    f"{self.provider_name} only accepts: {allowed}"
                )

        return issues

    def parse_wav_header(self, chunk: bytes) -> dict[str, Any] | None:
        """
        Parse WAV header from first chunk if present.

        Args:
            chunk: First chunk of audio data

        Returns:
            Dict with format info, or None if not a WAV or parsing failed
        """
        if len(chunk) < 44 or chunk[:4] != b"RIFF":
            return None

        try:
            # Find fmt chunk
            fmt_offset = chunk.find(b"fmt ")
            if fmt_offset == -1 or fmt_offset + 24 > len(chunk):
                return None

            # Read format details
            # fmt chunk structure:
            # +0: "fmt "
            # +4: chunk size (4 bytes)
            # +8: audio format (2 bytes) - 1 = PCM
            # +10: num channels (2 bytes)
            # +12: sample rate (4 bytes)
            # +16: byte rate (4 bytes)
            # +20: block align (2 bytes)
            # +22: bits per sample (2 bytes)

            audio_format = struct.unpack("<H", chunk[fmt_offset+8:fmt_offset+10])[0]
            num_channels = struct.unpack("<H", chunk[fmt_offset+10:fmt_offset+12])[0]
            sample_rate = struct.unpack("<I", chunk[fmt_offset+12:fmt_offset+16])[0]
            bits_per_sample = struct.unpack("<H", chunk[fmt_offset+22:fmt_offset+24])[0]

            # Find data chunk offset
            data_offset = chunk.find(b"data")
            if data_offset != -1:
                # Skip 'data' marker (4 bytes) + size (4 bytes)
                data_start = data_offset + 8
            else:
                data_start = 44  # Assume standard header size

            return {
                "format": "PCM" if audio_format == 1 else f"format_{audio_format}",
                "channels": num_channels,
                "sample_rate": sample_rate,
                "bits_per_sample": bits_per_sample,
                "header_size": data_start,
            }

        except Exception as e:
            logger.debug(f"Failed to parse WAV header: {e}")
            return None

    def check_header_mismatch(self, detected: dict[str, Any]) -> list[str]:
        """
        Compare detected WAV header with user parameters.

        Args:
            detected: Detected format from WAV header

        Returns:
            List of mismatch messages
        """
        mismatches = []

        if detected["sample_rate"] != self.user_sample_rate:
            mismatches.append(
                f"Sample rate: WAV header says {detected['sample_rate']}Hz, "
                f"but you specified {self.user_sample_rate}Hz"
            )

        if detected["channels"] != self.user_channels:
            mismatches.append(
                f"Channels: WAV header says {detected['channels']} channel(s), "
                f"but you specified {self.user_channels}"
            )

        return mismatches

    async def validate_and_transform(
        self,
        audio_stream: AsyncIterator[bytes],
    ) -> AsyncIterator[bytes]:
        """
        Validate audio stream and transform as needed.

        - Detects WAV headers and strips them
        - Validates parameters against provider requirements
        - Warns about format mismatches
        - Yields transformed audio chunks

        Args:
            audio_stream: Input audio stream

        Yields:
            Validated/transformed audio chunks
        """
        first_chunk = True

        async for chunk in audio_stream:
            if first_chunk and len(chunk) >= 44:
                first_chunk = False

                # Try to detect WAV header
                detected = self.parse_wav_header(chunk)

                if detected:
                    self.detected_format = detected
                    logger.debug(f"Detected WAV header: {detected}")

                    # Check for mismatches
                    mismatches = self.check_header_mismatch(detected)

                    if mismatches:
                        error_msg = (
                            f"\n{'='*70}\n"
                            f"⚠️  AUDIO FORMAT MISMATCH DETECTED!\n"
                            f"{'='*70}\n"
                            f"Your audio stream contains a WAV file, but the header doesn't match\n"
                            f"the parameters you provided. This WILL cause transcription to fail.\n\n"
                            f"Detected from WAV header:\n"
                            f"  • Sample Rate: {detected['sample_rate']} Hz\n"
                            f"  • Channels: {detected['channels']}\n"
                            f"  • Bits per sample: {detected['bits_per_sample']}\n\n"
                            f"Parameters you provided:\n"
                            f"  • sample_rate = {self.user_sample_rate}\n"
                            f"  • channels = {self.user_channels}\n\n"
                            f"❌ MISMATCHES:\n"
                        )
                        for mismatch in mismatches:
                            error_msg += f"  • {mismatch}\n"

                        error_msg += (
                            f"\n✅ SOLUTION: Update your parameters to match the WAV file:\n"
                            f"  speech_to_text_stream(\n"
                            f"    audio_stream=your_stream,\n"
                            f"    provider=\"{self.provider_name}\",\n"
                            f"    sample_rate={detected['sample_rate']},\n"
                            f"    channels={detected['channels']},\n"
                            f"    ...\n"
                            f"  )\n"
                            f"{'='*70}\n"
                        )
                        logger.error(error_msg)

                    # Strip WAV header
                    logger.info(f"Stripping WAV header ({detected['header_size']} bytes)")
                    chunk = chunk[detected['header_size']:]

                # Validate user params against provider (only warn once)
                if not self.has_warned:
                    self.has_warned = True
                    validation_issues = self.validate_against_provider()

                    if validation_issues:
                        warning_msg = (
                            f"\n{'='*70}\n"
                            f"⚠️  AUDIO FORMAT VALIDATION\n"
                            f"{'='*70}\n"
                        )
                        for issue in validation_issues:
                            warning_msg += f"  • {issue}\n"

                        warning_msg += (
                            f"\nProvider: {self.provider_name}\n"
                            f"Your parameters:\n"
                            f"  • sample_rate = {self.user_sample_rate} Hz\n"
                            f"  • channels = {self.user_channels}\n"
                            f"  • encoding = {self.user_encoding}\n"
                        )

                        if self.provider_spec.get("recommended_sample_rate"):
                            warning_msg += (
                                f"\nRecommended:\n"
                                f"  • sample_rate = {self.provider_spec['recommended_sample_rate']} Hz\n"
                            )

                        warning_msg += f"{'='*70}\n"
                        logger.warning(warning_msg)

            else:
                first_chunk = False

            yield chunk
