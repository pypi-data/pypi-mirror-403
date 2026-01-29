/**
 * Project Bar Component - Tabs Style
 * 
 * Shows all projects as tabs in the title bar, sorted by most recent.
 * Click to switch, + button to add new.
 */

import { PrismComponent } from './base.js';
import { bus } from '../core/events.js';

export class ProjectBar extends PrismComponent {
    constructor() {
        super();
        this.projects = [];
        this.currentProjectId = null;
    }

    connectedCallback() {
        super.connectedCallback();
        this.loadProjects();
    }

    async loadProjects() {
        try {
            const res = await fetch('/api/projects');
            const data = await res.json();
            this.projects = data.projects || [];
            this.currentProjectId = data.current || null;
            
            if (this.currentProject) {
                this.setProjectColor(this.currentProject.color);
            }

            this.render();
        } catch (err) {
            console.error('Failed to load projects:', err);
        }
    }

    get currentProject() {
        return this.projects.find(p => p.id === this.currentProjectId);
    }

    get sortedProjects() {
        // Sort by last accessed, most recent first
        return [...this.projects].sort((a, b) => {
            const aTime = a.last_accessed ? new Date(a.last_accessed).getTime() : 0;
            const bTime = b.last_accessed ? new Date(b.last_accessed).getTime() : 0;
            return bTime - aTime;
        });
    }

    async switchProject(projectId) {
        if (projectId === this.currentProjectId) return;
        
        const project = this.projects.find(p => p.id === projectId);
        if (!project) return;
        
        this.currentProjectId = projectId;
        this.setProjectColor(project.color);
        
        bus.emit('project-switched', { 
            project,
            sessionId: null,
            isNewSession: false
        });
        
        this.render();
    }

    setProjectColor(color) {
        document.documentElement.style.setProperty('--project-color', color);
        document.documentElement.style.setProperty('--accent', color);
        document.documentElement.style.setProperty('--accent-dim', color + '26');
    }

    openAddProject() {
        bus.emit('open-preferences', { pane: 'projects', action: 'add' });
    }

    render() {
        const sorted = this.sortedProjects;
        
        this.innerHTML = `
            <div class="project-tabs">
                ${sorted.map(p => `
                    <button 
                        class="project-tab ${p.id === this.currentProjectId ? 'active' : ''}"
                        data-id="${p.id}"
                        style="--tab-color: ${p.color || '#ff6b2b'}"
                        title="${this.esc(p.name)}${p.type === 'ssh' ? ' (SSH)' : ''}"
                    >
                        <span class="project-tab-dot"></span>
                        <span class="project-tab-name">${this.esc(p.name)}</span>
                        ${p.notifications > 0 ? `<span class="project-tab-badge">${p.notifications}</span>` : ''}
                    </button>
                `).join('')}
                
                <button class="project-tab-add" title="Add Project">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"/>
                    </svg>
                </button>
            </div>
        `;

        this.bindEvents();
    }

    bindEvents() {
        // Project tabs
        this.querySelectorAll('.project-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switchProject(tab.dataset.id);
            });
        });
        
        // Add button
        this.querySelector('.project-tab-add')?.addEventListener('click', () => {
            this.openAddProject();
        });
    }

    esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    }
}

customElements.define('project-bar', ProjectBar);
