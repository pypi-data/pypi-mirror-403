# Memory Blobs: Structured, Inspectable Agent Memory

## The Core Insight

The agent's memory should be **inspectable, structured, and goal-oriented** - not just a blob of text. The user (or the agent itself) should be able to look at the agent's "brain" and see exactly what it knows, what it's trying to do, and what it's learned.

This design is **universal** - it works for coding, legal analysis, games, research, mystery-solving, or any long-running task.

---

## The Four Boxes

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENT MEMORY                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📎 CONTEXT          What environment am I in?              │
│     - Project/domain facts                                  │
│     - Key entities, names, relationships                    │
│     - Tools/resources available                             │
│                                                             │
│  🎯 GOALS            What am I trying to do?                │
│     - Primary objective (the big thing)                     │
│     - Active tasks (current focus)                          │
│     - Blocked/waiting (paused, needs something)             │
│                                                             │
│  💡 LEARNINGS        What have I figured out?               │
│     - Insights (aha moments, connections)                   │
│     - Warnings (mistakes, dead ends, things to avoid)       │
│     - Open questions (unknowns, things to investigate)      │
│                                                             │
│  👤 PREFERENCES      How should I behave?                   │
│     - User preferences (style, tools, approach)             │
│     - Constraints (rules, boundaries, must/must-not)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

Four boxes. That's it. Simple and universal.

---

## Why These Four?

### 1. CONTEXT - "Where am I?"

The **world model** - stable facts about the environment.

| Domain | Example Context |
|--------|-----------------|
| Coding | "Mobius is a Python TUI app using Textual and LiteLLM" |
| Legal | "Reviewing employment contract for wrongful termination case" |
| Game | "Playing chess as white, opponent favors Sicilian defense" |
| Mystery | "Investigating disappearance of John Smith, last seen Tuesday" |
| Research | "Analyzing climate data from 1950-2020, focus on Arctic" |

### 2. GOALS - "What am I doing?"

Three levels of goal tracking:

```
OBJECTIVE: The overarching mission (one)
  └─ ACTIVE: What I'm working on right now (few)
       └─ BLOCKED: Things I'm waiting on (if any)
```

| Domain | Objective | Active | Blocked |
|--------|-----------|--------|---------|
| Coding | Build context management | Implement persistent memory | - |
| Legal | Build wrongful termination case | Analyzing clause 7.2 | Waiting for performance reviews |
| Game | Win the game | Develop kingside attack | - |
| Mystery | Find what happened to John | Interview witness #3 | Can't access phone records |

### 3. LEARNINGS - "What have I figured out?"

Three types of knowledge:

```
INSIGHTS:   Things I've discovered (positive knowledge)
WARNINGS:   Mistakes, dead ends, things to avoid (negative knowledge)
QUESTIONS:  Things I still don't know (gaps in knowledge)
```

| Type | Coding Example | Legal Example | Mystery Example |
|------|----------------|---------------|-----------------|
| Insight | "Edit tool needs exact string match" | "Clause 7.2 contradicts employment law" | "2-hour gap in witness testimonies" |
| Warning | "Don't split tool calls from results" | "Don't cite Johnson v. Smith - overturned" | "Witness #2 has motive to lie" |
| Question | "How does pruning handle pinned items?" | "Was employee handbook ever signed?" | "Where was the car between 6-8pm?" |

### 4. PREFERENCES - "How should I act?"

- **User preferences**: "User prefers concise answers", "Always use Bun not Node"
- **Constraints**: "Never reveal confidential client info", "Must cite sources"

---

## Data Structure

```python
@dataclass
class MemoryItem:
    """A single item in agent memory."""
    id: str                    # Unique ID for programmatic reference
    content: str               # The actual fact/goal/insight
    importance: float          # 0.0 to 1.0 (relative to current objective)
    created_at: datetime
    last_referenced: datetime
    reference_count: int
    source_ids: List[str]      # Trace back to ground truth entries
    pinned: bool = False       # User pinned = never auto-prune

    def mark_referenced(self):
        self.last_referenced = datetime.now()
        self.reference_count += 1


@dataclass
class AgentMemory:
    """
    The agent's structured memory - four boxes.
    Inspectable, prunable, goal-oriented.
    """

    # CONTEXT - What environment am I in?
    context: List[MemoryItem] = field(default_factory=list)

    # GOALS - What am I trying to do?
    objective: Optional[str] = None        # The big mission (just one)
    active_tasks: List[MemoryItem] = field(default_factory=list)  # Current focus
    blocked: List[MemoryItem] = field(default_factory=list)       # Waiting on something

    # LEARNINGS - What have I figured out?
    insights: List[MemoryItem] = field(default_factory=list)
    warnings: List[MemoryItem] = field(default_factory=list)
    questions: List[MemoryItem] = field(default_factory=list)  # Open questions

    # PREFERENCES - How should I behave?
    preferences: List[MemoryItem] = field(default_factory=list)
    constraints: List[MemoryItem] = field(default_factory=list)

    # Thread safety
    _lock: threading.Lock = field(default_factory=threading.Lock)
```

