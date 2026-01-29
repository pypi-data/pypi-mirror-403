/**
 * Zustand store for chat input state management.
 *
 * This store manages state specific to the chat input component:
 * - Input text value and placeholder
 * - Message history navigation
 * - Token progress and compacting state
 * - Focus management
 * - Pending message operations
 *
 * Note: `mode` and `contexts` are managed by useChatStore to avoid duplication.
 * Note: Mention dropdown state is managed locally in MentionDropdown.tsx component.
 */
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Pending message operation
 */
export interface IPendingMessageOp {
  id: string;
  type: 'send' | 'continue';
  cellContext?: string;
  hidden?: boolean;
  message?: string;
  timestamp: number;
}

export interface ChatInputState {
  // Input state
  inputValue: string;
  placeholder: string;

  // History navigation
  userMessageHistory: string[];
  historyPosition: number;
  unsavedInput: string;

  // Token progress
  currentTokenCount: number;
  isCompacting: boolean;

  // New Prompt CTA visibility (shown when token usage >= 40%)
  showNewPromptCta: boolean;

  // Focus management
  focusRequested: boolean;

  // Pending operations
  pendingMessageOp: IPendingMessageOp | null;

  // Context row refresh trigger
  contextRowKey: number;
}

export interface ChatInputActions {
  // Input actions
  setInputValue: (value: string) => void;
  clearInput: () => void;
  setPlaceholder: (placeholder: string) => void;

  // History actions
  setUserMessageHistory: (history: string[]) => void;
  addToHistory: (message: string) => void;
  navigateHistory: (
    direction: 'up' | 'down',
    currentInput: string
  ) => string | null;
  resetHistoryNavigation: () => void;

  // Token progress actions
  setTokenCount: (count: number) => void;
  setCompacting: (isCompacting: boolean) => void;

  // New Prompt CTA actions
  setShowNewPromptCta: (show: boolean) => void;
  updateNewPromptCtaFromTokenPercentage: (percentage: number) => void;

  // Focus actions
  requestFocus: () => void;
  focusCompleted: () => void;

  // Message operation actions
  sendMessage: (
    cellContext?: string,
    hidden?: boolean,
    message?: string
  ) => void;
  continueMessage: (cellContext?: string) => void;
  messageOpCompleted: () => void;

  // Context row actions
  refreshContextRow: () => void;

  // Reset
  reset: () => void;
}

export type ChatInputStore = ChatInputState & ChatInputActions;

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

