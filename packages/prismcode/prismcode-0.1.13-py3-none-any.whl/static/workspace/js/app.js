/* Prism Workspace - Main App */
import { Workspace } from './core/workspace.js';
import { bus } from './core/events.js';
import { PrismChat } from './components/chat.js';
import { PrismTree } from './components/tree.js';
import { PrismTerminal } from './components/terminal.js';
import { PrismSettings } from './components/settings.js';
import { PrismFocus } from './components/focus.js';
import { ProjectBar } from './components/project-bar.js';
import { PrismPreferences } from './components/preferences/index.js';

// Component registry
const components = {
  'chat': PrismChat,
  'tree': PrismTree,
  'terminal': PrismTerminal,
  'settings': PrismSettings,
  'focus': PrismFocus
};

class PrismApp {
  constructor() {
    this.workspace = null;
    this.socket = null;
  }

  init() {
    // Initialize socket
    this.socket = io();
    window.socket = this.socket;

    // Initialize workspace
    const container = document.getElementById('app');
    this.workspace = new Workspace(container, components);
    this.workspace.render();

    // Initialize preferences modal
    this.preferences = document.createElement('prism-preferences');
    document.body.appendChild(this.preferences);
    
    // toggle-right button now toggles the focus panel (right panel)
    // Settings are accessed via Cmd+, keyboard shortcut
    
    // Listen for open-preferences event from project bar
    bus.on('open-preferences', ({ pane, action }) => {
      // Switch to the requested pane and show
      if (pane && this.preferences.panes.find(p => p.id === pane)) {
        this.preferences.activePane = pane;
      }
      this.preferences.show();
    });
    
    // Keyboard shortcut: Cmd/Ctrl + , to open preferences
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        this.preferences.toggle();
      }
    });

    // Setup event handlers
    this.setupEventHandlers();

    console.log('Prism Workspace initialized');
  }

  setupEventHandlers() {
    // Session events
    bus.on('session-loaded', (data) => {
      // Handle both formats: { session, history } from tree.js and { sessionId, ... } from chat.js
      const sessionId = data?.sessionId || data?.session?.session_id;
      const history = data?.history || data?.session?.history;
      const session = data?.session || { session_id: sessionId, title: data?.title };
      const projectId = data?.project_id || data?.session?.project_id;
      
      // Update workspace project context if provided (Fixes project color/selection desync)
      if (projectId && projectId !== this.workspace.currentProject) {
        console.log(`[App] Syncing project context to ${projectId} for session ${sessionId}`);
        this.workspace.currentProject = projectId;
        this.workspace.layout.currentProject = projectId;
        document.querySelector('.workspace').dataset.project = projectId;
        
        // Reload project bar to update selection and colors
        const projectBar = document.querySelector('project-bar');
        if (projectBar) {
          projectBar.currentProjectId = projectId;
          projectBar.loadProjects(); // This also updates global CSS variables for colors
        }
      }

      // Check if session is already open in a tab
      const existingTabId = this.workspace.findTabBySessionId(sessionId);
      if (existingTabId) {
        // Switch to that tab instead of loading into current
        this.workspace.activateTab('main', existingTabId);
        return;
      }
      
      // Load into current tab
      const chat = this.workspace.getActiveChat();
      if (chat) {
        chat.currentSessionId = sessionId;
        chat.messagesEl.innerHTML = '';
        if (history) chat.loadHistory(history);
        
        // Load focused files for this session
        chat.loadFocusedFiles();
        
        // Update the current tab's config to track this session
        const activeTab = this.workspace.layout.main.activeTab;
        const tabConfig = this.workspace.layout.main.tabs.find(t => t.id === activeTab);
        if (tabConfig) {
          tabConfig.config.sessionId = sessionId;
          // Update tab title
          const title = session.title || `Chat ${sessionId.substring(0, 6)}`;
          this.workspace.updateTabTitle('main', activeTab, title);
          this.workspace.save(); // Persist the session association
        }
      }
      this.workspace.updateStatus('session', `Session: ${sessionId?.substring(0, 8)}...`);
      
      // Sync tab processing state from server's actual state
      if (sessionId) {
        const isProcessing = data?.processing || data?.session?.processing || false;
        this.workspace.setTabProcessing(sessionId, isProcessing);
      }
    });

    bus.on('session-created', ({ sessionId }) => {
      const chat = this.workspace.getActiveChat();
      if (chat) {
        chat.currentSessionId = sessionId;
        // chat.messagesEl.innerHTML = ''; // Already cleared by Chat component
      }
      
      // Update the current tab's config to track this session
      const activeTab = this.workspace.layout.main.activeTab;
      const tabConfig = this.workspace.layout.main.tabs.find(t => t.id === activeTab);
      if (tabConfig) {
        tabConfig.config.sessionId = sessionId;
        this.workspace.updateTabTitle('main', activeTab, `Chat ${sessionId.substring(0, 6)}`);
        this.workspace.save(); // Persist the session association
      }
      
      this.workspace.updateStatus('session', `Session: ${sessionId.substring(0, 8)}...`);
    });
    
    // Update tab title when title is generated
    bus.on('title-updated', ({ session_id, title }) => {
      const tabId = this.workspace.findTabBySessionId(session_id);
      if (tabId) {
        this.workspace.updateTabTitle('main', tabId, title);
      }
    });

    // Project events
    bus.on('project-switched', (data) => {
      // Handle both { projectId } and { project: { id } } formats
      const projectId = data.projectId || data.project?.id;
      if (projectId) {
        this.workspace.setProject(projectId, data.sessionId);
      }
    });

    // Socket events for status
    this.socket.on('connect', () => {
      this.workspace.updateStatus('model', 'Connected');
    });

    this.socket.on('disconnect', () => {
      this.workspace.updateStatus('model', 'Disconnected');
    });
    
    // Handle provider change events
    this.socket.on('provider_changed', (data) => {
      console.log('[App] Provider changed:', data);
      
      // Show notification
      const message = data.message || `Switched to ${data.model_id}`;
      this.workspace.showToast(message, 'success');
      
      // Reload context stats for all open chat components
      const chats = document.querySelectorAll('prism-chat');
      chats.forEach(chat => {
        if (chat.loadContextStats) {
          chat.loadContextStats();
        }
      });
      
      // Update model display in status bar
      this.workspace.updateStatus('model', data.model_id);
      
      // Update token bar instantly if stats were pushed
      if (data.stats) {
        this.workspace.updateToolbarTokenBar(data.stats);
      }
      
      // Refresh model selector list/label to reflect new active model
      this.workspace.refreshModelSelector();
      // Refresh token stats to reflect new model context window
      this.workspace.loadTokenStats();
    });

    this.socket.on('provider_models_updated', (data) => {
      console.log('[App] Provider models updated:', data);
      this.workspace.refreshModelSelector();
    });
  }

  // Legacy method removed - Chat components now self-load their sessions based on project context
  // async loadCurrentSession() { ... }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.app = new PrismApp();
  window.app.init();
});