---

## Structured Consolidation Output

The key innovation: **consolidation outputs structured JSON, not just a gist blob**.

When the consolidator compresses history, it outputs:

```json
{
  "gist": "Narrative of what happened in this segment...",

  "memory_updates": {
    "add": [
      {"box": "insights", "content": "Edit tool needs exact match", "importance": 0.8},
      {"box": "warnings", "content": "Don't split tool calls from results", "importance": 0.9},
      {"box": "context", "content": "Project uses three-layer architecture", "importance": 0.7}
    ],
    "update": [
      {"id": "task_3", "importance": 0.3}
    ],
    "remove": ["ctx_old_2"],
    "complete": ["task_1"],
    "block": {"id": "task_2", "reason": "Need user clarification on X"}
  },

  "objective_changed": false,
  "new_questions": ["How does the pruning system handle pinned items?"]
}
```

The consolidator doesn't just summarize - it **curates memory**.

### Consolidation Prompt

```python
CONSOLIDATION_PROMPT = '''
You are consolidating conversation history for an AI agent.

## CURRENT MEMORY STATE
{current_memory_json}

## CURRENT OBJECTIVE
{objective}

## CONVERSATION TO PROCESS
{conversation_slice}

---

Your job:
1. Write a gist (narrative summary) of what happened
2. Update the agent's memory based on what was learned

Output JSON:
{
  "gist": "Narrative summary...",

  "memory_updates": {
    "add": [
      {"box": "context|insights|warnings|questions|preferences|constraints|active_tasks",
       "content": "The fact/insight/task",
       "importance": 0.0-1.0}
    ],
    "update": [
      {"id": "existing_item_id", "importance": new_score}
    ],
    "remove": ["id1", "id2"],
    "complete": ["task_id1"],
    "block": {"id": "task_id", "reason": "Why blocked"}
  },

  "objective_changed": true/false,
  "new_objective": "Only if objective_changed is true",
  "new_questions": ["Questions that arose"]
}

Rules:
- importance is relative to current objective (0.0 = irrelevant, 1.0 = critical)
- Only add items that are valuable LONG-TERM
- Mark tasks complete when finished
- Remove items that are no longer relevant
- Be specific and actionable
'''
```

---

## Goal-Oriented Importance

**Key insight: importance is relative to the current objective.**

A fact important for one task might be irrelevant for another. When the objective changes, re-evaluate:

```python
def on_objective_change(self, new_objective: str):
    """Re-evaluate all memory importance relative to new goal."""
    old_objective = self.objective
    self.objective = new_objective

    prompt = f"""
The objective has changed.

Old objective: {old_objective}
New objective: {new_objective}

Re-evaluate importance (0.0-1.0) of all memory items based on relevance
to the NEW objective:

{self.to_json_with_ids()}

Return JSON: {{"item_id": new_importance, ...}}
"""

    new_scores = json.loads(self.llm(prompt))

    with self._lock:
        for item_id, score in new_scores.items():
            item = self.get_item(item_id)
            if item:
                item.importance = score
```

---

## Smart Pruning

When memory gets too big, the LLM decides what to forget:

