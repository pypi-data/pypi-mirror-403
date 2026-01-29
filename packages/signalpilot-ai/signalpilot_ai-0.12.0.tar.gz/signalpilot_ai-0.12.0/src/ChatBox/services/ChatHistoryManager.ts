import { IChatMessage } from '@/types';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import { StateDBCachingService } from '@/utils/backendCaching';
import { getChatboxState } from '@/stores/chatboxStore';
import { v4 as uuidv4 } from 'uuid';
import {
  LAUNCHER_NOTEBOOK_ID,
  isLauncherNotebookId
} from '@/stores/chatModeStore';

export interface IChatThread {
  id: string;
  name: string;
  messages: IChatMessage[];
  lastUpdated: number;
  contexts: Map<string, IMentionContext>;
  message_timestamps: Map<string, number>;
  continueButtonShown?: boolean; // Track if continue button has been shown in this thread
  needsContinue?: boolean; // Track if this thread should continue the LLM loop after loading (from launcher state)
  agent?: string; // Track the agent that created the thread
}

/**
 * Manager for persisting chat histories across notebook sessions
 */
export class ChatHistoryManager {
  // Map of notebook IDs to their chat threads (in-memory cache)
  private notebookChats: Map<string, IChatThread[]> = new Map();
  // Track which notebooks have been loaded from storage
  private loadedNotebooks: Set<string> = new Set();
  // Current active notebook ID
  private currentNotebookId: string | null = null;
  // Current active chat thread ID
  private currentThreadId: string | null = null;
  // Storage key prefix for individual notebook chat histories
  private readonly STORAGE_KEY_PREFIX = 'chat-history-notebook-';
  // Track loading state for chat history
  private isLoadingHistory: boolean = false;
  // Storage key for current thread mapping
  private readonly CURRENT_THREAD_MAP_KEY = 'notebook-current-threads';

  constructor() {
    // NOTE: Notebook change subscription is handled by chatHistoryStore.ts and NotebookChatContainer.tsx
    // Do NOT subscribe here to avoid duplicate calls to setCurrentNotebook which causes
    // duplicate saveNotebookToStorage operations and slow performance.
  }

  public static getCleanMessageArrayWithTimestamps(thread: IChatThread): any[] {
    // Return messages with timestamps
    return thread.messages.map(message => ({
      ...message,
      timestamp:
        thread.message_timestamps.get(JSON.stringify(message)) || Date.now()
    }));
  }

  /**
   * Check if chat history is currently loading
   */
  public isLoading(): boolean {
    return this.isLoadingHistory;
  }

  /**
   * Start loading state (should be called before triggering notebook change)
   */
  public startLoading(): void {
    this.isLoadingHistory = true;
  }

  public getCurrentThreadId(): string | null {
    return this.currentThreadId;
  }

  public updateNotebookId(oldId: string, newId: string): void {
    this.currentNotebookId = newId;
    const threads = this.notebookChats.get(oldId) || [];
    this.notebookChats.set(newId, threads);
    this.notebookChats.delete(oldId);

    // Update loaded notebooks tracking
    if (this.loadedNotebooks.has(oldId)) {
      this.loadedNotebooks.delete(oldId);
      this.loadedNotebooks.add(newId);
    }

    // Update localStorage mapping
    const oldThreadId = this.getCurrentThreadFromLocalStorage(oldId);
    if (oldThreadId && this.currentThreadId) {
      this.removeCurrentThreadFromLocalStorage(oldId);
      this.storeCurrentThreadInLocalStorage(newId, this.currentThreadId);
    }

    // Save the chat history under the new ID and remove the old one
    void this.saveNotebookToStorage(newId);
    void this.removeNotebookFromStorage(oldId);
  }

  /**
   * Clear the current notebook ID (for launcher mode)
   * This prevents chat messages from being saved to a notebook when in launcher mode
   */
  public clearCurrentNotebook(): void {
    console.log(
      '[ChatHistoryManager] Clearing current notebook (switching to launcher mode)'
    );
    this.currentNotebookId = null;
    this.currentThreadId = null;
  }

