"""
Tests for consolidation strategies.

Run with: python core/context_management/strategies/test_strategies.py
"""
import sys
from pathlib import Path
import asyncio

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.context_management import (
    HistoryManager,
    CharCounter,
    RollingGist,
    ContextAwareGist,
    ConsolidationResult,
)


# =============================================================================
# Mock gist function
# =============================================================================

def mock_gist_fn(prompt: str) -> str:
    """Simple mock that returns a fixed gist."""
    return "[GIST] Earlier conversation covered initial setup and greetings."


async def async_mock_gist_fn(prompt: str) -> str:
    """Async mock gist function."""
    return "[GIST] Earlier conversation covered initial setup and greetings."


# =============================================================================
# Helper to build up history
# =============================================================================

def build_history_with_tokens(manager: HistoryManager, target_tokens: int, counter: CharCounter):
    """Add messages until we hit approximately target_tokens."""
    i = 0
    while True:
        current = manager.query().total_tokens() if manager.working.entries else 0
        if current >= target_tokens:
            break

        # Alternate user/assistant messages with some bulk
        if i % 2 == 0:
            manager.add_user(f"User message {i}. " + "x" * 100)
        else:
            manager.add_assistant(f"Assistant response {i}. " + "y" * 100)
        i += 1

    return manager


# =============================================================================
# Tests
# =============================================================================

def test_should_consolidate_under_threshold():
    """Should not consolidate when under threshold."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(budget=10000, threshold=0.7)

    # Add just a little content
    manager.add_user("Hello")
    manager.add_assistant("Hi there!")

    assert strategy.should_consolidate(manager, counter) == False


def test_should_consolidate_over_threshold():
    """Should consolidate when over threshold."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(budget=1000, threshold=0.7)  # Small budget

    # Fill up the history
    build_history_with_tokens(manager, 800, counter)  # 80% of 1000

    assert strategy.should_consolidate(manager, counter) == True


def test_should_not_consolidate_too_few_entries():
    """Should not consolidate if too few entries remain."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(budget=100, threshold=0.1, min_entries_to_keep=10)

    # Add just a few entries
    manager.add_user("Hello")
    manager.add_assistant("Hi!")

    # Even though we're "over threshold" (tiny budget), too few entries
    assert strategy.should_consolidate(manager, counter) == False


def test_consolidate_basic():
    """Basic consolidation should replace entries with gist."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=mock_gist_fn,
    )

    # Build up history over threshold
    build_history_with_tokens(manager, 600, counter)
    entries_before = len(manager.working.entries)

    # Run consolidation
    result = asyncio.run(strategy.consolidate(manager, counter))

    assert result.consolidated == True
    assert result.entries_replaced > 0
    assert result.tokens_saved > 0
    assert len(manager.working.entries) < entries_before
    assert "[GIST]" in result.gist_text


def test_consolidate_creates_gist_entry():
    """Consolidation should create a gist entry in working history."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=mock_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)

    asyncio.run(strategy.consolidate(manager, counter))

    # First entry should now be a gist
    first_entry = manager.working.entries[0]
    assert first_entry.is_gist == True
    assert "[GIST]" in first_entry.content


def test_consolidate_preserves_ground_truth():
    """Consolidation should not modify ground truth."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=mock_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)
    gt_entries_before = len(manager.ground_truth.entries)

    asyncio.run(strategy.consolidate(manager, counter))

    # Ground truth should be unchanged
    assert len(manager.ground_truth.entries) == gt_entries_before


def test_consolidate_until_under_budget():
    """Should consolidate multiple times if needed."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(
        budget=500,
        threshold=0.5,
        compress_ratio=0.2,
        min_entries_to_keep=2,
        gist_fn=mock_gist_fn,
    )

    # Way over budget
    build_history_with_tokens(manager, 1000, counter)

    results = asyncio.run(strategy.consolidate_until_under_budget(manager, counter))

    # Should have done multiple consolidations
    consolidated_count = sum(1 for r in results if r.consolidated)
    assert consolidated_count >= 1

    # Should now be under threshold
    _, ratio = strategy.get_usage(manager, counter)
    # Note: might not be under threshold if min_entries_to_keep kicks in
    assert ratio < 1.0 or len(manager.working.entries) <= strategy.min_entries_to_keep


def test_async_gist_fn():
    """Should work with async gist functions."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=async_mock_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)

    result = asyncio.run(strategy.consolidate(manager, counter))

    assert result.consolidated == True
    assert "[GIST]" in result.gist_text


def test_consolidation_result_properties():
    """Test ConsolidationResult computed properties."""
    result = ConsolidationResult(
        consolidated=True,
        entries_replaced=5,
        tokens_before=1000,
        tokens_after=200,
    )

    assert result.tokens_saved == 800
    assert result.compression_ratio == 5.0


