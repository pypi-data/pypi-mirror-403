/* Prism Workspace - Resize Handling */
import { bus } from './events.js';

export function initResizers(workspace) {
  // Sidebar resizer - updates CSS variable so grid responds
  const sidebar = workspace.querySelector('.sidebar');
  const sidebarResizer = document.createElement('div');
  sidebarResizer.className = 'resizer resizer-h';
  sidebar.appendChild(sidebarResizer);
  makeResizable(sidebarResizer, sidebar, 'width', 'ew', { min: 160, max: 400, cssVar: '--sidebar-width' });

  // Right panel resizer - updates CSS variable so grid responds
  const rightPanel = workspace.querySelector('.right-panel');
  if (rightPanel) {
    const rightResizer = document.createElement('div');
    rightResizer.className = 'resizer resizer-h';
    rightPanel.appendChild(rightResizer);
    makeResizable(rightResizer, rightPanel, 'width', 'ew', { min: 200, max: 500, invert: true, cssVar: '--right-width' });
  }

  // Bottom panel resizer - updates CSS variable so layout responds
  const bottomPanel = workspace.querySelector('.bottom-panel');
  if (bottomPanel) {
    const bottomResizer = document.createElement('div');
    bottomResizer.className = 'resizer resizer-v';
    bottomPanel.appendChild(bottomResizer);
    makeResizable(bottomResizer, bottomPanel, 'height', 'ns', { min: 100, max: 400, invert: false, cssVar: '--bottom-height' });
  }
}

function makeResizable(handle, element, prop, cursor, { min = 0, max = Infinity, invert = false, cssVar = null } = {}) {
  let startPos, startSize;

  handle.addEventListener('mousedown', (e) => {
    e.preventDefault();
    startPos = prop === 'width' ? e.clientX : e.clientY;
    startSize = element.getBoundingClientRect()[prop];
    handle.classList.add('active');
    document.body.style.cursor = `${cursor}-resize`;
    document.body.style.userSelect = 'none';

    const onMove = (e) => {
      const currentPos = prop === 'width' ? e.clientX : e.clientY;
      let delta = currentPos - startPos;
      if (invert) delta = -delta;
      const newSize = Math.min(max, Math.max(min, startSize + delta));
      
      // Update CSS variable on workspace if specified
      if (cssVar) {
        const workspace = element.closest('.workspace');
        if (workspace) {
          workspace.style.setProperty(cssVar, `${newSize}px`);
        }
      }
      // Always set element size directly too (needed for non-grid items like bottom panel)
      element.style[prop] = `${newSize}px`;
      bus.emit('resize', { element, prop, size: newSize });
    };

    const onUp = () => {
      handle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      bus.emit('resize-end', { element, prop });
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
}
