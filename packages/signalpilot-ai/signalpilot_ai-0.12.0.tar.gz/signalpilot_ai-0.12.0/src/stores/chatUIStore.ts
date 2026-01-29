/**
 * ChatUIStore
 *
 * Zustand store for managing chat UI visibility states.
 * This store replaces direct DOM manipulation (classList, style.display)
 * with declarative state management.
 *
 * Manages:
 * - Panel visibility (new chat display, history widget)
 * - Loading states
 * - Update banner visibility
 * - Scroll state
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Loading overlay state
 */
export interface ILoadingOverlayState {
  isVisible: boolean;
  text: string;
}

/**
 * Chat UI state
 */
export interface IChatUIState {
  // Panel visibility
  showNewChatDisplay: boolean;
  showHistoryWidget: boolean;

  // Loading states
  chatHistoryLoading: boolean;
  loadingOverlay: ILoadingOverlayState;
  showLauncherWelcomeLoader: boolean;

  // Update banner
  showUpdateBanner: boolean;
  updateBannerDismissed: boolean;
}

/**
 * Chat UI actions
 */
export interface IChatUIActions {
  // Panel visibility actions
  setShowNewChatDisplay: (show: boolean) => void;
  setShowHistoryWidget: (show: boolean) => void;
  showNewChatDisplayIfEmpty: (messageCount: number) => void;

  // Display switching (mutual exclusion)
  // These replace chatWidget.showNewChatDisplay() and chatWidget.showHistoryWidget()
  switchToNewChatDisplay: () => void;
  switchToHistoryWidget: () => void;

  // Loading actions
  setChatHistoryLoading: (loading: boolean) => void;
  showLoadingOverlay: (text?: string) => void;
  hideLoadingOverlay: () => void;
  updateLoadingText: (text: string) => void;
  setShowLauncherWelcomeLoader: (show: boolean) => void;

  // Update banner actions
  displayUpdateBanner: () => void;
  dismissUpdateBanner: () => void;

  // Reset
  reset: () => void;
}

type IChatUIStore = IChatUIState & IChatUIActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IChatUIState = {
  showNewChatDisplay: true,
  showHistoryWidget: false,
  chatHistoryLoading: false,
  loadingOverlay: {
    isVisible: false,
    text: ''
  },
  showLauncherWelcomeLoader: false,
  showUpdateBanner: false,
  updateBannerDismissed: false
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatUIStore = create<IChatUIStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Panel Visibility Actions
      // ─────────────────────────────────────────────────────────────

      setShowNewChatDisplay: (show: boolean) => {
        set({ showNewChatDisplay: show }, false, 'setShowNewChatDisplay');
      },

      setShowHistoryWidget: (show: boolean) => {
        set({ showHistoryWidget: show }, false, 'setShowHistoryWidget');
      },

      showNewChatDisplayIfEmpty: (messageCount: number) => {
        if (messageCount === 0) {
          set(
            {
              showNewChatDisplay: true,
              showHistoryWidget: false
            },
            false,
            'showNewChatDisplayIfEmpty'
          );
        }
      },

      // Mutual exclusion - only one panel visible at a time
      switchToNewChatDisplay: () => {
        set(
          {
            showNewChatDisplay: true,
            showHistoryWidget: false
          },
          false,
          'switchToNewChatDisplay'
        );
      },

      switchToHistoryWidget: () => {
        set(
          {
            showNewChatDisplay: false,
            showHistoryWidget: true
          },
          false,
          'switchToHistoryWidget'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Loading Actions
      // ─────────────────────────────────────────────────────────────

      setChatHistoryLoading: (loading: boolean) => {
        set({ chatHistoryLoading: loading }, false, 'setChatHistoryLoading');
      },

      showLoadingOverlay: (text: string = 'Loading...') => {
        set(
          {
            loadingOverlay: {
              isVisible: true,
              text
            }
          },
          false,
          'showLoadingOverlay'
        );
      },

      hideLoadingOverlay: () => {
        set(
          {
            loadingOverlay: {
              isVisible: false,
              text: ''
            }
          },
          false,
          'hideLoadingOverlay'
        );
      },

      updateLoadingText: (text: string) => {
        set(
          state => ({
            loadingOverlay: {
              ...state.loadingOverlay,
              text
            }
          }),
          false,
          'updateLoadingText'
        );
      },

      setShowLauncherWelcomeLoader: (show: boolean) => {
        set(
          { showLauncherWelcomeLoader: show },
          false,
          'setShowLauncherWelcomeLoader'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Update Banner Actions
      // ─────────────────────────────────────────────────────────────

      displayUpdateBanner: () => {
        const { updateBannerDismissed } = get();
        if (!updateBannerDismissed) {
          set({ showUpdateBanner: true }, false, 'displayUpdateBanner');
        }
      },

      dismissUpdateBanner: () => {
        set(
          {
            showUpdateBanner: false,
            updateBannerDismissed: true
          },
          false,
          'dismissUpdateBanner'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Reset
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set({ ...initialState }, false, 'reset');
      }
    })),
    { name: 'ChatUIStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectShowNewChatDisplay = (state: IChatUIStore) =>
  state.showNewChatDisplay;
export const selectShowHistoryWidget = (state: IChatUIStore) =>
  state.showHistoryWidget;
export const selectChatHistoryLoading = (state: IChatUIStore) =>
  state.chatHistoryLoading;
export const selectLoadingOverlay = (state: IChatUIStore) =>
  state.loadingOverlay;
export const selectShowLauncherWelcomeLoader = (state: IChatUIStore) =>
  state.showLauncherWelcomeLoader;
export const selectShowUpdateBanner = (state: IChatUIStore) =>
  state.showUpdateBanner;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getChatUIState = () => useChatUIStore.getState();

/**
 * Subscribe to visibility changes
 */
export const subscribeToNewChatDisplay = (
  callback: (show: boolean) => void
) => {
  return useChatUIStore.subscribe(state => state.showNewChatDisplay, callback);
};

/**
 * Subscribe to history widget visibility
 */
export const subscribeToHistoryWidget = (callback: (show: boolean) => void) => {
  return useChatUIStore.subscribe(state => state.showHistoryWidget, callback);
};

/**
 * Subscribe to loading state
 */
export const subscribeToLoading = (callback: (loading: boolean) => void) => {
  return useChatUIStore.subscribe(state => state.chatHistoryLoading, callback);
};
