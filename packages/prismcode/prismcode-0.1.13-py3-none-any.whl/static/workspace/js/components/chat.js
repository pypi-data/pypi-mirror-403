/* Prism Workspace - Chat Component (Full Featured) */
import { PrismComponent } from './base.js';
import { bus } from '../core/events.js';
import { loadSetting } from '../core/storage.js';

export class PrismChat extends PrismComponent {
  constructor() {
    super();
    this.config = { session: null, project: 'local' };
    this.currentSessionId = null;  // Track which session this chat is showing
    this.isProcessing = false;
    this.streamingContent = '';
    this.currentMessage = null;
    this.currentStreamingTool = null;
    this.queuedMessage = null;
    this.showDiff = loadSetting('showDiff', true);
    this.focusedFiles = [];
    this.focusExpanded = false;
    
    // Scroll state management
    this.autoScroll = true;
    this.lastScrollTop = 0;
    this.programmaticScroll = false; // Flag to ignore our own scroll events
  }

  connectedCallback() {
    this.render();
    this.setupEvents();
  }

  disconnectedCallback() {
    this.cleanup();
  }

  render() {
    // Don't re-render if already rendered (preserve messages when switching tabs)
    if (this.messagesEl) {
      return;
    }
    this.innerHTML = `
      <div class="chat">
        <div class="chat-messages"></div>
        <div class="chat-focus-bar hidden"></div>
        <div class="chat-input">
          <div class="chat-activity hidden">
            <div class="activity-dots"><span></span><span></span><span></span></div>
            <span class="activity-text">Processing</span>
          </div>
          <div class="chat-input-group">
            <textarea placeholder="Type your message... (/ for commands)" rows="1"></textarea>
            <button class="btn btn-primary" id="send-btn"><span class="send-icon"></span></button>
          </div>
        </div>
      </div>
    `;
    this.messagesEl = this.$('.chat-messages');
    this.inputEl = this.$('textarea');
    this.sendBtn = this.$('#send-btn');
    this.activityEl = this.$('.chat-activity');
    this.activityText = this.$('.activity-text');
    this.focusBar = this.$('.chat-focus-bar');
    this.loadCurrentSession();
  }

