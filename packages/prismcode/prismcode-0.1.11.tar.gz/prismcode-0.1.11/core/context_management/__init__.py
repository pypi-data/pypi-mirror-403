"""
Context management utilities for Prism.

Provides flexible tools for managing conversation history:
- Ground truth storage and working history
- Token counting (accurate and fast implementations)
- History slicing (by percentage, token budget, index)
- Query interface for flexible selection
- Projections for filtering context sent to LLM

Example usage:

    from core.context_management import (
        HistoryManager, HistoryQuery, HistorySlice,
        TokenCounter, CharCounter, ModelProfile,
    )

    # Create history manager
    manager = HistoryManager()
    manager.add_user("Hello")
    manager.add_assistant("Hi there!")

    # Query interface
    query = manager.query()
    slice = query.first_percent(0.2)
    print(f"Got {slice.token_count} tokens")

    # Get text for gist generation
    gist_input = slice.to_gist_input()

    # Use model profiles for context-aware budgeting
    profile = ModelProfile.claude_sonnet()
    budget = profile.budget(0.8)  # 80% of 200k = 160k tokens
"""

from .ground_truth import (
    Entry,
    GroundTruth,
    WorkingHistory,
    HistoryManager,
    # Projections
    filter_tool_results,
    keep_recent_tool_results,
    dedupe_file_reads,
    hide_tool_args,
    truncate_tool_results,
    compose,
)

from .tokens import (
    TokenCounter,
    CharCounter,
    TiktokenCounter,
    CachedCounter,
    ModelProfile,
)

from .query import (
    HistorySlice,
    HistoryQuery,
)

from .strategies import (
    ConsolidationStrategy,
    ConsolidationResult,
    RollingGist,
    ContextAwareGist,
)

from .background_compaction import (
    BackgroundCompactor,
    CompactionStatus,
)

__all__ = [
    # Ground truth history
    "Entry",
    "GroundTruth",
    "WorkingHistory",
    "HistoryManager",
    # Projections
    "filter_tool_results",
    "keep_recent_tool_results",
    "dedupe_file_reads",
    "hide_tool_args",
    "truncate_tool_results",
    "compose",
    # Token counting
    "TokenCounter",
    "CharCounter",
    "TiktokenCounter",
    "CachedCounter",
    "ModelProfile",
    # Query and slicing
    "HistorySlice",
    "HistoryQuery",
    # Consolidation strategies
    "ConsolidationStrategy",
    "ConsolidationResult",
    "RollingGist",
    "ContextAwareGist",
    # Background compaction
    "BackgroundCompactor",
    "CompactionStatus",
]
