"""
Example: Detailed Provider Discovery with Metadata

This example demonstrates how to use the enhanced provider discovery methods
to get comprehensive information about available providers including model families,
language support, voice characteristics, use cases, and more.
"""

import os
import json
from pprint import pprint
from litespeech import LiteSpeech


def print_separator(title=""):
    """Print a formatted separator."""
    if title:
        print(f"\n{'=' * 80}")
        print(f"{title:^80}")
        print('=' * 80)
    else:
        print('-' * 80)


def example_basic_discovery():
    """Example 1: Basic provider discovery (default behavior)."""
    print_separator("BASIC PROVIDER DISCOVERY")

    ls = LiteSpeech()

    # Get basic provider information (without detailed metadata)
    tts_providers = ls.get_available_tts_providers()

    print(f"\nFound {len(tts_providers)} TTS provider(s)\n")

    for provider in tts_providers:
        print(f"Provider: {provider['display_name']}")
        print(f"  Models: {len(provider['models'])} available")
        print(f"  Voices: {len(provider['voices'])} available")
        print(f"  Supports streaming: {provider['supports_streaming']}")
        print(f"  Supports input streaming: {provider['supports_input_streaming']}")
        print()


def example_detailed_discovery():
    """Example 2: Detailed provider discovery with metadata."""
    print_separator("DETAILED PROVIDER DISCOVERY")

    ls = LiteSpeech()

    # Get detailed provider information (includes metadata from JSON)
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    print(f"\nFound {len(tts_providers)} TTS provider(s) with detailed metadata\n")

    for provider in tts_providers:
        print_separator()
        print(f"Provider: {provider['display_name']} ({provider['name']})")
        print()

        # Show basic info
        print("Basic Information:")
        print(f"  Connection: {provider['connection_type']}")
        print(f"  Default Model: {provider['default_model']}")
        print(f"  Language Format: {provider['language_format']}")
        print()

        # Show detailed metadata if available
        if 'detailed_metadata' in provider:
            metadata = provider['detailed_metadata']
            print("Detailed Metadata Available:")
            print(f"  Documentation: {metadata.get('documentation_url', 'N/A')}")
            print()

            # Model families
            if 'model_families' in metadata:
                print(f"Model Families ({len(metadata['model_families'])}):")
                for family in metadata['model_families']:
                    status = family.get('status', 'unknown')
                    status_label = f"[{status.upper()}]" if status == "legacy" else ""
                    print(f"  • {family['name']} {status_label}")
                    print(f"    {family['description']}")
                print()

            # Language summary
            if 'language_summary' in metadata:
                lang_summary = metadata['language_summary']
                print(f"Language Support:")
                print(f"  Total Languages: {lang_summary.get('total_languages', 'N/A')}")
                if 'languages' in lang_summary:
                    for lang in lang_summary['languages'][:5]:  # Show first 5
                        print(f"    • {lang['name']} ({lang['code']}): {lang.get('total_voices', 'N/A')} voices")
                    if len(lang_summary['languages']) > 5:
                        print(f"    ... and {len(lang_summary['languages']) - 5} more")
                print()

            # Special features
            if 'special_features' in metadata:
                print("Special Features:")
                for feature_name, feature_info in metadata['special_features'].items():
                    print(f"  • {feature_name.replace('_', ' ').title()}")
                    print(f"    {feature_info.get('description', 'N/A')}")
                print()

            # Notes
            if 'notes' in metadata:
                print("Notes:")
                for note in metadata['notes']:
                    print(f"  • {note}")
        else:
            print("(No detailed metadata available for this provider)")

        print()


def example_asr_detailed_discovery():
    """Example 3: Detailed ASR provider discovery."""
    print_separator("DETAILED ASR PROVIDER DISCOVERY")

    ls = LiteSpeech()

    # Get detailed ASR provider information
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    print(f"\nFound {len(asr_providers)} ASR provider(s) with detailed metadata\n")

    for provider in asr_providers:
        print_separator()
        print(f"Provider: {provider['display_name']} ({provider['name']})")
        print()

        # Show basic info
        print("Basic Information:")
        print(f"  Connection: {provider['connection_type']}")
        print(f"  Default Model: {provider['default_model']}")
        print(f"  Default Language: {provider['default_language']}")
        print()

        # Show detailed metadata if available
        if 'detailed_metadata' in provider:
            metadata = provider['detailed_metadata']

            # Model families
            if 'model_families' in metadata:
                print(f"Model Families ({len(metadata['model_families'])}):")
                for family in metadata['model_families']:
                    status = family.get('status', 'unknown')
                    status_label = f"[{status.upper()}]" if status != "current" else ""
                    print(f"\n  • {family['name']} {status_label}")
                    print(f"    {family['description']}")

                    if 'models' in family:
                        print(f"    Models: {len(family['models'])}")
                        for model in family['models'][:2]:  # Show first 2
                            print(f"      - {model['name']} (ID: {model['id']})")
                            if 'use_cases' in model and model['use_cases']:
                                use_cases = ', '.join(model['use_cases'][:3])
                                print(f"        Use cases: {use_cases}")
                        if len(family['models']) > 2:
                            print(f"      ... and {len(family['models']) - 2} more models")
                print()

            # Recommendations
            if 'recommendations' in metadata:
                print("Recommendations by Use Case:")
                for use_case, models in list(metadata['recommendations'].items())[:3]:
                    print(f"  • {use_case.replace('_', ' ').title()}: {', '.join(models)}")
                print()

        else:
            print("(No detailed metadata available for this provider)")

        print()


def example_export_metadata():
    """Example 4: Export detailed metadata to JSON file."""
    print_separator("EXPORT METADATA TO FILE")

    ls = LiteSpeech()

    # Get all provider information with metadata
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)
    asr_providers = ls.get_available_asr_providers(include_detailed_metadata=True)

    export_data = {
        "tts_providers": tts_providers,
        "asr_providers": asr_providers
    }

    output_file = "provider_metadata_export.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"\nExported metadata for {len(tts_providers)} TTS and {len(asr_providers)} ASR providers")
    print(f"Output file: {output_file}")
    print(f"File size: {os.path.getsize(output_file):,} bytes")
    print()


def example_filter_by_use_case():
    """Example 5: Filter providers by specific use cases."""
    print_separator("FILTER BY USE CASE")

    ls = LiteSpeech()

    # Get detailed TTS provider information
    tts_providers = ls.get_available_tts_providers(include_detailed_metadata=True)

    print("\nProviders with Code-Switching Support:\n")

    for provider in tts_providers:
        if 'detailed_metadata' not in provider:
            continue

        metadata = provider['detailed_metadata']

        # Check for code-switching feature
        if 'special_features' in metadata and 'code_switching' in metadata['special_features']:
            feature = metadata['special_features']['code_switching']
            print(f"✓ {provider['display_name']}")
            print(f"  {feature.get('description', '')}")
            if 'supported_voices' in feature:
                print(f"  Voices: {', '.join(feature['supported_voices'])}")
            print()


def main():
    """Run all examples."""
    print("=" * 80)
    print("LITESPEECH DETAILED PROVIDER DISCOVERY EXAMPLES")
    print("=" * 80)

    # Example 1: Basic discovery (without detailed metadata)
    example_basic_discovery()

    # Example 2: Detailed TTS discovery
    example_detailed_discovery()

    # Example 3: Detailed ASR discovery
    example_asr_detailed_discovery()

    # Example 4: Export to file
    example_export_metadata()

    # Example 5: Filter by use case
    example_filter_by_use_case()

    print_separator("EXAMPLES COMPLETE")
    print()


if __name__ == "__main__":
    main()
