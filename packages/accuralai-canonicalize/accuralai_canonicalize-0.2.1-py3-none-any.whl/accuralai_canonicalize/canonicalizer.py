"""Canonicalizer plugin for accuralai-core with token optimization."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from string import Template
from typing import Any, Iterable, Mapping, Optional, Sequence

from pydantic import BaseModel, Field, ValidationError

from accuralai_core.contracts.models import GenerateRequest
from accuralai_core.contracts.protocols import Canonicalizer
from accuralai_core.config.schema import PluginSettings


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    """Lowercase and deduplicate tags preserving sorted order."""
    normalized = sorted({tag.strip().lower() for tag in tags if tag.strip()})
    return normalized


def _compress_whitespace(text: str) -> str:
    """Intelligently compress whitespace while preserving structure."""
    if not text:
        return text
    
    # Preserve intentional line breaks and structure
    lines = text.split('\n')
    compressed_lines = []
    
    for line in lines:
        # Compress internal whitespace but preserve empty lines
        if line.strip():
            compressed_line = re.sub(r'\s+', ' ', line.strip())
            compressed_lines.append(compressed_line)
        else:
            compressed_lines.append('')
    
    # Join lines and compress multiple consecutive line breaks to maximum of 2
    result = '\n'.join(compressed_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result


def _deduplicate_repeated_phrases(text: str, min_length: int = 10) -> str:
    """Remove repeated phrases to reduce token count."""
    words = text.split()
    if len(words) < 4:  # Need at least 4 words to have a meaningful repetition
        return text
    
    # Find repeated sequences starting from 2 words up to half the text
    for length in range(2, len(words) // 2 + 1):
        for i in range(len(words) - length * 2 + 1):
            sequence = words[i:i + length]
            # Check if this sequence repeats immediately after
            if i + length < len(words) and words[i + length:i + length * 2] == sequence:
                # Remove all repetitions, keeping only the first occurrence
                remaining_words = words[:i + length]
                # Skip all subsequent repetitions
                j = i + length * 2
                while j + length <= len(words) and words[j:j + length] == sequence:
                    j += length
                remaining_words.extend(words[j:])
                return ' '.join(remaining_words)
    
    return text


def _optimize_prompt_structure(text: str) -> str:
    """Optimize prompt structure for better token efficiency."""
    if not text:
        return text
    
    # Remove excessive punctuation
    text = re.sub(r'[.]{3,}', '...', text)
    text = re.sub(r'[!]{2,}', '!', text)
    text = re.sub(r'[?]{2,}', '?', text)
    
    # Normalize quotes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r"[''']", "'", text)
    
    # Whitespace removal removed - preserving original whitespace for better response quality
    
    return text


def _extract_key_phrases(text: str, max_phrases: int = 5) -> list[str]:
    """Extract key phrases for semantic cache key generation."""
    if not text:
        return []
    
    # Simple key phrase extraction based on capitalization and length
    words = text.split()
    phrases = []
    
    # Find capitalized sequences (potential proper nouns/phrases)
    current_phrase = []
    for word in words:
        if word[0].isupper() and len(word) > 2:
            current_phrase.append(word.lower())
        else:
            if len(current_phrase) >= 2:
                phrases.append(' '.join(current_phrase))
            current_phrase = []
    
    if len(current_phrase) >= 2:
        phrases.append(' '.join(current_phrase))
    
    # Also extract longer words (potential technical terms)
    long_words = [word.lower() for word in words if len(word) > 6 and word.isalpha()]
    
    # For short texts, include all words to ensure uniqueness
    if len(words) <= 3:
        phrases.extend([word.lower() for word in words if word.isalpha()])
    
    # Combine and limit
    all_phrases = phrases + long_words
    return all_phrases[:max_phrases]


def _generate_semantic_cache_key(request: GenerateRequest, *, extra_fields: Sequence[str]) -> str:
    """Generate a semantic cache key that groups similar requests."""
    # Extract semantic content
    semantic_parts = []
    
    # Include the full prompt for uniqueness (but normalized)
    normalized_prompt = request.prompt.lower().strip()
    semantic_parts.append(f"prompt:{normalized_prompt}")
    
    # Extract key phrases from prompt for additional semantic grouping
    prompt_phrases = _extract_key_phrases(request.prompt)
    semantic_parts.extend(prompt_phrases)
    
    # Extract key phrases from system prompt
    if request.system_prompt:
        system_phrases = _extract_key_phrases(request.system_prompt)
        semantic_parts.extend(system_phrases)
        # Also include normalized system prompt
        normalized_system = request.system_prompt.lower().strip()
        semantic_parts.append(f"system:{normalized_system}")
    
    # Include metadata fields that affect semantics
    for field in extra_fields:
        if field in request.metadata:
            value = request.metadata[field]
            if isinstance(value, str):
                semantic_parts.append(f"{field}:{value}")
    
    # Include tools in semantic key (important for tool availability)
    if request.tools:
        tool_names = sorted([t.get("function", {}).get("name") or str(t) for t in request.tools])
        semantic_parts.append(f"tools:{'|'.join(tool_names)}")
    
    # Create semantic hash
    semantic_content = '|'.join(sorted(semantic_parts))
    semantic_hash = hashlib.sha256(semantic_content.encode("utf-8")).hexdigest()[:16]
    
    return f"sem:{semantic_hash}"


def _stable_json(obj: Any) -> str:
    """Serialize to canonical JSON (sorted keys)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _generate_cache_key(request: GenerateRequest, *, extra_fields: Sequence[str]) -> str:
    """Generate a deterministic cache key for the request."""
    payload: dict[str, Any] = {
        "prompt": request.prompt,
        "system_prompt": request.system_prompt,
        "history": request.history,
        "parameters": request.parameters,
        "metadata": {field: request.metadata.get(field) for field in extra_fields},
        "tags": request.tags,
        "tools": request.tools,  # Include tools in cache key
    }
    digest = hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()
    return f"req:{digest}"


