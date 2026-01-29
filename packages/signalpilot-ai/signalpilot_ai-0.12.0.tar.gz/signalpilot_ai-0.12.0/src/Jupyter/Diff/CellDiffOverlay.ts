/**
 * CellDiffOverlay - JupyterLab-specific DOM operations for diff overlays
 *
 * This module contains code that MUST use DOM APIs because it operates
 * on JupyterLab Cell nodes which are Lumino widgets, not React components.
 *
 * These operations cannot be converted to React patterns.
 */

import { Cell } from '@jupyterlab/cells';

/**
 * Remove diff overlay from a cell
 * This manipulates the cell.node DOM directly - required for JupyterLab integration
 *
 * @param cell The JupyterLab cell to remove the diff overlay from
 */
export function removeDiffOverlay(cell: Cell): void {
  try {
    const editorArea = cell.node.getElementsByClassName('jp-InputArea-editor');
    const item = editorArea.item(0) as HTMLElement;

    if (item) {
      const overlay = item.querySelector('.jp-DiffOverlay');
      if (overlay) {
        overlay.remove();
      }
      item.style.removeProperty('min-height');
    }
  } catch (error) {
    console.error('[CellDiffOverlay] Error removing diff overlay:', error);
  }
}

/**
 * Check if a cell has an active diff overlay
 *
 * @param cell The JupyterLab cell to check
 * @returns true if the cell has a diff overlay
 */
export function hasDiffOverlay(cell: Cell): boolean {
  try {
    const editorArea = cell.node.getElementsByClassName('jp-InputArea-editor');
    const item = editorArea.item(0);
    if (item) {
      return item.querySelector('.jp-DiffOverlay') !== null;
    }
  } catch (error) {
    console.error('[CellDiffOverlay] Error checking diff overlay:', error);
  }
  return false;
}

/**
 * Get the editor area element from a cell
 * Used for injecting diff UI elements
 *
 * @param cell The JupyterLab cell
 * @returns The editor area element or null
 */
export function getCellEditorArea(cell: Cell): HTMLElement | null {
  try {
    const editorArea = cell.node.getElementsByClassName('jp-InputArea-editor');
    return editorArea.item(0) as HTMLElement | null;
  } catch (error) {
    console.error('[CellDiffOverlay] Error getting editor area:', error);
    return null;
  }
}

/**
 * Get the input area element from a cell
 *
 * @param cell The JupyterLab cell
 * @returns The input area element or null
 */
export function getCellInputArea(cell: Cell): HTMLElement | null {
  try {
    return cell.node.querySelector('.jp-InputArea') as HTMLElement | null;
  } catch (error) {
    console.error('[CellDiffOverlay] Error getting input area:', error);
    return null;
  }
}
