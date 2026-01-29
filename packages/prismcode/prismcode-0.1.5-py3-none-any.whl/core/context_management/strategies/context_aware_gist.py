"""
ContextAwareGist Strategy

Like RollingGist, but the consolidation LLM receives context about
what the agent is currently working on. This allows it to make
smarter decisions about what to preserve vs compress.

The key insight: the consolidator shares the agent's working memory,
so it can see the current task, recent conversation, and judge
relevance when compressing old memories.
"""
from dataclasses import dataclass
from typing import Callable, List, Optional, Union, TYPE_CHECKING

from .base import ConsolidationStrategy, ConsolidationResult

if TYPE_CHECKING:
    from ..ground_truth import HistoryManager
    from ..tokens import TokenCounter


@dataclass
class ConsolidatorContext:
    """Context provided to the consolidation LLM."""

    # The full or partial working memory (as formatted text)
    working_memory: str
    working_memory_tokens: int

    # The specific slice being compressed
    slice_to_compress: str
    slice_tokens: int
    slice_start_idx: int
    slice_end_idx: int

    # Stats
    total_entries: int
    entries_to_compress: int


# Default prompt template - COMPREHENSIVE version
# This prompt produces detailed gists since we're compressing significant history
DEFAULT_CONTEXT_AWARE_PROMPT = '''You are the memory consolidation system for an AI coding assistant. Your job is to compress conversation history while preserving ALL information needed to continue work effectively.

## IMPORTANT: This is NOT a summary - it's a DETAILED MEMORY ARCHIVE

We are about to lose access to the raw conversation below. Your output will be the ONLY record of what happened. Be thorough - treat this like writing detailed notes that your future self needs to pick up exactly where you left off.

---

## CURRENT WORKING MEMORY (What we're keeping - for context)
{working_memory}

---

## ENTRIES TO ARCHIVE (indices {start_idx} to {end_idx})
These entries will be REPLACED by your archive. Capture everything important:

{slice_to_compress}

---

## YOUR TASK: Create a Comprehensive Memory Archive

Write a detailed archive that captures:

### 1. TASK CONTEXT
- What was the user trying to accomplish?
- What was the assistant working on?
- Any stated goals, requirements, or constraints?

### 2. KEY INFORMATION LEARNED
- Files read and their key contents (structure, important functions, patterns)
- Code patterns discovered
- System/architecture understanding gained
- Configuration or setup details

### 3. ACTIONS TAKEN
- Files created, modified, or deleted (include paths)
- Commands run and their outcomes
- Tool calls and results (especially errors or unexpected results)

### 4. DECISIONS & REASONING
- Why certain approaches were chosen
- Trade-offs considered
- User preferences expressed

### 5. PROBLEMS & SOLUTIONS
- Errors encountered and how they were resolved
- Blockers hit and workarounds found
- Failed attempts (so we don't repeat them)

### 6. CURRENT STATE
- What was accomplished?
- What's still pending or incomplete?
- Any open questions or uncertainties?

### 7. CRITICAL DETAILS TO PRESERVE
- Exact file paths, function names, class names
- Specific error messages or codes
- Configuration values, environment details
- Any information that would be hard to rediscover

---

## FORMAT GUIDELINES

- Use markdown for structure (headers, bullets, code blocks)
- Include exact file paths: `/path/to/file.py:123`
- Quote important code snippets in fenced blocks
- Preserve technical accuracy over brevity
- If unsure whether to include something, INCLUDE IT

## OUTPUT

Write your comprehensive memory archive below. This is your one chance to preserve this information:'''


