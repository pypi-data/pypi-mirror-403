Let me think through this properly with the scratchpad concept and real numbers.

**The key reframe:** Most of that 200K tokens is wasted on repeated file contents. If we separate *state* from *history*, the actual history generation rate drops dramatically.

**Estimating real history rate (without file contents):**

Per 30-minute session:
- User messages: ~20 messages × 100 tokens = 2K
- Diff descriptions: ~30 changes × 200 tokens = 6K  
- Assistant explanations (compressed): ~10K
- Errors/misc: ~4K
- **Total actual history: ~22K per 30 min = ~44K/hour**

That's 10x more manageable than 400K/hour.

**The scratchpad saves everything:**

Instead of files appearing 10+ times in history (375K tokens), they appear once in the scratchpad (~30-40K). The history only stores what *changed*.

Let me design this properly:

---

**The Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW (~30K target)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  SCRATCHPAD: Open Files (10-20K, variable)               │   │
│  │  ────────────────────────────────────────────────────────│   │
│  │  • file.py (current contents)                            │   │
│  │  • config.json (current contents)                        │   │
│  │  • [open/close as needed, max ~5-8 files]                │   │
│  │  NOT in history - just current state                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  T2: Session Facts (2K)                                  │   │
│  │  ────────────────────────────────────────────────────────│   │
│  │  • Architectural decisions                               │   │
│  │  • User preferences discovered                           │   │
│  │  • Conventions established                               │   │
│  │  • Key constraints                                       │   │
│  │  Format: Structured YAML                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  T1: Medium-Term Memory (3K) - covers ~1 hour            │   │
│  │  ────────────────────────────────────────────────────────│   │
│  │  • Summarized: what was done, decisions, solutions       │   │
│  │  • Compression: ~10:1                                    │   │
│  │  • Covers: ~30K original history                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  T0: Working Memory (5K) - last ~15 minutes              │   │
│  │  ────────────────────────────────────────────────────────│   │
│  │  • Verbatim user messages                                │   │
│  │  • Diffs (not full files)                                │   │
│  │  • Key assistant responses                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Total: Scratchpad (15K avg) + T2 (2K) + T1 (3K) + T0 (5K) = ~25K
```

---

**The scratchpad mechanics:**

```
OPEN file.py:
  → File contents added to scratchpad
  → History entry: "[opened file.py, 150 lines]"

EDIT file.py line 50:
  → Scratchpad updated in place
  → History entry: "[file.py:50] changed `x = 1` → `x = calculate()` (fixing init bug)"

CLOSE file.py:
  → Removed from scratchpad
  → History entry: "[closed file.py, 12 edits made]"

AUTO-CLOSE after 10 exchanges without touching:
  → Same as close
```

**History now looks like:**

```
[user] read the auth module
[opened auth.py, 200 lines]
[user] the login function has a bug on line 45
[auth.py:45] changed `if user:` → `if user and user.active:` (null check)
[user] also add logging
[auth.py:12] added `import logging`
[auth.py:47] added `logging.info(f"Login attempt: {user.id}")`
[user] now check the config
[opened config.json, 30 lines]
[closed auth.py, 3 edits]
...
```

Instead of 200 lines × 4 times = 800 lines of file content, we have ~10 lines of diffs.

---

**Graduation flow:**

```
Every ~3K tokens of history in T0:
├── Find natural boundary (task completion, topic change)
├── Graduate oldest ~2K to T1
├── Summarize 2K → ~300 tokens
└── Keep T0 at ~5K

Every ~2K tokens added to T1:
├── Consolidate oldest half
├── Extract key decisions → T2
├── Re-summarize remainder
└── Keep T1 at ~3K

T2 rolls continuously:
├── New facts update/replace old
├── Contradictions resolved (new wins)
└── Stays at ~2K max
```

---

**The effective coverage:**

| Tier | Tokens | Compression | Original | Time Coverage |
|------|--------|-------------|----------|---------------|
| Scratchpad | 15K | 1:1 (current) | N/A | Current state |
| T0 | 5K | 1:1 | 5K | ~15 min |
| T1 | 3K | 10:1 | 30K | ~45 min |
| T2 | 2K | extracted | session | Whole session |
| **Total** | **25K** | | **35K + state** | **~1-2 hours detailed** |

After 2 hours, oldest stuff is in T2 as facts. You still know *what* was decided, just not the full conversation about it. Which matches your "I've usually moved on after an hour anyway."

---

**What each tier stores:**

**T0 (verbatim):**
- Exact user messages
- Exact diffs
- Key error messages
- Assistant's conclusions (not full explanations)

**T1 (summarized):**
- "Fixed auth bug: was checking user without null check"
- "Implemented rate limiting on /api/query endpoint"
- "User prefers functional style over classes"
- "Refactored config loading into separate module"

**T2 (facts):**
```yaml
architecture:
  - "RAG system with indexer and query components"
  - "Background workers for content evaluation"
  
