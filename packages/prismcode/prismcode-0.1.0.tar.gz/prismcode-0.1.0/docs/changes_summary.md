# Recent Changes Summary

## Quick Start

```bash
python run_web.py
# Open http://localhost:5000
```

---

## 1. Session-Based Focus via Signella

Focus is now stored in Signella (disk cache) and scoped per session.

**Try it:**
```
/focus run_web.py
/focus static/js/app.js
```

The focus bar appears above the input. Click ▶ to expand, × to unfocus.

**Files changed:**
- `tools/tools.py` - focus/unfocus use Signella
- `core/agent.py` - publishes session ID, reads focus from Signella

---

## 2. Queue & Interrupt

You can now queue messages and interrupt mid-generation.

**Try it:**
1. Send a message that takes a while
2. Type new message, press **Enter** → queues it
3. Press **Enter again** → interrupts and sends new message

**Files changed:**
- `run_web.py` - cancel handler, queued message processing
- `static/js/app.js` - queue/interrupt logic in handleSubmit

---

## 3. Tool Streaming Progress

UI now shows progress while tool arguments stream (no more frozen UI).

**Try it:**
```
Create a Python file with 200 lines demonstrating various features
```

Watch the activity indicator:
- "Preparing create_file... 2.5kb"
- "Preparing create_file... 8.3kb"  
- "Executing create_file..."

**Files changed:**
- `core/agent.py` - new `ToolProgress` event
- `run_web.py` - emits `tool_progress` socket event
- `static/js/app.js` - `handleToolProgress()` updates activity

---

## 4. Sleek UI Redesign

Complete CSS overhaul - dark futuristic theme with purple accents.

**Features:**
- Smooth animations
- Streaming cursor blink
- Tool execution pulse
- Mobile responsive

**Files changed:**
- `static/css/style.css` - complete rewrite

---

## 5. Expandable Focus Bar

Shows focused files with line counts.

**Collapsed:** `📌 2 files  1.2k lines  [▶]`

**Expanded:** Each file with path, lines, and × button

**Files changed:**
- `templates/index.html` - added focus-bar div
- `static/js/app.js` - loadFocusedFiles(), updateFocusBar()
- `static/css/style.css` - focus bar styles
- `run_web.py` - /api/focused-files endpoint, /focus /unfocus commands

---

## Event Flow

```
User sends message
    ↓
[agent_start]    → "Sending..."
    ↓
[agent_delta]    → "Generating..." + streaming text
    ↓
[tool_progress]  → "Preparing create_file... 5kb"
[tool_progress]  → "Preparing create_file... 15kb"
    ↓
[tool_start]     → "Executing create_file..."
    ↓
[tool_done]      → Shows result in chat
    ↓
[agent_done]     → Complete, ready for next message
```

## Additional Fix: Tool Done Activity Gap

**Problem**: After a tool completed, the UI would show nothing for ~2 seconds while the LLM made its second API call to process the tool result.

**Solution**: After `handleToolDone`, show 'Thinking...' instead of hiding activity. This correctly reflects that the LLM is processing.

**Timeline of UI activity states**:
1. User sends → 'Sending message'
2. agent_start → 'Thinking...' (waiting for first token)
3. agent_delta → 'Generating response' + token count
4. tool_progress → 'Preparing create_file... 0.5kb'
5. tool_start → 'Executing create_file...'
6. tool_done → 'Thinking...' (LLM processing tool result - THIS WAS THE FIX)
7. agent_delta → 'Generating response' + token count
8. agent_done → Hide activity

