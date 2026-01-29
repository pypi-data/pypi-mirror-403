/**
 * HistoricalDiffList Component
 *
 * Renders a list of historical diff cells for display in chat history.
 * This is a pure React replacement for DiffApprovalDialog.createHistoricalDialog().
 *
 * @example
 * ```tsx
 * <HistoricalDiffList
 *   diffCells={[
 *     { cellId: 'cell_1', type: 'edit', originalContent: 'x = 1', newContent: 'x = 2' }
 *   ]}
 *   notebookPath="/notebooks/analysis.ipynb"
 *   onCellClick={handleCellClick}
 * />
 * ```
 */

import React, { memo, useCallback } from 'react';
import { HistoricalDiffCell } from './HistoricalDiffCell';
import {
  getNotebookTools,
  getNotebookDiffManager
} from '@/stores/servicesStore';
import { IPendingDiff } from '@/types';

// ===============================================================
// TYPES
// ===============================================================

export interface DiffCellData {
  /** Cell identifier */
  cellId: string;
  /** Type of change (add, edit, remove) */
  type: string;
  /** Original cell content */
  originalContent: string;
  /** New cell content */
  newContent: string;
  /** Display summary for the change */
  displaySummary?: string;
  /** Additional metadata */
  metadata?: Record<string, unknown>;
}

export interface HistoricalDiffListProps {
  /** Array of diff cells to display */
  diffCells: DiffCellData[];
  /** Notebook path for context */
  notebookPath?: string;
  /** Callback when a cell ID is clicked */
  onCellClick?: (cellId: string) => void;
}

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * HistoricalDiffList - Renders a list of historical diff cells
 */
export const HistoricalDiffList: React.FC<HistoricalDiffListProps> = memo(
  ({ diffCells, notebookPath, onCellClick }) => {
    // Handle cell click - scroll to cell in notebook
    const handleCellClick = useCallback(
      (cellId: string) => {
        if (onCellClick) {
          onCellClick(cellId);
        } else {
          // Default behavior: scroll to cell
          void getNotebookTools()?.scrollToCellById(cellId);
        }
      },
      [onCellClick]
    );

    // Handle reapply button click
    const handleReapply = useCallback(
      (cellId: string) => {
        // Get the diff cell data
        const diffCell = diffCells.find(cell => cell.cellId === cellId);
        if (!diffCell) return;

        // Get the diff manager and call reapplyDiff directly
        const diffManager = getNotebookDiffManager();
        if (diffManager) {
          // Convert to IPendingDiff format
          const pendingDiff: IPendingDiff = {
            cellId: diffCell.cellId,
            type: diffCell.type as 'add' | 'edit' | 'remove',
            originalContent: diffCell.originalContent,
            newContent: diffCell.newContent,
            displaySummary: diffCell.displaySummary,
            notebookId: notebookPath,
            metadata: diffCell.metadata || {}
          };

          diffManager.reapplyDiff(pendingDiff);
        }
      },
      [diffCells, notebookPath]
    );

    // Don't render if no cells
    if (!diffCells || diffCells.length === 0) {
      return null;
    }

    return (
      <div className="sage-ai-diff-approval-dialog-embedded sage-ai-diff-approval-historical">
        <div className="sage-ai-diff-list">
          {diffCells.map(cell => (
            <HistoricalDiffCell
              key={cell.cellId}
              cellId={cell.cellId}
              type={cell.type}
              originalContent={cell.originalContent}
              newContent={cell.newContent}
              displaySummary={cell.displaySummary}
              notebookPath={notebookPath}
              onCellClick={handleCellClick}
              onReapply={handleReapply}
            />
          ))}
        </div>
      </div>
    );
  }
);

HistoricalDiffList.displayName = 'HistoricalDiffList';

export default HistoricalDiffList;
