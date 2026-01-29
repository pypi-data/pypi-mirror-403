# Mobius UI Architecture

## Overview

The `run_mobius.py` entry point provides a terminal-based chat interface using the Rich library. The architecture follows a clean separation: **CLI (Rich)** → **Agent (event streaming)** → **LiteLLM** → **Tools**, with history persisted to disk.

## Files Involved

### Entry Point
- **`run_mobius.py`** - Just imports and calls `main()` from cli

### CLI Layer (`cli/`)
- **`cli/main.py`** - Main terminal UI using Rich library (rendering, input handling, slash commands)
- **`cli/__init__.py`** - Empty

### Configuration
- **`config.py`** - Agent config (system prompt, tools list, model), language mappings, slash command definitions
- **`settings.py`** - `Settings` class for persisting user preferences (theme, show_diff) to `settings.json`
- **`themes/__init__.py`** - 9 color themes (One Dark, GitHub Dark, Dracula, Nord, Monokai, Gruvbox, Tokyo Night, Catppuccin, Minimal)

### Core Logic
- **`core/agent.py`** - The `Agent` class:
  - Event-based streaming architecture (`TextDelta`, `TextDone`, `ToolStart`, `ToolDone`)
  - Tool schema conversion from Python functions
  - Integration with `litellm` for LLM calls
  - Session management with `SessionHistory` + new `HistoryManager`
  - HUD building (focused files, file tree, stats)
  
- **`core/history.py`** - `SessionHistory` class:
  - Stores sessions in `~/.mobius/histories/`
  - Manages display messages + raw API messages
  - `list_sessions()` for session picker

### Tools
- **`tools/__init__.py`** - Re-exports tool functions
- **`tools/tools.py`** - The actual tool implementations (read_file, create_file, edit_file, etc.) + focus/unfocus for HUD

## Key Components in `cli/main.py`

### Rendering Functions
- `render_inline_diff()` - Renders unified diffs with syntax highlighting and red/green backgrounds
- `render_tool_call()` - Displays tool calls with formatting (special handling for `edit_file`)

### Main Loop
- `run_agent_loop()` - Streams agent responses, handling:
  - `text_delta` events (streaming text)
  - `text_done` events
  - `tool_done` events

### Slash Commands (`handle_slash_command()`)
- `/theme`, `/themes` - Theme management
- `/toggle-diff` - Toggle diff display
- `/sessions` - List sessions
- `/new` - New session
- `/load <id>` - Load session
- `/help` - Show help
- `/session` - Current session info

### Session Management
- `show_session_picker()` - On startup, shows recent sessions in a table
- `load_and_display_chat_history()` - Renders history when loading a session

### Input Handling
- `get_multiline_input()` - Handles multi-line input with:
  - Backslash continuation (`\`)
  - Triple-backtick code blocks

## Data Flow

```
User Input
    ↓
cli/main.py (Rich UI)
    ↓
core/agent.py (Agent.stream())
    ↓
litellm (LLM API)
    ↓
Tool Calls → tools/tools.py
    ↓
Events yielded back to CLI
    ↓
Rendered output
```

## Persistence

- Sessions stored in `~/.mobius/histories/` as JSON files
- Settings stored in `settings.json` in project root
- Two history systems:
  - Legacy `SessionHistory` for backward compatibility
  - New `HistoryManager` with context management strategies
