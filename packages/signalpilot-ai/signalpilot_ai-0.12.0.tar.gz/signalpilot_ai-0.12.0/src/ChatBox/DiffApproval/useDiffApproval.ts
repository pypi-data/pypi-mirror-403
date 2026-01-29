/**
 * useDiffApproval Hook
 *
 * Manages diff approval state and actions.
 * Subscribes to the diffStore and provides action handlers.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { IDiffCellUI } from '@/stores/chatMessages';
import { useDiffStore } from '@/stores/diffStore';
import { IPendingDiff } from '@/types';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { CellDecision, DiffApprovalActions, DiffApprovalState } from './types';

/**
 * Hook for managing diff approval state and actions
 */
export function useDiffApproval(
  diffCells: IDiffCellUI[],
  notebookPath?: string
): DiffApprovalState & DiffApprovalActions {
  const [cellDecisions, setCellDecisions] = useState<Map<string, CellDecision>>(
    new Map()
  );

  // Subscribe to diff store changes
  useEffect(() => {
    const updateFromStore = (pendingDiffs: Map<string, IPendingDiff>) => {
      const newDecisions = new Map<string, CellDecision>();

      diffCells.forEach(cell => {
        const diff = pendingDiffs.get(cell.cellId);
        if (diff) {
          newDecisions.set(cell.cellId, {
            approved: diff.approved,
            userDecision: diff.userDecision || undefined,
            runResult: diff.runResult,
            isRunning: diff.userDecision === 'run' && !diff.runResult
          });
        }
      });

      setCellDecisions(newDecisions);
    };

    // Initialize from current state
    updateFromStore(useDiffStore.getState().pendingDiffs);

    // Subscribe to store changes
    const unsubscribe = useDiffStore.subscribe(
      state => state.pendingDiffs,
      updateFromStore
    );

    return unsubscribe;
  }, [diffCells]);

  // Check if all cells have been decided
  // For cells with userDecision === 'run', we must wait for runResult
  // to avoid a race condition where the dialog completes before execution finishes
  const isAllDecided = useMemo(() => {
    if (diffCells.length === 0 || cellDecisions.size !== diffCells.length) {
      return false;
    }

    return diffCells.every(cell => {
      const decision = cellDecisions.get(cell.cellId);
      if (!decision) return false;

      // If the cell was run, we must wait for the result
      if (decision.userDecision === 'run') {
        return decision.runResult !== undefined;
      }

      // For approve/reject without running, approved being set is enough
      return decision.approved !== undefined;
    });
  }, [cellDecisions, diffCells]);

  // Get the diff manager for actions
  const getDiffDialog = useCallback(() => {
    return getNotebookDiffManager()?.diffApprovalDialog;
  }, []);

  // Action: Approve a single cell
  const approveCell = useCallback(
    (cellId: string) => {
      getDiffDialog()?.approveCell(cellId);
    },
    [getDiffDialog]
  );

  // Action: Reject a single cell
  const rejectCell = useCallback(
    (cellId: string) => {
      getDiffDialog()?.rejectCell(cellId);
    },
    [getDiffDialog]
  );

  // Action: Run a single cell (approve + execute)
  const runCell = useCallback(
    async (cellId: string) => {
      await getDiffDialog()?.runCell(cellId);
    },
    [getDiffDialog]
  );

  // Action: Approve all cells
  const approveAll = useCallback(async () => {
    await getDiffDialog()?.approveAll();
  }, [getDiffDialog]);

  // Action: Reject all cells
  const rejectAll = useCallback(async () => {
    await getDiffDialog()?.rejectAll();
  }, [getDiffDialog]);

  return {
    cellDecisions,
    isAllDecided,
    approveCell,
    rejectCell,
    runCell,
    approveAll,
    rejectAll
  };
}

export default useDiffApproval;