```python
def prune_memory(self, target_tokens: int) -> PruningResult:
    """
    Intelligently prune memory to fit budget.
    Uses LLM to decide what's least relevant to current goal.
    """
    current_tokens = self.token_count()

    if current_tokens <= target_tokens:
        return PruningResult(pruned=False)

    prompt = f"""
Current objective: {self.objective}
Active tasks: {self.format_active_tasks()}

Memory items (with IDs and importance scores):
{self.to_json_with_ids()}

Current size: {current_tokens} tokens
Target size: {target_tokens} tokens
Need to free: {current_tokens - target_tokens} tokens

What should be pruned?

Rules:
- NEVER remove pinned items (marked with 📌)
- Prefer removing low-importance items first
- Prefer removing items unrelated to current objective
- Questions that have been answered can be removed
- Completed task learnings can be compressed
- Similar items can be merged

Return JSON:
{{
  "remove": ["id1", "id2"],
  "merge": [
    {{"ids": ["id3", "id4"], "merged": "Combined fact text", "importance": 0.7}}
  ],
  "adjust_importance": [
    {{"id": "id5", "new_importance": 0.3, "reason": "No longer relevant to objective"}}
  ]
}}
"""

    result = json.loads(self.llm(prompt))
    return self.apply_pruning(result)


def apply_pruning(self, pruning_result: dict) -> PruningResult:
    """Apply pruning decisions to memory."""
    removed = []
    merged = []
    adjusted = []

    with self._lock:
        # Remove items
        for item_id in pruning_result.get("remove", []):
            item = self.get_item(item_id)
            if item and not item.pinned:
                self.remove_item(item_id)
                removed.append(item_id)

        # Merge similar items
        for merge in pruning_result.get("merge", []):
            ids = merge["ids"]
            items = [self.get_item(i) for i in ids]
            items = [i for i in items if i and not i.pinned]

            if len(items) >= 2:
                # Remove old items
                for item in items:
                    self.remove_item(item.id)

                # Add merged item
                box = self.get_box_for_item(items[0])
                self.add_item(
                    box=box,
                    content=merge["merged"],
                    importance=merge.get("importance", 0.5),
                    source_ids=[i.id for i in items]
                )
                merged.append(ids)

        # Adjust importance scores
        for adj in pruning_result.get("adjust_importance", []):
            item = self.get_item(adj["id"])
            if item:
                item.importance = adj["new_importance"]
                adjusted.append(adj["id"])

    return PruningResult(
        pruned=True,
        removed=removed,
        merged=merged,
        adjusted=adjusted,
        tokens_freed=self._calculate_tokens_freed(removed, merged)
    )
```

---

## Rendering for Context Window

The memory renders as a floating header:

```python
def to_prompt_section(self, max_tokens: int = 2000) -> str:
    """Render memory as floating header for context window."""
    sections = []

    # Always show objective prominently
    if self.objective:
        sections.append(f"## 🎯 Objective\n{self.objective}")

    # Active tasks (sorted by importance)
    if self.active_tasks:
        lines = ["## 📋 Active Tasks"]
        for task in sorted(self.active_tasks, key=lambda t: -t.importance):
            pin = "📌 " if task.pinned else ""
            lines.append(f"- {pin}{task.content}")
        sections.append("\n".join(lines))

    # Blocked tasks (if any)
    if self.blocked:
        lines = ["## ⏸️ Blocked"]
        for item in self.blocked:
            lines.append(f"- {item.content}")
        sections.append("\n".join(lines))

    # Context - top N by importance
    if self.context:
        lines = ["## 📎 Context"]
        for item in sorted(self.context, key=lambda c: -c.importance)[:10]:
            pin = "📌 " if item.pinned else ""
            lines.append(f"- {pin}{item.content}")
        sections.append("\n".join(lines))

    # Key learnings - top insights and warnings
    top_insights = sorted(self.insights, key=lambda x: -x.importance)[:5]
    top_warnings = sorted(self.warnings, key=lambda x: -x.importance)[:3]

    if top_insights or top_warnings:
        lines = ["## 💡 Key Learnings"]
        for item in top_insights:
            pin = "📌 " if item.pinned else ""
            lines.append(f"- {pin}{item.content}")
        for item in top_warnings:
            pin = "📌 " if item.pinned else ""
            lines.append(f"- {pin}⚠️ {item.content}")
        sections.append("\n".join(lines))

    # Open questions
    if self.questions:
        lines = ["## ❓ Open Questions"]
        for q in sorted(self.questions, key=lambda x: -x.importance)[:5]:
            lines.append(f"- {q.content}")
        sections.append("\n".join(lines))

    # Preferences and constraints (compact)
    if self.preferences or self.constraints:
        lines = ["## 👤 Preferences"]
        for p in sorted(self.preferences, key=lambda x: -x.importance)[:5]:
            pin = "📌 " if p.pinned else ""
            lines.append(f"- {pin}{p.content}")
        for c in self.constraints:
            lines.append(f"- 🚫 {c.content}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
```

---

## User Commands: Look Inside the Brain

