/* Prism Workspace - Base Component */
export class PrismComponent extends HTMLElement {
  constructor() {
    super();
    this.config = {};
  }

  connectedCallback() {
    this.render();
    this.setupEvents();
  }

  disconnectedCallback() {
    this.cleanup();
  }

  render() {}
  setupEvents() {}
  cleanup() {}

  configure(config) {
    this.config = { ...this.config, ...config };
    if (this.isConnected) this.render();
    return this;
  }

  emit(name, detail = {}) {
    this.dispatchEvent(new CustomEvent(name, { bubbles: true, detail: { component: this, ...detail } }));
  }

  $(selector) { return this.querySelector(selector); }
  $$(selector) { return this.querySelectorAll(selector); }
}
