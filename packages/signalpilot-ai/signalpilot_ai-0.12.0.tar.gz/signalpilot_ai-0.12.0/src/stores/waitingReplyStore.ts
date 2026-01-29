/**
 * WaitingReplyStore
 *
 * Zustand store for managing the waiting user reply box state.
 * Replaces direct access to WaitingUserReplyBoxManager.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Lazy import to avoid circular dependency
const getChatMessagesStore = () =>
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  require('./chatMessages').useChatMessagesStore;

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IWaitingReplyState {
  /** Whether the waiting reply box is visible */
  isVisible: boolean;
  /** List of recommended prompts to display */
  recommendedPrompts: string[];
  /** Callback when continue is clicked */
  continueCallback: (() => void) | null;
  /** Callback when a prompt is selected */
  promptCallback: ((prompt: string) => void) | null;
  /** Whether continue button has been shown in current thread */
  continueButtonShown: boolean;
}

export interface IWaitingReplyActions {
  /** Show the waiting reply box */
  show: (recommendedPrompts?: string[]) => void;
  /** Hide the waiting reply box */
  hide: () => void;
  /** Set the continue callback */
  setContinueCallback: (callback: (() => void) | null) => void;
  /** Set the prompt callback */
  setPromptCallback: (callback: ((prompt: string) => void) | null) => void;
  /** Trigger continue action */
  triggerContinue: () => void;
  /** Trigger prompt selection */
  triggerPrompt: (prompt: string) => void;
  /** Mark continue button as shown for current thread */
  markContinueButtonShown: () => void;
  /** Reset continue button shown state (for new threads) */
  resetContinueButtonShown: () => void;
  /** Reset all state */
  reset: () => void;
}

export type IWaitingReplyStore = IWaitingReplyState & IWaitingReplyActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IWaitingReplyState = {
  isVisible: false,
  recommendedPrompts: [],
  continueCallback: null,
  promptCallback: null,
  continueButtonShown: false
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useWaitingReplyStore = create<IWaitingReplyStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────

      show: (recommendedPrompts?: string[]) => {
        console.log('[WaitingReplyStore] show() called', {
          recommendedPrompts
        });
        set(
          {
            isVisible: true,
            recommendedPrompts: recommendedPrompts || ['Continue']
          },
          false,
          'show'
        );
      },

      hide: () => {
        console.log('[WaitingReplyStore] hide() called');
        set({ isVisible: false }, false, 'hide');
        // Also remove any notebook-wait_user_reply tool call messages
        try {
          getChatMessagesStore()
            .getState()
            .removeToolCallsByName('notebook-wait_user_reply');
        } catch (e) {
          // Store may not be initialized yet during startup
          console.warn('[WaitingReplyStore] Could not remove tool calls:', e);
        }
      },

      setContinueCallback: (callback: (() => void) | null) => {
        console.log('[WaitingReplyStore] setContinueCallback() called');
        set({ continueCallback: callback }, false, 'setContinueCallback');
      },

      setPromptCallback: (callback: ((prompt: string) => void) | null) => {
        console.log('[WaitingReplyStore] setPromptCallback() called');
        set({ promptCallback: callback }, false, 'setPromptCallback');
      },

      triggerContinue: () => {
        const { continueCallback } = get();
        console.log('[WaitingReplyStore] triggerContinue() called');
        if (continueCallback) {
          continueCallback();
        } else {
          console.warn('[WaitingReplyStore] No continue callback set');
        }
        set({ isVisible: false }, false, 'triggerContinue');
      },

      triggerPrompt: (prompt: string) => {
        const { promptCallback } = get();
        console.log('[WaitingReplyStore] triggerPrompt() called', { prompt });
        if (promptCallback) {
          promptCallback(prompt);
        } else {
          console.warn('[WaitingReplyStore] No prompt callback set');
        }
        set({ isVisible: false }, false, 'triggerPrompt');
      },

      markContinueButtonShown: () => {
        set({ continueButtonShown: true }, false, 'markContinueButtonShown');
      },

      resetContinueButtonShown: () => {
        set({ continueButtonShown: false }, false, 'resetContinueButtonShown');
      },

      reset: () => {
        console.log('[WaitingReplyStore] reset() called');
        set(initialState, false, 'reset');
      }
    })),
    {
      name: 'WaitingReplyStore',
      serialize: {
        replacer: (_key: string, value: unknown) => {
          // Don't serialize callbacks
          if (typeof value === 'function') {
            return '[Function]';
          }
          return value;
        }
      }
    }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsVisible = (state: IWaitingReplyStore) => state.isVisible;
export const selectRecommendedPrompts = (state: IWaitingReplyStore) =>
  state.recommendedPrompts;
export const selectContinueButtonShown = (state: IWaitingReplyStore) =>
  state.continueButtonShown;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API
// ═══════════════════════════════════════════════════════════════

/**
 * Get current waiting reply state (for non-React code)
 */
export function getWaitingReplyState(): IWaitingReplyState {
  const state = useWaitingReplyStore.getState();
  return {
    isVisible: state.isVisible,
    recommendedPrompts: state.recommendedPrompts,
    continueCallback: state.continueCallback,
    promptCallback: state.promptCallback,
    continueButtonShown: state.continueButtonShown
  };
}

/**
 * Subscribe to visibility changes
 */
export function subscribeToWaitingReplyVisibility(
  callback: (isVisible: boolean) => void
): () => void {
  return useWaitingReplyStore.subscribe(state => state.isVisible, callback);
}
