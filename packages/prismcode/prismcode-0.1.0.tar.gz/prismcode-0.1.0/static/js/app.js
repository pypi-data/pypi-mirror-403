// Prism Web App
class PrismApp {
    constructor() {
        this.socket = io();
        this.currentMessage = null;
        this.streamingContent = '';
        this.showDiff = window.appData.showDiff;
        this.isProcessing = false;
        this.queuedMessage = null;
        this.focusedFiles = [];
        this.focusBarExpanded = false;
        this.tokenCount = 0;
        this.currentStreamingTool = null;
        this.autoScroll = true;  // Auto-scroll state
        this.contextStats = null;  // Token usage stats
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeSocketEvents();
        this.initializeMarked();
        this.loadFocusedFiles();
        this.loadContextStats();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.messageForm = document.getElementById('message-form');
        this.sendBtn = document.getElementById('send-btn');
        this.sendText = document.getElementById('send-text');
        this.autocomplete = document.getElementById('autocomplete');
        this.autocompleteList = document.getElementById('autocomplete-list');
        
        // Activity indicators
        this.activityStatus = document.getElementById('activity-status');
        this.activityText = document.getElementById('activity-text');
        this.tokenCounter = document.getElementById('token-counter');
        
        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.mobileMenuBtn = document.getElementById('mobile-menu-btn');
        this.sessionsList = document.getElementById('sessions-list');
        
        // Header elements
        this.sessionTitle = document.querySelector('.header .session-title');
        this.sessionIdEl = document.querySelector('.header .session-id');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.diffToggleBtn = document.getElementById('diff-toggle-btn');
        this.helpBtn = document.getElementById('help-btn');
        this.diffStatus = document.getElementById('diff-status');
        
        // Modals
        this.helpModal = document.getElementById('help-modal');
        this.helpCommands = document.getElementById('help-commands');
    }

