// src/stores/toolbarStore.ts
// PURPOSE: Toolbar UI state - thread banner, more options, undo state
// Manages all toolbar-related state for React components

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IToolbarState {
  // Thread banner (left sidebar)
  isBannerOpen: boolean;

  // More options popover
  isMoreOptionsOpen: boolean;
  moreOptionsAnchorRect: DOMRect | null;

  // Undo state
  canUndo: boolean;
  undoDescription: string;
}

interface IToolbarActions {
  // Banner actions
  openBanner: () => void;
  closeBanner: () => void;
  toggleBanner: () => void;

  // More options actions
  openMoreOptions: (anchorRect: DOMRect) => void;
  closeMoreOptions: () => void;
  toggleMoreOptions: (anchorRect?: DOMRect) => void;

  // Undo actions
  setUndoState: (canUndo: boolean, description: string) => void;
  clearUndoState: () => void;
}

type IToolbarStore = IToolbarState & IToolbarActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useToolbarStore = create<IToolbarStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      isBannerOpen: false,
      isMoreOptionsOpen: false,
      moreOptionsAnchorRect: null,
      canUndo: false,
      undoDescription: 'No action to undo',

      // ─────────────────────────────────────────────────────────────
      // Banner Actions
      // ─────────────────────────────────────────────────────────────
      openBanner: () => set({ isBannerOpen: true }),
      closeBanner: () => set({ isBannerOpen: false }),
      toggleBanner: () => set(state => ({ isBannerOpen: !state.isBannerOpen })),

      // ─────────────────────────────────────────────────────────────
      // More Options Actions
      // ─────────────────────────────────────────────────────────────
      openMoreOptions: (anchorRect: DOMRect) =>
        set({ isMoreOptionsOpen: true, moreOptionsAnchorRect: anchorRect }),

      closeMoreOptions: () =>
        set({ isMoreOptionsOpen: false, moreOptionsAnchorRect: null }),

      toggleMoreOptions: (anchorRect?: DOMRect) => {
        const { isMoreOptionsOpen } = get();
        if (isMoreOptionsOpen) {
          set({ isMoreOptionsOpen: false, moreOptionsAnchorRect: null });
        } else if (anchorRect) {
          set({ isMoreOptionsOpen: true, moreOptionsAnchorRect: anchorRect });
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Undo Actions
      // ─────────────────────────────────────────────────────────────
      setUndoState: (canUndo: boolean, description: string) =>
        set({ canUndo, undoDescription: description }),

      clearUndoState: () =>
        set({ canUndo: false, undoDescription: 'No action to undo' })
    })),
    { name: 'ToolbarStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsBannerOpen = (state: IToolbarStore) => state.isBannerOpen;
export const selectIsMoreOptionsOpen = (state: IToolbarStore) =>
  state.isMoreOptionsOpen;
export const selectMoreOptionsAnchorRect = (state: IToolbarStore) =>
  state.moreOptionsAnchorRect;
export const selectCanUndo = (state: IToolbarStore) => state.canUndo;
export const selectUndoDescription = (state: IToolbarStore) =>
  state.undoDescription;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript/Lumino widgets)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to banner open state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToBannerOpen(
  callback: (isOpen: boolean) => void
): () => void {
  return useToolbarStore.subscribe(
    state => state.isBannerOpen,
    (isOpen, prevIsOpen) => {
      if (isOpen !== prevIsOpen) {
        callback(isOpen);
      }
    }
  );
}

/**
 * Subscribe to undo state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToUndoState(
  callback: (canUndo: boolean, description: string) => void
): () => void {
  return useToolbarStore.subscribe(
    state => ({ canUndo: state.canUndo, description: state.undoDescription }),
    (current, prev) => {
      if (
        current.canUndo !== prev.canUndo ||
        current.description !== prev.description
      ) {
        callback(current.canUndo, current.description);
      }
    }
  );
}
