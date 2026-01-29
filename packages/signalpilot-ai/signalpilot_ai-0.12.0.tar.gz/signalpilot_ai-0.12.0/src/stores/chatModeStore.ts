// src/stores/chatModeStore.ts
// PURPOSE: Single source of truth for chat context (launcher vs notebook) and chat mode
// This store ensures that mode transitions are explicit and well-defined

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Special notebook ID for launcher mode - used for in-memory only chat
export const LAUNCHER_NOTEBOOK_ID = '__launcher__';

/**
 * Check if a notebook ID is the launcher notebook ID
 */
export function isLauncherNotebookId(notebookId: string | null): boolean {
  return notebookId === LAUNCHER_NOTEBOOK_ID;
}

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Chat context - where the chat is being used
 */
export type ChatContext = 'launcher' | 'notebook';

/**
 * Chat mode - how the LLM should behave
 */
export type ChatMode = 'agent' | 'ask' | 'fast' | 'welcome';

interface IChatModeState {
  // The current context (launcher or notebook)
  context: ChatContext;

  // The user-selected mode for notebook context
  notebookMode: 'agent' | 'ask' | 'fast';

  // The current notebook ID (null when in launcher)
  currentNotebookId: string | null;

  // Timestamp of last context change (for debugging/tracking)
  lastContextChangeTimestamp: number;
}

interface IChatModeActions {
  /**
   * Switch to launcher context
   * This will set the effective mode to 'welcome'
   */
  switchToLauncher: () => void;

  /**
   * Switch to notebook context
   * @param notebookId The ID of the notebook being switched to
   */
  switchToNotebook: (notebookId: string) => void;

  /**
   * Set the notebook mode (agent, ask, fast)
   * Only affects behavior when in notebook context
   */
  setNotebookMode: (mode: 'agent' | 'ask' | 'fast') => void;

  /**
   * Get the effective chat mode based on current context
   * Returns 'welcome' if in launcher, otherwise returns notebookMode
   */
  getEffectiveMode: () => ChatMode;

  /**
   * Check if currently in launcher context
   */
  isLauncherContext: () => boolean;

  /**
   * Get the current notebook ID (null if in launcher)
   */
  getCurrentNotebookId: () => string | null;
}

type IChatModeStore = IChatModeState & IChatModeActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatModeStore = create<IChatModeStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State - Start in launcher context
      // ─────────────────────────────────────────────────────────────
      context: 'launcher',
      notebookMode: 'agent',
      currentNotebookId: null,
      lastContextChangeTimestamp: Date.now(),

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      switchToLauncher: () => {
        const currentContext = get().context;
        if (currentContext !== 'launcher') {
          console.log('[ChatModeStore] Switching to LAUNCHER context');
          set({
            context: 'launcher',
            currentNotebookId: LAUNCHER_NOTEBOOK_ID,
            lastContextChangeTimestamp: Date.now()
          });
        }
      },

      switchToNotebook: (notebookId: string) => {
        const currentState = get();
        if (
          currentState.context !== 'notebook' ||
          currentState.currentNotebookId !== notebookId
        ) {
          console.log(
            `[ChatModeStore] Switching to NOTEBOOK context: ${notebookId}`
          );
          set({
            context: 'notebook',
            currentNotebookId: notebookId,
            lastContextChangeTimestamp: Date.now()
          });
        }
      },

      setNotebookMode: (mode: 'agent' | 'ask' | 'fast') => {
        const currentMode = get().notebookMode;
        if (currentMode !== mode) {
          console.log(`[ChatModeStore] Setting notebook mode to: ${mode}`);
          set({ notebookMode: mode });
        }
      },

      getEffectiveMode: (): ChatMode => {
        const state = get();
        if (state.context === 'launcher') {
          return 'welcome';
        }
        return state.notebookMode;
      },

      isLauncherContext: (): boolean => {
        return get().context === 'launcher';
      },

      getCurrentNotebookId: (): string | null => {
        return get().currentNotebookId;
      }
    })),
    { name: 'ChatModeStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS (for optimized re-renders)
// ═══════════════════════════════════════════════════════════════

export const selectContext = (state: IChatModeStore) => state.context;
export const selectNotebookMode = (state: IChatModeStore) => state.notebookMode;
export const selectCurrentNotebookId = (state: IChatModeStore) =>
  state.currentNotebookId;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to context changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToContextChange(
  callback: (context: ChatContext, notebookId: string | null) => void
): () => void {
  return useChatModeStore.subscribe(
    state => ({ context: state.context, notebookId: state.currentNotebookId }),
    ({ context, notebookId }, prev) => {
      if (context !== prev.context || notebookId !== prev.notebookId) {
        callback(context, notebookId);
      }
    }
  );
}

/**
 * Subscribe to effective mode changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToEffectiveModeChange(
  callback: (mode: ChatMode) => void
): () => void {
  let lastMode: ChatMode = useChatModeStore.getState().getEffectiveMode();

  return useChatModeStore.subscribe(state => {
    const newMode = state.getEffectiveMode();
    if (newMode !== lastMode) {
      lastMode = newMode;
      callback(newMode);
    }
  });
}
