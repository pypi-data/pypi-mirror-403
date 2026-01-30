"""
Example: Discovering Available Providers

This example demonstrates how to use the provider discovery methods
to programmatically find which TTS and ASR providers are available
based on your configured API keys.
"""

import os
from litespeech import LiteSpeech


def main():
    """Demonstrate provider discovery functionality."""

    # Initialize LiteSpeech (reads from environment variables)
    ls = LiteSpeech()

    print("=" * 60)
    print("PROVIDER DISCOVERY EXAMPLE")
    print("=" * 60)
    print()

    # Discover available TTS providers
    print("Available TTS (Text-to-Speech) Providers:")
    print("-" * 60)

    tts_providers = ls.get_available_tts_providers()

    if not tts_providers:
        print("No TTS providers available. Configure API keys in environment.")
        print("Example: export DEEPGRAM_API_KEY=your_key_here")
    else:
        for provider in tts_providers:
            print(f"\n{provider['display_name']} ({provider['name']})")
            print(f"  Connection Type: {provider['connection_type']}")
            print(f"  Default Model: {provider['default_model']}")
            print(f"  Models: {', '.join(provider['models'][:3])}..." if len(provider['models']) > 3 else f"  Models: {', '.join(provider['models'])}")

            if provider['voices']:
                print(f"  Voices: {len(provider['voices'])} available")

            print(f"  Capabilities:")
            print(f"    - Batch: {provider['supports_batch']}")
            print(f"    - Streaming: {provider['supports_streaming']}")
            print(f"    - Input Streaming: {provider['supports_input_streaming']}")

            print(f"  Language:")
            print(f"    - Default: {provider['default_language'] or 'N/A'}")
            print(f"    - Format: {provider['language_format']}")

    print()
    print("=" * 60)
    print()

    # Discover available ASR providers
    print("Available ASR (Speech-to-Text) Providers:")
    print("-" * 60)

    asr_providers = ls.get_available_asr_providers()

    if not asr_providers:
        print("No ASR providers available. Configure API keys in environment.")
        print("Example: export DEEPGRAM_API_KEY=your_key_here")
    else:
        for provider in asr_providers:
            print(f"\n{provider['display_name']} ({provider['name']})")
            print(f"  Connection Type: {provider['connection_type']}")
            print(f"  Default Model: {provider['default_model']}")
            print(f"  Models: {', '.join(provider['models'][:3])}..." if len(provider['models']) > 3 else f"  Models: {', '.join(provider['models'])}")

            print(f"  Capabilities:")
            print(f"    - Batch: {provider['supports_batch']}")
            print(f"    - Streaming: {provider['supports_streaming']}")

            print(f"  Language:")
            print(f"    - Default: {provider['default_language'] or 'N/A'}")
            print(f"    - Format: {provider['language_format']}")

    print()
    print("=" * 60)
    print()

    # Show which providers support streaming
    print("Streaming Capabilities Summary:")
    print("-" * 60)

    tts_streaming = [p['display_name'] for p in tts_providers if p['supports_streaming']]
    asr_streaming = [p['display_name'] for p in asr_providers if p['supports_streaming']]

    print(f"TTS Streaming: {', '.join(tts_streaming) or 'None'}")
    print(f"ASR Streaming: {', '.join(asr_streaming) or 'None'}")

    print()
    print("=" * 60)
    print()

    # Suggest which provider to use
    if tts_providers or asr_providers:
        print("Quick Start Recommendations:")
        print("-" * 60)

        if tts_providers:
            best_tts = tts_providers[0]  # First available
            print(f"\nFor TTS, try: provider='{best_tts['name']}'")
            if best_tts['default_model']:
                print(f"  Full format: provider='{best_tts['name']}/{best_tts['default_model']}'")

        if asr_providers:
            best_asr = asr_providers[0]  # First available
            print(f"\nFor ASR, try: provider='{best_asr['name']}'")
            if best_asr['default_model']:
                print(f"  Full format: provider='{best_asr['name']}/{best_asr['default_model']}'")

        print()
        print("=" * 60)


if __name__ == "__main__":
    main()
