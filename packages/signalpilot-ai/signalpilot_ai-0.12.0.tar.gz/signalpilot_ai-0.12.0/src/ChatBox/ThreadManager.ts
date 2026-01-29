import {
  ChatHistoryManager,
  IChatThread
} from '@/ChatBox/services/ChatHistoryManager';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { IChatService } from '../LLM/IChatService';
import {
  subscribeToNotebookChange,
  useNotebookEventsStore
} from '../stores/notebookEventsStore';
import { getNotebookDiffManager } from '../stores/servicesStore';
import { StateDBCachingService } from '../utils/backendCaching';
import { renderContextTagsAsPlainText } from '../utils/contextTagUtils';
import { useChatUIStore } from '../stores/chatUIStore';
import { useLLMStateStore } from '../stores/llmStateStore';
import { useChatHistoryStore } from '../stores/chatHistoryStore';

// Key for storing all last threads in a single object
const LAST_THREADS_KEY = 'lastThreads';

/**
 * Manages thread operations for the chatbox
 */
export class ThreadManager {
  private chatHistoryManager: ChatHistoryManager;
  private messageComponent: ChatMessages;
  private chatService: IChatService;
  private currentNotebookId: string | null = null;
  private static migrationDone = false;

  // Replace single templateContext with a templates array that includes names
  private templates: Array<{ name: string; content: string }> = [];

  constructor(
    chatHistoryManager: ChatHistoryManager,
    messageComponent: ChatMessages,
    chatService: IChatService,
    _chatNode: HTMLElement // Kept for API compatibility but banner is now React-based
  ) {
    this.chatHistoryManager = chatHistoryManager;
    this.messageComponent = messageComponent;
    this.chatService = chatService;

    // Banner is now handled by React ThreadBanner component
    // Thread name display is now handled by React ChatToolbar component

    // Subscribe to notebook change events from store
    subscribeToNotebookChange(({ newNotebookId }) => {
      if (newNotebookId) {
        this.setNotebookId(newNotebookId);
      }
    });
  }

  public updateNotebookId(newId: string): void {
    this.setNotebookId(newId);
  }

  /**
   * Set the current notebook ID
   * @param notebookId ID of the notebook
   */
  public setNotebookId(notebookId: string | null): void {
    this.currentNotebookId = notebookId;
    // Banner and thread name display are now handled by React components
  }

  /**
   * Migrate old last-thread-* keys to consolidated lastThreads object
   */
  private async migrateOldLastThreadKeys(): Promise<void> {
    if (ThreadManager.migrationDone) {
      return;
    }
    ThreadManager.migrationDone = true;

    try {
      // Get all app values to find old keys
      const appValues = await StateDBCachingService.getObjectValue<
        Record<string, any>
      >('__all_app_values__', {});

      // This won't work directly - we need to check for old keys via the backend
      // Instead, we'll do a simple migration: try to get old format, if exists, migrate
      // The backend will handle the actual migration
      console.log('[ThreadManager] Migration check completed');
    } catch (error) {
      console.warn('[ThreadManager] Migration check failed:', error);
    }
  }

  /**
   * Store the last selected thread for a notebook
   * @param notebookId ID of the notebook
   * @param threadId ID of the thread to remember
   */
  public async storeLastThreadForNotebook(
    notebookId: string,
    threadId?: string
  ): Promise<void> {
    try {
      // Get the current lastThreads object
      const lastThreads = await StateDBCachingService.getObjectValue<
        Record<string, string>
      >(LAST_THREADS_KEY, {});

      if (threadId) {
        lastThreads[notebookId] = threadId;
      } else {
        delete lastThreads[notebookId];
      }

      // Save the updated object
      await StateDBCachingService.setObjectValue(LAST_THREADS_KEY, lastThreads);
      console.log(
        `[ThreadManager] Stored last thread ${threadId} for notebook ${notebookId}`
      );
    } catch (error) {
      console.warn('[ThreadManager] Failed to store last thread:', error);
    }
  }

