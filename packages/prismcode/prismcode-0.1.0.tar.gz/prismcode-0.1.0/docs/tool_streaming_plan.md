# Tool Call Streaming Progress - Implementation Plan

## Prompt to Self
You are implementing tool call streaming progress. Follow this plan step by step, checking off items as you complete them. Keep this file in focus at all times. Focus/unfocus other files as indicated in each section. Be methodical - complete each section fully before moving to the next.

---

## Problem
When the LLM streams a tool call (especially large ones like `create_file` with 2000 lines), the UI freezes with no indication that anything is happening. Users can't tell if the system crashed or is working.

## Solution
Add a new `ToolProgress` event that streams during tool argument accumulation, allowing any UI to show real-time progress.

---

## Phase 1: Backend - Core Agent Events
**Focus**: `core/agent.py`
**Unfocus**: all others

### Tasks
- [x] 1.1 Add new `ToolProgress` dataclass event:
  ```python
  @dataclass
  class ToolProgress(Event):
      """Tool call arguments streaming."""
      type: str = "tool_progress"
      name: str = ""
      index: int = 0
      bytes_received: int = 0
  ```

- [x] 1.2 In `stream()` method, emit `ToolProgress` when tool arguments are received:
  - Track when tool name is first seen
  - Emit `ToolProgress` on each argument chunk with cumulative byte count
  - Only emit every ~500 bytes or every chunk (whichever is simpler) to avoid flooding

- [x] 1.3 Export `ToolProgress` in module `__init__` if needed (not needed - events are accessed via agent.py directly)

---

## Phase 2: Web Backend - Socket Events  
**Focus**: `run_web.py`
**Unfocus**: `core/agent.py`

### Tasks
- [x] 2.1 Handle `ToolProgress` event in the streaming loop
- [x] 2.2 Emit socket event `tool_progress` with: `{name, index, bytes_received}`

---

## Phase 3: Web Frontend - JavaScript
**Focus**: `static/js/app.js`
**Unfocus**: `run_web.py`

### Tasks
- [x] 3.1 Add state variables:
  - `this.currentToolProgress = null` - tracks tool being prepared
  - `this.lastActivityTime = Date.now()` - for activity pulse

- [x] 3.2 Add socket handler for `tool_progress`:
  ```javascript
  this.socket.on('tool_progress', (data) => this.handleToolProgress(data));
  ```

- [x] 3.3 Implement `handleToolProgress(data)`:
  - Update activity indicator: "Preparing {name}... {bytes}kb"
  - Trigger activity pulse animation

- [x] 3.4 Update `handleToolStart` to show "Executing {name}..."

- [x] 3.5 Add activity pulse mechanism:
  - Track `this.activityPulseInterval`
  - Visual pulse every time tokens received
  - Different animation for "inference" vs "executing"

---

## Phase 4: Web Frontend - CSS Animations
**Focus**: `static/css/style.css`
**Unfocus**: `static/js/app.js`

### Tasks
- [ ] 4.1 Add `.activity-inference` class - pulsing animation for token streaming
- [ ] 4.2 Add `.activity-executing` class - different animation for tool execution
- [ ] 4.3 Add token counter animation (number ticking up)
- [ ] 4.4 Keep animations subtle but clearly visible

---

## Phase 5: Testing & Polish
**Focus**: `run_web.py`, `static/js/app.js`
**Unfocus**: CSS

### Tasks
- [ ] 5.1 Test with a large file creation to verify progress shows
- [ ] 5.2 Test rapid tool calls to ensure no UI glitches
- [ ] 5.3 Verify activity indicator clears properly after completion
- [ ] 5.4 Test cancel/interrupt during tool streaming

---

## Event Flow Summary

```
User sends message
    ↓
[agent_start] → UI: "Sending..."
    ↓
[agent_delta] → UI: "Generating..." + token count + inference animation
    ↓
[tool_progress] → UI: "Preparing create_file... 5kb" + progress animation
[tool_progress] → UI: "Preparing create_file... 15kb"
[tool_progress] → UI: "Preparing create_file... 28kb"
    ↓
[tool_start] → UI: "Executing create_file..." + executing animation
    ↓
[tool_done] → UI: "✓ create_file" (result shown)
    ↓
[agent_delta] → UI: back to inference animation if more text
    ↓
[agent_done] → UI: clear all indicators
```

---

## File Reference

| File | Purpose |
|------|---------|
| `core/agent.py` | Event dataclasses, streaming loop |
| `run_web.py` | Socket event emission |
| `static/js/app.js` | Frontend handlers, animations |
| `static/css/style.css` | Animation definitions |

---

## Current Status
**Phase**: 2
**Last Updated**: Phase 1 complete - ToolProgress event added to agent.py