conventions:
  - "Functional style, minimal classes"
  - "Error handling via custom exceptions"
  
decisions:
  - "Using PostgreSQL over SQLite for concurrency"
  - "JWT tokens with 1hr expiry"
  
user_preferences:
  - "Concise responses"
  - "No unnecessary explanations"
```

---

Want me to write up the full implementation with the scratchpad system and the prompts for each tier transition? This is feeling much more practical now that we're not trying to compress repeated file contents.

# Mobius

## A Context Management System for Infinite Coding Sessions

---

## The Problem

### Current AI coding agents are fundamentally broken

Every major AI coding tool—Claude Code, Gemini CLI, Cursor, Cline—shares the same fatal flaw: they treat context management as an afterthought. The result is that productive coding sessions hit a wall after 20-30 minutes, and when they do, the "solution" destroys almost everything useful.

### The brutal math

A typical 30-minute coding session with Claude Code generates approximately **200,000 tokens**. This fills the context window. The bulk of these tokens come from:

- **File contents read repeatedly**: Every time you ask the agent to look at a file, the entire file goes into context. Edit a file 5 times? That's 5 complete copies of the file in history.
- **Full file contents in responses**: When the agent shows you code, that's more tokens.
- **Error traces**: Stack traces, logs, verbose error output.
- **Tool call overhead**: The structural tokens around every operation.

When the context fills, these tools trigger "compaction" or "compression." Here's what that actually means:

```
Before compression: 200,000 tokens of rich conversation history
After compression:  ~2,000 tokens of summary

Compression ratio: 100:1
Information retained: ~1-2%
```

This isn't compression. **This is amnesia.**

The agent that emerges from compaction doesn't remember:
- What files it was working on
- What approach was agreed upon
- What solutions were already tried and failed
- What conventions were established
- What the user's preferences are

Users consistently report that post-compaction, the agent "is definitely dumber," makes mistakes that were already corrected, and needs to re-read files it was just working on.

### Why current approaches fail

**1. Single-pass summarisation is catastrophic**

Summarising 200K tokens into 2K tokens is a 100:1 compression ratio. No summarisation technique, no matter how clever the prompt, can preserve meaningful context at this ratio. It's like trying to compress a novel into a tweet.

**2. Large context windows don't solve the problem**

Gemini offers 1M tokens. Claude offers 200K. But research consistently shows that model performance degrades well before these limits—around **25-30K tokens** regardless of advertised capacity. This is due to attention distribution issues and the "lost in the middle" phenomenon where information at the edges of context has high recall but middle-positioned information is effectively invisible.

So even if you could fit 1M tokens, the model couldn't effectively use it.

**3. The real problem: repeated file contents**

The dirty secret of why coding sessions burn through context so fast is that **the same information is stored over and over**. A 500-line file that gets edited 10 times appears 10 times in the conversation history. That's 5,000 lines of redundant file content.

This is the core inefficiency that Mobius addresses.

---

## The Solution

### Core Insight: Separate State from History

The fundamental innovation in Mobius is recognising that **current file state** and **conversation history** are different things that should be managed differently.

Current tools conflate them:
```
[msg 1] User: read auth.py
[msg 2] Assistant: Here's auth.py: <500 lines>
[msg 3] User: fix the bug on line 50
[msg 4] Assistant: Done. Here's the updated file: <500 lines>
[msg 5] User: also add logging
[msg 6] Assistant: Added. Here's the file now: <500 lines>
```

That's 1,500 lines of file content when only ~10 lines actually changed.

Mobius separates these:

```
┌─────────────────────────────────────┐
│  SCRATCHPAD (Current File State)    │
│  auth.py: <500 lines, always latest>│
└─────────────────────────────────────┘

HISTORY:
[msg 1] User: read auth.py
        [opened auth.py, 500 lines]
[msg 2] User: fix the bug on line 50  
        [auth.py:50] `if user:` → `if user and user.active:`
