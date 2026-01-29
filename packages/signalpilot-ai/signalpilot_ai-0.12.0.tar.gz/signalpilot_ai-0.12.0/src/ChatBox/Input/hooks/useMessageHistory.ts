/**
 * useMessageHistory Hook
 *
 * Manages user message history for the chat input.
 * Handles loading history from ChatHistoryManager and arrow key navigation.
 */
import { useCallback, useRef } from 'react';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import { useChatInputStore } from '@/stores/chatInput';

interface UseMessageHistoryOptions {
  chatHistoryManager?: ChatHistoryManager | null;
}

interface UseMessageHistoryReturn {
  /** Load user message history from all chat threads */
  loadHistory: () => Promise<void>;
  /** Navigate through message history */
  navigateHistory: (
    direction: 'up' | 'down',
    currentInput: string,
    cursorPosition: number,
    inputLength: number
  ) => string | null;
  /** Add a message to history after sending */
  addToHistory: (message: string) => void;
  /** Reset history navigation state */
  resetNavigation: () => void;
}

/**
 * Hook for managing user message history navigation.
 *
 * Features:
 * - Loads history from all notebooks and threads
 * - Arrow up/down navigation through history
 * - Preserves unsaved input when navigating
 * - Sorts history for intuitive navigation
 */
export function useMessageHistory({
  chatHistoryManager
}: UseMessageHistoryOptions): UseMessageHistoryReturn {
  const isLoadingRef = useRef(false);

  const {
    setUserMessageHistory,
    navigateHistory: storeNavigateHistory,
    addToHistory: storeAddToHistory,
    resetHistoryNavigation
  } = useChatInputStore();

  /**
   * Load user message history from all chat threads.
   * Called on component mount and when threads change.
   */
  const loadHistory = useCallback(async () => {
    if (isLoadingRef.current || !chatHistoryManager) return;
    isLoadingRef.current = true;

    try {
      const history: string[] = [];

      // Get all notebook IDs
      const notebookIds = await chatHistoryManager.getNotebookIds();

      for (const notebookId of notebookIds) {
        // Get all threads for this notebook
        const threads = chatHistoryManager.getThreadsForNotebook(notebookId);
        if (!threads) continue;

        // Extract user messages from each thread
        for (const thread of threads) {
          const userMessages = thread.messages
            .filter(
              msg => msg.role === 'user' && typeof msg.content === 'string'
            )
            .map(msg => (typeof msg.content === 'string' ? msg.content : ''));

          // Add non-empty, non-duplicate messages
          userMessages.forEach(msg => {
            if (msg && !history.includes(msg)) {
              history.push(msg);
            }
          });
        }
      }

      // Sort history - shorter messages (more general/reusable) at the end
      // This makes arrow key navigation more intuitive
      history.sort((a, b) => {
        if (a.length !== b.length) {
          return a.length - b.length;
        }
        return a.localeCompare(b);
      });

      setUserMessageHistory(history);
      console.log(
        `[useMessageHistory] Loaded ${history.length} user messages for history navigation`
      );
    } catch (error) {
      console.error('[useMessageHistory] Error loading history:', error);
    } finally {
      isLoadingRef.current = false;
    }
  }, [chatHistoryManager, setUserMessageHistory]);

  /**
   * Navigate through history with arrow keys.
   * Only triggers when cursor is at appropriate position:
   * - ArrowUp: cursor at start (position 0) or input empty
   * - ArrowDown: cursor at end (position === length) or input empty
   */
  const navigateHistory = useCallback(
    (
      direction: 'up' | 'down',
      currentInput: string,
      cursorPosition: number,
      inputLength: number
    ): string | null => {
      // ArrowUp: only navigate if cursor is at start or input is empty
      if (direction === 'up') {
        if (cursorPosition !== 0 && currentInput !== '') {
          return null;
        }
      }
      // ArrowDown: only navigate if cursor is at end or input is empty
      if (direction === 'down') {
        if (cursorPosition !== inputLength && currentInput !== '') {
          return null;
        }
      }

      return storeNavigateHistory(direction, currentInput);
    },
    [storeNavigateHistory]
  );

  /**
   * Add a message to history after sending.
   * Prevents duplicates and resets navigation state.
   */
  const addToHistory = useCallback(
    (message: string) => {
      if (message.trim()) {
        storeAddToHistory(message);
      }
    },
    [storeAddToHistory]
  );

  /**
   * Reset history navigation state.
   * Called when user starts typing new content.
   */
  const resetNavigation = useCallback(() => {
    resetHistoryNavigation();
  }, [resetHistoryNavigation]);

  return {
    loadHistory,
    navigateHistory,
    addToHistory,
    resetNavigation
  };
}
