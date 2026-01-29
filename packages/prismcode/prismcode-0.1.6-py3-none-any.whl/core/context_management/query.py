"""
History querying and slicing utilities.

Provides flexible selection of history entries by:
- Percentage (of tokens or entry count)
- Token budget
- Index ranges
- Filtering predicates

Returns HistorySlice objects that carry metadata for gist generation.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from .ground_truth import Entry

from .tokens import TokenCounter, CharCounter


@dataclass
class HistorySlice:
    """
    A view into history with metadata.

    Carries the entries plus information about where they came from
    and how many tokens they contain - everything needed to make
    decisions about gist generation.
    """
    entries: List["Entry"]
    start_idx: int
    end_idx: int  # exclusive, like Python slices
    token_count: int
    total_source_entries: int = 0  # how many entries in the source
    total_source_tokens: int = 0   # how many tokens in the source

    def to_messages(self) -> List[Dict[str, Any]]:
        """Export as raw LiteLLM messages."""
        return [e.message for e in self.entries]

    def to_gist_input(self, include_metadata: bool = True) -> str:
        """
        Format entries as text for feeding to a gist-generating LLM.

        Args:
            include_metadata: If True, include timestamps and tool names.
        """
        lines = []

        for entry in self.entries:
            role = entry.role.upper()

            if entry.role == "user":
                content = entry.content or ""
                if entry.is_gist:
                    lines.append(f"[PREVIOUS GIST]\n{content}\n")
                else:
                    lines.append(f"USER: {content}\n")

            elif entry.role == "assistant":
                content = entry.content or ""
                if entry.tool_calls:
                    tool_names = [tc["function"]["name"] for tc in entry.tool_calls]
                    if content:
                        lines.append(f"ASSISTANT: {content}")
                    lines.append(f"ASSISTANT called tools: {', '.join(tool_names)}\n")
                else:
                    lines.append(f"ASSISTANT: {content}\n")

            elif entry.role == "tool":
                tool_name = entry.tool_name or "unknown"
                content = entry.content or ""
                # Truncate very long tool results for gist input
                if len(content) > 2000:
                    content = content[:2000] + f"... [truncated, {len(content)} chars]"
                if include_metadata:
                    file_path = entry.file_path
                    if file_path:
                        lines.append(f"TOOL ({tool_name}) [{file_path}]: {content}\n")
                    else:
                        lines.append(f"TOOL ({tool_name}): {content}\n")
                else:
                    lines.append(f"TOOL: {content}\n")

            elif entry.role == "system":
                # Usually skip system messages in gist
                pass

        return "".join(lines)

    def ids(self) -> List[str]:
        """Get IDs of all entries in this slice."""
        return [e.id for e in self.entries]

    def entry_count(self) -> int:
        """Number of entries in this slice."""
        return len(self.entries)

    def is_empty(self) -> bool:
        """Check if slice is empty."""
        return len(self.entries) == 0

    def percent_of_source_tokens(self) -> float:
        """What percentage of source tokens does this slice represent?"""
        if self.total_source_tokens == 0:
            return 0.0
        return self.token_count / self.total_source_tokens

    def percent_of_source_entries(self) -> float:
        """What percentage of source entries does this slice represent?"""
        if self.total_source_entries == 0:
            return 0.0
        return len(self.entries) / self.total_source_entries

    def __repr__(self) -> str:
        return (
            f"HistorySlice(entries={len(self.entries)}, "
            f"range=[{self.start_idx}:{self.end_idx}], "
            f"tokens={self.token_count})"
        )


class HistoryQuery:
    """
    Query interface for history entries.

    Provides flexible selection by percentage, token budget, index,
    and filtering predicates. All selection methods return HistorySlice
    objects with full metadata.

    Example:
        query = HistoryQuery(entries, counter)

        # Get first 20% of tokens
        slice = query.first_percent(0.2)
        print(f"Got {slice.token_count} tokens")

        # Get last 50k tokens
        slice = query.last_n_tokens(50_000)

        # Find where to cut for a target budget
        idx = query.index_at_token(10_000)
    """

    def __init__(self, entries: List["Entry"], counter: TokenCounter = None):
        """
        Args:
            entries: List of Entry objects to query.
            counter: TokenCounter implementation. Defaults to CharCounter.
        """
        self._entries = entries
        self._counter = counter or CharCounter()

        # Precompute token counts for efficiency
        self._token_counts: List[int] = []
        self._cumulative: List[int] = []
        self._total_tokens: int = 0

        self._compute_tokens()

    def _compute_tokens(self):
        """Precompute token counts and cumulative sums."""
        self._token_counts = []
        self._cumulative = []
        running_total = 0

        for entry in self._entries:
            count = self._counter.count_message(entry.message)
            self._token_counts.append(count)
            running_total += count
            self._cumulative.append(running_total)

        self._total_tokens = running_total

    # =========================================================================
    # Measurement
    # =========================================================================

    def total_tokens(self) -> int:
        """Total tokens in all entries."""
        return self._total_tokens

    def total_entries(self) -> int:
        """Total number of entries."""
        return len(self._entries)

    def token_at(self, idx: int) -> int:
        """Token count for a single entry by index."""
        if not self._entries or idx < 0 or idx >= len(self._entries):
            return 0
        return self._token_counts[idx]

    def cumulative_tokens(self) -> List[int]:
        """
        Cumulative token counts.

        cumulative[i] = total tokens in entries[0:i+1]

        Useful for visualization and debugging.
        """
        return self._cumulative.copy()

    def tokens_in_range(self, start: int, end: int = None) -> int:
        """Get total tokens in a range of entries."""
        if not self._entries:
            return 0
        if end is None:
            end = len(self._entries)

        start = max(0, start)
        end = min(len(self._entries), end)

        if start >= end:
            return 0

        end_cumulative = self._cumulative[end - 1] if end > 0 else 0
        start_cumulative = self._cumulative[start - 1] if start > 0 else 0

        return end_cumulative - start_cumulative

    # =========================================================================
    # Selection by index
    # =========================================================================

    def _make_slice(self, start: int, end: int) -> HistorySlice:
        """Create a HistorySlice for the given range."""
        start = max(0, start)
        end = min(len(self._entries), end)

        if start >= end or not self._entries:
            return HistorySlice(
                entries=[],
                start_idx=start,
                end_idx=start,
                token_count=0,
                total_source_entries=len(self._entries),
                total_source_tokens=self._total_tokens,
            )

        entries = self._entries[start:end]
        token_count = self.tokens_in_range(start, end)

        return HistorySlice(
            entries=entries,
            start_idx=start,
            end_idx=end,
            token_count=token_count,
            total_source_entries=len(self._entries),
            total_source_tokens=self._total_tokens,
        )

    def range(self, start: int, end: int = None) -> HistorySlice:
        """
        Get entries by index range.

        Args:
            start: Start index (inclusive)
            end: End index (exclusive). Defaults to end of entries.
        """
        if end is None:
            end = len(self._entries)
        return self._make_slice(start, end)

    def before(self, idx: int) -> HistorySlice:
        """Get all entries before an index (exclusive)."""
        return self._make_slice(0, idx)

    def after(self, idx: int) -> HistorySlice:
        """Get all entries after an index (exclusive)."""
        return self._make_slice(idx + 1, len(self._entries))

    def all(self) -> HistorySlice:
        """Get all entries."""
        return self._make_slice(0, len(self._entries))

    # =========================================================================
    # Selection by token budget
    # =========================================================================

    def first_n_tokens(self, n: int) -> HistorySlice:
        """
        Get entries from the start up to N tokens.

        Returns entries[0:i] where cumulative tokens <= n.
        """
        if not self._entries or n <= 0:
            return self._make_slice(0, 0)

        # Find first index where cumulative exceeds n
        end_idx = 0
        for i, cumulative in enumerate(self._cumulative):
            if cumulative > n:
                break
            end_idx = i + 1

        return self._make_slice(0, end_idx)

    def last_n_tokens(self, n: int) -> HistorySlice:
        """
        Get entries from the end totaling up to N tokens.

        Returns entries[i:] where total tokens <= n.
        """
        if not self._entries or n <= 0:
            return self._make_slice(len(self._entries), len(self._entries))

        if n >= self._total_tokens:
            return self._make_slice(0, len(self._entries))

        # Work backwards to find start index
        target = self._total_tokens - n
        start_idx = len(self._entries)

        for i, cumulative in enumerate(self._cumulative):
            if cumulative >= target:
                start_idx = i + 1
                break

        return self._make_slice(start_idx, len(self._entries))

    def tokens_between(self, start_tokens: int, end_tokens: int) -> HistorySlice:
        """
        Get entries between two token positions.

        Args:
            start_tokens: Start at this token count from beginning
            end_tokens: End at this token count from beginning
        """
        start_idx = self.index_at_token(start_tokens)
        end_idx = self.index_at_token(end_tokens)
        return self._make_slice(start_idx, end_idx + 1)

    # =========================================================================
    # Selection by percentage
    # =========================================================================

    def first_percent(self, pct: float) -> HistorySlice:
        """
        Get first X% of history by TOKEN count.

        Args:
            pct: Percentage as decimal (0.2 = 20%)
        """
        if pct <= 0:
            return self._make_slice(0, 0)
        if pct >= 1.0:
            return self._make_slice(0, len(self._entries))

        target_tokens = int(self._total_tokens * pct)
        return self.first_n_tokens(target_tokens)

    def last_percent(self, pct: float) -> HistorySlice:
        """
        Get last X% of history by TOKEN count.

        Args:
            pct: Percentage as decimal (0.2 = 20%)
        """
        if pct <= 0:
            return self._make_slice(len(self._entries), len(self._entries))
        if pct >= 1.0:
            return self._make_slice(0, len(self._entries))

        target_tokens = int(self._total_tokens * pct)
        return self.last_n_tokens(target_tokens)

    def first_percent_by_count(self, pct: float) -> HistorySlice:
        """
        Get first X% of history by ENTRY count.

        Args:
            pct: Percentage as decimal (0.2 = 20%)
        """
        if pct <= 0:
            return self._make_slice(0, 0)
        if pct >= 1.0:
            return self._make_slice(0, len(self._entries))

        target_count = max(1, int(len(self._entries) * pct))
        return self._make_slice(0, target_count)

    def last_percent_by_count(self, pct: float) -> HistorySlice:
        """
        Get last X% of history by ENTRY count.

        Args:
            pct: Percentage as decimal (0.2 = 20%)
        """
        if pct <= 0:
            return self._make_slice(len(self._entries), len(self._entries))
        if pct >= 1.0:
            return self._make_slice(0, len(self._entries))

        target_count = max(1, int(len(self._entries) * pct))
        start_idx = len(self._entries) - target_count
        return self._make_slice(start_idx, len(self._entries))

    # =========================================================================
    # Boundary finding
    # =========================================================================

    def index_at_token(self, target_tokens: int) -> int:
        """
        Find which entry index contains the Nth token.

        Returns the index of the entry that contains or follows
        the target token position.
        """
        if not self._entries or target_tokens <= 0:
            return 0

        if target_tokens >= self._total_tokens:
            return len(self._entries) - 1

        for i, cumulative in enumerate(self._cumulative):
            if cumulative >= target_tokens:
                return i

        return len(self._entries) - 1

    def index_at_percent(self, pct: float) -> int:
        """
        Find entry index at X% of total tokens.

        Args:
            pct: Percentage as decimal (0.2 = 20%)
        """
        target_tokens = int(self._total_tokens * pct)
        return self.index_at_token(target_tokens)

    def safe_boundary_near(self, idx: int) -> int:
        """
        Find a safe boundary near the given index.

        Avoids splitting tool_call/tool_result pairs by moving
        the boundary to after a complete exchange.

        Returns the adjusted index (may be same as input).
        """
        if not self._entries or idx <= 0:
            return 0
        if idx >= len(self._entries):
            return len(self._entries)

        # Look at entry at idx-1 (the last one that would be included)
        last_included = self._entries[idx - 1]

        # If it's an assistant message with tool calls, we need to include the results
        if last_included.role == "assistant" and last_included.tool_calls:
            # Find all tool_call_ids
            call_ids = {tc["id"] for tc in last_included.tool_calls}

            # Scan forward to find all matching tool results
            new_idx = idx
            for i in range(idx, len(self._entries)):
                entry = self._entries[i]
                if entry.role == "tool" and entry.tool_call_id in call_ids:
                    new_idx = i + 1
                    call_ids.discard(entry.tool_call_id)
                    if not call_ids:
                        break
                elif entry.role != "tool":
                    # Hit a non-tool message, stop
                    break

            return new_idx

        # If it's a tool result, include any subsequent tool results for same call
        if last_included.role == "tool":
            # Check if there are more tool results immediately following
            new_idx = idx
            for i in range(idx, len(self._entries)):
                if self._entries[i].role == "tool":
                    new_idx = i + 1
                else:
                    break
            return new_idx

        return idx

    # =========================================================================
    # Chunking
    # =========================================================================

    def chunk_by_tokens(self, size: int) -> List[HistorySlice]:
        """
        Split history into chunks of approximately `size` tokens each.

        Useful for processing history in batches or for strategies
        that summarize in fixed-size chunks.
        """
        if not self._entries or size <= 0:
            return []

        chunks = []
        start_idx = 0

        while start_idx < len(self._entries):
            # Find end index for this chunk
            chunk_tokens = 0
            end_idx = start_idx

            for i in range(start_idx, len(self._entries)):
                token_count = self._token_counts[i]
                if chunk_tokens + token_count > size and end_idx > start_idx:
                    break
                chunk_tokens += token_count
                end_idx = i + 1

            chunks.append(self._make_slice(start_idx, end_idx))
            start_idx = end_idx

        return chunks

    def chunk_by_count(self, size: int) -> List[HistorySlice]:
        """
        Split history into chunks of `size` entries each.
        """
        if not self._entries or size <= 0:
            return []

        chunks = []
        for start in range(0, len(self._entries), size):
            end = min(start + size, len(self._entries))
            chunks.append(self._make_slice(start, end))

        return chunks

    # =========================================================================
    # Filtering (returns new HistoryQuery)
    # =========================================================================

    def where(self, predicate: Callable[["Entry"], bool]) -> "HistoryQuery":
        """
        Filter entries by predicate, returning a new HistoryQuery.

        Note: Indices in the returned query are relative to filtered list.
        """
        filtered = [e for e in self._entries if predicate(e)]
        return HistoryQuery(filtered, self._counter)

    def by_role(self, *roles: str) -> "HistoryQuery":
        """Filter to entries with specific roles."""
        role_set = set(roles)
        return self.where(lambda e: e.role in role_set)

    def by_tool(self, *tool_names: str) -> "HistoryQuery":
        """Filter to entries for specific tools."""
        tool_set = set(tool_names)
        return self.where(lambda e: e.tool_name in tool_set)

    def excluding_gists(self) -> "HistoryQuery":
        """Filter out gist entries."""
        return self.where(lambda e: not e.is_gist)

    def only_gists(self) -> "HistoryQuery":
        """Filter to only gist entries."""
        return self.where(lambda e: e.is_gist)

    # =========================================================================
    # Utilities
    # =========================================================================

    def token_histogram(self, buckets: int = 10) -> List[Dict[str, Any]]:
        """
        Get token distribution across history.

        Useful for understanding where tokens are concentrated.
        Returns list of dicts with bucket info.
        """
        if not self._entries:
            return []

        entries_per_bucket = max(1, len(self._entries) // buckets)
        histogram = []

        for i in range(0, len(self._entries), entries_per_bucket):
            end = min(i + entries_per_bucket, len(self._entries))
            tokens = self.tokens_in_range(i, end)

            # Count by role
            role_counts = {}
            for j in range(i, end):
                role = self._entries[j].role
                role_counts[role] = role_counts.get(role, 0) + self._token_counts[j]

            histogram.append({
                "start_idx": i,
                "end_idx": end,
                "entry_count": end - i,
                "tokens": tokens,
                "percent": tokens / self._total_tokens if self._total_tokens > 0 else 0,
                "by_role": role_counts,
            })

        return histogram

    def __repr__(self) -> str:
        return f"HistoryQuery(entries={len(self._entries)}, tokens={self._total_tokens})"
