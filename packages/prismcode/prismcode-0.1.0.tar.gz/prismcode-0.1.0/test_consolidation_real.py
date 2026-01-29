"""
Test consolidation strategies on real session data.
Outputs results to markdown files for review.
"""
import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.context_management import (
    HistoryManager,
    CharCounter,
    TiktokenCounter,
    RollingGist,
    ContextAwareGist,
    HistoryQuery,
)


# Use the largest session
SESSION_FILE = Path.home() / ".mobius/histories/20260121_171256_7f44c4.gt.json"


def mock_gist_fn(prompt: str) -> str:
    """Mock gist function that returns a placeholder."""
    # Count roughly how much content we're summarizing
    lines = prompt.count('\n')
    return f"[MOCK GIST] Summarized ~{lines} lines of conversation history."


def format_entry_preview(entry, max_len=200) -> str:
    """Format an entry for display."""
    role = entry.role.upper()
    content = entry.content or ""

    if entry.tool_calls:
        tools = [tc["function"]["name"] for tc in entry.tool_calls]
        content = f"[Tool calls: {', '.join(tools)}]"

    if len(content) > max_len:
        content = content[:max_len] + "..."

    return f"**{role}**: {content}"


async def test_on_real_session():
    """Load a real session and test consolidation."""

    if not SESSION_FILE.exists():
        print(f"Session file not found: {SESSION_FILE}")
        return

    # Load the session
    print(f"Loading session from {SESSION_FILE}...")
    manager = HistoryManager.load(SESSION_FILE)

    # Use CharCounter for speed (TiktokenCounter would be more accurate)
    counter = CharCounter()

    # Get initial stats
    query = HistoryQuery(manager.working.entries, counter)
    initial_tokens = query.total_tokens()
    initial_entries = query.total_entries()

    output = []
    output.append("# Consolidation Strategy Test Results\n")
    output.append(f"**Session**: `{SESSION_FILE.name}`\n")
    output.append(f"**Initial entries**: {initial_entries}\n")
    output.append(f"**Initial tokens** (estimated): {initial_tokens:,}\n")
    output.append("")

    # Show first few and last few entries
    output.append("## Sample of Original History\n")
    output.append("### First 5 entries:\n")
    for i, entry in enumerate(manager.working.entries[:5]):
        output.append(f"{i}. {format_entry_preview(entry)}\n")

    output.append("\n### Last 5 entries:\n")
    for i, entry in enumerate(manager.working.entries[-5:], start=initial_entries-5):
        output.append(f"{i}. {format_entry_preview(entry)}\n")

    output.append("\n---\n")

    # =========================================================================
    # Test 1: RollingGist
    # =========================================================================
    output.append("## Test 1: RollingGist Strategy\n")

    # Reload fresh copy
    manager1 = HistoryManager.load(SESSION_FILE)

    strategy1 = RollingGist(
        budget=initial_tokens,  # Use current size as budget
        threshold=0.5,          # Trigger at 50% (will definitely trigger)
        compress_ratio=0.2,     # Compress oldest 20%
        min_entries_to_keep=4,
        gist_fn=mock_gist_fn,
    )

    output.append(f"**Settings**: budget={initial_tokens:,}, threshold=0.5, compress_ratio=0.2\n")

    # Check if should consolidate
    should = strategy1.should_consolidate(manager1, counter)
    output.append(f"**Should consolidate?**: {should}\n")

    if should:
        # Run single consolidation
        result1 = await strategy1.consolidate(manager1, counter)

        output.append(f"**Consolidated**: {result1.consolidated}\n")
        output.append(f"**Entries replaced**: {result1.entries_replaced}\n")
        output.append(f"**Tokens before**: {result1.tokens_before:,}\n")
        output.append(f"**Tokens after**: {result1.tokens_after:,}\n")
        output.append(f"**Tokens saved**: {result1.tokens_saved:,}\n")
        output.append(f"**Compression ratio**: {result1.compression_ratio:.2f}x\n")
        output.append(f"\n**Gist created**:\n```\n{result1.gist_text}\n```\n")

        # Show what history looks like now
        output.append("\n### History after consolidation (first 5 entries):\n")
        for i, entry in enumerate(manager1.working.entries[:5]):
            is_gist = "[GIST] " if entry.is_gist else ""
            output.append(f"{i}. {is_gist}{format_entry_preview(entry)}\n")

    output.append("\n---\n")

    # =========================================================================
    # Test 2: ContextAwareGist with full context
    # =========================================================================
    output.append("## Test 2: ContextAwareGist (Full Context)\n")

    manager2 = HistoryManager.load(SESSION_FILE)

    strategy2 = ContextAwareGist(
        budget=initial_tokens,
        threshold=0.5,
        compress_ratio=0.2,
        min_entries_to_keep=4,
        consolidator_context=1.0,  # Full context
        gist_fn=mock_gist_fn,
    )

    output.append(f"**Settings**: consolidator_context=1.0 (full)\n")

    if strategy2.should_consolidate(manager2, counter):
        result2 = await strategy2.consolidate(manager2, counter)

        output.append(f"**Entries replaced**: {result2.entries_replaced}\n")
        output.append(f"**Tokens saved**: {result2.tokens_saved:,}\n")
        output.append(f"**Compression ratio**: {result2.compression_ratio:.2f}x\n")

    output.append("\n---\n")

    # =========================================================================
    # Test 3: ContextAwareGist with partial context
    # =========================================================================
    output.append("## Test 3: ContextAwareGist (50% Context)\n")

    manager3 = HistoryManager.load(SESSION_FILE)

    strategy3 = ContextAwareGist(
        budget=initial_tokens,
        threshold=0.5,
        compress_ratio=0.2,
        min_entries_to_keep=4,
        consolidator_context=0.5,  # Recent 50%
        gist_fn=mock_gist_fn,
    )

    output.append(f"**Settings**: consolidator_context=0.5 (recent half)\n")

    if strategy3.should_consolidate(manager3, counter):
        result3 = await strategy3.consolidate(manager3, counter)

        output.append(f"**Entries replaced**: {result3.entries_replaced}\n")
        output.append(f"**Tokens saved**: {result3.tokens_saved:,}\n")
        output.append(f"**Compression ratio**: {result3.compression_ratio:.2f}x\n")

    output.append("\n---\n")

    # =========================================================================
    # Test 4: Multiple consolidations
    # =========================================================================
    output.append("## Test 4: Multiple Consolidations (RollingGist)\n")

    manager4 = HistoryManager.load(SESSION_FILE)

    strategy4 = RollingGist(
        budget=initial_tokens // 2,  # Target 50% of original
        threshold=0.7,
        compress_ratio=0.2,
        min_entries_to_keep=4,
        gist_fn=mock_gist_fn,
    )

    output.append(f"**Target budget**: {initial_tokens // 2:,} tokens (50% of original)\n")

    results4 = await strategy4.consolidate_until_under_budget(manager4, counter, max_iterations=10)

    consolidated_count = sum(1 for r in results4 if r.consolidated)
    total_saved = sum(r.tokens_saved for r in results4 if r.consolidated)

    output.append(f"**Consolidation rounds**: {consolidated_count}\n")
    output.append(f"**Total tokens saved**: {total_saved:,}\n")

    query_after = HistoryQuery(manager4.working.entries, counter)
    output.append(f"**Final entries**: {len(manager4.working.entries)}\n")
    output.append(f"**Final tokens**: {query_after.total_tokens():,}\n")

    output.append("\n### Final history structure:\n")
    for i, entry in enumerate(manager4.working.entries[:10]):
        is_gist = "🗜️ [GIST] " if entry.is_gist else ""
        output.append(f"{i}. {is_gist}{format_entry_preview(entry, max_len=100)}\n")

    if len(manager4.working.entries) > 10:
        output.append(f"... ({len(manager4.working.entries) - 10} more entries)\n")

    output.append("\n---\n")

    # =========================================================================
    # Test 5: Show what the consolidator prompt looks like
    # =========================================================================
    output.append("## Test 5: Sample Consolidator Prompt (ContextAwareGist)\n")

    manager5 = HistoryManager.load(SESSION_FILE)

    captured_prompt = []

    def capture_prompt(prompt: str) -> str:
        captured_prompt.append(prompt)
        return "[CAPTURED]"

    strategy5 = ContextAwareGist(
        budget=initial_tokens,
        threshold=0.5,
        compress_ratio=0.1,  # Small slice to keep prompt manageable
        min_entries_to_keep=4,
        consolidator_context=0.3,  # 30% context
        gist_fn=capture_prompt,
    )

    await strategy5.consolidate(manager5, counter)

    if captured_prompt:
        # Truncate for display
        prompt_text = captured_prompt[0]
        if len(prompt_text) > 5000:
            prompt_text = prompt_text[:2500] + "\n\n... [TRUNCATED] ...\n\n" + prompt_text[-2500:]

        output.append("```\n")
        output.append(prompt_text)
        output.append("\n```\n")

    # Write output
    output_file = Path("/Users/offbeat/mobius/consolidation_test_results.md")
    output_file.write_text("\n".join(output))
    print(f"Results written to {output_file}")


if __name__ == "__main__":
    asyncio.run(test_on_real_session())
