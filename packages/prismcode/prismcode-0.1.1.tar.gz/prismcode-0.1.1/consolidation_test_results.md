# Consolidation Strategy Test Results

**Session**: `20260121_171256_7f44c4.gt.json`

**Initial entries**: 92

**Initial tokens** (estimated): 137,354


## Sample of Original History

### First 5 entries:

0. **USER**: hi

1. **ASSISTANT**: Hello! I'm a coding assistant that can help you work with files and code. I can:

- Read, create, edit, and delete files
- List directory contents
- Rename/move files
- Help with coding tasks

What wo...

2. **USER**: read CLAUDE.md

3. **ASSISTANT**: [Tool calls: read_file]

4. **TOOL**: # Mobius Project Overview

## 1. Core Concept

Mobius is a terminal-based AI coding assistant that streams responses and executes file operations through tool calls. It wraps LLM API calls (via LiteLL...


### Last 5 entries:

87. **TOOL**: #!/usr/bin/env python3
"""
Fancy Textual TUI for Mobius agent.
Streaming text, Escape to cancel, rich formatting, multiple themes.
"""
from textual.app import App, ComposeResult
from textual.container...

88. **ASSISTANT**: [Tool calls: edit_file]

89. **TOOL**: No match found for the specified text (best similarity: 19%).

90. **USER**: what were we tring to accomplish?

91. **ASSISTANT**: We were trying to fix the issue where **Markdown formatting is not applied during streaming responses**. 

## The Problem
Currently, when the agent streams its response (during the `text_delta` events...


---

## Test 1: RollingGist Strategy

**Settings**: budget=137,354, threshold=0.5, compress_ratio=0.2

**Should consolidate?**: True

**Consolidated**: True

**Entries replaced**: 17

**Tokens before**: 137,354

**Tokens after**: 103,825

**Tokens saved**: 33,529

**Compression ratio**: 1.32x


**Gist created**:
```
[MOCK GIST] Summarized ~462 lines of conversation history.
```


### History after consolidation (first 5 entries):

0. [GIST] **USER**: [Conversation gist]
[MOCK GIST] Summarized ~462 lines of conversation history.

1. **ASSISTANT**: Now I can see the issue! Looking at the code, I can identify why Markdown formatting isn't being applied during streaming. Let me analyze the relevant sections:

## The Problem

In the `_process_messa...

2. **USER**: fix it

3. **ASSISTANT**: [Tool calls: edit_file]

4. **TOOL**: No match found for the specified text (best similarity: 25%).


---

## Test 2: ContextAwareGist (Full Context)

**Settings**: consolidator_context=1.0 (full)

**Entries replaced**: 17

**Tokens saved**: 33,529

**Compression ratio**: 1.32x


---

## Test 3: ContextAwareGist (50% Context)

**Settings**: consolidator_context=0.5 (recent half)

**Entries replaced**: 17

**Tokens saved**: 33,529

**Compression ratio**: 1.32x


---

## Test 4: Multiple Consolidations (RollingGist)

**Target budget**: 68,677 tokens (50% of original)

**Consolidation rounds**: 4

**Total tokens saved**: 92,774

**Final entries**: 30

**Final tokens**: 44,580


### Final history structure:

0. 🗜️ [GIST] **USER**: [Conversation gist]
[MOCK GIST] Summarized ~142 lines of conversation history.

1. **ASSISTANT**: [Tool calls: edit_file]

2. **TOOL**: No match found for the specified text (best similarity: 70%).

Did you mean one of these?
          ...

3. **ASSISTANT**: [Tool calls: edit_file]

4. **TOOL**: No match found for the specified text (best similarity: 19%).

5. **ASSISTANT**: [Tool calls: edit_file]

6. **TOOL**: No match found for the specified text (best similarity: 78%).

Did you mean one of these?
          ...

7. **ASSISTANT**: [Tool calls: edit_file]

8. **TOOL**: No match found for the specified text (best similarity: 72%).

Did you mean one of these?
          ...

9. **ASSISTANT**: [Tool calls: edit_file]

... (20 more entries)


---

## Test 5: Sample Consolidator Prompt (ContextAwareGist)

```

You are consolidating old memories for an AI assistant.

## CURRENT WORKING MEMORY
This is what the assistant currently remembers (most recent at bottom):

ASSISTANT: Now I can see the current state of the file. Looking at the text_delta handler around lines 608-627, I can see it was already partially modified but needs to be completed. Let me find the exact current structure and fix it properly:ASSISTANT called tools: edit_file
TOOL (edit_file) [run_fancy.py]: No match found for the specified text (best similarity: 20%).
ASSISTANT: Let me search for the actual streaming assignment pattern in the current file:ASSISTANT called tools: read_file
TOOL (read_file) [run_fancy.py]: #!/usr/bin/env python3
"""
Fancy Textual TUI for Mobius agent.
Streaming text, Escape to cancel, rich formatting, multiple themes.
"""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Input, Header, Footer, ListView, ListItem, Label, TextArea
from textual.binding import Binding
from textual import work
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from rich.console import Group
from rich.markdown import Markdown
from core.agent import Agent
from core.history import list_sessions
from themes import THEMES
from settings import Settings
from config import LANG_MAP, AGENT_CONFIG, SLASH_COMMANDS

def generate_css(theme: dict) -> str:
    """Generate theme-compliant CSS from theme configuration."""
    return f"""
Screen {{
    background: {theme['screen_bg']};
}}

#main {{
    width: 100%;
    height: 100%;
}}

#chat-list {{
    width: 100%;
    height: 1fr;
    border: round {theme['chat_border']};
    background: {theme['chat_bg']};
    scrollbar-size: 1 1;
    scrollbar-color: {theme['scrollbar_color']};
    scrollbar-background: {theme['scrollbar_bg']};
}}

ListView > ListItem {{
    padding: 0 1;
    border: none;
    background: transparent;
}}
#input-row {{
    width: 100%;
    height: 1;
    margin-top: 0;
    padding: 0 1;
}}

#prompt {{
    width: 2;
    height: 1;
    content-align: right middle;
    color: {theme['user_color']};
    text-style: bold;
}}

#input {{
    width: 1fr;
    height: 3;
    max-height: 10;
    border: none;
    background: {theme['input_bg']};
    scrollbar-size: 0 1;
    padding: 0;
}}

#input:focus {{
    border: none;
    background: {theme['input_focus_bg']};
}}

#autocomplete {{
    width: 100%;
    max-heig

... [TRUNCATED] ...

led tools: read_file
TOOL (read_file) [run_fancy.py]: #!/usr/bin/env python3
"""
Fancy Textual TUI for Mobius agent.
Streaming text, Escape to cancel, rich formatting, multiple themes.
"""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Input, Header, Footer, ListView, ListItem, Label, TextArea
from textual.binding import Binding
from textual import work
from rich.text import Text
from rich.syntax import Syntax
from rich.panel import Panel
from rich.console import Group
from rich.markdown import Markdown
from core.agent import Agent
from core.history import list_sessions
from themes import THEMES
from settings import Settings
from config import LANG_MAP, AGENT_CONFIG, SLASH_COMMANDS

def generate_css(theme: dict) -> str:
    """Generate theme-compliant CSS from theme configuration."""
    return f"""
Screen {{
    background: {theme['screen_bg']};
}}

#main {{
    width: 100%;
    height: 100%;
}}

