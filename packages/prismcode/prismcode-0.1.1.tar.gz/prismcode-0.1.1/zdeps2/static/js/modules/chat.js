// ============================================================================
// Chat - Claude chat integration
// ============================================================================

import { state } from './state.js';
import { generateSnapshotForChat } from './snapshot.js';

export function openChatModal() {
    if (!state.selectedFile) {
        alert('Please select a file first');
        return;
    }

    // Generate the snapshot content (same as copy)
    generateSnapshotForChat().then(content => {
        state.currentSnapshotContent = content;
        const badge = document.getElementById('chat-context-badge');
        if (content) {
            const lines = content.split('\n').length;
            const chars = content.length;
            badge.textContent = `${lines} lines | ${Math.round(chars/4)} tokens (approx)`;
            badge.classList.add('loaded');
        } else {
            badge.textContent = 'No context loaded';
            badge.classList.remove('loaded');
        }
    });

    document.getElementById('chat-modal').classList.add('visible');
    document.getElementById('chat-input').focus();
}

export function closeChatModal() {
    document.getElementById('chat-modal').classList.remove('visible');
}

export function handleChatKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

export async function sendChatMessage() {
    if (state.isChatStreaming) return;

    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    state.isChatStreaming = true;
    updateSendButton();

    // Add user message to UI
    addChatMessage('user', message);
    state.chatHistory.push({ role: 'user', content: message });

    // Create assistant message placeholder
    const assistantDiv = addChatMessage('assistant', '');
    const contentDiv = assistantDiv.querySelector('.chat-message-content');
    contentDiv.innerHTML = '<span style="color:#8b949e">Thinking...</span>';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                snapshot: state.currentSnapshotContent || '',
                history: state.chatHistory.slice(0, -1)
            })
        });

        if (!response.ok) {
            const errText = await response.text();
            contentDiv.innerHTML = `<span class="chat-error">Error ${response.status}: ${errText}</span>`;
            state.isChatStreaming = false;
            updateSendButton();
            return;
        }

        // Handle both streaming and non-streaming responses
        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('text/event-stream')) {
            // SSE streaming
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let fullResponse = '';
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6);
                        if (data === '[DONE]') continue;
                        if (data.startsWith('[ERROR]')) {
                            contentDiv.innerHTML = `<span class="chat-error">${data}</span>`;
                            continue;
                        }
                        fullResponse += data;
                        renderMarkdown(contentDiv, fullResponse);
                        scrollChatToBottom();
                    }
                }
            }

            if (fullResponse) {
                state.chatHistory.push({ role: 'assistant', content: fullResponse });
            } else {
                contentDiv.innerHTML = '<span class="chat-error">No response received</span>';
            }
        } else {
            // JSON response fallback
            const data = await response.json();
            if (data.error) {
                contentDiv.innerHTML = `<span class="chat-error">${data.error}</span>`;
            } else if (data.content) {
                renderMarkdown(contentDiv, data.content);
                state.chatHistory.push({ role: 'assistant', content: data.content });
            }
        }

    } catch (e) {
        contentDiv.innerHTML = `<span class="chat-error">Error: ${e.message}</span>`;
    }

    state.isChatStreaming = false;
    updateSendButton();
}

function addChatMessage(role, content) {
    const messagesDiv = document.getElementById('chat-messages');

    // Remove welcome message if present
    const welcome = messagesDiv.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-message chat-message-${role}`;

    const labelDiv = document.createElement('div');
    labelDiv.className = 'chat-message-label';
    labelDiv.textContent = role === 'user' ? 'You' : 'Claude';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'chat-message-content';

    if (role === 'user') {
        contentDiv.textContent = content;
    } else if (content) {
        renderMarkdown(contentDiv, content);
    }

    msgDiv.appendChild(labelDiv);
    msgDiv.appendChild(contentDiv);
    messagesDiv.appendChild(msgDiv);

    scrollChatToBottom();
    return msgDiv;
}

function renderMarkdown(element, content) {
    if (typeof marked === 'undefined') {
        element.textContent = content;
        return;
    }

    // Configure marked with highlight.js
    marked.setOptions({
        breaks: true,
        gfm: true,
        highlight: function(code, lang) {
            if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang }).value;
                } catch (e) {}
            }
            // For unknown languages or plain text, just escape HTML
            return code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        }
    });

    // Parse and sanitize
    let html = marked.parse(content);
    if (typeof DOMPurify !== 'undefined') {
        html = DOMPurify.sanitize(html);
    }

    element.innerHTML = html;

    // Apply highlight.js to any code blocks that weren't highlighted
    if (typeof hljs !== 'undefined') {
        element.querySelectorAll('pre code:not(.hljs)').forEach(block => {
            hljs.highlightElement(block);
        });
    }
}

function scrollChatToBottom() {
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function updateSendButton() {
    const btn = document.getElementById('chat-send-btn');
    btn.disabled = state.isChatStreaming;
    btn.textContent = state.isChatStreaming ? '...' : 'Send';
}

export function clearChatHistory() {
    state.chatHistory = [];
    const messagesDiv = document.getElementById('chat-messages');
    messagesDiv.innerHTML = `
        <div class="chat-welcome">
            <div class="chat-welcome-icon">🔍</div>
            <p>Load a file's dependencies and ask questions about the code.</p>
            <p class="chat-welcome-hint">The current snapshot will be used as context.</p>
        </div>
    `;
}

// Make functions available globally for onclick handlers
window.openChatModal = openChatModal;
window.closeChatModal = closeChatModal;
window.handleChatKeydown = handleChatKeydown;
window.sendChatMessage = sendChatMessage;
window.clearChatHistory = clearChatHistory;
