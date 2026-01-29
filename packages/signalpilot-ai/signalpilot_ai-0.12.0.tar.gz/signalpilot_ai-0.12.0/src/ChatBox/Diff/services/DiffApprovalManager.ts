/**
 * DiffApprovalDialog
 *
 * Manager class for diff approval actions and callbacks.
 * UI rendering is handled by React components in DiffApproval/.
 *
 * This class:
 * - Manages callbacks from NotebookDiffManager
 * - Handles approve/reject/run actions
 * - Coordinates with Zustand stores (diffStore, chatMessagesStore)
 * - Tracks dialog open state
 */

import { IDiffApplicationResult, IPendingDiff } from '@/types';
import {
  getNotebookTools,
  getDiffNavigationWidgetSafe
} from '@/stores/servicesStore';
import { useDiffStore } from '@/stores/diffStore';
import { useLLMStateStore } from '@/stores/llmStateStore';
import { IDiffCellUI, useChatMessagesStore } from '@/stores/chatMessages';

// ===============================================================
// TYPES
// ===============================================================

/**
 * Callbacks interface for diff approval actions
 */
export interface IDiffApprovalCallbacks {
  onApprove: (trackingIds: string[]) => void;
  onReject: (trackingIds: string[]) => void;
  onApproveAll: (notebookId: string | null) => void;
  onRejectAll: (notebookId: string | null) => void;
  applyApprovedDiffs: (
    notebookId: string | null,
    trackingIds?: string[]
  ) => Promise<IDiffApplicationResult>;
  handleRejectedDiffs: (
    notebookId: string | null
  ) => Promise<IDiffApplicationResult>;
  setExecuteApprovedCells: (execute: boolean) => void;
  reapplyDiff: (diffCell: IPendingDiff) => void;
}

// ===============================================================
// MANAGER CLASS
// ===============================================================

/**
 * DiffApprovalDialog - Manages diff approval state and actions
 *
 * The UI is rendered by React components (ActiveDiffApprovalDialog).
 * This class provides the action methods and coordinates with stores.
 */
export class DiffApprovalDialog {
  /** Callbacks from NotebookDiffManager */
  public callbacks: IDiffApprovalCallbacks | null = null;

  /** Current notebook path being approved */
  private currentNotebookPath: string | null = null;

  /** Store message ID for the active diff approval */
  private currentDiffMessageId: string | null = null;

  /** Whether dialog is currently open */
  private isOpen: boolean = false;

  /** Diff cells being approved */
  private diffCells: IPendingDiff[] = [];

  /** Promise resolver for dialog completion */
  private resolvePromise:
    | ((value: { approved: boolean; runImmediately: boolean }) => void)
    | null = null;

  // ─────────────────────────────────────────────────────────────
  // Setup
  // ─────────────────────────────────────────────────────────────

