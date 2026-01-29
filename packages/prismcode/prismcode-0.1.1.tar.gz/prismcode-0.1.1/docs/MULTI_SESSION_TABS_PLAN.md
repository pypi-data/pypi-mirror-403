# Multi-Session Tabs Implementation Plan

## Overview

Enable multiple concurrent agent sessions in tabs, with proper session management.

**Behavior:**
- Each tab = one active agent/session
- Click session in sidebar → if already open, switch to that tab; otherwise load into current tab
- New tab button → creates new session
- Tabs show session title/preview
- Sessions sorted by most recent in sidebar

---

## Phase 1: Backend - Multi-Agent Support

**Goal:** Support multiple concurrent agents per client, routed by session ID.

**Files to focus:**
```
focus run_web.py
focus core/agent.py
focus core/signella.py
```

### Tasks:

- [x] Change `active_agents` from `{client_id: Agent}` to `{client_id: {session_id: Agent}}`
- [x] Update `get_agent(session_id)` to get/create agent for specific session
- [x] Add Signella tracking:
  - `tabs:{client_id}:active` = list of open session IDs
  - `tabs:{client_id}:current` = currently focused session ID
- [x] Update socket handlers to include `session_id` in messages
- [x] Route `send_message` to correct agent based on session_id
- [x] Route events back with session_id so UI knows which tab to update

---

## Phase 2: Socket Protocol Update

**Goal:** All messages include session_id for routing.

**Files to focus:**
```
focus run_web.py
focus static/workspace/js/components/chat.js
focus static/workspace/js/core/workspace.js
```

### Tasks:

- [x] Update `send_message` event to include `session_id`
- [x] Update all emitted events to include `session_id`:
  - `agent_start`, `agent_delta`, `agent_done`
  - `tool_start`, `tool_progress`, `tool_done`
  - `agent_error`, `agent_cancelled`
- [x] Client filters incoming events by session_id to update correct tab
- [ ] Add `switch_tab` event to notify server of focus change
- [ ] Add `open_session` event to load a session into current tab
- [ ] Add `close_tab` event to remove session from active list

---

## Phase 3: UI - Tab Bar Component

**Goal:** Add tab bar to main chat area showing open sessions.

**Files to focus:**
```
focus static/workspace/js/core/workspace.js
focus static/workspace/css/layout.css
focus static/workspace/css/tabs.css
```

### Tasks:

- [x] Create tab bar above chat area (already existed)
- [x] Each tab shows:
  - Session title (or first message preview)
  - Close button (X)
- [x] Active tab highlighted
- [x] Click tab → switch to that session
- [x] [+] button → create new session/tab
- [ ] Project color dot on tabs
- [ ] Tabs scrollable if too many

---

## Phase 4: UI - Chat Component Updates

**Goal:** Chat component handles multiple sessions, renders correct one.

**Files to focus:**
```
focus static/workspace/js/components/chat.js
focus static/workspace/js/core/events.js
```

### Tasks:

- [x] Chat component tracks `currentSessionId`
- [x] Maintains message history per session (or fetches on switch)
- [x] Only processes socket events matching `currentSessionId`
- [x] `switchSession(sessionId)` method to change active session
- [x] Emits `session-switched` event for other components

---

## Phase 5: Sidebar Session List Updates

**Goal:** Sidebar shows sessions, handles click to open/switch.

**Files to focus:**
```
focus static/workspace/js/components/tree.js
focus static/workspace/css/components/tree.css
```

### Tasks:

- [ ] Fetch sessions filtered by current project
- [ ] Sort by most recently used
- [ ] Show indicator if session is already open in a tab
- [x] Click behavior:
  - If session open in tab → switch to that tab
  - If not open → load into current tab
- [x] "New Session" button at top

---

## Phase 6: Session-Project Filtering

**Goal:** Sidebar only shows sessions for current project.

**Files to focus:**
```
focus run_web.py
focus static/workspace/js/components/tree.js
```

### Tasks:

- [x] Add `/api/sessions?project_id=X` filter parameter
- [x] Sidebar requests sessions for current project only
- [x] When project switches, refresh session list
- [x] New sessions automatically tagged with current project (via Agent.__init__)

---

## Data Model

### Signella Keys:
```
tabs:{client_id}:active = ["session-1", "session-2"]   # open tabs
tabs:{client_id}:current = "session-1"                  # focused tab

session:{id}:project_id = "agentech"                    # existing
focus:{id}:files = [...]                                # existing
```

### Socket Events (Updated):

**Client → Server:**
```javascript
send_message: { session_id, message }
switch_tab: { session_id }
open_session: { session_id }  // load into current tab
close_tab: { session_id }
new_tab: { project_id }       // create new session
```

**Server → Client:**
```javascript
agent_delta: { session_id, content, full_content }
agent_done: { session_id, content }
tool_start: { session_id, name, args }
tool_done: { session_id, name, args, result }
// ... all events include session_id
```

---

## Testing Checklist

- [x] Can open multiple tabs with different sessions
- [x] Messages route to correct session
- [x] Switching tabs shows correct history
- [x] Clicking open session in sidebar switches to its tab
- [x] Clicking closed session loads it in current tab
- [x] New tab creates new session
- [x] Close tab removes from active list
- [x] Sessions filtered by project in sidebar
- [x] Project switch refreshes session list
- [x] Two agents can work concurrently without interference

---

## Future Enhancements (Out of Scope)

- Tab reordering via drag
- Tab context menu (close others, close all)
- Split view (two chats side by side)
- Session search/filter in sidebar
- Pin tabs
