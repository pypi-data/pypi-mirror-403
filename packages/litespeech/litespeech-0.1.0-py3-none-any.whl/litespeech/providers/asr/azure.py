"""Azure Speech Service ASR provider implementation."""

import asyncio
import logging
import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    raise ImportError(
        "Azure Speech SDK not installed. "
        "Install with: pip install azure-cognitiveservices-speech"
    )

from litespeech.providers.base import (
    ASRProvider,
    ASRResult,
    ProviderInfo,
    ProviderCapabilities,
    ConnectionType,
)
from litespeech.exceptions import AuthenticationError, ProviderError, StreamingError

logger = logging.getLogger(__name__)


class AzureASRProvider(ASRProvider):
    """
    Azure Speech Service ASR provider with batch and streaming support.

    Features:
    - Batch speech-to-text via recognize_once
    - Streaming ASR with interim and final results
    - Multiple language support (BCP-47 format)
    """

    DEFAULT_LANGUAGE = "en-US"

    def __init__(
        self,
        azure_speech_key: str | None = None,
        azure_speech_region: str | None = None,
        **kwargs
    ):
        """
        Initialize Azure ASR provider.

        Args:
            azure_speech_key: Azure Speech Service key (defaults to AZURE_SPEECH_KEY env var)
            azure_speech_region: Azure region (defaults to AZURE_SPEECH_REGION env var)
            **kwargs: Additional options (ignored)
        """
        # Get API key from parameter or environment
        self._speech_key = azure_speech_key or os.getenv("AZURE_SPEECH_KEY")
        if not self._speech_key:
            raise AuthenticationError(
                "azure",
                "azure_speech_key must be provided or AZURE_SPEECH_KEY env var must be set"
            )

        # Get region from parameter or environment
        self._speech_region = azure_speech_region or os.getenv("AZURE_SPEECH_REGION")
        if not self._speech_region:
            raise AuthenticationError(
                "azure",
                "azure_speech_region must be provided or AZURE_SPEECH_REGION env var must be set (e.g., 'eastus')"
            )

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="azure",
            display_name="Azure Speech Service",
            capabilities=ProviderCapabilities(
                asr_batch=True,
                asr_streaming=True,
                tts_batch=False,
                tts_streaming=False,
            ),
            connection_type=ConnectionType.WEBSOCKET,
            default_model=None,  # Azure doesn't use models
            supported_models=[],
        )

    @classmethod
    def get_audio_specs(cls, model: str | None = None) -> dict:
        """
        Audio specs for Azure Speech Service.

        Azure accepts various formats but recommends:
        - 16kHz sample rate for best accuracy
        - WAV (PCM), MP3, Opus formats
        """
        return {
            "preferred": {"format": "wav"},
            "recommended_sample_rate": 16000,
        }

    def validate_language(self, language: str | None) -> str:
        """
        Validate and normalize language code for Azure.

        Azure uses BCP-47 format (e.g., "en-US", "de-DE").
        If None, defaults to "en-US".
        """
        if language is None:
            return self.DEFAULT_LANGUAGE

        # Azure expects BCP-47 format: language-REGION (e.g., "en-US", "de-DE")
        # Common patterns:
        # - "en-US", "en-GB", "es-ES", "fr-FR", etc.

        # For now, pass through as-is and let Azure validate
        # Azure will return an error if the format is invalid
        return language

    async def speech_to_text(
        self,
        audio: bytes,
        model: str | None = None,
        language: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Convert speech to text using Azure Speech Service (batch mode).

        Args:
            audio: Audio bytes (WAV, MP3, etc.)
            model: Not used (Azure doesn't have model parameter)
            language: Language code in BCP-47 format (e.g., "en-US", "de-DE")
            **kwargs: Additional options

        Returns:
            Transcribed text
        """
        language = self.validate_language(language)

        # Create speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=self._speech_key,
            region=self._speech_region
        )
        speech_config.speech_recognition_language = language

        # Azure SDK needs a file path, so write bytes to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_path.write_bytes(audio)

        try:
            # Create audio config from file
            audio_config = speechsdk.AudioConfig(filename=str(temp_path))

            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config
            )

            logger.debug(f"Starting Azure speech recognition (language: {language})")

            # Perform recognition (blocking)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                speech_recognizer.recognize_once_async().get
            )

            # Check result
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                logger.debug(f"Azure recognized: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("Azure: No speech could be recognized")
                return ""
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation = result.cancellation_details
                error_msg = f"Azure recognition canceled: {cancellation.reason}"
                if cancellation.reason == speechsdk.CancellationReason.Error:
                    error_msg += f"\nError details: {cancellation.error_details}"
                raise ProviderError(error_msg, provider="azure")
            else:
                raise ProviderError(
                    f"Azure returned unexpected reason: {result.reason}",
                    provider="azure"
                )

        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)

    async def speech_to_text_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        model: str | None = None,
        language: str | None = None,
        interim_results: bool = False,
        deduplicate: bool = True,
        sample_rate: int = 16000,
        channels: int = 1,
        encoding: str = "pcm_s16le",
        **kwargs: Any,
    ) -> AsyncIterator[ASRResult]:
        """
        Stream audio to Azure Speech Service for real-time transcription.

        Args:
            audio_stream: Async iterator of audio chunks (raw PCM bytes)
            model: Not used (Azure doesn't have model parameter)
            language: Language code in BCP-47 format (e.g., "en-US", "de-DE")
            interim_results: Whether to yield interim (partial) results
            deduplicate: Whether to deduplicate repeated transcripts
            sample_rate: Audio sample rate in Hz (default: 16000)
            channels: Number of audio channels (1=mono, 2=stereo)
            encoding: Audio encoding format (default: "pcm_s16le")
            **kwargs: Additional options

        Yields:
            ASRResult objects with text and is_final flag
        """
        language = self.validate_language(language)

        # Create speech config
        speech_config = speechsdk.SpeechConfig(
            subscription=self._speech_key,
            region=self._speech_region
        )
        speech_config.speech_recognition_language = language

        # Enable interim results if requested
        if interim_results:
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption,
                "TrueText"
            )

        # Determine bits per sample from encoding
        if "s16" in encoding or "16" in encoding:
            bits_per_sample = 16
        elif "s24" in encoding or "24" in encoding:
            bits_per_sample = 24
        elif "s32" in encoding or "32" in encoding:
            bits_per_sample = 32
        else:
            # Default to 16-bit
            bits_per_sample = 16
            logger.warning(
                f"Unknown encoding '{encoding}', assuming 16-bit PCM. "
                f"Use 'pcm_s16le' for 16-bit, 'pcm_s24le' for 24-bit, etc."
            )

        # Create audio format matching the stream
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=sample_rate,
            bits_per_sample=bits_per_sample,
            channels=channels
        )

        # Create push stream
        push_stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config
        )

        logger.debug(
            f"Azure streaming ASR started: {language}, {sample_rate}Hz, "
            f"{bits_per_sample}-bit, {channels}ch"
        )

        # Queue for results
        result_queue: asyncio.Queue[ASRResult | None] = asyncio.Queue()

        # Track for deduplication
        last_text = ""

        # Event handlers
        def recognizing_handler(evt):
            """Interim results (partial transcription)"""
            nonlocal last_text
            if interim_results and evt.result.text:
                # Deduplicate if requested
                if deduplicate and evt.result.text == last_text:
                    return

                # Update last_text for interim results (not final)
                last_text = evt.result.text
                result = ASRResult(text=evt.result.text, is_final=False)
                try:
                    result_queue.put_nowait(result)
                except asyncio.QueueFull:
                    logger.warning("Result queue full, dropping interim result")

        def recognized_handler(evt):
            """Final results"""
            nonlocal last_text
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Deduplicate if requested
                if deduplicate and evt.result.text == last_text:
                    return

                # Reset last_text for final results (next utterance starts fresh)
                last_text = ""
                result = ASRResult(text=evt.result.text, is_final=True)
                try:
                    result_queue.put_nowait(result)
                except asyncio.QueueFull:
                    logger.warning("Result queue full, dropping final result")

        def session_stopped_handler(evt):
            """Session stopped"""
            logger.debug("Azure session stopped")
            try:
                result_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

        def canceled_handler(evt):
            """Handle errors"""
            error_msg = f"Azure recognition canceled: {evt.cancellation_details.reason}"
            if evt.cancellation_details.reason == speechsdk.CancellationReason.Error:
                error_msg += f"\nError: {evt.cancellation_details.error_details}"
            logger.error(error_msg)
            try:
                result_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

        # Connect event handlers
        speech_recognizer.recognizing.connect(recognizing_handler)
        speech_recognizer.recognized.connect(recognized_handler)
        speech_recognizer.session_stopped.connect(session_stopped_handler)
        speech_recognizer.canceled.connect(canceled_handler)

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()

        try:
            # Task to send audio
            async def send_audio():
                try:
                    chunk_count = 0
                    async for chunk in audio_stream:
                        if chunk:
                            chunk_count += 1
                            # Push audio to Azure
                            push_stream.write(chunk)

                            if chunk_count % 100 == 0:
                                logger.debug(f"Sent {chunk_count} audio chunks to Azure")

                    logger.debug(f"Audio stream ended, sent {chunk_count} total chunks")
                    push_stream.close()

                except Exception as e:
                    logger.error(f"Error sending audio to Azure: {e}", exc_info=True)
                    push_stream.close()
                    raise StreamingError(f"Azure audio send error: {str(e)}")

            # Start sending audio in background
            send_task = asyncio.create_task(send_audio())

            # Yield results as they arrive
            try:
                while True:
                    result = await result_queue.get()
                    if result is None:
                        break
                    yield result
            finally:
                # Clean up
                send_task.cancel()
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass

                speech_recognizer.stop_continuous_recognition()
                push_stream.close()

        except Exception as e:
            if isinstance(e, StreamingError):
                raise
            raise StreamingError(f"Azure streaming error: {str(e)}")

    async def close(self) -> None:
        """Close any resources (Azure SDK manages its own connections)."""
        pass
