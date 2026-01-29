# Project Bar & Preferences Redesign Plan

## Overview
Redesign the project bar to use a compact dropdown with hover trigger, and enhance the preferences modal with rich project cards that support inline editing, favorites, and notifications.

## Design Principles
- VS Code style: flat, minimal, professional
- 150ms ease-out transitions everywhere
- Muted by default, accent on interaction
- 8px grid spacing
- No emojis, simple glyphs only

---

## Phase 1: Project Bar Dropdown

### 1.1 Basic Structure
- [x] Replace multiple project boxes with single dropdown trigger
- [x] Show: color dot + project name + chevron + notification badge
- [x] Dropdown appears on hover (with small delay to prevent accidental triggers)
- [x] Dropdown disappears on mouse leave (with small delay)

### 1.2 Dropdown Content
- [x] Favorites section (★ icon, max 5)
- [x] Recent section (last 5 non-favorited, sorted by last opened)
- [x] Divider line
- [x] "Add Project..." action
- [x] "Manage Projects..." action (opens preferences)

### 1.3 Dropdown Styling
- [x] Clean list: 32px row height, 12px horizontal padding
- [x] Color dot + name + optional notification count
- [x] Checkmark on current project
- [x] Hover: bg-2 background
- [x] Subtle drop shadow
- [x] Scale-in animation (150ms)

### 1.4 Notifications (Placeholder)
- [x] Aggregate badge on dropdown trigger showing count of other projects needing attention
- [x] Per-project notification count in dropdown list
- [x] Subtle pulse animation on badge
- [x] Data structure ready for future agent notifications

---

## Phase 2: Preferences Modal - Projects Pane

### 2.1 Rich Project Cards
- [ ] Larger color swatch (clickable)
- [ ] Project name (editable)
- [ ] Path display (with SSH badge if remote)
- [ ] "Last opened" timestamp
- [ ] Action buttons: favorite toggle (★/☆), edit (✎), more menu (···)

### 2.2 Inline Edit Mode
- [ ] Click edit button → card expands
- [ ] Name becomes editable input
- [ ] Color picker row appears (8 color dots)
- [ ] Save (✓) and Cancel (✕) buttons
- [ ] Smooth expand animation

### 2.3 Favorite Toggle
- [ ] Click star to toggle favorite status
- [ ] Filled star (★) = favorited, outline (☆) = not
- [ ] Favorites appear first in list
- [ ] Max 5 favorites enforced (show message if trying to add more)

### 2.4 More Menu (···)
- [ ] Delete project option
- [ ] Maybe later: duplicate, reveal in finder, etc.

### 2.5 Add Project Flow
- [ ] Single "Add Project" button (dashed border)
- [ ] Click → expand to show two options: Local / SSH
- [ ] Keep existing folder browser and SSH flow

### 2.6 Sorting
- [ ] Favorites first (sorted by last opened)
- [ ] Then non-favorites (sorted by last opened)
- [ ] Most recent at top

---

## Phase 3: Data Model Updates

### 3.1 Project Schema
- [x] Add `favorite: boolean` field
- [x] Add `last_opened: timestamp` field (already existed as `last_accessed`)
- [x] Add `notifications: number` field (placeholder)

### 3.2 API Endpoints
- [x] `PATCH /api/projects/:id` - update name, color, favorite
- [x] Ensure `GET /api/projects` returns favorite and last_opened
- [ ] Update project on switch to set last_opened

---

## Phase 4: Polish & Animation

### 4.1 Transitions
- [ ] Dropdown: scale + fade in (150ms ease-out)
- [ ] Card expand: smooth height transition
- [ ] Hover states: background fade (100ms)
- [ ] Notification badge: subtle pulse

### 4.2 Cleanup
- [ ] Remove old project-bar styles
- [ ] Remove emoji remnants
- [ ] Test all hover/click interactions
- [ ] Ensure keyboard accessibility (Escape closes dropdown)

---

## File Checklist

### Files to Modify
- [ ] `static/workspace/js/components/project-bar.js` - complete rewrite
- [ ] `static/workspace/css/components/project-bar.css` - complete rewrite
- [ ] `static/workspace/js/components/preferences/projects-pane.js` - rich cards, inline edit
- [ ] `static/workspace/css/components/preferences.css` - card styles, edit mode
- [ ] `run_web.py` - API endpoint updates (PATCH, last_opened)
- [ ] `core/project_manager.py` - add favorite, last_opened fields

### Files to Review
- [ ] `static/workspace/js/core/workspace.js` - toolbar rendering
- [ ] `static/workspace/css/components/toolbar.css` - may need adjustments

---

## Current Progress

**Phase 1**: Complete ✓
**Phase 2**: Complete ✓ - Completely rewritten with Apple-inspired design  
**Phase 3**: In Progress - data model already has `last_accessed`, need to add `favorite`
**Phase 4**: Not started

---

## Notes

- Hover delay: ~100ms before showing dropdown, ~300ms before hiding (prevents flicker)
- Notification system is placeholder - will connect to agent events later
- Color palette: use existing 8 colors from COLORS array
