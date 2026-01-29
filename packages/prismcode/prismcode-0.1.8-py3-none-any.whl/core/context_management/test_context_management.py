"""
Tests for context management system.

Run with: bun test core/context_management/test_context_management.py
"""
import sys
from pathlib import Path
from typing import List
import uuid
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.context_management.ground_truth import Entry, HistoryManager
from core.context_management import (
    CharCounter,
    CachedCounter,
    ModelProfile,
    HistorySlice,
    HistoryQuery,
)


# =============================================================================
# Test Fixtures
# =============================================================================

def make_entry(role: str, content: str, **meta) -> Entry:
    """Create a test entry."""
    msg = {"role": role, "content": content}
    if role == "tool":
        msg["tool_call_id"] = meta.pop("tool_call_id", f"call_{uuid.uuid4().hex[:8]}")
    if role == "assistant" and "tool_calls" in meta:
        msg["tool_calls"] = meta.pop("tool_calls")
        msg["content"] = content or None

    return Entry(
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        message=msg,
        meta=meta,
    )


def make_sample_history() -> List[Entry]:
    """Create a sample history for testing."""
    return [
        make_entry("user", "Hello, can you help me?"),
        make_entry("assistant", "Of course! What do you need help with?"),
        make_entry("user", "I need to read a file."),
        make_entry("assistant", None, tool_calls=[
            {"id": "call_1", "function": {"name": "read_file", "arguments": '{"path": "test.py"}'}}
        ]),
        make_entry("tool", "def hello():\n    print('world')", tool_call_id="call_1", tool_name="read_file", file_path="test.py"),
        make_entry("assistant", "I found a simple hello function in test.py."),
        make_entry("user", "Can you modify it?"),
        make_entry("assistant", None, tool_calls=[
            {"id": "call_2", "function": {"name": "edit_file", "arguments": '{"path": "test.py", "old": "world", "new": "universe"}'}}
        ]),
        make_entry("tool", "File edited successfully.", tool_call_id="call_2", tool_name="edit_file", file_path="test.py"),
        make_entry("assistant", "Done! I changed 'world' to 'universe'."),
    ]


# =============================================================================
# CharCounter Tests
# =============================================================================

def test_char_counter_basic():
    """CharCounter counts tokens as chars/4"""
    counter = CharCounter()

    # 20 chars = 5 tokens
    assert counter.count("12345678901234567890") == 5

    # Empty string = 0 tokens
    assert counter.count("") == 0

    # Min 1 token for non-empty
    assert counter.count("a") == 1


def test_char_counter_message():
    """CharCounter counts message tokens"""
    counter = CharCounter()

    msg = {"role": "user", "content": "Hello world"}  # 11 chars
    tokens = counter.count_message(msg)

    # Should have some tokens
    assert tokens > 0


def test_char_counter_tool_calls():
    """CharCounter counts tool calls"""
    counter = CharCounter()

    msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "1", "function": {"name": "read_file", "arguments": '{"path": "test.py"}'}}
        ]
    }
    tokens = counter.count_message(msg)
    assert tokens > 0


# =============================================================================
# CachedCounter Tests
# =============================================================================

def test_cached_counter():
    """CachedCounter caches repeated counts"""
    base = CharCounter()
    cached = CachedCounter(base, maxsize=100)

    text = "Hello world" * 100

    # First call
    result1 = cached.count(text)
    info1 = cached.cache_info()

    # Second call (should be cached)
    result2 = cached.count(text)
    info2 = cached.cache_info()

    assert result1 == result2
    assert info2.hits == info1.hits + 1


# =============================================================================
# ModelProfile Tests
# =============================================================================

def test_model_profile_budget():
    """ModelProfile calculates budget correctly"""
    profile = ModelProfile("test", context_window=100_000)

    assert profile.budget(1.0) == 100_000
    assert profile.budget(0.8) == 80_000
    assert profile.budget(0.5) == 50_000