  /**
   * Set the current notebook ID and load its chat history
   * @param notebookId ID of the notebook
   * @returns The active chat thread for this notebook (creates one if none exists)
   */
  public async setCurrentNotebook(notebookId: string): Promise<IChatThread> {
    // Set loading state
    this.isLoadingHistory = true;

    // Handle launcher notebook specially - always start fresh
    if (isLauncherNotebookId(notebookId)) {
      console.log(
        '[ChatHistoryManager] Setting up launcher notebook (fresh session)'
      );
      // Clear any existing launcher chat from previous sessions
      this.notebookChats.delete(notebookId);
      this.loadedNotebooks.delete(notebookId);
    }

    // If we're switching notebooks, save the previous one in the background (non-blocking)
    // This is fire-and-forget to avoid blocking the notebook switch - the save happens async
    if (
      this.currentNotebookId &&
      this.currentNotebookId !== notebookId &&
      !isLauncherNotebookId(this.currentNotebookId)
    ) {
      const notebookToSave = this.currentNotebookId;
      // Defer the save to not block the main thread during notebook switch
      setTimeout(() => {
        void this.saveNotebookToStorage(notebookToSave);
        console.log(
          `[ChatHistoryManager] Saved chat data for notebook ${notebookToSave} (background)`
        );
      }, 0);
    }

    if (this.currentNotebookId) {
      if (this.getCurrentThread()) {
        const lastThread = this.getCurrentThread();
        // Store in localStorage
        this.storeCurrentThreadInLocalStorage(
          this.currentNotebookId,
          lastThread!.id
        );
        // Also store in backend cache (optional - threadManager may not be available in new architecture)
        void getChatboxState().services?.chatContainer?.chatWidget?.threadManager?.storeLastThreadForNotebook(
          this.currentNotebookId,
          lastThread?.id
        );
      }
    }

    console.log(`[ChatHistoryManager] Setting current notebook: ${notebookId}`);
    this.currentNotebookId = notebookId;

    // Load chat history for this notebook if not already loaded
    await this.loadNotebookFromStorage(notebookId);

    // Check if we have chat history for this notebook
    if (!this.notebookChats.has(notebookId)) {
      // Create a default thread for this notebook
      const defaultThread: IChatThread = {
        id: this.generateThreadId(),
        name: 'New Chat',
        messages: [],
        lastUpdated: Date.now(),
        contexts: new Map<string, IMentionContext>(),
        message_timestamps: new Map<string, number>()
      };

      this.notebookChats.set(notebookId, [defaultThread]);
      // Save in background (non-blocking)
      void this.saveNotebookToStorage(notebookId);
      this.currentThreadId = defaultThread.id;
      this.storeCurrentThreadInLocalStorage(notebookId, defaultThread.id);

      // Clear loading state
      this.isLoadingHistory = false;

      return defaultThread;
    }

    // Get all threads for this notebook
    const threads = this.notebookChats.get(notebookId)!;

    // Try to restore the current thread from localStorage first
    const storedThreadId = this.getCurrentThreadFromLocalStorage(notebookId);

    if (storedThreadId) {
      // Check if the stored thread still exists
      const storedThread = threads.find(t => t.id === storedThreadId);
      if (storedThread) {
        console.log(
          `[ChatHistoryManager] Restored thread from localStorage: ${storedThread.name}`
        );
        this.currentThreadId = storedThreadId;

        // Clear loading state
        this.isLoadingHistory = false;

        return storedThread;
      }
    }

    // Sort threads by lastUpdated (most recent first)
    const sortedThreads = [...threads].sort(
      (a, b) => b.lastUpdated - a.lastUpdated
    );

    // Use the most recently updated thread as the fallback
    // This ensures we open to the last active thread when localStorage thread doesn't exist
    const mostRecentThread = sortedThreads[0];
    this.currentThreadId = mostRecentThread.id;
    this.storeCurrentThreadInLocalStorage(notebookId, mostRecentThread.id);

    console.log(
      `[ChatHistoryManager] Using most recent thread as fallback: ${mostRecentThread.name} (${mostRecentThread.id})`
    );

    // Clear loading state
    this.isLoadingHistory = false;

    // Return the current thread
    return this.getCurrentThread()!;
  }

  /**
   * Completely re-initialize chat history state for a notebook transition
   * This ensures clean state when transitioning from launcher to notebook
   * @param notebookId ID of the notebook to reinitialize for
   * @returns The active chat thread for this notebook
   */
  public async reinitializeForNotebook(
    notebookId: string
  ): Promise<IChatThread> {
    console.log(
      `[ChatHistoryManager] Re-initializing for notebook: ${notebookId}`
    );

    // Set loading state to true at the start
    this.isLoadingHistory = true;

    await this.loadNotebookFromStorage(notebookId);

    // Clear any stale thread selection state
    if (this.currentNotebookId && this.currentNotebookId !== notebookId) {
      console.log(
        `[ChatHistoryManager] Cleaning up previous notebook: ${this.currentNotebookId}`
      );
      // Save current state before switching
      await this.saveNotebookToStorage(this.currentNotebookId);
      console.log(
        `[ChatHistoryManager] Saved chat data for notebook ${this.currentNotebookId} before re-initializing`
      );

      if (this.getCurrentThread()) {
        const lastThread = this.getCurrentThread();
        this.storeCurrentThreadInLocalStorage(
          this.currentNotebookId,
          lastThread!.id
        );
      }
    }

    // Force reload from storage by marking as not loaded
    this.loadedNotebooks.delete(notebookId);

    // Now call the standard setCurrentNotebook which will reload everything
    return await this.setCurrentNotebook(notebookId);
  }

