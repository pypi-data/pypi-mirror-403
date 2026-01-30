/* Prism Workspace - Focus Component
 * 
 * Displays focused files for the active session.
 * Refreshes when:
 * - Tab is switched (tab-activated event)
 * - Session is loaded (session-loaded event with session_id)
 * - Focus changes (focused_files_updated socket event)
 * - Manual refresh button clicked
 */
import { PrismComponent } from './base.js';
import { bus } from '../core/events.js';

export class PrismFocus extends PrismComponent {
  constructor() {
    super();
    this.files = [];
    this.currentSessionId = null;
    this._pollInterval = null;
  }

  render() {
    this.innerHTML = `
      <div class="focus-panel">
        <div class="focus-header">
          <div class="focus-stats">
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
            <span class="focus-count">0 files</span>
            <span class="focus-lines">0 lines</span>
          </div>
          <button class="btn btn-ghost btn-sm" id="refresh-btn" title="Refresh">↻</button>
        </div>
        <div class="focus-list"></div>
      </div>
    `;
    this.listEl = this.$('.focus-list');
    this.countEl = this.$('.focus-count');
    this.linesEl = this.$('.focus-lines');
    
    // Initial load with retry logic
    this.loadWithRetry();
  }

  setupEvents() {
    this.$('#refresh-btn')?.addEventListener('click', () => this.load());

    // Socket event: focus changed
    if (window.socket) {
      window.socket.on('focused_files_updated', (data) => {
        // If event has a session_id, only refresh if it matches our current session
        // If no session_id, refresh anyway (legacy compatibility)
        if (data.session_id) {
          if (data.session_id === this.currentSessionId) {
            this.files = data.files?.map(f => typeof f === 'string' ? { path: f, lines: 0 } : f) || [];
            if (this.files.some(f => f.lines === 0)) {
               // If any files have 0 lines (which happens with socket push), 
               // trigger a full reload to get stats
               this.load();
            } else {
               this.renderList();
            }
          }
        } else {
          // No session_id in event - refresh to be safe
          this.load();
        }
      });
    }

    // Bus event: tab switched in main region
    bus.on('tab-activated', ({ region, tabId }) => {
      if (region === 'main') {
        // When tab switches, we need to get the new session from that tab
        // Use requestAnimationFrame to let DOM update first
        requestAnimationFrame(() => {
          this.loadWithRetry();
        });
      }
    });
    
    // Bus event: session loaded (from tree.js or chat.js)
    bus.on('session-loaded', (data) => {
      // Extract session_id from various payload formats
      const sessionId = data?.sessionId || data?.session?.session_id || data?.session_id;
      if (sessionId) {
        this.currentSessionId = sessionId;
        // Use timeout to allow backend state to settle before fetching
        setTimeout(() => this.load(), 100);
      } else {
        // No session_id in payload, try to get from active chat
        this.loadWithRetry();
      }
    });

    // Bus event: project switched
    bus.on('project-changed', () => {
      // Reset and retry when project changes
      this.loadWithRetry();
    });
    
    // Bus event: new session created
    bus.on('session-created', (data) => {
      if (data?.sessionId) {
        this.currentSessionId = data.sessionId;
        this.files = [];
        this.renderList();
      }
    });
  }

  cleanup() {
    if (this._pollInterval) {
      clearInterval(this._pollInterval);
      this._pollInterval = null;
    }
  }

  /**
   * Try to load focused files, retrying if session ID isn't available yet.
   * This handles the race condition where the chat hasn't loaded its session yet.
   */
  async loadWithRetry(attempts = 0) {
    const maxAttempts = 5;
    const delayMs = 100;
    
    // Try to get session ID from active chat
    const sessionId = this.getSessionIdFromActiveChat();
    
    if (sessionId) {
      this.currentSessionId = sessionId;
      await this.load();
      return;
    }
    
    // No session ID yet
    if (attempts < maxAttempts) {
      // Retry after delay
      setTimeout(() => this.loadWithRetry(attempts + 1), delayMs);
    } else {
      // Give up - show empty state
      this.currentSessionId = null;
      this.listEl.innerHTML = '<div class="focus-empty">No active session</div>';
    }
  }

  /**
   * Get the session ID from the currently active chat component.
   */
  getSessionIdFromActiveChat() {
    try {
      if (window.app?.workspace) {
        const chat = window.app.workspace.getActiveChat();
        if (chat?.currentSessionId) {
          return chat.currentSessionId;
        }
        // Also check the tab config as fallback
        const activeTabId = window.app.workspace.layout?.main?.activeTab;
        const tabConfig = window.app.workspace.layout?.main?.tabs?.find(t => t.id === activeTabId);
        if (tabConfig?.config?.sessionId) {
          return tabConfig.config.sessionId;
        }
      }
    } catch (e) {
      console.warn('Failed to get session ID from active chat:', e);
    }
    return null;
  }

  async load() {
    if (!this.currentSessionId) {
      this.listEl.innerHTML = '<div class="focus-empty">No active session</div>';
      return;
    }

    try {
      const res = await fetch(`/api/focused-files?session_id=${encodeURIComponent(this.currentSessionId)}`);
      const data = await res.json();
      
      // Verify we got data for the right session
      if (data.session_id && data.session_id !== this.currentSessionId) {
        console.warn(`Focus: got data for session ${data.session_id} but expected ${this.currentSessionId}`);
        return;
      }
      
      this.files = data.files || [];
      this.renderList();
    } catch (e) {
      console.error('Failed to load focused files:', e);
      this.listEl.innerHTML = '<div class="focus-empty">Failed to load</div>';
    }
  }

  renderList() {
    if (!this.files.length) {
      this.listEl.innerHTML = '<div class="focus-empty">No files focused</div>';
      this.updateStats(0, 0);
      return;
    }

    const totalLines = this.files.reduce((sum, f) => sum + (f.lines || 0), 0);
    this.updateStats(this.files.length, totalLines);

    const formatLines = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : n.toString();

    this.listEl.innerHTML = this.files.map((f, i) => `
      <div class="focus-item" data-idx="${i}">
        <span class="focus-item-icon">◉</span>
        <div class="focus-item-content">
          <span class="focus-item-path">${this.escapeHtml(f.path)}</span>
          <span class="focus-item-lines">${formatLines(f.lines || 0)} lines</span>
        </div>
        <button class="focus-item-remove" data-idx="${i}" title="Unfocus">×</button>
      </div>
    `).join('');

    // Bind remove buttons
    this.listEl.querySelectorAll('.focus-item-remove').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.dataset.idx);
        const file = this.files[idx];
        if (file) {
          this.unfocusFile(file.path);
        }
      });
    });
  }

  updateStats(count, lines) {
    if (this.countEl) this.countEl.textContent = `${count} file${count !== 1 ? 's' : ''}`;
    if (this.linesEl) {
      const formatLines = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : n.toString();
      this.linesEl.textContent = `${formatLines(lines)} lines`;
    }
  }

  unfocusFile(path) {
    if (!this.currentSessionId) return;
    
    // Send unfocus command via socket with explicit session_id
    if (window.socket) {
      window.socket.emit('send_message', { 
        message: `/unfocus ${path}`,
        session_id: this.currentSessionId
      });
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }
}

customElements.define('prism-focus', PrismFocus);
