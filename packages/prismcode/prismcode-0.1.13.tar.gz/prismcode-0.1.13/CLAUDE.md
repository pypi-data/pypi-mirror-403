# Mobius Project Overview

## 1. Core Concept

Mobius is an AI coding assistant that streams responses and executes file operations through tool calls. It wraps LLM API calls (via LiteLLM) with a modern web workspace interface supporting multi-project workflows.

- **Web UI** (`run_web.py`) - Flask + SocketIO real-time interface with session management, tool animations, and streaming responses
- **Modern Workspace** - Component-based UI with project tabs, focus panels, and real-time collaboration features
- **Multi-Project Support** - Local and SSH projects with unified filesystem abstraction

Think of it as a local Claude Code-style interface with dependency-aware context management and full project workflow support.

## 2. Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                   Modern Web Browser                        │
│               (Workspace UI - ES Modules)                   │
│   ┌─────────────┬─────────────┬─────────────┬─────────────┐ │
│   │Project Tabs │    Chat     │   Focus     │  Terminal   │ │
│   │(Toolbar)    │(Components) │   Panel     │  (Future)   │ │
│   └─────────────┴─────────────┴─────────────┴─────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ SocketIO (Real-time)
┌─────────────────────────▼───────────────────────────────────┐
│                   Flask Server (run_web.py)                 │
│         Multi-Project Sessions, Streaming, APIs             │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │Project Mgmt │Session Mgmt │  LLM Config │Tool Display │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    Agent (core/agent.py)                    │
│         LLM Streaming, Tool Dispatch, HUD Injection         │
└──────┬─────────────────┬─────────────────┬──────────────────┘
       │                 │                 │
