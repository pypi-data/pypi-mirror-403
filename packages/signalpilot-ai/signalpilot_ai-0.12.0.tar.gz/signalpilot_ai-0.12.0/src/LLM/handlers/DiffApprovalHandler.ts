/**
 * DiffApprovalHandler - Handles diff approval workflow during LLM loop
 *
 * This encapsulates all diff approval logic, including:
 * - Checking for pending diffs
 * - Auto-approval when enabled
 * - Manual approval workflow
 * - Recording approval results
 */

import { NotebookDiffManager } from '../../Notebook/NotebookDiffManager';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { useAppStore } from '../../stores/appStore';
import {
  useServicesStore,
  getNotebookTools,
  getDiffNavigationWidgetSafe
} from '../../stores/servicesStore';
import { useDiffStore } from '../../stores/diffStore';
import { useLLMStateStore } from '../../stores/llmStateStore';
import { IDiffApprovalResult } from '../LLMTypes';

// ═══════════════════════════════════════════════════════════════
// MAIN CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * Handler for diff approval workflow
 */
export class DiffApprovalHandler {
  private diffManager: NotebookDiffManager | null;
  private messageComponent: ChatMessages;
  private chatHistory: HTMLDivElement;

  constructor(
    diffManager: NotebookDiffManager | null,
    messageComponent: ChatMessages,
    chatHistory: HTMLDivElement
  ) {
    this.diffManager = diffManager;
    this.messageComponent = messageComponent;
    this.chatHistory = chatHistory;
  }

  // ═══════════════════════════════════════════════════════════════
  // MAIN ENTRY POINT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Handle pending diffs before continuing the LLM loop
   * Returns true if approved (should continue), false if rejected
   */
  async handlePendingDiffs(
    notebookId: string | null,
    isRunContext: boolean = true
  ): Promise<boolean> {
    if (!this.diffManager || !this.diffManager.hasPendingDiffs()) {
      return true;
    }

    console.log('[DiffApprovalHandler] Handling pending diffs');

    // Show diffs in UI
    this.showPendingDiffsInUI(notebookId, isRunContext);

    // Check if auto-run is enabled
    if (useAppStore.getState().autoRun) {
      return await this.handleAutoApproval();
    }

    // Manual approval
    return await this.handleManualApproval(isRunContext, notebookId);
  }

  // ═══════════════════════════════════════════════════════════════
  // AUTO APPROVAL
  // ═══════════════════════════════════════════════════════════════

  /**
   * Hide diff UI components
   */
  hideDiffUI(): void {
    // Use store directly instead of widget chain
    useLLMStateStore.getState().hidePendingDiffs();
  }

  // ═══════════════════════════════════════════════════════════════
  // MANUAL APPROVAL
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if there are pending diffs
   */
  hasPendingDiffs(): boolean {
    return this.diffManager?.hasPendingDiffs() || false;
  }

  // ═══════════════════════════════════════════════════════════════
  // UI MANAGEMENT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Get the number of pending diffs
   */
  getPendingDiffCount(): number {
    return this.diffManager?.getPendingDiffCount() || 0;
  }

  /**
   * Clear pending diffs
   */
  clearPendingDiffs(notebookId: string | null): void {
    useDiffStore.getState().clearDiffs(notebookId);
  }

  // ═══════════════════════════════════════════════════════════════
  // RESULT RECORDING
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check for approval decisions that should stop the LLM loop
   */
  checkForApprovalDecisions(): boolean {
    for (const diff of useDiffStore.getState().pendingDiffs.values()) {
      if (
        diff.userDecision === 'approved' ||
        diff.userDecision === 'rejected' ||
        diff.userDecision === 'run'
      ) {
        return true;
      }
    }
    return false;
  }

