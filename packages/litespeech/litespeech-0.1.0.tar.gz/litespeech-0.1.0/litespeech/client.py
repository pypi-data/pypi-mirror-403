"""Main LiteSpeech client interface."""

import asyncio
import queue
import threading
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any, Union

from litespeech.providers.registry import (
    ProviderRegistry,
    get_registry,
    parse_provider_string,
)
from litespeech.adapters.auto_detect import adapt_to_text_stream, is_llm_stream
from litespeech.audio.conversion import convert_to_provider_format
from litespeech.exceptions import (
    LiteSpeechError,
    ProviderNotFoundError,
    UnsupportedOperationError,
)
from litespeech.utils.logging import get_logger


# Type alias for audio input
AudioInput = Union[str, bytes, Path]


class SyncInterface:
    """
    Synchronous interface wrapper for LiteSpeech.

    Provides synchronous versions of all async methods by running
    them in an event loop.
    """

    def __init__(self, async_client: "LiteSpeech"):
        self._async = async_client

    def _run(self, coro: Any) -> Any:
        """Run a coroutine synchronously."""
        try:
            loop = asyncio.get_running_loop()
            # If there's a running loop, we can't use asyncio.run
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(coro)

    def text_to_speech(
        self,
        text: str,
        provider: str,
        output_format: str = "mp3",
        **kwargs: Any,
    ) -> bytes:
        """Synchronous text-to-speech."""
        return self._run(
            self._async.text_to_speech(
                text=text,
                provider=provider,
                output_format=output_format,
                **kwargs,
            )
        )

    def text_to_speech_stream(
        self,
        text: str | None = None,
        text_stream: Any | None = None,
        provider: str = "",
        output_format: str = "pcm_16000",
        **kwargs: Any,
    ) -> Iterator[bytes]:
        """
        Synchronous streaming text-to-speech.

        Returns a synchronous iterator of audio chunks.
        """
        # Use thread-safe queue to bridge async->sync iteration
        chunk_queue: queue.Queue[bytes | None] = queue.Queue()
        exception_holder: list[Exception] = []

        async def producer():
            """Async producer that fills the queue."""
            try:
                async for chunk in self._async.text_to_speech_stream(
                    text=text,
                    text_stream=text_stream,
                    provider=provider,
                    output_format=output_format,
                    **kwargs,
                ):
                    chunk_queue.put(chunk)
            except Exception as e:
                exception_holder.append(e)
            finally:
                chunk_queue.put(None)  # Signal end

        def run_producer():
            """Run producer in event loop."""
            try:
                loop = asyncio.get_running_loop()
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(producer())
            except RuntimeError:
                asyncio.run(producer())

        # Start producer in background thread
        producer_thread = threading.Thread(target=run_producer, daemon=True)
        producer_thread.start()

        # Yield chunks as they arrive
        while True:
            chunk = chunk_queue.get()
            if chunk is None:
                break
            yield chunk

        # Check for exceptions
        if exception_holder:
            raise exception_holder[0]

    def speech_to_text(
        self,
        audio: AudioInput,
        provider: str,
        language: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous speech-to-text."""
        return self._run(
            self._async.speech_to_text(
                audio=audio,
                provider=provider,
                language=language,
                **kwargs,
            )
        )

    def speech_to_text_stream(
        self,
        audio_stream: Iterator[bytes],
        provider: str,
        language: str | None = None,
        interim_results: bool = False,
        deduplicate: bool = True,
        sample_rate: int = 16000,
        **kwargs: Any,
    ) -> Iterator["ASRResult"]:
        """
        Synchronous streaming speech-to-text.

        Note: Converts sync iterator to async for processing.

        Args:
            audio_stream: Iterator of audio chunks
            provider: Provider string
            language: Language code
            interim_results: If False, only yield final transcripts.
                           If True, yield both interim and final (marked with is_final flag)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
            sample_rate: Sample rate of audio in Hz (default: 16000)
            **kwargs: Additional options

        Yields:
            ASRResult objects with text and is_final flag
        """
        # Use thread-safe queue to bridge async->sync iteration
        result_queue: queue.Queue[Any] = queue.Queue()
        exception_holder: list[Exception] = []

        async def async_audio_stream() -> AsyncIterator[bytes]:
            """Convert sync iterator to async iterator."""
            for chunk in audio_stream:
                yield chunk

        async def producer():
            """Async producer that fills the queue."""
            try:
                async for result in self._async.speech_to_text_stream(
                    audio_stream=async_audio_stream(),
                    provider=provider,
                    language=language,
                    interim_results=interim_results,
                    deduplicate=deduplicate,
                    sample_rate=sample_rate,
                    **kwargs,
                ):
                    result_queue.put(result)
            except Exception as e:
                exception_holder.append(e)
            finally:
                result_queue.put(None)  # Signal end

        def run_producer():
            """Run producer in event loop."""
            try:
                loop = asyncio.get_running_loop()
                import nest_asyncio
                nest_asyncio.apply()
                loop.run_until_complete(producer())
            except RuntimeError:
                asyncio.run(producer())

        # Start producer in background thread
        producer_thread = threading.Thread(target=run_producer, daemon=True)
        producer_thread.start()

        # Yield results as they arrive
        while True:
            result = result_queue.get()
            if result is None:
                break
            yield result

        # Check for exceptions
        if exception_holder:
            raise exception_holder[0]


class LiteSpeech:
    """
    Main client interface for all speech operations.

    Provides unified access to multiple TTS and ASR providers
    with support for both batch and streaming operations.

    Features:
    - Automatic API key detection from environment
    - Provider registry with capability detection
    - Stream adapter auto-detection for LLM integrations
    - Unified error handling
    - Both async (primary) and sync interfaces

    Example:
        >>> from litespeech import LiteSpeech
        >>>
        >>> ls = LiteSpeech()
        >>>
        >>> # Async usage
        >>> audio = await ls.text_to_speech(
        ...     text="Hello world",
        ...     provider="elevenlabs/eleven_turbo_v2_5/adam"
        ... )
        >>>
        >>> # Sync usage
        >>> audio = ls.sync.text_to_speech(
        ...     text="Hello world",
        ...     provider="elevenlabs/eleven_turbo_v2_5/adam"
        ... )
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize LiteSpeech client.

        All kwargs are passed directly to providers when instantiated.
        Each provider extracts what it needs and ignores the rest.

        Each provider will validate its own parameters and check
        environment variables for missing credentials.

        Example:
            >>> # Use environment variables only
            >>> ls = LiteSpeech()

            >>> # Pass specific provider credentials
            >>> ls = LiteSpeech(
            ...     elevenlabs_api_key="sk_...",
            ...     openai_api_key="sk-proj-...",
            ...     azure_speech_key="...",
            ...     azure_speech_region="eastus",
            ... )
        """
        self._registry = get_registry()
        self._init_kwargs = kwargs
        self._logger = get_logger()
        self._sync: SyncInterface | None = None

    @property
    def sync(self) -> SyncInterface:
        """Get synchronous interface."""
        if self._sync is None:
            self._sync = SyncInterface(self)
        return self._sync

    @property
    def registry(self) -> ProviderRegistry:
        """Get provider registry."""
        return self._registry

    # ========================================
    # Text-to-Speech Methods
    # ========================================

    async def text_to_speech(
        self,
        text: str,
        provider: str,
        voice: str | None = None,
        language: str | None = None,
        output_format: str | None = None,
        **kwargs: Any,
    ) -> bytes:
        """
        Convert text to speech (batch mode).

        Args:
            text: Text to convert
            provider: Provider string (format: "provider/model" e.g., "elevenlabs/eleven_turbo_v2_5")
            voice: Voice ID or name (provider-specific)
            language: Language code (e.g., "en", "es", "fr")
            output_format: Output audio format (provider-specific, e.g., "mp3_44100_128" for ElevenLabs).
                          If None, uses provider's default format.
            **kwargs: Additional provider-specific options

        Returns:
            Audio bytes in specified format

        Example:
            >>> audio = await ls.text_to_speech(
            ...     text="Hello world",
            ...     provider="elevenlabs/eleven_turbo_v2_5",
            ...     voice="JBFqnCBsd6RMkjVDRZzb",
            ...     language="en"
            ... )
            >>> with open("output.mp3", "wb") as f:
            ...     f.write(audio)
        """
        parsed = parse_provider_string(provider)

        # Get provider CLASS and instantiate with all kwargs
        provider_class = self._registry.get_tts_provider_class(provider)
        all_kwargs = {**self._init_kwargs, **kwargs}
        tts_provider = provider_class(**all_kwargs)

        if not tts_provider.capabilities.tts_batch:
            raise UnsupportedOperationError(parsed.provider, "tts_batch")

        # Build kwargs for provider method
        tts_kwargs = {
            "text": text,
            "model": parsed.model,
            **kwargs,
        }

        # Add optional parameters if provided
        if voice is not None:
            tts_kwargs["voice"] = voice
        if language is not None:
            tts_kwargs["language"] = language
        if output_format is not None:
            tts_kwargs["output_format"] = output_format

        return await tts_provider.text_to_speech(**tts_kwargs)

    async def text_to_speech_stream(
        self,
        text: str | None = None,
        text_stream: AsyncIterator[str] | Any | None = None,
        provider: str = "",
        voice: str | None = None,
        language: str | None = None,
        output_format: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[bytes]:
        """
        Convert text or text stream to streaming audio.

        Supports:
        - Static text with streaming audio output
        - Token stream (from LLM) with streaming audio output
        - Auto-detects OpenAI, Anthropic, LiteLLM streams

        Args:
            text: Static text to convert (mutually exclusive with text_stream)
            text_stream: Async iterator of text chunks or LLM completion stream
            provider: Provider string (format: "provider/model" e.g., "elevenlabs/eleven_turbo_v2_5")
            voice: Voice ID or name (provider-specific)
            language: Language code (e.g., "en", "es", "fr")
            output_format: Output format (provider-specific, e.g., "pcm_16000" for raw PCM).
                          If None, uses provider's default format.
            **kwargs: Additional provider-specific options

        Yields:
            Audio chunks

        Example:
            >>> # From static text
            >>> async for chunk in ls.text_to_speech_stream(
            ...     text="Hello world",
            ...     provider="elevenlabs/eleven_turbo_v2_5",
            ...     voice="JBFqnCBsd6RMkjVDRZzb",
            ...     language="en"
            ... ):
            ...     await play_audio(chunk)

            >>> # From LLM stream
            >>> llm_stream = await openai.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Tell me a story"}],
            ...     stream=True
            ... )
            >>> async for chunk in ls.text_to_speech_stream(
            ...     text_stream=llm_stream,
            ...     provider="elevenlabs/eleven_turbo_v2_5",
            ...     voice="JBFqnCBsd6RMkjVDRZzb"
            ... ):
            ...     await play_audio(chunk)
        """
        if not provider:
            raise ValueError("provider is required")

        if text is None and text_stream is None:
            raise ValueError("Either text or text_stream must be provided")

        if text is not None and text_stream is not None:
            raise ValueError("Cannot provide both text and text_stream")

        parsed = parse_provider_string(provider)

        # Get provider CLASS and instantiate with all kwargs
        provider_class = self._registry.get_tts_provider_class(provider)
        all_kwargs = {**self._init_kwargs, **kwargs}
        tts_provider = provider_class(**all_kwargs)

        if not tts_provider.capabilities.tts_streaming:
            raise UnsupportedOperationError(parsed.provider, "tts_streaming")

        # Create text stream from input
        if text is not None:
            # Single text string

            async def single_text_stream() -> AsyncIterator[str]:
                yield text

            adapted_stream = single_text_stream()
        else:
            # Adapt LLM stream or use as-is
            adapted_stream = adapt_to_text_stream(text_stream)

        # Build kwargs for provider
        stream_kwargs = {
            "text_stream": adapted_stream,
            "model": parsed.model,
            **kwargs,
        }

        # Add optional parameters if provided
        if voice is not None:
            stream_kwargs["voice"] = voice
        if language is not None:
            stream_kwargs["language"] = language
        if output_format is not None:
            stream_kwargs["output_format"] = output_format

        async for chunk in tts_provider.text_to_speech_stream(**stream_kwargs):
            yield chunk

    # ========================================
    # Speech-to-Text Methods
    # ========================================

    async def speech_to_text(
        self,
        audio: AudioInput,
        provider: str,
        language: str | None = None,
        preprocess: bool = True,
        **kwargs: Any,
    ) -> str:
        """
        Convert speech to text (batch mode).

        Args:
            audio: Audio as file path, bytes, or Path object
            provider: Provider string (e.g., "deepgram/nova-2")
            language: Language code (e.g., "en")
            preprocess: Whether to auto-convert audio format (default: True)
            **kwargs: Additional provider-specific options

        Returns:
            Transcribed text

        Example:
            >>> text = await ls.speech_to_text(
            ...     audio="recording.mp3",
            ...     provider="deepgram/nova-2"
            ... )
            >>> print(text)
        """
        from litespeech.audio.detection import detect_audio_format
        from litespeech.audio.specs import get_provider_spec

        parsed = parse_provider_string(provider)

        # Get provider CLASS and instantiate with all kwargs
        provider_class = self._registry.get_asr_provider_class(provider)
        all_kwargs = {**self._init_kwargs, **kwargs}
        asr_provider = provider_class(**all_kwargs)

        if not asr_provider.capabilities.asr_batch:
            raise UnsupportedOperationError(parsed.provider, "asr_batch")

        # Load audio bytes
        if isinstance(audio, (str, Path)):
            path = Path(audio)
            if not path.exists():
                raise LiteSpeechError(f"Audio file not found: {path}")
            audio_bytes = path.read_bytes()
        else:
            audio_bytes = audio

        # Detect audio format to extract sample rate
        audio_info = detect_audio_format(audio_bytes)

        # Preprocess audio if needed
        if preprocess:
            provider_model = f"{parsed.provider}/{parsed.model or 'default'}"
            audio_bytes = convert_to_provider_format(audio_bytes, provider_model)

        # Check if sample rate is not recommended and warn
        provider_model = f"{parsed.provider}/{parsed.model or 'default'}"
        spec = get_provider_spec(provider_model)
        if spec and "recommended_sample_rate" in spec:
            recommended = spec["recommended_sample_rate"]
            if audio_info.sample_rate != recommended:
                self._logger.warning(
                    f"Audio sample rate is {audio_info.sample_rate}Hz. "
                    f"{parsed.provider} recommends {recommended}Hz for best performance."
                )

        return await asr_provider.speech_to_text(
            audio=audio_bytes,
            model=parsed.model,
            language=language,
            **kwargs,
        )

    async def speech_to_text_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        provider: str,
        language: str | None = None,
        interim_results: bool = False,
        deduplicate: bool = True,
        sample_rate: int = 16000,
        **kwargs: Any,
    ) -> AsyncIterator["ASRResult"]:
        """
        Convert streaming audio to streaming text.

        IMPORTANT: You must specify the CORRECT audio parameters that match your stream!
        - sample_rate: Must match your actual audio sample rate
        - channels: Must match your actual channel count (1=mono, 2=stereo)
        - encoding: Must match your audio encoding format

        The stream validator will:
        - Automatically detect and strip WAV headers if present
        - Warn you if WAV header doesn't match your parameters
        - Validate your parameters against provider requirements
        - Give clear errors if there are mismatches

        Args:
            audio_stream: Async iterator of audio chunks (raw PCM or WAV)
            provider: Provider string (e.g., "deepgram/nova-2")
            language: Language code
            interim_results: If False, only yield final transcripts.
                           If True, yield both interim and final (marked with is_final flag)
            deduplicate: Whether to deduplicate consecutive identical transcripts (default: True)
                        Set to False if you want every message from the provider
            sample_rate: Sample rate of YOUR audio stream in Hz (default: 16000)
                        ⚠️  Must match actual audio or transcription will fail!
            **kwargs: Additional provider-specific options
                     - channels: Number of channels (1=mono, 2=stereo, default: 1)
                     - encoding: Audio encoding (e.g., "linear16", "mulaw")

        Yields:
            ASRResult objects with text and is_final flag

        Example:
            >>> # Microphone streaming (16kHz mono PCM)
            >>> async def microphone_stream():
            ...     # Yield raw PCM audio chunks from microphone
            ...     ...
            >>>
            >>> async for result in ls.speech_to_text_stream(
            ...     audio_stream=microphone_stream(),
            ...     provider="deepgram/nova-2",
            ...     sample_rate=16000,    # ⚠️  Must match your mic!
            ...     channels=1,           # Mono
            ...     interim_results=True
            ... ):
            ...     if result.is_final:
            ...         print(f"✓ {result.text}")
            ...     else:
            ...         print(f"  {result.text}...", end="\r", flush=True)
        """
        from litespeech.audio.specs import get_provider_spec
        from litespeech.audio.stream_validator import AudioStreamValidator

        parsed = parse_provider_string(provider)

        # Get provider CLASS and instantiate with all kwargs
        provider_class = self._registry.get_asr_provider_class(provider)
        all_kwargs = {**self._init_kwargs, **kwargs}
        asr_provider = provider_class(**all_kwargs)

        if not asr_provider.capabilities.asr_streaming:
            raise UnsupportedOperationError(parsed.provider, "asr_streaming")

        # Get provider spec for validation
        provider_model = f"{parsed.provider}/{parsed.model or 'default'}"
        spec = get_provider_spec(provider_model)

        # Extract user parameters
        user_channels = kwargs.get("channels", 1)
        user_encoding = kwargs.get("encoding", "linear16")

        # Create validator
        validator = AudioStreamValidator(
            provider_name=parsed.provider,
            user_sample_rate=sample_rate,
            user_channels=user_channels,
            user_encoding=user_encoding,
            provider_spec=spec,
        )

        # Pass sample_rate in kwargs for provider
        kwargs["sample_rate"] = sample_rate

        # Validate and transform stream
        validated_stream = validator.validate_and_transform(audio_stream)

        async for chunk in asr_provider.speech_to_text_stream(
            audio_stream=validated_stream,
            model=parsed.model,
            language=language,
            interim_results=interim_results,
            deduplicate=deduplicate,
            **kwargs,
        ):
            yield chunk

    # ========================================
    # Utility Methods
    # ========================================

    def list_providers(
        self,
        capability: str | None = None,
    ) -> dict[str, list[str]]:
        """
        List available providers.

        Args:
            capability: Filter by capability (tts, asr, tts_streaming, asr_streaming)

        Returns:
            Dict with 'tts' and 'asr' provider lists
        """
        tts_providers = self._registry.list_tts_providers()
        asr_providers = self._registry.list_asr_providers()

        if capability:
            if capability in ("tts", "tts_batch"):
                return {"tts": tts_providers, "asr": []}
            elif capability in ("asr", "asr_batch"):
                return {"tts": [], "asr": asr_providers}
            elif capability == "tts_streaming":
                tts_providers = [
                    p for p in tts_providers if self._registry.supports_tts_streaming(p)
                ]
                return {"tts": tts_providers, "asr": []}
            elif capability == "asr_streaming":
                asr_providers = [
                    p for p in asr_providers if self._registry.supports_asr_streaming(p)
                ]
                return {"tts": [], "asr": asr_providers}

        return {"tts": tts_providers, "asr": asr_providers}

    def supports_streaming(self, provider: str, operation: str) -> bool:
        """
        Check if provider supports streaming for an operation.

        Args:
            provider: Provider string
            operation: "tts" or "asr"

        Returns:
            True if streaming is supported
        """
        if operation == "tts":
            return self._registry.supports_tts_streaming(provider)
        elif operation == "asr":
            return self._registry.supports_asr_streaming(provider)
        return False

    async def close(self) -> None:
        """Close method for compatibility - providers manage their own connections."""
        pass

    async def __aenter__(self) -> "LiteSpeech":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
