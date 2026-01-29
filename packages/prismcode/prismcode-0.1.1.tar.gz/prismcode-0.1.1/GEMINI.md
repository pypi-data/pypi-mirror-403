# Mobius Project Overview

## 1. Core Concept

Mobius is a terminal-based AI coding assistant that streams responses and executes file operations through tool calls. It wraps LLM API calls (via LiteLLM) with a rich Textual TUI, providing session persistence, theming, and real-time streaming with cancellation support. Think of it as a local Claude Code-style interface you can run in your terminal.

## 2. Architecture Summary

The project follows a clean three-layer architecture:

- **Core Engine** - Agent loop, session history, and file editing logic (provider-agnostic)
- **Tools Layer** - File operation functions exposed to the LLM as callable tools
- **TUI Layer** - Textual-based terminal interface handling rendering, input, and user interactions
- **Configuration** - Theme definitions, settings persistence, and agent config

## 3. File Reference Tables

### Core Engine

| File | Purpose |
|------|---------|
| `core/agent.py` | Main agent class - handles LLM streaming, tool dispatch loop, message history management, and session loading |
| `core/history.py` | Session persistence to `~/.mobius/histories/` - saves both display-friendly and raw API messages for lossless restoration |
| `core/code_edit.py` | File editor with layered fuzzy matching (exact → whitespace-normalized → fuzzy) for str_replace operations |
| `core/__init__.py` | Re-exports core classes |

### Tools Layer

| File | Purpose |
|------|---------|
| `tools/tools.py` | Six file operation tools: `read_file`, `create_file`, `edit_file`, `rename_file`, `delete_file`, `ls` - thin wrappers around FileEditor |
| `tools/__init__.py` | Re-exports tool functions |

### TUI Layer

| File | Purpose |
|------|---------|
| `run_fancy.py` | Main TUI application - handles chat rendering, slash commands, autocomplete, scroll management, theme switching, streaming display, and agent coordination |
| `run_mobius.py` | Simple entry point that delegates to CLI (appears to be for a separate CLI interface not shown in snapshot) |

### Configuration

| File | Purpose |
|------|---------|
| `themes/__init__.py` | 14 theme definitions (github-dark, dracula, nord, etc.) with full color configs for all UI elements including diff highlighting |
| `settings.py` | Persists user preferences (theme, show_diff toggle) to `settings.json` |
| `config.py` | Central config: tool list, system prompt, model selection, language mappings for syntax highlighting, slash command definitions |

## 4. Data Flow

```
User Input (TUI)
      │
      ▼
┌─────────────────┐
│  Slash Command? │──Yes──▶ Handle locally (theme, session, help)
└────────┬────────┘
         │ No
         ▼
┌─────────────────┐
│  Agent.stream() │ ◀────────────────────────────┐
└────────┬────────┘                              │
         │                                       │
         ▼                                       │
┌─────────────────┐                              │
│   LiteLLM API   │                              │
└────────┬────────┘                              │
         │                                       │
         ▼                                       │
┌─────────────────┐     ┌──────────────┐         │
│  Text Chunks    │────▶│ Stream to UI │         │
└─────────────────┘     └──────────────┘         │
         │                                       │
         ▼                                       │
┌─────────────────┐     ┌──────────────┐         │
│  Tool Calls?    │─Yes─▶│ Execute Tool │─────────┘
└────────┬────────┘     └──────────────┘  (result back to LLM)
         │ No
         ▼
┌─────────────────┐
│ Save to History │
└─────────────────┘
```

## 5. Key Concepts

**Event System** - The agent yields typed events (`TextDelta`, `TextDone`, `ToolStart`, `ToolDone`) rather than returning strings. This allows the TUI to update incrementally during streaming and show tool execution status.

**Dual Message Storage** - `SessionHistory` keeps two parallel lists: `messages` (display-friendly with timestamps) and `api_messages` (raw API format for lossless conversation restoration). This lets you reload a session and continue exactly where you left off.

**Layered Fuzzy Matching** - `FileEditor.str_replace()` tries three match strategies in order: exact match, whitespace-normalized match, then fuzzy match (SequenceMatcher with 0.8 threshold). On failure, it returns candidate matches to help the LLM self-correct.

**Tool Cleanup** - `cleanup_incomplete_tool_calls()` handles the case where the user cancels mid-generation. If the LLM emitted a tool_use block but never got a result, this adds a "[Cancelled by user]" result to keep the message history valid for the API.

**Theme-Driven CSS** - The TUI generates its Textual CSS dynamically from theme dicts via `generate_css()`. Theme switching regenerates and hot-reloads the CSS.

**Auto-scroll State Machine** - The scroll handling tracks `auto_scroll` and `user_scrolled_up` separately to avoid fighting with the user. Manual scroll up disables auto-scroll; only scrolling to the very bottom (or pressing End) re-enables it.


# Read The Whole Damn File

When you are asked to look at, review, analyze, or understand a file - you read the ENTIRE thing. No exceptions.

---

## Why This Rule Exists

AI coding assistants have a bad habit: when given a 500-line file, they'll read 100-200 lines and call it done. This is unacceptable.

This codebase is built on a simple principle:

- **One script = One job** - Each file is a self-contained module
- **Everything under ~2000 lines** - If it's in the file, it's relevant
- **No filler** - Every function, every class, every line exists for a reason

When you do a partial read, you WILL miss context. You'll miss:
- Helper functions that affect the code you're looking at
- Class attributes that determine behavior
- Edge cases handled elsewhere in the file
- Import patterns and dependencies
- Error handling that matters

**Partial reads = incomplete understanding = wrong conclusions.**

---

## The Rule

When reading any file for the first time, or when asked to analyze/review code:

1. **Use the Read tool with NO offset or limit parameters**
2. **Read from line 1 to the end**
3. **No shortcuts, no skimming, no "relevant sections only"**

Yes, this costs more tokens. Yes, it fills context faster. **This is the correct tradeoff.** A thorough read that catches real issues beats a quick skim that misses problems.

---

## When This Applies

- First time looking at any file
- When asked to "look at" or "check" code
- When reviewing for bugs or issues
- When trying to understand how something works
- Basically always, unless you've already read it recently in this session