def test_model_presets():
    """ModelProfile provides preset profiles"""
    gpt4 = ModelProfile.gpt4()
    assert gpt4.context_window == 8_192

    claude = ModelProfile.claude_sonnet()
    assert claude.context_window == 200_000

    gemini = ModelProfile.gemini_pro()
    assert gemini.context_window == 1_000_000


def test_model_profile_counter():
    """ModelProfile creates counter"""
    profile = ModelProfile.gpt4()
    counter = profile.counter(use_tiktoken=False)

    assert isinstance(counter, CharCounter)


# =============================================================================
# HistoryQuery Tests - Measurement
# =============================================================================

def test_query_total_tokens():
    """HistoryQuery counts total tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    total = query.total_tokens()
    assert total > 0


def test_query_total_entries():
    """HistoryQuery counts total entries"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    assert query.total_entries() == 10


def test_query_cumulative():
    """HistoryQuery provides cumulative tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    cumulative = query.cumulative_tokens()

    assert len(cumulative) == 10
    # Should be monotonically increasing
    for i in range(1, len(cumulative)):
        assert cumulative[i] >= cumulative[i-1]


# =============================================================================
# HistoryQuery Tests - Index Selection
# =============================================================================

def test_query_range():
    """HistoryQuery selects range by index"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.range(2, 5)

    assert slice.entry_count() == 3
    assert slice.start_idx == 2
    assert slice.end_idx == 5


def test_query_before():
    """HistoryQuery selects before index"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.before(3)

    assert slice.entry_count() == 3
    assert slice.start_idx == 0
    assert slice.end_idx == 3


def test_query_after():
    """HistoryQuery selects after index"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.after(7)

    assert slice.entry_count() == 2
    assert slice.start_idx == 8


# =============================================================================
# HistoryQuery Tests - Token Selection
# =============================================================================

