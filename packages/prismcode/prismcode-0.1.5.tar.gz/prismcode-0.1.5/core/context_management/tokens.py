"""
Token counting utilities for context management.

Provides pluggable tokenizer abstraction so strategies can work
with different models (30k context vs 1M context).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
import hashlib
import json

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


class LiteLLMCounter:
    """
    Accurate token counter using LiteLLM's built-in token_counter.
    This uses the actual tokenizer for each model (Claude, GPT, Gemini, etc.)
    and is the most accurate option.
    """

    def __init__(self, model: str):
        """
        Args:
            model: Full model name (e.g., 'anthropic/claude-sonnet-4', 'gpt-4')
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("litellm is required. Install with: pip install litellm")
        self.model = model

    def count(self, text: str) -> int:
        """Count tokens in a string."""
        if not text:
            return 0
        try:
            return litellm.token_counter(model=self.model, text=text)
        except Exception:
            # Fallback to char-based estimate if model not supported
            return max(1, int(len(text) / 4.0))

    def count_message(self, msg: Dict[str, Any]) -> int:
        """Count tokens in a single message."""
        try:
            return litellm.token_counter(model=self.model, messages=[msg])
        except Exception:
            # Fallback to manual counting
            total = 0
            content = msg.get("content")
            if content:
                if isinstance(content, str):
                    total += self.count(content)
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            total += self.count(part["text"])
            
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    total += self.count(tc.get("function", {}).get("name", ""))
                    total += self.count(tc.get("function", {}).get("arguments", ""))
            
            return total + 4  # Message overhead

    def count_messages(self, msgs: List[Dict[str, Any]]) -> int:
        """Count tokens in a list of messages."""
        if not msgs:
            return 0
        try:
            return litellm.token_counter(model=self.model, messages=msgs)
        except Exception:
            # Fallback to sum of individual messages
            return sum(self.count_message(m) for m in msgs)


@runtime_checkable
class TokenCounter(Protocol):
    """Protocol for token counting implementations."""

    def count(self, text: str) -> int:
        """Count tokens in a string."""
        ...

    def count_message(self, msg: Dict[str, Any]) -> int:
        """Count tokens in a single LiteLLM message."""
        ...

    def count_messages(self, msgs: List[Dict[str, Any]]) -> int:
        """Count tokens in a list of messages."""
        ...


class CharCounter:
    """
    Fast fallback counter using chars/4 heuristic.
    Good enough for rough estimates, not accurate for billing.
    """

    def __init__(self, chars_per_token: float = 4.0):
        self.chars_per_token = chars_per_token

    def count(self, text: str) -> int:
        """Count tokens in a string."""
        if not text:
            return 0
        return max(1, int(len(text) / self.chars_per_token))

    def count_message(self, msg: Dict[str, Any]) -> int:
        """Count tokens in a single message."""
        total = 0

        # Content
        content = msg.get("content")
        if content:
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                # Multi-part content (images, etc.)
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total += self.count(part["text"])

        # Tool calls
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total += self.count(tc.get("function", {}).get("name", ""))
                total += self.count(tc.get("function", {}).get("arguments", ""))

        # Role and structural overhead (~4 tokens per message)
        total += 4

        return total

    def count_messages(self, msgs: List[Dict[str, Any]]) -> int:
        """Count tokens in a list of messages."""
        return sum(self.count_message(m) for m in msgs)


