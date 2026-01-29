/* LLM Pane - Manage LLM providers and API keys */

export const LLMPane = {
  id: 'llm',
  icon: '◎',
  label: 'Models',
  
  // State from API
  providers: [],
  activeProvider: null,
  activeModel: null,
  ollamaUrl: 'http://localhost:11434',
  
  // UI state
  expandedProvider: null,
  keyInput: '',
  keyVisible: false,
  validationState: 'idle', // 'idle' | 'validating' | 'valid' | 'invalid'
  validationError: null,
  validatedModels: [],
  saving: false,
  ollamaStatus: null, // null | 'testing' | 'connected' | 'error'
  ollamaModels: [],
  ollamaError: null,
  
  async load() {
    try {
      console.log('[LLMPane] Loading providers...');
      const res = await fetch('/api/llm/providers');
      const data = await res.json();
      console.log('[LLMPane] Got data:', data);
      
      this.providers = data.providers || [];
      this.activeProvider = data.active?.provider || null;
      this.activeModel = data.active?.model || null;
      this.ollamaUrl = data.ollama_url || 'http://localhost:11434';
      
      console.log('[LLMPane] Providers set:', this.providers.length, this.providers.map(p => p.id));
      
      // Reset UI state
      this.expandedProvider = null;
      this.validationState = 'idle';
      this.validationError = null;
      this.validatedModels = [];
      
    } catch (err) {
      console.error('[LLMPane] Failed to load LLM config:', err);
      this.providers = [];
    }
  },
  
  render(container) {
    const activeProviderInfo = this.providers.find(p => p.id === this.activeProvider);
    
    container.innerHTML = `
      <div class="llm-pane">
        <!-- Active Model Section -->
        <div class="pane-section">
          <div class="pane-section-title">Active Model</div>
          ${this.activeProvider ? `
            <div class="llm-active-model">
              <div class="llm-active-provider">
                <span class="llm-active-dot" style="background: var(--accent)"></span>
                <span class="llm-active-name">${activeProviderInfo?.name || this.activeProvider}</span>
              </div>
              <div class="llm-active-model-name">${this.activeModel || 'No model selected'}</div>
            </div>
          ` : `
            <div class="llm-no-active">
              <span class="llm-no-active-icon">○</span>
              <span>No model configured</span>
            </div>
          `}
        </div>
        
        <!-- API Keys Section -->
        <div class="pane-section">
          <div class="pane-section-title">API Keys</div>
          <div class="llm-providers-list">
            ${this.providers.filter(p => !p.isLocal).map(p => this.renderProvider(p)).join('')}
          </div>
        </div>
        
        <!-- Ollama Section -->
        <div class="pane-section">
          <div class="pane-section-title">Local Models (Ollama)</div>
          <div class="llm-ollama-section">
            <div class="pane-field">
              <label class="pane-label">Server URL</label>
              <div class="llm-ollama-url-row">
                <input type="text" class="pane-input" id="ollama-url" 
                       value="${this.escapeHtml(this.ollamaUrl)}" 
                       placeholder="http://localhost:11434">
                <button class="btn btn-secondary" id="test-ollama-btn">
                  ${this.ollamaStatus === 'testing' ? 'Testing...' : 'Test'}
                </button>
              </div>
            </div>
            ${this.ollamaStatus === 'connected' ? `
              <div class="llm-ollama-status llm-status-success">
                <span class="llm-status-icon">✓</span>
                <span>Connected - ${this.ollamaModels.length} model${this.ollamaModels.length !== 1 ? 's' : ''} available</span>
              </div>
              ${this.ollamaModels.length > 0 ? `
                <div class="llm-ollama-models">
                  <div class="pane-label">Available Models</div>
                  <div class="llm-model-chips">
                    ${this.ollamaModels.map(m => `
                      <button class="llm-model-chip ${this.activeProvider === 'ollama' && this.activeModel === m ? 'active' : ''}" 
                              data-provider="ollama" data-model="${m}">
                        ${m}
                      </button>
                    `).join('')}
                  </div>
                </div>
              ` : ''}
            ` : this.ollamaStatus === 'error' ? `
              <div class="llm-ollama-status llm-status-error">
                <span class="llm-status-icon">✗</span>
                <span>${this.escapeHtml(this.ollamaError || 'Connection failed')}</span>
              </div>
            ` : `
              <div class="llm-ollama-status llm-status-idle">
                <span class="llm-status-icon">○</span>
                <span>Click "Test" to check connection</span>
              </div>
            `}
          </div>
        </div>
      </div>
    `;
    
    this.setupEvents(container);
  },
  
  renderProvider(provider) {
    const isExpanded = this.expandedProvider === provider.id;
    const isActive = this.activeProvider === provider.id;
    
    return `
      <div class="llm-provider ${isExpanded ? 'expanded' : ''}" data-provider="${provider.id}">
        <div class="llm-provider-header">
          <span class="llm-provider-status ${provider.hasKey ? 'has-key' : 'no-key'}">
            ${provider.hasKey ? '✓' : '○'}
          </span>
          <div class="llm-provider-info">
            <div class="llm-provider-name">${provider.name}</div>
            <div class="llm-provider-subtitle">
              ${provider.hasKey 
                ? (isActive ? `Active: ${this.activeModel}` : 'Key configured') 
                : (provider.keyEnv ? `Set ${provider.keyEnv} or add key` : 'No API key')}
            </div>
          </div>
          <button class="btn btn-secondary llm-provider-btn" data-action="toggle" data-provider="${provider.id}">
            ${provider.hasKey ? 'Configure' : 'Add Key'}
          </button>
        </div>
        
        ${isExpanded ? this.renderProviderConfig(provider) : ''}
      </div>
    `;
  },
  
  renderProviderConfig(provider) {
    const hasModels = this.validatedModels.length > 0 || provider.models?.length > 0;
    const models = this.validatedModels.length > 0 ? this.validatedModels : provider.models || [];
    
    return `
      <div class="llm-provider-config">
        <div class="pane-field">
          <label class="pane-label">API Key</label>
          <div class="llm-key-input-row">
            <input type="${this.keyVisible ? 'text' : 'password'}" 
                   class="pane-input llm-key-input" 
                   id="api-key-input"
                   value="${this.escapeHtml(this.keyInput)}"
                   placeholder="${provider.hasKey ? '••••••••••••••••' : 'Enter your API key'}">
            <button class="btn btn-icon llm-toggle-visibility" title="${this.keyVisible ? 'Hide' : 'Show'}">
              ${this.keyVisible ? '🙈' : '👁'}
            </button>
          </div>
        </div>
        
        <!-- Validation Status -->
        ${this.validationState === 'validating' ? `
          <div class="llm-validation llm-validating">
            <span class="llm-validation-spinner"></span>
            <span>Validating key...</span>
          </div>
        ` : this.validationState === 'valid' ? `
          <div class="llm-validation llm-valid">
            <span class="llm-validation-icon">✓</span>
            <span>Valid - ${this.validatedModels.length} models available</span>
          </div>
        ` : this.validationState === 'invalid' ? `
          <div class="llm-validation llm-invalid">
            <span class="llm-validation-icon">✗</span>
            <span>${this.escapeHtml(this.validationError || 'Invalid key')}</span>
          </div>
        ` : ''}
        
        <!-- Model Selection (when key is valid or already has key) -->
        ${(provider.hasKey || this.validationState === 'valid') && hasModels ? `
          <div class="pane-field">
            <label class="pane-label">Model</label>
            <select class="pane-select llm-model-select" id="model-select">
              ${models.map(m => `
                <option value="${m.id}" ${m.id === this.activeModel && this.activeProvider === provider.id ? 'selected' : ''}>
                  ${m.name || m.id}
                </option>
              `).join('')}
            </select>
          </div>
        ` : ''}
        
        <!-- Actions -->
        <div class="llm-config-actions">
          <button class="btn btn-secondary" data-action="cancel">Cancel</button>
          
          ${!provider.hasKey || this.keyInput ? `
            <button class="btn btn-secondary" data-action="validate" 
                    ${!this.keyInput || this.validationState === 'validating' ? 'disabled' : ''}>
              ${this.validationState === 'validating' ? 'Validating...' : 'Validate'}
            </button>
          ` : ''}
          
          <button class="btn btn-primary" data-action="save"
                  ${this.saving ? 'disabled' : ''}>
            ${this.saving ? 'Saving...' : (this.validationState === 'valid' ? 'Save & Set Active' : 'Set Active')}
          </button>
        </div>
        
        ${provider.hasKey ? `
          <div class="llm-danger-zone">
            <button class="btn btn-danger-text" data-action="delete">Remove API Key</button>
          </div>
        ` : ''}
      </div>
    `;
  },
  
  setupEvents(container) {
    // Provider toggle/expand
    container.querySelectorAll('[data-action="toggle"]').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const providerId = btn.dataset.provider;
        if (this.expandedProvider === providerId) {
          this.expandedProvider = null;
        } else {
          this.expandedProvider = providerId;
          this.keyInput = '';
          this.keyVisible = false;
          this.validationState = 'idle';
          this.validationError = null;
          this.validatedModels = [];
          
          // Fetch fresh models for this provider when expanding
          const provider = this.providers.find(p => p.id === providerId);
          if (provider && provider.hasKey) {
            try {
              const res = await fetch(`/api/llm/models/${providerId}`);
              const data = await res.json();
              if (data.models) {
                // Update the provider's models with fresh data
                provider.models = data.models;
              }
            } catch (err) {
              console.warn(`Failed to fetch models for ${providerId}:`, err);
            }
          }
        }
        this.render(container);
      });
    });
    
    // Key input
    const keyInput = container.querySelector('#api-key-input');
    if (keyInput) {
      keyInput.addEventListener('input', (e) => {
        this.keyInput = e.target.value;
        // Reset validation when key changes
        if (this.validationState !== 'idle') {
          this.validationState = 'idle';
          this.validationError = null;
        }
      });
    }
    
    // Toggle visibility
    container.querySelector('.llm-toggle-visibility')?.addEventListener('click', () => {
      this.keyVisible = !this.keyVisible;
      this.render(container);
    });
    
    // Cancel
    container.querySelectorAll('[data-action="cancel"]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.expandedProvider = null;
        this.keyInput = '';
        this.validationState = 'idle';
        this.render(container);
      });
    });
    
    // Validate
    container.querySelectorAll('[data-action="validate"]').forEach(btn => {
      btn.addEventListener('click', () => this.validateKey(container));
    });
    
    // Save / Set Active
    container.querySelectorAll('[data-action="save"]').forEach(btn => {
      btn.addEventListener('click', () => this.saveAndActivate(container));
    });
    
    // Delete key
    container.querySelectorAll('[data-action="delete"]').forEach(btn => {
      btn.addEventListener('click', () => this.deleteKey(container));
    });
    
    // Model select change
    container.querySelector('#model-select')?.addEventListener('change', (e) => {
      // Just track the selection, will be saved on "Set Active"
    });
    
    // Ollama test
    container.querySelector('#test-ollama-btn')?.addEventListener('click', () => this.testOllama(container));
    
    // Ollama URL change
    container.querySelector('#ollama-url')?.addEventListener('change', (e) => {
      this.ollamaUrl = e.target.value;
      this.ollamaStatus = null; // Reset status when URL changes
    });
    
    // Ollama model chips
    container.querySelectorAll('.llm-model-chip').forEach(chip => {
      chip.addEventListener('click', async () => {
        const provider = chip.dataset.provider;
        const model = chip.dataset.model;
        await this.setActiveModel(provider, model, container);
      });
    });
  },
  
  async validateKey(container) {
    if (!this.keyInput || !this.expandedProvider) return;
    
    this.validationState = 'validating';
    this.render(container);
    
    try {
      const res = await fetch('/api/llm/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: this.expandedProvider,
          api_key: this.keyInput
        })
      });
      
      const data = await res.json();
      
      if (data.valid) {
        this.validationState = 'valid';
        this.validatedModels = data.models || [];
      } else {
        this.validationState = 'invalid';
        this.validationError = data.error || 'Invalid API key';
      }
    } catch (err) {
      this.validationState = 'invalid';
      this.validationError = 'Validation failed: ' + err.message;
    }
    
    this.render(container);
  },
  
  async saveAndActivate(container) {
    if (!this.expandedProvider) return;
    
    const provider = this.providers.find(p => p.id === this.expandedProvider);
    const modelSelect = container.querySelector('#model-select');
    const selectedModel = modelSelect?.value || provider?.models?.[0]?.id;
    
    this.saving = true;
    this.render(container);
    
    try {
      // If we have a new key to save
      if (this.keyInput && this.validationState === 'valid') {
        const res = await fetch('/api/llm/key', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider_id: this.expandedProvider,
            api_key: this.keyInput
          })
        });
        
        const data = await res.json();
        if (!data.success) {
          throw new Error(data.error || 'Failed to save key');
        }
      }
      
      // Set as active
      if (selectedModel) {
        const res = await fetch('/api/llm/active', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider_id: this.expandedProvider,
            model_id: selectedModel
          })
        });
        
        const data = await res.json();
        if (!data.success) {
          throw new Error(data.error || 'Failed to set active model');
        }
        
        this.activeProvider = this.expandedProvider;
        this.activeModel = selectedModel;
      }
      
      // Reload and close
      await this.load();
      this.expandedProvider = null;
      
    } catch (err) {
      alert('Error: ' + err.message);
    }
    
    this.saving = false;
    this.render(container);
  },
  
  async deleteKey(container) {
    if (!this.expandedProvider) return;
    
    if (!confirm('Remove API key for this provider?')) return;
    
    try {
      const res = await fetch(`/api/llm/key/${this.expandedProvider}`, {
        method: 'DELETE'
      });
      
      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to delete key');
      }
      
      // If this was the active provider, clear active
      if (this.activeProvider === this.expandedProvider) {
        this.activeProvider = null;
        this.activeModel = null;
      }
      
      // Reload
      await this.load();
      
    } catch (err) {
      alert('Error: ' + err.message);
    }
    
    this.render(container);
  },
  
  async testOllama(container) {
    this.ollamaStatus = 'testing';
    this.ollamaError = null;
    this.render(container);
    
    // Save URL first
    const urlInput = container.querySelector('#ollama-url');
    if (urlInput) {
      this.ollamaUrl = urlInput.value;
      await fetch('/api/llm/ollama/url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: this.ollamaUrl })
      });
    }
    
    try {
      const res = await fetch('/api/llm/ollama/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: this.ollamaUrl })
      });
      
      const data = await res.json();
      
      if (data.success) {
        this.ollamaStatus = 'connected';
        this.ollamaModels = data.models || [];
      } else {
        this.ollamaStatus = 'error';
        this.ollamaError = data.message || 'Connection failed';
      }
    } catch (err) {
      this.ollamaStatus = 'error';
      this.ollamaError = 'Test failed: ' + err.message;
    }
    
    this.render(container);
  },
  
  async setActiveModel(providerId, modelId, container) {
    try {
      const res = await fetch('/api/llm/active', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider_id: providerId,
          model_id: modelId
        })
      });
      
      const data = await res.json();
      if (data.success) {
        this.activeProvider = providerId;
        this.activeModel = modelId;
        this.render(container);
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  },
  
  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
  }
};