┌──────▼─────────┐ ┌─────▼─────────┐ ┌─────▼─────────────────┐
│Tools Layer     │ │History Manager│ │FileSystem Abstraction│
│• File ops      │ │• Ground truth │ │• Local projects       │
│• Prism tools   │ │• Working hist │ │• SSH projects         │
│• Focus mgmt    │ │• Projections  │ │• Unified interface    │
└────────────────┘ └───────────────┘ └───────────────────────┘
```

**Layers:**
- **Core Engine** - Agent loop, session history, file editing (provider-agnostic)
- **Tools Layer** - File ops + Prism dependency tools exposed to the LLM
- **Web UI Layer** - Flask + SocketIO real-time interface
- **HUD Layer** - Focused files + file tree injected into context
- **Prism Layer** - Dependency analysis, entry point discovery, smart focusing

## 3. File Reference Tables

### Core Engine

| File | Purpose |
|------|---------|
| `core/agent.py` | Main agent class - LLM streaming, tool dispatch, HUD injection, session management |
| `core/context_management/ground_truth.py` | Two-layer history: ground truth (append-only) + working history (compactable) with projections |
| `core/context_management/query.py` | History slicing by tokens, percentage, or count for gist generation |
| `core/context_management/tokens.py` | Token counting (tiktoken or char-based) with model profiles |
| `core/context_management/strategies/` | Consolidation strategies (RollingGist, ContextAwareGist) |
| `core/history.py` | Legacy session persistence to `~/.mobius/histories/` |
| `core/code_edit.py` | File editor with layered fuzzy matching (exact → whitespace → fuzzy) |
| `core/signella.py` | Cross-process shared state via diskcache - focused files, session state |

### Tools Layer

| File | Purpose |
|------|---------|
| `tools/tools.py` | File ops: `read_file`, `create_file`, `edit_file`, `rename_file`, `delete_file`, `ls`, `bash` |
| `tools/tools.py` | Focus ops: `focus`, `unfocus`, `list_focused` |
| `tools/prism_tools.py` | Dependency tools: `find_entry_points`, `get_dependency_info`, `focus_dependencies`, `add_entry_point`, `remove_entry_point`, `list_entry_points`, `trace_entry_point`, `rescan_project` |

### Prism Layer (Dependency Analysis)

| File | Purpose |
|------|---------|
| `prism/session.py` | Main controller - scanning, parsing, graph building for a project |
| `prism/graph.py` | Dependency graph with BFS tracing, orphan detection, entry point suggestions |
| `prism/scanner.py` | File discovery - finds .py, .html, .js, .css, detects templates/static folders |
| `prism/parsers.py` | AST parser for Python imports, regex parsers for HTML/JS/CSS references |
| `prism/models.py` | Data classes: Node, Edge, EntryPoint, SnapshotConfig |
| `prism/snapshot.py` | Generates formatted dependency snapshots for LLM context |

### Web UI Layer

#### Server Layer
| File | Purpose |
|------|---------|
| `run_web.py` | Flask + SocketIO server - Entry point and blueprint registration |
| `routes/__init__.py` | Blueprint package setup |
| `routes/sessions.py` | Session management routes |
| `routes/projects.py` | Project CRUD routes |
| `routes/ssh.py` | SSH connection routes |
| `routes/llm.py` | LLM configuration routes |
| `routes/shared.py` | Shared agent state and utilities |
| `routes/socket_handlers.py` | Real-time SocketIO event handlers |

#### Modern Workspace UI (Primary Interface)
| File | Purpose |
|------|---------|
| `templates/workspace.html` | Modern workspace template with ES modules |
| `static/workspace/js/app.js` | Main application entry point |
| `static/workspace/js/core/workspace.js` | Workspace management and layout system |
| `static/workspace/js/core/events.js` | Event bus for component communication |
| `static/workspace/js/components/chat.js` | Chat component with streaming |
| `static/workspace/js/components/tree.js` | File tree and session management |
| `static/workspace/js/components/focus.js` | Focus panel component |
| `static/workspace/js/components/project-bar.js` | Project switching tabs |
| `static/workspace/js/components/preferences/` | Settings modal system |

#### CSS Architecture (Component-Based)
| File | Purpose |
|------|---------|
| `static/workspace/css/index.css` | Master CSS entry point (imports all modules) |
| `static/workspace/css/variables.css` | CSS custom properties and theming |
| `static/workspace/css/base.css` | Typography, buttons, base components |
| `static/workspace/css/layout.css` | Grid layout and responsive design |
| `static/workspace/css/components/chat.css` | Chat messages, streaming, tools |
| `static/workspace/css/components/toolbar.css` | Top toolbar with project tabs |
| `static/workspace/css/components/preferences-index.css` | Master import for modular preferences CSS |
| `static/workspace/css/components/preferences-*.css` | Modular: base, browser, ssh, projects-pane, llm |
| `static/workspace/css/components/focus.css` | Focus panel styling |
| `static/workspace/css/components/tree.css` | File tree and session management |
| `static/workspace/css/components/project-bar.css` | Project switching tabs |
| `static/workspace/css/components/terminal.css` | Terminal component styling |
| `static/workspace/css/components/settings.css` | Settings component styling |

#### Legacy Interface (Deprecated)
| File | Purpose |
|------|---------|
| `templates/index.html` | Legacy chat interface template |
| `static/js/app.js` | Legacy JavaScript (single file) |
| `static/css/style.css` | Legacy dark theme styles |
| `static/css/highlight.css` | Code syntax highlighting (shared) |

### Project & Configuration System

| File | Purpose |
|------|---------|
| `config.py` | Central config: tool list, system prompt, model detection, slash commands |
| `settings.py` | User preferences (theme, show_diff) persisted to `settings.json` |
| `core/project.py` | Project data model (local/SSH projects) |
| `core/project_manager.py` | CRUD operations for projects and SSH profiles |
| `core/llm_config.py` | LLM provider management (Anthropic, OpenAI, Google, Groq, Ollama, + custom LiteLLM providers) |
| `core/filesystem.py` | Unified filesystem abstraction (local + SSH) |

## 4. Data Flow

```
Workspace Components (ES Modules)        Server (run_web.py)
      │                                         │
      │──── send_message (project context) ───▶│
      │──── project_switch ────────────────────▶│
      │──── session_load ──────────────────────▶│
      │                                         │
      │                                    ┌────▼────┐
      │                                    │  Agent  │
      │                                    │.stream()│
      │                                    └────┬────┘
      │                                         │
      │                                    ┌────▼────┐
      │                                    │ LiteLLM │
      │                                    │(Dynamic)│
      │                                    └────┬────┘
      │                                         │
      │◀──── agent_delta (streaming) ──────────│
      │◀──── tool_progress (args) ──────────────│
      │◀──── tool_start/done ───────────────────│──┐
      │◀──── focused_files_updated ─────────────│  │ Loop until
      │◀──── title_updated ─────────────────────│  │ complete
      │◀──── agent_complete ────────────────────│  │
      │                                         │  │
      │                                    ┌────┴──▼──┐
      │                                    │FileSystem│
      │                                    │Local/SSH │
      │                                    └──────────┘
