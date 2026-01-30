"""Azure Speech Services TTS provider implementation."""

import asyncio
import logging
import os
import threading
from collections.abc import AsyncIterator
from typing import Any

import azure.cognitiveservices.speech as speechsdk

from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError
from litespeech.providers.base import (
    ConnectionType,
    ProviderCapabilities,
    ProviderInfo,
    TTSProvider,
)

logger = logging.getLogger(__name__)


class AzureTTSProvider(TTSProvider):
    """
    Azure Speech Services TTS provider with event-driven streaming.

    Features:
    - Batch TTS via SDK
    - Streaming TTS with text stream support (LLM integration)
    - Event-driven audio delivery
    - Multiple voice options and languages

    Voice Specification:
    Supports two formats:
    1. Full format: voice="en-US-AvaMultilingualNeural", language=None
    2. Split format: voice="AvaMultilingualNeural", language="en-US"
    """

    DEFAULT_MODEL = "tts"  # Azure doesn't use model concept
    DEFAULT_VOICE = "en-US-AvaMultilingualNeural"

    def __init__(
        self,
        azure_speech_key: str | None = None,
        azure_speech_region: str | None = None,
        **kwargs,
    ):
        """
        Initialize Azure TTS provider.

        Args:
            azure_speech_key: Azure Speech key (defaults to AZURE_SPEECH_KEY env var)
            azure_speech_region: Azure region (defaults to AZURE_SPEECH_REGION env var)
            **kwargs: Additional options (ignored)
        """
        self._api_key = azure_speech_key or os.getenv("AZURE_SPEECH_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "azure", "azure_speech_key must be provided or AZURE_SPEECH_KEY env var must be set"
            )

        # Get region from parameter or environment
        self._region = azure_speech_region or os.getenv("AZURE_SPEECH_REGION")
        if not self._region:
            raise AuthenticationError(
                "azure",
                "azure_speech_region must be provided or AZURE_SPEECH_REGION env var must be set (e.g., 'eastus')",
            )

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="azure",
            display_name="Azure Speech Services",
            capabilities=ProviderCapabilities(
                tts_batch=True,
                tts_streaming=True,
                tts_input_streaming=True,  # Supports text_stream from LLMs
                asr_batch=False,
                asr_streaming=False,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=self.DEFAULT_MODEL,
            default_voice=self.DEFAULT_VOICE,
            supported_models=["tts"],
        )

    def _build_voice_name(self, voice: str | None, language: str | None) -> str:
        """
        Build full voice name from voice and language.

        Supports two formats:
        1. Full format: voice="en-US-AvaMultilingualNeural", language=None
        2. Split format: voice="AvaMultilingualNeural", language="en-US"

        Args:
            voice: Voice name (with or without locale prefix)
            language: Optional language/locale (e.g., "en-US")

        Returns:
            Full voice name (e.g., "en-US-AvaMultilingualNeural")
        """
        voice = voice or self.DEFAULT_VOICE

        # If voice already contains locale (e.g., "en-US-AvaMultilingualNeural")
        if "-" in voice and len(voice.split("-")[0]) == 2:
            return voice

        # If language provided, combine them (e.g., "en-US" + "AvaMultilingualNeural")
        if language:
            # Ensure language is in correct format (e.g., "en-US")
            if "-" not in language:
                raise ProviderError(
                    f"Invalid language format: '{language}'. "
                    f"Expected format: 'en-US', 'es-ES', etc.",
                    provider="azure",
                )
            return f"{language}-{voice}"

        # Voice doesn't contain locale and no language provided - use as-is
        # (might fail if not a valid full voice name)
        return voice

    async def text_to_speech(
        self,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "wav",
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech using Azure Speech SDK.

        Args:
            text: Text to convert
            model: Ignored (Azure doesn't use model concept)
            voice: Voice name (with or without locale prefix)
            language: Optional language/locale (e.g., "en-US")
            output_format: Output format ("wav", "mp3", or "raw")
            **kwargs: Additional arguments

        Returns:
            Audio bytes
        """
        # Build full voice name
        voice_name = self._build_voice_name(voice, language)

        # Configure speech config
        speech_config = speechsdk.SpeechConfig(subscription=self._api_key, region=self._region)
        speech_config.speech_synthesis_voice_name = voice_name

        # Set output format - match the working example
        if output_format.lower() == "raw":
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
            )
        elif output_format.lower() == "mp3":
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
            )
        else:
            # Default WAV format (matches working example)
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
            )

        # Create synthesizer (matching working example)
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )

        try:
            # Run blocking synthesis - EXACT same as working example
            def _synthesize():
                speech_synthesis_result = speech_synthesizer.speak_text_async(text)
                return speech_synthesis_result.get()

            # Wait for synthesis to complete
            speech_synthesis_result = await asyncio.to_thread(_synthesize)

            # Check if synthesis was successful
            if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Return audio data directly - same as streaming events use evt.result.audio_data
                # The result already contains the complete WAV/MP3/RAW audio based on output_format
                return speech_synthesis_result.audio_data
            elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
                cancellation = speech_synthesis_result.cancellation_details
                error_msg = f"Speech synthesis canceled: {cancellation.reason}"
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    error_msg += f" - {cancellation.error_details}"
                raise ProviderError(error_msg, provider="azure")
            else:
                raise ProviderError(f"Unexpected synthesis result: {speech_synthesis_result.reason}", provider="azure")

        except Exception as e:
            raise ProviderError(f"Azure TTS error: {e}", provider="azure") from e

    async def text_to_speech_stream(
        self,
        text: str | None = None,
        text_stream: AsyncIterator[str] | None = None,
        model: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        output_format: str = "raw",
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with streaming output.

        Supports both:
        - Regular text: Streams audio chunks as they're generated
        - Text stream: True LLM integration (text in → audio out)

        Args:
            text: Text to convert (for regular streaming)
            text_stream: Async iterator of text chunks (for LLM integration)
            model: Ignored (Azure doesn't use model concept)
            voice: Voice name (with or without locale prefix)
            language: Optional language/locale (e.g., "en-US")
            output_format: Output format ("wav" or "raw")
            **kwargs: Additional arguments

        Yields:
            Audio chunks
        """
        if not text and not text_stream:
            raise StreamingError("Either text or text_stream must be provided")

        # Build full voice name
        voice_name = self._build_voice_name(voice, language)

        # Configure speech
        # For text streaming, MUST use WebSocket v2 endpoint
        if text_stream:
            speech_config = speechsdk.SpeechConfig(
                endpoint=f"wss://{self._region}.tts.speech.microsoft.com/cognitiveservices/websocket/v2",
                subscription=self._api_key,
            )
            # Set timeout properties for text streaming
            speech_config.set_property(
                speechsdk.PropertyId.SpeechSynthesis_FrameTimeoutInterval, "100000000"
            )
            speech_config.set_property(
                speechsdk.PropertyId.SpeechSynthesis_RtfTimeoutThreshold, "10"
            )
        else:
            speech_config = speechsdk.SpeechConfig(subscription=self._api_key, region=self._region)

        speech_config.speech_synthesis_voice_name = voice_name

        # Set output format
        if output_format.lower() == "raw":
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
            )
        else:
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
            )

        # Create synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        # Storage for audio
        audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        synthesis_done = threading.Event()
        loop = asyncio.get_event_loop()

        # Event handlers
        def synthesizing_handler(evt):
            if evt.result.audio_data:
                loop.call_soon_threadsafe(audio_queue.put_nowait, evt.result.audio_data)

        def completed_handler(evt):
            loop.call_soon_threadsafe(audio_queue.put_nowait, None)
            synthesis_done.set()

        def canceled_handler(evt):
            error_msg = f"Synthesis canceled: {evt.result.cancellation_details.reason}"
            if evt.result.cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_msg += f" - {evt.result.cancellation_details.error_details}"
            logger.error(error_msg)
            loop.call_soon_threadsafe(audio_queue.put_nowait, None)
            synthesis_done.set()

        # Connect handlers
        synthesizer.synthesizing.connect(synthesizing_handler)
        synthesizer.synthesis_completed.connect(completed_handler)
        synthesizer.synthesis_canceled.connect(canceled_handler)

        try:
            if text_stream:
                # Text streaming mode (LLM integration)
                tts_request = speechsdk.SpeechSynthesisRequest(
                    input_type=speechsdk.SpeechSynthesisRequestInputType.TextStream
                )

                # Start synthesis task
                tts_task = synthesizer.speak_async(tts_request)

                # Stream text chunks
                async for chunk in text_stream:
                    if chunk:
                        tts_request.input_stream.write(chunk)

                # Close input stream to signal end
                tts_request.input_stream.close()

                # Yield audio chunks as they arrive
                while True:
                    audio_chunk = await audio_queue.get()
                    if audio_chunk is None:
                        break
                    yield audio_chunk

                # Wait for synthesis to complete
                await asyncio.to_thread(tts_task.get)

            else:
                # Regular text mode
                tts_task = synthesizer.speak_text_async(text)

                # Yield audio chunks as they arrive
                while True:
                    audio_chunk = await audio_queue.get()
                    if audio_chunk is None:
                        break
                    yield audio_chunk

                # Wait for synthesis to complete
                await asyncio.to_thread(tts_task.get)

        except Exception as e:
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"Azure TTS streaming error: {e}", provider="azure") from e

    async def close(self) -> None:
        """Close resources."""
        pass  # SDK handles cleanup automatically
