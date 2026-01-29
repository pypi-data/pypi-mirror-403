/**
 * DiffClassManager - Centralized CSS class management for diff states
 *
 * This module handles classList operations on JupyterLab Cell nodes.
 * These operations MUST use DOM APIs because cells are Lumino widgets.
 *
 * All diff-related CSS classes are managed here for consistency.
 */

import { Cell } from '@jupyterlab/cells';

/**
 * CSS class names used for diff visualization
 */
export const DIFF_CSS_CLASSES = {
  /** Cell has an active unified merge view */
  UNIFIED_DIFF_ACTIVE: 'sage-ai-unified-diff-active',

  /** Cell has merge chunks pending resolution */
  HAS_MERGE_CHUNKS: 'has-merge-chunks',

  /** Cell originally had empty content */
  EMPTY_ORIGINAL_CONTENT: 'code-mirror-empty-original-content',

  /** Cell is in context for chat */
  IN_CONTEXT: 'sage-ai-in-context-cell',

  /** Quick generation is active on cell */
  QUICK_GEN_ACTIVE: 'sage-ai-quick-gen-active',

  /** Cell is in edit mode for diff */
  DIFF_EDIT_MODE: 'sage-ai-diff-edit-mode'
} as const;

/**
 * Add a CSS class to a cell's node
 *
 * @param cell The JupyterLab cell
 * @param className The class to add
 */
export function addDiffClass(cell: Cell, className: string): void {
  if (cell?.node) {
    cell.node.classList.add(className);
  }
}

/**
 * Remove a CSS class from a cell's node
 *
 * @param cell The JupyterLab cell
 * @param className The class to remove
 */
export function removeDiffClass(cell: Cell, className: string): void {
  if (cell?.node) {
    cell.node.classList.remove(className);
  }
}

/**
 * Check if a cell has a specific CSS class
 *
 * @param cell The JupyterLab cell
 * @param className The class to check
 * @returns true if the cell has the class
 */
export function hasDiffClass(cell: Cell, className: string): boolean {
  return cell?.node?.classList.contains(className) ?? false;
}

/**
 * Toggle a CSS class on a cell's node
 *
 * @param cell The JupyterLab cell
 * @param className The class to toggle
 * @param force Optional force value (true = add, false = remove)
 * @returns The new state (true if class is now present)
 */
export function toggleDiffClass(
  cell: Cell,
  className: string,
  force?: boolean
): boolean {
  if (cell?.node) {
    return cell.node.classList.toggle(className, force);
  }
  return false;
}

// ============================================================
// Convenience functions for common diff state management
// ============================================================

/**
 * Mark a cell as having an active unified diff view
 */
export function setUnifiedDiffActive(cell: Cell, active: boolean): void {
  if (active) {
    addDiffClass(cell, DIFF_CSS_CLASSES.UNIFIED_DIFF_ACTIVE);
  } else {
    removeDiffClass(cell, DIFF_CSS_CLASSES.UNIFIED_DIFF_ACTIVE);
  }
}

/**
 * Check if cell has an active unified diff view
 */
export function isUnifiedDiffActive(cell: Cell): boolean {
  return hasDiffClass(cell, DIFF_CSS_CLASSES.UNIFIED_DIFF_ACTIVE);
}

/**
 * Mark a cell as having pending merge chunks
 */
export function setHasMergeChunks(cell: Cell, hasChunks: boolean): void {
  if (hasChunks) {
    addDiffClass(cell, DIFF_CSS_CLASSES.HAS_MERGE_CHUNKS);
  } else {
    removeDiffClass(cell, DIFF_CSS_CLASSES.HAS_MERGE_CHUNKS);
  }
}

/**
 * Check if cell has pending merge chunks
 */
export function hasMergeChunks(cell: Cell): boolean {
  return hasDiffClass(cell, DIFF_CSS_CLASSES.HAS_MERGE_CHUNKS);
}

/**
 * Mark a cell as originally having empty content
 */
export function setEmptyOriginalContent(cell: Cell, isEmpty: boolean): void {
  if (isEmpty) {
    addDiffClass(cell, DIFF_CSS_CLASSES.EMPTY_ORIGINAL_CONTENT);
  } else {
    removeDiffClass(cell, DIFF_CSS_CLASSES.EMPTY_ORIGINAL_CONTENT);
  }
}

/**
 * Clean up all diff-related classes from a cell
 */
export function cleanupDiffClasses(cell: Cell): void {
  removeDiffClass(cell, DIFF_CSS_CLASSES.UNIFIED_DIFF_ACTIVE);
  removeDiffClass(cell, DIFF_CSS_CLASSES.HAS_MERGE_CHUNKS);
  removeDiffClass(cell, DIFF_CSS_CLASSES.EMPTY_ORIGINAL_CONTENT);
  removeDiffClass(cell, DIFF_CSS_CLASSES.DIFF_EDIT_MODE);
}
