// src/stores/llmStateStore.ts
// PURPOSE: LLM State Display - manages the LLM processing state shown above chat input
// Replaces the ReactWidget-based LLMStateDisplay with a pure Zustand store

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { IPendingDiff } from '../types';
import { useDiffStore } from './diffStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Enum for LLM display states
 */
export enum LLMDisplayState {
  IDLE = 'idle',
  GENERATING = 'generating',
  USING_TOOL = 'using_tool',
  DIFF = 'diff',
  RUN_KERNEL = 'run_kernel'
}

/**
 * Interface for the LLM state
 */
export interface ILLMState {
  isVisible: boolean;
  state: LLMDisplayState;
  text: string;
  toolName?: string;
  diffs?: IPendingDiff[];
  waitingForUser?: boolean;
  isRunContext?: boolean;
  onRunClick?: () => void;
  onRejectClick?: () => void;
}

interface ILLMStateActions {
  /**
   * Show the LLM state in generating mode
   */
  show: (text?: string, waitingForUser?: boolean) => void;

  /**
   * Show the LLM state in using tool mode with run/reject for notebook-run_cell
   */
  showRunCellTool: (
    onRunClick?: () => void,
    onRejectClick?: () => void
  ) => void;

  /**
   * Show the LLM state in using tool mode with run/reject for terminal-execute_command
   */
  showRunTerminalCommandTool: (
    onRunClick?: () => void,
    onRejectClick?: () => void
  ) => void;

  /**
   * Show the LLM state in using tool mode
   */
  showTool: (toolName: string, text?: string) => void;

  /**
   * Show the diff state with pending diffs
   */
  showDiffs: (diffs: IPendingDiff[], isRunContext?: boolean) => void;

  /**
   * Show pending diffs from the diff store
   * @param notebookId Optional ID to filter diffs for a specific notebook
   * @param isRunContext Whether this is in a run context
   */
  showPendingDiffs: (
    notebookId?: string | null,
    isRunContext?: boolean
  ) => void;

  /**
   * Hide pending diffs (alias for hide)
   */
  hidePendingDiffs: () => void;

  /**
   * Check if currently in diff state
   */
  isDiffState: () => boolean;

  /**
   * Check if currently in using tool state
   */
  isUsingToolState: () => boolean;

  /**
   * Update diffs while in diff state
   */
  updateDiffs: (diffs: IPendingDiff[]) => void;

  /**
   * Show the run kernel button
   */
  showRunKernelButton: () => void;

  /**
   * Hide the LLM state display and set to idle
   */
  hide: () => void;

  /**
   * Reset callbacks (for cleanup)
   */
  clearCallbacks: () => void;
}

