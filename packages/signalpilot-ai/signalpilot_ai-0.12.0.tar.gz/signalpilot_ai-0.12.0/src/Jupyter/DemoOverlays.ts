/**
 * Demo Overlays for JupyterLab Elements
 *
 * Handles DOM manipulation for JupyterLab (non-React) UI elements
 * during demo mode. These overlays disable user interaction with
 * JupyterLab's native UI components.
 */

// Track overlay elements for cleanup
const overlayElements: HTMLElement[] = [];

/**
 * Create a grey overlay element with tooltip
 */
function createOverlay(zIndex: number = 9999): HTMLElement {
  const overlay = document.createElement('div');
  overlay.className = 'sage-demo-overlay';
  overlay.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(128, 128, 128, 0.3);
    z-index: ${zIndex};
    cursor: not-allowed;
    pointer-events: auto;
  `;
  overlay.title = 'Disabled on replay';
  return overlay;
}

/**
 * Add overlay to an element if it exists
 */
function addOverlayToElement(selector: string, zIndex: number = 9999): void {
  const element = document.querySelector(selector) as HTMLElement;
  if (element) {
    // Ensure element has positioning for overlay
    const currentPosition = window.getComputedStyle(element).position;
    if (currentPosition === 'static') {
      element.style.position = 'relative';
    }
    const overlay = createOverlay(zIndex);
    element.appendChild(overlay);
    overlayElements.push(overlay);
  }
}

/**
 * Add overlays to all JupyterLab UI elements
 * Called when demo mode starts
 */
export function addJupyterLabOverlays(): void {
  console.log('[DemoOverlays] Adding JupyterLab overlays');

  // Right sidebar
  addOverlayToElement(
    '.lm-Widget.lm-TabBar.jp-SideBar.jp-mod-right.lm-BoxPanel-child'
  );

  // Left sidebar
  addOverlayToElement(
    '.lm-Widget.lm-TabBar.jp-SideBar.jp-mod-left.lm-BoxPanel-child'
  );

  // Notebook toolbar
  addOverlayToElement('.lm-Widget.jp-Toolbar.jp-NotebookPanel-toolbar');

  // Tab bar
  addOverlayToElement('.lm-Widget.lm-TabBar.lm-DockPanel-tabBar');

  // Top panel (menu bar)
  const topPanel = document.getElementById('jp-top-panel') as HTMLElement;
  if (topPanel) {
    topPanel.style.position = 'relative';
    const overlay = createOverlay(9999);
    topPanel.appendChild(overlay);
    overlayElements.push(overlay);
  }
}

/**
 * Remove all JupyterLab overlays
 * Called when demo mode ends
 */
export function removeJupyterLabOverlays(): void {
  console.log('[DemoOverlays] Removing JupyterLab overlays');

  overlayElements.forEach(overlay => {
    overlay.remove();
  });
  overlayElements.length = 0;
}