```

## 5. Key Concepts

**Event-Driven Streaming** - Agent yields typed events (`TextDelta`, `TextDone`, `ToolStart`, `ToolDone`, `ToolProgress`) enabling incremental UI updates during generation.

**Layered Fuzzy Matching** - `FileEditor.str_replace()` tries: exact → whitespace-normalized → fuzzy (0.8 threshold). On failure, returns candidate matches to help LLM self-correct.

**Tool Cleanup** - `cleanup_incomplete_tool_calls()` handles cancelled generations by adding "[Cancelled by user]" results to maintain valid message history.

**HUD (Heads-Up Display)** - `Agent._build_hud()` injects ephemeral context into every LLM call:
- Focused file contents (from Signella)
- Git-aware file tree
- Context stats (entries, tokens, files)

**Signella** - Cross-process shared memory via diskcache (`/tmp/signella`). Stores focused files, entry points, session state. Enables state sharing between processes.

**Modern UI Features**:
- Component-based architecture with ES modules
- Real-time project switching with color-coded tabs
- Focus panel for file management and context visualization
- Tool animations: shimmer (streaming) → glow (executing) → dot (done)
- Mobile-responsive with overlay panels
- Tab system with attention indicators and processing states

**Smart Tool Retention** - Default projection keeps first + last file reads per file, all edits, truncates long bash output. Balances context preservation with token efficiency.

## 6. History Management System

### Two-Layer Architecture

```
HistoryManager
├── GroundTruth (append-only, never modified)
│   • Full fidelity record of everything
│   • Indexed by file_path, tool_name
│   • Source for future RAG/search
│
└── WorkingHistory (what LLM sees)
    • Compactable via gists
    • Projections filter before sending
```

### Projections (Composable Filters)

```python
from core.context_management import compose, dedupe_file_reads, smart_tool_retention

# Default projection
projection = smart_tool_retention(max_file_reads=5, bash_truncate=10000)

# Or compose custom
projection = compose(
    dedupe_file_reads(),           # Only most recent read per file
    keep_recent_tool_results(30),  # Keep last 30 tool results
    truncate_tool_results(10000),  # Truncate long outputs
)
```

### Persistence

Saved to `~/.mobius/histories/{session_id}.gt.json`

## 7. Modern Workspace UI Architecture

### Component System (Web Components + ES Modules)

| Component | File | Purpose |
|-----------|------|---------|
| `<prism-chat>` | `components/chat.js` | Chat interface with streaming |
| `<prism-tree>` | `components/tree.js` | File tree and session management |
| `<prism-focus>` | `components/focus.js` | Right panel focus management |
| `<project-bar>` | `components/project-bar.js` | Project switching tabs |
| `<prism-preferences>` | `components/preferences/` | Settings modal system |
| `<prism-terminal>` | `components/terminal.js` | Terminal component (future) |

### SocketIO Events (Enhanced)

| Event | Direction | Purpose |
|-------|-----------|---------|
| `send_message` | Client → Server | User sends message with session/project context |
| `join_session` | Client → Server | Subscribe to session room for multi-tab support |
| `cancel` | Client → Server | Stop generation |
| `agent_start` | Server → Client | Generation starting (with session_id) |
| `agent_delta` | Server → Client | Streaming text chunk |
| `agent_complete` | Server → Client | Generation complete (triggers notifications) |
| `tool_progress` | Server → Client | Tool args streaming with byte counts |
| `tool_start/done` | Server → Client | Tool execution with rich metadata |
| `focused_files_updated` | Server → Client | Focus panel updates |
| `title_updated` | Server → Client | Session title generation |

### Advanced UI Features

- **Multi-Tab Sessions** - Each session in separate tab with state indicators
- **Project Context** - Color-coded project tabs with automatic switching
- **Real-Time Collaboration** - Multi-tab support with session rooms
- **Smart Notifications** - Browser notifications + tab attention indicators
- **Mobile Responsive** - Overlay panels on mobile with touch optimization
- **Focus System** - Visual file management with line counts and removal
- **Token Visualization** - Real-time context usage with breakdown charts
- **Modern Animations** - CSS-based with attention states and processing indicators

### CSS Architecture (Component-Based)

```
static/workspace/css/
├── variables.css       # CSS custom properties, project colors
├── base.css           # Typography, buttons, form elements
├── layout.css         # Grid system, responsive breakpoints
├── tabs.css           # Tab system with animations
└── components/        # Component-specific styles
    ├── chat.css       # Messages, streaming, tools, diffs
    ├── toolbar.css    # Project tabs, token bar, actions
    ├── tree.css       # File trees, session lists
    ├── focus.css      # Focus panel styling
    ├── preferences-index.css   # Master import (loads all below)
    │   ├── preferences-base.css        # Modal, overlay, forms, buttons
    │   ├── preferences-browser.css     # Folder browser, path input
    │   ├── preferences-ssh.css         # SSH forms, hosts, connections
    │   ├── preferences-projects-pane.css # Project cards, grids
    │   ├── preferences-projects.css    # Apple-style project cards
    │   └── preferences-llm.css         # LLM provider config
    └── ...