[msg 3] User: also add logging
        [auth.py:3] added `import logging`
        [auth.py:52] added `logging.info(f"Login: {user.id}")`
```

The file exists **once** in the scratchpad. The history stores only **what changed**. Token usage drops by 10-50x for file-heavy sessions.

---

## Architecture

### The Mobius Context Window

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CONTEXT WINDOW (~25-30K tokens)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  SCRATCHPAD: Open Files                         (10-15K)      │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │                                                               │  │
│  │  Currently open files with their latest contents.             │  │
│  │  Files are opened/closed explicitly or automatically.         │  │
│  │  NOT stored in history—just current state.                    │  │
│  │                                                               │  │
│  │  Example:                                                     │  │
│  │  • src/auth.py (245 lines) [opened 12 min ago, 4 edits]      │  │
│  │  • src/config.json (52 lines) [opened 3 min ago]             │  │
│  │  • tests/test_auth.py (180 lines) [opened 8 min ago, 2 edits]│  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  TIER 2: Session Facts                          (2K)          │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │                                                               │  │
│  │  Extracted durable knowledge that persists across the         │  │
│  │  entire session. Updated continuously, not appended.          │  │
│  │                                                               │  │
│  │  Contains:                                                    │  │
│  │  • Architectural decisions made                               │  │
│  │  • User preferences discovered                                │  │
│  │  • Conventions established                                    │  │
│  │  • Constraints and requirements                               │  │
│  │  • Patterns to follow or avoid                                │  │
│  │                                                               │  │
│  │  Format: Structured YAML for easy parsing and updating        │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  TIER 1: Medium-Term Memory                     (3-4K)        │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │                                                               │  │
│  │  Summarised history covering ~30-45 minutes of work.          │  │
│  │  Compression ratio: ~10:1                                     │  │
│  │                                                               │  │
│  │  Contains:                                                    │  │
│  │  • What was accomplished (features, fixes)                    │  │
│  │  • Key decisions and their rationale                          │  │
│  │  • Problems solved (symptom → solution)                       │  │
│  │  • Important context for ongoing work                         │  │
│  │                                                               │  │
│  │  Format: Narrative markdown, scannable                        │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  TIER 0: Working Memory                         (5-8K)        │  │
│  │  ─────────────────────────────────────────────────────────    │  │
│  │                                                               │  │
│  │  Verbatim recent conversation. Last ~10-15 minutes.           │  │
│  │  No compression—full fidelity.                                │  │
│  │                                                               │  │
│  │  Contains:                                                    │  │
│  │  • Exact user messages                                        │  │
│  │  • Diff records (not full files)                              │  │
│  │  • Error messages encountered                                 │  │
│  │  • Assistant conclusions and actions                          │  │
│  │                                                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Token Budget

| Component | Tokens | Purpose |
|-----------|--------|---------|
| Scratchpad | 10-15K | Current state of open files |
| Tier 2 (Facts) | 2K | Durable session knowledge |
| Tier 1 (Medium) | 3-4K | Summarised recent work |
| Tier 0 (Working) | 5-8K | Verbatim recent conversation |
| **Total** | **20-29K** | Well within effective model range |

### Time Coverage

With the scratchpad handling file state, the actual conversation history generation rate drops to approximately **30-40K tokens/hour** (versus 400K+/hour without it).

| Tier | Covers | Detail Level |
|------|--------|--------------|
| T0 | Last ~15 min | Full verbatim |
| T1 | ~15-60 min ago | Summarised 10:1 |
| T2 | Entire session | Extracted facts |

**Effective coverage: 1-2+ hours with full continuity.**

After 2 hours, the oldest details have been summarised and key facts extracted. The agent knows *what* was decided even if it doesn't remember the full conversation. This matches actual usage patterns—most users have moved on from their initial task after an hour anyway.

---

## The Scratchpad

### Concept

The Scratchpad is a **floating window** of currently relevant files. It exists outside the conversation history. Files are:

- **Opened** when the user asks to read them or when the agent needs to work on them
- **Updated in place** when edits are made (the Scratchpad always shows current state)
- **Closed** explicitly or automatically after a period of inactivity

The conversation history stores only:
- The fact that a file was opened/closed
- The diffs (changes made), not full contents

### Mechanics

**Opening a file:**
```
User: "look at the auth module"

Scratchpad: [adds src/auth.py with current contents]
History: "[opened src/auth.py, 245 lines]"
```

**Editing a file:**
```
User: "fix the null check on line 50"

