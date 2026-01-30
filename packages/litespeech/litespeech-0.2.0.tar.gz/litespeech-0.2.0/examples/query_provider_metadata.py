"""
Example: Query Provider Metadata

Demonstrates how to query and filter provider metadata to find
specific models, voices, or capabilities that match your requirements.
"""

from litespeech import LiteSpeech


def find_voice_agent_optimized_voices():
    """Find voices optimized for voice agents (conversational AI)."""
    print("=" * 80)
    print("VOICES OPTIMIZED FOR VOICE AGENTS")
    print("=" * 80)

    ls = LiteSpeech()
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    for provider in tts_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']
        print(f"\n{provider['display_name']}:")

        # Check recommendations
        recommendations = metadata.get('recommendations', {})
        if 'voice_agents' in recommendations:
            agent_voices = recommendations['voice_agents']
            print(f"  Recommended voices: {', '.join(agent_voices)}")

        # Look through voice details
        for family in metadata.get('model_families', []):
            for language in family.get('languages', []):
                for voice in language.get('voices', []):
                    if 'voice-agents' in voice.get('use_cases', []) or 'conversational-ai' in voice.get('use_cases', []):
                        print(f"    - {voice['name']} (ID: {voice['id']})")
                        print(f"      Style: {voice.get('characteristics', {}).get('style', 'N/A')}")
                        if voice.get('notes'):
                            print(f"      Note: {voice['notes']}")


def find_multilingual_models():
    """Find models with the broadest language support."""
    print("\n" + "=" * 80)
    print("MODELS WITH MULTILINGUAL SUPPORT")
    print("=" * 80)

    ls = LiteSpeech()

    # TTS providers
    print("\nTTS Providers:")
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    for provider in tts_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']
        lang_summary = metadata.get('language_summary', {})
        total_langs = lang_summary.get('total_languages', 0)

        if total_langs > 0:
            print(f"  {provider['display_name']}: {total_langs} languages")

    # ASR providers
    print("\nASR Providers:")
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    for provider in asr_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']
        lang_summary = metadata.get('language_summary', {})

        for model_family, lang_count in lang_summary.items():
            if 'languages' not in model_family.lower():
                print(f"  {provider['display_name']} ({model_family}): {lang_count}")


def find_real_time_optimized_models():
    """Find models optimized for real-time/streaming use."""
    print("\n" + "=" * 80)
    print("MODELS OPTIMIZED FOR REAL-TIME")
    print("=" * 80)

    ls = LiteSpeech()

    # ASR providers
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    for provider in asr_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']

        print(f"\n{provider['display_name']}:")

        # Check recommendations
        recommendations = metadata.get('recommendations', {})
        if 'real_time_agents' in recommendations:
            print(f"  Recommended for real-time: {', '.join(recommendations['real_time_agents'])}")

        # Look for real-time features
        for family in metadata.get('model_families', []):
            for model in family.get('models', []):
                features = model.get('features', [])

                # Check if model has real-time related features
                realtime_features = [f for f in features if 'real-time' in f or 'latency' in f or 'streaming' in f]

                if realtime_features:
                    print(f"  Model: {model['name']}")
                    print(f"    Features: {', '.join(realtime_features)}")

                    performance = model.get('performance', {})
                    if 'latency' in performance:
                        print(f"    Latency: {performance['latency']}")


def find_models_with_special_features():
    """Find models with special features like emotion control, code-switching, etc."""
    print("\n" + "=" * 80)
    print("MODELS WITH SPECIAL FEATURES")
    print("=" * 80)

    ls = LiteSpeech()
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    for provider in tts_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']
        special_features = metadata.get('special_features', {})

        if special_features:
            print(f"\n{provider['display_name']}:")
            for feature_name, feature_info in special_features.items():
                print(f"  {feature_name.replace('_', ' ').title()}:")
                print(f"    {feature_info.get('description', 'N/A')}")

                if 'supported_voices' in feature_info:
                    supported = feature_info['supported_voices']
                    if supported == 'all':
                        print(f"    Supported by: All voices")
                    else:
                        print(f"    Supported by: {', '.join(supported)}")


def find_production_ready_models():
    """Find models recommended for production use."""
    print("\n" + "=" * 80)
    print("PRODUCTION-READY MODELS")
    print("=" * 80)

    ls = LiteSpeech()

    # TTS providers
    print("\nTTS Providers:")
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    for provider in tts_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']

        # Check recommendations
        recommendations = metadata.get('recommendations', {})
        if 'production_model' in recommendations:
            print(f"  {provider['display_name']}: {recommendations['production_model']}")

        # Look for current/stable models
        for family in metadata.get('model_families', []):
            if family.get('status') == 'current':
                print(f"  {provider['display_name']} - {family['name']} [CURRENT]")

                # Show model variants recommended for production
                for variant in family.get('model_variants', []):
                    if variant.get('recommended_for') == 'production':
                        print(f"    Recommended: {variant['name']}")

    # ASR providers
    print("\nASR Providers:")
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    for provider in asr_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']

        # Check recommendations
        recommendations = metadata.get('recommendations', {})
        if 'production' in recommendations:
            print(f"  {provider['display_name']}: {', '.join(recommendations['production'])}")


def find_models_for_noisy_environments():
    """Find ASR models optimized for noisy environments."""
    print("\n" + "=" * 80)
    print("MODELS FOR NOISY ENVIRONMENTS")
    print("=" * 80)

    ls = LiteSpeech()
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    for provider in asr_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']

        # Check recommendations
        recommendations = metadata.get('recommendations', {})
        if 'noisy_environments' in recommendations:
            print(f"\n{provider['display_name']}:")
            print(f"  Recommended: {', '.join(recommendations['noisy_environments'])}")

        # Check key capabilities
        capabilities = metadata.get('key_capabilities', {})
        if 'noise_resilience' in capabilities:
            noise_cap = capabilities['noise_resilience']
            print(f"  Capability: {noise_cap.get('description', 'N/A')}")
            print(f"  Benefit: {noise_cap.get('benefit', 'N/A')}")


def main():
    """Run all query examples."""

    # Query 1: Voice agent optimized voices
    find_voice_agent_optimized_voices()

    # Query 2: Multilingual support
    find_multilingual_models()

    # Query 3: Real-time optimization
    find_real_time_optimized_models()

    # Query 4: Special features
    find_models_with_special_features()

    # Query 5: Production-ready models
    find_production_ready_models()

    # Query 6: Noisy environments
    find_models_for_noisy_environments()

    print("\n" + "=" * 80)
    print("QUERY EXAMPLES COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
