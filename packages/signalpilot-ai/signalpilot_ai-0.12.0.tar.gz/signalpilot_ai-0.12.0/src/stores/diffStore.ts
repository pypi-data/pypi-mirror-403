// src/stores/diffStore.ts
// PURPOSE: Manage pending code diffs and approval workflow
// Replaces DiffStateService.ts RxJS implementation
// ~180 lines

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { useEffect, useRef } from 'react';
import { IPendingDiff } from '../types';

// Track update count for debugging
let diffUpdateCount = 0;

// Custom serializer for devtools to handle Maps
const devtoolsSerialize = {
  replacer: (_key: string, value: any) => {
    if (value instanceof Map) {
      return `[Map: ${value.size} entries]`;
    }
    return value;
  }
};

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IDiffStateChange {
  cellId: string;
  approved: boolean | undefined;
  notebookId?: string | null;
}

export interface IApprovalStatus {
  pending: number;
  approved: number;
  rejected: number;
  allResolved: boolean;
}

interface IDiffState {
  pendingDiffs: Map<string, IPendingDiff>;
  notebookId: string | null;
  // Loading states for action buttons (shared between LLMStateContent and DiffNavigationContent)
  isRunAllLoading: boolean;
  isRejectAllLoading: boolean;
  isApproveAllLoading: boolean;
}

interface IDiffActions {
  // Diff management
  addDiff: (cellId: string, diff: IPendingDiff) => void;
  removeDiff: (cellId: string, notebookId?: string | null) => void;
  updateDiffApproval: (
    cellId: string,
    approved: boolean | undefined,
    notebookId?: string | null
  ) => void;
  updateDiffToRun: (cellId: string, notebookId?: string | null) => void;
  updateDiffResult: (cellId: string, runResult: any) => void;
  clearDiffs: (notebookId?: string | null) => void;
  updatePendingDiffs: (
    pendingDiffs: Map<string, IPendingDiff>,
    notebookId?: string | null
  ) => void;

  // Notebook context
  setNotebookId: (notebookId: string | null) => void;

  // Loading state actions
  setRunAllLoading: (loading: boolean) => void;
  setRejectAllLoading: (loading: boolean) => void;
  setApproveAllLoading: (loading: boolean) => void;

  // Getters (for computed values)
  getAllDiffsResolved: (notebookId?: string | null) => boolean;
  getPendingDiffCount: (notebookId?: string | null) => number;
  getApprovedDiffCount: (notebookId?: string | null) => number;
  getRejectedDiffCount: (notebookId?: string | null) => number;
  getApprovalStatus: (notebookId?: string | null) => IApprovalStatus;
  getDiffsForNotebook: (notebookId?: string | null) => IPendingDiff[];
  getCellDiff: (cellId: string) => IPendingDiff | undefined;
}

type IDiffStore = IDiffState & IDiffActions;

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

