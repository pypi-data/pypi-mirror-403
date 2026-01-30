# Plan: Fix LLM Provider Management and Project Settings

## 🎯 MISSION: COMPLETE ALL FIXES AND TEST THOROUGHLY
**Directive:** Keep going until all plan is finished and tested. DON'T STOP UNTIL EVERYTHING CONFIRMED WORKING. Test thoroughly with bash tests.

## Overview
Fix issues with LLM provider configuration, real-time updates, and project management.

## Issues Completed ✓
- [x] **Issue #3: Inaccurate Token Counting**
  - Added `LiteLLMCounter` class using LiteLLM's built-in token counter
  - Fixed budget calculation to account for `max_tokens`: `budget = (context_window - max_tokens) * 0.85`
  - Updated Agent, prism_tools, and get_context_stats to use accurate counting
  - Test results: Counter now matches provider's actual token count (was 17% undercount)

## Issues Remaining

### **Issue #1: Can't Add Arbitrary LiteLLM Providers**
**Problem:** LLM providers floating menu only shows predefined providers. Should be able to add any LiteLLM-supported provider.

**Current State:**
- `core/llm_config.py` has hardcoded provider list
- UI only shows these predefined options
- No way to add custom provider strings (e.g., `vertex_ai/gemini-pro`, `ollama/llama3`)

**Solution:**
1. Add "Custom Provider" option to LLM providers menu
2. Show input field for custom model string when selected
3. Validate against LiteLLM supported providers
4. Store custom providers in config

**Focus Files:**
- `core/llm_config.py` - Add custom provider support
- `static/workspace/js/components/preferences/llm-pane.js` - UI for custom providers
- `run_web.py` - API endpoints for provider management

---

### **Issue #2: Provider Changes Don't Update Immediately**
**Problem:** When adding/setting a new provider, the UI doesn't reflect the change right away.

**Root Cause:**
- Agent is initialized with model at startup
- Changing provider in settings doesn't reload the agent
- Need to trigger agent recreation or reload

**Solution:**
1. When provider changes, invalidate cached agent
2. Emit SocketIO event to notify clients
3. UI reloads agent context/stats
4. Show visual feedback during provider switch

**Focus Files:**
- `run_web.py` - Invalidate agent cache on provider change
- `static/workspace/js/components/preferences/llm-pane.js` - Emit reload event
- `static/workspace/js/app.js` - Listen for provider change events

---

### **Issue #4: Can't Remove Default Project**
**Problem:** Getting "Cannot remove the default project" error when trying to change/remove the original project.

**Current State:**
- `core/project_manager.py` has logic preventing default project deletion
- No way to change which project is default
- Users stuck with initial project choice

**Solution:**
1. Add "Set as Default" option for projects
2. Allow removing default only if another project exists
3. Auto-promote another project to default if needed
4. Update UI to show default indicator

**Focus Files:**
- `core/project_manager.py` - Fix default project logic
- `static/workspace/js/components/preferences/projects-pane.js` - UI for default toggle
- `run_web.py` - API endpoint for changing default

---

## Implementation Order

### Phase 1: Issue #2 - Provider Updates (Quickest Win)
**Why first:** Smallest change, fixes immediate UX problem, unblocks testing of #1

**Steps:**
1. Add `invalidate_agent_cache()` helper in `run_web.py`
2. Call it when provider is saved via API
3. Emit `provider_changed` SocketIO event
4. Client-side: reload context stats and show notification

**Files to focus:**
```
focus run_web.py
focus static/workspace/js/components/preferences/llm-pane.js
focus static/workspace/js/app.js
```

**Checklist:**
- [x] Add agent cache invalidation on provider save
- [x] Emit SocketIO event with new provider info
- [x] Handle event in client (reload stats, show toast)
- [x] Test: change provider, verify immediate update

---

### Phase 2: Issue #4 - Default Project Management
**Why second:** Standalone feature, doesn't depend on #1 or #2

**Steps:**
1. Modify `ProjectManager.delete()` to handle default logic
2. Add `set_default(project_id)` method
3. Update projects-pane UI with default indicator
4. Add "Set as Default" button to project cards

**Files to focus:**
```
focus core/project_manager.py
focus static/workspace/js/components/preferences/projects-pane.js
focus run_web.py
```

**Checklist:**
- [x] Add `set_default()` method to ProjectManager
- [x] Modify `delete()` to auto-promote if deleting default
- [x] Add `/api/projects/<id>/set-default` endpoint
- [x] UI: Show star icon for default project
- [x] UI: Add "Set as Default" button
- [ ] Test: switch default, delete default with multiple projects

---

### Phase 3: Issue #1 - Custom Provider Support
**Why last:** Most complex, benefits from #2 being fixed first for testing

**Steps:**
1. Add `validate_model_string()` to llm_config
2. Add "Custom Provider" to provider list
3. Show text input when custom selected
4. Store custom providers in config
5. Add recent/favorites for custom models

**Files to focus:**
```
focus core/llm_config.py
focus static/workspace/js/components/preferences/llm-pane.js
focus run_web.py
```

**Checklist:**
- [ ] Add LiteLLM model validation helper
- [ ] Extend LLMConfigManager to store custom providers
- [ ] UI: Add "Custom Provider" option
- [ ] UI: Show text input with placeholder examples
- [ ] UI: Validate input before saving
- [ ] UI: Show recent custom providers
- [ ] Test: Add vertex_ai/gemini-pro, ollama/llama3, etc.

---

## Testing Plan

### After Phase 1 (Provider Updates)
1. Open preferences → LLM tab
2. Change model from Claude to GPT-4
3. Verify toast notification appears
4. Verify token bar updates immediately
5. Send message, verify new model is used

### After Phase 2 (Default Projects)
1. Create 2 projects (Project A, Project B)
2. Project A is default (has star)
3. Click "Set as Default" on Project B
4. Verify star moves to Project B
5. Try to delete Project B (should warn about default)
6. Delete Project A (non-default) - should succeed
7. Try to delete last project - should prevent

### After Phase 3 (Custom Providers)
1. Open preferences → LLM tab
2. Select "Custom Provider"
3. Enter `vertex_ai/gemini-1.5-pro`
4. Save and verify it works
5. Enter invalid model `fake/model-xyz`
6. Verify validation error
7. Check recent providers list shows custom entry

---

## Success Criteria

- [x] **Issue #3:** Token counting accurate within 2% of provider's count
- [ ] **Issue #2:** Provider changes reflect immediately (< 1 second)
- [ ] **Issue #1:** Can add any LiteLLM provider via custom input
- [ ] **Issue #4:** Can change default project and delete old default

---

## Notes

- Phase 1 is critical for testing Phases 2 & 3
- Keep backward compatibility with existing configs
- Add migration for projects without explicit default flag
- Custom providers should persist across sessions
- Consider adding provider presets (Ollama, LocalAI, etc.)
