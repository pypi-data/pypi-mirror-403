# Workspace UI Architecture

## Vision

A VS Code-like modular workspace where:
- Panes can be resized, moved, collapsed
- Components aren't tied to locations (chat can be in main area, sidebar, or bottom)
- Tabs allow multiple instances of same component type
- Per-project color theming
- Minimal, maintainable code designed for AI agents to extend

## Core Principles

1. **Location-agnostic components** - A `<mobius-chat>` works the same whether it's in the main area, a sidebar, or a bottom panel
2. **Declarative layout** - Layout defined in JSON, rendered dynamically
3. **Web Components** - Each component is self-contained with its own JS/CSS
4. **CSS variables everywhere** - Theming and sizing through variables, not hardcoded values
5. **Event-driven communication** - Components talk via custom events, not direct references

## Layout System

### Regions

```
┌─────────────────────────────────────────────────────────────┐
│                        TOOLBAR                              │
├───────────┬─────────────────────────────────┬───────────────┤
│           │                                 │               │
│  SIDEBAR  │            MAIN                 │   RIGHT       │
│  (LEFT)   │                                 │   (optional)  │
│           │                                 │               │
│           ├─────────────────────────────────┤               │
│           │           BOTTOM (optional)     │               │
├───────────┴─────────────────────────────────┴───────────────┤
│                       STATUSBAR                             │
└─────────────────────────────────────────────────────────────┘
```

### Layout Config (JSON)

```json
{
  "sidebar": {
    "width": "250px",
    "minWidth": "180px",
    "tabs": [
      {"id": "sessions", "icon": "💬", "component": "tree", "config": {"type": "sessions"}},
      {"id": "explorer", "icon": "📁", "component": "tree", "config": {"type": "files"}},
      {"id": "git", "icon": "⎇", "component": "git-panel"}
    ],
    "activeTab": "sessions"
  },
  "main": {
    "tabs": [
      {"id": "chat-1", "title": "Chat", "component": "chat", "config": {"session": "abc123"}}
    ],
    "activeTab": "chat-1"
  },
  "bottom": {
    "height": "200px",
    "collapsed": true,
    "tabs": [
      {"id": "term-1", "title": "Terminal", "component": "terminal"}
    ]
  },
  "right": {
    "width": "300px",
    "collapsed": true,
    "tabs": [
      {"id": "settings", "title": "Settings", "component": "settings"}
    ]
  }
}
```

## Component Registry

Components register themselves and can be instantiated anywhere:

```js
// Component registry
const Components = {
  'chat': MobiusChat,
  'terminal': MobiusTerminal,
  'tree': MobiusTree,
  'settings': MobiusSettings,
  'git-panel': MobiusGit,
  'file-viewer': MobiusFileViewer,
};

// Instantiate component by name
function createComponent(name, config) {
  const Component = Components[name];
  const el = new Component();
  el.configure(config);
  return el;
}
```

## File Structure

```
static/
├── css/
│   ├── variables.css      # All CSS variables (colors, sizes, fonts)
│   ├── base.css           # Reset, typography, utilities
│   ├── layout.css         # Grid regions, resizers, collapse states
│   ├── tabs.css           # Tab bars (works in any region)
│   └── components/
│       ├── chat.css       # Chat-specific styles
│       ├── terminal.css
│       ├── tree.css
│       ├── settings.css
│       └── toolbar.css
│
├── js/
│   ├── core/
│   │   ├── workspace.js   # Layout manager, region handling
│   │   ├── tabs.js        # Tab logic (add, remove, reorder, drag)
│   │   ├── resize.js      # Pane resizing logic
│   │   ├── events.js      # Custom event bus
│   │   └── storage.js     # Persist layout to localStorage
│   │
│   ├── components/
│   │   ├── base.js        # Base class for all components
│   │   ├── chat.js        # Chat component (extracted from app.js)
│   │   ├── terminal.js    # Terminal emulator
│   │   ├── tree.js        # Generic tree (sessions, files, git)
│   │   ├── settings.js    # Settings panel
│   │   └── toolbar.js     # Top toolbar
│   │
│   └── app.js             # Bootstrap, socket setup, orchestration
│
└── themes/
    ├── dark.css
    ├── light.css
    └── projects.css       # Per-project color overrides
```

## Base Component Class

All components extend this for consistency:

```js
// components/base.js (~60 lines)
class MobiusComponent extends HTMLElement {
  constructor() {
    super();
    this.config = {};
  }

  // Called when added to DOM
  connectedCallback() {
    this.render();
    this.setupEvents();
  }

  // Called when removed from DOM
  disconnectedCallback() {
    this.cleanup();
  }

  // Override in subclass
  render() {}
  setupEvents() {}
  cleanup() {}

  // Configure from layout JSON
  configure(config) {
    this.config = { ...this.config, ...config };
    if (this.isConnected) this.render();
    return this;
  }

  // Emit custom event (bubbles up to workspace)
  emit(name, detail = {}) {
    this.dispatchEvent(new CustomEvent(name, { 
      bubbles: true, 
      detail: { component: this, ...detail }
    }));
  }

  // Get CSS variable value
  cssVar(name) {
    return getComputedStyle(this).getPropertyValue(name).trim();
  }
}
```

## Workspace Manager

Handles layout, regions, and component lifecycle:

```js
// core/workspace.js (~150 lines)
class Workspace {
  constructor(container) {
    this.container = container;
    this.layout = this.loadLayout();
    this.regions = new Map();  // region name -> element
    this.components = new Map();  // tab id -> component instance
  }

  loadLayout() {
    const saved = localStorage.getItem('mobius-layout');
    return saved ? JSON.parse(saved) : DEFAULT_LAYOUT;
  }

  saveLayout() {
    localStorage.setItem('mobius-layout', JSON.stringify(this.layout));
  }

  render() {
    this.container.innerHTML = `
      <div class="workspace" data-project="${this.currentProject}">
        <header class="toolbar" id="toolbar"></header>
        <aside class="sidebar" id="sidebar"></aside>
        <main class="main" id="main"></main>
        <aside class="right-panel" id="right"></aside>
        <footer class="statusbar" id="statusbar"></footer>
      </div>
    `;
    
    ['sidebar', 'main', 'bottom', 'right'].forEach(region => {
      this.renderRegion(region);
    });
  }

  renderRegion(name) {
    const config = this.layout[name];
    if (!config) return;

    const el = this.container.querySelector(`#${name}`);
    if (!el) return;

    // Set size
    if (config.width) el.style.width = config.width;
    if (config.height) el.style.height = config.height;
    if (config.collapsed) el.classList.add('collapsed');

    // Render tabs
    if (config.tabs?.length) {
      el.innerHTML = `
        <div class="tab-bar">
          ${config.tabs.map(tab => `
            <button class="tab ${tab.id === config.activeTab ? 'active' : ''}" 
                    data-tab="${tab.id}">
              ${tab.icon || ''} ${tab.title || ''}
            </button>
          `).join('')}
        </div>
        <div class="tab-content"></div>
      `;

      // Create active component
      this.activateTab(name, config.activeTab);
    }

    this.regions.set(name, el);
  }

  activateTab(region, tabId) {
    const config = this.layout[region];
    const tabConfig = config.tabs.find(t => t.id === tabId);
    if (!tabConfig) return;

    // Update layout state
    config.activeTab = tabId;

    // Get or create component
    let component = this.components.get(tabId);
    if (!component) {
      component = createComponent(tabConfig.component, tabConfig.config);
      this.components.set(tabId, component);
    }

    // Mount to region
    const content = this.regions.get(region).querySelector('.tab-content');
    content.innerHTML = '';
    content.appendChild(component);

    this.saveLayout();
  }

  addTab(region, componentType, config = {}) {
    const id = `${componentType}-${Date.now()}`;
    const tab = { id, component: componentType, config, title: config.title || componentType };
    
    this.layout[region].tabs.push(tab);
    this.renderRegion(region);
    this.activateTab(region, id);
    
    return id;
  }

  closeTab(region, tabId) {
    const config = this.layout[region];
    config.tabs = config.tabs.filter(t => t.id !== tabId);
    
    // Cleanup component
    const component = this.components.get(tabId);
    if (component) {
      component.remove();
      this.components.delete(tabId);
    }

    // Activate another tab if needed
    if (config.activeTab === tabId && config.tabs.length) {
      this.activateTab(region, config.tabs[0].id);
    }

    this.saveLayout();
  }

  moveTab(fromRegion, toRegion, tabId) {
    const tab = this.layout[fromRegion].tabs.find(t => t.id === tabId);
    if (!tab) return;

    this.layout[fromRegion].tabs = this.layout[fromRegion].tabs.filter(t => t.id !== tabId);
    this.layout[toRegion].tabs.push(tab);

    this.renderRegion(fromRegion);
    this.activateTab(toRegion, tabId);
  }

  toggleRegion(name) {
    const config = this.layout[name];
    config.collapsed = !config.collapsed;
    this.regions.get(name).classList.toggle('collapsed');
    this.saveLayout();
  }

  setProject(projectId) {
    this.currentProject = projectId;
    this.container.querySelector('.workspace').dataset.project = projectId;
    this.emit('project-changed', { projectId });
  }
}
```

## CSS Variables System

Everything themeable via variables:

```css
/* variables.css */
:root {
  /* Colors - base */
  --bg-0: #0a0a0a;
  --bg-1: #111;
  --bg-2: #1a1a1a;
  --bg-3: #222;
  --border: #2a2a2a;
  --text: #e5e5e5;
  --text-muted: #666;
  
  /* Colors - semantic */
  --accent: var(--project-color, #ff6b2b);
  --accent-dim: color-mix(in srgb, var(--accent) 15%, transparent);
  --success: #3d9;
  --error: #f66;
  --warning: #fa0;
  
  /* Sizing */
  --sidebar-width: 250px;
  --sidebar-min: 180px;
  --bottom-height: 200px;
  --right-width: 300px;
  --tab-height: 36px;
  --toolbar-height: 40px;
  --statusbar-height: 24px;
  
  /* Typography */
  --font: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-size: 14px;
  --font-size-sm: 12px;
  --font-size-xs: 10px;
  
  /* Misc */
  --radius: 6px;
  --radius-sm: 4px;
  --transition: 150ms ease;
}

/* Project color overrides */
[data-project="mobius"]    { --project-color: #ff6b2b; }
[data-project="api"]       { --project-color: #3b82f6; }
[data-project="pi"]        { --project-color: #10b981; }
[data-project="ml"]        { --project-color: #8b5cf6; }
[data-project="gamedev"]   { --project-color: #f59e0b; }
```

## Layout CSS

Grid-based regions with resize support:

```css
/* layout.css */
.workspace {
  display: grid;
  grid-template-areas:
    "toolbar toolbar toolbar"
    "sidebar main right"
    "sidebar bottom right"
    "statusbar statusbar statusbar";
  grid-template-columns: var(--sidebar-width) 1fr var(--right-width);
  grid-template-rows: var(--toolbar-height) 1fr auto var(--statusbar-height);
  height: 100vh;
  background: var(--bg-0);
}

.toolbar    { grid-area: toolbar; }
.sidebar    { grid-area: sidebar; }
.main       { grid-area: main; display: flex; flex-direction: column; }
.right-panel{ grid-area: right; }
.bottom     { grid-area: bottom; }
.statusbar  { grid-area: statusbar; }

/* Collapsible regions */
.sidebar.collapsed { width: 48px !important; }
.right-panel.collapsed { width: 0 !important; overflow: hidden; }
.bottom.collapsed { height: 0 !important; overflow: hidden; }

/* Resizer handles */
.resizer {
  position: absolute;
  background: transparent;
  transition: background var(--transition);
  z-index: 10;
}
.resizer:hover, .resizer.active {
  background: var(--accent);
}
.resizer-h {
  width: 4px;
  cursor: ew-resize;
  top: 0;
  bottom: 0;
}
.resizer-v {
  height: 4px;
  cursor: ns-resize;
  left: 0;
  right: 0;
}
```

## Tab System CSS

Reusable tabs that work in any region:

```css
/* tabs.css */
.tab-bar {
  display: flex;
  gap: 2px;
  padding: 4px;
  background: var(--bg-1);
  border-bottom: 1px solid var(--border);
  height: var(--tab-height);
  overflow-x: auto;
}

.tab {
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.tab:hover {
  background: var(--bg-2);
  color: var(--text);
}

.tab.active {
  background: var(--bg-2);
  color: var(--accent);
}

.tab-close {
  opacity: 0;
  margin-left: 4px;
  font-size: 10px;
}

.tab:hover .tab-close {
  opacity: 0.5;
}

.tab-close:hover {
  opacity: 1;
  color: var(--error);
}

.tab-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}
```

## Event Bus

Simple pub/sub for component communication:

```js
// core/events.js (~30 lines)
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    return () => this.off(event, callback);
  }

  off(event, callback) {
    this.listeners.get(event)?.delete(callback);
  }

  emit(event, data) {
    this.listeners.get(event)?.forEach(cb => cb(data));
  }
}

export const bus = new EventBus();
```

## Example: Chat Component

Extracted from current app.js, now standalone:

```js
// components/chat.js
class MobiusChat extends MobiusComponent {
  static defaults = {
    session: null,
    project: 'local'
  };

  constructor() {
    super();
    this.config = { ...MobiusChat.defaults };
    this.messages = [];
    this.isProcessing = false;
  }

  render() {
    this.innerHTML = `
      <div class="chat">
        <div class="chat-messages"></div>
        <div class="chat-input">
          <textarea placeholder="Type a message..."></textarea>
          <button class="btn btn-primary">Send</button>
        </div>
      </div>
    `;
    this.messagesEl = this.querySelector('.chat-messages');
    this.inputEl = this.querySelector('textarea');
    this.btnEl = this.querySelector('button');
  }

  setupEvents() {
    this.btnEl.addEventListener('click', () => this.send());
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.send();
      }
    });

    // Socket events scoped to this chat's session
    socket.on('agent_delta', (data) => {
      if (data.session === this.config.session) {
        this.handleDelta(data);
      }
    });
  }

  send() {
    const msg = this.inputEl.value.trim();
    if (!msg || this.isProcessing) return;

    this.addMessage('user', msg);
    this.inputEl.value = '';

    socket.emit('send_message', {
      message: msg,
      session: this.config.session,
      project: this.config.project
    });

    this.isProcessing = true;
    this.emit('chat:sending', { message: msg });
  }

  addMessage(role, content) {
    // ... (reuse existing message rendering logic)
  }

  handleDelta(data) {
    // ... (reuse existing streaming logic)
  }
}

customElements.define('mobius-chat', MobiusChat);
```

## Example: Terminal Component

```js
// components/terminal.js
class MobiusTerminal extends MobiusComponent {
  static defaults = {
    project: 'local',
    cwd: '~'
  };

  render() {
    this.innerHTML = `
      <div class="terminal">
        <div class="terminal-output"></div>
        <div class="terminal-input">
          <span class="terminal-prompt">$</span>
          <input type="text" spellcheck="false" />
        </div>
      </div>
    `;
    this.outputEl = this.querySelector('.terminal-output');
    this.inputEl = this.querySelector('input');
  }

  setupEvents() {
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.execute(this.inputEl.value);
        this.inputEl.value = '';
      }
    });

    socket.on('terminal_output', (data) => {
      if (data.terminal === this.id) {
        this.appendOutput(data.output);
      }
    });
  }

  execute(command) {
    this.appendOutput(`$ ${command}\n`, 'command');
    socket.emit('terminal_exec', {
      command,
      project: this.config.project,
      terminal: this.id
    });
  }

  appendOutput(text, type = 'output') {
    const line = document.createElement('div');
    line.className = `terminal-line terminal-${type}`;
    line.textContent = text;
    this.outputEl.appendChild(line);
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }
}

