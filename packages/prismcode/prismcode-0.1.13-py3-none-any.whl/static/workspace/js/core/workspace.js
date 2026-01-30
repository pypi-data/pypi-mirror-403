/* Prism Workspace - Layout Manager */
import { bus } from './events.js';
import { loadLayout, saveLayout } from './storage.js';
import { initResizers } from './resize.js';

const DEFAULT_LAYOUT = {
    sidebar: {
      width: '220px',
      collapsed: false,
      tabs: [
        { id: 'sessions', icon: '◎', title: 'Sessions', component: 'tree', config: { type: 'sessions' } },
        { id: 'explorer', icon: '📁', title: 'Explorer', component: 'tree', config: { type: 'files' } }
      ],
      activeTab: 'sessions'
    },
  main: {
    tabs: [
      { id: 'chat-1', title: 'Chat', component: 'chat', config: {} }
    ],
    activeTab: 'chat-1'
  },
  bottom: {
    height: '200px',
    collapsed: true,
    tabs: [
      { id: 'terminal-1', title: 'Terminal', component: 'terminal', config: {} }
    ],
    activeTab: 'terminal-1'
  },
  right: {
    width: '280px',
    collapsed: false,
    tabs: [
      { id: 'focused-files', icon: '◉', title: 'Focused Files', component: 'focus', config: {} }
    ],
    activeTab: 'focused-files'
  }
};
export class Workspace {
  constructor(container, components) {
    this.container = container;
    this.components = components;
    this.layout = loadLayout() || JSON.parse(JSON.stringify(DEFAULT_LAYOUT));
    
    // Ensure main region always has at least one chat tab
    if (!this.layout.main?.tabs?.length) {
      console.log('[Workspace] No main tabs found, adding default chat tab');
      this.layout.main = {
        tabs: [{ id: 'chat-1', title: 'Chat', component: 'chat', config: {} }],
        activeTab: 'chat-1'
      };
    }
    
    // Ensure sidebar exists and has tabs
    if (!this.layout.sidebar?.tabs?.length) {
      console.log('[Workspace] No sidebar config found, adding default');
      this.layout.sidebar = {
        width: '220px',
        collapsed: false,
        tabs: [
          { id: 'sessions', icon: '◎', title: 'Sessions', component: 'tree', config: { type: 'sessions' } },
          { id: 'explorer', icon: '📁', title: 'Explorer', component: 'tree', config: { type: 'files' } }
        ],
        activeTab: 'sessions'
      };
    }
    
    // Migration: Remove redundant focus tab from sidebar
    if (this.layout.sidebar?.tabs?.some(t => t.id === 'focus')) {
      console.log('[Workspace] Migrating sidebar to remove redundant focus tab');
      this.layout.sidebar.tabs = this.layout.sidebar.tabs.filter(t => t.id !== 'focus');
      if (this.layout.sidebar.activeTab === 'focus') {
        this.layout.sidebar.activeTab = 'sessions';
      }
      this.save();
    }
    
    // Migration: Replace legacy settings tab in right panel with focus
    if (this.layout.right?.tabs?.some(t => t.id === 'settings')) {
      console.log('[Workspace] Migrating right panel from settings to focus');
      this.layout.right = {
        width: '280px',
        collapsed: false,
        tabs: [
          { id: 'focused-files', icon: '◉', title: 'Focused Files', component: 'focus', config: {} }
        ],
        activeTab: 'focused-files'
      };
      this.save();
    }
    
    // Initialize project state storage if missing
    if (!this.layout.projects) {
      this.layout.projects = {};
    }
    
    this.instances = new Map();
    // Restore current project from layout if available
    this.currentProject = this.layout.currentProject || '';
  }