  /**
   * Get the current active chat thread
   * @returns The current chat thread or null if no notebook is set
   */
  public getCurrentThread(): IChatThread | null {
    if (!this.currentNotebookId || !this.currentThreadId) {
      return null;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      return null;
    }

    return threads.find(thread => thread.id === this.currentThreadId) || null;
  }

  /**
   * Get all chat threads for the current notebook
   * @returns Array of chat threads or empty array if no notebook is set
   */
  public getCurrentNotebookThreads(): IChatThread[] {
    if (!this.currentNotebookId) {
      return [];
    }

    return this.notebookChats.get(this.currentNotebookId) || [];
  }

  /**
   * Get all chat threads for a specific notebook
   * @param notebookId Path to the notebook
   * @returns Array of chat threads or null if notebook not found
   */
  public getThreadsForNotebook(notebookId: string): IChatThread[] | null {
    if (!notebookId || !this.notebookChats.has(notebookId)) {
      return null;
    }

    return this.notebookChats.get(notebookId) || [];
  }

  /**
   * Update the contexts in the current chat thread
   * @param contexts New contexts for the current thread
   */
  public updateCurrentThreadContexts(
    contexts: Map<string, IMentionContext>
  ): void {
    if (!this.currentNotebookId || !this.currentThreadId) {
      console.warn(
        '[ChatHistoryManager] Cannot update contexts: No active notebook or thread'
      );
      return;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      console.warn(
        `[ChatHistoryManager] No threads found for notebook: ${this.currentNotebookId}`
      );
      return;
    }

    const threadIndex = threads.findIndex(
      thread => thread.id === this.currentThreadId
    );
    if (threadIndex === -1) {
      console.warn(
        `[ChatHistoryManager] Thread with ID ${this.currentThreadId} not found`
      );
      return;
    }

    // Update the contexts
    threads[threadIndex].contexts = new Map(contexts);
    threads[threadIndex].lastUpdated = Date.now();

    console.log(
      `[ChatHistoryManager] Updated thread contexts, saving to storage...`
    );

    // Save only this notebook's data to storage
    void this.saveNotebookToStorage(this.currentNotebookId);

    console.log(`[ChatHistoryManager] Context update complete`);
  }

  public updateCurrentThreadAgent(agent: string): void {
    if (!this.currentNotebookId || !this.currentThreadId) {
      console.warn(
        '[ChatHistoryManager] Cannot update agent: No active notebook or thread'
      );
      return;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      console.warn(
        `[ChatHistoryManager] No threads found for notebook: ${this.currentNotebookId}`
      );
      return;
    }

    const threadIndex = threads.findIndex(
      thread => thread.id === this.currentThreadId
    );
    if (threadIndex === -1) {
      console.warn(
        `[ChatHistoryManager] Thread with ID ${this.currentThreadId} not found`
      );
      return;
    }
    threads[threadIndex].agent = agent;

    // Save only this notebook's data to storage
    void this.saveNotebookToStorage(this.currentNotebookId);
  }

