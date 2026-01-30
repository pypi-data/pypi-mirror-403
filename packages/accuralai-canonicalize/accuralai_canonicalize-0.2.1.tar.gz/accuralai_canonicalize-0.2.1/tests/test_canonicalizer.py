import pytest

from accuralai_core.contracts.models import GenerateRequest

from accuralai_canonicalize.canonicalizer import (
    CanonicalizerOptions,
    StandardCanonicalizer,
    CanonicalizationMetrics,
    build_canonicalizer,
    _compress_whitespace,
    _deduplicate_repeated_phrases,
    _optimize_prompt_structure,
    _extract_key_phrases,
)


@pytest.mark.anyio("asyncio")
async def test_advanced_canonicalizer_generates_cache_key_and_normalizes():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            default_tags=["Demo"],
            cache_key_metadata_fields=["topic"],
            metadata_defaults={"topic": "general"},
            track_metrics=True,
        )
    )

    request = GenerateRequest(prompt="  Hello   World  ", tags=["Test"])
    canonical = await canonicalizer.canonicalize(request)

    # Whitespace is preserved (not compressed)
    assert canonical.prompt == "  Hello   World  "
    assert canonical.tags == ["demo", "test"]
    assert canonical.metadata["topic"] == "general"
    assert canonical.cache_key is not None
    assert isinstance(canonicalizer.metrics, CanonicalizationMetrics)


@pytest.mark.anyio("asyncio")
async def test_factory_uses_plugin_settings():
    canonicalizer = await build_canonicalizer(
        config={"default_tags": ["One", "Two"], "normalize_tags": True}
    )

    request = GenerateRequest(prompt="hey", tags=["alpha"])
    canonical = await canonicalizer.canonicalize(request)

    assert canonical.tags == ["alpha", "one", "two"]


@pytest.mark.anyio("asyncio")
async def test_advanced_canonicalizer_with_full_features():
    canonicalizer = await build_canonicalizer(
        config={
            "enable_deduplication": True,
            "enable_structure_optimization": True,
            "enable_whitespace_compression": True,
            "use_semantic_cache_keys": True,
            "track_metrics": True,
        }
    )

    request = GenerateRequest(
        prompt="Hello   World!!!   This is a test...   Hello World!!!",
        system_prompt="You are a helpful assistant.",
        tags=["test"]
    )
    canonical = await canonicalizer.canonicalize(request)

    # Whitespace is preserved - multiple spaces remain
    assert "   " in canonical.prompt  # Multiple spaces preserved
    assert canonical.prompt.count("!") <= 2  # Reduced excessive punctuation (allow some remaining)
    assert canonical.cache_key.startswith("sem:")  # Semantic cache key
    assert canonicalizer.metrics.tokens_saved >= 0


@pytest.mark.anyio("asyncio")
async def test_whitespace_preservation():
    """Test that whitespace is preserved by default."""
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(enable_whitespace_compression=False)
    )

    request = GenerateRequest(prompt="  Multiple    spaces   and\n\n\nline breaks  ")
    canonical = await canonicalizer.canonicalize(request)

    # Whitespace is preserved - original formatting maintained
    assert "  " in canonical.prompt  # Double spaces preserved
    assert "    " in canonical.prompt  # Multiple spaces preserved
    assert "\n\n\n" in canonical.prompt  # Triple line breaks preserved


@pytest.mark.anyio("asyncio")
async def test_deduplication():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            enable_deduplication=True,
            deduplication_min_length=2,  # Use 2 words minimum
            track_metrics=True
        )
    )

    request = GenerateRequest(prompt="Hello world Hello world Hello world")
    canonical = await canonicalizer.canonicalize(request)

    # Should remove repeated phrases
    assert canonical.prompt.count("Hello world") == 1
    assert canonicalizer.metrics.deduplication_applied


@pytest.mark.anyio("asyncio")
async def test_structure_optimization():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            enable_structure_optimization=True,
            track_metrics=True
        )
    )

    request = GenerateRequest(prompt="Hello!!!   How are you???   Fine...")
    canonical = await canonicalizer.canonicalize(request)

    # Should normalize punctuation but preserve whitespace
    assert canonical.prompt.count("!") <= 1
    assert canonical.prompt.count("?") <= 1
    assert canonical.prompt.count(".") <= 3
    assert "   " in canonical.prompt  # Whitespace around punctuation preserved
    assert canonicalizer.metrics.structure_optimization_applied


