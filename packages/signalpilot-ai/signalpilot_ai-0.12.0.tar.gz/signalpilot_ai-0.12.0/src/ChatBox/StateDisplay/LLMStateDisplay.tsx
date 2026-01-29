import * as React from 'react';
import { Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/ui-components';
import { LLMStateContent } from './LLMStateContent';
import { LLMDisplayState } from './types';
import {
  subscribeToAllDiffsResolved,
  subscribeToDiffChanges,
  useDiffStore
} from '@/stores/diffStore';
import { useLLMStateStore } from '@/stores/llmStateStore';

/**
 * Component for displaying LLM processing state above the chat input.
 *
 * This class now delegates to the Zustand store (useLLMStateStore) for state management.
 * The class interface is maintained for backwards compatibility with existing code.
 *
 * @deprecated Use useLLMStateStore actions directly or LLMStateDisplayComponent for new code.
 */
export class LLMStateDisplay extends ReactWidget {
  private unsubscribes: (() => void)[] = [];

  constructor() {
    super();
    this.addClass('sage-ai-llm-state-widget');
    this.addClass('hidden');
    this.setupDiffStateSubscriptions();
    this.setupStoreSubscription();
  }

  /**
   * Clean up subscriptions
   */
  public dispose(): void {
    this.unsubscribes.forEach(unsub => unsub());
    this.unsubscribes = [];
    super.dispose();
  }

  /**
   * Render the React component - now uses store mode
   */
  render(): JSX.Element {
    return (
      <LLMStateContent
        useStore={true}
        isVisible={true}
        state={LLMDisplayState.IDLE}
        text=""
      />
    );
  }

  /**
   * Show the LLM state in generating mode
   * @param text The status text to display
   * @param waitingForUser
   */
  public show(text: string = 'Generating...', waitingForUser?: boolean): void {
    useLLMStateStore.getState().show(text, waitingForUser);
  }

  /**
   * Show the LLM state in using tool mode with approval buttons
   * @param onRunClick Optional callback for run action (for notebook-run_cell tool)
   * @param onRejectClick Optional callback for reject action (for notebook-run_cell tool)
   */
  public showRunCellTool(
    onRunClick?: () => void,
    onRejectClick?: () => void
  ): void {
    useLLMStateStore.getState().showRunCellTool(onRunClick, onRejectClick);
  }

  /**
   * Show the LLM state in using tool mode with approval buttons
   * @param onRunClick Optional callback for run action
   * @param onRejectClick Optional callback for reject action
   */
  public showRunTerminalCommandTool(
    onRunClick?: () => void,
    onRejectClick?: () => void
  ): void {
    useLLMStateStore
      .getState()
      .showRunTerminalCommandTool(onRunClick, onRejectClick);
  }

  /**
   * Show the LLM state in using tool mode
   * @param toolName The name of the tool being used
   * @param text Optional custom status text
   */
  public showTool(toolName: string, text?: string): void {
    useLLMStateStore.getState().showTool(toolName, text);
  }

  /**
   * Show the diff state with pending diffs using diffStore
   * @param notebookId Optional ID to filter diffs for a specific notebook
   * @param isRunContext
   */
  public showDiffsWithManager(
    notebookId?: string,
    isRunContext?: boolean
  ): void {
    try {
      // Get diffs from the Zustand store
      const { pendingDiffs } = useDiffStore.getState();
      const diffs = Array.from(pendingDiffs.values()).filter(
        diff => !notebookId || diff.notebookId === notebookId
      );

      if (diffs.length === 0) {
        this.hide();
        return;
      }

      useLLMStateStore.getState().showDiffs(diffs, isRunContext);
    } catch (error) {
      console.warn('Could not show diffs with manager:', error);
      this.hide();
    }
  }

  /**
   * Hide the LLM state display and set to idle
   */
  public hide(): void {
    useLLMStateStore.getState().hide();
  }

  /**
   * Public method to show pending diffs
   * @param notebookId Optional ID to filter diffs for a specific notebook
   */
  public showPendingDiffs(
    notebookId?: string | null,
    isRunContext?: boolean
  ): void {
    this.showDiffsWithManager(notebookId || undefined, isRunContext);
  }

  /**
   * Public method to show run kernel button
   */
  public showRunKernelButton(): void {
    useLLMStateStore.getState().showRunKernelButton();
  }

  /**
   * Public method to hide pending diffs
   */
  public hidePendingDiffs(): void {
    this.hide();
  }

  /**
   * Check if currently in diff state
   */
  public isDiffState(): boolean {
    return useLLMStateStore.getState().state === LLMDisplayState.DIFF;
  }

  /**
   * Check if currently in using tool state
   */
  public isUsingToolState(): boolean {
    return useLLMStateStore.getState().state === LLMDisplayState.USING_TOOL;
  }

  /**
   * Get the widget for adding to layout (for backwards compatibility)
   */
  public getWidget(): Widget {
    return this;
  }

  /**
   * Set up subscription to sync hidden class with store state
   */
  private setupStoreSubscription(): void {
    const unsubscribe = useLLMStateStore.subscribe(
      state => ({
        isVisible: state.isVisible,
        displayState: state.state,
        diffs: state.diffs
      }),
      ({ isVisible, displayState, diffs }) => {
        const shouldHide =
          !isVisible ||
          displayState === LLMDisplayState.IDLE ||
          (displayState === LLMDisplayState.DIFF &&
            (!diffs || diffs.length === 0));

        if (shouldHide) {
          this.addClass('hidden');
        } else {
          this.removeClass('hidden');
        }
        this.update();
      }
    );
    this.unsubscribes.push(unsubscribe);
  }

  /**
   * Set up subscriptions for diff state changes using Zustand
   */
  private setupDiffStateSubscriptions(): void {
    // Subscribe to diff state changes to auto-update the display
    const unsubscribeDiff = subscribeToDiffChanges(
      (pendingDiffs, notebookId) => {
        const storeState = useLLMStateStore.getState();
        // If we're in diff mode and diffs change, update the store
        if (storeState.state === LLMDisplayState.DIFF) {
          const diffs = Array.from(pendingDiffs.values());
          useLLMStateStore.getState().updateDiffs(diffs);
        }
      }
    );
    this.unsubscribes.push(unsubscribeDiff);

    // Subscribe to allDiffsResolved changes to automatically hide when complete
    const unsubscribeResolved = subscribeToAllDiffsResolved(
      undefined,
      (resolved, notebookId) => {
        const { pendingDiffs } = useDiffStore.getState();
        const hasAnyDiffs = pendingDiffs.size > 0;
        const storeState = useLLMStateStore.getState();

        // If all diffs are resolved and no pending diffs remain, hide the display
        if (!hasAnyDiffs && storeState.state === LLMDisplayState.DIFF) {
          this.hide();
        }
      }
    );
    this.unsubscribes.push(unsubscribeResolved);
  }
}