type ILLMStateStore = ILLMState & ILLMStateActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useLLMStateStore = create<ILLMStateStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      isVisible: false,
      state: LLMDisplayState.IDLE,
      text: '',
      toolName: undefined,
      diffs: undefined,
      waitingForUser: false,
      isRunContext: false,
      onRunClick: undefined,
      onRejectClick: undefined,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      show: (text = 'Generating...', waitingForUser?: boolean) =>
        set({
          isVisible: true,
          state: LLMDisplayState.GENERATING,
          text,
          waitingForUser,
          toolName: undefined,
          diffs: undefined,
          onRunClick: undefined,
          onRejectClick: undefined
        }),

      showRunCellTool: (onRunClick?: () => void, onRejectClick?: () => void) =>
        set({
          isVisible: true,
          state: LLMDisplayState.USING_TOOL,
          text: '',
          toolName: 'notebook-run_cell',
          onRunClick,
          onRejectClick,
          diffs: undefined,
          waitingForUser: false
        }),

      showRunTerminalCommandTool: (
        onRunClick?: () => void,
        onRejectClick?: () => void
      ) =>
        set({
          isVisible: true,
          state: LLMDisplayState.USING_TOOL,
          text: '',
          toolName: 'terminal-execute_command',
          onRunClick,
          onRejectClick,
          diffs: undefined,
          waitingForUser: false
        }),

      showTool: (toolName: string, text?: string) =>
        set({
          isVisible: true,
          state: LLMDisplayState.USING_TOOL,
          text: text || '',
          toolName,
          onRunClick: undefined,
          onRejectClick: undefined,
          diffs: undefined,
          waitingForUser: false
        }),

      showDiffs: (diffs: IPendingDiff[], isRunContext?: boolean) => {
        if (diffs.length === 0) {
          // If no diffs, hide
          set({
            isVisible: false,
            state: LLMDisplayState.IDLE,
            text: '',
            diffs: undefined,
            isRunContext: false
          });
        } else {
          set({
            isVisible: true,
            state: LLMDisplayState.DIFF,
            text: '',
            diffs,
            isRunContext: isRunContext || false,
            toolName: undefined,
            onRunClick: undefined,
            onRejectClick: undefined,
            waitingForUser: false
          });
        }
      },

      showPendingDiffs: (
        notebookId?: string | null,
        isRunContext?: boolean
      ) => {
        try {
          // Get diffs from the diff store
          const { pendingDiffs } = useDiffStore.getState();
          const diffs = Array.from(pendingDiffs.values()).filter(
            diff => !notebookId || diff.notebookId === notebookId
          );

          if (diffs.length === 0) {
            get().hide();
            return;
          }

          get().showDiffs(diffs, isRunContext);
        } catch (error) {
          console.warn('[LLMStateStore] Could not show pending diffs:', error);
          get().hide();
        }
      },

      hidePendingDiffs: () => {
        get().hide();
      },

      isDiffState: () => {
        return get().state === LLMDisplayState.DIFF;
      },

      isUsingToolState: () => {
        return get().state === LLMDisplayState.USING_TOOL;
      },

      updateDiffs: (diffs: IPendingDiff[]) => {
        const { state } = get();
        if (state === LLMDisplayState.DIFF) {
          set({ diffs });
        }
      },

      showRunKernelButton: () =>
        set({
          isVisible: true,
          state: LLMDisplayState.RUN_KERNEL,
          text: '',
          toolName: undefined,
          diffs: undefined,
          onRunClick: undefined,
          onRejectClick: undefined,
          waitingForUser: false
        }),

      hide: () =>
        set({
          isVisible: false,
          state: LLMDisplayState.IDLE,
          text: '',
          waitingForUser: false,
          toolName: undefined,
          diffs: undefined,
          onRunClick: undefined,
          onRejectClick: undefined,
          isRunContext: false
        }),

      clearCallbacks: () =>
        set({
          onRunClick: undefined,
          onRejectClick: undefined
        })
    })),
    { name: 'LLMStateStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectLLMState = (state: ILLMStateStore): ILLMState => ({
  isVisible: state.isVisible,
  state: state.state,
  text: state.text,
  toolName: state.toolName,
  diffs: state.diffs,
  waitingForUser: state.waitingForUser,
  isRunContext: state.isRunContext,
  onRunClick: state.onRunClick,
  onRejectClick: state.onRejectClick
});

export const selectIsVisible = (state: ILLMStateStore) => state.isVisible;
export const selectDisplayState = (state: ILLMStateStore) => state.state;
export const selectText = (state: ILLMStateStore) => state.text;
export const selectToolName = (state: ILLMStateStore) => state.toolName;
export const selectDiffs = (state: ILLMStateStore) => state.diffs;
export const selectWaitingForUser = (state: ILLMStateStore) =>
  state.waitingForUser;
export const selectIsRunContext = (state: ILLMStateStore) => state.isRunContext;

/**
 * Check if currently in diff state
 */
export const selectIsDiffState = (state: ILLMStateStore) =>
  state.state === LLMDisplayState.DIFF;

/**
 * Check if currently in using tool state
 */
export const selectIsUsingToolState = (state: ILLMStateStore) =>
  state.state === LLMDisplayState.USING_TOOL;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript/Lumino widgets)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to LLM state visibility changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToLLMVisibility(
  callback: (isVisible: boolean) => void
): () => void {
  return useLLMStateStore.subscribe(
    state => state.isVisible,
    (isVisible, prevIsVisible) => {
      if (isVisible !== prevIsVisible) {
        callback(isVisible);
      }
    }
  );
}

/**
 * Subscribe to LLM display state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToLLMDisplayState(
  callback: (displayState: LLMDisplayState) => void
): () => void {
  return useLLMStateStore.subscribe(
    state => state.state,
    (displayState, prevDisplayState) => {
      if (displayState !== prevDisplayState) {
        callback(displayState);
      }
    }
  );
}

/**
 * Subscribe to full LLM state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToLLMState(
  callback: (state: ILLMState) => void
): () => void {
  return useLLMStateStore.subscribe(
    state => selectLLMState(state),
    (current, prev) => {
      // Only trigger if something actually changed
      if (
        current.isVisible !== prev.isVisible ||
        current.state !== prev.state ||
        current.text !== prev.text ||
        current.toolName !== prev.toolName ||
        current.diffs !== prev.diffs ||
        current.waitingForUser !== prev.waitingForUser ||
        current.isRunContext !== prev.isRunContext
      ) {
        callback(current);
      }
    }
  );
}