Scratchpad: [updates src/auth.py in place]
History: "[src/auth.py:50] `if user:` → `if user and user.active:` — added null check"
```

**Multiple edits:**
```
User: "add logging to that function"

Scratchpad: [updates src/auth.py in place]
History: 
  "[src/auth.py:3] added `import logging`"
  "[src/auth.py:52-53] added logging statements for login tracking"
```

**Closing a file:**
```
User: "done with auth for now" 
  — or —
Auto-close after 10 exchanges without touching the file

Scratchpad: [removes src/auth.py]
History: "[closed src/auth.py, 6 edits made]"
```

### Why this works

In a typical session, a file might be:
- Read once
- Edited 5-10 times
- Referenced in discussion multiple times

**Without Scratchpad:** File contents appear 10+ times = 10 × file_size tokens
**With Scratchpad:** File contents appear once = 1 × file_size tokens

For a 500-line file (roughly 2K tokens) edited 10 times:
- Without: 20K tokens
- With: 2K tokens + ~500 tokens of diffs = 2.5K tokens

**That's an 8x reduction** for a single file. Across a session with multiple files, this compounds dramatically.

---

## Tiered Memory

### The Graduation Flow

As the conversation progresses, older content graduates from verbatim storage to summarised storage to extracted facts:

```
New messages arrive
       │
       ▼
┌─────────────────┐
│     TIER 0      │ ← Verbatim storage
│   max: ~6K      │
└────────┬────────┘
         │
When T0 exceeds limit:
Find natural boundary, summarise oldest chunk
         │
         ▼
┌─────────────────┐
│     TIER 1      │ ← Detailed summaries (~10:1 compression)
│   max: ~4K      │
└────────┬────────┘
         │
When T1 exceeds limit:
Consolidate, extract facts
         │
         ▼
┌─────────────────┐
│     TIER 2      │ ← Extracted facts (update in place)
│   max: ~2K      │
└─────────────────┘
```

### Natural Boundaries

Content doesn't graduate at arbitrary token counts. Mobius detects natural conversation boundaries:

**Strong boundaries (prefer these):**
- Task completion: "Done!", "That should work", "Fixed", "All tests passing"
- Topic change: "Now let's work on...", "Different question", "Moving on to"

**Moderate boundaries:**
- User message (natural turn-taking)
- End of code block

**Weak/avoid:**
- Mid-code-block
- Mid-error-trace
- Continuation of same thought

This preserves coherent chunks of work rather than slicing arbitrarily.

### Content-Aware Retention

Not all content compresses at the same rate. Different types have different "half-lives":

**Compress slowly (often promote to T2):**
- Architectural decisions
- User-stated requirements
- Error resolutions (problem + solution)
- Established conventions
- Security/performance constraints

**Compress normally:**
- Feature implementations
- Refactoring rationale
- API design choices
- Test strategies

**Compress aggressively:**
- Routine Q&A
- Minor clarifications
- Standard code review exchanges

**Drop entirely after T0:**
- Greetings and pleasantries
- Acknowledgments ("Got it", "Thanks")
- Verbose code blocks (code is in files/scratchpad)
- Dead-end debugging attempts
- Repeated explanations

---

## What Each Tier Stores

### Tier 0: Working Memory (Verbatim)

The last ~15 minutes of conversation, stored exactly as it happened.

```
[user] the login function seems to hang sometimes

[opened src/auth/login.py, 89 lines]

[user] I think it's the database call on line 45

[assistant] Looking at line 45, you're right—there's no timeout on the 
database query. If the DB is slow, this blocks indefinitely.

[login.py:45] `result = db.query(user_id)` → `result = db.query(user_id, timeout=5.0)`
[login.py:46-52] added try/except for TimeoutError with retry logic

[user] test it

[ran: pytest tests/test_login.py -v]
[result: 3 passed, 0 failed]

[user] nice, let's also add logging
```

### Tier 1: Medium-Term Memory (Summarised)

Covers ~15-60 minutes ago, compressed ~10:1.

```
## Session Progress (45 min - 15 min ago)

### Completed
- Fixed login timeout issue: added 5s timeout to DB query with retry logic
- Added comprehensive logging to auth module
- Created test_login.py with 3 test cases (all passing)

### Decisions Made
- Using 5s timeout for all DB calls (user approved)
- Retry logic: max 3 attempts with exponential backoff
- Log format: structured JSON for parsing

