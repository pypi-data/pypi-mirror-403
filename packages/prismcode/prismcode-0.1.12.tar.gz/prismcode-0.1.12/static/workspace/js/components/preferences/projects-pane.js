/**
 * Projects Pane - Clean, Apple-inspired project management
 * 
 * Design principles:
 * - Generous whitespace, clear hierarchy
 * - Subtle shadows and borders, not harsh lines
 * - Smooth 200ms transitions on everything
 * - Large touch targets (44px minimum)
 * - Visual feedback on every interaction
 */

const COLORS = [
  { value: '#ff6b2b', name: 'Orange' },
  { value: '#3b82f6', name: 'Blue' },
  { value: '#10b981', name: 'Green' },
  { value: '#8b5cf6', name: 'Purple' },
  { value: '#f59e0b', name: 'Amber' },
  { value: '#ef4444', name: 'Red' },
  { value: '#ec4899', name: 'Pink' },
  { value: '#06b6d4', name: 'Cyan' }
];

export const ProjectsPane = {
  id: 'projects',
  icon: '◈',
  label: 'Projects',
  
  // State
  projects: [],
  sshHosts: [],
  currentProjectId: null,
  defaultProjectId: null,
  homeDir: '~',
  
  view: 'list',
  editingId: null,
  editName: '',
  editColor: '',
  
  // Add flow state
  addType: null, // 'local' | 'ssh'
  localPath: '',
  localFolders: [],
  newName: '',
  newColor: COLORS[0].value,
  
  // SSH fields
  sshHost: '',
  sshHostName: '', // display name from config
  sshUser: '',
  sshPort: 22,
  sshPath: '',
  sshConnected: false,
  sshFolders: [],
  sshSuggestions: [],
  sshBrowsing: false,
  showManualSSH: false,
  _sshDebounce: null,
  
  error: '',
  success: '',
  
  async load() {
    try {
      const [projectsRes, hostsRes] = await Promise.all([
        fetch('/api/projects'),
        fetch('/api/ssh/hosts').catch(() => ({ json: () => ({ hosts: [] }) }))
      ]);
      
      const pData = await projectsRes.json();
      const hData = await hostsRes.json();
      
      this.projects = pData.projects || [];
      this.currentProjectId = pData.current;
      this.defaultProjectId = pData.default;
      this.homeDir = pData.home_dir || '~';
      this.sshHosts = hData.hosts || [];
    } catch (e) {
      console.error('Failed to load projects:', e);
    }
  },
  
  render(container) {
    const html = this.view === 'list' ? this.renderList() : this.renderAddProject();
    container.innerHTML = `<div class="prefs-projects">${html}</div>`;
    this.bind(container);
  },
  
  renderList() {
    // Sort: favorites first, then by last accessed
    const sorted = [...this.projects].sort((a, b) => {
      if (a.favorite && !b.favorite) return -1;
      if (!a.favorite && b.favorite) return 1;
      const aTime = a.last_accessed ? new Date(a.last_accessed).getTime() : 0;
      const bTime = b.last_accessed ? new Date(b.last_accessed).getTime() : 0;
      return bTime - aTime;
    });
    
    return `
      ${this.renderMessages()}
      
      <div class="pp-section">
        <div class="pp-section-header">
          <h2 class="pp-section-title">Projects</h2>
          <span class="pp-section-count">${this.projects.length}</span>
        </div>
        
        <div class="pp-cards">
          ${sorted.length ? sorted.map(p => this.renderCard(p)).join('') : `
            <div class="pp-empty">
              <div class="pp-empty-icon">◈</div>
              <div class="pp-empty-title">No projects yet</div>
              <div class="pp-empty-text">Add a local folder or connect to a remote server</div>
            </div>
          `}
        </div>
      </div>
      
      <div class="pp-section">
        <div class="pp-section-header">
          <h2 class="pp-section-title">Add New</h2>
        </div>
        
        <div class="pp-add-buttons">
          <button class="pp-add-btn" data-add="local">
            <div class="pp-add-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
              </svg>
            </div>
            <div class="pp-add-label">Local Folder</div>
            <div class="pp-add-hint">Browse your filesystem</div>
          </button>
          
          <button class="pp-add-btn" data-add="ssh">
            <div class="pp-add-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="4" width="20" height="16" rx="2"/>
                <path d="M6 12h.01M10 12h.01M14 12h.01"/>
              </svg>
            </div>
            <div class="pp-add-label">Remote Server</div>
            <div class="pp-add-hint">Connect via SSH</div>
          </button>
        </div>
      </div>
    `;
  },
  
  renderCard(p) {
    const isEditing = this.editingId === p.id;
    const isCurrent = p.id === this.currentProjectId;
    const isDefault = p.id === this.defaultProjectId;
    const favCount = this.projects.filter(x => x.favorite).length;
    const canFavorite = p.favorite || favCount < 5;
    
    if (isEditing) {
      return `
        <div class="pp-card editing">
          <div class="pp-card-color-bar" style="background: ${this.editColor}"></div>
          
          <div class="pp-card-body">
            <input 
              type="text" 
              class="pp-edit-input"
              value="${this.esc(this.editName)}"
              data-field="editName"
              placeholder="Project name"
              spellcheck="false"
            >
            
            <div class="pp-card-path">${this.formatPath(p)}</div>
            
            <div class="pp-color-picker">
              ${COLORS.map(c => `
                <button 
                  class="pp-color-dot ${c.value === this.editColor ? 'selected' : ''}"
                  data-color="${c.value}"
                  title="${c.name}"
                  style="--dot-color: ${c.value}"
                ></button>
              `).join('')}
            </div>
          </div>
          
          <div class="pp-card-actions editing">
            <button class="pp-btn pp-btn-secondary" data-action="cancelEdit">Cancel</button>
            <button class="pp-btn pp-btn-primary" data-action="saveEdit">Save</button>
          </div>
        </div>
      `;
    }
    
    return `
      <div class="pp-card ${isCurrent ? 'active' : ''}" data-id="${p.id}">
        <div class="pp-card-color-bar" style="background: ${p.color || COLORS[0].value}"></div>
        
        <button 
          class="pp-favorite ${p.favorite ? 'is-favorite' : ''}"
          data-action="toggleFavorite"
          data-id="${p.id}"
          title="${p.favorite ? 'Remove from favorites' : canFavorite ? 'Add to favorites' : 'Max 5 favorites'}"
          ${!canFavorite && !p.favorite ? 'disabled' : ''}
        >
          ${p.favorite ? '★' : '☆'}
        </button>
        
        <div class="pp-card-body" data-action="switch" data-id="${p.id}">
          <div class="pp-card-name">${this.esc(p.name)}</div>
          <div class="pp-card-path">${this.formatPath(p)}</div>
          <div class="pp-card-meta">${this.formatTime(p.last_accessed)}</div>
        </div>
        
        <div class="pp-card-actions">
          ${!isDefault ? `
            <button class="pp-icon-btn" data-action="setDefault" data-id="${p.id}" title="Set as Default">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </button>
          ` : ''}
          <button class="pp-icon-btn" data-action="edit" data-id="${p.id}" title="Edit">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="pp-icon-btn danger" data-action="delete" data-id="${p.id}" title="Delete">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
          </button>
        </div>
        
        ${isCurrent ? '<div class="pp-card-badge">Current</div>' : ''}
        ${isDefault ? '<div class="pp-card-badge default">Default</div>' : ''}
      </div>
    `;
  },
  
  renderAddProject() {
    return `
      <button class="pp-back" data-action="back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Back to Projects
      </button>
      
      ${this.renderMessages()}
      
      <div class="pp-section">
        <div class="pp-section-header">
          <h2 class="pp-section-title">${this.addType === 'ssh' ? 'Add Remote Server' : 'Add Local Folder'}</h2>
        </div>
        
        ${this.addType === 'local' ? this.renderLocalForm() : this.renderSSHForm()}
      </div>
    `;
  },
  
  renderLocalForm() {
    // Reuse the folder browser component
    return this.renderFolderBrowser('local');
  },
  
  renderSSHForm() {
    // If connected, show folder browser
    if (this.sshConnected) {
      return this.renderFolderBrowser('ssh');
    }
    
    // If showing manual entry form
    if (this.showManualSSH) {
      return `
        <div class="pp-form">
          <button class="pp-back-link" data-action="hideManualSSH">← Back to hosts</button>
          
          <div class="pp-field">
            <label class="pp-label">Host</label>
            <input type="text" class="pp-input" data-field="sshHost" 
                   value="${this.esc(this.sshHost || '')}" placeholder="hostname or IP">
          </div>
          
          <div class="pp-field-row">
            <div class="pp-field pp-field-grow">
              <label class="pp-label">Username</label>
              <input type="text" class="pp-input" data-field="sshUser"
                     value="${this.esc(this.sshUser || '')}" placeholder="username">
            </div>
            <div class="pp-field" style="width: 100px;">
              <label class="pp-label">Port</label>
              <input type="number" class="pp-input" data-field="sshPort"
                     value="${this.sshPort || 22}" placeholder="22">
            </div>
          </div>
          
          <div class="pp-form-actions">
            <button class="pp-btn pp-btn-primary ${this.sshBrowsing ? 'loading' : ''}" data-action="connectSSH">
              ${this.sshBrowsing ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </div>
      `;
    }
    
    // Show SSH hosts list (like network drives)
    return `
      <div class="pp-form">
        ${this.sshHosts.length ? `
          <div class="pp-hosts-grid">
            ${this.sshHosts.map(h => `
              <button class="pp-host-card ${this.sshBrowsing ? 'disabled' : ''}" 
                      data-quickconnect="${this.esc(h.name)}"
                      data-hostname="${this.esc(h.hostname || h.name)}"
                      data-user="${this.esc(h.user || '')}" 
                      data-port="${h.port || 22}">
                <div class="pp-host-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="2" y="4" width="20" height="16" rx="2"/>
                    <path d="M6 12h.01M10 12h.01M14 12h.01"/>
                  </svg>
                </div>
                <div class="pp-host-name">${this.esc(h.name)}</div>
                <div class="pp-host-details">${this.esc(h.user || 'user')}@${this.esc(h.hostname || h.name)}</div>
              </button>
            `).join('')}
          </div>
        ` : `
          <div class="pp-empty-hosts">
            <p>No SSH hosts found in ~/.ssh/config</p>
          </div>
        `}
        
        <button class="pp-add-manual" data-action="showManualSSH">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          Add new connection...
        </button>
        
        ${this.sshBrowsing ? `<div class="pp-connecting">Connecting...</div>` : ''}
      </div>
    `;
  },
  
  renderFolderBrowser(type) {
    const isSSH = type === 'ssh';
    const path = isSSH ? this.sshPath : this.localPath;
    const folders = isSSH ? this.sshFolders : this.localFolders;
    const suggestions = isSSH ? this.sshSuggestions : [];
    const isLoading = this.sshBrowsing;
    
    return `
      <div class="pp-form">
        ${isSSH ? `
          <div class="pp-browser-header-bar">
            <button class="pp-back-link" data-action="disconnectSSH">← ${this.esc(this.sshHostName || this.sshHost)}</button>
            <span class="pp-connection-info">${this.esc(this.sshUser)}@${this.esc(this.sshHost)}:${this.sshPort}</span>
          </div>
        ` : ''}
        
        <div class="pp-path-bar">
          <button class="pp-path-nav" data-action="${isSSH ? 'sshNavUp' : 'localNavUp'}" title="Go up">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 15l-6-6-6 6"/>
            </svg>
          </button>
          <button class="pp-path-nav" data-action="${isSSH ? 'sshNavHome' : 'localNavHome'}" title="Home">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
            </svg>
          </button>
          <div class="pp-path-autocomplete pp-path-autocomplete-bar">
            <input type="text" class="pp-path-input" 
                   data-field="${isSSH ? 'sshPath' : 'localPath'}"
                   data-autocomplete="${type}"
                   value="${this.esc(path || '')}" 
                   placeholder="Enter path...">
            ${suggestions.length ? `
              <div class="pp-suggestions">
                ${suggestions.map(s => `
                  <button class="pp-suggestion" data-suggestion="${this.esc(s.path)}" data-type="${type}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M10 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V8a2 2 0 00-2-2h-8l-2-2z"/>
                    </svg>
                    <span>${this.esc(s.name)}</span>
                  </button>
                `).join('')}
              </div>
            ` : ''}
          </div>
        </div>
        
        <div class="pp-folder-list ${isLoading ? 'loading' : ''}">
          ${folders.length ? folders.map(f => `
            <button class="pp-folder-item" data-${isSSH ? 'sshpath' : 'path'}="${this.esc(f.path)}">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M10 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V8a2 2 0 00-2-2h-8l-2-2z"/>
              </svg>
              <span>${this.esc(f.name)}</span>
            </button>
          `).join('') : `
            <div class="pp-folder-empty">
              ${isLoading ? 'Loading...' : 'No subfolders'}
            </div>
          `}
        </div>
        
        <div class="pp-add-project-bar">
          <div class="pp-field-row">
            <div class="pp-field pp-field-grow">
              <input type="text" class="pp-input" data-field="newName"
                     value="${this.esc(this.newName || '')}" placeholder="Project name">
            </div>
            <div class="pp-color-picker-inline">
              ${COLORS.map(c => `
                <button class="pp-color-dot ${c.value === this.newColor ? 'selected' : ''}"
                        data-newcolor="${c.value}" title="${c.name}"
                        style="--dot-color: ${c.value}"></button>
              `).join('')}
            </div>
            <button class="pp-btn pp-btn-primary" data-action="${isSSH ? 'createSSH' : 'createLocal'}">
              Add Project
            </button>
          </div>
        </div>
      </div>
    `;
  },
  
  renderMessages() {
    if (!this.error && !this.success) return '';
    
    return `
      <div class="pp-message ${this.error ? 'error' : 'success'}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          ${this.error 
            ? '<circle cx="12" cy="12" r="10"/><path d="M15 9l-6 6M9 9l6 6"/>'
            : '<path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/>'
          }
        </svg>
        <span>${this.esc(this.error || this.success)}</span>
      </div>
    `;
  },
  
  formatPath(p) {
    if (p.type === 'ssh') {
      return `<span class="pp-ssh-badge">SSH</span>${this.esc(p.host)}:${this.esc(p.path)}`;
    }
    return this.esc(p.path);
  },
  
  formatTime(ts) {
    if (!ts) return 'Never opened';
    const d = new Date(ts);
    const now = new Date();
    const diff = now - d;
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString();
  },
  
  esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
  },
  
  // Event binding
  bind(container) {
    // Generic field inputs
    container.querySelectorAll('[data-field]').forEach(el => {
      el.addEventListener('input', e => {
        this[e.target.dataset.field] = e.target.value;
      });
      el.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
          if (this.editingId) this.saveEdit(container);
          else if (this.view === 'add') this.createLocal(container);
        }
      });
    });
    
    // Color pickers (edit mode)
    container.querySelectorAll('[data-color]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.editColor = btn.dataset.color;
        this.render(container);
      });
    });
    
    // Color pickers (add mode)
    container.querySelectorAll('[data-newcolor]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.newColor = btn.dataset.newcolor;
        this.render(container);
      });
    });
    
    // Action buttons
    container.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const action = btn.dataset.action;
        const id = btn.dataset.id;
        
        switch(action) {
          case 'switch': this.switchProject(id, container); break;
          case 'edit': this.startEdit(id, container); break;
          case 'delete': this.deleteProject(id, container); break;
          case 'toggleFavorite': this.toggleFavorite(id, container); break;
          case 'setDefault': this.setDefault(id, container); break;
          case 'saveEdit': this.saveEdit(container); break;
          case 'cancelEdit': this.cancelEdit(container); break;
          case 'back': this.goBack(container); break;
          case 'createLocal': this.createLocal(container); break;
          case 'createSSH': this.createSSH(container); break;
          case 'testSSH': this.testSSH(container); break;
          case 'connectSSH': this.connectSSH(container); break;
          case 'disconnectSSH': this.disconnectSSH(container); break;
          case 'sshNavUp': this.sshNavigateUp(container); break;
          case 'sshNavHome': this.sshNavigateHome(container); break;
          case 'showManualSSH': this.showManualSSH = true; this.render(container); break;
          case 'hideManualSSH': this.showManualSSH = false; this.render(container); break;
          case 'localNavUp': this.localNavigateUp(container); break;
          case 'localNavHome': this.localNavigateHome(container); break;
        }
      });
    });
    
    // Add buttons
    container.querySelectorAll('[data-add]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.addType = btn.dataset.add;
        this.view = 'add';
        this.localPath = this.homeDir;
        this.newName = '';
        this.newColor = COLORS[0].value;
        this.loadFolders(container);
      });
    });
    
    // Browser navigation
    container.querySelectorAll('[data-nav]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.nav === 'up') {
          const parts = this.localPath.split('/').filter(Boolean);
          parts.pop();
          this.localPath = '/' + parts.join('/') || '/';
        } else {
          this.localPath = this.homeDir;
        }
        this.loadFolders(container);
      });
    });
    
    // Browser items
    container.querySelectorAll('[data-path]').forEach(item => {
      item.addEventListener('click', () => {
        this.localPath = item.dataset.path;
        this.loadFolders(container);
      });
    });
    
    // SSH host quick-connect (one-click to connect and browse)
    container.querySelectorAll('[data-quickconnect]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (this.sshBrowsing) return; // Prevent double-click
        this.sshHostName = btn.dataset.quickconnect;
        this.sshHost = btn.dataset.hostname || btn.dataset.quickconnect;
        this.sshUser = btn.dataset.user || '';
        this.sshPort = parseInt(btn.dataset.port) || 22;
        this.newName = btn.dataset.quickconnect; // Use config name as default project name
        this.connectSSH(container); // Immediately connect
      });
    });
    
    // SSH folder browser items
    container.querySelectorAll('[data-sshpath]').forEach(item => {
      item.addEventListener('click', () => {
        this.sshPath = item.dataset.sshpath;
        this.loadSSHFolders(container);
      });
    });
    
    // SSH path autocomplete
    const sshPathInput = container.querySelector('[data-autocomplete="ssh"]');
    if (sshPathInput) {
      sshPathInput.addEventListener('input', (e) => {
        this.sshPath = e.target.value;
        // Debounce the autocomplete fetch
        clearTimeout(this._sshDebounce);
        this._sshDebounce = setTimeout(() => {
          this.fetchSSHSuggestions(container);
        }, 300);
      });
      
      sshPathInput.addEventListener('keydown', (e) => {
        if (e.key === 'Tab' && this.sshSuggestions.length) {
          e.preventDefault();
          // Auto-complete with first suggestion
          this.sshPath = this.sshSuggestions[0].path;
          this.sshSuggestions = [];
          this.loadSSHFolders(container);
        } else if (e.key === 'Escape') {
          this.sshSuggestions = [];
          this.render(container);
        } else if (e.key === 'Enter') {
          this.sshSuggestions = [];
          this.loadSSHFolders(container);
        }
      });
    }
    
    // Suggestion clicks
    container.querySelectorAll('[data-suggestion]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.sshPath = btn.dataset.suggestion;
        this.sshSuggestions = [];
        this.loadSSHFolders(container);
      });
    });
    
    // Focus edit input if exists
    const editInput = container.querySelector('.pp-edit-input');
    if (editInput) {
      editInput.focus();
      editInput.select();
    }
  },
  
  // Actions
  async loadFolders(container) {
    try {
      const res = await fetch(`/api/folders?path=${encodeURIComponent(this.localPath)}`);
      const data = await res.json();
      this.localFolders = data.contents || [];
      this.localPath = data.path || this.localPath; // Update to resolved path
      
      // Auto-generate name from path
      if (!this.newName) {
        const parts = this.localPath.split('/').filter(Boolean);
        this.newName = parts[parts.length - 1] || '';
      }
    } catch (e) {
      this.localFolders = [];
    }
    this.render(container);
  },
  
  startEdit(id, container) {
    const p = this.projects.find(x => x.id === id);
    if (!p) return;
    
    this.editingId = id;
    this.editName = p.name;
    this.editColor = p.color || COLORS[0].value;
    this.render(container);
  },
  
  cancelEdit(container) {
    this.editingId = null;
    this.editName = '';
    this.editColor = '';
    this.render(container);
  },
  
  async saveEdit(container) {
    if (!this.editName.trim()) {
      this.error = 'Name cannot be empty';
      this.render(container);
      return;
    }
    
    const editedId = this.editingId;
    const newColor = this.editColor;
    
    try {
      const res = await fetch(`/api/projects/${editedId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: this.editName.trim(), color: newColor })
      });
      
      if (res.ok) {
        this.editingId = null;
        this.success = 'Project updated';
        await this.load();
        this.render(container);
        document.querySelector('project-bar')?.loadProjects();
        
        // If we edited the current project, update the UI accent color
        if (editedId === this.currentProjectId) {
          this.setAccentColor(newColor);
        }
        
        setTimeout(() => { this.success = ''; this.render(container); }, 2000);
      } else {
        const err = await res.json();
        this.error = err.error || 'Update failed';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Update failed';
      this.render(container);
    }
  },
  
  setAccentColor(color) {
    document.documentElement.style.setProperty('--project-color', color);
    document.documentElement.style.setProperty('--accent', color);
    // Generate dimmed version (~15% opacity)
    document.documentElement.style.setProperty('--accent-dim', color + '26');
  },
  
  async toggleFavorite(id, container) {
    const p = this.projects.find(x => x.id === id);
    if (!p) return;
    
    try {
      const res = await fetch(`/api/projects/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ favorite: !p.favorite })
      });
      
      if (res.ok) {
        p.favorite = !p.favorite;
        this.render(container);
        document.querySelector('project-bar')?.loadProjects();
      } else {
        const err = await res.json();
        this.error = err.error || 'Update failed';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Update failed';
      this.render(container);
    }
  },
  
  async deleteProject(id, container) {
    const p = this.projects.find(x => x.id === id);
    if (!p) return;
    if (!confirm(`Delete "${p.name}"? This cannot be undone.`)) return;
    
    try {
      const res = await fetch(`/api/projects/${id}`, { method: 'DELETE' });
      if (res.ok) {
        this.success = 'Project deleted';
        await this.load();
        this.render(container);
        document.querySelector('project-bar')?.loadProjects();
        setTimeout(() => { this.success = ''; this.render(container); }, 2000);
      } else {
        const err = await res.json();
        this.error = err.error || 'Delete failed';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Delete failed';
      this.render(container);
    }
  },
  
  async setDefault(id, container) {
    const p = this.projects.find(x => x.id === id);
    if (!p) return;
    
    try {
      const res = await fetch(`/api/projects/${id}/set-default`, { method: 'POST' });
      if (res.ok) {
        this.success = `"${p.name}" is now the default project`;
        this.defaultProjectId = id;
        await this.load();
        this.render(container);
        setTimeout(() => { this.success = ''; this.render(container); }, 2000);
      } else {
        const err = await res.json();
        this.error = err.error || 'Failed to set default';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Failed to set default';
      this.render(container);
    }
  },
  
  async switchProject(id, container) {
    try {
      await fetch('/api/projects/switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: id })
      });
      this.currentProjectId = id;
      this.render(container);
      document.querySelector('project-bar')?.loadProjects();
    } catch (e) {
      this.error = 'Switch failed';
      this.render(container);
    }
  },
  
  async createLocal(container) {
    if (!this.localPath) {
      this.error = 'Please select a folder';
      this.render(container);
      return;
    }
    if (!this.newName.trim()) {
      this.error = 'Please enter a project name';
      this.render(container);
      return;
    }
    
    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.newName.trim(),
          path: this.localPath,
          color: this.newColor,
          type: 'local'
        })
      });
      
      if (res.ok) {
        this.view = 'list';
        this.addType = null;
        this.success = 'Project added';
        await this.load();
        this.render(container);
        document.querySelector('project-bar')?.loadProjects();
        setTimeout(() => { this.success = ''; this.render(container); }, 2000);
      } else {
        const err = await res.json();
        this.error = err.error || 'Failed to add project';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Failed to add project';
      this.render(container);
    }
  },
  
  goBack(container) {
    this.view = 'list';
    this.addType = null;
    this.error = '';
    this.render(container);
  },
  
  async connectSSH(container) {
    if (!this.sshHost || !this.sshUser) {
      this.error = 'Host and username are required';
      this.render(container);
      return;
    }
    
    this.sshBrowsing = true;
    this.render(container);
    
    try {
      // Test connection and browse home directory
      const res = await fetch('/api/ssh/browse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: this.sshHost,
          user: this.sshUser,
          port: this.sshPort || 22,
          path: '~'
        })
      });
      const data = await res.json();
      
      if (data.success) {
        this.sshConnected = true;
        this.sshPath = data.path;
        this.sshFolders = data.contents || [];
        this.error = '';
        // Auto-generate project name from host
        if (!this.newName) {
          this.newName = this.sshHost.split('.')[0];
        }
      } else {
        this.error = data.error || 'Connection failed';
      }
    } catch (e) {
      this.error = 'Connection failed';
    }
    
    this.sshBrowsing = false;
    this.render(container);
  },
  
  disconnectSSH(container) {
    this.sshConnected = false;
    this.sshPath = '';
    this.sshFolders = [];
    this.render(container);
  },
  
  async loadSSHFolders(container) {
    this.sshBrowsing = true;
    this.render(container);
    
    try {
      const res = await fetch('/api/ssh/browse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: this.sshHost,
          user: this.sshUser,
          port: this.sshPort || 22,
          path: this.sshPath
        })
      });
      const data = await res.json();
      
      if (data.success) {
        this.sshPath = data.path;
        this.sshFolders = data.contents || [];
        // Update project name from deepest folder
        const parts = this.sshPath.split('/').filter(Boolean);
        if (parts.length && !this.newName) {
          this.newName = parts[parts.length - 1];
        }
      } else {
        this.error = data.error || 'Failed to browse';
      }
    } catch (e) {
      this.error = 'Failed to browse';
    }
    
    this.sshBrowsing = false;
    this.render(container);
  },
  
  sshNavigateUp(container) {
    const parts = this.sshPath.split('/').filter(Boolean);
    parts.pop();
    this.sshPath = '/' + parts.join('/') || '/';
    this.loadSSHFolders(container);
  },
  
  sshNavigateHome(container) {
    this.sshPath = '~';
    this.loadSSHFolders(container);
  },
  
  localNavigateUp(container) {
    const parts = this.localPath.split('/').filter(Boolean);
    parts.pop();
    this.localPath = '/' + parts.join('/') || '/';
    this.loadFolders(container);
  },
  
  localNavigateHome(container) {
    this.localPath = this.homeDir;
    this.loadFolders(container);
  },
  
  async fetchSSHSuggestions(container) {
    if (!this.sshPath || this.sshPath.length < 2) {
      this.sshSuggestions = [];
      this.render(container);
      return;
    }
    
    // Determine what to browse and what prefix to filter
    let browsePath = this.sshPath;
    let prefix = '';
    
    // If path ends with /, browse that directory with no prefix filter
    if (this.sshPath.endsWith('/')) {
      browsePath = this.sshPath;
      prefix = '';
    } else {
      // Otherwise, browse the parent directory and filter by the last segment
      const lastSlash = this.sshPath.lastIndexOf('/');
      if (lastSlash > 0) {
        browsePath = this.sshPath.substring(0, lastSlash) || '/';
        prefix = this.sshPath.substring(lastSlash + 1).toLowerCase();
      } else if (lastSlash === 0) {
        // Path like "/foo" - browse root, filter by "foo"
        browsePath = '/';
        prefix = this.sshPath.substring(1).toLowerCase();
      } else {
        // No slash at all - treat as relative to current browsed path
        browsePath = this.sshPath;
        prefix = '';
      }
    }
    
    try {
      const res = await fetch('/api/ssh/browse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: this.sshHost,
          user: this.sshUser,
          port: this.sshPort || 22,
          path: browsePath
        })
      });
      const data = await res.json();
      
      if (data.success) {
        // Filter folders that match the prefix (if any)
        let suggestions = data.contents || [];
        if (prefix) {
          suggestions = suggestions.filter(f => f.name.toLowerCase().startsWith(prefix));
        }
        this.sshSuggestions = suggestions.slice(0, 8);  // Limit to 8 suggestions
      } else {
        this.sshSuggestions = [];
      }
    } catch (e) {
      this.sshSuggestions = [];
    }
    
    this.render(container);
    
    // Re-focus and position cursor at end
    const input = container.querySelector('[data-autocomplete="ssh"]');
    if (input) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  },
  
  async testSSH(container) {
    if (!this.sshHost || !this.sshUser) {
      this.error = 'Host and username are required';
      this.render(container);
      return;
    }
    
    try {
      const res = await fetch('/api/ssh/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          host: this.sshHost,
          user: this.sshUser,
          port: this.sshPort || 22
        })
      });
      const data = await res.json();
      
      if (data.success) {
        this.success = 'Connection successful!';
        this.error = '';
      } else {
        this.error = data.error || 'Connection failed';
        this.success = '';
      }
      this.render(container);
    } catch (e) {
      this.error = 'Connection test failed';
      this.render(container);
    }
  },
  
  async createSSH(container) {
    if (!this.sshHost || !this.sshUser) {
      this.error = 'Host and username are required';
      this.render(container);
      return;
    }
    if (!this.sshPath) {
      this.error = 'Remote path is required';
      this.render(container);
      return;
    }
    if (!this.newName) {
      this.error = 'Project name is required';
      this.render(container);
      return;
    }
    
    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.newName,
          type: 'ssh',
          path: this.sshPath,
          host: this.sshHost,
          user: this.sshUser,
          port: this.sshPort || 22,
          color: this.newColor
        })
      });
      
      if (res.ok) {
        this.view = 'list';
        this.addType = null;
        this.success = 'SSH project added';
        this.sshHost = '';
        this.sshUser = '';
        this.sshPort = 22;
        this.sshPath = '';
        this.newName = '';
        await this.load();
        this.render(container);
        document.querySelector('project-bar')?.loadProjects();
        setTimeout(() => { this.success = ''; this.render(container); }, 2000);
      } else {
        const err = await res.json();
        this.error = err.error || 'Failed to add project';
        this.render(container);
      }
    } catch (e) {
      this.error = 'Failed to add project';
      this.render(container);
    }
  }
};