def test_query_first_n_tokens():
    """HistoryQuery selects first N tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    total = query.total_tokens()
    slice = query.first_n_tokens(total // 2)

    assert slice.token_count <= total // 2 + 50  # some tolerance
    assert slice.start_idx == 0


def test_query_last_n_tokens():
    """HistoryQuery selects last N tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    total = query.total_tokens()
    slice = query.last_n_tokens(total // 2)

    assert slice.token_count <= total // 2 + 50
    assert slice.end_idx == 10


# =============================================================================
# HistoryQuery Tests - Percentage Selection
# =============================================================================

def test_query_first_percent():
    """HistoryQuery selects first 20% by tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.first_percent(0.2)

    # Should be roughly 20% of tokens
    assert slice.percent_of_source_tokens() <= 0.35  # some tolerance
    assert slice.start_idx == 0


def test_query_last_percent():
    """HistoryQuery selects last 50% by tokens"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.last_percent(0.5)

    assert slice.percent_of_source_tokens() <= 0.65
    assert slice.end_idx == 10


def test_query_first_percent_by_count():
    """HistoryQuery selects first 30% by entry count"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.first_percent_by_count(0.3)

    assert slice.entry_count() == 3  # 30% of 10


# =============================================================================
# HistoryQuery Tests - Boundary Finding
# =============================================================================

def test_query_index_at_token():
    """HistoryQuery finds index at token position"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    total = query.total_tokens()

    # At 0, should be index 0
    assert query.index_at_token(0) == 0

    # At end, should be last index
    assert query.index_at_token(total) == 9


def test_query_safe_boundary():
    """HistoryQuery finds safe boundary avoiding tool splits"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    # Entry 3 is assistant with tool_calls, entry 4 is tool result
    # If we try to cut at 4, it should move to 5 (after tool result)
    safe = query.safe_boundary_near(4)
    assert safe == 5


# =============================================================================
# HistoryQuery Tests - Chunking
# =============================================================================

def test_query_chunk_by_tokens():
    """HistoryQuery chunks by token size"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    total = query.total_tokens()
    chunks = query.chunk_by_tokens(total // 3)

    assert len(chunks) >= 2

    # All entries should be covered
    all_entries = []
    for chunk in chunks:
        all_entries.extend(chunk.entries)
    assert len(all_entries) == 10


def test_query_chunk_by_count():
    """HistoryQuery chunks by entry count"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    chunks = query.chunk_by_count(3)

    assert len(chunks) == 4  # 10 entries / 3 = 4 chunks
    assert chunks[0].entry_count() == 3
    assert chunks[-1].entry_count() == 1  # remainder


# =============================================================================
# HistoryQuery Tests - Filtering
# =============================================================================

def test_query_by_role():
    """HistoryQuery filters by role"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    user_only = query.by_role("user")

    assert user_only.total_entries() == 3


def test_query_where():
    """HistoryQuery filters by predicate"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    tools_only = query.where(lambda e: e.role == "tool")

    assert tools_only.total_entries() == 2


# =============================================================================
# HistorySlice Tests
# =============================================================================

def test_slice_to_messages():
    """HistorySlice converts to messages"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.range(0, 3)
    messages = slice.to_messages()

    assert len(messages) == 3
    assert messages[0]["role"] == "user"


def test_slice_to_gist_input():
    """HistorySlice converts to gist input"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.range(0, 5)
    gist_input = slice.to_gist_input()

    assert "USER:" in gist_input
    assert "ASSISTANT" in gist_input
    assert "TOOL" in gist_input


def test_slice_ids():
    """HistorySlice provides IDs for tracking"""
    entries = make_sample_history()
    query = HistoryQuery(entries, CharCounter())

    slice = query.range(2, 5)
    ids = slice.ids()

    assert len(ids) == 3
    assert ids[0] == entries[2].id


# =============================================================================
# Integration Tests
# =============================================================================

def test_history_manager_query():
    """HistoryManager provides query interface"""
    manager = HistoryManager()

    # Add some messages
    manager.add_user("Hello")
    manager.add_assistant("Hi there!")
    manager.add_user("How are you?")
    manager.add_assistant("I'm doing well!")

    # Query should work
    query = manager.query()

    assert query.total_entries() == 4

    slice = query.first_percent(0.5)
    assert slice.entry_count() > 0


def test_gist_workflow():
    """Test the full gist workflow: query -> slice -> replace"""
    manager = HistoryManager()

    # Build up some history
    manager.add_user("First question")
    manager.add_assistant("First answer")
    manager.add_user("Second question")
    manager.add_assistant("Second answer")
    manager.add_user("Third question")
    manager.add_assistant("Third answer")

    # Query first 50%
    query = manager.query()
    slice = query.first_percent(0.5)

    # Get gist input
    gist_input = slice.to_gist_input()
    assert len(gist_input) > 0

    # Replace with gist
    gist_entry = manager.working.replace_range_with_gist(
        slice.start_idx,
        slice.end_idx,
        "User asked first and second questions, assistant answered both."
    )

    assert gist_entry.is_gist == True
    assert len(manager.working.entries) < 6


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    import traceback

    test_functions = [
        # CharCounter
        test_char_counter_basic,
        test_char_counter_message,
        test_char_counter_tool_calls,
        # CachedCounter
        test_cached_counter,
        # ModelProfile
        test_model_profile_budget,
        test_model_presets,
        test_model_profile_counter,
        # HistoryQuery - Measurement
        test_query_total_tokens,
        test_query_total_entries,
        test_query_cumulative,
        # HistoryQuery - Index Selection
        test_query_range,
        test_query_before,
        test_query_after,
        # HistoryQuery - Token Selection
        test_query_first_n_tokens,
        test_query_last_n_tokens,
        # HistoryQuery - Percentage Selection
        test_query_first_percent,
        test_query_last_percent,
        test_query_first_percent_by_count,
        # HistoryQuery - Boundary Finding
        test_query_index_at_token,
        test_query_safe_boundary,
        # HistoryQuery - Chunking
        test_query_chunk_by_tokens,
        test_query_chunk_by_count,
        # HistoryQuery - Filtering
        test_query_by_role,
        test_query_where,
        # HistorySlice
        test_slice_to_messages,
        test_slice_to_gist_input,
        test_slice_ids,
        # Integration
        test_history_manager_query,
        test_gist_workflow,
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