  /**
   * Update the messages in the current chat thread
   * @param messages New messages for the current thread
   * @param contexts Optional contexts for mentions in the messages
   */
  public updateCurrentThreadMessages(
    messages: IChatMessage[],
    contexts?: Map<string, IMentionContext>
  ): void {
    console.log(
      `[ChatHistoryManager] updateCurrentThreadMessages called:`,
      `notebookId=${this.currentNotebookId}, threadId=${this.currentThreadId}, messageCount=${messages.length}`
    );

    if (!this.currentNotebookId || !this.currentThreadId) {
      console.warn(
        '[ChatHistoryManager] Cannot update messages: No active notebook or thread',
        'currentNotebookId:',
        this.currentNotebookId,
        'currentThreadId:',
        this.currentThreadId,
        '(This is expected in launcher mode)'
      );
      return;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      console.warn(
        `[ChatHistoryManager] No threads found for notebook: ${this.currentNotebookId}`
      );
      return;
    }

    const threadIndex = threads.findIndex(
      thread => thread.id === this.currentThreadId
    );
    if (threadIndex === -1) {
      console.warn(
        `[ChatHistoryManager] Thread with ID ${this.currentThreadId} not found`
      );
      return;
    }

    try {
      for (const message of messages) {
        if (
          threads[threadIndex].message_timestamps?.has &&
          threads[threadIndex].message_timestamps?.has(JSON.stringify(message))
        ) {
          continue;
        }

        // Add timestamp for the message
        threads[threadIndex].message_timestamps.set(
          JSON.stringify(message),
          Date.now()
        );
        threads[threadIndex].message_timestamps;
      }
    } catch (error) {
      console.log(
        '[ChatHistoryManager] Error updating message timestamps for eval:',
        error
      );
      return;
    }

    // Update the messages and last updated time
    threads[threadIndex].messages = [...messages];

    threads[threadIndex].lastUpdated = Date.now();

    // Update contexts if provided
    if (contexts) {
      threads[threadIndex].contexts = new Map(contexts);
    }

    // Store current thread in localStorage so it's restored on page refresh
    // This is important because threads with 0 messages are filtered out during save,
    // so we need to ensure the localStorage always points to a valid thread with messages
    if (messages.length > 0) {
      this.storeCurrentThreadInLocalStorage(
        this.currentNotebookId,
        this.currentThreadId
      );
    }

    // Save only this notebook's data to storage
    void this.saveNotebookToStorage(this.currentNotebookId);
  }

  /**
   * Clear the messages in the current chat thread
   */
  public clearCurrentThread(): void {
    this.updateCurrentThreadMessages([]);
  }

  /**
   * Get all notebook paths with chat histories (loaded and in storage)
   * @returns Array of notebook paths
   */
  public async getNotebookIds(): Promise<string[]> {
    // Get currently loaded notebook IDs
    const loadedIds = Array.from(this.notebookChats.keys());

    // Get all notebook IDs that have storage entries
    try {
      const allKeys = await StateDBCachingService.listKeys();
      const storageIds = allKeys
        .filter(key => key.startsWith(this.STORAGE_KEY_PREFIX))
        .map(key => key.replace(this.STORAGE_KEY_PREFIX, ''));

      // Combine and deduplicate
      const allIds = new Set([...loadedIds, ...storageIds]);
      return Array.from(allIds);
    } catch (error) {
      console.error(
        '[ChatHistoryManager] Error listing notebook IDs from storage:',
        error
      );
      // Fallback to only loaded IDs
      return loadedIds;
    }
  }

  /**
   * Get all notebook paths with chat histories (synchronous, only loaded notebooks)
   * @returns Array of notebook paths currently loaded in memory
   * @deprecated Use getNotebookIds() for complete list including storage
   */
  public getLoadedNotebookIds(): string[] {
    return Array.from(this.notebookChats.keys());
  }

  /**
   * Create a new chat thread for the current notebook
   * @param name Name of the new thread
   * @returns The newly created thread or null if no notebook is active
   */
  public createNewThread(name: string = 'New Chat'): IChatThread | null {
    if (!this.currentNotebookId) {
      console.warn(
        '[ChatHistoryManager] Cannot create thread: No active notebook'
      );
      return null;
    }

    const newThread: IChatThread = {
      id: this.generateThreadId(),
      name,
      messages: [],
      lastUpdated: Date.now(),
      contexts: new Map<string, IMentionContext>(),
      message_timestamps: new Map<string, number>(),
      continueButtonShown: false
    };

    console.log(
      `[ChatHistoryManager] Creating new thread: ${newThread.id} for notebook: ${this.currentNotebookId}`
    );

    const existingThreads =
      this.notebookChats.get(this.currentNotebookId) || [];

    console.log(
      `[ChatHistoryManager] Existing threads before add: ${existingThreads.length}`,
      existingThreads.map(t => ({
        id: t.id,
        name: t.name,
        msgCount: t.messages.length
      }))
    );

    this.notebookChats.set(this.currentNotebookId, [
      ...existingThreads,
      newThread
    ]);

    // Set the new thread as the current thread
    this.currentThreadId = newThread.id;

    // Store in localStorage
    if (this.currentNotebookId) {
      this.storeCurrentThreadInLocalStorage(
        this.currentNotebookId,
        newThread.id
      );
      console.log(
        `[ChatHistoryManager] Stored thread ${newThread.id} in localStorage for notebook ${this.currentNotebookId}`
      );
    }

    // Save only this notebook's data to storage
    // Note: Empty threads (0 messages) are filtered out during save,
    // but localStorage still points to this thread ID
    if (this.currentNotebookId) {
      void this.saveNotebookToStorage(this.currentNotebookId);
    }

    return newThread;
  }