class TiktokenCounter:
    """
    Accurate token counter using tiktoken.
    Works for OpenAI models and is close enough for Anthropic.

    Requires: pip install tiktoken
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        """
        Args:
            encoding_name: Tiktoken encoding. Common ones:
                - "cl100k_base": GPT-4, GPT-3.5-turbo, text-embedding-ada-002
                - "o200k_base": GPT-4o
                - "p50k_base": Codex, text-davinci-002/003
        """
        try:
            import tiktoken
            self._encoding = tiktoken.get_encoding(encoding_name)
        except ImportError:
            raise ImportError(
                "tiktoken is required for accurate token counting. "
                "Install with: pip install tiktoken"
            )
        self.encoding_name = encoding_name

    def count(self, text: str) -> int:
        """Count tokens in a string."""
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def count_message(self, msg: Dict[str, Any]) -> int:
        """
        Count tokens in a single message.
        Follows OpenAI's token counting for chat models.
        """
        total = 0

        # Every message has structural overhead
        total += 3  # <|start|>role<|end|>

        # Content
        content = msg.get("content")
        if content:
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and "text" in part:
                        total += self.count(part["text"])

        # Tool calls
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            for tc in tool_calls:
                total += self.count(tc.get("function", {}).get("name", ""))
                total += self.count(tc.get("function", {}).get("arguments", ""))
                total += 3  # function call overhead

        # Tool call ID (for tool results)
        if msg.get("tool_call_id"):
            total += self.count(msg["tool_call_id"])

        return total

    def count_messages(self, msgs: List[Dict[str, Any]]) -> int:
        """Count tokens in a list of messages."""
        total = 3  # every conversation has priming overhead
        for msg in msgs:
            total += self.count_message(msg)
        return total


class CachedCounter:
    """
    Wraps any TokenCounter with LRU caching.
    Caches based on content hash to avoid re-counting identical content.
    """

    def __init__(self, counter: TokenCounter, maxsize: int = 1024):
        self._counter = counter
        self._maxsize = maxsize
        # Create cached version of count
        self._cached_count = lru_cache(maxsize=maxsize)(self._count_impl)

    def _hash_text(self, text: str) -> str:
        """Create a hash for cache key."""
        return hashlib.md5(text.encode()).hexdigest()

    def _count_impl(self, text_hash: str, text: str) -> int:
        """Implementation that gets cached."""
        return self._counter.count(text)

    def count(self, text: str) -> int:
        """Count tokens with caching."""
        if not text:
            return 0
        return self._cached_count(self._hash_text(text), text)

    def _hash_message(self, msg: Dict[str, Any]) -> str:
        """Create a hash for a message."""
        # Stable JSON serialization for hashing
        return hashlib.md5(json.dumps(msg, sort_keys=True).encode()).hexdigest()

    def count_message(self, msg: Dict[str, Any]) -> int:
        """Count tokens in a message (not cached at message level)."""
        return self._counter.count_message(msg)

    def count_messages(self, msgs: List[Dict[str, Any]]) -> int:
        """Count tokens in messages."""
        return self._counter.count_messages(msgs)

    def cache_info(self):
        """Get cache statistics."""
        return self._cached_count.cache_info()

    def cache_clear(self):
        """Clear the cache."""
        self._cached_count.cache_clear()


@dataclass
class ModelProfile:
    """
    Model-specific configuration for context management.

    Bundles context window size with appropriate tokenizer,
    allowing strategies to be model-agnostic.
    """
    name: str
    context_window: int
    tokenizer: str = "cl100k_base"  # tiktoken encoding name

    def counter(self, use_litellm: bool = True) -> TokenCounter:
        """
        Get a token counter for this model.

        Args:
            use_litellm: If True, use accurate LiteLLM counter (recommended).
                        If False (or LiteLLM unavailable), use CharCounter.
        """
        if use_litellm and LITELLM_AVAILABLE:
            try:
                return LiteLLMCounter(self.name)
            except Exception:
                pass
        return CharCounter(chars_per_token=3.5)  # More conservative estimate

    def cached_counter(self, use_litellm: bool = True, maxsize: int = 1024) -> CachedCounter:
        """Get a cached token counter for this model."""
        return CachedCounter(self.counter(use_litellm), maxsize=maxsize)

    def budget(self, utilization: float = 0.8) -> int:
        """
        Get target token budget for this model.

        Args:
            utilization: Fraction of context window to use (0.0-1.0).
                        Default 0.8 leaves room for response.
        """
        return int(self.context_window * utilization)

    # --- Common model presets ---

    @classmethod
    def gpt4(cls) -> "ModelProfile":
        return cls("gpt-4", context_window=8_192, tokenizer="cl100k_base")

    @classmethod
    def gpt4_turbo(cls) -> "ModelProfile":
        return cls("gpt-4-turbo", context_window=128_000, tokenizer="cl100k_base")

    @classmethod
    def gpt4o(cls) -> "ModelProfile":
        return cls("gpt-4o", context_window=128_000, tokenizer="o200k_base")

    @classmethod
    def claude_sonnet(cls) -> "ModelProfile":
        return cls("claude-3-5-sonnet", context_window=200_000, tokenizer="cl100k_base")

    @classmethod
    def claude_opus(cls) -> "ModelProfile":
        return cls("claude-3-opus", context_window=200_000, tokenizer="cl100k_base")

    @classmethod
    def gemini_pro(cls) -> "ModelProfile":
        return cls("gemini-1.5-pro", context_window=1_000_000, tokenizer="cl100k_base")

    @classmethod
    def gemini_flash(cls) -> "ModelProfile":
        return cls("gemini-1.5-flash", context_window=1_000_000, tokenizer="cl100k_base")

    @classmethod
    def gemini_3_pro(cls) -> "ModelProfile":
        return cls("gemini-3-pro-preview", context_window=1_000_000, tokenizer="cl100k_base")

    @classmethod
    def mistral_small(cls) -> "ModelProfile":
        return cls("mistral-small", context_window=32_000, tokenizer="cl100k_base")

    @classmethod
    def llama3_8b(cls) -> "ModelProfile":
        return cls("llama-3-8b", context_window=8_192, tokenizer="cl100k_base")

    @classmethod
    def llama3_70b(cls) -> "ModelProfile":
        return cls("llama-3-70b", context_window=8_192, tokenizer="cl100k_base")

    @classmethod
    def from_name(cls, name: str) -> "ModelProfile":
        """
        Get a ModelProfile by model name.
        Returns a reasonable default if model is unknown.
        """
        presets = {
            "gpt-4": cls.gpt4,
            "gpt-4-turbo": cls.gpt4_turbo,
            "gpt-4o": cls.gpt4o,
            "claude-3-5-sonnet": cls.claude_sonnet,
            "claude-3-opus": cls.claude_opus,
            "gemini-1.5-pro": cls.gemini_pro,
            "gemini-1.5-flash": cls.gemini_flash,
            "gemini-3-pro-preview": cls.gemini_3_pro,
            "mistral-small": cls.mistral_small,
            "llama-3-8b": cls.llama3_8b,
            "llama-3-70b": cls.llama3_70b,
        }

        # Try exact match
        if name in presets:
            return presets[name]()

        # Try partial match (handles provider prefixes like "anthropic/claude-opus-4-5")
        name_lower = name.lower()
        
        # Check for Claude models (various naming conventions)
        if "opus" in name_lower:
            return cls.claude_opus()
        if "sonnet" in name_lower:
            return cls.claude_sonnet()
        if "claude" in name_lower:
            # Default Claude to 200k
            return cls(name, context_window=200_000, tokenizer="cl100k_base")

        # Check for Gemini models
        if "gemini" in name_lower:
            if "flash" in name_lower:
                return cls.gemini_flash()
            if "3-pro" in name_lower or "3.0-pro" in name_lower:
                return cls.gemini_3_pro()
            return cls.gemini_pro()
        
        # Check for other models
        for key, factory in presets.items():
            if key in name_lower or name_lower in key:
                return factory()

        # Default: assume 128k context
        return cls(name, context_window=128_000, tokenizer="cl100k_base")
