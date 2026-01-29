# Plan: Fix Tab Animations and Tool Rendering on Reload

## Problem 1: Tab Animations Stop When Switching Projects

### Description
When switching to a different project and then coming back, tab animations (processing shimmer, needs-attention glow) stop working even if the agent is still actively running in that tab.

### Root Cause
When `setProject()` is called in workspace.js:
1. Current project's tab state is saved
2. All DOM instances are cleared and removed
3. Fresh tabs are rendered for the restored project
4. But the CSS classes (`processing`, `needs-attention`) are not reapplied
5. Socket handlers add classes by session ID, but the newly rendered tabs start fresh

### Files Involved
```
static/workspace/js/core/workspace.js    # setProject(), tab rendering, socket handlers
static/workspace/js/components/chat.js   # isProcessing state, socket handlers
static/workspace/css/tabs.css            # Animation CSS classes
```

### Focus Command
```
unfocus (clear all)
focus static/workspace/js/core/workspace.js
focus static/workspace/js/components/chat.js
focus static/workspace/css/tabs.css
```

### Solution Approach

1. **Store processing state in tab config**
   - When a tab starts processing, save `isProcessing: true` in the tab's config object
   - When processing ends, set `isProcessing: false`

2. **Restore animation classes on render**
   - In `renderRegion()` or when mounting tabs, check `tab.config.isProcessing`
   - If true, add the `processing` class to the tab button

3. **Sync chat component state with tab config**
   - When chat's `isProcessing` changes, update the parent tab config
   - When chat component is re-mounted, read from config to restore state

4. **Handle needs-attention similarly**
   - Store `needsAttention: true` in tab config when agent completes on inactive tab
   - Restore the class when tab is rendered

### Checklist
- [x] Add `isProcessing` and `needsAttention` to tab config schema
- [x] Update `setTabProcessing()` to also save to tab config
- [x] Update `setTabNeedsAttention()` to also save to tab config  
- [x] Update `renderRegion()` to apply classes based on config
- [ ] Test: Start agent, switch project, switch back - animation should continue
- [ ] Test: Agent finishes on background tab, switch project, switch back - glow should remain

---

## Problem 2: Tool Outputs Look Different After Session Reload

### Description
During live sessions, tools like `edit_file` show rich diffs and `bash` shows mini-terminals. After reloading the session (or page refresh), those same tools show basic collapsed messages with no rich content.

### Root Cause
Two different rendering paths:
1. **Live**: `onToolDone()` receives full data (old_content, new_content, file_path) and calls `renderDiff()` / `renderBashResult()`
2. **History**: `loadHistory()` only gets basic message info and calls `addToolMessage(tool_name, '')` with no rich data

The session history API doesn't return the full tool arguments/results needed to reconstruct rich views.

### Files Involved
```
static/workspace/js/components/chat.js   # loadHistory(), onToolDone(), rendering methods
run_web.py                               # /api/load-session, /api/current-session endpoints
core/history.py                          # Session storage, what gets persisted
core/context_management/ground_truth.py  # HistoryManager, Entry structure
```

### Focus Command
```
unfocus (clear all)
focus static/workspace/js/components/chat.js
focus run_web.py
focus core/history.py
focus core/context_management/ground_truth.py
```

### Solution Approach

1. **Ensure tool data is stored in history**
   - Check what `HistoryManager.add_tool_result()` stores in `meta`
   - Verify `tool_args` is being saved (it should be based on agent.py)

2. **Update API to return rich tool data**
   - In `/api/load-session` and `/api/current-session`, include tool args in the response
   - Structure: `{ role: 'tool', tool_name: '...', tool_args: {...}, content: '...' }`

3. **Update loadHistory() to render rich tools**
   - Parse the tool_args from history
   - For `edit_file`: if has `old_str` and `new_str`, call `renderDiff()`
   - For `bash`: if has `command`, call `renderBashResult()`
   - Otherwise fall back to basic display

4. **Match the data structure between live and history**
   - Live `onToolDone()` receives: `{ name, args, result, old_content, new_content, ... }`
   - History sends lightweight version to avoid latency

5. **Optimization: Keep payloads small**
   - For `bash`: only send `command` (small), `content` already has output
   - For `edit_file`: send `file_path`, `old_lines`, `new_lines` (not full content)
   - For other tools: send full args (they're small)
   - Result: Fast session loading, rich bash terminals, meaningful edit summaries

### Checklist
- [x] Verify ground_truth.py stores tool_args in Entry.meta
- [x] Update run_web.py API endpoints to include tool_args in history response
- [x] Update chat.js `loadHistory()` to detect and render rich tools
- [x] Create helper method to unify live vs history tool rendering
- [x] Optimize: Only send small tool_args to avoid latency
- [ ] Test: Create session with edit_file, reload page, summary should appear
- [ ] Test: Create session with bash command, reload page, terminal should appear

---

## Implementation Order

1. **Problem 1 first** - simpler, self-contained in frontend
2. **Problem 2 second** - requires backend + frontend changes

## Post-Implementation
- [ ] Test both fixes together
- [ ] Verify no performance regression on large histories
- [ ] Update CLAUDE.md if any architectural patterns changed