### Files Modified
- src/auth/login.py: timeout handling, retry logic, logging
- tests/test_login.py: created with timeout and retry tests
- src/config.py: added DB_TIMEOUT constant

### Open Items
- TODO: Apply same timeout pattern to other DB calls
- NOTE: User mentioned possible rate limiting needs later
```

### Tier 2: Session Facts (Extracted)

Durable knowledge that applies across the whole session.

```yaml
project:
  name: "Chat To Premium"
  type: "RAG system for hotel customer service"
  
architecture:
  - "Separate indexing and query pipelines"
  - "Background workers for content evaluation"
  - "Chatbot class with ask/amend methods"
  
conventions:
  db_calls: "Always use 5s timeout with 3x retry"
  logging: "Structured JSON format"
  errors: "Custom exceptions extending BaseError"
  style: "Functional preferred, minimal classes"
  
user_preferences:
  communication: "Concise, no unnecessary explanation"
  code_style: "Simple, readable, separation of concerns"
  
constraints:
  - "Must handle content changes gracefully (intelligent laziness)"
  - "Black box component design"
  
patterns_established:
  - "Timeout + retry for all external calls"
  - "Log at entry and exit of key functions"
```

---

## The Math

### Without Mobius (Current Tools)

```
30-minute session:
├── File contents (repeated): 150K tokens
├── Tool call overhead: 20K tokens  
├── Conversation: 20K tokens
├── Code in responses: 10K tokens
└── Total: ~200K tokens

Compression triggered → 2K summary
Retention: 1%
```

### With Mobius

```
30-minute session:
├── Scratchpad (files once): 15K tokens [not in history]
├── Diffs in history: 3K tokens
├── Tool call overhead: 5K tokens (reduced—no file contents)
├── Conversation: 15K tokens
└── History total: ~23K tokens

No compression needed—fits in effective context window
Retention: 100%

After 1 hour:
├── Scratchpad: 15K tokens
├── T2 (facts): 2K tokens
├── T1 (summarised): 4K tokens  
├── T0 (verbatim): 6K tokens
└── Total: ~27K tokens

Still fits. Oldest details summarised but decisions preserved.
Retention: ~60-80% of meaningful information
```

### Comparison

| Metric | Current Tools | Mobius |
|--------|---------------|--------|
| 30 min session tokens | 200K | ~23K history + 15K scratchpad |
| Compression needed | Yes, catastrophic | No |
| 1 hour retention | ~1% after compression | ~70% |
| 2 hour retention | Near zero | ~50% + all facts |
| File efficiency | 10x redundant | 1x + diffs |
| Effective session length | ~30 min then amnesia | Hours with continuity |

---

## Future Considerations

### Archival Memory (Tier 3+)

For truly infinite sessions spanning days, a fourth tier could provide:
- Vector database storage of all historical content
- Semantic search for retrieval when context seems relevant
- "Self-healing" when the model appears confused—search archive, inject relevant context

This is noted as a future enhancement. The core three-tier system with scratchpad handles 1-2+ hour sessions well, which covers the majority of real usage.

### Goal/Task Management

A separate system could track:
- Current objective
- Sub-tasks and progress
- Blocked items awaiting user input

This would integrate with Mobius but is architecturally separate—a "subroutine manager" that uses Mobius for memory but has its own goal-tracking logic.

### Cross-Session Persistence

Tier 2 (Session Facts) could persist to disk and reload on session start, carrying learned preferences and conventions across sessions. This transforms the agent from stateless to having genuine long-term memory of the project.

---

## Why "Mobius"?

The Möbius strip is a surface with only one side and one boundary—a loop that seems to have two sides but is actually continuous.

Mobius (the system) creates a similar illusion: what appears to be an infinite conversation is actually a carefully managed continuous loop where old content transforms into compressed knowledge, which informs new interactions, which generate new content, which transforms again.

The conversation never "ends" or "resets"—it flows continuously, with the past always present in transformed form.

---

## Summary

**The problem:** AI coding agents waste context on repeated file contents, then destroy information with catastrophic single-pass compression.

**The solution:** 
1. **Scratchpad**: Separate current file state from conversation history
2. **Tiered Memory**: Graduate old content through compression levels instead of single-pass destruction
3. **Content-Aware Retention**: Preserve decisions and solutions longer than routine exchanges
4. **Natural Boundaries**: Split at task completions, not arbitrary token counts

**The result:** Coding sessions that maintain continuity for hours instead of collapsing after 30 minutes.