  render() {
    // Detect mobile viewport
    this.isMobile = window.matchMedia('(max-width: 768px)').matches;
    
    this.container.innerHTML = `
      <div class="workspace ${this.layout.right?.collapsed === false ? 'right-open' : ''}" data-project="${this.currentProject}">
        <div class="mobile-backdrop" id="mobile-backdrop"></div>
        <header class="toolbar">
          <button class="sidebar-toggle-btn" id="toggle-sidebar-left" title="Toggle Sidebar (Ctrl+B)">☰</button>
          <project-bar id="project-bar"></project-bar>
          <div class="toolbar-spacer"></div>
          
          <div class="toolbar-model-selector" id="toolbar-model-selector">
            <button class="model-selector-trigger" id="model-selector-trigger">
              <span class="model-icon">◎</span>
              <span class="model-name-label" id="model-name-label">Loading...</span>
              <span class="model-chevron">▼</span>
            </button>
            <div class="model-selector-dropdown hidden" id="model-selector-dropdown">
              <div class="model-dropdown-header">Select Model</div>
              <div class="model-dropdown-list" id="model-dropdown-list">
                <!-- Providers and models injected here -->
              </div>
            </div>
          </div>

          <div class="toolbar-token-bar" id="toolbar-token-bar" title="Context Usage">
            <div class="toolbar-token-track" id="toolbar-token-track"></div>
            <span class="toolbar-token-label" id="toolbar-token-label">0k/0k</span>
            <div class="toolbar-token-tooltip" id="toolbar-token-tooltip"></div>
          </div>
          <div class="toolbar-actions">
            <button class="toolbar-btn" id="toggle-bottom" title="Toggle Terminal (Ctrl+\`)">⌨</button>
            <button class="toolbar-btn" id="toggle-right">
              <span class="focus-icon" data-tooltip="Files the agent can see but aren't saved into the history">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="9"></circle>
                  <line x1="12" y1="1" x2="12" y2="5"></line>
                  <line x1="12" y1="19" x2="12" y2="23"></line>
                  <line x1="1" y1="12" x2="5" y2="12"></line>
                  <line x1="19" y1="12" x2="23" y2="12"></line>
                  <circle cx="12" cy="12" r="0.5" fill="currentColor"></circle>
                </svg>
              </span>
            </button>
          </div>        </header>
        <aside class="sidebar ${this.layout.sidebar.collapsed ? 'collapsed' : ''}" style="width: ${this.layout.sidebar.width}">
          <div class="sidebar-header">
            <div class="tab-bar icon-tabs"></div>
          </div>
          <div class="sidebar-content"></div>
        </aside>
        <div class="main">
          <div class="bottom-panel ${this.layout.bottom.collapsed ? 'collapsed' : ''}" style="height: ${this.layout.bottom.height}">
            <div class="tab-bar"></div>
            <div class="tab-content"></div>
          </div>
          <div class="main-content">
            <div class="tab-bar main-tabs"></div>
            <div class="tab-content"></div>
          </div>
        </div>
        <aside class="right-panel ${this.layout.right.collapsed ? 'collapsed' : ''}" style="width: ${this.layout.right.width}">
          <div class="right-panel-header">
            <span class="right-panel-title">Focused Files</span>
          </div>
          <div class="right-panel-content"></div>
        </aside>
        <footer class="statusbar">
          <div class="statusbar-item" id="status-model"><span class="statusbar-dot online"></span> Connected</div>
        </footer>
      </div>
    `;

    // Render regions
    this.renderSidebarTabs();
    this.renderRegion('main', '.main-content');
    this.renderRegion('bottom', '.bottom-panel');
    this.renderRightPanel();

    // Init resizers
    initResizers(this.container.querySelector('.workspace'));

    // Bind toolbar actions
    this.bindToolbarEvents();
    this.initModelSelector();

    // Keyboard shortcuts
    this.bindKeyboardShortcuts();

    // Load initial token stats
    this.loadTokenStats();

    // Listen for focus changes to update token bar
    if (window.socket) {
      window.socket.on('focused_files_updated', () => this.loadTokenStats());
    }
    
    // Update token stats when a session is loaded (not on tab switch, only on actual session change)
    bus.on('session-loaded', () => this.loadTokenStats());
    
    // Close mobile panels when requested (e.g., after selecting a session)
    bus.on('close-mobile-panels', () => this.closeMobilePanels());

    // Refresh token stats periodically (every 30s) and after agent messages
    if (window.socket) {
      window.socket.on('agent_done', () => setTimeout(() => this.loadTokenStats(), 500));
      window.socket.on('tool_done', () => setTimeout(() => this.loadTokenStats(), 500));
      
      // Handle agent completion - glow tabs that need attention
      window.socket.on('agent_complete', (data) => this.handleAgentComplete(data));
      
      // Track processing state for tabs
      // NOTE: Use agent_complete (not agent_done) because agent_done fires after each text chunk,
      // not when the agent is truly finished. agent_complete only fires at the very end.
      window.socket.on('agent_start', (data) => {
        if (data.session_id) {
          this.setTabProcessing(data.session_id, true);
        }
      });
      window.socket.on('agent_complete', (data) => {
        if (data.session_id) {
          this.setTabProcessing(data.session_id, false);
        }
      });
      window.socket.on('agent_cancelled', (data) => {
        if (data.session_id) {
          this.setTabProcessing(data.session_id, false);
        }
      });
      window.socket.on('agent_error', (data) => {
        if (data.session_id) {
          this.setTabProcessing(data.session_id, false);
        }
      });
      
      // Handle reconnection to a session that's still processing
      window.socket.on('agent_reconnected', (data) => {
        if (data.session_id) {
          this.setTabProcessing(data.session_id, !!data.processing);
        }
      });
    }
    
    // Initialize notification sound
    this.initNotificationSound();
  }

