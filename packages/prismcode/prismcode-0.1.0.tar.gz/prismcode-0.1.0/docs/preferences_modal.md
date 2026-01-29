# Preferences Modal Component

A Mac-style settings modal for the Mobius workspace, providing a modular way to configure projects, LLM providers, and agent behavior.

## Overview

The preferences modal follows the Mac System Preferences pattern:
- Sidebar with icon tabs on the left
- Content area on the right that swaps based on selection
- Centered modal overlay with smooth animations
- Keyboard shortcut support (Cmd/Ctrl + ,)

```
┌─────────────────────────────────────────────────┐
│ ● ● ●                Settings              ✕    │
├─────────┬───────────────────────────────────────┤
│ 📁 Proj │                                       │
│ 🤖 LLM  │   [Content for selected pane]        │
│ ⚙ Agent │                                       │
│         │                                       │
└─────────┴───────────────────────────────────────┘
```

## File Structure

```
static/workspace/
├── css/
│   └── components/
│       └── preferences.css      # All modal and pane styling
└── js/
    └── components/
        └── preferences/
            ├── index.js         # Main modal component
            ├── projects-pane.js # Projects management
            ├── llm-pane.js      # LLM/API configuration
            └── agent-pane.js    # Agent settings
```

## Usage

### Opening the Modal

```javascript
// Via the app instance
window.app.preferences.show();
window.app.preferences.hide();
window.app.preferences.toggle();

// Or keyboard shortcut: Cmd/Ctrl + ,
```

### Integration

The modal is initialized in `app.js`:

```javascript
import { MobiusPreferences } from './components/preferences/index.js';

// In init():
this.preferences = document.createElement('mobius-preferences');
document.body.appendChild(this.preferences);
```

## Adding New Panes

Panes are simple objects with a standard interface. To add a new pane:

### 1. Create the Pane File

```javascript
// static/workspace/js/components/preferences/my-pane.js

export const MyPane = {
  id: 'my-pane',           // Unique identifier
  icon: '🔧',              // Emoji or icon
  label: 'My Settings',    // Sidebar label
  
  // Optional: Load data before rendering
  async load() {
    const res = await fetch('/api/my-settings');
    this.data = await res.json();
  },
  
  // Render the pane content
  render(container) {
    container.innerHTML = `
      <div class="pane-section">
        <div class="pane-section-title">Section Title</div>
        <div class="pane-field">
          <label class="pane-label">Field Label</label>
          <input type="text" class="pane-input" id="my-field">
        </div>
      </div>
      
      <div class="pane-actions">
        <button class="btn btn-primary" id="save-btn">Save</button>
      </div>
    `;
    
    this.setupEvents(container);
  },
  
  // Wire up interactivity
  setupEvents(container) {
    container.querySelector('#save-btn').addEventListener('click', () => {
      const value = container.querySelector('#my-field').value;
      // Save to backend...
    });
  }
};
```

### 2. Register the Pane

In `preferences/index.js`:

```javascript
import { MyPane } from './my-pane.js';

const PANES = [
  ProjectsPane,
  LLMPane,
  AgentPane,
  MyPane  // Add here
];
```

## CSS Classes Reference

### Layout Classes

| Class | Purpose |
|-------|---------|
| `.prefs-overlay` | Full-screen backdrop |
| `.prefs-modal` | Modal window container |
| `.prefs-header` | Header with title and close button |
| `.prefs-sidebar` | Left sidebar with tabs |
| `.prefs-content` | Right content area |
| `.prefs-tab` | Sidebar tab button |

### Pane Content Classes

| Class | Purpose |
|-------|---------|
| `.pane-section` | Groups related fields |
| `.pane-section-title` | Section header (uppercase, muted) |
| `.pane-field` | Single form field container |
| `.pane-label` | Field label |
| `.pane-input` | Text input styling |
| `.pane-select` | Dropdown select styling |
| `.pane-textarea` | Multiline text input |
| `.pane-hint` | Help text below fields |

### List Classes

| Class | Purpose |
|-------|---------|
| `.pane-list` | Container for list items |
| `.pane-list-item` | Single list item (project, model, etc) |
| `.pane-list-item-icon` | Icon/indicator on left |
| `.pane-list-item-content` | Title + subtitle container |
| `.pane-list-item-title` | Item title |
| `.pane-list-item-subtitle` | Item description |
| `.pane-list-item-actions` | Action buttons on right |
| `.pane-add-btn` | Dashed "add new" button |

### Interactive Classes

| Class | Purpose |
|-------|---------|
| `.pane-toggle` | Toggle switch row |
| `.pane-color-picker` | Color selection grid |
| `.pane-color-option` | Individual color circle |
| `.pane-actions` | Button row at bottom |

## Current Panes

### Projects Pane (`projects-pane.js`)

Manages local and SSH project connections:
- List existing projects with color indicators
- Add new local or SSH projects
- Edit project settings
- Delete projects

**Backend endpoints needed:**
- `POST /api/projects` - Create project
- `PUT /api/projects/:id` - Update project
- `DELETE /api/projects/:id` - Delete project

### LLM Pane (`llm-pane.js`)

Configures LLM providers and API keys:
- Select active provider and model
- Manage API keys (Anthropic, OpenAI, Google)
- Configure local Ollama connection

**Backend endpoints needed:**
- `GET /api/llm/config` - Get current config
- `POST /api/llm/config` - Save config
- `POST /api/llm/keys/:provider` - Save API key (encrypted)
- `POST /api/llm/test-ollama` - Test Ollama connection

### Agent Pane (`agent-pane.js`)

Configures agent behavior:
- System prompt customization
- Temperature and max tokens
- Toggle features (auto-title, streaming, diffs)
- Enable/disable individual tools

**Backend endpoints needed:**
- `GET /api/agent/config` - Get current config
- `POST /api/agent/config` - Save config

## Theming

The modal uses CSS variables from `variables.css`:

```css
--bg-0, --bg-1, --bg-2, --bg-3  /* Background layers */
--text, --text-muted            /* Text colors */
--accent, --accent-dim          /* Project accent color */
--border, --radius              /* Borders and corners */
--error, --success              /* Status colors */
```

Project color automatically applies via `--accent` variable.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd/Ctrl + ,` | Toggle preferences modal |
| `Escape` | Close modal |

## Future Enhancements

- [ ] Search/filter within panes
- [ ] Import/export settings
- [ ] Keyboard navigation between tabs
- [ ] Appearance/theme pane
- [ ] Keyboard shortcuts pane
- [ ] Plugin/extension management pane