function checkIfAllDiffsResolved(
  pendingDiffs: Map<string, IPendingDiff>,
  notebookId?: string | null
): boolean {
  const relevantDiffs: IPendingDiff[] = [];

  for (const [, diff] of pendingDiffs) {
    if (!notebookId || diff.notebookId === notebookId) {
      relevantDiffs.push(diff);
    }
  }

  if (relevantDiffs.length === 0) {
    return true;
  }

  // Check for pending "run" decisions that haven't completed
  for (const diff of relevantDiffs) {
    if (diff.userDecision === 'run' && !diff.runResult) {
      return false;
    }
  }

  return relevantDiffs.every(
    diff =>
      diff.approved !== undefined ||
      diff.userDecision === 'approved' ||
      diff.userDecision === 'rejected' ||
      diff.userDecision === 'run'
  );
}

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDiffStore = create<IDiffStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      pendingDiffs: new Map(),
      notebookId: null,
      isRunAllLoading: false,
      isRejectAllLoading: false,
      isApproveAllLoading: false,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      addDiff: (cellId, diff) =>
        set(state => {
          const newDiffs = new Map(state.pendingDiffs);
          newDiffs.set(cellId, diff);
          return {
            pendingDiffs: newDiffs,
            notebookId: diff.notebookId ?? state.notebookId
          };
        }),

      removeDiff: (cellId, notebookId) =>
        set(state => {
          const newDiffs = new Map(state.pendingDiffs);
          newDiffs.delete(cellId);
          return {
            pendingDiffs: newDiffs,
            notebookId: notebookId ?? state.notebookId
          };
        }),

      updateDiffApproval: (cellId, approved, notebookId) =>
        set(state => {
          const newDiffs = new Map(state.pendingDiffs);
          const existing = newDiffs.get(cellId);
          if (existing) {
            newDiffs.set(cellId, {
              ...existing,
              approved,
              userDecision:
                existing.userDecision ||
                (approved === true
                  ? 'approved'
                  : approved === false
                    ? 'rejected'
                    : null)
            });
          }
          return {
            pendingDiffs: newDiffs,
            notebookId: notebookId ?? state.notebookId
          };
        }),

      updateDiffToRun: (cellId, notebookId) =>
        set(state => {
          const newDiffs = new Map(state.pendingDiffs);
          const existing = newDiffs.get(cellId);
          if (existing) {
            newDiffs.set(cellId, {
              ...existing,
              approved: true,
              userDecision: 'run'
            });
          }
          return {
            pendingDiffs: newDiffs,
            notebookId: notebookId ?? state.notebookId
          };
        }),

      updateDiffResult: (cellId, runResult) =>
        set(state => {
          const newDiffs = new Map(state.pendingDiffs);
          const existing = newDiffs.get(cellId);
          if (existing) {
            newDiffs.set(cellId, { ...existing, runResult });
          }
          return { pendingDiffs: newDiffs };
        }),

      clearDiffs: notebookId =>
        set(state => {
          console.log('[DiffStore] Clearing diffs', notebookId);
          if (!notebookId) {
            return { pendingDiffs: new Map() };
          }
          // Clear only diffs for specific notebook
          const newDiffs = new Map<string, IPendingDiff>();
          state.pendingDiffs.forEach((diff, cellId) => {
            if (diff.notebookId !== notebookId) {
              newDiffs.set(cellId, diff);
            }
          });
          return {
            pendingDiffs: newDiffs,
            notebookId: notebookId ?? state.notebookId
          };
        }),

      updatePendingDiffs: (pendingDiffs, notebookId) =>
        set(state => ({
          pendingDiffs,
          notebookId: notebookId ?? state.notebookId
        })),

      setNotebookId: notebookId => set({ notebookId }),

      // Loading state setters
      setRunAllLoading: loading => set({ isRunAllLoading: loading }),
      setRejectAllLoading: loading => set({ isRejectAllLoading: loading }),
      setApproveAllLoading: loading => set({ isApproveAllLoading: loading }),

      // ─────────────────────────────────────────────────────────────
      // Computed Getters
      // ─────────────────────────────────────────────────────────────
      getAllDiffsResolved: notebookId => {
        const state = get();
        return checkIfAllDiffsResolved(state.pendingDiffs, notebookId);
      },

      getPendingDiffCount: notebookId => {
        const state = get();
        let count = 0;
        state.pendingDiffs.forEach(diff => {
          if (
            (!notebookId || diff.notebookId === notebookId) &&
            !diff.userDecision
          ) {
            count++;
          }
        });
        return count;
      },

      getApprovedDiffCount: notebookId => {
        const state = get();
        let count = 0;
        state.pendingDiffs.forEach(diff => {
          if (
            (!notebookId || diff.notebookId === notebookId) &&
            (diff.approved === true ||
              diff.userDecision === 'approved' ||
              diff.userDecision === 'run')
          ) {
            count++;
          }
        });
        return count;
      },

      getRejectedDiffCount: notebookId => {
        const state = get();
        let count = 0;
        state.pendingDiffs.forEach(diff => {
          if (
            (!notebookId || diff.notebookId === notebookId) &&
            (diff.approved === false || diff.userDecision === 'rejected')
          ) {
            count++;
          }
        });
        return count;
      },

      getApprovalStatus: notebookId => {
        const state = get();
        let pending = 0;
        let approved = 0;
        let rejected = 0;

        state.pendingDiffs.forEach(diff => {
          if (!notebookId || diff.notebookId === notebookId) {
            if (
              diff.approved === true ||
              diff.userDecision === 'approved' ||
              diff.userDecision === 'run'
            ) {
              approved++;
            } else if (
              diff.approved === false ||
              diff.userDecision === 'rejected'
            ) {
              rejected++;
            } else {
              pending++;
            }
          }
        });

        const total = pending + approved + rejected;
        return {
          pending,
          approved,
          rejected,
          allResolved: total > 0 && pending === 0
        };
      },

      getDiffsForNotebook: notebookId => {
        const state = get();
        const diffs: IPendingDiff[] = [];
        state.pendingDiffs.forEach(diff => {
          if (!notebookId || diff.notebookId === notebookId) {
            diffs.push(diff);
          }
        });
        return diffs;
      },

      getCellDiff: cellId => {
        return get().pendingDiffs.get(cellId);
      }
    })),
    { name: 'DiffStore', serialize: devtoolsSerialize }
  )
);

// Debug utility
(window as any).getDiffStoreUpdateCount = () => diffUpdateCount;

// ═══════════════════════════════════════════════════════════════
// SELECTORS (for optimized React re-renders)
// ═══════════════════════════════════════════════════════════════

export const selectPendingDiffs = (state: IDiffStore) => state.pendingDiffs;
export const selectNotebookId = (state: IDiffStore) => state.notebookId;
export const selectDiffCount = (state: IDiffStore) => state.pendingDiffs.size;
export const selectIsRunAllLoading = (state: IDiffStore) =>
  state.isRunAllLoading;