```

- **CSS Custom Properties** - Dynamic theming with project colors
- **Component Isolation** - Scoped styles for maintainability
- **Mobile-First Design** - Responsive with overlay panels
- **Modern CSS** - Grid, Flexbox, custom properties, animations
- **Modular Preferences** - Split into logical modules via @import

## 8. Prism Dependency Tools

### Available Tools

| Tool | Purpose |
|------|---------|
| `find_entry_points(top_n, include_tests)` | Rank files by dependency count |
| `get_dependency_info(file, depth, parents, frontend, max_tokens)` | Dry run - preview what would be focused |
| `focus_dependencies(file, depth, parents, frontend, max_tokens)` | Add file + deps to focus within token budget |
| `add_entry_point(file, label)` | Register named entry point |
| `remove_entry_point(file)` | Remove entry point |
| `list_entry_points()` | Show configured entry points |
| `trace_entry_point(file)` | BFS trace all connected files |
| `rescan_project()` | Re-scan after file changes |

### How It Works

1. `PrismSession` scans project, builds dependency graph
2. Parsers extract imports (Python AST), script/link tags (HTML regex), imports (JS/CSS)
3. Graph tracks forward (children) and reverse (parents) edges
4. `focus_dependencies` does BFS, adds files to Signella until token budget hit


# Read The Whole Damn File

When asked to look at, review, or analyze a file - read the ENTIRE thing. No exceptions.

**Why:** Partial reads miss helper functions, class attributes, edge cases, and error handling. This codebase follows "one script = one job" - if it's in the file, it's relevant.

**The Rule:** Use `read_file` with NO offset or limit. Read from line 1 to end. Yes it costs tokens. That's the correct tradeoff.


# Focus-First Development Strategy

You are a coding agent with access to a **focus system** - a mechanism that injects file contents into your context each turn without storing them in conversation history. This is fundamentally different from reading files into chat history, and you should leverage it strategically.

## Understanding the Focus System

**How it works:**
- Files added to focus are read and injected at the start of each turn
- When you edit a focused file, you automatically see the updated version next turn
- Focused files do NOT accumulate in conversation history
- You can focus/unfocus files to control your working context

**Why this matters:**
Traditional coding agents read files into history, edit them, read again, edit again - ending up with 20 copies of the same file polluting context. The focus system keeps your history clean. Your history contains only your reasoning and edits, while focus provides live file state.

---

## Phase 1: Project Mapping (Do This First for New Projects)

When starting work on a new or unfamiliar project, collaborate with the user to build a project map.

### Step 1: Identify Entry Points
Ask the user:
> "What's the main entry point for this project? (e.g., the file you run to start the app, the main script, the index file)"

### Step 2: Scan and Map
Once you have the entry point, offer to scan the codebase:
> "Would you like me to scan the codebase from this entry point and build a project map? This helps me understand how files connect and what each one does."

If yes:
1. Use `focus_dependencies` or equivalent to load the entry point and its dependency tree
2. Analyze the focused files to understand:
   - What each file does (one-line summary)
   - The data flow between files
   - Key abstractions and interfaces
   - External dependencies

### Step 3: Create or Update CLAUDE.md
Create/update a `CLAUDE.md` file in the project root with:

```markdown
# Project: [Name]

## Entry Points
- `[path/to/main.py]` - [what it does]

## Project Map

### Core Files
| File | Purpose | Connects To |
|------|---------|-------------|
| `path/to/file.py` | Brief description | `other_file.py`, `another.py` |

### Data Flow
[Describe how data moves through the system - what calls what, what depends on what]

### Key Abstractions
- **[AbstractionName]**: What it represents and where it's defined

