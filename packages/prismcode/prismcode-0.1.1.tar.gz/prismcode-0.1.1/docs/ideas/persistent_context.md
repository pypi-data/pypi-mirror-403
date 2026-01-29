# Persistent Context: Solving Information Decay in Memory Compression

## The Problem

When we compress conversation history through gisting, information decays exponentially:

```
Round 1: [A B C D E F G H I J] → compress oldest 20% (A B)
         [GIST₁ C D E F G H I J]

Round 2: [GIST₁ C D E F G H I J K L M N] → compress oldest 20%
         [GIST₂ E F G H I J K L M N]

         GIST₂ now contains: compressed(GIST₁ + C + D)
         So GIST₁'s info is now ~33% of GIST₂

Round 3: [GIST₂ ... more stuff ...] → compress again
         GIST₃ contains: compressed(GIST₂ + ...)
         Original GIST₁ info is now ~10% of GIST₃

Round 4+: Information from early conversation approaches 0%
```

Important facts, user preferences, and key insights get diluted with each compression round until they're essentially lost - even if we wrote them down carefully in a gist.

## Root Cause: Missing Memory Type

Humans have three memory systems:

1. **Working memory** - Current focus (our context window)
2. **Episodic memory** - What happened (our ground truth + gists)
3. **Semantic memory** - Facts, knowledge, preferences (**we don't have this**)

We're missing semantic memory. That's the gap.

## Solution: Floating Persistent Context

A **persistent context** section that floats at the top of the context window, immune to compression:

```
┌─────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT                                           │
├─────────────────────────────────────────────────────────┤
│ 📌 PERSISTENT CONTEXT (floating, always present)        │
│                                                         │
│ ## User Preferences                                     │
│ - Prefers Bun over Node                                 │
│ - Likes concise responses with confidence scores        │
│ - Uses "gist" not "summary"                             │
│                                                         │
│ ## Project Facts                                        │
│ - Mobius is a terminal AI coding assistant              │
│ - Three-layer arch: Core, Tools, TUI                    │
│ - Uses LiteLLM for API calls                            │
│                                                         │
│ ## Current Goals                                        │
│ - Building context management system                    │
│ - Solving information decay in compression              │
│                                                         │
│ ## Key Insights                                         │
│ - Compression causes exponential info decay             │
│ - Need semantic memory separate from episodic           │
├─────────────────────────────────────────────────────────┤
│ [GIST of older conversation]                            │
├─────────────────────────────────────────────────────────┤
│ [Recent conversation - full fidelity]                   │
└─────────────────────────────────────────────────────────┘
```

The persistent context is:
- **Rebuilt/injected each turn** - not stored in conversation history
- **Immune to compression** - lives outside the episodic memory cycle
- **Accumulated over time** - extracted during compression or on-demand

## Data Structures

### PersistentFact

```python
@dataclass
class PersistentFact:
    """A single fact in persistent memory."""
    id: str
    content: str
    category: str  # "preference", "fact", "insight", "warning", "goal"
    created_at: datetime
    last_referenced: datetime
    reference_count: int = 0
    pinned: bool = False  # User pinned = never auto-prune
    source_entry_ids: List[str] = field(default_factory=list)  # Trace to ground truth

    def mark_referenced(self):
        """Update when this fact is used/mentioned."""
        self.last_referenced = datetime.now()
        self.reference_count += 1

    def age_in_turns(self, current_turn: int) -> int:
        """How many turns since last referenced."""
        # Implementation depends on turn tracking
        pass

    def is_stale(self, turns_threshold: int = 50) -> bool:
        """Check if fact hasn't been referenced recently."""
        # Pinned facts are never stale
        if self.pinned:
            return False
        # Check reference recency
        # ...
```

### PersistentContext

```python
@dataclass
class CategoryConfig:
    """Configuration for a fact category."""
    name: str
    max_items: int
    max_tokens: int
    header: str  # Display header like "## User Preferences"


class PersistentContext:
    """
    Semantic memory that floats at the top of context.
    Immune to compression, accumulated over time.
    """

    # Category configurations
    DEFAULT_CATEGORIES = {
        "preference": CategoryConfig("preference", max_items=10, max_tokens=500,
                                     header="## User Preferences"),
        "fact": CategoryConfig("fact", max_items=20, max_tokens=1000,
                              header="## Project Facts"),
        "goal": CategoryConfig("goal", max_items=5, max_tokens=300,
                              header="## Current Goals"),
        "insight": CategoryConfig("insight", max_items=10, max_tokens=500,
                                 header="## Key Insights"),
        "warning": CategoryConfig("warning", max_items=5, max_tokens=300,
                                 header="## Warnings (Mistakes to Avoid)"),
    }

    def __init__(self, max_total_tokens: int = 2500):
        self.facts: List[PersistentFact] = []
        self.max_total_tokens = max_total_tokens
        self.categories = self.DEFAULT_CATEGORIES.copy()
        self._lock = threading.Lock()  # Thread safety for background operations

    def add(self, content: str, category: str, source_ids: List[str] = None) -> PersistentFact:
        """Add a new fact. Handles deduplication."""
        with self._lock:
            # Check for duplicates (fuzzy match)
            if self._is_duplicate(content, category):
                return None

            fact = PersistentFact(
                id=str(uuid.uuid4()),
                content=content,
                category=category,
                created_at=datetime.now(),
                last_referenced=datetime.now(),
                source_entry_ids=source_ids or [],
            )
            self.facts.append(fact)

            # Handle overflow
            self._handle_overflow(category)

            return fact

    def _is_duplicate(self, content: str, category: str) -> bool:
        """Check if similar fact already exists."""
        # Simple: exact match
        # Better: fuzzy similarity threshold
        for fact in self.facts:
            if fact.category == category:
                if self._similarity(fact.content, content) > 0.85:
                    return True
        return False

    def _handle_overflow(self, category: str):
        """Handle when a category exceeds its limits."""
        config = self.categories.get(category)
        if not config:
            return

        category_facts = [f for f in self.facts if f.category == category]

        if len(category_facts) > config.max_items:
            # Strategy: Remove oldest non-pinned, least-referenced fact
            candidates = [f for f in category_facts if not f.pinned]
            if candidates:
                # Sort by reference_count (ascending), then by created_at (ascending)
                candidates.sort(key=lambda f: (f.reference_count, f.created_at))
                to_remove = candidates[0]
                self.facts.remove(to_remove)

    def merge(self, new_facts: List[PersistentFact]):
        """Merge extracted facts, handling duplicates."""
        for fact in new_facts:
            self.add(fact.content, fact.category, fact.source_entry_ids)

    def get_by_category(self, category: str) -> List[PersistentFact]:
        """Get all facts in a category."""
        return [f for f in self.facts if f.category == category]

    def get_stale(self, turns_threshold: int = 50) -> List[PersistentFact]:
        """Get facts that haven't been referenced recently."""
        return [f for f in self.facts if f.is_stale(turns_threshold)]

    def pin(self, fact_id: str):
        """Pin a fact (never auto-prune)."""
        for fact in self.facts:
            if fact.id == fact_id:
                fact.pinned = True
                break

    def remove(self, fact_id: str):
        """Remove a fact by ID."""
        self.facts = [f for f in self.facts if f.id != fact_id]

    def to_prompt_section(self) -> str:
        """Render as text for injection into context window."""
        sections = []

        for cat_key, config in self.categories.items():
            cat_facts = self.get_by_category(cat_key)
            if cat_facts:
                lines = [config.header]
                for fact in cat_facts:
                    pin_marker = "📌 " if fact.pinned else "- "
                    lines.append(f"{pin_marker}{fact.content}")
                sections.append("\n".join(lines))

        if not sections:
            return ""

        return "# 📋 Persistent Context\n\n" + "\n\n".join(sections)

    def token_count(self, counter) -> int:
        """Count tokens in the rendered persistent context."""
        return counter.count(self.to_prompt_section())

    # --- Persistence ---

    def save(self, path: Path):
        """Save to JSON file."""
        data = {
            "facts": [asdict(f) for f in self.facts],
            "max_total_tokens": self.max_total_tokens,
        }
        path.write_text(json.dumps(data, indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> "PersistentContext":
        """Load from JSON file."""
        if not path.exists():
            return cls()

        data = json.loads(path.read_text())
        ctx = cls(max_total_tokens=data.get("max_total_tokens", 2500))

        for fact_data in data.get("facts", []):
            fact = PersistentFact(
                id=fact_data["id"],
                content=fact_data["content"],
                category=fact_data["category"],
                created_at=datetime.fromisoformat(fact_data["created_at"]),
                last_referenced=datetime.fromisoformat(fact_data["last_referenced"]),
                reference_count=fact_data.get("reference_count", 0),
                pinned=fact_data.get("pinned", False),
                source_entry_ids=fact_data.get("source_entry_ids", []),
            )
            ctx.facts.append(fact)

        return ctx
```

## Extraction During Compression

When the consolidator compresses history, it also extracts persistent facts:

```python
class ConsolidatorWithExtraction:
    """Consolidator that extracts persistent facts during compression."""

    EXTRACTION_PROMPT = '''
Review this conversation segment and extract ONLY information worth remembering permanently.

## Categories

1. **USER PREFERENCES** - How the user likes to work
   - Tool/language preferences
   - Communication style preferences
   - Workflow preferences

2. **PROJECT FACTS** - Key technical facts about the codebase
   - Architecture decisions
   - Important file locations
   - Technology choices

3. **INSIGHTS** - Important realizations or decisions made
   - Design decisions and rationale
   - Problem-solving approaches that worked

4. **WARNINGS** - Mistakes made, things to avoid
   - Errors encountered and solutions
   - Anti-patterns discovered

5. **GOALS** - Current objectives (replace old goals, don't accumulate)
   - What the user is trying to accomplish
   - Active tasks

## Rules
- Only extract information valuable LONG-TERM
- Be specific and actionable
- One fact per line
- Skip transient/temporary information

## Output Format (JSON)
{
  "preferences": ["fact 1", "fact 2"],
  "facts": ["fact 1", "fact 2"],
  "insights": ["fact 1"],
  "warnings": ["fact 1"],
  "goals": ["goal 1"]
}

## Conversation to analyze:
{content}
'''

    def consolidate_with_extraction(
        self,
        history: HistoryManager,
        counter: TokenCounter,
        persistent_context: PersistentContext,
        gist_fn: Callable[[str], str],
    ) -> ConsolidationResult:
        """
        Compress history AND extract persistent facts.
        Uses threading for parallel gist + extraction.
        """
        # Get slice to compress
        query = HistoryQuery(history.working.entries, counter)
        slice_to_compress = query.first_percent(self.compress_ratio)

        if slice_to_compress.is_empty():
            return ConsolidationResult(consolidated=False)

        # Prepare inputs
        gist_input = slice_to_compress.to_gist_input()
        extraction_input = slice_to_compress.to_gist_input()

        # Run gist and extraction in parallel threads
        gist_result = [None]
        extraction_result = [None]

        def generate_gist():
            prompt = self.gist_prompt.format(content=gist_input)
            gist_result[0] = gist_fn(prompt)

        def extract_facts():
            prompt = self.EXTRACTION_PROMPT.format(content=extraction_input)
            response = gist_fn(prompt)  # Use same LLM
            try:
                extraction_result[0] = json.loads(response)
            except json.JSONDecodeError:
                extraction_result[0] = {}

        # Run in parallel
        gist_thread = threading.Thread(target=generate_gist)
        extract_thread = threading.Thread(target=extract_facts)

        gist_thread.start()
        extract_thread.start()

        gist_thread.join()
        extract_thread.join()

        # Process extraction results
        extracted = extraction_result[0] or {}
        source_ids = slice_to_compress.ids()

        for pref in extracted.get("preferences", []):
            persistent_context.add(pref, "preference", source_ids)
        for fact in extracted.get("facts", []):
            persistent_context.add(fact, "fact", source_ids)
        for insight in extracted.get("insights", []):
            persistent_context.add(insight, "insight", source_ids)
        for warning in extracted.get("warnings", []):
            persistent_context.add(warning, "warning", source_ids)
        for goal in extracted.get("goals", []):
            persistent_context.add(goal, "goal", source_ids)

        # Replace with gist
        safe_end = query.safe_boundary_near(slice_to_compress.end_idx)
        history.working.replace_range_with_gist(0, safe_end, gist_result[0])

        # Save persistent context
        persistent_context.save(self.persistent_context_path)

        return ConsolidationResult(
            consolidated=True,
            entries_replaced=slice_to_compress.entry_count(),
            gist_text=gist_result[0],
            # ... other fields
        )
```

## When to Extract Facts: Hybrid Approach

Facts need to be captured at the right moments - not too rarely (miss important stuff) and not too frequently (noise). We use a hybrid approach with multiple triggers:

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTRACTION TRIGGERS                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. COMPRESSION (always)                                    │
│     └─ Extract from slice being compressed                  │
│     └─ Information is about to be "lost" - last chance      │
│                                                             │
│  2. PATTERN MATCH (lightweight, every user turn)            │
│     └─ User says "remember", "always", "never", "I prefer"  │
│     └─ → Inject reflection prompt for agent to remember()   │
│                                                             │
│  3. EVENT-TRIGGERED (specific situations)                   │
│     └─ User corrects the agent → preference/warning         │
│     └─ Error resolved after struggle → warning + insight    │
│     └─ Major task completed → goals update                  │
│                                                             │
│  4. PERIODIC (every N turns, background thread)             │
│     └─ Quick scan of recent history                         │
│     └─ Low priority, non-blocking safety net                │
│                                                             │
│  5. EXPLICIT (user or agent initiated)                      │
│     └─ Agent calls remember() tool                          │
│     └─ User runs /remember command                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Trigger 1: During Compression

Already covered above - when context hits budget threshold, extract from the slice being gisted.

### Trigger 2: Pattern Matching

Lightweight regex check on every user message:

```python
class ExtractionTriggers:
    """Detect when extraction should happen."""

    CORRECTION_PATTERNS = [
        r"no,?\s+(actually|I meant|I want)",
        r"don't do that",
        r"stop doing",
        r"I told you",
    ]

    PREFERENCE_PATTERNS = [
        r"I (prefer|like|want|hate|don't like)",
        r"always use",
        r"never use",
        r"from now on",
    ]

    REMEMBER_PATTERNS = [
        r"remember (this|that)",
        r"keep in mind",
        r"important:",
        r"note:",
        r"don't forget",
    ]

    def check_user_message(self, message: str) -> Optional[str]:
        """
        Check if message contains extraction triggers.
        Returns trigger type or None.
        """
        text = message.lower()

        for pattern in self.CORRECTION_PATTERNS:
            if re.search(pattern, text):
                return "correction"

        for pattern in self.PREFERENCE_PATTERNS:
            if re.search(pattern, text):
                return "preference"

        for pattern in self.REMEMBER_PATTERNS:
            if re.search(pattern, text):
                return "explicit"

        return None
```

When a trigger fires, inject a reflection prompt:

```python
def on_user_message(self, message: str) -> Optional[str]:
    """Called after each user message. Returns system injection if needed."""
    trigger = self.triggers.check_user_message(message)

    if trigger == "correction":
        return (
            "[System: The user just corrected you. Consider using remember() "
            "to store their preference or a warning about the mistake.]"
        )
    elif trigger == "preference":
        return (
            "[System: The user expressed a preference. Consider using remember() "
            "to store it permanently.]"
        )
    elif trigger == "explicit":
        return (
            "[System: The user wants you to remember something. Use remember() "
            "to store it in persistent memory.]"
        )

    return None
```

### Trigger 3: Event-Triggered

Certain events signal "this might be important":

| Event | Extraction Type | Example |
|-------|-----------------|---------|
| User corrects agent | preference, warning | "No, use Bun not Node" |
| Error resolved after multiple attempts | warning, insight | Finally fixed after 5 tries |
| User says "remember/always/never" | explicit preference | "Always use type hints" |
| Major task completed | goal update | Feature implementation done |
| File structure explained | project fact | "The API lives in /src/api" |
| Architecture decision made | insight | "We're using event sourcing" |

### Trigger 4: Periodic Background Check

Safety net that runs every N turns in a background thread:

```python
class FactExtractor:
    """Manages when and how facts get extracted."""

    def __init__(self, persistent_context: PersistentContext, llm_fn: Callable):
        self.context = persistent_context
        self.llm_fn = llm_fn
        self.turn_count = 0
        self.last_periodic_check = 0
        self.periodic_interval = 15  # Every 15 turns
        self._background_thread = None

    def tick(self):
        """Called each turn. Schedules background extraction if needed."""
        self.turn_count += 1

        if self.turn_count - self.last_periodic_check >= self.periodic_interval:
            self._schedule_background_extraction()

    def _schedule_background_extraction(self):
        """Run extraction in background thread."""
        self.last_periodic_check = self.turn_count

        # Don't stack up background jobs
        if self._background_thread and self._background_thread.is_alive():
            return

        self._background_thread = threading.Thread(
            target=self._background_extract,
            daemon=True
        )
        self._background_thread.start()

    def _background_extract(self):
        """Background thread: scan recent history for facts."""
        # Get last N entries (since last check)
        recent_entries = self._get_recent_entries()

        if not recent_entries:
            return

        # Lightweight extraction prompt
        prompt = f"""
Quick scan: Are there any facts worth remembering permanently from this conversation?

Only extract if clearly important. Return empty JSON if nothing notable.

{self._format_entries(recent_entries)}

Return JSON: {{"preferences": [], "facts": [], "insights": [], "warnings": []}}
"""

        try:
            response = self.llm_fn(prompt)
            extracted = json.loads(response)

            # Add any extracted facts
            for pref in extracted.get("preferences", []):
                self.context.add(pref, "preference")
            # ... etc
        except:
            pass  # Background extraction is best-effort
```

### Trigger 5: Explicit (The `remember` Tool)

The agent can proactively remember things via a tool call:

```python
REMEMBER_TOOL = {
    "type": "function",
    "function": {
        "name": "remember",
        "description": (
            "Store an important fact in persistent memory. Use this when you learn "
            "something worth remembering long-term: user preferences, project facts, "
            "key insights, or warnings about mistakes to avoid. "
            "Persistent memories survive context compression."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The fact to remember (be specific and actionable)"
                },
                "category": {
                    "type": "string",
                    "enum": ["preference", "fact", "insight", "warning", "goal"],
                    "description": "Category: preference (user likes/dislikes), fact (project info), insight (realization), warning (mistake to avoid), goal (current objective)"
                }
            },
            "required": ["content", "category"]
        }
    }
}
```

System prompt addition:

```
## Persistent Memory

You have a `remember` tool to store important information permanently. Use it when:
- User expresses a preference ("I prefer X", "always do Y", "never do Z")
- You learn a key fact about the project or codebase
- You have an important insight or realization
- You make a mistake worth avoiding in the future
- Goals or objectives change

Persistent memories survive context compression and will always be available to you.
Don't over-use this - only remember things that are genuinely important long-term.
```

### Full FactExtractor Implementation

```python
class FactExtractor:
    """
    Manages when and how facts get extracted to persistent memory.
    Uses multiple triggers: compression, pattern matching, periodic, explicit.
    """

    def __init__(
        self,
        persistent_context: PersistentContext,
        llm_fn: Callable[[str], str],
        periodic_interval: int = 15,
    ):
        self.context = persistent_context
        self.llm_fn = llm_fn
        self.periodic_interval = periodic_interval

        self.turn_count = 0
        self.last_periodic_check = 0
        self.triggers = ExtractionTriggers()

        self._background_thread = None
        self._lock = threading.Lock()

    def on_user_message(self, message: str, history_entries: List = None) -> Optional[str]:
        """
        Called after each user message.

        Args:
            message: The user's message
            history_entries: Recent history for periodic extraction

        Returns:
            System injection string if extraction should happen, else None
        """
        self.turn_count += 1

        # Check pattern triggers (lightweight)
        trigger_type = self.triggers.check_user_message(message)
        injection = None

        if trigger_type == "correction":
            injection = (
                "[System: The user just corrected you. Consider using remember() "
                "to store their preference or a warning about the mistake.]"
            )
        elif trigger_type == "preference":
            injection = (
                "[System: The user expressed a preference. Consider using remember() "
                "to store it permanently.]"
            )
        elif trigger_type == "explicit":
            injection = (
                "[System: The user wants you to remember something. Use remember() "
                "to store it in persistent memory.]"
            )

        # Check if periodic extraction is due (runs in background)
        if self.turn_count - self.last_periodic_check >= self.periodic_interval:
            if history_entries:
                self._schedule_background_extraction(history_entries)

        return injection

    def on_compression(self, slice_to_compress, gist_fn: Callable = None) -> Dict:
        """
        Called during compression. Extract facts from disappearing content.
        Runs in parallel with gist generation.

        Args:
            slice_to_compress: HistorySlice being compressed
            gist_fn: LLM function (uses self.llm_fn if None)

        Returns:
            Dict of extracted facts by category
        """
        fn = gist_fn or self.llm_fn
        content = slice_to_compress.to_gist_input()
        source_ids = slice_to_compress.ids()

        prompt = self._extraction_prompt(content)

        try:
            response = fn(prompt)
            extracted = json.loads(response)
        except (json.JSONDecodeError, Exception):
            extracted = {}

        # Add to persistent context
        with self._lock:
            for pref in extracted.get("preferences", []):
                self.context.add(pref, "preference", source_ids)
            for fact in extracted.get("facts", []):
                self.context.add(fact, "fact", source_ids)
            for insight in extracted.get("insights", []):
                self.context.add(insight, "insight", source_ids)
            for warning in extracted.get("warnings", []):
                self.context.add(warning, "warning", source_ids)
            for goal in extracted.get("goals", []):
                self.context.add(goal, "goal", source_ids)

        return extracted

    def _schedule_background_extraction(self, recent_entries: List):
        """Schedule background extraction in a thread."""
        self.last_periodic_check = self.turn_count

        if self._background_thread and self._background_thread.is_alive():
            return

        self._background_thread = threading.Thread(
            target=self._background_extract,
            args=(recent_entries,),
            daemon=True
        )
        self._background_thread.start()

    def _background_extract(self, entries: List):
        """Background thread: scan entries for facts."""
        # Format entries for prompt
        content = "\n".join(
            f"{e.role.upper()}: {e.content or '[tool call]'}"
            for e in entries[-20:]  # Last 20 entries max
        )

        prompt = f"""
Quick scan: Any facts worth remembering permanently?
Only extract if clearly important. Return empty lists if nothing notable.

{content}

Return JSON only: {{"preferences": [], "facts": [], "insights": [], "warnings": []}}
"""

        try:
            response = self.llm_fn(prompt)
            # Try to extract JSON from response
            extracted = json.loads(response)

            with self._lock:
                for pref in extracted.get("preferences", []):
                    self.context.add(pref, "preference")
                for fact in extracted.get("facts", []):
                    self.context.add(fact, "fact")
                for insight in extracted.get("insights", []):
                    self.context.add(insight, "insight")
                for warning in extracted.get("warnings", []):
                    self.context.add(warning, "warning")
        except:
            pass  # Background extraction is best-effort

    def _extraction_prompt(self, content: str) -> str:
        """Generate the full extraction prompt."""
        return f'''
Review this conversation and extract ONLY information worth remembering permanently.

## Categories
- **preferences**: User preferences (tools, style, workflow)
- **facts**: Project/codebase facts (architecture, file locations)
- **insights**: Important realizations, decisions, rationale
- **warnings**: Mistakes made, things to avoid
- **goals**: Current objectives (these replace old goals)

## Rules
- Only extract LONG-TERM valuable information
- Be specific and actionable
- Skip transient/temporary details
- One fact per item

## Conversation:
{content}

## Output (JSON only):
{{"preferences": [], "facts": [], "insights": [], "warnings": [], "goals": []}}
'''
```

### Summary: When Facts Get Extracted

| Trigger | Frequency | Blocking? | Reliability |
|---------|-----------|-----------|-------------|
| Compression | When budget exceeded | Yes (parallel with gist) | High - last chance |
| Pattern match | Every user turn | No (just injects prompt) | Medium - depends on agent |
| Event-triggered | On specific events | No | Medium |
| Periodic | Every N turns | No (background thread) | Low - safety net |
| Explicit tool | Agent decides | Yes | High - intentional |

The hybrid approach ensures facts are captured at multiple points without being intrusive or blocking the conversation.

## On-Demand Extraction via Tools

Users or the agent can add facts at any time via tool calls:

```python
def remember_fact(content: str, category: str = "fact") -> str:
    """
    Tool: Store a fact in persistent memory.

    Args:
        content: The fact to remember
        category: One of: preference, fact, insight, warning, goal

    Returns:
        Confirmation message
    """
    fact = persistent_context.add(content, category)
    if fact:
        return f"Remembered: {content}"
    else:
        return f"Already known (duplicate detected)"


def forget_fact(fact_id: str) -> str:
    """
    Tool: Remove a fact from persistent memory.

    Args:
        fact_id: The ID of the fact to forget

    Returns:
        Confirmation message
    """
    persistent_context.remove(fact_id)
    return f"Forgot fact {fact_id}"
```

## User Commands

```
/facts                    # Show all persistent facts by category
/facts preferences        # Show only preferences
/facts add "user likes X" # Manually add a fact
/facts pin <id>           # Pin a fact (never auto-prune)
/facts remove <id>        # Remove a fact
/facts prune              # Show stale facts, prompt for removal
/facts clear              # Clear all (with confirmation)
/facts export             # Export to markdown
```

## Integration with Context Building

When building context for the LLM:

```python
class Agent:
    def build_context(self) -> List[Dict[str, Any]]:
        """Build the full context for LLM call."""
        messages = []

        # 1. System prompt
        messages.append({"role": "system", "content": self.system_prompt})

        # 2. Persistent context (floating header)
        persistent_section = self.persistent_context.to_prompt_section()
        if persistent_section:
            messages.append({
                "role": "user",
                "content": f"{persistent_section}\n\n---\n\n[Conversation continues below]"
            })

        # 3. Working history (gists + recent conversation)
        messages.extend(self.history.get_context())

        return messages
```

## Storage Layout

```
~/.mobius/
├── histories/
│   └── {session_id}.gt.json       # Ground truth + working history
├── persistent/
│   └── {session_id}.facts.json    # Persistent context for this session
└── global/
    └── preferences.json            # Cross-session user preferences (Phase 2)
```

## Pruning Strategy

Facts accumulate over time. Pruning keeps the persistent context useful:

### Automatic (Soft)
- When a category overflows its `max_items`:
  - Remove oldest non-pinned fact with lowest `reference_count`
  - Never remove pinned facts

### User-Initiated (Hard)
- `/facts prune` shows stale facts (not referenced in N turns)
- User decides what to keep/remove
- Can pin important facts to protect them

### Smart Consolidation (Future)
- When facts overflow significantly, prompt LLM to consolidate similar facts
- "User prefers Bun" + "User likes Bun over Node" → "User prefers Bun over Node.js"

## Reference Tracking

To know which facts are still relevant:

```python
class Agent:
    def post_response_hook(self, response: str):
        """After each LLM response, track fact references."""
        # Simple: Check if fact content appears in response
        for fact in self.persistent_context.facts:
            if fact.content.lower() in response.lower():
                fact.mark_referenced()

        # Better: Ask LLM which facts it used (adds latency)
        # Best: Fine-tune model to output fact IDs when using them
```

## Phase 1 vs Phase 2

### Phase 1: In-Context (This Document)
- Persistent context as floating header
- Extracted during compression + on-demand
- JSON storage, injected each turn
- User commands for management
- Simple overflow handling

### Phase 2: RAG Integration (Future)
- Vector embeddings of ground truth
- Semantic search for relevant past context
- Dynamic retrieval based on current query
- Cross-session memory
- Much larger memory capacity

## Summary

The solution separates **semantic memory** (facts, preferences, insights) from **episodic memory** (what happened).

- Episodic → Ground truth + gists, subject to compression decay
- Semantic → Persistent context, floating header, protected from compression

This mirrors how human memory works and prevents the exponential information decay problem.