export const selectIsRejectAllLoading = (state: IDiffStore) =>
  state.isRejectAllLoading;
export const selectIsApproveAllLoading = (state: IDiffStore) =>
  state.isApproveAllLoading;
export const selectIsAnyActionLoading = (state: IDiffStore) =>
  state.isRunAllLoading ||
  state.isRejectAllLoading ||
  state.isApproveAllLoading;

// ═══════════════════════════════════════════════════════════════
// REACT HOOKS FOR SUBSCRIBING TO DIFF CHANGES
// ═══════════════════════════════════════════════════════════════

/**
 * Hook to subscribe to changes for a specific cell's diff state.
 * @param cellId - The cell ID to monitor
 * @param callback - Function called when the cell's diff state changes
 */
export function useCellDiffChange(
  cellId: string,
  callback: (change: IDiffStateChange | null) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const unsubscribe = useDiffStore.subscribe(
      state => state.pendingDiffs.get(cellId),
      (diff, prevDiff) => {
        if (diff !== prevDiff) {
          callbackRef.current(
            diff
              ? {
                  cellId,
                  approved: diff.approved,
                  notebookId: diff.notebookId
                }
              : null
          );
        }
      }
    );
    return unsubscribe;
  }, [cellId]);
}

/**
 * Hook to subscribe to approval status changes.
 * @param notebookId - Optional notebook ID to filter by
 * @param callback - Function called when approval status changes
 */
export function useApprovalStatusChange(
  notebookId: string | null | undefined,
  callback: (status: IApprovalStatus) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const unsubscribe = useDiffStore.subscribe(
      state => state.getApprovalStatus(notebookId),
      (status, prevStatus) => {
        if (JSON.stringify(status) !== JSON.stringify(prevStatus)) {
          callbackRef.current(status);
        }
      }
    );
    return unsubscribe;
  }, [notebookId]);
}

/**
 * Hook to subscribe to "all diffs resolved" state changes.
 * @param notebookId - Optional notebook ID to filter by
 * @param callback - Function called when resolution state changes
 */
export function useAllDiffsResolved(
  notebookId: string | null | undefined,
  callback: (resolved: boolean, notebookId: string | null) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const unsubscribe = useDiffStore.subscribe(
      state => ({
        resolved: state.getAllDiffsResolved(notebookId),
        nbId: state.notebookId
      }),
      (current, prev) => {
        if (current.resolved !== prev?.resolved) {
          callbackRef.current(current.resolved, current.nbId);
        }
      }
    );
    return unsubscribe;
  }, [notebookId]);
}

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to diff state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToDiffChanges(
  callback: (
    pendingDiffs: Map<string, IPendingDiff>,
    notebookId: string | null
  ) => void
): () => void {
  return useDiffStore.subscribe(
    state => ({ diffs: state.pendingDiffs, notebookId: state.notebookId }),
    ({ diffs, notebookId }) => callback(diffs, notebookId)
  );
}

/**
 * Subscribe to approval status changes from non-React code.
 */
export function subscribeToApprovalStatus(
  notebookId: string | null | undefined,
  callback: (status: IApprovalStatus) => void
): () => void {
  return useDiffStore.subscribe(
    state => state.getApprovalStatus(notebookId),
    (status, prevStatus) => {
      if (JSON.stringify(status) !== JSON.stringify(prevStatus)) {
        callback(status);
      }
    }
  );
}

/**
 * Subscribe to "all diffs resolved" changes from non-React code.
 * Calls callback when the resolved state changes.
 */
export function subscribeToAllDiffsResolved(
  notebookId: string | null | undefined,
  callback: (resolved: boolean, notebookId: string | null) => void
): () => void {
  return useDiffStore.subscribe(
    state => ({
      resolved: state.getAllDiffsResolved(notebookId),
      nbId: state.notebookId
    }),
    (current, prev) => {
      if (current.resolved !== prev?.resolved) {
        callback(current.resolved, current.nbId);
      }
    }
  );
}

/**
 * Subscribe to changes for a specific cell's diff state from non-React code.
 */
export function subscribeToCellDiffChange(
  cellId: string,
  callback: (change: IDiffStateChange | null) => void
): () => void {
  return useDiffStore.subscribe(
    state => state.pendingDiffs.get(cellId),
    (diff, prevDiff) => {
      if (diff !== prevDiff) {
        callback(
          diff
            ? {
                cellId,
                approved: diff.approved,
                notebookId: diff.notebookId
              }
            : null
        );
      }
    }
  );
}

// ═══════════════════════════════════════════════════════════════
// CONVENIENCE ACCESSORS (for non-React code)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the current state directly (for non-React code).
 * Equivalent to DiffStateService.getCurrentState()
 */
export function getDiffState() {
  return useDiffStore.getState();
}

/**
 * Alias for setNotebookId for backwards compatibility.
 */
export function setNotebookPath(notebookId: string | null): void {
  useDiffStore.getState().setNotebookId(notebookId);
}
