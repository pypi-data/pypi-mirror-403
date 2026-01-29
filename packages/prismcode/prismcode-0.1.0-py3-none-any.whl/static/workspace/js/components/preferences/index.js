/* Preferences Modal - Mac-style settings window */
import { PrismComponent } from '../base.js';
import { ProjectsPane } from './projects-pane.js';
import { LLMPane } from './llm-pane.js';
import { AgentPane } from './agent-pane.js';

// Registry of all panes - use direct references (not spread) to preserve 'this' binding
const PANES = [
  ProjectsPane,
  LLMPane,
  // AgentPane hidden for now - not yet implemented
];

export class PrismPreferences extends PrismComponent {
  constructor() {
    super();
    this.panes = PANES;
    this.activePane = PANES[0]?.id || null;
    this.isVisible = false;
  }
  
  render() {
    this.innerHTML = `
      <div class="prefs-overlay hidden">
        <div class="prefs-modal">
          <div class="prefs-header">
            <span class="prefs-title">Settings</span>
            <button class="prefs-close" title="Close">✕</button>
          </div>
          <div class="prefs-body">
            <div class="prefs-sidebar">
              ${this.panes.map(pane => `
                <button class="prefs-tab ${pane.id === this.activePane ? 'active' : ''}" data-pane="${pane.id}">
                  <span class="prefs-tab-icon">${pane.icon}</span>
                  <span>${pane.label}</span>
                </button>
              `).join('')}
            </div>
            <div class="prefs-content"></div>
          </div>
        </div>
      </div>
    `;
    
    this.overlay = this.$('.prefs-overlay');
    this.content = this.$('.prefs-content');
  }
  
  setupEvents() {
    // Close button
    this.$('.prefs-close').addEventListener('click', () => this.hide());
    
    // Click outside to close
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) this.hide();
    });
    
    // Escape key to close
    this._escHandler = (e) => {
      if (e.key === 'Escape' && this.isVisible) this.hide();
    };
    document.addEventListener('keydown', this._escHandler);
    
    // Tab switching
    this.$$('.prefs-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        this.switchPane(tab.dataset.pane);
      });
    });
  }
  
  cleanup() {
    document.removeEventListener('keydown', this._escHandler);
  }
  
  async show() {
    // Load data for active pane
    const pane = this.panes.find(p => p.id === this.activePane);
    if (pane?.load) await pane.load();
    
    // Render the pane
    this.renderActivePane();
    
    // Show modal with animation
    this.overlay.classList.remove('hidden');
    requestAnimationFrame(() => {
      this.overlay.classList.add('visible');
    });
    this.isVisible = true;
  }
  
  hide() {
    this.overlay.classList.remove('visible');
    setTimeout(() => {
      this.overlay.classList.add('hidden');
    }, 200);
    this.isVisible = false;
  }
  
  toggle() {
    if (this.isVisible) {
      this.hide();
    } else {
      this.show();
    }
  }
  
  async switchPane(paneId) {
    if (paneId === this.activePane) return;
    
    this.activePane = paneId;
    
    // Update tab active state
    this.$$('.prefs-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.pane === paneId);
    });
    
    // Load and render new pane
    const pane = this.panes.find(p => p.id === paneId);
    if (pane?.load) await pane.load();
    this.renderActivePane();
  }
  
  renderActivePane() {
    const pane = this.panes.find(p => p.id === this.activePane);
    if (pane?.render) {
      pane.render(this.content);
    } else {
      this.content.innerHTML = '<div class="pane-hint">Select a tab</div>';
    }
  }
}

// Register custom element
customElements.define('prism-preferences', PrismPreferences);

// Export for use elsewhere
export { ProjectsPane, LLMPane, AgentPane };