  /**
   * Get the last selected thread for a notebook
   * @param notebookId ID of the notebook
   * @returns The thread ID if found, null otherwise
   */
  public async getLastThreadForNotebook(
    notebookId: string
  ): Promise<string | null> {
    try {
      // Ensure migration has been attempted
      await this.migrateOldLastThreadKeys();

      // Get the lastThreads object
      const lastThreads = await StateDBCachingService.getObjectValue<
        Record<string, string>
      >(LAST_THREADS_KEY, {});

      const threadId = lastThreads[notebookId] || null;
      console.log(
        `[ThreadManager] Retrieved last thread ${threadId} for notebook ${notebookId}`
      );
      return threadId;
    } catch (error) {
      console.warn('[ThreadManager] Failed to get last thread:', error);
      return null;
    }
  }

  /**
   * Get the last selected thread object for a notebook, or null if not found
   * @param notebookId ID of the notebook
   * @returns The thread object if found and valid, null otherwise
   */
  public async getLastValidThreadForNotebook(
    notebookId: string
  ): Promise<IChatThread | null> {
    try {
      const threadId = await this.getLastThreadForNotebook(notebookId);
      if (!threadId) {
        return null;
      }

      // Check if the thread still exists in the chat history
      const threads = this.chatHistoryManager.getThreadsForNotebook(notebookId);
      if (!threads) {
        console.log(
          `[ThreadManager] No threads found for notebook ${notebookId}`
        );
        await this.clearLastThreadForNotebook(notebookId);
        return null;
      }

      const thread = threads.find(t => t.id === threadId);

      if (thread) {
        console.log(
          `[ThreadManager] Found valid last thread: ${thread.name} for notebook ${notebookId}`
        );
        return thread;
      } else {
        console.log(
          `[ThreadManager] Last thread ${threadId} no longer exists for notebook ${notebookId}`
        );
        // Clean up invalid reference
        await this.clearLastThreadForNotebook(notebookId);
        return null;
      }
    } catch (error) {
      console.warn('[ThreadManager] Failed to get last valid thread:', error);
      return null;
    }
  }

  /**
   * Clear the stored last thread for a notebook
   * @param notebookId ID of the notebook
   */
  public async clearLastThreadForNotebook(notebookId: string): Promise<void> {
    try {
      // Get the current lastThreads object
      const lastThreads = await StateDBCachingService.getObjectValue<
        Record<string, string>
      >(LAST_THREADS_KEY, {});

      // Remove the entry for this notebook
      delete lastThreads[notebookId];

      // Save the updated object
      await StateDBCachingService.setObjectValue(LAST_THREADS_KEY, lastThreads);
      console.log(
        `[ThreadManager] Cleared last thread for notebook ${notebookId}`
      );
    } catch (error) {
      console.warn('[ThreadManager] Failed to clear last thread:', error);
    }
  }

  /**
   * Filter thread list to display only one "New Chat" (the most recent)
   * @param threads Sorted threads (most recent first)
   * @returns Filtered thread list
   */
  private filterNewChatThreads(threads: IChatThread[]): IChatThread[] {
    // Find the most recent "New Chat" thread
    const newChatThreads = threads.filter(thread => thread.name === 'New Chat');

    // If there's only 0 or 1 "New Chat" thread, return all threads
    if (newChatThreads.length <= 1) {
      return threads;
    }

    // Get the most recent "New Chat" thread (should be first since threads are pre-sorted)
    const mostRecentNewChat = newChatThreads[0];

    // Filter out all other "New Chat" threads for display purposes
    return threads.filter(
      thread => thread.name !== 'New Chat' || thread.id === mostRecentNewChat.id
    );
  }

  // Thread name display is now handled by React ChatToolbar component
  // The component polls ChatHistoryManager for the current thread name

