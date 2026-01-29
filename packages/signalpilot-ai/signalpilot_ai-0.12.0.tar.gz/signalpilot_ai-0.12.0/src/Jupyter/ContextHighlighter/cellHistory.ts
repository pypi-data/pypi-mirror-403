/**
 * Cell History Manager
 *
 * Manages undo history for AI-modified cells, allowing users to
 * revert changes made by inline editing.
 */

import { Cell } from '@jupyterlab/cells';
import { CellHistoryMap } from './types';

/**
 * Manages cell content history for undo functionality
 */
export class CellHistoryManager {
  private cellHistory: CellHistoryMap = new Map();

  /**
   * Save current cell content to history before modification
   */
  saveToHistory(trackingId: string, content: string): void {
    if (!this.cellHistory.has(trackingId)) {
      this.cellHistory.set(trackingId, []);
    }
    this.cellHistory.get(trackingId)!.push(content);
  }

  /**
   * Handle undo functionality for a cell
   */
  handleUndo(cell: Cell): boolean {
    const metadata: any = cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;

    if (trackingId && this.cellHistory.has(trackingId)) {
      const history = this.cellHistory.get(trackingId);
      if (history && history.length > 0) {
        // Get the most recent previous version
        const previousContent = history.pop()!;
        cell.model.sharedModel.setSource(previousContent);

        // Remove from history if empty
        if (history.length === 0) {
          this.cellHistory.delete(trackingId);
        }

        return true;
      }
    }
    return false;
  }

  /**
   * Clear history for a specific cell
   */
  clearCellHistory(trackingId: string): void {
    this.cellHistory.delete(trackingId);
  }

  /**
   * Get the number of undo steps available for a cell
   */
  getUndoStepsAvailable(trackingId: string): number {
    const history = this.cellHistory.get(trackingId);
    return history ? history.length : 0;
  }

  /**
   * Check if a cell has undo history
   */
  hasHistory(trackingId: string): boolean {
    return this.getUndoStepsAvailable(trackingId) > 0;
  }

  /**
   * Restore to original content on cancellation
   */
  restoreOnCancel(trackingId: string, cell: Cell): void {
    if (this.cellHistory.has(trackingId)) {
      const history = this.cellHistory.get(trackingId);
      if (history && history.length > 0) {
        // Get the most recent version (the original content before editing)
        const originalContent = history[history.length - 1];
        cell.model.sharedModel.setSource(originalContent);

        // Clean up the history entry since we're cancelling
        history.pop();
        if (history.length === 0) {
          this.cellHistory.delete(trackingId);
        }
      }
    }
  }
}

/**
 * Update undo button tooltip and state
 */
export function updateUndoButtonState(
  cell: Cell,
  historyManager: CellHistoryManager
): void {
  const metadata: any = cell.model.sharedModel.getMetadata() || {};
  const trackingId = metadata.cell_tracker?.trackingId;
  const undoButton = cell.node.querySelector(
    '.sage-ai-quick-gen-undo'
  ) as HTMLButtonElement;

  if (undoButton && trackingId) {
    const stepsAvailable = historyManager.getUndoStepsAvailable(trackingId);
    undoButton.disabled = stepsAvailable === 0;
    undoButton.title =
      stepsAvailable > 0
        ? `Undo AI changes (${stepsAvailable} step${stepsAvailable > 1 ? 's' : ''} available)`
        : 'No AI changes to undo';
  }
}
