/**
 * DiffApprovalMessage Component
 *
 * Displays a diff approval dialog showing notebook cell changes.
 * Uses pure React components for rendering both active and historical diffs.
 *
 * @example
 * ```tsx
 * <DiffApprovalMessage
 *   messageId="msg_123"
 *   notebookPath="/notebooks/analysis.ipynb"
 *   diffCells={[{ cellId: 'cell_1', type: 'edit', ... }]}
 *   isHistorical={true}
 * />
 * ```
 */

import React, { memo, useCallback } from 'react';
import { IDiffCellUI, useChatMessagesStore } from '@/stores/chatMessages';
import { HistoricalDiffList } from './HistoricalDiffList';
import { ActiveDiffApprovalDialog } from './index';
import { getNotebookDiffManager } from '@/stores/servicesStore';

// ===============================================================
// TYPES
// ===============================================================

export interface DiffApprovalMessageProps {
  /** Message ID in the store */
  messageId: string;
  /** Notebook path this diff applies to */
  notebookPath?: string;
  /** Diff cells to display */
  diffCells: IDiffCellUI[];
  /** Whether this is a historical (non-interactive) display */
  isHistorical?: boolean;
  /** Callback when a cell ID is clicked */
  onCellClick?: (cellId: string) => void;
}

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * DiffApprovalMessage - Renders diff approval dialog
 *
 * For historical diffs (isHistorical=true), renders a static view of what was changed.
 * For active diffs (isHistorical=false), renders the interactive ActiveDiffApprovalDialog.
 *
 * This is part of the data-first architecture:
 * 1. When diff dialog is shown, a non-historical message is added to store
 * 2. React renders ActiveDiffApprovalDialog with interactive buttons
 * 3. When approved/rejected, message is marked historical
 * 4. React re-renders this component showing the historical view
 */
export const DiffApprovalMessage: React.FC<DiffApprovalMessageProps> = memo(
  ({
    messageId,
    notebookPath,
    diffCells,
    isHistorical = true,
    onCellClick
  }) => {
    console.log('[DiffApprovalMessage] Rendering with props:', {
      messageId,
      notebookPath,
      diffCellsCount: diffCells?.length,
      isHistorical,
      diffCells
    });

    // Handler for when the active dialog completes
    const handleComplete = useCallback(() => {
      console.log(
        '[DiffApprovalMessage] Active dialog completed, marking historical'
      );
      useChatMessagesStore.getState().markDiffApprovalHistorical(messageId);

      // CRITICAL: Also complete the class-based dialog to resolve the Promise
      // This unblocks the LLM loop when all individual cells are decided
      const diffManager = getNotebookDiffManager();
      if (diffManager?.diffApprovalDialog) {
        diffManager.diffApprovalDialog.completeAllDecided();
      }
    }, [messageId]);

    // Don't render if no cells
    if (!diffCells?.length) {
      console.log('[DiffApprovalMessage] No cells, returning null');
      return null;
    }

    // Active (non-historical) diffs render the interactive dialog
    if (!isHistorical) {
      console.log(
        '[DiffApprovalMessage] Active diff, rendering ActiveDiffApprovalDialog'
      );
      return (
        <div className="sage-ai-diff-approval-message" data-historical="false">
          <ActiveDiffApprovalDialog
            notebookPath={notebookPath}
            diffCells={diffCells}
            onComplete={handleComplete}
          />
        </div>
      );
    }

    // Convert IDiffCellUI to the format expected by HistoricalDiffList
    const formattedCells = diffCells.map(cell => ({
      cellId: cell.cellId,
      type: cell.type,
      originalContent: cell.originalContent || '',
      newContent: cell.newContent || '',
      displaySummary: cell.displaySummary || `${cell.type} cell`
    }));

    return (
      <div className="sage-ai-diff-approval-message" data-historical="true">
        <HistoricalDiffList
          diffCells={formattedCells}
          notebookPath={notebookPath}
          onCellClick={onCellClick}
        />
      </div>
    );
  }
);

DiffApprovalMessage.displayName = 'DiffApprovalMessage';

export default DiffApprovalMessage;