  /**
   * Set callbacks for the dialog actions
   */
  public setCallbacks(callbacks: IDiffApprovalCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * Update the current notebook path
   */
  public updateNotebookPath(newPath: string): void {
    this.currentNotebookPath = newPath;
  }

  // ─────────────────────────────────────────────────────────────
  // Dialog Lifecycle
  // ─────────────────────────────────────────────────────────────

  /**
   * Show the approval dialog
   *
   * Adds a diff approval message to the store. React handles rendering.
   */
  public async showDialog(
    _parentElement: HTMLElement,
    notebookPath: string | null = null,
    _embedded: boolean = false,
    isRunContext: boolean = false
  ): Promise<{ approved: boolean; runImmediately: boolean }> {
    // Get diffs from store
    const { pendingDiffs } = useDiffStore.getState();
    const allDiffs = Array.from(pendingDiffs.values());

    // Filter for current notebook
    this.diffCells = allDiffs
      .filter(diff => !notebookPath || diff.notebookId === notebookPath)
      .map(diff => ({
        ...diff,
        displaySummary:
          diff.summary || diff.metadata?.summary || `${diff.type} cell`
      }));

    this.currentNotebookPath = notebookPath;
    this.isOpen = true;

    // Add to chat messages store (React will render)
    const store = useChatMessagesStore.getState();
    const diffCellsUI: IDiffCellUI[] = this.diffCells.map(diff => ({
      cellId: diff.cellId,
      type: diff.type,
      originalContent: diff.originalContent,
      newContent: diff.newContent,
      displaySummary: diff.displaySummary
    }));

    this.currentDiffMessageId = store.addDiffApproval(
      notebookPath || undefined,
      diffCellsUI,
      false // Not historical - active dialog
    );

    console.log(
      '[DiffApprovalDialog] Opened with ID:',
      this.currentDiffMessageId
    );

    // Show in LLM state display using store directly
    useLLMStateStore.getState().showPendingDiffs(notebookPath, isRunContext);

    // Show in diff navigation widget
    const diffNavigationWidget = getDiffNavigationWidgetSafe();
    diffNavigationWidget?.showPendingDiffs(notebookPath, isRunContext);

    // Return promise that resolves when dialog is completed
    return new Promise(resolve => {
      this.resolvePromise = resolve;
    });
  }

  /**
   * Check if dialog is currently open
   */
  public isDialogOpen(): boolean {
    return this.isOpen;
  }

  /**
   * Close the dialog and cleanup
   */
  public async close(): Promise<void> {
    console.log('[DiffApprovalDialog] Closing');
    this.isOpen = false;
    this.currentDiffMessageId = null;
  }

  /**
   * Complete the dialog when all individual cells have been decided
   * This is called from the React component when isAllDecided becomes true
   */
  public completeAllDecided(): void {
    console.log('[DiffApprovalDialog] All cells decided, completing dialog');

    // Determine if all were approved by checking the diff store
    const { pendingDiffs } = useDiffStore.getState();
    let allApproved = true;

    for (const diff of this.diffCells) {
      const storedDiff = pendingDiffs.get(diff.cellId);
      if (storedDiff && storedDiff.approved === false) {
        allApproved = false;
        break;
      }
    }

    // Mark as historical and persist to LLM history
    this.markHistorical();

    // Close the dialog
    this.isOpen = false;

    // CRITICAL: Resolve the showDialog Promise to unblock the LLM loop
    if (this.resolvePromise) {
      this.resolvePromise({ approved: allApproved, runImmediately: false });
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Cell Actions
  // ─────────────────────────────────────────────────────────────

  /**
   * Approve a single cell
   */
  public approveCell(trackingId: string): void {
    if (!this.callbacks) return;

    this.callbacks.onApprove([trackingId]);
    useDiffStore
      .getState()
      .updateDiffApproval(trackingId, true, this.currentNotebookPath);

    void this.callbacks.applyApprovedDiffs(this.currentNotebookPath, [
      trackingId
    ]);
  }

  /**
   * Reject a single cell
   */
  public rejectCell(trackingId: string): void {
    if (!this.callbacks) return;

    this.callbacks.onReject([trackingId]);
    useDiffStore
      .getState()
      .updateDiffApproval(trackingId, false, this.currentNotebookPath);

    void this.callbacks.handleRejectedDiffs(this.currentNotebookPath);
  }

  /**
   * Run a single cell (approve + execute)
   */
  public async runCell(trackingId: string): Promise<void> {
    if (!this.callbacks) return;

    // Mark as "run" in store
    useDiffStore
      .getState()
      .updateDiffToRun(trackingId, this.currentNotebookPath);
    this.callbacks.onApprove([trackingId]);

    // Apply diff
    await this.callbacks.applyApprovedDiffs(this.currentNotebookPath, [
      trackingId
    ]);

    // Execute cell
    const notebookTools = getNotebookTools();
    if (notebookTools) {
      try {
        const result = await notebookTools.run_cell({
          cell_id: trackingId,
          notebook_path: this.currentNotebookPath
        });
        useDiffStore
          .getState()
          .updateDiffResult(trackingId, result.slice(0, 5000));
      } catch (error) {
        useDiffStore.getState().updateDiffResult(trackingId, {});
        console.error('[DiffApprovalDialog] Run cell error:', error);
      }
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Bulk Actions
  // ─────────────────────────────────────────────────────────────

  /**
   * Approve all cells
   */
  public async approveAll(): Promise<void> {
    if (!this.callbacks) return;

    try {
      this.callbacks.onApproveAll(this.currentNotebookPath);

      // Update all diffs in store
      const { updateDiffApproval } = useDiffStore.getState();
      this.diffCells.forEach(diff => {
        updateDiffApproval(diff.cellId, true, this.currentNotebookPath);
      });

      // Set execute flag
      this.callbacks.setExecuteApprovedCells(true);

      // Apply diffs
      await this.callbacks.applyApprovedDiffs(this.currentNotebookPath);
    } catch (error) {
      console.error('[DiffApprovalDialog] Approve all error:', error);
    }

    // Mark as historical and close
    this.markHistorical();
    void this.close();

    // CRITICAL: Resolve the showDialog Promise to unblock the LLM loop
    if (this.resolvePromise) {
      this.resolvePromise({ approved: true, runImmediately: false });
    }
  }

  /**
   * Reject all cells
   */
  public async rejectAll(): Promise<void> {
    if (!this.callbacks) return;

    try {
      this.callbacks.onRejectAll(this.currentNotebookPath);

      // Update all diffs in store
      const { updateDiffApproval } = useDiffStore.getState();
      this.diffCells.forEach(diff => {
        updateDiffApproval(diff.cellId, false, this.currentNotebookPath);
      });

      // Handle rejections
      await this.callbacks.handleRejectedDiffs(this.currentNotebookPath);
    } catch (error) {
      console.error('[DiffApprovalDialog] Reject all error:', error);
    }

    // Mark as historical and close
    this.markHistorical();
    void this.close();

    // CRITICAL: Resolve the showDialog Promise to unblock the LLM loop
    if (this.resolvePromise) {
      this.resolvePromise({ approved: false, runImmediately: false });
    }
  }

  // ─────────────────────────────────────────────────────────────
  // Private Helpers
  // ─────────────────────────────────────────────────────────────

  /**
   * Mark the diff approval message as historical and persist to LLM history
   */
  private markHistorical(): void {
    if (this.currentDiffMessageId) {
      const store = useChatMessagesStore.getState();

      // Mark as historical in UI
      store.markDiffApprovalHistorical(this.currentDiffMessageId);
      console.log(
        '[DiffApprovalDialog] Marked as historical:',
        this.currentDiffMessageId
      );

      // Add to LLM history so it persists across page refresh
      const diffCellsForHistory = this.diffCells.map(diff => ({
        cellId: diff.cellId,
        type: diff.type,
        originalContent: diff.originalContent,
        newContent: diff.newContent,
        displaySummary: diff.displaySummary
      }));

      store.addToLlmHistory({
        role: 'diff_approval' as any,
        content: [
          {
            type: 'diff_approval',
            id: this.currentDiffMessageId,
            timestamp: new Date().toISOString(),
            notebook_path: this.currentNotebookPath,
            diff_cells: diffCellsForHistory
          }
        ]
      });

      console.log('[DiffApprovalDialog] Added to LLM history for persistence');
    }
  }
}

export default DiffApprovalDialog;
