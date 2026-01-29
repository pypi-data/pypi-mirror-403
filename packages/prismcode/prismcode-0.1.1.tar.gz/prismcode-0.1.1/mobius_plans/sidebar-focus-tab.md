# Plan: Add Focused Files Tab to Sidebar

## Files to Modify/Create

| File | Action |
|------|--------|
| `static/workspace/js/components/focus.js` | **CREATE** - New component |
| `static/workspace/css/components/focus.css` | **CREATE** - Styles for focus panel |
| `static/workspace/js/app.js` | **MODIFY** - Register component |
| `static/workspace/js/core/workspace.js` | **MODIFY** - Add tab to DEFAULT_LAYOUT |
| `templates/workspace.html` | **MODIFY** - Include new CSS file |

## Checklist

- [x] **1. Create `focus.js` component**
  - Extend `MobiusComponent`
  - Render a scrollable list of focused files
  - Fetch from `/api/focused-files?session_id=X`
  - Get current session ID from active chat via `bus` event or workspace method
  - Listen for `focused_files_updated` socket event
  - Listen for `tab-activated` bus event to refresh when main tab changes
  - Add × button to unfocus files

- [x] **2. Create `focus.css` styles**
  - Reuse patterns from `tree.css`
  - Scrollable list
  - File items with path, line count, remove button

- [x] **3. Register component in `app.js`**
  - Import `MobiusFocus` 
  - Add to `components` registry

- [x] **4. Add tab to `DEFAULT_LAYOUT` in `workspace.js`**
  - Add `{ id: 'focus', icon: '◉', title: 'Focus', component: 'focus', config: {} }` to sidebar tabs

- [x] **5. Include CSS in `workspace.html`**
  - Add `<link>` for `focus.css`

- [ ] **6. Test**
  - Focus some files
  - Check sidebar Focus tab shows them
  - Switch main tabs - focus list updates
  - Click × to unfocus - list updates
  - Agent focuses/unfocuses files - list updates in real-time
