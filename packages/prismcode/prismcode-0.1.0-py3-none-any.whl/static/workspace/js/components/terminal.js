/* Prism Workspace - Terminal Component */
import { PrismComponent } from './base.js';

export class PrismTerminal extends PrismComponent {
  constructor() {
    super();
    this.config = { project: 'local', cwd: '~' };
    this.history = [];
    this.historyIndex = -1;
    this.busy = false;
  }

  render() {
    this.innerHTML = `
      <div class="terminal">
        <div class="terminal-status">
          <span class="terminal-status-dot"></span>
          <span>Terminal</span>
          <span style="margin-left: auto; opacity: 0.5">${this.config.cwd}</span>
        </div>
        <div class="terminal-output"></div>
        <div class="terminal-input">
          <span class="terminal-prompt">$</span>
          <input type="text" spellcheck="false" placeholder="Enter command..." />
        </div>
      </div>
    `;
    this.outputEl = this.$('.terminal-output');
    this.inputEl = this.$('input');
    this.statusDot = this.$('.terminal-status-dot');
  }

  setupEvents() {
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.execute(this.inputEl.value);
        this.inputEl.value = '';
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.navigateHistory(-1);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.navigateHistory(1);
      }
    });

    // Focus input when clicking terminal
    this.addEventListener('click', () => this.inputEl.focus());

    // Socket events for terminal output
    if (window.socket) {
      window.socket.on('terminal_output', (data) => {
        if (data.terminal === this.id || !data.terminal) {
          this.appendOutput(data.output, data.type || 'stdout');
          this.setBusy(false);
        }
      });
    }
  }

  execute(command) {
    if (!command.trim()) return;
    
    this.history.push(command);
    this.historyIndex = this.history.length;
    
    this.appendOutput(command, 'command');
    this.setBusy(true);

    // Send to backend
    if (window.socket) {
      window.socket.emit('terminal_exec', {
        command,
        project: this.config.project,
        terminal: this.id,
        cwd: this.config.cwd
      });
    } else {
      // Fallback: use fetch to hit bash endpoint
      this.executeViaFetch(command);
    }
  }

  async executeViaFetch(command) {
    try {
      // For now, just show that terminal is connected
      this.appendOutput('Terminal connected. Commands will execute via agent.', 'stdout');
      this.setBusy(false);
    } catch (e) {
      this.appendOutput(`Error: ${e.message}`, 'stderr');
      this.setBusy(false);
    }
  }

  appendOutput(text, type = 'stdout') {
    const line = document.createElement('div');
    line.className = `terminal-line terminal-${type}`;
    line.textContent = text;
    this.outputEl.appendChild(line);
    this.outputEl.scrollTop = this.outputEl.scrollHeight;
  }

  navigateHistory(direction) {
    const newIndex = this.historyIndex + direction;
    if (newIndex >= 0 && newIndex < this.history.length) {
      this.historyIndex = newIndex;
      this.inputEl.value = this.history[newIndex];
    } else if (newIndex >= this.history.length) {
      this.historyIndex = this.history.length;
      this.inputEl.value = '';
    }
  }

  setBusy(busy) {
    this.busy = busy;
    this.statusDot.classList.toggle('busy', busy);
    this.inputEl.disabled = busy;
  }

  clear() {
    this.outputEl.innerHTML = '';
  }
}

customElements.define('prism-terminal', PrismTerminal);