    initializeEventListeners() {
        // Message form
        this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Input handling
        this.messageInput.addEventListener('input', () => this.handleInput());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        this.messageInput.addEventListener('focus', () => this.hideAutocomplete());
        
        // Global escape key to cancel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isProcessing) {
                this.cancelRequest();
            }
        });
        
        // Sidebar toggle
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => this.toggleMobileSidebar());
        }
        
        // Sidebar buttons
        this.newSessionBtn.addEventListener('click', () => this.createNewSession());
        this.diffToggleBtn.addEventListener('click', () => this.toggleDiffMode());
        this.helpBtn.addEventListener('click', () => this.showHelpModal());
        
        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => this.closeModal(e));
        });
        
        // Modal background clicks
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal(e);
            });
        });
        
        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
        
        // Track user scroll to manage auto-scroll behavior
        this.chatMessages.addEventListener('scroll', () => this.handleScroll());
        
        // Load sessions on init
        this.loadSessions();
    }

    handleScroll() {
        // Calculate distance from bottom
        const distanceFromBottom = this.chatMessages.scrollHeight - this.chatMessages.scrollTop - this.chatMessages.clientHeight;
        
        // If user scrolled to bottom (within 50px), re-enable auto-scroll
        if (distanceFromBottom < 50) {
            this.autoScroll = true;
        } 
        // If user scrolled up significantly (more than 150px from bottom), disable auto-scroll
        else if (distanceFromBottom > 150) {
            this.autoScroll = false;
        }
    }

    initializeSocketEvents() {
        this.socket.on('user_message', (data) => this.handleUserMessage(data));
        this.socket.on('agent_start', () => this.handleAgentStart());
        this.socket.on('agent_delta', (data) => this.handleAgentDelta(data));
        this.socket.on('agent_done', (data) => this.handleAgentDone(data));
        this.socket.on('agent_error', (data) => this.handleAgentError(data));
        this.socket.on('agent_cancelled', (data) => this.handleAgentCancelled(data));
        this.socket.on('agent_complete', (data) => this.handleAgentComplete(data));
        this.socket.on('tool_progress', (data) => this.handleToolProgress(data));
        this.socket.on('tool_start', (data) => this.handleToolStart(data));
        this.socket.on('tool_done', (data) => this.handleToolDone(data));
        this.socket.on('command_result', (data) => this.handleCommandResult(data));
        this.socket.on('cancelled', () => this.handleCancelled());
        this.socket.on('message_queued', (data) => this.handleMessageQueued(data));
        this.socket.on('focused_files_updated', (data) => this.handleFocusedFilesUpdated(data));
        this.socket.on('title_updated', (data) => this.handleTitleUpdated(data));
        
        // Ensure activity is hidden on page load
        this.hideActivity();
        this.hideTokenCounter();
        
        // Restore sidebar state
        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            this.sidebar.classList.add('collapsed');
        }
        
        // Load current session history on page load
        this.loadCurrentSessionHistory();
    }
    
    loadCurrentSessionHistory() {
        fetch('/api/current-session')
            .then(res => res.json())
            .then(data => {
                // Update header
                if (this.sessionTitle && data.title) {
                    this.sessionTitle.textContent = data.title;
                }
                window.appData.sessionId = data.session_id;
                
                // Render history
                if (data.history && data.history.length > 0) {
                    this.renderHistory(data.history);
                }
            })
            .catch(err => console.error('Failed to load session history:', err));
    }
    
    renderHistory(history) {
        // Clear chat messages
        this.chatMessages.innerHTML = '';
        
        for (const msg of history) {
            if (msg.role === 'user') {
                this.addUserMessage(msg.content);
            } else if (msg.role === 'assistant' && msg.content) {
                this.addAssistantMessage(msg.content);
            } else if (msg.role === 'tool' && msg.tool_name) {
                // Show tool results in a collapsed state
                this.addToolResult(msg.tool_name, msg.content);
            }
        }
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    addUserMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `<div class="message-content">${this.escapeHtml(content)}</div>`;
        this.chatMessages.appendChild(messageDiv);
    }
    
    addAssistantMessage(content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant-message';
        messageDiv.innerHTML = `<div class="message-content">${this.renderMarkdown(content)}</div>`;
        this.chatMessages.appendChild(messageDiv);
    }
    
    addToolResult(toolName, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message tool-message collapsed';
        messageDiv.innerHTML = `
            <div class="tool-header" onclick="this.parentElement.classList.toggle('collapsed')">
                <span class="tool-name">🔧 ${this.escapeHtml(toolName)}</span>
                <span class="tool-toggle">▼</span>
            </div>
            <div class="tool-content"><pre>${this.escapeHtml(content || '')}</pre></div>
        `;
        this.chatMessages.appendChild(messageDiv);
    }

    initializeMarked() {
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });
    }

    // Input handling
    handleSubmit(e) {
        e.preventDefault();
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        if (this.isProcessing) {
            if (this.queuedMessage === null) {
                this.queuedMessage = message;
                this.messageInput.value = '';
                this.autoResizeTextarea();
                this.showActivity(`Queued: "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}" (Enter again to interrupt)`);
                return;
            } else {
                this.queuedMessage = message;
                this.messageInput.value = '';
                this.autoResizeTextarea();
                this.socket.emit('cancel');
                this.showActivity('Interrupting...');
                return;
            }
        }
        
        this.sendMessage(message);
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.hideAutocomplete();
    }

    handleInput() {
        const value = this.messageInput.value;
        if (value.startsWith('/')) {
            this.showAutocomplete(value);
        } else {
            this.hideAutocomplete();
        }
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            if (!this.isAutocompleteVisible()) {
                e.preventDefault();
                this.handleSubmit(e);
            }
        }
    }

    autoResizeTextarea() {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        const scrollHeight = Math.min(textarea.scrollHeight, 200);
        textarea.style.height = scrollHeight + 'px';
    }

    // Autocomplete
    showAutocomplete(input) {
        const commands = window.appData.commands;
        const matches = commands.filter(cmd => 
            cmd.command.toLowerCase().startsWith(input.toLowerCase())
        );

        if (matches.length > 0) {
            this.autocompleteList.innerHTML = matches.map(cmd => `
                <div class="autocomplete-item" data-command="${cmd.command}">
                    <div class="autocomplete-command">${cmd.command}</div>
                    <div class="autocomplete-description">${cmd.description}</div>
                </div>
            `).join('');

            this.autocompleteList.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('click', () => {
                    this.messageInput.value = item.dataset.command + ' ';
                    this.hideAutocomplete();
                    this.messageInput.focus();
                });
            });

            this.autocomplete.classList.remove('hidden');
        } else {
            this.hideAutocomplete();
        }
    }

    hideAutocomplete() {
        this.autocomplete.classList.add('hidden');
    }

    isAutocompleteVisible() {
        return !this.autocomplete.classList.contains('hidden');
    }

    // Message sending
    sendMessage(message) {
        this.isProcessing = true;
        this.queuedMessage = null;
        this.updateSendButton();
        this.showActivity('Sending message');
        this.socket.emit('send_message', { message: message });
    }

    updateSendButton() {
        if (this.isProcessing) {
            this.sendBtn.classList.add('btn-stop');
            this.sendText.textContent = 'Stop';
            this.sendBtn.disabled = false;
            this.sendBtn.onclick = (e) => { e.preventDefault(); this.cancelRequest(); };
        } else {
            this.sendBtn.classList.remove('btn-stop');
            this.sendText.textContent = 'Send';
            this.sendBtn.disabled = false;
            this.sendBtn.onclick = null;
        }
    }

    cancelRequest() {
        if (this.isProcessing) {
            this.socket.emit('cancel');
            this.showActivity('Stopping...');
        }
    }

    // Socket event handlers
    handleUserMessage(data) {
        this.addMessage('user', data.content);
        this.hideActivity();
    }

    handleAgentStart() {
        this.currentMessage = null;
        this.streamingContent = '';
        this.tokenCount = 0;
        this.currentStreamingTool = null;
        this.showThinkingIndicator();
        this.showTokenCounter();
    }

    showThinkingIndicator() {
        // Remove any existing thinking indicator
        this.hideThinkingIndicator();
        
        const thinking = document.createElement('div');
        thinking.className = 'thinking-indicator';
        thinking.id = 'thinking-indicator';
        thinking.innerHTML = `
            <div class="thinking-dots">
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
                <span class="thinking-dot"></span>
            </div>
            <span class="thinking-text">Thinking</span>
        `;
        this.chatMessages.appendChild(thinking);
        this.scrollToBottom();
    }

    hideThinkingIndicator() {
        const existing = document.getElementById('thinking-indicator');
        if (existing) existing.remove();
    }

    handleAgentDelta(data) {
        // Hide thinking indicator when text starts
        this.hideThinkingIndicator();
        
        if (!this.currentMessage) {
            this.currentMessage = this.addMessage('assistant', '', true);
        }
        
        this.streamingContent = data.full_content;
        this.tokenCount += data.content.split(/\s+/).filter(s => s).length;
        this.updateTokenCounter();
        this.hideActivity();
        
        const content = this.currentMessage.querySelector('.message-content');
        content.innerHTML = this.renderMarkdown(this.streamingContent);
        content.classList.add('streaming');
        this.scrollToBottom();
    }

    handleAgentDone(data) {
        // Hide thinking indicator if still visible
        this.hideThinkingIndicator();
        
        if (this.currentMessage) {
            const content = this.currentMessage.querySelector('.message-content');
            content.innerHTML = this.renderMarkdown(data.content || this.streamingContent);
            content.classList.remove('streaming');
        }
        this.currentMessage = null;
        this.streamingContent = '';
        this.currentStreamingTool = null;
        this.isProcessing = false;
        this.hideActivity();
        this.hideTokenCounter();
        this.updateSendButton();
        this.scrollToBottom();
        
        if (this.queuedMessage) {
            const queued = this.queuedMessage;
            this.queuedMessage = null;
            this.sendMessage(queued);
        }
    }

    handleAgentError(data) {
        this.addMessage('system', `Error: ${data.error}`, false, 'error');
        this.isProcessing = false;
        this.queuedMessage = null;
        this.hideActivity();
        this.hideTokenCounter();
        this.updateSendButton();
    }

    handleAgentCancelled(data) {
        // Hide thinking indicator
        this.hideThinkingIndicator();
        
        if (this.currentMessage && data.content) {
            const content = this.currentMessage.querySelector('.message-content');
            content.innerHTML = this.renderMarkdown(data.content + '\n\n*[Generation stopped]*');
            content.classList.remove('streaming');
        }
        this.currentMessage = null;
        this.streamingContent = '';
        this.currentStreamingTool = null;
        this.isProcessing = false;
        this.hideActivity();
        this.hideTokenCounter();
        this.updateSendButton();
        this.scrollToBottom();
        
        if (this.queuedMessage) {
            const queued = this.queuedMessage;
            this.queuedMessage = null;
            setTimeout(() => this.sendMessage(queued), 100);
        }
    }

    handleCancelled() {
        this.showActivity('Cancelled');
    }

    handleMessageQueued(data) {
        this.showActivity(`Queued: "${data.message.substring(0, 30)}..."`);
    }

    handleProcessingQueued(data) {
        this.showActivity(`Processing queued: "${data.message.substring(0, 30)}..."`);
    }

    handleFocusedFilesUpdated(data) {
        this.loadFocusedFiles();
        this.loadContextStats();  // Refresh token bar when focus changes
    }

    handleTitleUpdated(data) {
        // Update header title
        if (this.sessionTitle && data.session_id === window.appData.sessionId) {
            this.sessionTitle.textContent = data.title;
        }
        // Refresh sessions list to show new title
        this.loadSessions();
    }

    handleAgentComplete(data) {
        // Play notification sound and show browser notification if tab is not focused
        if (document.hidden) {
            this.playNotificationSound();
            this.showBrowserNotification('Prism', 'Agent has completed its response');
        }
    }

    playNotificationSound() {
        // Create notification sound using Web Audio API
        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const ctx = this.audioContext;
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            // Pleasant two-tone chime
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(880, ctx.currentTime);
            oscillator.frequency.setValueAtTime(1108.73, ctx.currentTime + 0.1);
            
            gainNode.gain.setValueAtTime(0.1, ctx.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
            
            oscillator.start(ctx.currentTime);
            oscillator.stop(ctx.currentTime + 0.3);
        } catch (e) {
            console.warn('Failed to play notification sound:', e);
        }
    }

    showBrowserNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body, icon: '/static/favicon.ico' });
        } else if ('Notification' in window && Notification.permission !== 'denied') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    new Notification(title, { body });
                }
            });
        }
    }

    handleToolProgress(data) {
        // Hide thinking indicator
        this.hideThinkingIndicator();
        
        const kb = (data.bytes_received / 1024).toFixed(1);
        
        // Create or update streaming tool element in chat
        if (!this.currentStreamingTool) {
            // Finalize any pending text first
            if (this.currentMessage && this.streamingContent) {
                const content = this.currentMessage.querySelector('.message-content');
                content.innerHTML = this.renderMarkdown(this.streamingContent);
                content.classList.remove('streaming');
                this.currentMessage = null;
            }
            
            this.currentStreamingTool = this.addStreamingToolMessage(data.name);
        }
        
        // Update bytes display
        const bytesEl = this.currentStreamingTool.querySelector('.tool-bytes');
        if (bytesEl) {
            bytesEl.textContent = `${kb}kb`;
        }
        
        this.scrollToBottom();
        this.hideActivity();
    }

    addStreamingToolMessage(name) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'message-tool tool-streaming';
        toolDiv.innerHTML = `
            <div class="tool-header"><span class="tool-indicator"></span>${name}</div>
            <div class="tool-content">
                <span class="tool-bytes">0kb</span>
            </div>
        `;
        this.chatMessages.appendChild(toolDiv);
        this.scrollToBottom();
        return toolDiv;
    }

    handleToolStart(data) {
        // Hide thinking indicator
        this.hideThinkingIndicator();
        
        if (this.currentMessage && this.streamingContent) {
            const content = this.currentMessage.querySelector('.message-content');
            content.innerHTML = this.renderMarkdown(this.streamingContent);
            content.classList.remove('streaming');
            this.currentMessage = null;
        }
        
        const args = Object.entries(data.args)
            .map(([key, value]) => `${key}: ${this.truncate(String(value), 50)}`)
            .join(', ');
        
        // If we have a streaming tool, upgrade it to executing
        if (this.currentStreamingTool) {
            this.currentStreamingTool.classList.remove('tool-streaming');
            this.currentStreamingTool.classList.add('tool-executing');
            // Update with args
            const argsEl = this.currentStreamingTool.querySelector('.tool-bytes');
            if (argsEl) {
                argsEl.className = 'tool-args';
                argsEl.textContent = this.truncate(args, 50);
            }
            // Add result placeholder
            const content = this.currentStreamingTool.querySelector('.tool-content');
            if (content && !content.querySelector('.tool-result')) {
                const resultSpan = document.createElement('span');
                resultSpan.className = 'tool-result';
                content.appendChild(resultSpan);
            }
            this.currentStreamingTool = null;
        } else {
            // Create new tool message
            const toolMessage = this.addToolMessage(data.name, args, null);
            toolMessage.classList.add('tool-executing');
        }
        
        this.showActivity(`Running ${data.name}`);
    }

    handleToolDone(data) {
        // Clear streaming tool reference
        this.currentStreamingTool = null;
        
        // Find all animated tools and mark them done
        const animatedTools = this.chatMessages.querySelectorAll('.message-tool.tool-executing, .message-tool.tool-streaming');
        animatedTools.forEach(tool => {
            tool.classList.remove('tool-executing', 'tool-streaming');
            tool.classList.add('tool-done');
        });
        
        // Update the last tool with result
        const toolMessages = this.chatMessages.querySelectorAll('.message-tool');
        const lastTool = toolMessages[toolMessages.length - 1];
        
        if (lastTool) {
            const resultDiv = lastTool.querySelector('.tool-result');
            
            if (data.name === 'edit_file' && data.old_content && data.new_content) {
                this.renderDiffTool(lastTool, data);
            } else if (data.name === 'read_file') {
                const lineCount = data.result.split('\n').length;
                if (resultDiv) resultDiv.textContent = `Read ${lineCount} lines`;
            } else {
                if (resultDiv) resultDiv.textContent = this.truncate(data.result, 100);
            }
        }
        
        // Show "Thinking..." while waiting for LLM to process tool result
        this.showActivity('Thinking...');
        this.scrollToBottom();
    }

    handleCommandResult(data) {
        switch (data.type) {
            case 'sessions':
                this.renderSessions(data.sessions, data.current);
                break;
            case 'new_session':
                this.updateSessionInfo(data.new_session);
                this.addMessage('system', `Started new session: ${data.new_session}\nPrevious session: ${data.old_session}`);
                break;
            case 'load_session':
                this.updateSessionInfo(data.new_session);
                this.clearMessages();
                this.renderHistory(data.history);
                this.addMessage('system', `Loaded session: ${data.new_session}\nLoaded ${data.message_count} messages`);
                break;
            case 'toggle_diff':
                this.showDiff = data.show_diff;
                this.diffStatus.textContent = data.show_diff ? 'Detailed' : 'Simple';
                this.addMessage('system', `Diff display ${data.show_diff ? 'enabled' : 'disabled'}`);
                break;
            case 'help':
                this.renderHelpModal(data);
                break;
            case 'unfocus':
            case 'focus':
                this.addMessage('system', data.message);
                break;
            case 'error':
                this.addMessage('system', data.message, false, 'error');
                break;
        }
        
        this.isProcessing = false;
        this.hideActivity();
        this.hideTokenCounter();
        this.updateSendButton();
    }

    // Activity indicators
    showActivity(text) {
        if (this.activityStatus) {
            this.activityStatus.classList.remove('hidden');
            if (this.activityText) {
                this.activityText.textContent = text;
            }
        }
    }

    hideActivity() {
        if (this.activityStatus) {
            this.activityStatus.classList.add('hidden');
        }
    }

    showTokenCounter() {
        if (this.tokenCounter) {
            this.tokenCounter.classList.remove('hidden');
        }
    }

    hideTokenCounter() {
        if (this.tokenCounter) {
            this.tokenCounter.classList.add('hidden');
        }
    }

    updateTokenCounter() {
        if (this.tokenCounter) {
            this.tokenCounter.textContent = this.tokenCount.toString();
        }
    }

    // Message rendering
    addMessage(role, content, streaming = false, variant = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;
        
        const roleNames = { 'user': 'You', 'assistant': 'Prism', 'system': 'System' };
        
        messageDiv.innerHTML = `
            <div class="message-header">${roleNames[role] || role}</div>
            <div class="message-content ${streaming ? 'streaming' : ''}">
                ${role === 'assistant' ? this.renderMarkdown(content) : content}
            </div>
        `;

        this.chatMessages.appendChild(messageDiv);
        if (!this._bulkLoading) this.scrollToBottom();
        return messageDiv;
    }

    addToolMessage(name, args, result) {
        const toolDiv = document.createElement('div');
        toolDiv.className = 'message-tool';
        
        toolDiv.innerHTML = `
            <div class="tool-header"><span class="tool-indicator"></span>${name}</div>
            <div class="tool-content">
                <span class="tool-args">${this.truncate(args, 50)}</span>
                <span class="tool-result">${result || ''}</span>
            </div>
        `;

        this.chatMessages.appendChild(toolDiv);
        if (!this._bulkLoading) this.scrollToBottom();
        return toolDiv;
    }

    renderDiffTool(toolElement, data) {
        const toolContent = toolElement.querySelector('.tool-content');
        
        if (this.showDiff) {
            const diff = this.generateMinimalDiff(data.old_content, data.new_content, data.language);
            toolContent.innerHTML = `
                <div class="tool-args">file_path: ${data.file_path}</div>
                <div class="diff-viewer">
                    <div class="diff-header">${data.file_path} • ${diff.stats.added} additions, ${diff.stats.removed} deletions</div>
                    <div class="diff-content">${diff.html}</div>
                </div>
            `;
        } else {
            const summary = data.old_lines === data.new_lines 
                ? `modified ${data.old_lines} line${data.old_lines !== 1 ? 's' : ''}`
                : `changed ${data.old_lines} → ${data.new_lines} lines`;
            toolContent.innerHTML = `
                <div class="tool-args">file_path: ${data.file_path}</div>
                <div class="diff-summary">${summary}</div>
            `;
        }
    }

    generateMinimalDiff(oldContent, newContent, language) {
        const oldLines = oldContent.split('\n');
        const newLines = newContent.split('\n');
        const changes = this.computeDiff(oldLines, newLines);
        
        let html = '';
        let stats = { added: 0, removed: 0 };
        
        const hunks = this.groupChangesIntoHunks(changes);
        
        hunks.forEach((hunk, hunkIndex) => {
            if (hunkIndex > 0) html += '<div class="diff-context-separator">⋯</div>';
            
            hunk.forEach(change => {
                if (change.type === 'removed') {
                    html += this.renderDiffLine('-', change.line, 'removed');
                    stats.removed++;
                } else if (change.type === 'added') {
                    html += this.renderDiffLine('+', change.line, 'added');
                    stats.added++;
                } else {
                    html += this.renderDiffLine(change.lineNum, change.line, 'unchanged');
                }
            });
        });
        
        return { html, stats };
    }

    computeDiff(oldLines, newLines) {
        const lcs = this.longestCommonSubsequence(oldLines, newLines);
        const result = [];
        
        let oldIndex = 0, newIndex = 0, lcsIndex = 0, lineNum = 1;
        
        while (oldIndex < oldLines.length || newIndex < newLines.length) {
            if (lcsIndex < lcs.length && oldIndex < oldLines.length && newIndex < newLines.length &&
                oldLines[oldIndex] === lcs[lcsIndex] && newLines[newIndex] === lcs[lcsIndex]) {
                result.push({ type: 'unchanged', line: oldLines[oldIndex], lineNum: lineNum++ });
                oldIndex++; newIndex++; lcsIndex++;
            } else if (oldIndex < oldLines.length && (lcsIndex >= lcs.length || oldLines[oldIndex] !== lcs[lcsIndex])) {
                result.push({ type: 'removed', line: oldLines[oldIndex] });
                oldIndex++;
            } else if (newIndex < newLines.length && (lcsIndex >= lcs.length || newLines[newIndex] !== lcs[lcsIndex])) {
                result.push({ type: 'added', line: newLines[newIndex] });
                newIndex++;
            }
        }
        
        return result;
    }

    longestCommonSubsequence(arr1, arr2) {
        const m = arr1.length, n = arr2.length;
        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));
        
        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                dp[i][j] = arr1[i-1] === arr2[j-1] ? dp[i-1][j-1] + 1 : Math.max(dp[i-1][j], dp[i][j-1]);
            }
        }
        
        const lcs = [];
        let i = m, j = n;
        while (i > 0 && j > 0) {
            if (arr1[i-1] === arr2[j-1]) { lcs.unshift(arr1[i-1]); i--; j--; }
            else if (dp[i-1][j] > dp[i][j-1]) i--;
            else j--;
        }
        
        return lcs;
    }

    groupChangesIntoHunks(changes) {
        const hunks = [], contextLines = 3;
        let currentHunk = [], lastChangeIndex = -1;
        
        for (let i = 0; i < changes.length; i++) {
            const change = changes[i];
            
            if (change.type !== 'unchanged') {
                if (currentHunk.length === 0) {
                    const contextStart = Math.max(0, i - contextLines);
                    for (let j = contextStart; j < i; j++) {
                        if (changes[j].type === 'unchanged') currentHunk.push(changes[j]);
                    }
                }
                currentHunk.push(change);
                lastChangeIndex = i;
            } else if (lastChangeIndex !== -1 && i - lastChangeIndex <= contextLines * 2) {
                currentHunk.push(change);
            } else if (lastChangeIndex !== -1 && i - lastChangeIndex > contextLines * 2) {
                const contextEnd = Math.min(changes.length, lastChangeIndex + contextLines + 1);
                for (let j = lastChangeIndex + 1; j < contextEnd; j++) {
                    if (changes[j].type === 'unchanged') currentHunk.push(changes[j]);
                }
                if (currentHunk.length > 0) hunks.push(currentHunk);
                currentHunk = [];
                lastChangeIndex = -1;
            }
        }
        
        if (currentHunk.length > 0) {
            const contextEnd = Math.min(changes.length, lastChangeIndex + contextLines + 1);
            for (let j = lastChangeIndex + 1; j < contextEnd; j++) {
                if (changes[j].type === 'unchanged') currentHunk.push(changes[j]);
            }
            hunks.push(currentHunk);
        }
        
        return hunks.length > 0 ? hunks : [changes];
    }

    renderDiffLine(lineNumber, content, type) {
        const escapedContent = this.escapeHtml(content);
        const lineNumberText = typeof lineNumber === 'number' ? lineNumber.toString() : lineNumber;
        return `<div class="diff-line diff-line-${type}">
            <div class="diff-line-number">${lineNumberText}</div>
            <div class="diff-line-content">${escapedContent}</div>
        </div>`;
    }

    renderMarkdown(text) {
        return marked.parse(text);
    }

    renderHistory(history) {
        this._bulkLoading = true;
        history.forEach(msg => {
            if (msg.role === 'user') this.addMessage('user', msg.content);
            else if (msg.role === 'assistant') this.addMessage('assistant', msg.content);
            else if (msg.role === 'tool') {
                const toolDiv = this.addToolMessage(msg.tool_name || 'tool', '', '');
                toolDiv.classList.add('tool-done');
            }
        });
        this._bulkLoading = false;
        // Scroll to bottom instantly after loading history
        this.scrollToBottom(true);
    }

    // Sidebar handling
    toggleSidebar() {
        this.sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebarCollapsed', this.sidebar.classList.contains('collapsed'));
    }

    toggleMobileSidebar() {
        this.sidebar.classList.toggle('open');
        let overlay = document.querySelector('.sidebar-overlay');
        if (this.sidebar.classList.contains('open')) {
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.className = 'sidebar-overlay';
                overlay.addEventListener('click', () => this.toggleMobileSidebar());
                document.body.appendChild(overlay);
            }
            overlay.classList.remove('hidden');
        } else if (overlay) {
            overlay.classList.add('hidden');
        }
    }

    // Modal handling
    showHelpModal() {
        this.helpModal.classList.remove('hidden');
        this.renderHelp();
    }

    closeModal(e) {
        const modal = e.target.closest('.modal');
        if (modal) modal.classList.add('hidden');
    }

    loadSessions() {
        this.sessionsList.innerHTML = '<div class="loading">Loading...</div>';
        fetch('/api/sessions')
            .then(res => res.json())
            .then(data => this.renderSessions(data.sessions, data.current))
            .catch(() => { this.sessionsList.innerHTML = '<div class="error">Failed to load</div>'; });
    }

    renderSessions(sessions, currentId) {
        if (sessions.length === 0) {
            this.sessionsList.innerHTML = '<div class="loading">No sessions</div>';
            return;
        }

        this.sessionsList.innerHTML = sessions.map(session => {
            const title = session.title || this.truncate(session.preview || 'New chat', 30);
            const dateStr = session.created_at ? this.formatDate(session.created_at) : '';
            return `
                <div class="session-item ${session.id === currentId ? 'current' : ''}" data-session-id="${session.id}">
                    <div class="session-title">${this.escapeHtml(title)}</div>
                    <div class="session-meta">
                        <span class="session-date">${dateStr}</span>
                        <span class="session-msgs">${session.message_count || 0} msgs</span>
                    </div>
                </div>
            `;
        }).join('');

        this.sessionsList.querySelectorAll('.session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.dataset.sessionId;
                if (sessionId !== currentId) this.loadSession(sessionId);
            });
        });
    }

    renderHelp() {
        this.helpCommands.innerHTML = window.appData.commands.map(cmd => `
            <div class="command-item">
                <div class="command-name">${cmd.command}</div>
                <div class="command-description">${cmd.description}</div>
            </div>
        `).join('');
    }

    renderHelpModal(data) {
        this.helpCommands.innerHTML = data.commands.map(cmd => `
            <div class="command-item">
                <div class="command-name">${cmd.command}</div>
                <div class="command-description">${cmd.description}</div>
            </div>
        `).join('');
        this.showHelpModal();
    }

    // Session management
    loadSession(sessionId) {
        fetch('/api/load-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                this.updateSessionInfo(data.session_id, data.title);
                this.clearMessages();
                this.renderHistory(data.history);
                this.addMessage('system', `Loaded session: ${data.title || data.session_id}\nLoaded ${data.message_count} messages`);
                this.loadSessions();
                if (this.sidebar.classList.contains('open')) this.toggleMobileSidebar();
            } else {
                alert(`Failed to load session: ${data.error}`);
            }
        })
        .catch(err => alert(`Error loading session: ${err.message}`));
    }

    createNewSession() {
        fetch('/api/new-session', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.updateSessionInfo(data.session_id);
                    this.clearMessages();
                    this.addMessage('system', `Started new session: ${data.session_id}`);
                    this.loadSessions();
                    if (this.sidebar.classList.contains('open')) this.toggleMobileSidebar();
                }
            })
            .catch(err => alert(`Error creating session: ${err.message}`));
    }

    toggleDiffMode() {
        fetch('/api/toggle-diff', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.showDiff = data.show_diff;
                    this.diffStatus.textContent = data.show_diff ? 'Detailed' : 'Simple';
                    this.addMessage('system', `Diff display ${data.show_diff ? 'enabled' : 'disabled'}`);
                }
            })
            .catch(err => alert(`Error toggling diff: ${err.message}`));
    }

    updateSessionInfo(sessionId, title = null) {
        if (this.sessionIdEl) {
            this.sessionIdEl.textContent = sessionId.substring(0, 8) + '...';
        }
        if (this.sessionTitle) {
            this.sessionTitle.textContent = title || 'New Chat';
        }
    }

    clearMessages() {
        this.chatMessages.innerHTML = '';
    }

    scrollToBottom(instant = false) {
        // Only auto-scroll if autoScroll is enabled (user hasn't scrolled up)
        if (this.autoScroll) {
            requestAnimationFrame(() => {
                if (instant) {
                    // Jump instantly - used when loading history to avoid disorienting scroll animation
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                } else {
                    this.chatMessages.scrollTo({ top: this.chatMessages.scrollHeight, behavior: 'smooth' });
                }
            });
        }
    }

    // Utility functions
    truncate(str, length) {
        return str.length > length ? str.substring(0, length) + '...' : str;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return date.toLocaleDateString([], { weekday: 'short' });
        } else {
            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
        }
    }

    // Focus bar methods
    loadFocusedFiles() {
        fetch('/api/focused-files')
            .then(res => res.json())
            .then(data => {
                this.focusedFiles = data.files;
                this.updateFocusBar();
            })
            .catch(err => console.error('Failed to load focused files:', err));
    }

    updateFocusBar() {
        const focusBar = document.getElementById('focus-bar');
        if (!focusBar) return;
        
        if (this.focusedFiles.length === 0) {
            focusBar.classList.add('hidden');
            return;
        }
        
        focusBar.classList.remove('hidden');
        
        const formatLines = (lines) => lines >= 1000 ? `${(lines/1000).toFixed(1)}k` : lines.toString();
        
        if (this.focusBarExpanded) {
            const filesHtml = this.focusedFiles.map((file, idx) => {
                const path = typeof file === 'object' ? file.path : file;
                const lines = typeof file === 'object' ? file.lines : 0;
                return `<span class="focus-file">
                    <span class="focus-file-name">${path}</span>
                    <span class="focus-file-lines">${formatLines(lines)} lines</span>
                    <button class="focus-remove" data-index="${idx}" title="Unfocus">×</button>
                </span>`;
            }).join('');
            focusBar.innerHTML = `
                <span class="focus-icon">●</span>
                <span class="focus-files">${filesHtml}</span>
                <button class="focus-toggle" title="Collapse">▼</button>
            `;
        } else {
            const totalLines = this.focusedFiles.reduce((sum, f) => sum + (typeof f === 'object' ? f.lines : 0), 0);
            focusBar.innerHTML = `
                <span class="focus-icon">●</span>
                <span class="focus-count">${this.focusedFiles.length} file${this.focusedFiles.length !== 1 ? 's' : ''}</span>
                <span class="focus-lines">${formatLines(totalLines)} lines</span>
                <button class="focus-toggle" title="Expand">▶</button>
            `;
        }
        
        const toggleBtn = focusBar.querySelector('.focus-toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.focusBarExpanded = !this.focusBarExpanded;
                this.updateFocusBar();
            });
        }
        
        focusBar.querySelectorAll('.focus-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const idx = parseInt(btn.dataset.index);
                const file = this.focusedFiles[idx];
                const path = typeof file === 'object' ? file.path : file;
                this.sendMessage(`/unfocus ${path}`);
            });
        });
    }

    // Token usage bar methods
    loadContextStats() {
        fetch('/api/context-stats')
            .then(res => res.json())
            .then(data => {
                this.contextStats = data;
                this.updateTokenBar();
            })
            .catch(err => console.error('Failed to load context stats:', err));
    }

    updateTokenBar() {
        const tokenBar = document.getElementById('token-bar');
        if (!tokenBar || !this.contextStats) return;

        const stats = this.contextStats;
        const budget = stats.budget;
        const total = stats.total;
        
        // Show bar if there's any content
        if (total > 0) {
            tokenBar.classList.remove('hidden');
        } else {
            tokenBar.classList.add('hidden');
            return;
        }

        // Update stats text
        const formatK = (n) => n >= 1000 ? `${(n/1000).toFixed(1)}k` : n.toString();
        document.getElementById('token-bar-stats').textContent = `${formatK(total)} / ${formatK(budget)}`;

        // Calculate percentages (relative to budget for display)
        const pct = (n) => Math.max(0, Math.min(100, (n / budget) * 100));
        
        // Update segment widths
        document.getElementById('token-seg-system').style.width = `${pct(stats.system)}%`;
        document.getElementById('token-seg-history').style.width = `${pct(stats.history)}%`;
        document.getElementById('token-seg-gists').style.width = `${pct(stats.gists)}%`;
        document.getElementById('token-seg-focus').style.width = `${pct(stats.focus)}%`;
        document.getElementById('token-seg-tree').style.width = `${pct(stats.tree)}%`;

        // Position threshold marker
        const thresholdPct = (stats.threshold / budget) * 100;
        document.getElementById('token-threshold').style.left = `${thresholdPct}%`;

        // Build legend
        const legendItems = [
            { cls: 'system', label: 'System', value: stats.system },
            { cls: 'history', label: 'History', value: stats.history },
        ];
        
        if (stats.gists > 0) {
            legendItems.push({ cls: 'gists', label: `Gists (${stats.gist_count})`, value: stats.gists });
        }
        
        legendItems.push({ cls: 'focus', label: `Focus (${stats.focus_count})`, value: stats.focus });
        legendItems.push({ cls: 'tree', label: 'Tree', value: stats.tree });
        legendItems.push({ cls: 'threshold', label: 'Threshold', value: stats.threshold });

        const legendHtml = legendItems.map(item => `
            <div class="token-bar-legend-item">
                <span class="token-bar-legend-dot ${item.cls}"></span>
                <span>${item.label}</span>
                <span class="token-bar-legend-value">${formatK(item.value)}</span>
            </div>
        `).join('');
        
        document.getElementById('token-bar-legend').innerHTML = legendHtml;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.prismApp = new PrismApp();
});