```
/memory                     # Show full memory state (formatted)
/memory context             # Show just context box
/memory goals               # Show objective + active + blocked
/memory learnings           # Show insights, warnings, questions
/memory preferences         # Show preferences and constraints
/memory json                # Export raw JSON (for debugging)
/memory importance          # Show all items sorted by importance
/memory stale               # Show items not referenced recently
/memory prune               # Manually trigger pruning with preview
/memory pin <id>            # Pin an item (never auto-prune)
/memory unpin <id>          # Unpin an item
/memory remove <id>         # Manually remove an item
/memory add <box> "content" # Manually add an item
/memory clear               # Clear all (with confirmation)
/memory export              # Export to markdown file
```

### Example Output: `/memory`

```
┌─────────────────────────────────────────────────────────────┐
│                     🧠 AGENT MEMORY                         │
├─────────────────────────────────────────────────────────────┤
│ 🎯 OBJECTIVE                                                │
│    Build a context management system for Mobius             │
│                                                             │
│ 📋 ACTIVE TASKS                                             │
│    • Design persistent memory architecture     [0.95] 📌    │
│    • Implement pruning system                  [0.80]       │
│                                                             │
│ ⏸️ BLOCKED                                                  │
│    (none)                                                   │
│                                                             │
│ 📎 CONTEXT (6 items)                                        │
│    • Mobius is a Python TUI using Textual     [0.85]       │
│    • Uses LiteLLM for LLM API calls           [0.70]       │
│    • Three-layer arch: Core, Tools, TUI       [0.65]       │
│    ...                                                      │
│                                                             │
│ 💡 INSIGHTS (4 items)                                       │
│    • Compression causes exponential decay     [0.90] 📌    │
│    • Need semantic memory separate from       [0.85]       │
│      episodic                                               │
│    ...                                                      │
│                                                             │
│ ⚠️ WARNINGS (2 items)                                       │
│    • Edit tool needs exact string match       [0.80]       │
│    • Don't split tool calls from results      [0.75]       │
│                                                             │
│ ❓ OPEN QUESTIONS (1 item)                                  │
│    • How to handle cross-session memory?      [0.60]       │
│                                                             │
│ 👤 PREFERENCES (3 items)                                    │
│    • User prefers Bun over Node              [0.90] 📌     │
│    • User wants concise responses            [0.85]        │
│    • Use "gist" not "summary"                [0.70]        │
├─────────────────────────────────────────────────────────────┤
│ 📊 15 items | ~850 tokens | budget: 2000                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Storage

```python
def save(self, path: Path):
    """Save memory to JSON file."""
    data = {
        "version": 1,
        "objective": self.objective,
        "context": [self._item_to_dict(i) for i in self.context],
        "active_tasks": [self._item_to_dict(i) for i in self.active_tasks],
        "blocked": [self._item_to_dict(i) for i in self.blocked],
        "insights": [self._item_to_dict(i) for i in self.insights],
        "warnings": [self._item_to_dict(i) for i in self.warnings],
        "questions": [self._item_to_dict(i) for i in self.questions],
        "preferences": [self._item_to_dict(i) for i in self.preferences],
        "constraints": [self._item_to_dict(i) for i in self.constraints],
    }
    path.write_text(json.dumps(data, indent=2, default=str))


@classmethod
def load(cls, path: Path) -> "AgentMemory":
    """Load memory from JSON file."""
    if not path.exists():
        return cls()

    data = json.loads(path.read_text())
    memory = cls()
    memory.objective = data.get("objective")
    memory.context = [cls._dict_to_item(d) for d in data.get("context", [])]
    memory.active_tasks = [cls._dict_to_item(d) for d in data.get("active_tasks", [])]
    memory.blocked = [cls._dict_to_item(d) for d in data.get("blocked", [])]
    memory.insights = [cls._dict_to_item(d) for d in data.get("insights", [])]
    memory.warnings = [cls._dict_to_item(d) for d in data.get("warnings", [])]
    memory.questions = [cls._dict_to_item(d) for d in data.get("questions", [])]
    memory.preferences = [cls._dict_to_item(d) for d in data.get("preferences", [])]
    memory.constraints = [cls._dict_to_item(d) for d in data.get("constraints", [])]
    return memory
```

### File Layout

```
~/.mobius/
├── histories/
│   └── {session_id}.gt.json       # Ground truth + working history
├── memory/
│   └── {session_id}.memory.json   # Agent memory (four boxes)
└── global/
    └── preferences.json            # Cross-session preferences (Phase 2)
