/* Agent Pane - Configure agent behavior and tools */

export const AgentPane = {
  id: 'agent',
  icon: '⚙',
  label: 'Agent',  
  // State
  config: {
    systemPrompt: '',
    temperature: 0.7,
    maxTokens: 4096,
    enabledTools: [],
    autoTitle: true,
    streamResponses: true,
    showDiffs: true
  },
  availableTools: [],
  
  async load() {
    // TODO: Load from backend
    this.config = {
      systemPrompt: `You are a helpful coding assistant. You have access to tools for reading, writing, and editing files.

Be concise and helpful. When editing code, explain what you're changing and why.`,
      temperature: 0.7,
      maxTokens: 4096,
      enabledTools: ['read_file', 'create_file', 'edit_file', 'bash', 'ls', 'focus', 'unfocus'],
      autoTitle: true,
      streamResponses: true,
      showDiffs: true
    };
    
    this.availableTools = [
      { id: 'read_file', name: 'Read File', description: 'Read contents of a file' },
      { id: 'create_file', name: 'Create File', description: 'Create a new file' },
      { id: 'edit_file', name: 'Edit File', description: 'Edit existing file with fuzzy matching' },
      { id: 'delete_file', name: 'Delete File', description: 'Delete a file' },
      { id: 'rename_file', name: 'Rename File', description: 'Rename or move a file' },
      { id: 'bash', name: 'Bash', description: 'Execute shell commands' },
      { id: 'ls', name: 'List Directory', description: 'List files and directories' },
      { id: 'focus', name: 'Focus', description: 'Add file to HUD context' },
      { id: 'unfocus', name: 'Unfocus', description: 'Remove file from HUD' },
      { id: 'macro_focus', name: 'Macro Focus', description: 'Focus file with dependencies' },
      { id: 'find_entry_points', name: 'Find Entry Points', description: 'Discover main files' },
      { id: 'get_dependency_info', name: 'Dependency Info', description: 'Analyze file dependencies' }
    ];
  },
  
  render(container) {
    container.innerHTML = `
      <div class="pane-section">
        <div class="pane-section-title">System Prompt</div>
        <div class="pane-field">
          <textarea class="pane-textarea" id="system-prompt" rows="6">${this.escapeHtml(this.config.systemPrompt)}</textarea>
          <div class="pane-hint">Instructions given to the agent at the start of each conversation.</div>
        </div>
      </div>
      
      <div class="pane-section">
        <div class="pane-section-title">Generation Settings</div>
        <div class="pane-field">
          <label class="pane-label">Temperature: <span id="temp-value">${this.config.temperature}</span></label>
          <input type="range" class="pane-input" id="temperature" 
                 min="0" max="1" step="0.1" value="${this.config.temperature}"
                 style="padding: 0;">
          <div class="pane-hint">Higher = more creative, Lower = more focused</div>
        </div>
        <div class="pane-field">
          <label class="pane-label">Max Tokens</label>
          <select class="pane-select" id="max-tokens">
            <option value="2048" ${this.config.maxTokens === 2048 ? 'selected' : ''}>2,048</option>
            <option value="4096" ${this.config.maxTokens === 4096 ? 'selected' : ''}>4,096</option>
            <option value="8192" ${this.config.maxTokens === 8192 ? 'selected' : ''}>8,192</option>
            <option value="16384" ${this.config.maxTokens === 16384 ? 'selected' : ''}>16,384</option>
          </select>
        </div>
      </div>
      
      <div class="pane-section">
        <div class="pane-section-title">Behavior</div>
        <div class="pane-toggle">
          <span class="pane-toggle-label">Auto-generate session titles</span>
          <label class="toggle">
            <input type="checkbox" id="auto-title" ${this.config.autoTitle ? 'checked' : ''}>
            <span class="toggle-slider"></span>
          </label>
        </div>
        <div class="pane-toggle">
          <span class="pane-toggle-label">Stream responses</span>
          <label class="toggle">
            <input type="checkbox" id="stream-responses" ${this.config.streamResponses ? 'checked' : ''}>
            <span class="toggle-slider"></span>
          </label>
        </div>
        <div class="pane-toggle">
          <span class="pane-toggle-label">Show detailed diffs</span>
          <label class="toggle">
            <input type="checkbox" id="show-diffs" ${this.config.showDiffs ? 'checked' : ''}>
            <span class="toggle-slider"></span>
          </label>
        </div>
      </div>
      
      <div class="pane-section">
        <div class="pane-section-title">Enabled Tools</div>
        <div class="pane-list" id="tools-list">
          ${this.availableTools.map(tool => `
            <div class="pane-list-item" style="cursor: default;">
              <label class="toggle" style="margin-right: 10px;">
                <input type="checkbox" class="tool-checkbox" data-tool="${tool.id}"
                       ${this.config.enabledTools.includes(tool.id) ? 'checked' : ''}>
                <span class="toggle-slider"></span>
              </label>
              <div class="pane-list-item-content">
                <div class="pane-list-item-title">${tool.name}</div>
                <div class="pane-list-item-subtitle">${tool.description}</div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
      
      <div class="pane-actions">
        <button class="btn btn-secondary" id="reset-defaults-btn">Reset to Defaults</button>
        <button class="btn btn-primary" id="save-agent-btn">Save Changes</button>
      </div>
    `;
    
    this.setupEvents(container);
  },
  
  setupEvents(container) {
    // Temperature slider
    const tempSlider = container.querySelector('#temperature');
    const tempValue = container.querySelector('#temp-value');
    tempSlider.addEventListener('input', () => {
      tempValue.textContent = tempSlider.value;
      this.config.temperature = parseFloat(tempSlider.value);
    });
    
    // Max tokens
    container.querySelector('#max-tokens').addEventListener('change', (e) => {
      this.config.maxTokens = parseInt(e.target.value);
    });
    
    // Toggles
    container.querySelector('#auto-title').addEventListener('change', (e) => {
      this.config.autoTitle = e.target.checked;
    });
    container.querySelector('#stream-responses').addEventListener('change', (e) => {
      this.config.streamResponses = e.target.checked;
    });
    container.querySelector('#show-diffs').addEventListener('change', (e) => {
      this.config.showDiffs = e.target.checked;
    });
    
    // System prompt
    container.querySelector('#system-prompt').addEventListener('input', (e) => {
      this.config.systemPrompt = e.target.value;
    });
    
    // Tool checkboxes
    container.querySelectorAll('.tool-checkbox').forEach(cb => {
      cb.addEventListener('change', () => {
        const toolId = cb.dataset.tool;
        if (cb.checked) {
          if (!this.config.enabledTools.includes(toolId)) {
            this.config.enabledTools.push(toolId);
          }
        } else {
          this.config.enabledTools = this.config.enabledTools.filter(t => t !== toolId);
        }
      });
    });
    
    // Reset defaults
    container.querySelector('#reset-defaults-btn').addEventListener('click', () => {
      if (confirm('Reset all agent settings to defaults?')) {
        // TODO: Reset and re-render
        console.log('Reset to defaults');
        alert('Reset not yet connected to backend');
      }
    });
    
    // Save changes
    container.querySelector('#save-agent-btn').addEventListener('click', () => {
      // TODO: Save to backend
      console.log('Save agent config:', this.config);
      alert('Agent config save not yet connected to backend');
    });
  },
  
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }
};