@pytest.mark.anyio("asyncio")
async def test_conversation_history_optimization():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            optimize_conversation_history=True,
            max_history_entries=2,
            enable_whitespace_compression=True
        )
    )

    history = [
        {"role": "user", "content": "  Hello   there  "},
        {"role": "assistant", "content": "  Hi   back  "},
        {"role": "user", "content": "  How   are   you  "},
        {"role": "assistant", "content": "  I'm   fine  "},
    ]

    request = GenerateRequest(prompt="What's next?", history=history)
    canonical = await canonicalizer.canonicalize(request)

    # Should limit history but preserve whitespace
    assert len(canonical.history) == 2  # Limited to max_history_entries
    for entry in canonical.history:
        for value in entry.values():
            if isinstance(value, str):
                # Whitespace is preserved in history
                assert "  " in value  # Multiple spaces preserved


@pytest.mark.anyio("asyncio")
async def test_system_prompt_compression():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(compress_system_prompt=True)
    )

    request = GenerateRequest(
        prompt="Hello",
        system_prompt="  You are a helpful   assistant.   Be   nice!  "
    )
    canonical = await canonicalizer.canonicalize(request)

    # System prompt whitespace is preserved by default
    assert "  " in canonical.system_prompt  # Multiple spaces preserved
    assert canonical.system_prompt.count("!") <= 1  # Punctuation normalized


@pytest.mark.anyio("asyncio")
async def test_validation():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            min_prompt_length=5,
            max_prompt_length=100
        )
    )

    # Test too short prompt
    with pytest.raises(ValueError, match="Prompt too short"):
        await canonicalizer.canonicalize(GenerateRequest(prompt="Hi"))

    # Test too long prompt
    long_prompt = "x" * 101
    with pytest.raises(ValueError, match="Prompt too long"):
        await canonicalizer.canonicalize(GenerateRequest(prompt=long_prompt))

    # Test empty prompt with no history - this will be caught by Pydantic validation
    with pytest.raises(Exception):  # Either ValueError or ValidationError
        await canonicalizer.canonicalize(GenerateRequest(prompt=""))


@pytest.mark.anyio("asyncio")
async def test_metrics_tracking():
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(
            track_metrics=True,
            enable_deduplication=True,
            enable_structure_optimization=True,
            enable_whitespace_compression=True
        )
    )

    request = GenerateRequest(prompt="  Hello   world!!!   Hello   world!!!  ")
    canonical = await canonicalizer.canonicalize(request)

    metrics = canonicalizer.metrics
    assert metrics.original_token_count > 0
    assert metrics.optimized_token_count > 0
    assert metrics.tokens_saved >= 0
    assert 0 <= metrics.compression_ratio <= 1


def test_utility_functions():
    # Whitespace compression function exists but is no longer used by default
    # Note: _compress_whitespace still exists for backward compatibility but is disabled

    # Test deduplication
    assert _deduplicate_repeated_phrases("hello world hello world") == "hello world"
    assert _deduplicate_repeated_phrases("short") == "short"  # Too short (less than 4 words)

    # Test structure optimization (whitespace removal removed from this function)
    assert _optimize_prompt_structure("Hello!!!") == "Hello!"
    assert _optimize_prompt_structure('He said "hello"   with   spaces') == 'He said "hello"   with   spaces'  # Whitespace preserved

    # Test key phrase extraction
    phrases = _extract_key_phrases("Hello World Python Programming Language")
    # Check that we get some phrases related to the input
    assert len(phrases) > 0
    assert any("hello" in phrase for phrase in phrases)
    assert any("world" in phrase for phrase in phrases)


@pytest.mark.anyio("asyncio")
async def test_backward_compatibility():
    # Test that StandardCanonicalizer still works
    canonicalizer = StandardCanonicalizer(
        options=CanonicalizerOptions(default_tags=["legacy"])
    )

    request = GenerateRequest(prompt="test", tags=["new"])
    canonical = await canonicalizer.canonicalize(request)

    assert "legacy" in canonical.tags
    assert "new" in canonical.tags
