/* Prism Workspace - Tree Component */
import { PrismComponent } from './base.js';
import { bus } from '../core/events.js';

export class PrismTree extends PrismComponent {
  constructor() {
    super();
    this.config = { type: 'sessions' };
    this.items = [];
    this.activeId = null;
    this.currentProjectId = null;
  }

  render() {
    this.innerHTML = `
      <div class="tree">
        <div class="tree-header">
          <span class="tree-title">${this.getTitle()}</span>
          <div class="tree-actions">
            ${this.config.type === 'sessions' ? '<button class="btn btn-ghost btn-sm" id="new-btn" title="New Session">+</button>' : ''}
            <button class="btn btn-ghost btn-sm" id="refresh-btn" title="Refresh">↻</button>
          </div>
        </div>
        <div class="tree-list"></div>
      </div>
    `;
    this.listEl = this.$('.tree-list');
    this.load();
  }

  setupEvents() {
    this.$('#refresh-btn')?.addEventListener('click', () => this.load());
    this.$('#new-btn')?.addEventListener('click', () => this.createNew());

    bus.on('title-updated', (data) => {
      if (this.config.type === 'sessions') this.load();
    });
    
    // Refresh sessions when project changes
    bus.on('project-switched', (data) => {
      if (this.config.type === 'sessions' && data.project) {
        this.currentProjectId = data.project.id;
        this.load();
      }
    });
  }

  getTitle() {
    const titles = { sessions: 'Sessions', files: 'Explorer', projects: 'Projects' };
    return titles[this.config.type] || this.config.type;
  }

  async load() {
    this.listEl.innerHTML = '<div class="tree-empty">Loading...</div>';
    
    try {
      if (this.config.type === 'sessions') {
        // Filter by project if we have one
        const url = this.currentProjectId 
          ? `/api/sessions?project_id=${this.currentProjectId}`
          : '/api/sessions';
        const res = await fetch(url);
        const data = await res.json();
        this.items = data.sessions || [];
        this.activeId = data.current;
        this.renderSessions();
      } else if (this.config.type === 'files') {
        // File tree would go here - for now show placeholder
        this.listEl.innerHTML = '<div class="tree-empty">File explorer coming soon</div>';
      } else if (this.config.type === 'projects') {
        const res = await fetch('/api/projects');
        const data = await res.json();
        this.items = data.projects || [];
        this.renderProjects();
      }
    } catch (e) {
      this.listEl.innerHTML = '<div class="tree-empty">Failed to load</div>';
    }
  }

  renderSessions() {
    if (!this.items.length) {
      this.listEl.innerHTML = '<div class="tree-empty">No sessions yet</div>';
      return;
    }

    this.listEl.innerHTML = this.items.map(s => `
      <div class="tree-item session ${s.id === this.activeId ? 'active' : ''}" data-id="${s.id}">
        <span class="tree-label">${this.escapeHtml(s.title || s.preview || 'Untitled')}</span>
        <span class="tree-meta">${s.message_count || 0}</span>
      </div>
    `).join('');

    this.listEl.querySelectorAll('.tree-item').forEach(el => {
      el.addEventListener('click', () => this.selectSession(el.dataset.id));
    });
  }

  renderProjects() {
    if (!this.items.length) {
      this.listEl.innerHTML = '<div class="tree-empty">No projects configured</div>';
      return;
    }

    this.listEl.innerHTML = this.items.map(p => `
      <div class="tree-item ${p.id === this.activeId ? 'active' : ''}" data-id="${p.id}">
        <span class="tree-icon" style="color: ${p.color || 'var(--accent)'}">●</span>
        <span class="tree-label">${this.escapeHtml(p.name)}</span>
        <span class="tree-meta">${p.type || 'local'}</span>
      </div>
    `).join('');

    this.listEl.querySelectorAll('.tree-item').forEach(el => {
      el.addEventListener('click', () => this.selectProject(el.dataset.id));
    });
  }

  async selectSession(id) {
    if (id === this.activeId) return;

    try {
      const res = await fetch('/api/load-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: id })
      });
      const data = await res.json();
      
      if (data.success) {
        this.activeId = id;
        this.renderSessions();
        bus.emit('session-loaded', { session: data, history: data.history });
        
        // Close mobile panels after selecting a session
        bus.emit('close-mobile-panels');
      }
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  }

  selectProject(id) {
    this.activeId = id;
    this.renderProjects();
    bus.emit('project-selected', { projectId: id });
  }

  async createNew() {
    try {
      // If we have a current project, create session for that project
      const url = this.currentProjectId 
        ? `/api/projects/${this.currentProjectId}/new-session`
        : '/api/new-session';
      
      const res = await fetch(url, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        this.activeId = data.session_id;
        this.load();
        bus.emit('session-created', { 
          sessionId: data.session_id,
          projectId: data.project_id || this.currentProjectId
        });
        
        // Close mobile panels after creating a session
        bus.emit('close-mobile-panels');
      }
    } catch (e) {
      console.error('Failed to create session:', e);
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
  }
}

customElements.define('prism-tree', PrismTree);
