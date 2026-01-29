/**
 * Demo Overlay Store
 *
 * Manages the overlay state for demo mode.
 * React components subscribe to this store to conditionally render overlays.
 *
 * For JupyterLab elements (non-React), use the functions in /Jupyter/DemoOverlays.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IDemoOverlayState {
  /** Whether demo overlays are active */
  isActive: boolean;
  /** Whether to show spinner on send button */
  showSendSpinner: boolean;
}

interface IDemoOverlayActions {
  /** Activate all demo overlays */
  activate: () => void;
  /** Deactivate all demo overlays */
  deactivate: () => void;
  /** Set send button spinner state */
  setSendSpinner: (show: boolean) => void;
}

type IDemoOverlayStore = IDemoOverlayState & IDemoOverlayActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDemoOverlayStore = create<IDemoOverlayStore>()(
  devtools(
    set => ({
      // Initial state
      isActive: false,
      showSendSpinner: false,

      // Actions
      activate: () => {
        console.log('[DemoOverlayStore] Activating demo overlays');
        set({ isActive: true, showSendSpinner: true });
      },

      deactivate: () => {
        console.log('[DemoOverlayStore] Deactivating demo overlays');
        set({ isActive: false, showSendSpinner: false });
      },

      setSendSpinner: (show: boolean) => {
        set({ showSendSpinner: show });
      }
    }),
    { name: 'DemoOverlayStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsOverlayActive = (state: IDemoOverlayStore) =>
  state.isActive;
export const selectShowSendSpinner = (state: IDemoOverlayStore) =>
  state.showSendSpinner;

// ═══════════════════════════════════════════════════════════════
// NON-REACT HELPERS
// ═══════════════════════════════════════════════════════════════

/**
 * Activate demo overlays (for non-React code)
 */
export function activateDemoOverlays(): void {
  useDemoOverlayStore.getState().activate();
}

/**
 * Deactivate demo overlays (for non-React code)
 */
export function deactivateDemoOverlays(): void {
  useDemoOverlayStore.getState().deactivate();
}