  initNotificationSound() {
    // Create a subtle notification sound using Web Audio API
    this.audioContext = null;
    this.notificationEnabled = true;
    
    // Lazy initialize audio context on first user interaction
    const initAudio = () => {
      if (!this.audioContext) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      document.removeEventListener('click', initAudio);
      document.removeEventListener('keydown', initAudio);
    };
    document.addEventListener('click', initAudio);
    document.addEventListener('keydown', initAudio);
  }

  playNotificationSound() {
    if (!this.notificationEnabled || !this.audioContext) return;
    
    try {
      const ctx = this.audioContext;
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);
      
      // Pleasant two-tone chime
      oscillator.type = 'sine';
      oscillator.frequency.setValueAtTime(880, ctx.currentTime); // A5
      oscillator.frequency.setValueAtTime(1108.73, ctx.currentTime + 0.1); // C#6
      
      gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      
      oscillator.start(ctx.currentTime);
      oscillator.stop(ctx.currentTime + 0.3);
    } catch (e) {
      console.warn('Failed to play notification sound:', e);
    }
  }

  handleAgentComplete(data) {
    const sessionId = data.session_id;
    const tabId = this.findTabBySessionId(sessionId);
    
    if (!tabId) return;
    
    // If this tab is not currently active, make it glow
    if (tabId !== this.layout.main.activeTab) {
      this.setTabNeedsAttention(tabId, true);
      this.playNotificationSound();
    }
  }

  setTabProcessing(sessionId, isProcessing) {
    if (!sessionId) return;

    // First, try to find in current project's tabs
    let tabId = this.findTabBySessionId(sessionId);
    let targetLayout = this.layout.main;
    let tab = tabId ? targetLayout.tabs.find(t => t.id === tabId) : null;
    
    // If not found in current project, search all projects' saved tabs
    if (!tab && this.layout.projects) {
      for (const [projectId, projectLayout] of Object.entries(this.layout.projects)) {
        if (projectLayout.tabs) {
          const foundTab = projectLayout.tabs.find(t => t.config?.sessionId === sessionId);
          if (foundTab) {
            tab = foundTab;
            tabId = foundTab.id;
            targetLayout = projectLayout; // Track which layout we're updating
            break;
          }
        }
      }
    }
    
    if (!tab) return;
    
    // Persist state in tab config so it survives project switches
    tab.config = tab.config || {};
    tab.config.isProcessing = isProcessing;
    // Clear needs-attention when processing starts
    if (isProcessing) {
      tab.config.needsAttention = false;
    }
    
    // Only update DOM if tab is in current project (visible)
    if (targetLayout === this.layout.main) {
      const tabBtn = this.container.querySelector(`.main-tabs .tab[data-tab="${tabId}"]`);
      if (tabBtn) {
        tabBtn.classList.toggle('processing', isProcessing);
        if (isProcessing) {
          tabBtn.classList.remove('needs-attention');
        }
      }
    }
    
    // Save layout to persist the isProcessing state
    this.save();
  }

  setTabNeedsAttention(tabId, needsAttention) {
    // Persist state in tab config so it survives project switches
    const tab = this.layout.main.tabs.find(t => t.id === tabId);
    if (tab) {
      tab.config = tab.config || {};
      tab.config.needsAttention = needsAttention;
    }
    
    const tabBtn = this.container.querySelector(`.main-tabs .tab[data-tab="${tabId}"]`);
    if (tabBtn) {
      tabBtn.classList.toggle('needs-attention', needsAttention);
    }
  }

  // Find tab by session ID - searches current project only
  // For cross-project search, use the logic in setTabProcessing
  findTabBySessionId(sessionId) {
    for (const tab of this.layout.main.tabs) {
      if (tab.config?.sessionId === sessionId) {
        return tab.id;
      }
    }
    return null;
  }

  renderSidebarTabs() {
    const sidebar = this.container.querySelector('.sidebar');
    const tabBar = sidebar.querySelector('.tab-bar');
    const content = sidebar.querySelector('.sidebar-content');
    const config = this.layout.sidebar;

    tabBar.innerHTML = config.tabs.map(tab => `
      <button class="tab ${tab.id === config.activeTab ? 'active' : ''}" data-tab="${tab.id}" title="${tab.title}">
        <span class="tab-icon">${tab.icon || ''}</span>
        <span>${tab.title}</span>
      </button>
    `).join('');

    tabBar.querySelectorAll('.tab').forEach(btn => {
      btn.addEventListener('click', () => this.activateTab('sidebar', btn.dataset.tab));
    });

    // Render active component
    this.mountComponent(content, config, config.activeTab);
  }

  renderRightPanel() {
    const rightPanel = this.container.querySelector('.right-panel');
    if (!rightPanel) return;
    
    const content = rightPanel.querySelector('.right-panel-content');
    const config = this.layout.right;
    if (!config?.tabs?.length) return;
    
    // Mount the focus component directly (no tab bar needed)
    this.mountComponent(content, config, config.activeTab);
  }

  renderRegion(region, selector) {
    const el = this.container.querySelector(selector);
    if (!el) return;

    const tabBar = el.querySelector('.tab-bar');
    const content = el.querySelector('.tab-content');
    const config = this.layout[region];
    if (!config?.tabs?.length) return;

    // Build tab classes including persisted animation states
    const getTabClasses = (tab) => {
      const classes = ['tab'];
      if (tab.id === config.activeTab) classes.push('active');
      // Restore animation states from config (survives project switches)
      if (tab.config?.isProcessing) classes.push('processing');
      if (tab.config?.needsAttention) classes.push('needs-attention');
      return classes.join(' ');
    };

    tabBar.innerHTML = config.tabs.map(tab => `
      <button class="${getTabClasses(tab)}" data-tab="${tab.id}">
        <span>${tab.title}</span>
        ${region !== 'right' ? '<span class="tab-close">×</span>' : ''}
      </button>
    `).join('') + (region === 'main' ? '<button class="tab tab-add" title="New Tab">+</button>' : '');

    tabBar.querySelectorAll('.tab:not(.tab-add)').forEach(btn => {
      btn.addEventListener('click', (e) => {
        if (e.target.classList.contains('tab-close')) {
          this.closeTab(region, btn.dataset.tab);
        } else {
          this.activateTab(region, btn.dataset.tab);
        }
      });
    });

    const addBtn = tabBar.querySelector('.tab-add');
    if (addBtn) addBtn.addEventListener('click', () => this.addTab(region, 'chat'));

    this.mountComponent(content, config, config.activeTab);
  }

  mountComponent(container, config, tabId) {
    const tabConfig = config.tabs.find(t => t.id === tabId);
    if (!tabConfig) return;

    let instance = this.instances.get(tabId);
    let needsScrollRestore = false;
    
    if (!instance) {
      const Component = this.components[tabConfig.component];
      if (!Component) {
        console.warn(`Unknown component: ${tabConfig.component}`);
        return;
      }
      instance = new Component();
      instance.configure(tabConfig.config || {});
      instance.setAttribute('data-tab-id', tabId);
      this.instances.set(tabId, instance);
      container.appendChild(instance);
    } else if (!instance.parentNode) {
      // Instance exists but was detached from DOM (e.g., project switch)
      // Re-append it to the container
      container.appendChild(instance);
      needsScrollRestore = true;
    }

    // Hide all tabs, show only the active one
    for (const child of container.children) {
      child.style.display = child.getAttribute('data-tab-id') === tabId ? '' : 'none';
    }
    
    // Restore scroll position after re-attaching (must be done after display is set)
    // Also restore on regular tab switch since scroll state was saved in activateTab
    if (instance._savedScrollState) {
      // Use requestAnimationFrame to ensure DOM has fully updated
      requestAnimationFrame(() => {
        this.restoreScrollState(instance);
      });
    }
    // NOTE: Don't call loadFocusedFiles() here - it causes network requests on every tab switch.
    // The focus bar is already rendered in the DOM and updates via socket events.
  }

  /**
   * Save scroll positions of all scrollable elements within a component.
   * Called before detaching from DOM (which resets scroll state).
   * Result should be stored on instance._savedScrollState.
   */
  saveScrollState(instance) {
    const scrollState = {};
    
    // Chat component: save .chat-messages scroll
    const chatMessages = instance.querySelector?.('.chat-messages');
    if (chatMessages) {
      scrollState.chatMessages = chatMessages.scrollTop;
    }
    
    // Terminal component: save .terminal-output scroll
    const terminalOutput = instance.querySelector?.('.terminal-output');
    if (terminalOutput) {
      scrollState.terminalOutput = terminalOutput.scrollTop;
    }
    
    // Tree component: save .tree-list scroll
    const treeList = instance.querySelector?.('.tree-list');
    if (treeList) {
      scrollState.treeList = treeList.scrollTop;
    }
    
    return scrollState;
  }

  /**
   * Restore scroll positions after re-attaching to DOM.
   * Reads from instance._savedScrollState (saved before detaching).
   */
  restoreScrollState(instance) {
    const scrollState = instance._savedScrollState;
    if (!scrollState) return;
    
    // Restore chat messages scroll
    if (scrollState.chatMessages !== undefined) {
      const chatMessages = instance.querySelector?.('.chat-messages');
      if (chatMessages) {
        chatMessages.scrollTop = scrollState.chatMessages;
      }
    }
    
    // Restore terminal output scroll
    if (scrollState.terminalOutput !== undefined) {
      const terminalOutput = instance.querySelector?.('.terminal-output');
      if (terminalOutput) {
        terminalOutput.scrollTop = scrollState.terminalOutput;
      }
    }
    
    // Restore tree list scroll
    if (scrollState.treeList !== undefined) {
      const treeList = instance.querySelector?.('.tree-list');
      if (treeList) {
        treeList.scrollTop = scrollState.treeList;
      }
    }
    
    // Keep the saved state - don't delete it
    // It stays on the instance forever as the "last known scroll position"
  }

  activateTab(region, tabId) {
    const config = region === 'sidebar' ? this.layout.sidebar : this.layout[region];
    if (!config) return;

    // Save scroll state of currently active tab before switching
    const previousTabId = config.activeTab;
    if (previousTabId && previousTabId !== tabId) {
      const previousInstance = this.instances.get(previousTabId);
      if (previousInstance) {
        previousInstance._savedScrollState = this.saveScrollState(previousInstance);
      }
    }

    config.activeTab = tabId;

    // Update tab bar
    const selector = region === 'sidebar' ? '.sidebar' : 
                     region === 'main' ? '.main-content' :
                     region === 'bottom' ? '.bottom-panel' : '.right-panel';
    const el = this.container.querySelector(selector);
    el.querySelectorAll('.tab-bar .tab').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
      // Clear attention state when tab is activated
      if (btn.dataset.tab === tabId) {
        btn.classList.remove('needs-attention');
        // Also clear persisted state in config
        const tab = config.tabs.find(t => t.id === tabId);
        if (tab && tab.config) {
          tab.config.needsAttention = false;
        }
      }
    });

    // Mount component
    const content = region === 'sidebar' ? el.querySelector('.sidebar-content') : el.querySelector('.tab-content');
    this.mountComponent(content, config, tabId);

    this.save();
    bus.emit('tab-activated', { region, tabId });
    // NOTE: Don't call loadTokenStats() here - it causes network requests on every tab switch.
    // Token stats update via socket events (agent_done, tool_done) and on session load.
  }

  async addTab(region, componentType, config = {}) {
    const id = `${componentType}-${Date.now()}`;
    let title = config.title || componentType;
    
    // For chat tabs, create a new session
    if (componentType === 'chat' && !config.sessionId) {
      try {
        // Robustly determine project ID: Use internal state, or fallback to DOM attribute, or default to local
        const projectId = this.currentProject || this.container.querySelector('.workspace')?.dataset.project || 'local';
        const payload = { project_id: projectId };
        
        const res = await fetch('/api/new-session', { 
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          config.sessionId = data.session_id;
          title = 'New Chat';
        }
      } catch (e) {
        console.error('Failed to create session for new tab:', e);
      }
    }
    
    const tab = { id, title, component: componentType, config };
    this.layout[region].tabs.push(tab);
    
    const selector = region === 'main' ? '.main-content' : region === 'bottom' ? '.bottom-panel' : '.right-panel';
    this.renderRegion(region, selector);
    this.activateTab(region, id);
    
    this.save();
    return id;
  }

  closeTab(region, tabId) {
    const config = this.layout[region];
    const idx = config.tabs.findIndex(t => t.id === tabId);
    if (idx === -1) return;

    config.tabs.splice(idx, 1);
    
    const instance = this.instances.get(tabId);
    if (instance) {
      instance.remove();
      this.instances.delete(tabId);
    }

    if (config.activeTab === tabId && config.tabs.length) {
      config.activeTab = config.tabs[Math.min(idx, config.tabs.length - 1)].id;
    }

    const selector = region === 'main' ? '.main-content' : region === 'bottom' ? '.bottom-panel' : '.right-panel';
    this.renderRegion(region, selector);
    
    this.save();
  }

  toggleRegion(region) {
    const config = this.layout[region];
    config.collapsed = !config.collapsed;

    if (region === 'sidebar') {
      this.container.querySelector('.sidebar').classList.toggle('collapsed', config.collapsed);
    } else if (region === 'bottom') {
      this.container.querySelector('.bottom-panel').classList.toggle('collapsed', config.collapsed);
    } else if (region === 'right') {
      this.container.querySelector('.workspace').classList.toggle('right-open', !config.collapsed);
    }

    this.save();
    bus.emit('region-toggled', { region, collapsed: config.collapsed });
  }

  async setProject(projectId, sessionId = null) {
    // 1. Save current project's tab state AND instances
    if (this.currentProject) {
      // Deep copy layout to disconnect from layout.main
      this.layout.projects[this.currentProject] = JSON.parse(JSON.stringify(this.layout.main));
      
      // Save instances for this project (don't destroy them!)
      if (!this.projectInstances) this.projectInstances = {};
      this.projectInstances[this.currentProject] = {};
      
      if (this.layout.main && this.layout.main.tabs) {
        const activeTabId = this.layout.main.activeTab;
        this.layout.main.tabs.forEach(t => {
          const instance = this.instances.get(t.id);
          if (instance) {
            // Only save scroll for the ACTIVE tab - inactive tabs already have
            // their scroll saved from when we switched away from them.
            // Reading scrollTop from a hidden element returns 0, which would
            // incorrectly overwrite the saved position.
            if (t.id === activeTabId) {
              instance._savedScrollState = this.saveScrollState(instance);
            }
            
            // Hide and detach from DOM, but keep in memory
            instance.style.display = 'none';
            if (instance.parentNode) {
              instance.parentNode.removeChild(instance);
            }
            // Store in project-specific cache
            this.projectInstances[this.currentProject][t.id] = instance;
            this.instances.delete(t.id);
          }
        });
      }
    }

    // 2. Load new project's tab state
    if (this.layout.projects[projectId]) {
      this.layout.main = JSON.parse(JSON.stringify(this.layout.projects[projectId]));
    } else {
      // Default state for new projects - Use unique ID to prevent instance sharing!
      const newChatId = `chat-${Date.now()}`;
      this.layout.main = {
        tabs: [{ id: newChatId, title: 'Chat', component: 'chat', config: {} }],
        activeTab: newChatId
      };
    }
    
    // 3. Restore instances for new project if we have them cached
    if (this.projectInstances && this.projectInstances[projectId]) {
      const cached = this.projectInstances[projectId];
      for (const [tabId, instance] of Object.entries(cached)) {
        this.instances.set(tabId, instance);
      }
    }

    // 4. Update local UI state
    this.currentProject = projectId;
    this.layout.currentProject = projectId; // Persist for reload
    this.container.querySelector('.workspace').dataset.project = projectId;
    const projectName = this.container.querySelector('#project-name');
    if (projectName) projectName.textContent = projectId;
    
    // 5. Re-render main region tabs (will reuse cached instances)
    this.renderRegion('main', '.main-content');
    
    // 6. Only load session if we don't have a cached instance
    const activeChat = this.getActiveChat();
    const activeTabId = this.layout.main.activeTab;
    const hadCachedInstance = this.projectInstances?.[projectId]?.[activeTabId];
    
    if (sessionId && !hadCachedInstance) {
      // Specific session requested and no cache - load it
      if (activeChat && activeChat.loadSession) {
        await activeChat.loadSession(sessionId);
        
        // Update tab config to reflect this session
        const activeTab = this.layout.main.tabs.find(t => t.id === this.layout.main.activeTab);
        if (activeTab) {
          activeTab.config.sessionId = sessionId;
        }
      }
    } else if (!hadCachedInstance) {
      // No cache - load current session
      if (activeChat && activeChat.loadCurrentSession) {
        await activeChat.loadCurrentSession();
      }
    }
    // If we had a cached instance, it already has its content - no API call needed!
    // But we still need to update token stats for the restored session
    if (hadCachedInstance) {
      this.loadTokenStats();
    }
    
    this.save();
    bus.emit('project-changed', { projectId, sessionId });
  }

  updateTabTitle(region, tabId, title) {
    const config = this.layout[region];
    if (!config) return;
    
    const tab = config.tabs.find(t => t.id === tabId);
    if (tab) {
      tab.title = title;
      const selector = region === 'main' ? '.main-content' : 
                       region === 'bottom' ? '.bottom-panel' : '.right-panel';
      const el = this.container.querySelector(selector);
      const tabBtn = el?.querySelector(`.tab[data-tab="${tabId}"] span`);
      if (tabBtn) tabBtn.textContent = title;
      this.save();
    }
  }

  bindToolbarEvents() {
    this.container.querySelector('#toggle-sidebar-left')?.addEventListener('click', () => {
      if (this.isMobile) {
        this.toggleMobilePanel('sidebar');
      } else {
        this.toggleRegion('sidebar');
      }
    });
    this.container.querySelector('#toggle-bottom')?.addEventListener('click', () => this.toggleRegion('bottom'));
    this.container.querySelector('#toggle-right')?.addEventListener('click', () => {
      if (this.isMobile) {
        this.toggleMobilePanel('right');
      } else {
        // If we're opening it, ensure it's not collapsed internally
        if (this.layout.right.collapsed) {
          this.layout.right.collapsed = false;
          this.container.querySelector('.right-panel')?.classList.remove('collapsed');
          this.container.querySelector('.workspace').classList.add('right-open');
          this.save();
          // Initial render of content if needed
          this.renderRightPanel();
        } else {
          this.toggleRegion('right');
        }
      }
    });
    
    // Mobile backdrop click to close panels
    this.container.querySelector('#mobile-backdrop')?.addEventListener('click', () => {
      this.closeMobilePanels();
    });
    
    // Listen for viewport changes (e.g., device rotation)
    window.matchMedia('(max-width: 768px)').addEventListener('change', (e) => {
      this.isMobile = e.matches;
      if (!this.isMobile) {
        // Switched to desktop - close mobile panels and remove classes
        this.closeMobilePanels();
      }
    });
  }

  async initModelSelector() {
    const trigger = this.container.querySelector('#model-selector-trigger');
    const dropdown = this.container.querySelector('#model-selector-dropdown');
    const label = this.container.querySelector('#model-name-label');
    const list = this.container.querySelector('#model-dropdown-list');

    if (!trigger || !dropdown) return;

    // Toggle dropdown
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('hidden');
      if (!dropdown.classList.contains('hidden')) {
        this.refreshModelSelector();
      }
    });

    // Close on outside click
    document.addEventListener('click', () => {
      dropdown.classList.add('hidden');
    });

    // Initial load
    this.refreshModelSelector();
  }

  async refreshModelSelector() {
    const label = this.container.querySelector('#model-name-label');
    const list = this.container.querySelector('#model-dropdown-list');
    
    try {
      // Force a refresh from the server to get latest active state
      const res = await fetch('/api/llm/providers?fetch_models=1');
      const data = await res.json();
      
      const activeProvider = data.active?.provider;
      const activeModel = data.active?.model;
      
      if (label) {
        label.textContent = activeModel || 'Select Model';
      }
      
      // Update status bar too
      this.updateStatus('model', activeModel || 'Connected');

      if (list) {
        list.innerHTML = data.providers.map(p => {
          if (!p.hasKey && !p.isLocal) return '';
          
          const models = p.models || [];
          if (models.length === 0) return '';

          return `
            <div class="model-dropdown-provider">
              <div class="model-dropdown-provider-name">${p.name}</div>
              ${models.map(m => `
                <div class="model-dropdown-item ${activeProvider === p.id && activeModel === m.id ? 'active' : ''}" 
                     data-provider="${p.id}" data-model="${m.id}">
                  ${m.name || m.id}
                </div>
              `).join('')}
            </div>
          `;
        }).join('');

        // Bind clicks
        list.querySelectorAll('.model-dropdown-item').forEach(item => {
          item.addEventListener('click', async () => {
            const providerId = item.dataset.provider;
            const modelId = item.dataset.model;
            
            try {
              const res = await fetch('/api/llm/active', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider_id: providerId, model_id: modelId })
              });
              const result = await res.json();
              if (result.success) {
                // 1. Refresh the selector label
                await this.refreshModelSelector();
                // 2. IMMEDIATELY refresh token stats for the current session
                await this.loadTokenStats();
              }
            } catch (err) {
              console.error('Failed to set active model:', err);
            }
          });
        });
      }
    } catch (err) {
      console.error('Failed to load providers for selector:', err);
    }
  }
  
  toggleMobilePanel(panel) {
    const sidebar = this.container.querySelector('.sidebar');
    const rightPanel = this.container.querySelector('.right-panel');
    const backdrop = this.container.querySelector('#mobile-backdrop');
    
    if (panel === 'sidebar') {
      const isOpen = sidebar.classList.contains('mobile-open');
      // Close right panel if open
      rightPanel?.classList.remove('mobile-open');
      
      if (isOpen) {
        sidebar.classList.remove('mobile-open');
        backdrop?.classList.remove('visible');
      } else {
        sidebar.classList.add('mobile-open');
        backdrop?.classList.add('visible');
      }
    } else if (panel === 'right') {
      const isOpen = rightPanel?.classList.contains('mobile-open');
      // Close sidebar if open
      sidebar?.classList.remove('mobile-open');
      
      if (isOpen) {
        rightPanel?.classList.remove('mobile-open');
        backdrop?.classList.remove('visible');
      } else {
        rightPanel?.classList.add('mobile-open');
        backdrop?.classList.add('visible');
      }
    }
  }
  
  closeMobilePanels() {
    const sidebar = this.container.querySelector('.sidebar');
    const rightPanel = this.container.querySelector('.right-panel');
    const backdrop = this.container.querySelector('#mobile-backdrop');
    
    sidebar?.classList.remove('mobile-open');
    rightPanel?.classList.remove('mobile-open');
    backdrop?.classList.remove('visible');
  }

  bindKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl+` toggle terminal
      if (e.ctrlKey && e.key === '`') {
        e.preventDefault();
        this.toggleRegion('bottom');
      }
      // Ctrl+B toggle sidebar
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        this.toggleRegion('sidebar');
      }
      // Ctrl+T new tab
      if (e.ctrlKey && e.key === 't') {
        e.preventDefault();
        this.addTab('main', 'chat');
      }
      // Ctrl+W close tab
      if (e.ctrlKey && e.key === 'w') {
        e.preventDefault();
        const activeTab = this.layout.main.activeTab;
        if (this.layout.main.tabs.length > 1) {
          this.closeTab('main', activeTab);
        }
      }
    });
  }

  save() {
    saveLayout(this.layout);
  }

  getActiveChat() {
    const tabId = this.layout.main.activeTab;
    return this.instances.get(tabId);
  }

  updateStatus(key, value) {
    const el = this.container.querySelector(`#status-${key}`);
    if (el) el.textContent = value;
  }

  async loadTokenStats() {
    try {
      const chat = this.getActiveChat();
      const sessionId = chat?.currentSessionId;
      
      // If we don't have a session ID, don't fetch (prevents getting zeroed fallback stats)
      if (!sessionId) {
        console.warn('[Workspace] Cannot load token stats: No active session ID found');
        return;
      }

      const url = `/api/context-stats?session_id=${encodeURIComponent(sessionId)}`;
      const res = await fetch(url);
      if (!res.ok) {
        console.warn('Token stats API returned', res.status);
        return;
      }
      const stats = await res.json();
      this.updateToolbarTokenBar(stats);
    } catch (e) {
      console.error('Failed to load token stats:', e);
    }
  }

  updateToolbarTokenBar(stats) {
    const track = this.container.querySelector('#toolbar-token-track');
    const label = this.container.querySelector('#toolbar-token-label');
    const tooltip = this.container.querySelector('#toolbar-token-tooltip');
    if (!track || !stats) return;

    const budget = stats.budget;
    const total = stats.total;
    const formatK = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : n.toString();
    const pct = (n) => Math.max(0, Math.min(100, (n / budget) * 100));
    const thresholdPct = (stats.threshold / budget) * 100;

    // Update label
    label.textContent = `${formatK(total)}/${formatK(budget)}`;

    // Combine system + tree as "system", and gists into history
    const systemTotal = stats.system + stats.tree;
    const historyTotal = stats.history + stats.gists;
    
    // Calculate cumulative widths (each bar covers all previous + itself)
    // Order from bottom to top: focus, history, system
    const focusPct = pct(stats.focus + historyTotal + systemTotal);
    const historyPct = pct(historyTotal + systemTotal);
    const systemPct = pct(systemTotal);

    // Update track with stacked bars (lower z-index = further back = wider)
    track.innerHTML = `
      <div class="bar focus" style="width: ${focusPct}%"></div>
      <div class="bar history" style="width: ${historyPct}%"></div>
      <div class="bar system" style="width: ${systemPct}%"></div>
      <div class="threshold" style="left: ${thresholdPct}%"></div>
    `;

    // Update tooltip - combine tree into system
    const rows = [
      { cls: 'system', label: 'System', value: stats.system + stats.tree },
      { cls: 'history', label: 'History', value: stats.history },
    ];
    if (stats.gists > 0) {
      rows.push({ cls: 'gists', label: `Gists (${stats.gist_count})`, value: stats.gists });
    }
    rows.push({ cls: 'focus', label: `Focus (${stats.focus_count})`, value: stats.focus });
    rows.push({ cls: 'threshold', label: 'Threshold', value: stats.threshold });

    tooltip.innerHTML = rows.map(r => `
      <div class="tooltip-row">
        <span class="dot ${r.cls}"></span>
        <span class="label">${r.label}</span>
        <span class="value">${formatK(r.value)}</span>
      </div>
    `).join('');
  }
}