@dataclass(slots=True)
class CanonicalizationMetrics:
    """Metrics tracking canonicalization effectiveness."""
    
    original_token_count: int = 0
    optimized_token_count: int = 0
    tokens_saved: int = 0
    compression_ratio: float = 0.0
    deduplication_applied: bool = False
    whitespace_compression_applied: bool = False
    structure_optimization_applied: bool = False
    
    def __post_init__(self) -> None:
        """Calculate derived metrics."""
        if self.original_token_count > 0:
            self.tokens_saved = self.original_token_count - self.optimized_token_count
            self.compression_ratio = self.tokens_saved / self.original_token_count


class CanonicalizerOptions(BaseModel):
    """Configuration options for the canonicalizer."""

    # Basic options
    prompt_template: Optional[str] = None
    normalize_tags: bool = True
    default_tags: list[str] = Field(default_factory=list)
    metadata_defaults: dict[str, Any] = Field(default_factory=dict)
    auto_cache_key: bool = True
    cache_key_metadata_fields: list[str] = Field(default_factory=list)
    
    # Token optimization options
    enable_deduplication: bool = True
    deduplication_min_length: int = Field(default=10, ge=2, le=50)
    enable_structure_optimization: bool = True
    enable_whitespace_compression: bool = False  # Disabled by default - preserving whitespace improves response quality
    
    # Cache key generation options
    use_semantic_cache_keys: bool = False
    semantic_key_max_phrases: int = Field(default=5, ge=1, le=20)
    
    # Context-aware processing
    optimize_conversation_history: bool = True
    max_history_entries: Optional[int] = Field(default=None, ge=1)
    compress_system_prompt: bool = True
    
    # Metrics and telemetry
    track_metrics: bool = True
    log_optimization_stats: bool = False
    
    # Validation options
    max_prompt_length: Optional[int] = Field(default=None, ge=1)
    min_prompt_length: int = Field(default=1, ge=1)
    
    @property
    def effective_max_history_entries(self) -> int:
        """Get the effective maximum history entries."""
        return self.max_history_entries or 50