#chat-list {{
    width: 100%;
    height: 1fr;
    border: round {theme['chat_border']};
    background: {theme['chat_bg']};
    scrollbar-size: 1 1;
    scrollbar-color: {theme['scrollbar_color']};
    scrollbar-background: {theme['scrollbar_bg']};
}}

ListView > ListItem {{
    padding: 0 1;
    border: none;
    background: transparent;
}}
#input-row {{
    width: 100%;
    height: 1;
    margin-top: 0;
    padding: 0 1;
}}

#prompt {{
    width: 2;
    height: 1;
    content-align: right middle;
    color: {theme['user_color']};
    text-style: bold;
}}

#input {{
    width: 1fr;
    height: 3;
    max-height: 10;
    border: none;
    background: {theme['input_bg']};
    scrollbar-size: 0 1;
    padding: 0;
}}

#input:focus {{
    border: none;
    background: {theme['input_focus_bg']};
}}

#autocomplete {{
    width: 100%;
    max-height: 8;
    background: {theme['input_bg']};
    border: round {theme['chat_border']};
    padding: 1;
    margin: 0 1;
    display: none;
}}

#autocomplete.show {{
    display: block;
... [truncated, 51891 chars]


## GUIDELINES
1. PRESERVE details that relate to the current task or recent conversation
2. PRESERVE any errors, blockers, or important decisions
3. COMPRESS or OMIT details about work that seems finished/irrelevant
4. Keep file paths and function names when they might be referenced again
5. Write in past tense as a summary of what happened

## OUTPUT
Write a concise gist that captures the essential information:

```
