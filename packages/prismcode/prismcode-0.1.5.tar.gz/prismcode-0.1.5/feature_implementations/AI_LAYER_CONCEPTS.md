# AI Layer Concepts for zdeps2

A high-level overview of the semantic intelligence layer we're building on top of the dependency viewer.

---

## The Core Problem

AI models have limited context windows. When exploring a codebase, they either:
- Read too much (expensive, slow, loses focus)
- Read too little (misses important context)

**zdeps2 already solves the structural problem** - it shows you which files connect to which. But it doesn't tell you *what* those files do. You see `auth_middleware.py | 120 lines` but you don't know if that's relevant to your task without opening it.

---

## The Solution: A Semantic Map

We add an "understanding layer" on top of the structural layer.

Instead of just seeing file names and line counts, you see:
```
auth_middleware.py | 120 lines | "Validates JWT tokens and enforces role permissions"
```

That one sentence lets you decide if you need to read the file without actually reading it.

---

## Two Layers of Information

### Layer 1: The Base Map (Auto-Generated)
- Tier 1 summaries for every file in the codebase
- One sentence each: what does this file do?
- Generated in batch, relatively cheap
- The foundation that makes navigation possible

### Layer 2: Notes (Human + AI Added)
- Deeper observations layered on top of the base map
- "This timeout is 30s because of the legacy system"
- "Watch out: this function has a subtle race condition"
- Accumulated over time as you work with the codebase
- Could be added by you manually or by an AI during analysis

---

## The Tiered Analysis System

Not all understanding needs to be deep. We use resolution levels like video quality:

- **Tier 1 (Index Card)**: One sentence. "What is this file?"
- **Tier 2 (Wiki Page)**: A paragraph with key functions listed. "How does it work?"
- **Tier 3 (Deep Dive)**: Detailed walkthrough. "Explain the logic step by step."

Higher tiers cost more tokens. You only pay for depth when you need it.

---

## Cost Awareness

Every analysis shows you the price before you commit:
- "Summarize this file at Tier 1: ~$0.002"
- "Summarize entire dependency tree (23 files): ~$0.05"

You can set budgets: "Summarize as much as possible for $0.10" and the system prioritizes intelligently.

---

## How It Connects to the Dependency Viewer

The existing dependency viewer is the navigation interface. We extend it:

1. **Current**: Click a file → see dependency tree with file names and line counts
2. **Extended**: Same tree, but each node also shows its Tier 1 summary if cached
3. **Actions**: Generate summaries for individual files or batch-generate for the whole tree
4. **Detail Panel**: Shows cached summaries and notes for the selected file

The structural view (what connects to what) and the semantic view (what does each thing do) live together.

---

## The AI Consumer Perspective

When an AI agent needs to understand your codebase:

1. **First**: Query the map - get Tier 1 summaries for all files
2. **Filter**: Based on the task, identify which 2-3 files actually matter
3. **Deep Dive**: Request Tier 2/3 analysis on just those files
4. **Read Code**: Only when actually editing, read the raw source

This dramatically reduces token usage while improving accuracy - the AI knows *where* to look before it looks.

---

## The Modular Architecture

Five independent pieces that combine:

1. **Estimator** - Calculates cost before any AI runs
2. **Prompts** - Template strings for each tier level
3. **Client** - Thin wrapper around the Claude API
4. **Cache** - Stores summaries and notes as JSON
5. **Orchestrator** - Connects the pieces together

Each piece works in isolation. You can test the estimator without API keys. You can edit prompts without touching code. The cache works without any AI at all.

These live in `zdeps2/core/ai/` - a dedicated subfolder to keep the AI logic separate from the existing analysis engine.

---

## Future: MCP Server

Eventually, zdeps2 becomes a tool that external AI systems can query:

- "What files handle authentication?" → Returns relevant files with summaries
- "Explain the timeout logic in auth.py" → Returns cached analysis or generates on-demand
- "Show me the dependency chain from main.py to database.py" → Returns structural + semantic info

The summaries and notes you build up become a knowledge base that any AI can tap into.

---

## Key Principles

1. **Map before territory** - Always see the overview before diving into code
2. **Pay for depth only when needed** - Tier 1 is cheap and covers everything; Tier 3 is expensive and targeted
3. **Accumulate knowledge** - Notes persist, so insights aren't lost
4. **Cost transparency** - Always know what you're spending before you spend it
5. **Modular construction** - Simple pieces that combine, not one complex system

---

*This document captures the concepts discussed. Implementation details to follow.*
