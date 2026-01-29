/**
 * RichTextInputStore
 *
 * Zustand store for rich text input state management.
 * This store manages the logical state of the rich text input,
 * while DOM-specific operations remain in the component.
 *
 * Manages:
 * - Plain text content (synced with DOM)
 * - Focus state and focus requests
 * - Active mention contexts
 * - Text insertion requests
 *
 * Note: DOM-specific operations like selection management and
 * scroll height remain in the RichTextInput component via refs.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Text insertion request
 * Component listens for these and performs the insertion
 */
export interface ITextInsertRequest {
  id: string;
  text: string;
  timestamp: number;
}

/**
 * Rich text input state
 */
export interface IRichTextInputState {
  // Content state (synced from DOM)
  plainText: string;
  isEmpty: boolean;

  // Focus state
  isFocused: boolean;
  focusRequested: boolean;

  // Active contexts for mention formatting
  activeContexts: Map<string, IMentionContext>;

  // Pending operations (component handles these)
  pendingTextInsert: ITextInsertRequest | null;
  pendingClear: boolean;
  pendingSetText: string | null;
}

/**
 * Rich text input actions
 */
export interface IRichTextInputActions {
  // Content actions
  setPlainText: (text: string) => void;
  updateFromDOM: (text: string) => void;
  clear: () => void;
  clearCompleted: () => void;

  // Focus actions
  requestFocus: () => void;
  focusCompleted: () => void;
  setIsFocused: (focused: boolean) => void;

  // Context actions
  setActiveContexts: (contexts: Map<string, IMentionContext>) => void;
  addActiveContext: (context: IMentionContext) => void;
  removeActiveContext: (contextId: string) => void;
  clearActiveContexts: () => void;

  // Text insertion
  insertText: (text: string) => void;
  insertCompleted: () => void;

  // Set text (triggers DOM update)
  setText: (text: string) => void;
  setTextCompleted: () => void;

  // Reset
  reset: () => void;
}

type IRichTextInputStore = IRichTextInputState & IRichTextInputActions;

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IRichTextInputState = {
  plainText: '',
  isEmpty: true,
  isFocused: false,
  focusRequested: false,
  activeContexts: new Map(),
  pendingTextInsert: null,
  pendingClear: false,
  pendingSetText: null
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useRichTextInputStore = create<IRichTextInputStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Content Actions
      // ─────────────────────────────────────────────────────────────

      setPlainText: (text: string) => {
        set(
          {
            pendingSetText: text,
            plainText: text,
            isEmpty: text.trim().length === 0
          },
          false,
          'setPlainText'
        );
      },

      updateFromDOM: (text: string) => {
        // Called by component when DOM content changes
        set(
          {
            plainText: text,
            isEmpty: text.trim().length === 0
          },
          false,
          'updateFromDOM'
        );
      },

      clear: () => {
        set(
          {
            pendingClear: true,
            plainText: '',
            isEmpty: true
          },
          false,
          'clear'
        );
      },

      clearCompleted: () => {
        set({ pendingClear: false }, false, 'clearCompleted');
      },

      // ─────────────────────────────────────────────────────────────
      // Focus Actions
      // ─────────────────────────────────────────────────────────────

      requestFocus: () => {
        set({ focusRequested: true }, false, 'requestFocus');
      },

      focusCompleted: () => {
        set({ focusRequested: false }, false, 'focusCompleted');
      },

      setIsFocused: (focused: boolean) => {
        set({ isFocused: focused }, false, 'setIsFocused');
      },

      // ─────────────────────────────────────────────────────────────
      // Context Actions
      // ─────────────────────────────────────────────────────────────

      setActiveContexts: (contexts: Map<string, IMentionContext>) => {
        set({ activeContexts: new Map(contexts) }, false, 'setActiveContexts');
      },

      addActiveContext: (context: IMentionContext) => {
        set(
          state => {
            const newContexts = new Map(state.activeContexts);
            newContexts.set(context.id, context);
            return { activeContexts: newContexts };
          },
          false,
          'addActiveContext'
        );
      },

      removeActiveContext: (contextId: string) => {
        set(
          state => {
            const newContexts = new Map(state.activeContexts);
            newContexts.delete(contextId);
            return { activeContexts: newContexts };
          },
          false,
          'removeActiveContext'
        );
      },

      clearActiveContexts: () => {
        set({ activeContexts: new Map() }, false, 'clearActiveContexts');
      },

      // ─────────────────────────────────────────────────────────────
      // Text Insertion Actions
      // ─────────────────────────────────────────────────────────────

      insertText: (text: string) => {
        set(
          {
            pendingTextInsert: {
              id: generateId(),
              text,
              timestamp: Date.now()
            }
          },
          false,
          'insertText'
        );
      },

      insertCompleted: () => {
        set({ pendingTextInsert: null }, false, 'insertCompleted');
      },

      // ─────────────────────────────────────────────────────────────
      // Set Text Actions
      // ─────────────────────────────────────────────────────────────

      setText: (text: string) => {
        set(
          {
            pendingSetText: text,
            plainText: text,
            isEmpty: text.trim().length === 0
          },
          false,
          'setText'
        );
      },

      setTextCompleted: () => {
        set({ pendingSetText: null }, false, 'setTextCompleted');
      },

      // ─────────────────────────────────────────────────────────────
      // Reset
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set({ ...initialState, activeContexts: new Map() }, false, 'reset');
      }
    })),
    { name: 'RichTextInputStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectPlainText = (state: IRichTextInputStore) => state.plainText;
export const selectIsEmpty = (state: IRichTextInputStore) => state.isEmpty;
export const selectIsFocused = (state: IRichTextInputStore) => state.isFocused;
export const selectFocusRequested = (state: IRichTextInputStore) =>
  state.focusRequested;
export const selectActiveContexts = (state: IRichTextInputStore) =>
  state.activeContexts;
export const selectPendingTextInsert = (state: IRichTextInputStore) =>
  state.pendingTextInsert;
export const selectPendingClear = (state: IRichTextInputStore) =>
  state.pendingClear;
export const selectPendingSetText = (state: IRichTextInputStore) =>
  state.pendingSetText;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getRichTextInputState = () => useRichTextInputStore.getState();

/**
 * Subscribe to plain text changes
 */
export const subscribeToPlainText = (callback: (text: string) => void) => {
  return useRichTextInputStore.subscribe(state => state.plainText, callback);
};

/**
 * Subscribe to focus requests
 */
export const subscribeToFocusRequest = (
  callback: (requested: boolean) => void
) => {
  return useRichTextInputStore.subscribe(
    state => state.focusRequested,
    callback
  );
};