  async loadSession(sessionId) {
    // Load a specific session by ID
    if (!sessionId || this.currentSessionId === sessionId) {
      return; // Already loaded
    }
    
    try {
      const oldSessionId = this.currentSessionId;
      this.currentSessionId = sessionId;
      this.config.sessionId = sessionId;
      
      // Join the session room to receive streaming events (including reconnection)
      window.socket?.emit('join_session', { session_id: sessionId, old_session_id: oldSessionId });
      
      const res = await fetch('/api/load-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      
      const data = await res.json();
      this.messagesEl.innerHTML = '';
      
      if (data.success) {
        if (data.history?.length > 0) {
          this.loadHistory(data.history);
        }
        
        // Update session display
        bus.emit('session-loaded', { 
          sessionId, 
          title: data.title,
          messageCount: data.message_count,
          processing: data.processing
        });
        
        // Reload focused files for new session
        this.loadFocusedFiles();
      }
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  }

  async loadCurrentSession() {
    try {
      // If config has a sessionId, load that session
      if (this.config.sessionId) {
        // Only reload if session changed
        if (this.currentSessionId === this.config.sessionId) {
          return; // Already loaded
        }
        this.currentSessionId = this.config.sessionId;
        
        // Join the session room to receive streaming events (including reconnection)
        window.socket?.emit('join_session', { session_id: this.config.sessionId, old_session_id: null });
        
        // Pass project ID context if known
        const payload = { session_id: this.config.sessionId };
        if (this.config.project) payload.project_id = this.config.project; // From old config?
        
        // Better: Get current project from workspace if available
        const workspace = document.querySelector('.workspace');
        if (workspace && workspace.dataset.project) {
            payload.project_id = workspace.dataset.project;
        }

        const res = await fetch('/api/load-session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.error && data.project_mismatch) {
            // If we tried to load a session that doesn't belong to this project,
            // we should probably bail out and create a new one instead of showing an error.
            console.warn('Session project mismatch, creating new session...');
            this.createNewSession();
            return;
        }

        this.messagesEl.innerHTML = '';
        if (data.success && data.history?.length > 0) {
          this.loadHistory(data.history);
        }
        
        // Emit session-loaded so app.js can sync processing state from server
        bus.emit('session-loaded', {
          sessionId: this.config.sessionId,
          title: data.title,
          messageCount: data.message_count,
          processing: data.processing
        });
        
        this.loadFocusedFiles();
        return;
      }
      
      // If NO session ID is configured (e.g. fresh tab in new project),
      // DO NOT fetch /api/current-session (that returns global history).
      // Instead, create a new session for the current project.
      await this.createNewSession();
      
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  }

  async createNewSession() {
    try {
        const workspace = document.querySelector('.workspace');
        const projectId = workspace?.dataset.project || 'local'; // Fallback to local
        
        const res = await fetch('/api/new-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId })
        });
        const data = await res.json();
        
        if (data.success) {
            this.currentSessionId = data.session_id;
            this.config.sessionId = data.session_id;
            this.messagesEl.innerHTML = '';
            // Emit event so Workspace can save this ID to config
            bus.emit('session-created', { sessionId: data.session_id });
        }
    } catch (e) {
        console.error('Failed to create new session:', e);
    }
  }

  // Switch to a different session
  async switchSession(sessionId) {
    if (sessionId === this.currentSessionId) return;
    
    try {
      const res = await fetch('/api/load-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
      });
      const data = await res.json();
      
      if (data.success) {
        this.currentSessionId = sessionId;
        this.messagesEl.innerHTML = '';
        if (data.history) this.loadHistory(data.history);
        bus.emit('session-switched', { sessionId, title: data.title });
      }
    } catch (e) {
      console.error('Failed to switch session:', e);
    }
  }

  // Check if an event belongs to this chat's session
  isMySession(data) {
    // If we don't have a session yet, reject ALL events (prevents duplicates during init)
    if (!this.currentSessionId) return false;
    
    // Strict check: Data MUST have session_id and it MUST match
    if (!data.session_id) return false; // Reject legacy/global events
    
    return data.session_id === this.currentSessionId;
  }  setupEvents() {
    this.sendBtn.addEventListener('click', () => this.handleSend());
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSend();
      }
    });
    this.inputEl.addEventListener('input', () => this.autoResize());
    
    // Track user scroll to manage auto-scroll behavior
    this.messagesEl.addEventListener('scroll', () => this.handleScroll());

    // Global escape to cancel - check multiple indicators of activity
    this._escHandler = (e) => {
      if (e.key === 'Escape') {
        // Check ALL indicators that we're processing
        const hasStreamingTool = this.currentStreamingTool !== null;
        const hasStreamingMessage = this.currentMessage !== null;
        const hasThinking = this.$('#thinking') !== null;
        const activityVisible = !this.activityEl.classList.contains('hidden');
        
        const isActive = this.isProcessing || hasStreamingTool || hasStreamingMessage || hasThinking || activityVisible;
        
        if (isActive) {
          window.socket?.emit('cancel');
          this.showActivity('Stopping...');
          // Force state reset after a delay if cancel doesn't complete
          setTimeout(() => {
            if (this.isProcessing) {
              this.finishProcessing();
            }
          }, 3000);
        }
      }
    };
    document.addEventListener('keydown', this._escHandler);

    // Socket events - filter by session_id
    // Store bound handlers so we can remove them in cleanup()
    if (window.socket) {
      this._socketHandlers = {
        user_message: (d) => { if (this.isMySession(d)) this.onUserMessage(d); },
        agent_start: (d) => { if (this.isMySession(d)) this.onAgentStart(); },
        agent_delta: (d) => { if (this.isMySession(d)) this.onAgentDelta(d); },
        agent_done: (d) => { if (this.isMySession(d)) this.onAgentDone(d); },
        agent_cancelled: (d) => { if (this.isMySession(d)) this.onAgentCancelled(d); },
        agent_error: (d) => { if (this.isMySession(d)) this.onAgentError(d); },
        tool_progress: (d) => { if (this.isMySession(d)) this.onToolProgress(d); },
        tool_start: (d) => { if (this.isMySession(d)) this.onToolStart(d); },
        tool_done: (d) => { if (this.isMySession(d)) this.onToolDone(d); },
        command_result: (d) => this.onCommandResult(d),
        cancelled: () => this.showActivity('Cancelled'),
        focused_files_updated: (d) => { if (this.isMySession(d)) this.loadFocusedFiles(); },
        title_updated: (d) => bus.emit('title-updated', d),
      };
      
      // Register all handlers
      for (const [event, handler] of Object.entries(this._socketHandlers)) {
        window.socket.on(event, handler);
      }
    }

    // Note: session-loaded and session-created are handled by app.js
    // which calls workspace.getActiveChat() to update only the active tab
  }

  cleanup() {
    document.removeEventListener('keydown', this._escHandler);
    
    // Remove socket event listeners to prevent duplicates
    if (window.socket && this._socketHandlers) {
      for (const [event, handler] of Object.entries(this._socketHandlers)) {
        window.socket.off(event, handler);
      }
      this._socketHandlers = null;
    }
  }

  handleSend() {
    const msg = this.inputEl.value.trim();
    if (!msg) return;

    if (this.isProcessing) {
      // Queue or interrupt
      if (!this.queuedMessage) {
        this.queuedMessage = msg;
        this.inputEl.value = '';
        this.showActivity(`Queued: "${msg.substring(0, 25)}..." (Enter to interrupt)`);
      } else {
        this.queuedMessage = msg;
        this.inputEl.value = '';
        window.socket?.emit('cancel');
        this.showActivity('Interrupting...');
      }
      return;
    }

    this.inputEl.value = '';
    this.autoResize();
    this.isProcessing = true;
    this.queuedMessage = null;
    this.updateSendButton();
    this.showActivity('Sending...');
    window.socket?.emit('send_message', { message: msg, session_id: this.currentSessionId });
  }

  updateSendButton() {
    if (this.isProcessing) {
      this.sendBtn.innerHTML = '<span class="stop-icon"></span>';
      this.sendBtn.className = 'btn btn-stop';
      this.sendBtn.onclick = () => { window.socket?.emit('cancel'); this.showActivity('Stopping...'); };
    } else {
      this.sendBtn.innerHTML = '<span class="send-icon"></span>';
      this.sendBtn.className = 'btn btn-primary';
      this.sendBtn.onclick = () => this.handleSend();
    }
  }

  autoResize() {
    this.inputEl.style.height = 'auto';
    this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 150) + 'px';
  }

  handleScroll() {
    // Ignore scroll events triggered by our own scrollTo()
    if (this.programmaticScroll) {
      this.lastScrollTop = this.messagesEl.scrollTop;
      return;
    }
    
    const currentScrollTop = this.messagesEl.scrollTop;
    
    // Check if user scrolled UP even a single pixel
    if (currentScrollTop < this.lastScrollTop) {
      this.autoScroll = false;
    }
    
    // Check if user scrolled back to the very bottom
    const distanceFromBottom = this.messagesEl.scrollHeight - currentScrollTop - this.messagesEl.clientHeight;
    if (distanceFromBottom < 10) {
      this.autoScroll = true;
    }
    
    this.lastScrollTop = currentScrollTop;
  }
  
  showActivity(text) {
    this.activityEl.classList.remove('hidden');
    this.activityText.textContent = text;
  }

  hideActivity() {
    this.activityEl.classList.add('hidden');
  }

  // Socket handlers
  onUserMessage(data) {
    this.addMessage('user', data.content);
    this.hideActivity();
  }

  onAgentStart() {
    this.streamingContent = '';
    this.currentMessage = null;
    this.currentStreamingTool = null;
    this.isProcessing = true;  // Ensure processing state is set
    this.updateSendButton();   // Update button to show stop
    this.showThinking();
  }

  onAgentDelta(data) {
    this.hideThinking();
    if (!this.currentMessage) {
      this.currentMessage = this.addMessage('assistant', '', true);
    }
    this.streamingContent = data.full_content;
    const content = this.currentMessage.querySelector('.message-content');
    content.innerHTML = this.renderMarkdown(this.streamingContent);
    content.classList.add('streaming');
    this.hideActivity();
    this.scrollDuringStream();  // Use instant scroll during streaming
  }

  onAgentDone(data) {
    this.hideThinking();
    if (this.currentMessage) {
      const content = this.currentMessage.querySelector('.message-content');
      content.innerHTML = this.renderMarkdown(data.content || this.streamingContent);
      content.classList.remove('streaming');
    }
    this.finishProcessing();
  }

  onAgentCancelled(data) {
    this.hideThinking();
    if (this.currentMessage && data.content) {
      const content = this.currentMessage.querySelector('.message-content');
      content.innerHTML = this.renderMarkdown(data.content + '\n\n*[Cancelled]*');
      content.classList.remove('streaming');
    }
    this.finishProcessing();
  }

  onAgentError(data) {
    this.hideThinking();
    this.addMessage('system', `Error: ${data.error}`);
    this.finishProcessing();
  }

  finishProcessing() {
    this.currentMessage = null;
    this.streamingContent = '';
    this.currentStreamingTool = null;
    this.isProcessing = false;
    this.hideActivity();
    this.updateSendButton();
    this.scrollDuringStream();

    // Process queued message
    if (this.queuedMessage) {
      const queued = this.queuedMessage;
      this.queuedMessage = null;
      setTimeout(() => {
        this.inputEl.value = queued;
        this.handleSend();
      }, 100);
    }
  }

  onToolProgress(data) {
    this.hideThinking();
    if (!this.currentStreamingTool) {
      // Finalize any pending text
      if (this.currentMessage && this.streamingContent) {
        const content = this.currentMessage.querySelector('.message-content');
        content.innerHTML = this.renderMarkdown(this.streamingContent);
        content.classList.remove('streaming');
        this.currentMessage = null;
      }
      this.currentStreamingTool = this.addStreamingTool(data.name);
    }
    this.hideActivity();
    this.scrollDuringStream();
  }

  onToolStart(data) {
    this.hideThinking();
    // Finalize text
    if (this.currentMessage && this.streamingContent) {
      const content = this.currentMessage.querySelector('.message-content');
      content.innerHTML = this.renderMarkdown(this.streamingContent);
      content.classList.remove('streaming');
      this.currentMessage = null;
    }

    const args = Object.entries(data.args || {}).map(([k, v]) => `${k}: ${this.truncate(String(v), 40)}`).join(', ');

    if (this.currentStreamingTool) {
      // Upgrade streaming to executing
      this.currentStreamingTool.classList.remove('tool-streaming');
      this.currentStreamingTool.classList.add('tool-executing');
      const argsEl = this.currentStreamingTool.querySelector('.tool-args');
      if (argsEl) argsEl.textContent = this.truncate(args, 50);
      this.currentStreamingTool = null;
    } else {
      this.addToolMessage(data.name, args);
    }
    this.showActivity(`Running ${data.name}...`);
  }

  onToolDone(data) {
    this.currentStreamingTool = null;
    
    // Mark all executing tools as done
    this.messagesEl.querySelectorAll('.message-tool.tool-executing, .message-tool.tool-streaming').forEach(t => {
      t.classList.remove('tool-executing', 'tool-streaming');
      t.classList.add('tool-done');
    });

    // Update last tool with result
    const tools = this.messagesEl.querySelectorAll('.message-tool');
    const lastTool = tools[tools.length - 1];
    if (lastTool) {
      if (data.name === 'bash') {
        this.renderBashResult(lastTool, data);
      } else if (data.name === 'edit_file' && data.old_content && data.new_content && this.showDiff) {
        this.renderDiff(lastTool, data);
      } else if (data.name === 'read_file') {
        const lines = (data.result || '').split('\n').length;
        const filePath = data.args?.file_path || '';
        
        lastTool.innerHTML = `
          <span class="tool-indicator"></span>
          <div class="tool-read-layout">
            <div class="tool-name">read_file</div>
            <div class="tool-read-meta">
              <span class="tool-read-path">${this.escapeHtml(filePath)}</span>
              <span class="tool-read-count">${lines} lines</span>
            </div>
          </div>
        `;
      } else if (data.name === 'create_file') {
        const resultEl = lastTool.querySelector('.tool-result');
        if (resultEl) resultEl.textContent = '✓ created';
      } else if (data.name === 'delete_file') {
        const resultEl = lastTool.querySelector('.tool-result');
        if (resultEl) resultEl.textContent = '✓ deleted';
      } else if (data.name === 'focus' || data.name === 'unfocus' || data.name === 'macro_focus') {
        const resultEl = lastTool.querySelector('.tool-result');
        if (resultEl) resultEl.style.display = 'none'; // Hide generic result string

        // Extract files from args (handle both singular and plural)
        let files = [];
        if (data.args?.file_paths) {
            const paths = data.args.file_paths;
            if (Array.isArray(paths)) files = paths;
            else if (typeof paths === 'string') {
                 try { files = JSON.parse(paths); } catch(e) { files = [paths]; }
            }
        } else if (data.args?.file_path) {
            files = [data.args.file_path];
        }

        const type = data.name.includes('unfocus') ? 'removed' : 'added';
        const fileCount = files.length > 1 ? ` <span style="opacity:0.6">(${files.length})</span>` : '';
        
        const icon = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px; display: inline-block; vertical-align: middle; color: var(--accent);">
                 <circle cx="12" cy="12" r="10"></circle>
                 <circle cx="12" cy="12" r="3"></circle>
                 <line x1="12" y1="2" x2="12" y2="4"></line>
                 <line x1="12" y1="20" x2="12" y2="22"></line>
                 <line x1="2" y1="12" x2="4" y2="12"></line>
                 <line x1="20" y1="12" x2="22" y2="12"></line>
                </svg>`;

        let listHtml = '';
        if (files.length > 0) {
            listHtml = `<div class="tool-file-list">` + 
                files.map(f => `<div class="tool-file-item">${icon} ${this.escapeHtml(f)}</div>`).join('') +
                `</div>`;
        }

        lastTool.innerHTML = `
          <span class="tool-indicator"></span>
          <div class="tool-read-layout">
            <div class="tool-name">${data.name}${fileCount}</div>
            ${listHtml}
            <div class="tool-read-meta">
              <span class="tool-read-count">${type}</span>
            </div>
          </div>
        `;
      } else {
        const resultEl = lastTool.querySelector('.tool-result');
        if (resultEl) resultEl.textContent = this.truncate(data.result || '', 60);
      }
    }
    
    this.showActivity('Thinking...');
    this.scrollToBottom();
  }

  renderBashResult(toolEl, data) {
    const result = data.result || '';
    const lines = result.split('\n');
    const command = data.args?.command || '';
    
    // Create mini terminal
    let html = `<div class="mini-terminal">
      <div class="terminal-cmd">$ ${this.escapeHtml(this.truncate(command, 60))}</div>
      <div class="terminal-output">`;
    
    // Show all lines (CSS handles scroll)
    for (const line of lines) {
      html += `<div class="terminal-line">${this.escapeHtml(line)}</div>`;
    }
    
    html += '</div></div>';
    
    // Replace the tool content
    toolEl.innerHTML = `
      <span class="tool-indicator"></span>
      <span class="tool-name">bash</span>
      ${html}
    `;
  }

  onCommandResult(data) {
    switch (data.type) {
      case 'new_session':
        this.messagesEl.innerHTML = '';
        this.addMessage('system', `New session: ${data.new_session}`);
        bus.emit('session-created', { sessionId: data.new_session });
        break;
      case 'load_session':
        this.messagesEl.innerHTML = '';
        this.loadHistory(data.history || []);
        this.addMessage('system', `Loaded ${data.message_count} messages`);
        break;
      case 'toggle_diff':
        this.showDiff = data.show_diff;
        this.addMessage('system', `Diff display ${data.show_diff ? 'enabled' : 'disabled'}`);
        break;
      case 'focus':
      case 'unfocus':
        this.addMessage('system', data.message);
        this.loadFocusedFiles();
        break;
      case 'error':
        this.addMessage('system', data.message);
        break;
    }
    this.isProcessing = false;
    this.hideActivity();
    this.updateSendButton();
  }

  // UI helpers
  addMessage(role, content, streaming = false) {
    const div = document.createElement('div');
    div.className = `message message-${role}`;
    const labels = { user: 'You', assistant: 'Prism', system: 'System' };
    div.innerHTML = `
      <div class="message-header">${labels[role] || role}</div>
      <div class="message-content ${streaming ? 'streaming' : ''}">${role === 'assistant' ? this.renderMarkdown(content) : this.escapeHtml(content)}</div>
    `;
    this.messagesEl.appendChild(div);
    if (!this._bulkLoading) this.scrollToBottom();
    return div;
  }

  addToolMessage(name, args) {
    const div = document.createElement('div');
    div.className = 'message-tool tool-executing';
    div.innerHTML = `
      <span class="tool-indicator"></span>
      <span class="tool-name">${name}</span>
      <span class="tool-args">${this.truncate(args || '', 50)}</span>
      <span class="tool-result"></span>
    `;
    this.messagesEl.appendChild(div);
    if (!this._bulkLoading) this.scrollToBottom();
    return div;
  }

  addStreamingTool(name) {
    const div = document.createElement('div');
    div.className = 'message-tool tool-streaming';
    div.innerHTML = `
      <span class="tool-indicator"></span>
      <span class="tool-name">${name}</span>
      <span class="tool-args"></span>
      <span class="tool-result"></span>
    `;
    this.messagesEl.appendChild(div);
    if (!this._bulkLoading) this.scrollToBottom();
    return div;
  }

  showThinking() {
    this.hideThinking();
    const div = document.createElement('div');
    div.className = 'thinking';
    div.id = 'thinking';
    div.innerHTML = '<div class="thinking-dots"><span class="thinking-dot"></span><span class="thinking-dot"></span><span class="thinking-dot"></span></div>';
    this.messagesEl.appendChild(div);
    this.scrollToBottom();
  }

  hideThinking() {
    this.$('#thinking')?.remove();
  }

  scrollToBottom(instant = false) {
    // Only auto-scroll if autoScroll is enabled (user hasn't scrolled up)
    if (this.autoScroll) {
      requestAnimationFrame(() => {
        if (instant) {
          // Jump instantly - used when loading history to avoid disorienting scroll animation
          this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
        } else {
          this.messagesEl.scrollTo({ top: this.messagesEl.scrollHeight, behavior: 'smooth' });
        }
      });
    }
  }
  
  // Scroll during streaming - instant, no animation fight
  scrollDuringStream() {
    if (!this.autoScroll) return;
    
    this.programmaticScroll = true;
    this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    setTimeout(() => { this.programmaticScroll = false; }, 30);
  }

  renderMarkdown(text) {
    return window.marked ? marked.parse(text || '') : this.escapeHtml(text || '');
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }

  truncate(str, len) {
    return (str || '').length > len ? str.substring(0, len) + '...' : str;
  }

  loadHistory(history) {
    this._bulkLoading = true;
    this.messagesEl.innerHTML = '';
    for (const msg of history) {
      if (msg.role === 'user') this.addMessage('user', msg.content);
      else if (msg.role === 'assistant' && msg.content) this.addMessage('assistant', msg.content);
      else if (msg.role === 'tool' && msg.tool_name) {
        const toolArgs = msg.tool_args || {};
        const args = Object.entries(toolArgs).map(([k, v]) => `${k}: ${this.truncate(String(v), 40)}`).join(', ');
        const t = this.addToolMessage(msg.tool_name, args);
        t.classList.remove('tool-executing');
        t.classList.add('tool-done');
        
        // Render rich content for specific tools
        if (msg.tool_name === 'bash' && toolArgs.command) {
          this.renderBashResult(t, {
            args: toolArgs,
            result: msg.content
          });
        } else if (msg.tool_name === 'read_file') {
          const lines = (msg.content || '').split('\n').length;
          const filePath = toolArgs.file_path || '';
          t.innerHTML = `
            <span class="tool-indicator"></span>
            <div class="tool-read-layout">
              <div class="tool-name">read_file</div>
              <div class="tool-read-meta">
                <span class="tool-read-path">${this.escapeHtml(filePath)}</span>
                <span class="tool-read-count">${lines} lines</span>
              </div>
            </div>
          `;
        } else if (msg.tool_name === 'edit_file') {          // For reloaded history, we get line counts instead of full content
          // Show a summary instead of full diff (full diff only available live)
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) {
            const oldLines = toolArgs.old_lines || 0;
            const newLines = toolArgs.new_lines || 0;
            const diff = newLines - oldLines;
            const diffStr = diff > 0 ? `+${diff}` : diff < 0 ? `${diff}` : '±0';
            resultEl.textContent = `${oldLines}→${newLines} lines (${diffStr})`;
          }
        } else if (msg.tool_name === 'read_file') {
          const lines = (msg.content || '').split('\n').length;
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) resultEl.textContent = `${lines} lines`;
        } else if (msg.tool_name === 'create_file') {
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) resultEl.textContent = '✓ created';
        } else if (msg.tool_name === 'delete_file') {
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) resultEl.textContent = '✓ deleted';
        } else if (msg.tool_name === 'focus' || msg.tool_name === 'unfocus') {
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) resultEl.textContent = '✓';
        } else {
          const resultEl = t.querySelector('.tool-result');
          if (resultEl) resultEl.textContent = this.truncate(msg.content || '', 60);
        }
      }
    }
    this._bulkLoading = false;
    // Use instant scroll when loading history - no animation, just be there
    this.scrollToBottom(true);
  }
  // Diff rendering
  renderDiff(toolEl, data) {
    const content = toolEl.querySelector('.tool-args');
    if (!content) return;
    
    // Detect language from file extension
    const ext = data.file_path.split('.').pop() || '';
    const langMap = { py: 'python', js: 'javascript', ts: 'typescript', jsx: 'javascript', tsx: 'typescript', css: 'css', html: 'html', json: 'json', md: 'markdown', yml: 'yaml', yaml: 'yaml', sh: 'bash', rs: 'rust', go: 'go', rb: 'ruby' };
    const lang = langMap[ext] || ext;
    
    const diff = this.computeDiff(data.old_content.split('\n'), data.new_content.split('\n'));
    const fileName = data.file_path.split('/').pop(); // Just the filename
    let html = `<div class="diff-viewer">
      <div class="diff-header">${this.escapeHtml(fileName)} <span class="diff-stats">+${diff.added} -${diff.removed}</span></div>
      <div class="diff-content">`;
    
    for (const line of diff.lines) {
      const cls = line.type === 'added' ? 'diff-line-added' : line.type === 'removed' ? 'diff-line-removed' : '';
      const num = line.type === 'added' ? '+' : line.type === 'removed' ? '-' : line.num;
      // Syntax highlight the line content
      let highlighted = this.escapeHtml(line.text);
      if (window.hljs && lang) {
        try {
          highlighted = hljs.highlight(line.text, { language: lang, ignoreIllegals: true }).value;
        } catch (e) {
          // Fallback to escaped text
        }
      }
      html += `<div class="diff-line ${cls}"><div class="diff-line-number">${num}</div><div class="diff-line-content">${highlighted}</div></div>`;
    }
    
    html += '</div></div>';
    content.innerHTML = `file_path: ${this.escapeHtml(data.file_path)}`;
    content.insertAdjacentHTML('afterend', html);
  }

  computeDiff(oldLines, newLines) {
    const lines = [];
    let added = 0, removed = 0, num = 1;
    let i = 0, j = 0;
    
    while (i < oldLines.length || j < newLines.length) {
      if (i < oldLines.length && j < newLines.length && oldLines[i] === newLines[j]) {
        lines.push({ type: 'context', text: oldLines[i], num: num++ });
        i++; j++;
      } else if (i < oldLines.length && (j >= newLines.length || !newLines.includes(oldLines[i]))) {
        lines.push({ type: 'removed', text: oldLines[i] });
        removed++;
        i++;
      } else {
        lines.push({ type: 'added', text: newLines[j] });
        added++;
        j++;
      }
    }
    return { lines, added, removed };
  }

  // Focus bar
  async loadFocusedFiles() {
    if (!this.currentSessionId) return;
    try {
      const res = await fetch(`/api/focused-files?session_id=${this.currentSessionId}`);
      const data = await res.json();
      this.focusedFiles = data.files || [];
      this.updateFocusBar();
    } catch (e) {
      this.focusedFiles = [];
    }
  }

  updateFocusBar() {
    if (!this.focusedFiles.length) {
      this.focusBar.classList.add('hidden');
      return;
    }
    this.focusBar.classList.remove('hidden');
    const total = this.focusedFiles.reduce((s, f) => s + (f.lines || 0), 0);
    const formatLines = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : n.toString();
    
    const magnifyingGlass = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px; opacity: 0.8;" title="Files the agent can see but aren't saved into the history">
        <circle cx="12" cy="12" r="9"></circle>
        <line x1="12" y1="1" x2="12" y2="5"></line>
        <line x1="12" y1="19" x2="12" y2="23"></line>
        <line x1="1" y1="12" x2="5" y2="12"></line>
        <line x1="19" y1="12" x2="23" y2="12"></line>
        <circle cx="12" cy="12" r="0.5" fill="currentColor"></circle>
      </svg>`;
    
    if (this.focusExpanded) {
      this.focusBar.innerHTML = `
        <span class="focus-icon" data-tooltip="Files the agent can see but aren't saved into the history">${magnifyingGlass}</span>
        <span class="focus-files">${this.focusedFiles.map((f, i) => 
          `<span class="focus-file"><span class="focus-file-name">${f.path}</span><span class="focus-file-lines">${formatLines(f.lines)} lines</span><button class="focus-remove" data-idx="${i}">×</button></span>`
        ).join('')}</span>
        <button class="focus-toggle">▼</button>
      `;
    } else {
      this.focusBar.innerHTML = `
        <span class="focus-icon" data-tooltip="Files the agent can see but aren't saved into the history">${magnifyingGlass}</span>
        <span class="focus-count">${this.focusedFiles.length} file${this.focusedFiles.length !== 1 ? 's' : ''}</span>
        <span class="focus-lines">${formatLines(total)} lines</span>
        <button class="focus-toggle">▶</button>
      `;
    }
    
    this.focusBar.querySelector('.focus-toggle')?.addEventListener('click', () => {
      this.focusExpanded = !this.focusExpanded;
      this.updateFocusBar();
    });
    
    this.focusBar.querySelectorAll('.focus-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const f = this.focusedFiles[+btn.dataset.idx];
        if (f) window.socket?.emit('send_message', { message: `/unfocus ${f.path}` });
      });
    });
  }

}

customElements.define('prism-chat', PrismChat);
