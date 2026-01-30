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

  // Custom provider state
  customModelInput: '',
  customNameInput: '',
  customKeyEnvInput: '',
  customApiKeyInput: '',
  addingCustom: false,
  
  async load(fetchModels = false) {
    try {
      console.log('[LLMPane] Loading providers...');
      const res = await fetch(`/api/llm/providers?fetch_models=${fetchModels ? '1' : '0'}`);
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
      alert('Failed to load LLM configuration: ' + err.message);
      this.providers = [];
    }  },
  
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

        <!-- Custom Providers Section -->
        <div class="pane-section">
          <div class="pane-section-title">Custom Providers</div>
          <p class="pane-hint">Add any LiteLLM-supported model (e.g. vertex_ai/gemini-pro, azure/gpt-4, deepseek/deepseek-chat)</p>

          <!-- Existing custom providers -->
          ${this.providers.filter(p => p.isCustom).length > 0 ? `
            <div class="llm-custom-list">
              ${this.providers.filter(p => p.isCustom).map(p => `
                <div class="llm-custom-item ${p.isActive ? 'active' : ''}">
                  <div class="llm-custom-info">
                    <div class="llm-custom-name">${this.escapeHtml(p.name)}</div>
                    <div class="llm-custom-model">${this.escapeHtml(p.modelString || '')}</div>
                  </div>
                  <div class="llm-custom-actions">
                    ${p.isActive ? `
                      <span class="llm-custom-active-badge">Active</span>
                    ` : `
                      <button class="btn btn-secondary btn-sm" data-action="activate-custom" data-id="${p.id}">Use</button>
                    `}
                    <button class="btn btn-icon btn-danger-text" data-action="remove-custom" data-id="${p.id}" title="Remove">×</button>
                  </div>
                </div>
              `).join('')}
            </div>
          ` : ''}

          <!-- Add new custom provider form -->
          <div class="llm-custom-add">
            <div class="pane-field">
              <label class="pane-label">Model String</label>
              <input type="text" class="pane-input" id="custom-model-input"
                     value="${this.escapeHtml(this.customModelInput)}"
                     placeholder="e.g. vertex_ai/gemini-pro, azure/gpt-4">
            </div>
            <div class="pane-field">
              <label class="pane-label">Display Name (optional)</label>
              <input type="text" class="pane-input" id="custom-name-input"
                     value="${this.escapeHtml(this.customNameInput)}"
                     placeholder="e.g. Vertex Gemini Pro">
            </div>
            <div class="pane-field">
              <label class="pane-label">API Key Env Var (optional)</label>
              <input type="text" class="pane-input" id="custom-keyenv-input"
                     value="${this.escapeHtml(this.customKeyEnvInput)}"
                     placeholder="e.g. VERTEX_API_KEY">
            </div>
            <div class="pane-field">
              <label class="pane-label">API Key (optional, stored encrypted)</label>
              <input type="password" class="pane-input" id="custom-apikey-input"
                     value="${this.escapeHtml(this.customApiKeyInput)}"
                     placeholder="Your API key">
            </div>
            <button class="btn btn-primary" id="add-custom-btn" ${this.addingCustom ? 'disabled' : ''}>
              ${this.addingCustom ? 'Adding...' : 'Add Custom Provider'}
            </button>
          </div>
        </div>
      </div>
    `;

    this.setupEvents(container);

    // Listen for server-side model list updates
    if (!this._modelsListenerAttached && window.socket) {
      this._modelsListenerAttached = true;
      window.socket.on('provider_models_updated', ({ provider_id, models }) => {
        const provider = this.providers.find(p => p.id === provider_id);
        if (provider && Array.isArray(models)) {
          provider.models = models;
          this.render(container);
        }
      });
    }
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

          // Refresh all providers with dynamic fetch when opening settings
          this.load(true);
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

    // Custom provider inputs
    container.querySelector('#custom-model-input')?.addEventListener('input', (e) => {
      this.customModelInput = e.target.value;
    });
    container.querySelector('#custom-name-input')?.addEventListener('input', (e) => {
      this.customNameInput = e.target.value;
    });
    container.querySelector('#custom-keyenv-input')?.addEventListener('input', (e) => {
      this.customKeyEnvInput = e.target.value;
    });
    container.querySelector('#custom-apikey-input')?.addEventListener('input', (e) => {
      this.customApiKeyInput = e.target.value;
    });

    // Add custom provider button
    container.querySelector('#add-custom-btn')?.addEventListener('click', () => this.addCustomProvider(container));

    // Activate custom provider
    container.querySelectorAll('[data-action="activate-custom"]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const providerId = btn.dataset.id;
        await this.activateCustomProvider(providerId, container);
      });
    });

    // Remove custom provider
    container.querySelectorAll('[data-action="remove-custom"]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const providerId = btn.dataset.id;
        await this.removeCustomProvider(providerId, container);
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
      console.error('[LLMPane] Validation error:', err);
    }
    
    this.render(container);
  },
  
  async saveAndActivate(container) {
    if (!this.expandedProvider) return;
    
    const provider = this.providers.find(p => p.id === this.expandedProvider);
    
    // If there's a new key that hasn't been validated yet, validate first
    if (this.keyInput && this.validationState !== 'valid') {
      // Auto-validate the key before saving
      this.saving = true;
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
        
        if (!data.valid) {
          this.validationState = 'invalid';
          this.validationError = data.error || 'Invalid API key';
          this.saving = false;
          this.render(container);
          return;
        }
        
        this.validationState = 'valid';
        this.validatedModels = data.models || [];
        // Re-render to show the model dropdown, then continue
        this.render(container);
      } catch (err) {
        this.validationState = 'invalid';
        this.validationError = 'Validation failed: ' + err.message;
        this.saving = false;
        this.render(container);
        return;
      }
    }
    
    // Now get the selected model (re-query after potential re-render)
    const modelSelect = container.querySelector('#model-select');
    // Use validated models if available, otherwise fall back to provider's static models
    const availableModels = this.validatedModels.length > 0 ? this.validatedModels : provider?.models || [];
    const selectedModel = modelSelect?.value || availableModels[0]?.id;
    
    // If no model available, we can still save the key but can't set active
    if (!selectedModel && !this.keyInput) {
      alert('No model available to set as active');
      this.saving = false;
      return;
    }
    
    this.saving = true;
    this.render(container);
    
    try {
      // If we have a new key to save (already validated at this point)
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
        
        // Show success toast (the provider_changed event will trigger other updates)
        // The event is handled in app.js to update all connected tabs
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  },
  
  async addCustomProvider(container) {
    if (!this.customModelInput.trim()) {
      alert('Model string is required (e.g. vertex_ai/gemini-pro)');
      return;
    }

    this.addingCustom = true;
    this.render(container);

    try {
      const res = await fetch('/api/llm/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_string: this.customModelInput.trim(),
          name: this.customNameInput.trim() || null,
          api_key_env: this.customKeyEnvInput.trim() || null,
          api_key: this.customApiKeyInput.trim() || null
        })
      });

      const data = await res.json();

      if (data.success) {
        // Clear form
        this.customModelInput = '';
        this.customNameInput = '';
        this.customKeyEnvInput = '';
        this.customApiKeyInput = '';
        // Reload providers
        await this.load();
      } else {
        alert('Error: ' + (data.error || 'Failed to add provider'));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }

    this.addingCustom = false;
    this.render(container);
  },

  async activateCustomProvider(providerId, container) {
    try {
      const res = await fetch(`/api/llm/custom/${providerId}/activate`, {
        method: 'POST'
      });

      const data = await res.json();

      if (data.success) {
        await this.load();
        this.render(container);
      } else {
        alert('Error: ' + (data.error || 'Failed to activate provider'));
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  },

  async removeCustomProvider(providerId, container) {
    if (!confirm('Remove this custom provider?')) return;

    try {
      const res = await fetch(`/api/llm/custom/${providerId}`, {
        method: 'DELETE'
      });

      const data = await res.json();

      if (data.success) {
        await this.load();
        this.render(container);
      } else {
        alert('Error: ' + (data.error || 'Failed to remove provider'));
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
