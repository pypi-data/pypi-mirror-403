"""
RollingGist Strategy

The simplest consolidation strategy:
- When working history exceeds threshold (default 70% of budget)
- Compress the oldest X% (default 20%) into a gist
- Repeat as needed

Like a rolling wave that continuously compresses old memories
while keeping recent ones intact.
"""
from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING

from .base import ConsolidationStrategy, ConsolidationResult

if TYPE_CHECKING:
    from ..ground_truth import HistoryManager
    from ..tokens import TokenCounter


# Default prompt for generating gists - COMPREHENSIVE version
DEFAULT_GIST_PROMPT = """You are the memory consolidation system for an AI coding assistant. Your job is to compress conversation history while preserving ALL information needed to continue work effectively.

## IMPORTANT: This is NOT a brief summary - it's a DETAILED MEMORY ARCHIVE

We are about to lose access to the raw conversation below. Your output will be the ONLY record of what happened. Be thorough.

---

## CONVERSATION TO ARCHIVE:
{content}

---

## YOUR TASK: Create a Comprehensive Memory Archive

Write a detailed archive covering:

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
- Files created, modified, or deleted (include full paths)
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

### 7. CRITICAL DETAILS
- Exact file paths, function names, class names
- Specific error messages or codes
- Configuration values, environment details

---

## FORMAT
- Use markdown (headers, bullets, code blocks)
- Include exact paths: `/path/to/file.py:123`
- Quote code snippets in fenced blocks
- Preserve technical accuracy over brevity
- If unsure whether to include something, INCLUDE IT

## MEMORY ARCHIVE:"""


class RollingGist(ConsolidationStrategy):
    """
    Simple rolling consolidation strategy.

    When context usage exceeds threshold:
    1. Take the oldest X% of working history
    2. Compress it into a gist
    3. Replace those entries with the gist

    This creates a "rolling window" effect where recent history
    stays detailed and older history progressively compresses.
    """

    def __init__(
        self,
        budget: int,
        threshold: float = 0.7,
        compress_ratio: float = 0.2,
        min_entries_to_keep: int = 4,
        gist_fn: Optional[Callable[[str], str]] = None,
        gist_prompt: str = DEFAULT_GIST_PROMPT,
    ):
        """
        Args:
            budget: Maximum token budget for working history
            threshold: Trigger consolidation when usage exceeds this (0.0-1.0)
            compress_ratio: What fraction of history to compress each time (0.0-1.0)
            min_entries_to_keep: Never compress if fewer than this many entries remain
            gist_fn: Async function that takes text and returns a gist.
            gist_prompt: Prompt template for gist generation. Use {content} placeholder.
        """
        super().__init__(budget, threshold, gist_fn)
        self.compress_ratio = compress_ratio
        self.min_entries_to_keep = min_entries_to_keep
        self.gist_prompt = gist_prompt

    def should_consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
    ) -> bool:
        """Check if we've exceeded the threshold."""
        tokens, ratio = self.get_usage(history, counter)

        # Don't consolidate if too few entries
        if len(history.working.entries) < self.min_entries_to_keep:
            return False

        return ratio > self.threshold

    async def consolidate(
        self,
        history: "HistoryManager",
        counter: "TokenCounter",
        gist_fn: Optional[Callable[[str], str]] = None,
    ) -> ConsolidationResult:
        """
        Compress the oldest portion of history.

        Args:
            history: The history manager (modified in place)
            counter: Token counter
            gist_fn: Async function to generate gist. Overrides self.gist_fn.

        Returns:
            ConsolidationResult with details
        """
        from ..query import HistoryQuery

        # Use provided gist_fn or fall back to self.gist_fn
        fn = gist_fn or self.gist_fn
        if fn is None:
            raise ValueError("No gist_fn provided. Pass one to consolidate() or __init__().")

        # Check if we should consolidate
        if not self.should_consolidate(history, counter):
            return ConsolidationResult(consolidated=False)

        # Build query for current working history
        query = HistoryQuery(history.working.entries, counter)
        tokens_before = query.total_tokens()

        # Select oldest X% to compress
        slice_to_compress = query.first_percent(self.compress_ratio)

        # Don't compress if it would leave too few entries
        remaining = len(history.working.entries) - slice_to_compress.entry_count()
        if remaining < self.min_entries_to_keep:
            return ConsolidationResult(consolidated=False)

        # Don't compress empty slices
        if slice_to_compress.is_empty():
            return ConsolidationResult(consolidated=False)

        # Find safe boundary (don't split tool call from result)
        safe_end = query.safe_boundary_near(slice_to_compress.end_idx)

        # Re-slice with safe boundary
        if safe_end != slice_to_compress.end_idx:
            slice_to_compress = query.range(0, safe_end)

        # Generate gist input
        gist_input = slice_to_compress.to_gist_input()

        # Format the prompt
        prompt = self.gist_prompt.format(content=gist_input)

        # Call the gist function (might be sync or async)
        import asyncio
        import inspect

        if inspect.iscoroutinefunction(fn):
            gist_text = await fn(prompt)
        else:
            gist_text = fn(prompt)

        # Get entry IDs before replacing
        consolidated_ids = slice_to_compress.ids()

        # Replace the range with the gist
        history.working.replace_range_with_gist(
            slice_to_compress.start_idx,
            slice_to_compress.end_idx,
            gist_text,
        )

        # Measure tokens after
        query_after = HistoryQuery(history.working.entries, counter)
        tokens_after = query_after.total_tokens()

        return ConsolidationResult(
            consolidated=True,
            entries_replaced=slice_to_compress.entry_count(),
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
    ) -> list[ConsolidationResult]:
        """
        Keep consolidating until we're under threshold.

        Useful when you've added a lot of content and need to
        compress multiple times to get back under budget.

        Args:
            history: The history manager
            counter: Token counter
            gist_fn: Function to generate gists
            max_iterations: Safety limit to prevent infinite loops

        Returns:
            List of all ConsolidationResults from each iteration
        """
        results = []

        for _ in range(max_iterations):
            result = await self.consolidate(history, counter, gist_fn)
            results.append(result)

            if not result.consolidated:
                break

        return results

    def __repr__(self) -> str:
        return (
            f"RollingGist(budget={self.budget}, "
            f"threshold={self.threshold}, "
            f"compress_ratio={self.compress_ratio})"
        )
