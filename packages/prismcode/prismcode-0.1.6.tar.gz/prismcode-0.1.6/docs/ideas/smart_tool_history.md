# Smart Tool History Strategy

## Problem

Current approach (`keep_recent_tool_results(30)`) is too aggressive:
- Drops 95% of tool output (71k tokens)
- Loses file contents from earlier reads
- No compression - infois just **dropped**
- Not using the full context budget

## Proposed Strategy: Intelligent Tool Result Retention

### Core Principles

1. **Keep what matters** - Edit diffs are always important
2. **Dedupe intelligently** - Multiple reads of same file → keep first + last
3. **Preserve context** - Know when and why files were accessed
4. **Add intent** - Let LLM annotate diffs with reasoning

---

## 1. Read File Strategy: First + Last + Sampled

When the same file is read multiple times:

```
Read #1: config.py (full content)     ← KEEP (first state)
Read #2: config.py (full content)     ← POINTER: "Re-read config.py"
Read #3: config.py (full content)     ← POINTER: "Re-read config.py"  
Read #4: config.py (full content)     ← SAMPLE (if >5 reads, keep middle sample)
Read #5: config.py (full content)     ← POINTER: "Re-read config.py"
Read #6: config.py (full content)     ← KEEP (most recent state)
```

### Rules

| Reads of Same File | What to Keep |
|--------------------|--------------|
| 1 | Full content |
| 2 | Both (first + last) |
| 3-5 | First + last, pointers for middle |
| 6+ | First + last + up to 3 sampled midpoints, pointers for rest |

### Pointer Format

```json
{
  "role": "tool",
  "tool_call_id": "xyz",
  "content": "[Re-read of config.py - see first read above for content]"
}
```

This preserves:
- ✅ Initial file state (what we started with)
- ✅ Current file state (what it looks like now)
- ✅ Timeline of when file was accessed
- ✅ Major checkpoints if heavily accessed

---

## 2. Edit File Strategy: Always Keep + Intent Annotation

Diffs are **always kept** because they represent actual work done.

### Add Intent Field to edit_file Tool

```python
def edit_file(
    file_path: str,
    old_str: str,
    new_str: str,
    intent: str = ""  # NEW: Optional intent annotation
) -> str:
    """
    Args:
        file_path: Path to the file to edit
        old_str: The exact text to find and replace
        new_str: The replacement text
        intent: Brief description of why this change is being made
    """
```

### How It Appears in History

```json
{
  "role": "assistant",
  "tool_calls": [{
    "function": {
      "name": "edit_file",
      "arguments": {
        "file_path": "core/agent.py",
        "old_str": "keep_recent_tool_results(30)",
        "new_str": "keep_recent_tool_results(50)",
        "intent": "Increase tool result retention for better context"
      }
    }
  }]
}
```

### Benefits

- Makes history self-documenting
- Easier to understand what happened when reviewing
- Helps summarization - intent can be preserved even when diff is compressed
- Future: Could use intents to generate changelogs

---

## 3. Bash Output Strategy: Truncate + Summarize

Bash outputs can be huge but often repetitive (test output, logs, etc.)

### Rules

| Output Size | Strategy |
|-------------|----------|
| < 1k chars | Keep full |
| 1k - 10k chars | Keep, mark for potential truncation |
| > 10k chars | Keep first 2k + last 2k + summary line |

### Truncated Format

```
$ npm test

[First 2000 chars of output...]

... [truncated: 45,231 chars total, 342 lines] ...

[Last 2000 chars of output...]
```

---

## 4. Implementation: `smart_tool_retention()` Projection

