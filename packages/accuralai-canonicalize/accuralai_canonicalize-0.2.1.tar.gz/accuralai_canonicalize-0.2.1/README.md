# accuralai-canonicalize

`accuralai-canonicalize` provides advanced canonicalization utilities and plugins for the AccuralAI pipeline. The library includes sophisticated token optimization, semantic caching, and comprehensive metrics tracking to maximize LLM efficiency and reduce costs.

## Features

### 🚀 Advanced Token Optimization
- **Whitespace Preservation**: Original whitespace is preserved for better response quality (compression disabled by default)
- **Phrase Deduplication**: Removes repeated phrases to reduce token count
- **Structure Optimization**: Normalizes punctuation and formatting for efficiency
- **Context-Aware Processing**: Optimizes conversation history and system prompts

### 🧠 Semantic Caching
- **Semantic Cache Keys**: Groups similar requests for better cache hit rates
- **Key Phrase Extraction**: Identifies important concepts for intelligent grouping
- **Hierarchical Caching**: Multiple cache key strategies for different use cases

### 📊 Comprehensive Metrics
- **Token Savings Tracking**: Monitor compression ratios and optimization effectiveness
- **Performance Analytics**: Track which optimizations provide the most benefit
- **Real-time Statistics**: Live metrics during canonicalization

### 🔧 Flexible Configuration
- **Granular Controls**: Enable/disable specific optimization features
- **Validation Options**: Configurable length limits and quality checks
- **Backward Compatibility**: Drop-in replacement for existing implementations

## Installation

Install alongside `accuralai-core` to enable the canonicalizer:

```bash
pip install accuralai-core accuralai-canonicalize
```

## Usage

### Basic Usage

The canonicalizer automatically integrates with the AccuralAI pipeline:

```bash
accuralai-core generate --prompt "Hello there!"
```

### Advanced Configuration

Configure the canonicalizer in your `config.toml`:

```toml
[canonicalizer]
plugin = "advanced"  # Use the advanced canonicalizer
[canonicalizer.options]
# Basic options
normalize_tags = true
auto_cache_key = true
cache_key_metadata_fields = ["topic", "domain"]

# Advanced token optimization
enable_deduplication = true
deduplication_min_length = 10
enable_structure_optimization = true
enable_whitespace_compression = false  # Disabled by default - preserving whitespace improves response quality

# Semantic caching
use_semantic_cache_keys = true
semantic_key_max_phrases = 5

# Context-aware processing
optimize_conversation_history = true
max_history_entries = 50
compress_system_prompt = true

# Metrics and telemetry
track_metrics = true
log_optimization_stats = false

# Validation
max_prompt_length = 10000
min_prompt_length = 1
```

### Programmatic Usage

```python
from accuralai_canonicalize.canonicalizer import AdvancedCanonicalizer, CanonicalizerOptions
from accuralai_core.contracts.models import GenerateRequest

# Create canonicalizer with custom options
options = CanonicalizerOptions(
    enable_deduplication=True,
    enable_structure_optimization=True,
    use_semantic_cache_keys=True,
    track_metrics=True
)
canonicalizer = AdvancedCanonicalizer(options=options)

# Process a request
request = GenerateRequest(
    prompt="  Hello   world!!!   Hello   world!!!  ",
    system_prompt="You are a helpful assistant.",
    tags=["test"]
)

canonical = await canonicalizer.canonicalize(request)

# Access optimization metrics
metrics = canonicalizer.metrics
print(f"Tokens saved: {metrics.tokens_saved}")
print(f"Compression ratio: {metrics.compression_ratio:.2%}")
```

## Configuration Options

### Basic Options
- `prompt_template`: Template string for prompt formatting
- `normalize_tags`: Normalize and deduplicate tags
- `default_tags`: Default tags to add to all requests
- `metadata_defaults`: Default metadata values
- `auto_cache_key`: Automatically generate cache keys
- `cache_key_metadata_fields`: Metadata fields to include in cache keys

### Advanced Token Optimization
- `enable_deduplication`: Remove repeated phrases (default: true)
- `deduplication_min_length`: Minimum phrase length for deduplication (default: 10)
- `enable_structure_optimization`: Optimize punctuation and formatting (default: true)
- `enable_whitespace_compression`: Whitespace compression (default: false - preserving whitespace improves response quality)

### Semantic Caching
- `use_semantic_cache_keys`: Use semantic similarity for cache keys (default: false)
- `semantic_key_max_phrases`: Maximum phrases to extract for semantic keys (default: 5)

### Context-Aware Processing
- `optimize_conversation_history`: Optimize conversation history (default: true)
- `max_history_entries`: Maximum history entries to keep (default: 50)
- `compress_system_prompt`: Apply optimizations to system prompt (default: true, but whitespace is preserved)

### Metrics and Telemetry
- `track_metrics`: Track optimization metrics (default: true)
- `log_optimization_stats`: Log optimization statistics (default: false)

### Validation
- `max_prompt_length`: Maximum prompt length (default: none)
- `min_prompt_length`: Minimum prompt length (default: 1)

## Optimization Examples

### Whitespace Preservation
```
Input:  "  Hello   world    with    multiple    spaces  "
Output: "  Hello   world    with    multiple    spaces  "  # Whitespace preserved by default
```

### Deduplication
```
Input:  "Hello world Hello world Hello world"
Output: "Hello world"
```

### Structure Optimization
```
Input:  "Hello!!!   How are you???   Fine..."
Output: "Hello! How are you? Fine..."
```

### Semantic Cache Keys
```
Input:  "Explain Python programming concepts"
Output: Cache key: "sem:a1b2c3d4e5f6g7h8" (groups with similar Python questions)
```

## Metrics and Monitoring

The canonicalizer provides detailed metrics about optimization effectiveness:

```python
metrics = canonicalizer.metrics
print(f"Original tokens: {metrics.original_token_count}")
print(f"Optimized tokens: {metrics.optimized_token_count}")
print(f"Tokens saved: {metrics.tokens_saved}")
print(f"Compression ratio: {metrics.compression_ratio:.2%}")
print(f"Deduplication applied: {metrics.deduplication_applied}")
print(f"Whitespace compression applied: {metrics.whitespace_compression_applied}")
print(f"Structure optimization applied: {metrics.structure_optimization_applied}")
```

## Performance Benefits

Typical token savings with the advanced canonicalizer:

- **Whitespace Preservation**: Enabled by default for better response quality
- **Deduplication**: 10-30% reduction (when applicable)
- **Structure Optimization**: 3-8% reduction
- **Combined Optimization**: 10-35% total reduction (with whitespace preservation)

## Migration from Standard Canonicalizer

The advanced canonicalizer is backward compatible. To migrate:

1. Update your configuration to use `plugin = "advanced"`
2. Optionally enable additional features:
   ```toml
   [canonicalizer.options]
   enable_deduplication = true
   use_semantic_cache_keys = true
   track_metrics = true
   ```
3. Monitor metrics to measure optimization effectiveness

## Contributing

Contributions are welcome! Please see the main AccuralAI repository for contribution guidelines.

## License

Apache-2.0
