"""LLM stream adapters for LiteSpeech."""

from litespeech.adapters.base import StreamAdapter
from litespeech.adapters.openai_adapter import OpenAIStreamAdapter
from litespeech.adapters.anthropic_adapter import AnthropicStreamAdapter
from litespeech.adapters.litellm_adapter import LiteLLMStreamAdapter
from litespeech.adapters.auto_detect import detect_and_adapt, is_llm_stream

__all__ = [
    "StreamAdapter",
    "OpenAIStreamAdapter",
    "AnthropicStreamAdapter",
    "LiteLLMStreamAdapter",
    "detect_and_adapt",
    "is_llm_stream",
]