  /**
   * Copy the current launcher thread to a notebook
   * This is used when transitioning from launcher state to a notebook
   * @param targetNotebookId The notebook ID to copy the thread to
   * @param messages The messages to copy (from ChatMessages component)
   * @param contexts The mention contexts to copy (from ChatMessages component)
   * @returns The newly created thread in the target notebook, or null if no messages to copy
   */
  public async copyLauncherThreadToNotebook(
    targetNotebookId: string,
    messages: IChatMessage[] = [],
    contexts: Map<string, IMentionContext> = new Map()
  ): Promise<IChatThread | null> {
    console.log(
      '[ChatHistoryManager] Copying launcher thread to notebook:',
      targetNotebookId,
      'with',
      messages.length,
      'messages'
    );
    if (!targetNotebookId) {
      console.warn(
        '[ChatHistoryManager] Cannot copy thread: No target notebook ID provided'
      );
      return null;
    }

    // If messages were passed explicitly, use them (this is the case when called from copyThreadToNotebook)
    // Only fall back to current thread's messages when no messages were passed
    if (messages.length === 0) {
      // Try to get messages from current thread
      if (
        this.currentNotebookId !== null &&
        !isLauncherNotebookId(this.currentNotebookId)
      ) {
        const currentThread = this.getCurrentThread();
        if (currentThread) {
          messages = currentThread.messages;
          contexts = currentThread.contexts;
        }
      }
    }

    // Skip if still no messages
    if (messages.length === 0) {
      console.log('[ChatHistoryManager] No messages to copy');
      return null;
    }

    console.log(
      '[ChatHistoryManager] Using',
      messages.length,
      'messages for copied thread'
    );

    // Check if the thread needs to continue the LLM loop
    // This happens when the last message is from the assistant or contains tool_use
    const needsContinue = true;

    // Generate message timestamps map
    const message_timestamps = new Map<string, number>();
    messages.forEach((msg, index) => {
      if (msg.id) {
        message_timestamps.set(
          msg.id,
          Date.now() - (messages.length - index) * 1000
        );
      }
    });

    // Create a new thread in the target notebook with the same content
    const copiedThread: IChatThread = {
      id: this.generateThreadId(), // Generate new ID for the copied thread
      name: 'From Launcher Chat', // Default name for copied threads
      messages: [...messages], // Deep copy messages
      lastUpdated: Date.now(),
      contexts: new Map(contexts), // Deep copy contexts
      message_timestamps: message_timestamps,
      continueButtonShown: false,
      needsContinue: needsContinue
    };

    // Ensure the target notebook has an entry in notebookChats
    await this.loadNotebookFromStorage(targetNotebookId);
    const existingThreads = this.notebookChats.get(targetNotebookId) || [];
    this.notebookChats.set(targetNotebookId, [
      ...existingThreads,
      copiedThread
    ]);

    // Mark the notebook as loaded
    this.loadedNotebooks.add(targetNotebookId);

    // Save the notebook to storage
    await this.saveNotebookToStorage(targetNotebookId);

    // Store this as the current thread for the target notebook in localStorage
    this.storeCurrentThreadInLocalStorage(targetNotebookId, copiedThread.id);

    console.log(
      `[ChatHistoryManager] Copied launcher thread to notebook ${targetNotebookId} as thread ${copiedThread.id}, needsContinue=${needsContinue}`
    );

    return copiedThread;
  }

  /**
   * Switch to a specific chat thread
   * @param threadId ID of the thread to switch to
   * @returns The thread that was switched to, or null if not found
   */
  public switchToThread(threadId: string): IChatThread | null {
    if (!this.currentNotebookId) {
      return null;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      return null;
    }

    const thread = threads.find(t => t.id === threadId);
    if (thread) {
      this.currentThreadId = threadId;
      // Store in localStorage
      this.storeCurrentThreadInLocalStorage(this.currentNotebookId, threadId);
      return thread;
    }

    return null;
  }