function generateId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: ChatInputState = {
  inputValue: '',
  placeholder: 'What would you like me to generate or analyze?',
  userMessageHistory: [],
  historyPosition: -1,
  unsavedInput: '',
  currentTokenCount: 0,
  isCompacting: false,
  showNewPromptCta: false,
  focusRequested: false,
  pendingMessageOp: null,
  contextRowKey: 0
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatInputStore = create<ChatInputStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // Input actions
      setInputValue: (value: string) => {
        set({ inputValue: value }, false, 'setInputValue');
      },

      clearInput: () => {
        set({ inputValue: '' }, false, 'clearInput');
      },

      setPlaceholder: (placeholder: string) => {
        set({ placeholder }, false, 'setPlaceholder');
      },

      // History actions
      setUserMessageHistory: (history: string[]) => {
        set({ userMessageHistory: history }, false, 'setUserMessageHistory');
      },

      addToHistory: (message: string) => {
        const { userMessageHistory } = get();
        if (!userMessageHistory.includes(message)) {
          set(
            {
              userMessageHistory: [...userMessageHistory, message],
              historyPosition: -1,
              unsavedInput: ''
            },
            false,
            'addToHistory'
          );
        } else {
          set({ historyPosition: -1, unsavedInput: '' }, false, 'resetHistory');
        }
      },

      navigateHistory: (direction: 'up' | 'down', currentInput: string) => {
        const { userMessageHistory, historyPosition, unsavedInput } = get();

        if (userMessageHistory.length === 0) {
          return null;
        }

        // Save current input if this is the first navigation
        let newUnsavedInput = unsavedInput;
        if (historyPosition === -1) {
          newUnsavedInput = currentInput;
        }

        let newPosition = historyPosition;
        let resultMessage: string | null = null;

        if (direction === 'up') {
          // Navigate to older message
          if (historyPosition < userMessageHistory.length - 1) {
            newPosition = historyPosition + 1;
            resultMessage =
              userMessageHistory[userMessageHistory.length - 1 - newPosition];
          }
        } else {
          // Navigate to newer message
          if (historyPosition > 0) {
            newPosition = historyPosition - 1;
            resultMessage =
              userMessageHistory[userMessageHistory.length - 1 - newPosition];
          } else if (historyPosition === 0) {
            // Restore unsaved input
            newPosition = -1;
            resultMessage = newUnsavedInput;
          }
        }

        if (resultMessage !== null) {
          set(
            {
              historyPosition: newPosition,
              unsavedInput: newUnsavedInput,
              inputValue: resultMessage
            },
            false,
            'navigateHistory'
          );
        }

        return resultMessage;
      },

      resetHistoryNavigation: () => {
        set(
          { historyPosition: -1, unsavedInput: '' },
          false,
          'resetHistoryNavigation'
        );
      },

      // Token progress actions
      setTokenCount: (count: number) => {
        set({ currentTokenCount: count }, false, 'setTokenCount');
      },

      setCompacting: (isCompacting: boolean) => {
        set({ isCompacting }, false, 'setCompacting');
      },

      // New Prompt CTA actions
      setShowNewPromptCta: (show: boolean) => {
        set({ showNewPromptCta: show }, false, 'setShowNewPromptCta');
      },

      updateNewPromptCtaFromTokenPercentage: (percentage: number) => {
        const show = percentage >= 40;
        const { showNewPromptCta } = get();
        if (showNewPromptCta !== show) {
          set(
            { showNewPromptCta: show },
            false,
            'updateNewPromptCtaFromTokenPercentage'
          );
        }
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

      // ─────────────────────────────────────────────────────────────
      // Message Operation Actions
      // ─────────────────────────────────────────────────────────────

      sendMessage: (
        cellContext?: string,
        hidden?: boolean,
        message?: string
      ) => {
        set(
          {
            pendingMessageOp: {
              id: generateId(),
              type: 'send',
              cellContext,
              hidden,
              message,
              timestamp: Date.now()
            }
          },
          false,
          'sendMessage'
        );
      },

      continueMessage: (cellContext?: string) => {
        set(
          {
            pendingMessageOp: {
              id: generateId(),
              type: 'continue',
              cellContext,
              timestamp: Date.now()
            }
          },
          false,
          'continueMessage'
        );
      },

      messageOpCompleted: () => {
        set({ pendingMessageOp: null }, false, 'messageOpCompleted');
      },

      // ─────────────────────────────────────────────────────────────
      // Context Row Actions
      // ─────────────────────────────────────────────────────────────

      refreshContextRow: () => {
        set(
          state => ({ contextRowKey: state.contextRowKey + 1 }),
          false,
          'refreshContextRow'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Reset
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set(initialState, false, 'reset');
      }
    })),
    { name: 'ChatInputStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectInputValue = (state: ChatInputStore) => state.inputValue;
export const selectPlaceholder = (state: ChatInputStore) => state.placeholder;
export const selectTokenCount = (state: ChatInputStore) =>
  state.currentTokenCount;
export const selectIsCompacting = (state: ChatInputStore) => state.isCompacting;
export const selectShowNewPromptCta = (state: ChatInputStore) =>
  state.showNewPromptCta;
export const selectFocusRequested = (state: ChatInputStore) =>
  state.focusRequested;
export const selectPendingMessageOp = (state: ChatInputStore) =>
  state.pendingMessageOp;
export const selectContextRowKey = (state: ChatInputStore) =>
  state.contextRowKey;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getChatInputState = () => useChatInputStore.getState();

/**
 * Subscribe to input value changes
 */
export const subscribeToInputValue = (callback: (value: string) => void) => {
  return useChatInputStore.subscribe(state => state.inputValue, callback);
};

/**
 * Subscribe to focus requests
 */
export const subscribeToFocusRequested = (
  callback: (requested: boolean) => void
) => {
  return useChatInputStore.subscribe(state => state.focusRequested, callback);
};

/**
 * Subscribe to pending message operations
 */
export const subscribeToPendingMessageOp = (
  callback: (op: IPendingMessageOp | null) => void
) => {
  return useChatInputStore.subscribe(state => state.pendingMessageOp, callback);
};
