/* Prism Workspace - Settings Component */
import { PrismComponent } from './base.js';
import { bus } from '../core/events.js';
import { loadSetting, saveSetting } from '../core/storage.js';

export class PrismSettings extends PrismComponent {
  constructor() {
    super();
    this.projects = [];
    this.currentProject = 'local';
  }

  render() {
    const showDiff = loadSetting('showDiff', true);
    
    this.innerHTML = `
      <div class="settings">
        <div class="settings-header">⚙ Settings</div>
        
        <div class="settings-section">
          <div class="settings-section-title">Project</div>
          <div class="project-list" id="project-list">
            <div class="project-item active" data-project="local">
              <span class="project-color" style="background: #ff6b2b"></span>
              <div class="project-info">
                <div class="project-name">Local</div>
                <div class="project-path">local</div>
              </div>
            </div>
          </div>
          <button class="btn btn-secondary btn-sm" style="margin-top: 8px; width: 100%" id="add-project-btn">+ Add Project</button>
        </div>

        <div class="settings-section">
          <div class="settings-section-title">Display</div>
          <div class="settings-item">
            <span class="settings-label">Detailed Diffs</span>
            <label class="toggle">
              <input type="checkbox" id="show-diff" ${showDiff ? 'checked' : ''}>
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="settings-item">
            <span class="settings-label">Theme</span>
            <select class="settings-select" id="theme-select">
              <option value="dark" selected>Dark</option>
              <option value="light">Light (coming soon)</option>
            </select>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-title">Model</div>
          <div class="settings-item">
            <span class="settings-label">Current Model</span>
            <span class="settings-value" id="current-model">claude-opus</span>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-title">Connections</div>
          <div id="connections-list">
            <div class="settings-item">
              <span class="settings-label">Local</span>
              <span class="settings-value" style="color: var(--success)">● Connected</span>
            </div>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-section-title">Keyboard Shortcuts</div>
          <div class="settings-item">
            <span class="settings-label">Toggle Terminal</span>
            <span class="settings-value"><kbd>Ctrl</kbd> + <kbd>\`</kbd></span>
          </div>
          <div class="settings-item">
            <span class="settings-label">Toggle Sidebar</span>
            <span class="settings-value"><kbd>Ctrl</kbd> + <kbd>B</kbd></span>
          </div>
          <div class="settings-item">
            <span class="settings-label">New Tab</span>
            <span class="settings-value"><kbd>Ctrl</kbd> + <kbd>T</kbd></span>
          </div>
          <div class="settings-item">
            <span class="settings-label">Close Tab</span>
            <span class="settings-value"><kbd>Ctrl</kbd> + <kbd>W</kbd></span>
          </div>
          <div class="settings-item">
            <span class="settings-label">Cancel Generation</span>
            <span class="settings-value"><kbd>Escape</kbd></span>
          </div>
        </div>
      </div>
    `;

    this.loadProjects();
  }

  setupEvents() {
    this.$('#show-diff')?.addEventListener('change', (e) => {
      saveSetting('showDiff', e.target.checked);
      this.toggleDiff(e.target.checked);
    });

    this.$('#add-project-btn')?.addEventListener('click', () => {
      this.showAddProjectDialog();
    });

    bus.on('project-changed', ({ projectId }) => {
      this.currentProject = projectId;
      this.updateProjectList();
    });
  }

  async loadProjects() {
    try {
      const res = await fetch('/api/projects');
      const data = await res.json();
      this.projects = data.projects || [];
      this.currentProject = data.current || 'local';
      this.updateProjectList();
    } catch (e) {
      // Use default local project
      this.projects = [{ id: 'local', name: 'Local', type: 'local', color: '#ff6b2b' }];
    }
  }

  updateProjectList() {
    const list = this.$('#project-list');
    if (!list) return;

    const defaultProjects = [
      { id: 'local', name: 'Local', type: 'local', color: '#ff6b2b' }
    ];
    const projects = this.projects.length ? this.projects : defaultProjects;

    list.innerHTML = projects.map(p => `
      <div class="project-item ${p.id === this.currentProject ? 'active' : ''}" data-project="${p.id}">
        <span class="project-color" style="background: ${p.color || '#ff6b2b'}"></span>
        <div class="project-info">
          <div class="project-name">${p.name || p.id}</div>
          <div class="project-path">${p.type === 'ssh' ? p.host : 'local'}</div>
        </div>
        ${p.type === 'ssh' ? `<span class="project-status">${p.connected ? '●' : '○'}</span>` : ''}
      </div>
    `).join('');

    list.querySelectorAll('.project-item').forEach(el => {
      el.addEventListener('click', () => {
        const projectId = el.dataset.project;
        bus.emit('project-switched', { projectId });
      });
    });
  }

  async toggleDiff(show) {
    try {
      await fetch('/api/toggle-diff', { method: 'POST' });
    } catch (e) {
      console.warn('Failed to toggle diff:', e);
    }
  }

  showAddProjectDialog() {
    // For now, just log - would show a modal in full implementation
    console.log('Add project dialog - TODO');
    alert('Project management coming soon!\n\nWill support:\n- Local projects\n- SSH remote projects\n- Git repositories');
  }
}

customElements.define('prism-settings', PrismSettings);
