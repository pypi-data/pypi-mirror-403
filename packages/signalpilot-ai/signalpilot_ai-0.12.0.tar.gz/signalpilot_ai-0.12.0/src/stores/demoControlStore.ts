/**
 * Demo Control Store
 *
 * Manages the state for the demo control panel.
 * Used to show/hide the demo controls and handle callbacks.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IDemoControlState {
  /** Whether the demo control panel is visible */
  isVisible: boolean;
  /** Whether the demo has finished */
  isDemoFinished: boolean;
  /** Whether the skip/results button is visible */
  showSkipButton: boolean;
  /** Callback for "Try it yourself" button */
  onTryIt: (() => void) | null;
  /** Callback for "Results" button */
  onSkip: (() => void) | null;
}

interface IDemoControlActions {
  /** Show the demo control panel with callbacks */
  show: (onTryIt: () => void, onSkip: () => void) => void;
  /** Hide the demo control panel */
  hide: () => void;
  /** Mark demo as finished (changes button text to "Login to Chat") */
  markDemoFinished: () => void;
  /** Hide the skip button */
  hideSkipButton: () => void;
  /** Set skip button visibility */
  setSkipButtonVisible: (visible: boolean) => void;
  /** Reset all state */
  reset: () => void;
}

type IDemoControlStore = IDemoControlState & IDemoControlActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDemoControlStore = create<IDemoControlStore>()(
  devtools(
    set => ({
      // Initial state
      isVisible: false,
      isDemoFinished: false,
      showSkipButton: true,
      onTryIt: null,
      onSkip: null,

      // Actions
      show: (onTryIt, onSkip) => {
        console.log('[DemoControlStore] Showing demo control panel');
        set({
          isVisible: true,
          isDemoFinished: false,
          showSkipButton: true,
          onTryIt,
          onSkip
        });
      },

      hide: () => {
        console.log('[DemoControlStore] Hiding demo control panel');
        set({
          isVisible: false,
          onTryIt: null,
          onSkip: null
        });
      },

      markDemoFinished: () => {
        console.log('[DemoControlStore] Marking demo as finished');
        set({
          isDemoFinished: true,
          showSkipButton: false
        });
      },

      hideSkipButton: () => {
        set({ showSkipButton: false });
      },

      setSkipButtonVisible: (visible: boolean) => {
        set({ showSkipButton: visible });
      },

      reset: () => {
        set({
          isVisible: false,
          isDemoFinished: false,
          showSkipButton: true,
          onTryIt: null,
          onSkip: null
        });
      }
    }),
    { name: 'DemoControlStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsVisible = (state: IDemoControlStore) => state.isVisible;
export const selectIsDemoFinished = (state: IDemoControlStore) =>
  state.isDemoFinished;
export const selectShowSkipButton = (state: IDemoControlStore) =>
  state.showSkipButton;

// ═══════════════════════════════════════════════════════════════
// NON-REACT HELPERS
// ═══════════════════════════════════════════════════════════════

/**
 * Show demo control panel (for non-React code)
 */
export function showDemoControls(
  onTryIt: () => void,
  onSkip: () => void
): void {
  useDemoControlStore.getState().show(onTryIt, onSkip);
}

/**
 * Hide demo control panel (for non-React code)
 */
export function hideDemoControls(completely: boolean = false): void {
  if (completely) {
    useDemoControlStore.getState().hide();
  } else {
    useDemoControlStore.getState().hideSkipButton();
  }
}

/**
 * Mark demo as finished (for non-React code)
 */
export function markDemoFinished(): void {
  useDemoControlStore.getState().markDemoFinished();
}

/**
 * Check if demo is finished (for non-React code)
 */
export function getDemoFinished(): boolean {
  return useDemoControlStore.getState().isDemoFinished;
}