class ContextAwareGist(ConsolidationStrategy):
    """
    Context-aware consolidation strategy.

    The consolidation LLM receives the agent's working memory (full or partial)
    so it can make informed decisions about what to preserve based on
    current task relevance.
    """

    def __init__(
        self,
        budget: int,
        threshold: float = 0.7,
        compress_ratio: float = 0.2,
        min_entries_to_keep: int = 4,
        # Context for consolidator
        consolidator_context: float = 1.0,  # 0.0-1.0, how much of working memory to include
        consolidator_context_tokens: Optional[int] = None,  # Alternative: fixed token budget
        # LLM settings
        gist_fn: Optional[Callable[[str], str]] = None,
        gist_prompt: str = DEFAULT_CONTEXT_AWARE_PROMPT,
        # Model for consolidation (if using built-in LLM call)
        consolidator_model: str = "gpt-4o-mini",
    ):
        """
        Args:
            budget: Maximum token budget for working history
            threshold: Trigger consolidation when usage exceeds this (0.0-1.0)
            compress_ratio: What fraction of history to compress each time
            min_entries_to_keep: Never compress if fewer than this many entries remain
            consolidator_context: Fraction of working memory to show consolidator (0.0-1.0)
                                 1.0 = full context, 0.5 = recent half
            consolidator_context_tokens: Alternative to consolidator_context -
                                         fixed token budget for context
            gist_fn: Function that takes prompt and returns gist. If None, uses litellm.
            gist_prompt: Prompt template with {working_memory}, {slice_to_compress},
                        {start_idx}, {end_idx} placeholders
            consolidator_model: Model to use if gist_fn is None
        """
        super().__init__(budget, threshold, gist_fn)
        self.compress_ratio = compress_ratio
        self.min_entries_to_keep = min_entries_to_keep
        self.consolidator_context = consolidator_context
        self.consolidator_context_tokens = consolidator_context_tokens
        self.gist_prompt = gist_prompt
        self.consolidator_model = consolidator_model

    def should_consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
    ) -> bool:
        """Check if we've exceeded the threshold."""
        tokens, ratio = self.get_usage(history, counter)

        if len(history.working.entries) < self.min_entries_to_keep:
            return False

        return ratio > self.threshold

    def _get_context_for_consolidator(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        exclude_slice_end: int,
    ) -> tuple[str, int]:
        """
        Get the working memory context to show the consolidator.

        Returns (formatted_context, token_count)
        """
        from ..query import HistoryQuery

        # Get entries AFTER the slice we're compressing
        # (the consolidator needs to see what's "current")
        remaining_entries = history.working.entries[exclude_slice_end:]

        if not remaining_entries:
            return "", 0

        query = HistoryQuery(remaining_entries, counter)

        # Determine how much context to include
        if self.consolidator_context_tokens is not None:
            # Fixed token budget
            slice = query.last_n_tokens(self.consolidator_context_tokens)
        else:
            # Percentage of remaining
            slice = query.last_percent(self.consolidator_context)

        # Format as readable text
        context_text = slice.to_gist_input()

        return context_text, slice.token_count

    def _build_consolidator_context(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        slice_start: int,
        slice_end: int,
    ) -> ConsolidatorContext:
        """Build the full context object for the consolidator."""
        from ..query import HistoryQuery

        # Get the slice to compress
        query = HistoryQuery(history.working.entries, counter)
        slice_to_compress = query.range(slice_start, slice_end)

        # Get context (everything after the slice)
        context_text, context_tokens = self._get_context_for_consolidator(
            history, counter, slice_end
        )

        return ConsolidatorContext(
            working_memory=context_text,
            working_memory_tokens=context_tokens,
            slice_to_compress=slice_to_compress.to_gist_input(),
            slice_tokens=slice_to_compress.token_count,
            slice_start_idx=slice_start,
            slice_end_idx=slice_end,
            total_entries=len(history.working.entries),
            entries_to_compress=slice_to_compress.entry_count(),
        )

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM to generate gist. Override or provide gist_fn."""
        import litellm

        response = await litellm.acompletion(
            model=self.consolidator_model,
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    async def consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        gist_fn: Optional[Callable[[str], str]] = None,
    ) -> ConsolidationResult:
        """
        Run context-aware consolidation.

        The consolidation LLM receives:
        1. Working memory context (full or partial based on settings)
        2. The specific entries to compress
        3. Instructions to preserve relevant details
        """
        from ..query import HistoryQuery
        import inspect

        # Check if we should consolidate
        if not self.should_consolidate(history, counter):
            return ConsolidationResult(consolidated=False)

        # Build query for working history
        query = HistoryQuery(history.working.entries, counter)
        tokens_before = query.total_tokens()

        # Select oldest X% to compress
        slice_to_compress = query.first_percent(self.compress_ratio)

        # Don't compress if it would leave too few entries
        remaining = len(history.working.entries) - slice_to_compress.entry_count()
        if remaining < self.min_entries_to_keep:
            return ConsolidationResult(consolidated=False)

        if slice_to_compress.is_empty():
            return ConsolidationResult(consolidated=False)

        # Find safe boundary
        safe_end = query.safe_boundary_near(slice_to_compress.end_idx)
        slice_start = 0
        slice_end = safe_end

        # Build context for consolidator
        ctx = self._build_consolidator_context(history, counter, slice_start, slice_end)

        # Format the prompt
        prompt = self.gist_prompt.format(
            working_memory=ctx.working_memory if ctx.working_memory else "[No additional context - this is the beginning of the conversation]",
            slice_to_compress=ctx.slice_to_compress,
            start_idx=ctx.slice_start_idx,
            end_idx=ctx.slice_end_idx,
        )

        # Call the gist function
        fn = gist_fn or self.gist_fn

        if fn is not None:
            if inspect.iscoroutinefunction(fn):
                gist_text = await fn(prompt)
            else:
                gist_text = fn(prompt)
        else:
            # Use built-in LLM call
            gist_text = await self._call_llm(prompt)

        # Get entry IDs before replacing
        consolidated_ids = query.range(slice_start, slice_end).ids()

        # Replace the range with the gist
        history.working.replace_range_with_gist(slice_start, slice_end, gist_text)

        # Measure tokens after
        query_after = HistoryQuery(history.working.entries, counter)
        tokens_after = query_after.total_tokens()

        return ConsolidationResult(
            consolidated=True,
            entries_replaced=ctx.entries_to_compress,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            gist_text=gist_text,
            consolidated_ids=consolidated_ids,
        )

    async def consolidate_until_under_budget(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        gist_fn: Optional[Callable[[str], str]] = None,
        max_iterations: int = 10,
    ) -> List[ConsolidationResult]:
        """Keep consolidating until under threshold."""
        results = []

        for _ in range(max_iterations):
            result = await self.consolidate(history, counter, gist_fn)
            results.append(result)

            if not result.consolidated:
                break

        return results

    def __repr__(self) -> str:
        ctx = f"context={self.consolidator_context}"
        if self.consolidator_context_tokens:
            ctx = f"context_tokens={self.consolidator_context_tokens}"

        return (
            f"ContextAwareGist(budget={self.budget}, "
            f"threshold={self.threshold}, "
            f"compress_ratio={self.compress_ratio}, "
            f"{ctx})"
        )
