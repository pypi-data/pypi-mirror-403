"""Audio type definitions."""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class AudioFormat(str, Enum):
    """Supported audio formats."""

    MP3 = "mp3"
    WAV = "wav"
    PCM = "pcm"
    FLAC = "flac"
    OGG = "ogg"
    OPUS = "opus"
    WEBM = "webm"
    M4A = "m4a"
    AAC = "aac"
    MULAW = "mulaw"
    ALAW = "alaw"


# Common sample rates
SampleRate = Literal[8000, 16000, 22050, 24000, 44100, 48000]

# Common bit depths
BitDepth = Literal[8, 16, 24, 32]


@dataclass
class AudioInfo:
    """Information about an audio file or stream."""

    format: AudioFormat | str
    sample_rate: int
    channels: int
    bit_depth: int | None = None
    duration: float | None = None
    bitrate: int | None = None
    file_size: int | None = None

    @property
    def is_mono(self) -> bool:
        """Check if audio is mono."""
        return self.channels == 1

    @property
    def is_stereo(self) -> bool:
        """Check if audio is stereo."""
        return self.channels == 2


@dataclass
class AudioChunk:
    """A chunk of audio data for streaming."""

    data: bytes
    sample_rate: int
    channels: int = 1
    format: str = "pcm"
    bit_depth: int = 16