  /**
   * Rename the current chat thread
   * @param newName New name for the current thread
   * @returns True if successful, false otherwise
   */
  public renameCurrentThread(newName: string): boolean {
    console.log('[ChatHistoryManager] renameCurrentThread called:', {
      newName,
      currentNotebookId: this.currentNotebookId,
      currentThreadId: this.currentThreadId
    });

    if (!this.currentNotebookId || !this.currentThreadId) {
      console.warn(
        '[ChatHistoryManager] Cannot rename thread: No active notebook or thread',
        {
          currentNotebookId: this.currentNotebookId,
          currentThreadId: this.currentThreadId
        }
      );
      return false;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      console.warn(
        `[ChatHistoryManager] No threads found for notebook: ${this.currentNotebookId}`
      );
      return false;
    }

    console.log(
      '[ChatHistoryManager] Looking for thread in',
      threads.length,
      'threads'
    );

    const threadIndex = threads.findIndex(
      thread => thread.id === this.currentThreadId
    );
    if (threadIndex === -1) {
      console.warn(
        `[ChatHistoryManager] Thread with ID ${this.currentThreadId} not found in threads:`,
        threads.map(t => ({ id: t.id, name: t.name }))
      );
      return false;
    }

    // Update the thread name
    threads[threadIndex].name = newName;

    // Save only this notebook's data to storage
    if (this.currentNotebookId) {
      void this.saveNotebookToStorage(this.currentNotebookId);
    }

    console.log(
      `[ChatHistoryManager] Renamed thread ${this.currentThreadId} to "${newName}"`
    );
    return true;
  }

  /**
   * Delete a chat thread
   * @param threadId ID of the thread to delete
   * @returns True if successful, false otherwise
   */
  public deleteThread(threadId: string): boolean {
    if (!this.currentNotebookId) {
      console.warn(
        '[ChatHistoryManager] Cannot delete thread: No active notebook'
      );
      return false;
    }

    const threads = this.notebookChats.get(this.currentNotebookId);
    if (!threads) {
      return false;
    }

    const threadIndex = threads.findIndex(thread => thread.id === threadId);
    if (threadIndex === -1) {
      return false;
    }

    // Remove the thread
    threads.splice(threadIndex, 1);

    // If we deleted the current thread, switch to first available thread
    if (threadId === this.currentThreadId) {
      if (threads.length > 0) {
        this.currentThreadId = threads[threads.length - 1].id;
        // Update localStorage
        this.storeCurrentThreadInLocalStorage(
          this.currentNotebookId,
          this.currentThreadId
        );
      } else {
        // Create a new default thread if we deleted the last one
        const defaultThread: IChatThread = {
          id: this.generateThreadId(),
          name: 'New Chat',
          messages: [],
          lastUpdated: Date.now(),
          contexts: new Map<string, IMentionContext>(),
          message_timestamps: new Map<string, number>(),
          continueButtonShown: false
        };

        threads.push(defaultThread);
        this.currentThreadId = defaultThread.id;
        // Update localStorage
        this.storeCurrentThreadInLocalStorage(
          this.currentNotebookId,
          this.currentThreadId
        );
      }
    }

    // Save only this notebook's data to storage
    if (this.currentNotebookId) {
      void this.saveNotebookToStorage(this.currentNotebookId);
    }

    console.log(`[ChatHistoryManager] Deleted thread ${threadId}`);
    return true;
  }

