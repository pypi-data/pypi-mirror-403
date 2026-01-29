/**
 * ActiveDiffApprovalDialog Component
 *
 * Main container for the interactive diff approval dialog.
 * Composes DiffCellItem components and uses the useDiffApproval hook.
 */

import React, { memo, useEffect } from 'react';
import { DiffApprovalDialogProps } from './types';
import { useDiffApproval } from '../../hooks/useDiffApproval';
import { DiffCellItem } from './DiffCellItem';
import { BulkActionButtons } from './DiffActionButtons';

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * ActiveDiffApprovalDialog - Interactive diff approval UI
 *
 * Renders when a diff approval is active (not historical).
 * Provides approve/reject/run actions for individual cells and bulk operations.
 */
export const ActiveDiffApprovalDialog: React.FC<DiffApprovalDialogProps> = memo(
  ({ notebookPath, diffCells, onComplete }) => {
    // Get state and actions from hook
    const {
      cellDecisions,
      isAllDecided,
      approveCell,
      rejectCell,
      runCell,
      approveAll,
      rejectAll
    } = useDiffApproval(diffCells, notebookPath);

    // Notify when all decisions are made
    useEffect(() => {
      if (isAllDecided && diffCells.length > 0) {
        console.log('[ActiveDiffApprovalDialog] All cells decided, completing');
        onComplete?.();
      }
    }, [isAllDecided, diffCells.length, onComplete]);

    // Don't render if no cells
    if (!diffCells?.length) {
      return null;
    }

    return (
      <div className="sage-ai-diff-approval-dialog-embedded sage-ai-diff-approval-active">
        {/* List of diff cells */}
        <div className="sage-ai-diff-list">
          {diffCells.map(cell => (
            <DiffCellItem
              key={cell.cellId}
              cell={cell}
              decision={cellDecisions.get(cell.cellId) || {}}
              onApprove={approveCell}
              onReject={rejectCell}
              onRun={runCell}
            />
          ))}
        </div>

        {/* Bulk action buttons */}
        <BulkActionButtons
          onApproveAll={approveAll}
          onRejectAll={rejectAll}
          isRunContext={true}
        />
      </div>
    );
  }
);

ActiveDiffApprovalDialog.displayName = 'ActiveDiffApprovalDialog';

export default ActiveDiffApprovalDialog;