```

---

## The `remember` and `forget` Tools

```python
def remember(content: str, box: str, importance: float = 0.7) -> str:
    """
    Tool: Store something in agent memory.

    Args:
        content: What to remember
        box: One of: context, insight, warning, question, preference, constraint, task
        importance: How important (0.0-1.0), relative to current objective

    Returns:
        Confirmation with assigned ID
    """
    item = agent_memory.add_item(box, content, importance)
    return f"Remembered [{item.id}]: {content}"


def forget(item_id: str) -> str:
    """
    Tool: Remove something from agent memory.

    Args:
        item_id: The ID of the item to forget

    Returns:
        Confirmation
    """
    item = agent_memory.get_item(item_id)
    if not item:
        return f"Item {item_id} not found"
    if item.pinned:
        return f"Cannot forget pinned item {item_id}"

    agent_memory.remove_item(item_id)
    return f"Forgot [{item_id}]: {item.content}"


def set_objective(objective: str) -> str:
    """
    Tool: Set or update the main objective.
    Triggers re-evaluation of all importance scores.

    Args:
        objective: The new objective

    Returns:
        Confirmation
    """
    agent_memory.on_objective_change(objective)
    return f"Objective set: {objective}"
```

---

## Integration with Consolidation Pipeline

```python
class MemoryAwareConsolidator:
    """Consolidator that maintains structured agent memory."""

    def consolidate(
        self,
        history: HistoryManager,
        memory: AgentMemory,
        counter: TokenCounter,
        llm_fn: Callable[[str], str],
    ) -> ConsolidationResult:
        """
        Compress history AND update agent memory.
        """
        # Get slice to compress
        query = HistoryQuery(history.working.entries, counter)
        slice_to_compress = query.first_percent(self.compress_ratio)

        if slice_to_compress.is_empty():
            return ConsolidationResult(consolidated=False)

        # Build consolidation prompt
        prompt = CONSOLIDATION_PROMPT.format(
            current_memory_json=memory.to_json_with_ids(),
            objective=memory.objective or "Not set",
            conversation_slice=slice_to_compress.to_gist_input(),
        )

        # Call LLM
        response = llm_fn(prompt)
        result = json.loads(response)

        # Apply memory updates
        updates = result.get("memory_updates", {})

        for item in updates.get("add", []):
            memory.add_item(
                box=item["box"],
                content=item["content"],
                importance=item.get("importance", 0.5),
                source_ids=slice_to_compress.ids(),
            )

        for item in updates.get("update", []):
            memory.update_importance(item["id"], item["importance"])

        for item_id in updates.get("remove", []):
            memory.remove_item(item_id)

        for task_id in updates.get("complete", []):
            memory.complete_task(task_id)

        if updates.get("block"):
            block = updates["block"]
            memory.block_task(block["id"], block["reason"])

        if result.get("objective_changed") and result.get("new_objective"):
            memory.on_objective_change(result["new_objective"])

        for question in result.get("new_questions", []):
            memory.add_item("questions", question, importance=0.5)

        # Replace history with gist
        safe_end = query.safe_boundary_near(slice_to_compress.end_idx)
        history.working.replace_range_with_gist(0, safe_end, result["gist"])

        # Save memory
        memory.save(self.memory_path)

        return ConsolidationResult(
            consolidated=True,
            entries_replaced=slice_to_compress.entry_count(),
            gist_text=result["gist"],
            memory_updates=updates,
        )
```

---

## Summary

| Aspect | Design |
|--------|--------|
| **Categories** | 4 boxes: Context, Goals, Learnings, Preferences |
| **Goals** | Objective (one) → Active (few) → Blocked (waiting) |
| **Learnings** | Insights, Warnings, Open Questions |
| **Structure** | MemoryItem with ID, content, importance, timestamps |
| **Consolidation** | Outputs structured JSON, not just gist blob |
| **Pruning** | LLM-assisted, goal-relative importance scores |
| **Visibility** | `/memory` commands let user inspect agent's brain |
| **Universal** | Works for coding, legal, games, research, anything |

### The Elegance

**Four boxes, one objective, importance scores, IDs for everything.**

- **Simple**: Just 4 categories that cover any domain
- **Structured**: JSON in/out, programmatic manipulation
- **Goal-oriented**: Importance is relative to current objective
- **Inspectable**: User can see exactly what the agent "knows"
- **Prunable**: When too big, LLM decides what to forget
- **Traceable**: Every item links back to source in ground truth