  /**
   * Clear all chat history for a specific notebook
   * @param notebookId The notebook ID to clear
   * @returns True if successful, false otherwise
   */
  public async clearNotebookHistory(notebookId: string): Promise<boolean> {
    try {
      // Remove from memory cache
      this.notebookChats.delete(notebookId);
      this.loadedNotebooks.delete(notebookId);

      // Remove from storage
      await this.removeNotebookFromStorage(notebookId);

      // Remove from localStorage
      this.removeCurrentThreadFromLocalStorage(notebookId);

      // If this was the current notebook, reset current state
      if (this.currentNotebookId === notebookId) {
        this.currentNotebookId = null;
        this.currentThreadId = null;
      }

      console.log(
        `[ChatHistoryManager] Cleared all chat history for notebook: ${notebookId}`
      );
      return true;
    } catch (error) {
      console.error(
        `[ChatHistoryManager] Error clearing chat history for notebook ${notebookId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Unload a notebook's chat history from memory (but keep in storage)
   * @param notebookId The notebook ID to unload
   */
  public unloadNotebookFromMemory(notebookId: string): void {
    if (notebookId === this.currentNotebookId) {
      console.warn(
        `[ChatHistoryManager] Cannot unload current notebook ${notebookId} from memory`
      );
      return;
    }

    this.notebookChats.delete(notebookId);
    this.loadedNotebooks.delete(notebookId);
    console.log(
      `[ChatHistoryManager] Unloaded notebook ${notebookId} from memory`
    );
  }

  /**
   * Get cache statistics
   * @returns Object with cache information
   */
  public getCacheStats(): {
    loadedNotebooks: number;
    totalThreadsInMemory: number;
    currentNotebook: string | null;
    memoryUsageEstimate: string;
  } {
    let totalThreads = 0;
    let memorySize = 0;

    for (const [, threads] of this.notebookChats.entries()) {
      totalThreads += threads.length;
      // Rough estimate of memory usage
      memorySize += JSON.stringify(threads).length;
    }

    return {
      loadedNotebooks: this.notebookChats.size,
      totalThreadsInMemory: totalThreads,
      currentNotebook: this.currentNotebookId,
      memoryUsageEstimate: `${(memorySize / 1024).toFixed(2)} KB`
    };
  }

  /**
   * Get current thread for a notebook from localStorage
   */
  private getCurrentThreadFromLocalStorage(notebookId: string): string | null {
    try {
      const stored = localStorage.getItem(this.CURRENT_THREAD_MAP_KEY);
      if (stored) {
        const map = JSON.parse(stored) as Record<string, string>;
        return map[notebookId] || null;
      }
    } catch (error) {
      console.warn(
        '[ChatHistoryManager] Failed to get current thread from localStorage:',
        error
      );
    }
    return null;
  }

  /**
   * Store current thread for a notebook in localStorage
   */
  private storeCurrentThreadInLocalStorage(
    notebookId: string,
    threadId: string
  ): void {
    try {
      const stored = localStorage.getItem(this.CURRENT_THREAD_MAP_KEY);
      const map: Record<string, string> = stored ? JSON.parse(stored) : {};
      map[notebookId] = threadId;
      localStorage.setItem(this.CURRENT_THREAD_MAP_KEY, JSON.stringify(map));
    } catch (error) {
      console.warn(
        '[ChatHistoryManager] Failed to store current thread in localStorage:',
        error
      );
    }
  }

  /**
   * Remove current thread for a notebook from localStorage
   */
  private removeCurrentThreadFromLocalStorage(notebookId: string): void {
    try {
      const stored = localStorage.getItem(this.CURRENT_THREAD_MAP_KEY);
      if (stored) {
        const map: Record<string, string> = JSON.parse(stored);
        delete map[notebookId];
        localStorage.setItem(this.CURRENT_THREAD_MAP_KEY, JSON.stringify(map));
      }
    } catch (error) {
      console.warn(
        '[ChatHistoryManager] Failed to remove current thread from localStorage:',
        error
      );
    }
  }

  /**
   * Save a specific notebook's chat history to storage
   * @param notebookId The notebook ID to save
   */
  private async saveNotebookToStorage(notebookId: string): Promise<void> {
    console.log(
      `[ChatHistoryManager] saveNotebookToStorage called for notebook: ${notebookId}`
    );

    // Skip persistence for launcher notebook - it's in-memory only
    if (isLauncherNotebookId(notebookId)) {
      console.log(
        '[ChatHistoryManager] Skipping save for launcher notebook (in-memory only)'
      );
      return;
    }

    if (!notebookId || !this.notebookChats.has(notebookId)) {
      console.warn(
        `[ChatHistoryManager] Cannot save: notebook ${notebookId} not found in cache`
      );
      return;
    }

    try {
      const threads = this.notebookChats.get(notebookId)!;

      console.log(
        `[ChatHistoryManager] Threads in memory before filtering:`,
        threads.map(t => ({
          id: t.id,
          name: t.name,
          msgCount: t.messages?.length || 0
        }))
      );

      // Filter out empty chats - keep all threads with messages regardless of name
      const filteredThreads = threads.filter(thread => {
        // Skip chats with 0 messages
        if (!thread.messages || thread.messages.length === 0) {
          console.log(
            `[ChatHistoryManager] Skipping empty chat: ${thread.name} (${thread.id})`
          );
          return false;
        }

        // Keep all threads that have messages, even if named "New Chat"
        // The UI may show multiple "New Chat" threads if renaming failed,
        // but we shouldn't delete user data
        return true;
      });

      console.log(
        `[ChatHistoryManager] Threads after filtering (will be saved):`,
        filteredThreads.map(t => ({
          id: t.id,
          name: t.name,
          msgCount: t.messages?.length || 0
        }))
      );

      // Convert each thread's contexts Map to a serializable object
      const serializedThreads = filteredThreads.map(thread => ({
        ...thread,
        contexts: thread.contexts ? Object.fromEntries(thread.contexts) : {},
        message_timestamps: thread.message_timestamps
          ? Object.fromEntries(thread.message_timestamps)
          : {}
      }));

      const storageKey = `${this.STORAGE_KEY_PREFIX}${notebookId}`;
      await StateDBCachingService.setObjectValue(storageKey, serializedThreads);

      console.log(
        `[ChatHistoryManager] Saved chat history for notebook: ${notebookId} (${serializedThreads.length} threads, filtered from ${threads.length})`
      );

      // Also log current localStorage state for this notebook
      const storedThreadId = this.getCurrentThreadFromLocalStorage(notebookId);
      console.log(
        `[ChatHistoryManager] localStorage currentThreadId for ${notebookId}: ${storedThreadId}`
      );
    } catch (error) {
      console.error(
        `[ChatHistoryManager] Error saving chat history for notebook ${notebookId}:`,
        error
      );
    }
  }

  /**
   * Load a specific notebook's chat history from storage
   * @param notebookId The notebook ID to load
   */
  private async loadNotebookFromStorage(notebookId: string): Promise<void> {
    console.log(
      `[ChatHistoryManager] loadNotebookFromStorage called for: ${notebookId}`
    );

    // Skip loading from storage for launcher notebook - it's in-memory only
    if (isLauncherNotebookId(notebookId)) {
      console.log(
        '[ChatHistoryManager] Skipping load for launcher notebook (in-memory only)'
      );
      this.loadedNotebooks.add(notebookId);
      return;
    }

    if (this.loadedNotebooks.has(notebookId)) {
      console.log(
        `[ChatHistoryManager] Notebook ${notebookId} already loaded, skipping`
      );
      return;
    }

    try {
      const storageKey = `${this.STORAGE_KEY_PREFIX}${notebookId}`;
      const storedThreads = await StateDBCachingService.getObjectValue<any[]>(
        storageKey,
        []
      );

      console.log(
        `[ChatHistoryManager] Raw threads from storage for ${notebookId}:`,
        storedThreads?.map(t => ({
          id: t.id,
          name: t.name,
          msgCount: t.messages?.length || 0
        })) || 'none'
      );

      // Also log localStorage state
      const storedThreadId = this.getCurrentThreadFromLocalStorage(notebookId);
      console.log(
        `[ChatHistoryManager] localStorage currentThreadId for ${notebookId}: ${storedThreadId}`
      );

      if (storedThreads && storedThreads.length > 0) {
        // Convert object back to proper IChatThread format
        const migratedThreads: IChatThread[] = storedThreads.map(thread => ({
          ...thread,
          contexts: thread.contexts
            ? new Map<string, IMentionContext>(Object.entries(thread.contexts))
            : new Map<string, IMentionContext>(),
          message_timestamps: thread.message_timestamps
            ? new Map<string, number>(Object.entries(thread.message_timestamps))
            : new Map<string, number>()
        }));

        this.notebookChats.set(notebookId, migratedThreads);
        console.log(
          `[ChatHistoryManager] Loaded ${migratedThreads.length} threads for notebook: ${notebookId}`,
          migratedThreads.map(t => ({
            id: t.id,
            name: t.name,
            msgCount: t.messages?.length || 0
          }))
        );
      } else {
        console.log(
          `[ChatHistoryManager] No stored chat history found for notebook: ${notebookId}`
        );
      }

      this.loadedNotebooks.add(notebookId);
    } catch (error) {
      console.error(
        `[ChatHistoryManager] Error loading chat history for notebook ${notebookId}:`,
        error
      );
      this.loadedNotebooks.add(notebookId); // Mark as loaded even on error to avoid retry loops
    }
  }

  /**
   * Remove a notebook's chat history from storage
   * @param notebookId The notebook ID to remove
   */
  private async removeNotebookFromStorage(notebookId: string): Promise<void> {
    try {
      const storageKey = `${this.STORAGE_KEY_PREFIX}${notebookId}`;
      await StateDBCachingService.removeValue(storageKey);
      console.log(
        `[ChatHistoryManager] Removed chat history for notebook: ${notebookId}`
      );
    } catch (error) {
      console.error(
        `[ChatHistoryManager] Error removing chat history for notebook ${notebookId}:`,
        error
      );
    }
  }

  /**
   * Generate a unique ID for a new chat thread
   */
  private generateThreadId(): string {
    return 'thread_' + uuidv4();
  }
}