@dataclass(slots=True)
class StandardCanonicalizer(Canonicalizer):
    """Canonicalizer with token optimization and semantic caching."""

    options: CanonicalizerOptions = field(default_factory=CanonicalizerOptions)
    _metrics: CanonicalizationMetrics = field(default_factory=CanonicalizationMetrics, init=False)

    async def canonicalize(self, request: GenerateRequest) -> GenerateRequest:
        """Normalize request data with token optimization."""
        # Initialize metrics
        if self.options.track_metrics:
            self._metrics = CanonicalizationMetrics()
            self._metrics.original_token_count = self._estimate_token_count(request)

        # Validate input
        self._validate_request(request)

        updated: dict[str, Any] = {}

        # Process prompt with token optimization
        prompt = await self._optimize_prompt(request.prompt)
        updated["prompt"] = prompt

        # Process system prompt
        system_prompt = request.system_prompt
        if system_prompt and self.options.compress_system_prompt:
            system_prompt = await self._optimize_prompt(system_prompt)
        updated["system_prompt"] = system_prompt

        # Process conversation history
        history = request.history
        if self.options.optimize_conversation_history and history:
            history = await self._optimize_history(history)
        updated["history"] = history

        # Process tags
        tags = list(request.tags)
        tags.extend(self.options.default_tags)
        if self.options.normalize_tags:
            tags = _normalize_tags(tags)
        updated["tags"] = tags

        # Process metadata
        metadata = dict(request.metadata)
        for key, value in self.options.metadata_defaults.items():
            metadata.setdefault(key, value)
        updated["metadata"] = metadata

        # Generate cache key
        cache_key = request.cache_key
        if self.options.auto_cache_key and not cache_key:
            if self.options.use_semantic_cache_keys:
                cache_key = _generate_semantic_cache_key(
                    request.model_copy(update=updated),
                    extra_fields=self.options.cache_key_metadata_fields,
                )
            else:
                cache_key = _generate_cache_key(
                    request.model_copy(update=updated),
                    extra_fields=self.options.cache_key_metadata_fields,
                )
        updated["cache_key"] = cache_key

        # Update metrics
        if self.options.track_metrics:
            self._metrics.optimized_token_count = self._estimate_token_count(
                request.model_copy(update=updated)
            )
            self._metrics.__post_init__()

        # Log optimization stats if enabled
        if self.options.log_optimization_stats and self.options.track_metrics:
            self._log_optimization_stats()

        return request.model_copy(update=updated)

    async def _optimize_prompt(self, prompt: str) -> str:
        """Apply comprehensive prompt optimization."""
        if not prompt:
            return prompt

        original_prompt = prompt

        # Whitespace compression removed - preserving original whitespace for better response quality

        # Apply structure optimization
        if self.options.enable_structure_optimization:
            prompt = _optimize_prompt_structure(prompt)
            if prompt != original_prompt:
                self._metrics.structure_optimization_applied = True

        # Apply deduplication
        if self.options.enable_deduplication:
            deduplicated = _deduplicate_repeated_phrases(
                prompt, self.options.deduplication_min_length
            )
            if deduplicated != prompt:
                prompt = deduplicated
                self._metrics.deduplication_applied = True

        # Apply template if configured
        if self.options.prompt_template:
            prompt = Template(self.options.prompt_template).safe_substitute(
                prompt=prompt,
                system_prompt="",  # Will be handled separately
                tags=",".join([]),  # Will be handled separately
            )

        return prompt

    async def _optimize_history(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Optimize conversation history for token efficiency."""
        if not history:
            return history

        # Limit history entries if configured
        max_entries = self.options.effective_max_history_entries
        if len(history) > max_entries:
            history = history[-max_entries:]

        # Optimize each history entry
        optimized_history = []
        for entry in history:
            optimized_entry = {}
            for key, value in entry.items():
                # Whitespace compression removed - preserving original whitespace for better response quality
                    optimized_entry[key] = value
            optimized_history.append(optimized_entry)

        return optimized_history

    def _validate_request(self, request: GenerateRequest) -> None:
        """Validate the request meets canonicalization requirements."""
        if not request.prompt or not request.prompt.strip():
            if not request.history:
                raise ValueError("Request must have a non-empty prompt or conversation history")

        # Only validate prompt length if there's actually a prompt
        if request.prompt and request.prompt.strip():
            prompt_length = len(request.prompt)
            if self.options.min_prompt_length and prompt_length < self.options.min_prompt_length:
                raise ValueError(f"Prompt too short: {prompt_length} < {self.options.min_prompt_length}")

            if self.options.max_prompt_length and prompt_length > self.options.max_prompt_length:
                raise ValueError(f"Prompt too long: {prompt_length} > {self.options.max_prompt_length}")

    def _estimate_token_count(self, request: GenerateRequest) -> int:
        """Estimate token count using simple word-based approximation."""
        text_parts = []
        
        if request.system_prompt:
            text_parts.append(request.system_prompt)
        if request.prompt:
            text_parts.append(request.prompt)
        
        for entry in request.history:
            for value in entry.values():
                if isinstance(value, str):
                    text_parts.append(value)
        
        total_text = " ".join(text_parts)
        # Simple approximation: ~4 characters per token
        return len(total_text) // 4

    def _log_optimization_stats(self) -> None:
        """Log optimization statistics."""
        print("Canonicalization Stats:")
        print(f"  Original tokens: {self._metrics.original_token_count}")
        print(f"  Optimized tokens: {self._metrics.optimized_token_count}")
        print(f"  Tokens saved: {self._metrics.tokens_saved}")
        print(f"  Compression ratio: {self._metrics.compression_ratio:.2%}")
        print(f"  Deduplication applied: {self._metrics.deduplication_applied}")
        print(f"  Whitespace compression applied: {self._metrics.whitespace_compression_applied}")
        print(f"  Structure optimization applied: {self._metrics.structure_optimization_applied}")

    @property
    def metrics(self) -> CanonicalizationMetrics:
        """Get the latest canonicalization metrics."""
        return self._metrics


async def build_canonicalizer(
    *,
    config: PluginSettings | Mapping[str, Any] | None = None,
    **_: Any,
) -> Canonicalizer:
    """Factory entry point for creating a canonicalizer."""
    options_data: Mapping[str, Any] | None = None
    if isinstance(config, PluginSettings):
        options_data = config.options
    elif isinstance(config, Mapping):
        options_data = dict(config)

    try:
        options = CanonicalizerOptions.model_validate(options_data or {})
    except ValidationError as error:
        message = f"Invalid canonicalizer options: {error}"
        raise ValueError(message) from error
    return StandardCanonicalizer(options=options)