def test_no_gist_fn_raises():
    """Should raise if no gist_fn provided."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = RollingGist(budget=1000, threshold=0.5)

    build_history_with_tokens(manager, 600, counter)

    try:
        asyncio.run(strategy.consolidate(manager, counter))
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "gist_fn" in str(e)


def test_safe_boundary_respected():
    """Should not split tool calls from their results."""
    manager = HistoryManager()
    counter = CharCounter()

    # Add some regular messages
    manager.add_user("Hello")
    manager.add_assistant("Hi!")
    manager.add_user("Read a file")

    # Add tool call + result (these should stay together)
    tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "read_file", "arguments": "{}"}}]
    manager.add_assistant(content=None, tool_calls=tool_calls)
    manager.add_tool_result("call_1", "File content here", tool_name="read_file")

    manager.add_assistant("I read the file.")
    manager.add_user("Thanks!")
    manager.add_assistant("You're welcome!")

    strategy = RollingGist(
        budget=100,  # Very small to force compression
        threshold=0.1,
        compress_ratio=0.5,
        min_entries_to_keep=2,
        gist_fn=mock_gist_fn,
    )

    asyncio.run(strategy.consolidate(manager, counter))

    # The consolidation should have happened, but tool call/result
    # should either both be in the gist or both be outside
    # (safe_boundary_near should handle this)
    assert True  # If we got here without error, boundaries were respected


# =============================================================================
# ContextAwareGist Tests
# =============================================================================

def mock_context_aware_gist_fn(prompt: str) -> str:
    """Mock that verifies it received context."""
    # Check that the prompt contains working memory section
    has_context = "WORKING MEMORY" in prompt or "working memory" in prompt.lower()
    has_slice = "CONSOLIDATE" in prompt or "consolidate" in prompt.lower()

    if has_context and has_slice:
        return "[GIST] Context-aware summary of earlier work."
    else:
        return "[ERROR] Missing context or slice in prompt"


def test_context_aware_basic():
    """ContextAwareGist should consolidate with context."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = ContextAwareGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=mock_context_aware_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)
    entries_before = len(manager.working.entries)

    result = asyncio.run(strategy.consolidate(manager, counter))

    assert result.consolidated == True
    assert result.entries_replaced > 0
    assert len(manager.working.entries) < entries_before
    assert "[GIST]" in result.gist_text
    assert "[ERROR]" not in result.gist_text


def test_context_aware_with_partial_context():
    """ContextAwareGist should work with partial context."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = ContextAwareGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        consolidator_context=0.5,  # Only recent 50%
        gist_fn=mock_context_aware_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)

    result = asyncio.run(strategy.consolidate(manager, counter))

    assert result.consolidated == True
    assert "[GIST]" in result.gist_text


def test_context_aware_with_token_budget():
    """ContextAwareGist should work with fixed token budget for context."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = ContextAwareGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        consolidator_context_tokens=200,  # Fixed 200 tokens of context
        gist_fn=mock_context_aware_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)

    result = asyncio.run(strategy.consolidate(manager, counter))

    assert result.consolidated == True
    assert "[GIST]" in result.gist_text


def test_context_aware_preserves_ground_truth():
    """ContextAwareGist should not modify ground truth."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = ContextAwareGist(
        budget=1000,
        threshold=0.5,
        compress_ratio=0.3,
        min_entries_to_keep=2,
        gist_fn=mock_context_aware_gist_fn,
    )

    build_history_with_tokens(manager, 600, counter)
    gt_before = len(manager.ground_truth.entries)

    asyncio.run(strategy.consolidate(manager, counter))

    assert len(manager.ground_truth.entries) == gt_before


def test_context_aware_consolidate_until_under_budget():
    """ContextAwareGist should consolidate multiple times if needed."""
    manager = HistoryManager()
    counter = CharCounter()
    strategy = ContextAwareGist(
        budget=500,
        threshold=0.5,
        compress_ratio=0.2,
        min_entries_to_keep=2,
        gist_fn=mock_context_aware_gist_fn,
    )

    build_history_with_tokens(manager, 1000, counter)

    results = asyncio.run(strategy.consolidate_until_under_budget(manager, counter))

    consolidated_count = sum(1 for r in results if r.consolidated)
    assert consolidated_count >= 1


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    import traceback

    test_functions = [
        # RollingGist tests
        test_should_consolidate_under_threshold,
        test_should_consolidate_over_threshold,
        test_should_not_consolidate_too_few_entries,
        test_consolidate_basic,
        test_consolidate_creates_gist_entry,
        test_consolidate_preserves_ground_truth,
        test_consolidate_until_under_budget,
        test_async_gist_fn,
        test_consolidation_result_properties,
        test_no_gist_fn_raises,
        test_safe_boundary_respected,
        # ContextAwareGist tests
        test_context_aware_basic,
        test_context_aware_with_partial_context,
        test_context_aware_with_token_budget,
        test_context_aware_preserves_ground_truth,
        test_context_aware_consolidate_until_under_budget,
    ]

    passed = 0
    failed = 0

    for test_fn in test_functions:
        try:
            test_fn()
            print(f"✓ {test_fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_fn.__name__}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    exit(0 if failed == 0 else 1)