customElements.define('mobius-terminal', MobiusTerminal);
```

## Migration Path

### Phase 1: Layout Shell
1. Create new `workspace.html` template
2. Add `variables.css`, `layout.css`, `tabs.css`
3. Hardcode current chat into main area
4. Get resizing and collapse working

### Phase 2: Extract Chat
1. Move chat logic from `app.js` to `components/chat.js`
2. Make it a Web Component
3. Verify it works in the new layout

### Phase 3: Add Components
1. Terminal component
2. Tree component (reuse for sessions + files)
3. Settings component

### Phase 4: Full Workspace
1. Tab management (add, close, drag)
2. Layout persistence
3. Keyboard shortcuts

### Phase 5: Multi-Project
1. Project registry
2. SSH tool routing
3. Project color theming

## Keyboard Shortcuts

```
Ctrl+`          Toggle bottom panel (terminal)
Ctrl+B          Toggle sidebar
Ctrl+Shift+B    Toggle right panel
Ctrl+T          New chat tab
Ctrl+W          Close current tab
Ctrl+Tab        Next tab
Ctrl+Shift+Tab  Previous tab
Ctrl+1-9        Switch to tab N
Ctrl+Shift+P    Command palette (future)
```

## Summary

This architecture gives you:

- **~1500 lines of JS** across modular files
- **~500 lines of CSS** with full theming
- **Location-agnostic components** that work anywhere
- **Declarative layout** stored in JSON
- **Easy to extend** - just add new component files
- **AI-maintainable** - clear patterns, isolated logic