## Common Tasks
- To run: `[command]`
- To test: `[command]`
- Config location: `[path]`
```

This map becomes your starting point for all future work on this project.

---

## Phase 2: The Wide-Then-Narrow Strategy

When tackling any task, follow this pattern:

### Step 1: Cast a Wide Net
Add as much relevant context as possible to focus. Start broad:
- Focus the entry point and its full dependency tree
- Or focus all files in a relevant directory
- Goal: Get maximum codebase visibility

### Step 2: Identify Relevant Files
With the full context visible, analyze which files actually matter for this specific task. **Say them out loud to the user:**
> "Looking at the codebase, the files relevant to this task are:
> - `core/auth.py` - handles the authentication logic we need to modify
> - `api/routes.py` - where the endpoint is defined
> - `models/user.py` - the User model we'll be updating
> 
> Does this look right? Any files I'm missing?"

### Step 3: Narrow the Focus
Once confirmed:
1. Unfocus everything
2. Re-focus only the identified relevant files

Now you have clean, targeted context for the actual work.

---

## Phase 3: Planning with Focus Manifests

For any non-trivial task, create a plan with explicit focus instructions.

### Plan Structure
Create plans in: `mobius_plans/[descriptive-name].md`

```markdown
# Plan: [Task Name]

## Overview
[1-2 sentence description of what we're building/fixing]

## Relevant Files
These files were identified as relevant to this task:
- `path/to/file1.py` - [why it's relevant]
- `path/to/file2.py` - [why it's relevant]

---

## Phase 1: [Phase Name]

### Focus for this phase
```
focus path/to/file1.py
focus path/to/file2.py
```

### Checklist
- [ ] Step one description
- [ ] Step two description
- [ ] Step three description

### Completion
When done, mark checklist complete and proceed to Phase 2.

---

## Phase 2: [Phase Name]

### Focus for this phase
```
focus path/to/file3.py
focus path/to/file4.py
```

### Checklist
- [ ] Step one description
- [ ] Step two description

---

## Post-Implementation
- [ ] Test all changes
- [ ] Update CLAUDE.md if architecture changed
- [ ] Clean up any temporary files
```

### After Creating the Plan
1. Add the plan file itself to focus
2. Work through each phase, following the focus instructions
3. Mark checklist items as you complete them
4. The plan in focus serves as persistent memory of progress

---

## Working Principles

### Never Read What's Already Focused
If a file is in focus, you already see its current state. Don't use read_file on focused files - it wastes history space.

### Edit Confidently
When you edit a focused file, trust that you'll see the result next turn. No need to read-after-write.

### Keep History for Reasoning
Your conversation history should contain:
- Your analysis and reasoning
- The edits you made (diffs)
- Discussions with the user
- Plan progress

NOT:
- Full file contents (that's what focus is for)
- Repeated reads of the same file

### Collaborate on Focus Decisions
When uncertain which files matter, ask:
> "I think these files are relevant: [list]. Should I focus on all of them, or do you want to narrow it down?"

### Update the Map
If you discover the project structure is different than documented, or you add new files, update CLAUDE.md so future sessions start with accurate context.

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| New project | Build project map first |
| Starting a task | Go wide (focus dependency tree) → identify relevant files → go narrow |
| Multi-phase work | Create plan in `mobius_plans/` with focus instructions per phase |
| After editing | Trust focus auto-updates, don't re-read |
| Lost context | Check CLAUDE.md, re-focus relevant files |
| Task complete | Mark plan checklist, update CLAUDE.md if needed |

---

## Example Collaboration Flow

**User:** "I need to add authentication to the API"

**You:** "I'll help with that. Let me first understand the current structure. What's the main entry point for the API?"

**User:** "run_api.py"

**You:** "Got it. I'll focus on run_api.py and its dependencies to map out the codebase."
*[focuses dependency tree]*

**You:** "Looking at the codebase, I can see the API structure. The files relevant to adding authentication are:
- `api/routes.py` - where endpoints are defined
- `api/middleware.py` - where we'd add auth middleware  
- `core/config.py` - for auth configuration
- `models/user.py` - exists but needs auth fields

Does this look complete? I'll unfocus the rest and create an implementation plan."

**User:** "Also need to touch the database migrations"

**You:** "Good catch. I'll include `db/migrations/` as well. Let me unfocus everything and refocus just these files, then write up a phased plan in `mobius_plans/add-authentication.md`."