  /**
   * Select a specific thread and load its history
   * @param threadId ID of the thread to select
   */
  public async selectThread(threadId: string): Promise<void> {
    // First, cancel any ongoing request in the chat service
    this.chatService.cancelRequest();
    let thread = this.chatHistoryManager.getCurrentThread();
    if (threadId !== this.chatHistoryManager.getCurrentThread()?.id) {
      thread = this.chatHistoryManager.switchToThread(threadId);
      const nbId = useNotebookEventsStore.getState().currentNotebookId;
      if (nbId) {
        await this.storeLastThreadForNotebook(nbId, thread?.id);
      }
    }

    if (thread) {
      // Load the selected thread
      await this.messageComponent.loadFromThread(thread);

      // Thread name display is now handled by React ChatToolbar component

      if (thread.messages.length > 0) {
        useChatUIStore.getState().switchToHistoryWidget();
      } else {
        useChatUIStore.getState().switchToNewChatDisplay();
      }
      useLLMStateStore.getState().hide();

      this.clearDiffs();
    }
  }

  /**
   * Create a new chat thread
   */
  public async createNewThread(): Promise<IChatThread | null> {
    // Only proceed if we have an active notebook
    if (!this.currentNotebookId) {
      return null;
    }

    // Get the current thread to rename if it has messages
    const currentThread = this.chatHistoryManager.getCurrentThread();
    if (currentThread && currentThread.messages.length > 0) {
      // Find the first user message to use for naming
      const firstUserMessage = currentThread.messages.find(
        msg => msg.role === 'user' && typeof msg.content === 'string'
      );

      if (firstUserMessage && typeof firstUserMessage.content === 'string') {
        // Generate a paraphrased name for the thread
        const threadName = this.paraphraseThreadName(firstUserMessage.content);

        // Rename the current thread
        this.chatHistoryManager.renameCurrentThread(threadName);
      }
    }

    // Create a new thread
    const newThread = this.chatHistoryManager.createNewThread('New Chat');

    if (newThread) {
      // Sync Zustand from ChatHistoryManager (single source of truth)
      await useChatHistoryStore.getState().syncFromManager();

      const nbId = useNotebookEventsStore.getState().currentNotebookId;
      if (nbId) {
        await this.storeLastThreadForNotebook(nbId, newThread?.id);
      }

      // Load the empty thread into the UI
      await this.messageComponent.loadFromThread(newThread);

      // Thread name display is now handled by React ChatToolbar component

      this.clearDiffs();
    }

    return newThread;
  }

  public clearDiffs(): void {
    getNotebookDiffManager().rejectAndRevertDiffsImmediately();
  }

  /**
   * Generate a paraphrased name from a user message
   * @param message User message to paraphrase
   * @returns Short paraphrased thread name
   */
  private paraphraseThreadName(message: string): string {
    const processedMessage = renderContextTagsAsPlainText(message);
    // Simplistic approach: take the first 5-8 words, max 30 chars
    const words = processedMessage.split(/\s+/);
    const selectedWords = words.slice(0, Math.min(8, words.length));
    let threadName = selectedWords.join(' ');

    // Truncate if too long
    if (threadName.length > 30) {
      threadName = threadName.substring(0, 27) + '...';
    }

    return threadName;
  }

  // ============================================
  // Banner functionality has been moved to React ThreadBanner component
  // The following methods are no longer used:
  // - initializeBanner(), setupBannerEventHandlers()
  // - openBanner(), closeBanner()
  // - populateBannerContent(), refreshBannerIfVisible()
  // ============================================
}

/**
 * Format a date as a string.
 * Example: "7/1/25 · 12:00 PM"
 * @param date The date to format
 * @returns The formatted date string
 */
function formatDate(date: number): string {
  return (
    new Date(date).toLocaleDateString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: '2-digit'
    }) +
    ' · ' +
    new Date(date).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  );
}
