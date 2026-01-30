"""
Ground truth history storage with projection support.

Two layers:
1. GroundTruth - append-only, full fidelity, never modified (except appending)
2. WorkingHistory - what the LLM sees, can be compacted via gists over time

Both are persisted. Ground truth is the source of truth for RAG/search.
Working history evolves with gists (compressed summaries).
"""
import json
import re
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .query import HistoryQuery
    from .tokens import TokenCounter


def _sanitize_tool_call_id(tc_id: str) -> str:
    """
    Sanitize malformed tool call IDs from Gemini.

    Gemini sometimes embeds its internal "thinking" into tool call IDs like:
        call_abc123__thought__<huge base64 blob>

    This truncates to just the valid prefix before __thought__.
    """
    if not tc_id:
        return f"call_{uuid.uuid4().hex[:12]}"
    if "__thought__" in tc_id:
        return tc_id.split("__thought__")[0]
    # Also handle excessively long IDs (limit to 100 chars)
    if len(tc_id) > 100:
        return tc_id[:100]
    return tc_id


def _sanitize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize a message for cross-provider compatibility.

    Fixes:
    - None content in assistant messages -> empty string
    - None arguments in tool calls -> empty object "{}"
    """
    if msg.get("role") == "assistant":
        # Some providers don't like None content
        if msg.get("content") is None:
            msg = {**msg, "content": ""}

        # Sanitize tool calls
        if msg.get("tool_calls"):
            sanitized_calls = []
            for tc in msg["tool_calls"]:
                if tc is None:
                    continue
                func = tc.get("function", {})
                if func is None:
                    continue
                # Ensure arguments is a string, not None
                args = func.get("arguments")
                if args is None:
                    func = {**func, "arguments": "{}"}
                    tc = {**tc, "function": func}
                sanitized_calls.append(tc)
            msg = {**msg, "tool_calls": sanitized_calls}

    return msg


def _sanitize_malformed_entries(entries: List["Entry"]) -> List["Entry"]:
    """
    Fix malformed tool calls from misbehaving models (especially Gemini).

    Issues handled:
    1. Concatenated JSON in arguments: '{"a":1}{"b":2}' -> split into separate calls
    2. Thinking tokens in tool call IDs: 'call_xxx__thought__<base64>' -> truncate

    This function works at the ENTRIES level (not message level) because
    when we split one tool call into N, we also need to duplicate the
    corresponding tool result N times to satisfy Gemini's requirement
    that function call count == function response count.

    Returns a new list of entries with fixes applied.
    """
    result = []
    i = 0

    while i < len(entries):
        entry = entries[i]

        # Only process assistant messages with tool_calls
        if entry.role != "assistant" or not entry.tool_calls:
            # For tool results, sanitize the tool_call_id
            if entry.role == "tool" and entry.tool_call_id:
                sanitized_id = _sanitize_tool_call_id(entry.tool_call_id)
                if sanitized_id != entry.tool_call_id:
                    new_msg = {**entry.message, "tool_call_id": sanitized_id}
                    result.append(Entry(entry.id, entry.timestamp, new_msg, entry.meta))
                else:
                    result.append(entry)
            else:
                result.append(entry)
            i += 1
            continue

        # Check if any tool calls need fixing (malformed args OR malformed IDs)
        needs_fix = False
        for tc in entry.tool_calls:
            tc_id = tc.get("id", "")
            # Check for malformed ID
            if "__thought__" in tc_id or len(tc_id) > 100:
                needs_fix = True
                break
            # Check for malformed args
            args_str = tc.get("function", {}).get("arguments", "")
            if args_str:
                try:
                    json.loads(args_str)
                except json.JSONDecodeError as e:
                    if "Extra data" in str(e):
                        needs_fix = True
                        break

        if not needs_fix:
            result.append(entry)
            i += 1
            continue

        # Build mapping: original_id -> list of (new_id, args)
        id_mapping = {}  # original_id -> [(new_id, args_str), ...]
        sanitized_calls = []

        for tc in entry.tool_calls:
            func = tc.get("function", {})
            args_str = func.get("arguments", "")
            original_id = tc.get("id", str(uuid.uuid4()))
            sanitized_base_id = _sanitize_tool_call_id(original_id)
            func_name = func.get("name", "unknown")

            if not args_str:
                new_call = {**tc, "id": sanitized_base_id}
                sanitized_calls.append(new_call)
                id_mapping[original_id] = [(sanitized_base_id, args_str)]
                continue

            # Try to parse
            try:
                json.loads(args_str)
                new_call = {**tc, "id": sanitized_base_id}
                sanitized_calls.append(new_call)
                id_mapping[original_id] = [(sanitized_base_id, args_str)]
                continue
            except json.JSONDecodeError as e:
                if "Extra data" not in str(e):
                    new_call = {**tc, "id": sanitized_base_id}
                    sanitized_calls.append(new_call)
                    id_mapping[original_id] = [(sanitized_base_id, args_str)]
                    continue

            # Split concatenated JSON
            json_objects = re.findall(r'\{[^{}]*\}', args_str)
            if not json_objects:
                parts = args_str.replace("}{", "}\n{").split("\n")
                json_objects = [p for p in parts if p.strip()]

            id_mapping[original_id] = []
            for j, obj_str in enumerate(json_objects):
                try:
                    json.loads(obj_str)
                    new_id = f"{sanitized_base_id}_{j}" if j > 0 else sanitized_base_id
                    new_call = {
                        "id": new_id,
                        "type": "function",
                        "function": {
                            "name": func_name,
                            "arguments": obj_str
                        }
                    }
                    sanitized_calls.append(new_call)
                    id_mapping[original_id].append((new_id, obj_str))
                except json.JSONDecodeError:
                    continue

            # If nothing was extracted, keep with sanitized ID
            if not id_mapping[original_id]:
                new_call = {**tc, "id": sanitized_base_id}
                sanitized_calls.append(new_call)
                id_mapping[original_id] = [(sanitized_base_id, args_str)]

        # Create fixed assistant entry
        fixed_msg = {**entry.message, "tool_calls": sanitized_calls}
        fixed_entry = Entry(
            id=entry.id,
            timestamp=entry.timestamp,
            message=fixed_msg,
            meta={**entry.meta, "sanitized": True}
        )
        result.append(fixed_entry)
        i += 1

        # Now handle tool results - duplicate them for split calls
        while i < len(entries) and entries[i].role == "tool":
            tool_entry = entries[i]
            original_tid = tool_entry.tool_call_id

            if original_tid in id_mapping:
                mappings = id_mapping[original_tid]
                for new_id, _ in mappings:
                    new_msg = {**tool_entry.message, "tool_call_id": new_id}
                    new_entry = Entry(
                        id=f"{tool_entry.id}_{new_id}" if new_id != original_tid else tool_entry.id,
                        timestamp=tool_entry.timestamp,
                        message=new_msg,
                        meta={**tool_entry.meta, "duplicated_for": new_id if new_id != original_tid else None}
                    )
                    result.append(new_entry)
            else:
                # No mapping, keep as-is
                result.append(tool_entry)

            i += 1

    return result


@dataclass
class Entry:
    """
    Single message in history. Wraps raw LiteLLM message + metadata.
    """
    id: str
    timestamp: str
    message: Dict[str, Any]  # Raw LiteLLM format
    meta: Dict[str, Any] = field(default_factory=dict)

    # --- Convenience accessors ---
    @property
    def role(self) -> str:
        return self.message.get("role", "")

    @property
    def content(self) -> Optional[str]:
        return self.message.get("content")

    @property
    def tool_calls(self) -> Optional[List[Dict]]:
        return self.message.get("tool_calls")

    @property
    def tool_call_id(self) -> Optional[str]:
        return self.message.get("tool_call_id")

    @property
    def tool_name(self) -> Optional[str]:
        return self.meta.get("tool_name")

    @property
    def file_path(self) -> Optional[str]:
        return self.meta.get("file_path")

    @property
    def is_gist(self) -> bool:
        """Check if this entry is a gist (compressed summary)."""
        return self.meta.get("is_gist", False) or self.meta.get("is_summary", False)

    @property
    def is_summary(self) -> bool:
        """Deprecated: Use is_gist instead."""
        return self.is_gist

    @property
    def token_estimate(self) -> int:
        """Rough token estimate (chars / 4)."""
        return self.meta.get("tokens") or len(str(self.message)) // 4

    # --- Serialization ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "message": self.message,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entry":
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            message=data["message"],
            meta=data.get("meta", {}),
        )


class GroundTruth:
    """
    Append-only ground truth storage.
    Never modified except by appending. Used for RAG/search later.
    """

    def __init__(self):
        self.entries: List[Entry] = []
        # Indices for fast lookup
        self._by_id: Dict[str, Entry] = {}
        self._by_file: Dict[str, List[str]] = {}  # file_path -> [entry_ids]
        self._by_tool: Dict[str, List[str]] = {}  # tool_name -> [entry_ids]

    def add(self, message: Dict[str, Any], **meta) -> Entry:
        """Add a message to ground truth. Returns the created entry."""
        entry = Entry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            message=message,
            meta=meta,
        )
        self.entries.append(entry)
        self._index_entry(entry)
        return entry

    def _index_entry(self, entry: Entry):
        """Update indices for fast lookup."""
        self._by_id[entry.id] = entry

        if entry.file_path:
            self._by_file.setdefault(entry.file_path, []).append(entry.id)

        if entry.tool_name:
            self._by_tool.setdefault(entry.tool_name, []).append(entry.id)

    def _rebuild_indices(self):
        """Rebuild all indices from entries."""
        self._by_id.clear()
        self._by_file.clear()
        self._by_tool.clear()
        for entry in self.entries:
            self._index_entry(entry)

    # --- Queries ---
    def get(self, entry_id: str) -> Optional[Entry]:
        return self._by_id.get(entry_id)

    def file_reads(self, path: str) -> List[Entry]:
        """Get all entries that read a specific file."""
        ids = self._by_file.get(path, [])
        return [self._by_id[i] for i in ids if i in self._by_id]

    def tool_calls(self, name: str) -> List[Entry]:
        """Get all entries for a specific tool."""
        ids = self._by_tool.get(name, [])
        return [self._by_id[i] for i in ids if i in self._by_id]

    def by_role(self, role: str) -> List[Entry]:
        """Get all entries with a specific role."""
        return [e for e in self.entries if e.role == role]

    def tool_results(self) -> List[Entry]:
        """Get all tool result entries."""
        return [e for e in self.entries if e.role == "tool"]

    def range(self, start: int, end: int = None) -> List[Entry]:
        """Get entries by index range."""
        return self.entries[start:end]

    # --- Serialization ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GroundTruth":
        gt = cls()
        gt.entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        gt._rebuild_indices()
        return gt

    def to_messages(self) -> List[Dict[str, Any]]:
        """Export as raw LiteLLM messages (full fidelity)."""
        return [e.message for e in self.entries]

    def __len__(self) -> int:
        return len(self.entries)


class WorkingHistory:
    """
    The history the LLM actually sees. Can include gists.
    Persisted separately from ground truth.

    Entries here may be:
    - Direct references to ground truth entries
    - Gist entries (is_gist=True in meta)
    """

    def __init__(self):
        self.entries: List[Entry] = []

    def append(self, entry: Entry):
        """Add an entry to working history."""
        self.entries.append(entry)

    def append_from_ground_truth(self, gt_entry: Entry):
        """Add a ground truth entry to working history."""
        # We copy rather than reference so working history can evolve independently
        self.entries.append(Entry(
            id=gt_entry.id,
            timestamp=gt_entry.timestamp,
            message=gt_entry.message.copy(),
            meta={**gt_entry.meta, "gt_id": gt_entry.id},
        ))

    def add_gist(self, gist_text: str, covers_ids: List[str],
                 gist_of_gists: bool = False) -> Entry:
        """
        Add a gist entry that replaces earlier content.

        Args:
            gist_text: The gist content
            covers_ids: IDs of entries this gist replaces
            gist_of_gists: True if this summarizes previous gists
        """
        entry = Entry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            message={"role": "user", "content": f"[Conversation gist]\n{gist_text}"},
            meta={
                "is_gist": True,
                "gist_covers_ids": covers_ids,
                "gist_covers_count": len(covers_ids),
                "gist_of_gists": gist_of_gists,
            },
        )
        self.entries.append(entry)
        return entry

    def add_summary(self, summary_text: str, covers_ids: List[str],
                    summary_of_summaries: bool = False) -> Entry:
        """Deprecated: Use add_gist instead."""
        return self.add_gist(summary_text, covers_ids, summary_of_summaries)

    def replace_range_with_gist(self, start: int, end: int, gist_text: str) -> Entry:
        """
        Replace entries[start:end] with a gist.
        Returns the new gist entry.
        """
        to_gist = self.entries[start:end]
        covers_ids = [e.id for e in to_gist]

        # Check if we're creating a gist of gists
        gist_of_gists = any(e.is_gist for e in to_gist)

        gist_entry = Entry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            message={"role": "user", "content": f"[Conversation gist]\n{gist_text}"},
            meta={
                "is_gist": True,
                "gist_covers_ids": covers_ids,
                "gist_covers_count": len(covers_ids),
                "gist_of_gists": gist_of_gists,
            },
        )

        # Replace the range with the gist
        self.entries = self.entries[:start] + [gist_entry] + self.entries[end:]
        return gist_entry

    def replace_range_with_summary(self, start: int, end: int, summary_text: str) -> Entry:
        """Deprecated: Use replace_range_with_gist instead."""
        return self.replace_range_with_gist(start, end, summary_text)

    def to_messages(self) -> List[Dict[str, Any]]:
        """Export as LiteLLM messages."""
        return [e.message for e in self.entries]

    # --- Serialization ---
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingHistory":
        wh = cls()
        wh.entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        return wh

    def __len__(self) -> int:
        return len(self.entries)


# =============================================================================
# Projection utilities (for filtering working history before sending to LLM)
# =============================================================================

def filter_tool_results(entries: List[Entry], keep: Callable[[Entry], bool]) -> List[Entry]:
    """
    Filter tool results by predicate.
    Automatically removes orphaned tool_calls from assistant messages.

    This is the core utility that handles the tricky tool_call/result pairing.
    """
    # Which tool_call_ids survive?
    keep_ids = {e.tool_call_id for e in entries if e.role == "tool" and keep(e)}

    result = []
    for e in entries:
        if e.role == "tool":
            if e.tool_call_id in keep_ids:
                result.append(e)
        elif e.role == "assistant" and e.tool_calls:
            # Filter tool_calls to match surviving results
            new_calls = [tc for tc in e.tool_calls if tc["id"] in keep_ids]
            if new_calls:
                new_msg = {**e.message, "tool_calls": new_calls}
                result.append(Entry(e.id, e.timestamp, new_msg, e.meta))
            else:
                # All tool calls filtered - keep as text-only or minimal message
                # IMPORTANT: Never drop assistant messages entirely, as it breaks message alternation
                content = e.content or ""
                new_msg = {"role": "assistant", "content": content}
                result.append(Entry(e.id, e.timestamp, new_msg, e.meta))
        else:
            result.append(e)

    return result


def keep_recent_tool_results(n: int) -> Callable[[List[Entry]], List[Entry]]:
    """Projection: Keep only the N most recent tool results."""
    def proj(entries: List[Entry]) -> List[Entry]:
        tool_entries = [e for e in entries if e.role == "tool"]
        if not tool_entries:
            return entries
        recent_ids = {e.tool_call_id for e in tool_entries[-n:]}
        return filter_tool_results(entries, lambda e: e.tool_call_id in recent_ids)
    return proj


def dedupe_file_reads() -> Callable[[List[Entry]], List[Entry]]:
    """Projection: Keep only the most recent read of each file."""
    def proj(entries: List[Entry]) -> List[Entry]:
        # Find most recent read per file
        latest_by_file = {}
        for e in entries:
            if e.role == "tool" and e.tool_name == "read_file" and e.file_path:
                latest_by_file[e.file_path] = e.tool_call_id

        keep_ids = set(latest_by_file.values())

        # Also keep all non-read_file tool results
        for e in entries:
            if e.role == "tool" and e.tool_name != "read_file":
                keep_ids.add(e.tool_call_id)

        return filter_tool_results(entries, lambda e: e.tool_call_id in keep_ids)
    return proj


def hide_tool_args(*tool_names: str, max_length: int = 200) -> Callable[[List[Entry]], List[Entry]]:
    """Projection: Truncate long tool arguments for specified tools."""
    def proj(entries: List[Entry]) -> List[Entry]:
        result = []
        for e in entries:
            if e.role == "assistant" and e.tool_calls:
                new_calls = []
                for tc in e.tool_calls:
                    if tc["function"]["name"] in tool_names:
                        args = tc["function"]["arguments"]
                        if len(args) > max_length:
                            args = args[:max_length] + "..."
                        new_calls.append({
                            **tc,
                            "function": {**tc["function"], "arguments": args}
                        })
                    else:
                        new_calls.append(tc)
                new_msg = {**e.message, "tool_calls": new_calls}
                result.append(Entry(e.id, e.timestamp, new_msg, e.meta))
            else:
                result.append(e)
        return result
    return proj


def truncate_tool_results(max_length: int = 5000) -> Callable[[List[Entry]], List[Entry]]:
    """Projection: Truncate long tool results."""
    def proj(entries: List[Entry]) -> List[Entry]:
        result = []
        for e in entries:
            if e.role == "tool" and e.content and len(e.content) > max_length:
                truncated = e.content[:max_length] + f"\n... [truncated, {len(e.content)} chars total]"
                new_msg = {**e.message, "content": truncated}
                result.append(Entry(e.id, e.timestamp, new_msg, e.meta))
            else:
                result.append(e)
        return result
    return proj


def compose(*projections: Callable) -> Callable[[List[Entry]], List[Entry]]:
    """Chain projections: compose(a, b, c)(entries) = c(b(a(entries)))"""
    def combined(entries: List[Entry]) -> List[Entry]:
        for p in projections:
            entries = p(entries)
        return entries
    return combined


def smart_tool_retention(
    max_file_reads: int = 5,
    keep_all_edits: bool = True,
    bash_truncate: int = 10000,
) -> Callable[[List[Entry]], List[Entry]]:
    """
    Smart tool result retention that preserves context while reducing tokens.
    
    - read_file: Keep first + last + sampled midpoints per file
    - edit_file: Always keep (never drop)
    - bash: Truncate long outputs (keep head + tail)
    - others: Keep as-is
    
    Args:
        max_file_reads: Max full reads to keep per file (default 5)
        keep_all_edits: Always keep edit_file results (default True)
        bash_truncate: Truncate bash output over this length (default 10000)
    """
    
    def _truncate_bash_content(content: str, max_len: int) -> str:
        """Truncate bash output keeping head and tail."""
        if len(content) <= max_len:
            return content
        half = max_len // 2
        head = content[:half]
        tail = content[-half:]
        return f"{head}\n\n... [truncated: {len(content):,} chars total] ...\n\n{tail}"
    
    def _select_reads_to_keep(reads: List[Entry], max_reads: int) -> set:
        """Select which reads to keep full content for."""
        if len(reads) <= 2:
            return set(range(len(reads)))
        
        # Always keep first and last
        keep_indices = {0, len(reads) - 1}
        
        # Sample from middle if needed
        middle_count = max_reads - 2
        if middle_count > 0 and len(reads) > 2:
            middle_indices = list(range(1, len(reads) - 1))
            if len(middle_indices) <= middle_count:
                keep_indices.update(middle_indices)
            else:
                # Evenly sample from middle
                step = len(middle_indices) / middle_count
                for i in range(middle_count):
                    idx = middle_indices[int(i * step)]
                    keep_indices.add(idx)
        
        return keep_indices
    
    def _make_pointer(entry: Entry, path: str) -> Entry:
        """Create a pointer entry instead of full content."""
        filename = path.split('/')[-1] if '/' in path else path
        return Entry(
            id=entry.id,
            timestamp=entry.timestamp,
            message={
                "role": "tool",
                "tool_call_id": entry.tool_call_id,
                "content": f"[Re-read of {filename} - see earlier read for content]"
            },
            meta={**entry.meta, "is_pointer": True}
        )
    
    def proj(entries: List[Entry]) -> List[Entry]:
        # First pass: collect read_file entries by file path
        reads_by_file: dict = {}  # file_path -> [(index, entry), ...]
        
        for i, e in enumerate(entries):
            if e.role == "tool" and e.tool_name == "read_file" and e.file_path:
                if e.file_path not in reads_by_file:
                    reads_by_file[e.file_path] = []
                reads_by_file[e.file_path].append((i, e))
        
        # Determine which read indices to keep full content
        keep_full_read_indices: set = set()
        for path, reads in reads_by_file.items():
            indices_to_keep = _select_reads_to_keep(reads, max_file_reads)
            for local_idx in indices_to_keep:
                global_idx = reads[local_idx][0]
                keep_full_read_indices.add(global_idx)
        
        # Second pass: build result
        result = []
        for i, e in enumerate(entries):
            if e.role != "tool":
                result.append(e)
                continue
            
            tool = e.tool_name
            
            if tool == "read_file" and e.file_path:
                if i in keep_full_read_indices:
                    result.append(e)
                else:
                    result.append(_make_pointer(e, e.file_path))
            
            elif tool == "edit_file":
                # Always keep edits
                result.append(e)
            
            elif tool == "bash":
                # Truncate long output
                content = e.content or ""
                if len(content) > bash_truncate:
                    truncated = _truncate_bash_content(content, bash_truncate)
                    new_msg = {**e.message, "content": truncated}
                    result.append(Entry(e.id, e.timestamp, new_msg, {**e.meta, "truncated": True}))
                else:
                    result.append(e)
            
            else:
                # Keep other tools as-is
                result.append(e)
        
        return result
    
    return proj


# =============================================================================
# Main interface
# =============================================================================

class HistoryManager:
    """
    Main interface for history management.

    Manages both ground truth (append-only) and working history (can be compacted).
    """

    def __init__(self, storage_path: Path = None, counter: "TokenCounter" = None):
        self.ground_truth = GroundTruth()
        self.working = WorkingHistory()
        self.storage_path = storage_path
        self.projection: Callable = None  # Default projection for get_context()
        self._counter = counter  # Lazy-loaded if not provided
        self.metadata: Dict[str, Any] = {}  # Session metadata (title, model, etc.)

    # -------------------------------------------------------------------------
    # Adding messages (to both ground truth and working history)
    # -------------------------------------------------------------------------

    def add_user(self, content: str, **meta) -> Entry:
        """Add a user message."""
        entry = self.ground_truth.add({"role": "user", "content": content}, **meta)
        self.working.append_from_ground_truth(entry)
        self._auto_save()
        return entry

    def add_assistant(self, content: str = None, tool_calls: List[Dict] = None, **meta) -> Entry:
        """Add an assistant message (with optional tool calls)."""
        msg = {"role": "assistant"}
        if content:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
            msg.setdefault("content", None)

        entry = self.ground_truth.add(msg, **meta)
        self.working.append_from_ground_truth(entry)
        self._auto_save()
        return entry

    def add_tool_result(self, tool_call_id: str, content: str,
                        tool_name: str = None, file_path: str = None, **meta) -> Entry:
        """Add a tool result."""
        msg = {"role": "tool", "tool_call_id": tool_call_id, "content": content}

        # Add tool metadata
        if tool_name:
            meta["tool_name"] = tool_name
        if file_path:
            meta["file_path"] = file_path

        entry = self.ground_truth.add(msg, **meta)
        self.working.append_from_ground_truth(entry)
        self._auto_save()
        return entry

    # -------------------------------------------------------------------------
    # Getting context (what the LLM sees)
    # -------------------------------------------------------------------------

    def get_context(self, projection: Callable = None) -> List[Dict[str, Any]]:
        """
        Get LiteLLM-compatible messages from working history.
        Applies projection if provided (or default projection).
        Sanitizes malformed tool calls before returning.
        """
        entries = self.working.entries
        p = projection or self.projection
        if p:
            entries = p(entries)
        # Sanitize malformed tool calls (splits concatenated JSON + duplicates results)
        entries = _sanitize_malformed_entries(entries)
        # Apply per-message sanitization (None -> empty string, etc.)
        return [_sanitize_message(e.message) for e in entries]

    def get_working_entries(self, projection: Callable = None) -> List[Entry]:
        """Get working history entries (with optional projection)."""
        entries = self.working.entries
        p = projection or self.projection
        if p:
            entries = p(entries)
        return entries

    # -------------------------------------------------------------------------
    # Query interface (for flexible slicing and selection)
    # -------------------------------------------------------------------------

    def query(self, source: str = "working") -> "HistoryQuery":
        """
        Get a query interface for history.

        Provides flexible selection by percentage, token budget, index,
        and filtering predicates. Returns HistorySlice objects with metadata.

        Args:
            source: "working" or "ground_truth"

        Example:
            # Get first 20% of tokens
            slice = history.query().first_percent(0.2)
            print(f"Got {slice.token_count} tokens")

            # Get last 50k tokens
            slice = history.query().last_n_tokens(50_000)
        """
        from .query import HistoryQuery
        from .tokens import CharCounter

        entries = self.working.entries if source == "working" else self.ground_truth.entries
        counter = self._counter or CharCounter()
        return HistoryQuery(entries, counter)

    # -------------------------------------------------------------------------
    # Queries (on ground truth)
    # -------------------------------------------------------------------------

    def file_reads(self, path: str) -> List[Entry]:
        """Get all ground truth entries that read a specific file."""
        return self.ground_truth.file_reads(path)

    def tool_calls(self, name: str) -> List[Entry]:
        """Get all ground truth entries for a specific tool."""
        return self.ground_truth.tool_calls(name)

    def search_ground_truth(self, query: str) -> List[Entry]:
        """
        Simple text search over ground truth.
        (Placeholder for future RAG integration)
        """
        query_lower = query.lower()
        results = []
        for entry in self.ground_truth.entries:
            content = str(entry.message).lower()
            if query_lower in content:
                results.append(entry)
        return results

    # -------------------------------------------------------------------------
    # Token estimation
    # -------------------------------------------------------------------------

    def estimate_tokens(self, entries: List[Entry] = None) -> int:
        """Estimate token count for entries (defaults to working history)."""
        if entries is None:
            entries = self.working.entries
        return sum(e.token_estimate for e in entries)

    def ground_truth_tokens(self) -> int:
        """Estimate tokens in ground truth."""
        return sum(e.token_estimate for e in self.ground_truth.entries)

    def working_tokens(self) -> int:
        """Estimate tokens in working history."""
        return sum(e.token_estimate for e in self.working.entries)

    # -------------------------------------------------------------------------
    # Persistence
    # -------------------------------------------------------------------------

    def _auto_save(self):
        """Auto-save if storage path is set."""
        if self.storage_path:
            self.save(self.storage_path)

    def save(self, path: Path):
        """Save both ground truth and working history."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": self.metadata,
            "ground_truth": self.ground_truth.to_dict(),
            "working": self.working.to_dict(),
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "HistoryManager":
        """Load from file."""
        path = Path(path)
        if not path.exists():
            return cls(storage_path=path)

        data = json.loads(path.read_text())
        manager = cls(storage_path=path)
        manager.metadata = data.get("metadata", {})
        manager.ground_truth = GroundTruth.from_dict(data.get("ground_truth", {}))
        manager.working = WorkingHistory.from_dict(data.get("working", {}))
        return manager

    # -------------------------------------------------------------------------
    # Stats
    # -------------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Get statistics about the history."""
        return {
            "ground_truth_entries": len(self.ground_truth),
            "ground_truth_tokens": self.ground_truth_tokens(),
            "working_entries": len(self.working),
            "working_tokens": self.working_tokens(),
            "gists": sum(1 for e in self.working.entries if e.is_gist),
            "files_read": list(self.ground_truth._by_file.keys()),
            "tools_used": list(self.ground_truth._by_tool.keys()),
        }

    def __repr__(self) -> str:
        return f"HistoryManager(gt={len(self.ground_truth)}, working={len(self.working)})"
