"""Configuration for API key parameter mapping."""

from typing import Dict, List

# Mapping of allowed parameter names to environment variable names
# This defines what parameters LiteSpeech.__init__ accepts
API_KEY_MAPPING: Dict[str, str] = {
    # ElevenLabs
    "elevenlabs_api_key": "ELEVENLABS_API_KEY",
    # OpenAI
    "openai_api_key": "OPENAI_API_KEY",
    # Deepgram
    "deepgram_api_key": "DEEPGRAM_API_KEY",
    # Cartesia
    "cartesia_api_key": "CARTESIA_API_KEY",
    # Azure Speech
    "azure_speech_key": "AZURE_SPEECH_KEY",
    "azure_speech_region": "AZURE_SPEECH_REGION",
    # Google Cloud (example of multi-key provider)
    "google_application_credentials": "GOOGLE_APPLICATION_CREDENTIALS",
    "google_project_id": "GOOGLE_PROJECT_ID",
}

# Mapping of provider names to their required environment variables
# This defines what env vars each provider needs
PROVIDER_ENV_VARS: Dict[str, List[str]] = {
    "elevenlabs": ["ELEVENLABS_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "deepgram": ["DEEPGRAM_API_KEY"],
    "cartesia": ["CARTESIA_API_KEY"],
    "azure": ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
    "google": ["GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_PROJECT_ID"],
}