```python
def smart_tool_retention(
    max_file_reads: int = 5,      # Max full reads per file
    keep_all_edits: bool = True,  # Always keep edit diffs
    bash_truncate: int = 10000,   # Truncate bash over this
) -> Callable[[List[Entry]], List[Entry]]:
    """
    Smart tool result retention that preserves context while reducing tokens.
    
    - read_file: Keep first + last + sampled midpoints per file
    - edit_file: Always keep (with intent if provided)
    - bash: Truncate long outputs, keep head + tail
    - focus/unfocus/ls: Keep recent only (lightweight)
    """
    def proj(entries: List[Entry]) -> List[Entry]:
        # Group reads by file
        reads_by_file: Dict[str, List[Entry]] = {}
        
        result = []
        for e in entries:
            if e.role != "tool":
                result.append(e)
                continue
            
            tool = e.tool_name
            
            if tool == "read_file":
                # Track reads per file
                path = e.file_path
                if path not in reads_by_file:
                    reads_by_file[path] = []
                reads_by_file[path].append(e)
                # Will process at end
                
            elif tool == "edit_file":
                # Always keep edits
                result.append(e)
                
            elif tool == "bash":
                # Truncate if needed
                result.append(truncate_bash(e, bash_truncate))
                
            else:
                # Keep other tools as-is
                result.append(e)
        
        # Process file reads - keep first + last + samples
        for path, reads in reads_by_file.items():
            to_keep = select_reads_to_keep(reads, max_file_reads)
            for read in reads:
                if read in to_keep:
                    result.append(read)
                else:
                    result.append(make_pointer(read, path))
        
        return result
    
    return proj


def select_reads_to_keep(reads: List[Entry], max_reads: int) -> Set[Entry]:
    """Select which reads to keep full content for."""
    if len(reads) <= 2:
        return set(reads)
    
    # Always keep first and last
    keep = {reads[0], reads[-1]}
    
    # Sample from middle if needed
    middle = reads[1:-1]
    if len(middle) <= max_reads - 2:
        keep.update(middle)
    else:
        # Evenly sample from middle
        step = len(middle) / (max_reads - 2)
        for i in range(max_reads - 2):
            idx = int(i * step)
            keep.add(middle[idx])
    
    return keep


def make_pointer(entry: Entry, path: str) -> Entry:
    """Create a pointer entry instead of full content."""
    return Entry(
        id=entry.id,
        timestamp=entry.timestamp,
        message={
            "role": "tool",
            "tool_call_id": entry.tool_call_id,
            "content": f"[Re-read of {path} - see earlier read for content]"
        },
        meta={**entry.meta, "is_pointer": True}
    )
```

---

## 5. Token Budget Comparison

### Current Strategy
```
Full history:     ~142k tokens
After projection:  ~20k tokens (86% dropped)
Lost info:        All old file reads, most bash output
```

### Proposed Strategy (Estimated)
```
Full history:     ~142k tokens
After projection:  ~60-80k tokens (50% reduction)
Preserved:        First+last reads, all edits, bash summaries
```

### With Consolidation (Future)
```
Budget:           140k tokens (70% of 200k)
Working history:  ~60-80k tokens (smart retention)
Headroom:         60-80k for new content before summarization needed
```

---

## 6. Future Enhancements

### 6.1 Edit Intent → Changelog Generation
```python
# Auto-generate from edit intents
changelog = generate_changelog(session)
# Output:
# - core/agent.py: Increased tool retention for better context
# - config.py: Added new model configuration
# - tools/tools.py: Fixed bash timeout handling
```

### 6.2 File State Timeline
```python
# Query file state at any point
content = history.file_state_at("config.py", turn=50)
```

### 6.3 Smart Diff Compression
For very long sessions, even diffs could be compressed:
```
[Edits to config.py: 12 changes between turns 10-50]
- Added AGENT_CONFIG
- Modified system prompt 3x
- Added tool definitions
[Full diff available in ground truth]
```

---

## Summary

| Tool | Current | Proposed |
|------|---------|----------|
| read_file | Drop all but most recent | Keep first + last + samples |
| edit_file | Keep if in last 30 | **Always keep** + intent field |
| bash | Drop if old | Truncate long output (head+tail) |
| focus/ls/etc | Keep if in last 30 | Keep recent only |

**Result**: ~50% token reduction (vs 86%) but preserves actual history coherence.