  // ═══════════════════════════════════════════════════════════════
  // UTILITY METHODS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Get detailed approval result
   */
  getApprovalResult(): IDiffApprovalResult {
    let approved = true;
    let rejected = false;
    let partial = false;

    for (const diff of useDiffStore.getState().pendingDiffs.values()) {
      if (diff.userDecision === 'rejected') {
        rejected = true;
        approved = false;
      } else if (diff.userDecision === 'approved') {
        partial = true;
      }
    }

    return { approved, rejected, partial };
  }

  /**
   * Handle auto-approval of diffs when auto-run is enabled
   */
  private async handleAutoApproval(): Promise<boolean> {
    const pendingDiffs = useDiffStore.getState().pendingDiffs;
    const diffCount = pendingDiffs.size;

    this.messageComponent.addSystemMessage(
      `Auto-approving ${diffCount} changes (auto-run is enabled).`
    );

    // Run all diffs
    for (const diff of pendingDiffs.values()) {
      console.log('[DiffApprovalHandler] Auto-approving diff:', diff.cellId);
      try {
        await useServicesStore
          .getState()
          .notebookDiffManager?.diffApprovalDialog.runCell(diff.cellId);
      } catch (error) {
        console.error(
          '[DiffApprovalHandler] Error running cell in auto-approve mode:',
          diff.cellId,
          error
        );
      }
    }

    // Record results
    return this.recordDiffResults();
  }

  /**
   * Handle manual approval of diffs
   */
  private async handleManualApproval(
    isRunContext: boolean,
    notebookId: string | null
  ): Promise<boolean> {
    if (!this.diffManager) return true;

    // Start the diff approval process
    this.diffManager.startDiffApprovalProcess(
      this.chatHistory,
      true,
      isRunContext,
      notebookId || undefined
    );

    // Wait for user to complete approval
    await this.diffManager.waitForDiffProcessingComplete();

    // Record and return results
    return this.recordDiffResults();
  }

  /**
   * Show pending diffs in UI components
   */
  private showPendingDiffsInUI(
    notebookId: string | null,
    isRunContext: boolean
  ): void {
    // Show in LLM state display using store directly
    useLLMStateStore.getState().showPendingDiffs(notebookId, isRunContext);

    // Show in DiffNavigationWidget for synchronized display
    // Note: DiffNavigationWidget still needs widget reference as it's a Lumino widget
    // that manages its own DOM. The diff data comes from useDiffStore which it subscribes to.
    const diffNavigationWidget = getDiffNavigationWidgetSafe();
    if (diffNavigationWidget) {
      diffNavigationWidget.showPendingDiffs(notebookId, isRunContext);
    }
  }

  /**
   * Record diff results as messages and return approval status
   */
  private recordDiffResults(): boolean {
    let allApproved = true;
    const hidden = true;

    for (const diff of useDiffStore.getState().pendingDiffs.values()) {
      // Handle remove diffs differently - no "run" concept
      if (diff.type === 'remove') {
        if (diff.userDecision === 'approved' || diff.userDecision === 'run') {
          this.messageComponent.addUserMessage(
            `${diff.cellId} was successfully removed.`,
            hidden
          );
        } else if (diff.userDecision === 'rejected') {
          this.messageComponent.addUserMessage(
            `${diff.cellId} removal was rejected by the user.`,
            hidden
          );
          allApproved = false;
        }
        continue;
      }

      // Handle add/edit diffs
      if (diff.userDecision === 'run' && diff.runResult) {
        const { cell } = getNotebookTools()?.findCellByAnyId(diff.cellId) || {};

        this.messageComponent.addUserMessage(
          `${diff.cellId} was approved and run.${cell?.model.type === 'code' ? ` Result: ${JSON.stringify(diff.runResult)}` : ''}`,
          hidden
        );
      } else if (diff.userDecision === 'rejected') {
        this.messageComponent.addUserMessage(
          `${diff.cellId} was rejected.`,
          hidden
        );
        allApproved = false;
      } else if (diff.userDecision === 'approved') {
        this.messageComponent.addUserMessage(
          `${diff.cellId} was approved but not run.`,
          hidden
        );
        allApproved = false;
      }
    }

    return allApproved;
  }
}
