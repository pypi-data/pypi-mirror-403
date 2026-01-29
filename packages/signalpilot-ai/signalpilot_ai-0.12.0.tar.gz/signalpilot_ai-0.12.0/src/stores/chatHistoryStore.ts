/**
 * ChatHistoryStore
 *
 * Zustand store for chat history management.
 * Manages thread listing, selection, and history persistence state.
 *
 * Note: This complements useChatStore which handles the active thread's
 * messages. This store focuses on:
 * - Thread list for the banner/dropdown
 * - Thread selection state
 * - History loading state
 * - User message history (for up/down navigation)
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { IChatMessage, ICheckpoint } from '../types';
import {
  ChatUIMessage,
  IAssistantUIMessage,
  IDiffApprovalUIMessage,
  IDiffCellUI,
  IToolCallUIMessage,
  IUserUIMessage,
  useChatMessagesStore
} from './chatMessages';
import { useWaitingReplyStore } from './waitingReplyStore';
import { getIsDemoActivelyRunning } from '../Demo/demo';
import { startTimer, endTimer } from '../utils/performanceDebug';
import { isToolSearchTool, isMCPTool } from '../utils/toolDisplay';
import { CheckpointManager } from '../Services/CheckpointManager';

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

/**
 * Convert LLM messages (IChatMessage[]) to UI messages (ChatUIMessage[])
 * This is needed because stored threads only have LLM-format messages,
 * but the UI needs ChatUIMessage format for rendering.
 */
function convertLlmMessagesToUiMessages(
  llmMessages: IChatMessage[],
  timestamps: Map<string, number>,
  checkpointManager?: CheckpointManager
): ChatUIMessage[] {
  const uiMessages: ChatUIMessage[] = [];
  let lastRole: string | null = null;

  // STEP 1: Build a map of tool_use_id → tool_result content
  // This allows us to correlate tool calls with their results (for toolSearchResult)
  const toolResultMap = new Map<string, any>();
  for (const msg of llmMessages) {
    if (msg.role === 'user' && Array.isArray(msg.content)) {
      for (const content of msg.content as any[]) {
        if (content.type === 'tool_result' && content.tool_use_id) {
          // Try to parse JSON string results (they were stringified when stored)
          let resultContent = content.content;
          if (typeof resultContent === 'string') {
            try {
              resultContent = JSON.parse(resultContent);
            } catch {
              // Keep as string if not valid JSON
            }
          }
          toolResultMap.set(content.tool_use_id, resultContent);
        }
      }
    }
  }

  for (let i = 0; i < llmMessages.length; i++) {
    const msg = llmMessages[i];
    const messageId = msg.id || `msg_restored_${i}_${Date.now()}`;
    const timestamp =
      timestamps.get(messageId) || Date.now() - (llmMessages.length - i) * 1000;

    // Skip hidden messages
    if (msg.hidden) {
      continue;
    }

    if (msg.role === 'user') {
      // Handle user messages
      const content =
        typeof msg.content === 'string'
          ? msg.content
          : Array.isArray(msg.content)
            ? msg.content
                .filter((block: any) => block.type === 'text')
                .map((block: any) => block.text)
                .join('\n')
            : '';

      if (content) {
        // Look up checkpoint from CheckpointManager if available
        let checkpoint: ICheckpoint | undefined;
        if (checkpointManager) {
          checkpoint =
            checkpointManager.findCheckpointByUserMessageId(messageId) ??
            undefined;
          if (!checkpoint) {
            checkpoint =
              checkpointManager.findCheckpointByUserMessage(content) ??
              undefined;
          }
        }

        const userMsg: IUserUIMessage = {
          id: messageId,
          type: 'user',
          timestamp,
          content,
          checkpoint
        };
        uiMessages.push(userMsg);
      }
      lastRole = 'user';
    } else if (msg.role === 'assistant') {
      // Handle assistant messages
      if (typeof msg.content === 'string') {
        // Simple text content
        if (msg.content) {
          const assistantMsg: IAssistantUIMessage = {
            id: messageId,
            type: 'assistant',
            timestamp,
            content: msg.content,
            showHeader: lastRole === 'user'
          };
          uiMessages.push(assistantMsg);
        }
      } else if (Array.isArray(msg.content)) {
        // Content blocks (may contain text and tool_use)
        // IMPORTANT: Process blocks in order to preserve the sequence:
        // text -> tool_call -> text (not accumulate all text first)
        let pendingText = '';
        let textBlockIndex = 0;
        let shownHeader = false;

        const flushPendingText = () => {
          if (pendingText) {
            const assistantMsg: IAssistantUIMessage = {
              id: `${messageId}_text_${textBlockIndex++}`,
              type: 'assistant',
              timestamp,
              content: pendingText,
              showHeader: !shownHeader && lastRole === 'user'
            };
            uiMessages.push(assistantMsg);
            shownHeader = true;
            pendingText = '';
          }
        };

        for (const block of msg.content) {
          if (block.type === 'text' && block.text) {
            // Accumulate consecutive text blocks
            pendingText += block.text;
          } else if (
            block.type === 'tool_use' ||
            block.type === 'server_tool_use'
          ) {
            // Flush any pending text before adding tool call
            flushPendingText();

            // Skip wait_user_reply tool calls - they are handled by the WaitingUserReplyBox
            if (block.name === 'notebook-wait_user_reply') {
              continue;
            }

            // Look up the tool result for this tool call
            const result = toolResultMap.get(block.id);
            const hasResult = result !== undefined;
            const isToolSearch = isToolSearchTool(block.name);
            const isMCP = isMCPTool(block.name);

            const toolCallMsg: IToolCallUIMessage = {
              id: `${messageId}_tool_${block.id}`,
              type: 'tool_call',
              timestamp,
              toolName: block.name,
              toolInput: block.input || {},
              toolCallId: block.id,
              isStreaming: false,
              hasResult: hasResult,
              result: result,
              // Populate toolSearchResult for tool search and MCP tools
              toolSearchResult:
                (isToolSearch || isMCP) && hasResult
                  ? { input: block.input || {}, result }
                  : undefined
            };
            uiMessages.push(toolCallMsg);
          }
        }

        // Flush any remaining text
        flushPendingText();
      }
      lastRole = 'assistant';
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } else if ((msg as any).role === 'diff_approval') {
      // Handle diff approval messages from history
      if (
        Array.isArray(msg.content) &&
        (msg.content[0] as any)?.type === 'diff_approval'
      ) {
        const diffContent = msg.content[0] as any;
        const diffCells: IDiffCellUI[] = (diffContent.diff_cells || []).map(
          (cell: any) => ({
            cellId: cell.cellId,
            type: cell.type,
            originalContent: cell.originalContent || '',
            newContent: cell.newContent || '',
            displaySummary: cell.displaySummary || `${cell.type} cell`
          })
        );

        const diffMsg: IDiffApprovalUIMessage = {
          id: diffContent.id || `msg_restored_diff_${i}_${Date.now()}`,
          type: 'diff_approval',
          timestamp,
          notebookPath: diffContent.notebook_path,
          diffCells,
          isHistorical: true // Historical diffs are always non-interactive
        };
        uiMessages.push(diffMsg);
      }
    }
  }

  return uiMessages;
}

/**
 * Find the last wait_user_reply tool call in a thread and show the waiting reply box
 * This is called after loading a thread to restore the waiting reply UI state
 * Only shows if the user hasn't already replied after the wait_user_reply
 */
async function showLastWaitUserReplyPrompts(
  llmMessages: IChatMessage[]
): Promise<void> {
  // Find the last wait_user_reply tool call
  let waitUserReplyIndex = -1;
  let prompts: string[] = [];

  for (let i = llmMessages.length - 1; i >= 0; i--) {
    const msg = llmMessages[i];
    if (msg.role === 'assistant' && Array.isArray(msg.content)) {
      for (const block of msg.content) {
        if (
          (block.type === 'tool_use' || block.type === 'server_tool_use') &&
          block.name === 'notebook-wait_user_reply'
        ) {
          // Found the last wait_user_reply
          waitUserReplyIndex = i;
          prompts =
            block.input?.recommended_next_prompts ||
            block.input?.prompt_buttons ||
            [];
          break;
        }
      }
    }
    if (waitUserReplyIndex >= 0) break;
  }

  // If we didn't find a wait_user_reply, nothing to do
  if (waitUserReplyIndex < 0) {
    return;
  }

  // Check if user has already replied after the wait_user_reply tool call
  for (let i = waitUserReplyIndex + 1; i < llmMessages.length; i++) {
    const msg = llmMessages[i];
    // Check for non-hidden user messages with actual text content (not tool_result)
    if (
      msg.role === 'user' &&
      !msg.hidden &&
      typeof msg.content === 'string' &&
      msg.content.trim().length > 0
    ) {
      console.log(
        '[ChatHistoryStore] User already replied after wait_user_reply at index',
        i,
        '- not showing waiting reply box'
      );
      return;
    }
  }

  // User hasn't replied yet, show the waiting reply box
  // Skip if demo is actively running - demo handles its own flow
  if (getIsDemoActivelyRunning()) {
    console.log(
      '[ChatHistoryStore] Skipping waiting reply box - demo is actively running'
    );
    return;
  }

  console.log(
    '[ChatHistoryStore] Found last wait_user_reply, showing prompts:',
    prompts
  );

  // Use setTimeout to ensure the messages are loaded first
  setTimeout(() => {
    // Double-check demo state in case it changed
    if (getIsDemoActivelyRunning()) {
      console.log('[ChatHistoryStore] Skipping show in timeout - demo started');
      return;
    }
    useWaitingReplyStore.getState().show(prompts);
  }, 100);
}

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Thread summary for display in UI
 */
export interface IThreadSummary {
  id: string;
  name: string;
  lastUpdated: number;
  messageCount?: number;
  preview?: string;
}

/**
 * Chat history state
 */
export interface IChatHistoryState {
  // Thread list
  threads: IThreadSummary[];
  currentThreadId: string | null;
  currentThreadName: string;

  // Loading state
  isLoadingThreads: boolean;
  isLoadingHistory: boolean;

  // Persistence
  lastSavedAt: number | null;
  hasUnsavedChanges: boolean;
}

/**
 * Chat history actions
 */
export interface IChatHistoryActions {
  // Thread list management
  setThreads: (threads: IThreadSummary[]) => void;
  addThread: (thread: IThreadSummary) => void;
  removeThread: (threadId: string) => void;
  updateThread: (threadId: string, updates: Partial<IThreadSummary>) => void;
  loadThreads: (notebookId: string) => Promise<void>;

  // Thread selection
  selectThread: (threadId: string) => Promise<void>;
  setCurrentThreadId: (threadId: string | null) => void;
  setCurrentThreadName: (name: string) => void;

  // Loading state
  setLoadingThreads: (loading: boolean) => void;
  setLoadingHistory: (loading: boolean) => void;

  // Persistence
  markSaved: () => void;
  markUnsaved: () => void;

  // Reset
  reset: () => void;
  clearForNotebook: () => void;
  clearHistory: () => void;

  // Sync
  syncFromManager: () => Promise<void>;
}

type IChatHistoryStore = IChatHistoryState & IChatHistoryActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IChatHistoryState = {
  threads: [],
  currentThreadId: null,
  currentThreadName: 'New Chat',
  isLoadingThreads: false,
  isLoadingHistory: false,
  lastSavedAt: null,
  hasUnsavedChanges: false
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatHistoryStore = create<IChatHistoryStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Thread List Management
      // ─────────────────────────────────────────────────────────────

      setThreads: (threads: IThreadSummary[]) => {
        set({ threads }, false, 'setThreads');
      },

      addThread: (thread: IThreadSummary) => {
        set(
          state => ({
            threads: [...state.threads, thread]
          }),
          false,
          'addThread'
        );
      },

      removeThread: (threadId: string) => {
        set(
          state => ({
            threads: state.threads.filter(t => t.id !== threadId),
            // If removed thread was current, clear selection
            currentThreadId:
              state.currentThreadId === threadId ? null : state.currentThreadId,
            currentThreadName:
              state.currentThreadId === threadId
                ? 'New Chat'
                : state.currentThreadName
          }),
          false,
          'removeThread'
        );
      },

      updateThread: (threadId: string, updates: Partial<IThreadSummary>) => {
        set(
          state => ({
            threads: state.threads.map(t =>
              t.id === threadId ? { ...t, ...updates } : t
            ),
            // Update current thread name if it's the one being updated
            currentThreadName:
              state.currentThreadId === threadId && updates.name
                ? updates.name
                : state.currentThreadName
          }),
          false,
          'updateThread'
        );
      },

      loadThreads: async (notebookId: string) => {
        startTimer('ChatHistory.loadThreads.TOTAL');

        // IMMEDIATELY clear messages AND threads BEFORE any async work
        // This ensures the UI shows empty state instantly on notebook switch
        startTimer('ChatHistory.loadThreads.clearMessages');
        useChatMessagesStore.getState().clearMessages();
        endTimer('ChatHistory.loadThreads.clearMessages');

        startTimer('ChatHistory.loadThreads.setInitialState');
        set(
          {
            threads: [], // Clear threads immediately too
            currentThreadId: null,
            currentThreadName: 'New Chat',
            isLoadingThreads: true,
            isLoadingHistory: true
          },
          false,
          'loadThreads:start'
        );
        endTimer('ChatHistory.loadThreads.setInitialState');

        try {
          console.log(
            '[ChatHistoryStore] Loading threads for notebook:',
            notebookId
          );

          // Import chatboxStore to get chatHistoryManager
          startTimer('ChatHistory.loadThreads.importChatboxStore');
          const { useChatboxStore } = await import('./chatboxStore');
          endTimer('ChatHistory.loadThreads.importChatboxStore');

          // Reset isProcessingMessage flag on page load - it shouldn't be true when restoring history
          useChatboxStore.getState().setIsProcessingMessage(false);

          let chatHistoryManager =
            useChatboxStore.getState().services.chatHistoryManager;

          // Retry a few times if chatHistoryManager isn't available yet (race condition safety)
          if (!chatHistoryManager) {
            for (let i = 0; i < 5; i++) {
              await new Promise(resolve => setTimeout(resolve, 100));
              chatHistoryManager =
                useChatboxStore.getState().services.chatHistoryManager;
              if (chatHistoryManager) break;
            }
          }

          if (!chatHistoryManager) {
            console.warn(
              '[ChatHistoryStore] ChatHistoryManager not available after retries'
            );
            set(
              { isLoadingThreads: false, isLoadingHistory: false, threads: [] },
              false,
              'loadThreads:noManager'
            );
            return;
          }

          // Load threads from ChatHistoryManager
          startTimer('ChatHistory.loadThreads.setCurrentNotebook');
          await chatHistoryManager.setCurrentNotebook(notebookId);
          endTimer('ChatHistory.loadThreads.setCurrentNotebook');

          startTimer('ChatHistory.loadThreads.getThreads');
          const rawThreads =
            chatHistoryManager.getThreadsForNotebook(notebookId) || [];

          // Convert to thread summaries
          const threads: IThreadSummary[] = rawThreads.map((thread: any) => ({
            id: thread.id,
            name: thread.name || 'Untitled Chat',
            lastUpdated: thread.lastUpdated || Date.now(),
            messageCount: thread.messages?.length || 0,
            preview: thread.messages?.[0]?.content?.substring(0, 50) || ''
          }));

          // Get current thread (ChatHistoryManager restores the last selected thread from localStorage)
          const currentThread = chatHistoryManager.getCurrentThread();
          endTimer('ChatHistory.loadThreads.getThreads');

          console.log(
            '[ChatHistoryStore] Current thread after setCurrentNotebook:',
            {
              threadId: currentThread?.id,
              threadName: currentThread?.name,
              messageCount: currentThread?.messages?.length || 0
            }
          );

          set(
            {
              threads,
              currentThreadId: currentThread?.id || null,
              currentThreadName: currentThread?.name || 'New Chat',
              isLoadingThreads: false,
              isLoadingHistory: false
            },
            false,
            'loadThreads:complete'
          );

          console.log(`[ChatHistoryStore] Loaded ${threads.length} threads`);

          // Load the current thread's messages into the chat UI
          if (
            currentThread &&
            currentThread.messages &&
            currentThread.messages.length > 0
          ) {
            startTimer('ChatHistory.loadThreads.loadCurrentThreadMessages');
            const { useChatUIStore } = await import('./chatUIStore');

            const llmHistory = currentThread.messages || [];
            const contexts = currentThread.contexts || new Map();
            const timestamps = currentThread.message_timestamps || new Map();

            // Load checkpoints from backend before converting messages
            const checkpointManager = CheckpointManager.getInstance();
            checkpointManager.setCurrentNotebookId(notebookId);
            await checkpointManager.loadCheckpointsForNotebook(notebookId);

            // Convert LLM messages to UI messages (with checkpoint lookup)
            startTimer('ChatHistory.loadThreads.convertMessages');
            const uiMessages = convertLlmMessagesToUiMessages(
              llmHistory,
              timestamps,
              checkpointManager
            );
            endTimer('ChatHistory.loadThreads.convertMessages');

            console.log('[ChatHistoryStore] Loading last thread messages:', {
              threadId: currentThread.id,
              uiMessageCount: uiMessages.length
            });

            startTimer('ChatHistory.loadThreads.loadFromThread');
            useChatMessagesStore
              .getState()
              .loadFromThread(
                uiMessages,
                llmHistory,
                contexts,
                currentThread.id
              );
            endTimer('ChatHistory.loadThreads.loadFromThread');

            // Show waiting reply box if the last message was a wait_user_reply
            void showLastWaitUserReplyPrompts(llmHistory);

            // Hide the new chat display since we have messages
            if (uiMessages.length > 0) {
              useChatUIStore.getState().setShowNewChatDisplay(false);
            }

            // Auto-continue conversation if the thread ends with an open_notebook tool result
            // This happens when a notebook is opened from the launcher and the conversation should continue
            const lastMessage = llmHistory[llmHistory.length - 1];
            if (
              lastMessage?.role === 'user' &&
              Array.isArray(lastMessage.content)
            ) {
              const hasOpenNotebookResult = lastMessage.content.some(
                (block: any) =>
                  block.type === 'tool_result' &&
                  block.content?.includes?.('Opened notebook')
              );
              if (hasOpenNotebookResult) {
                // Use thread ID to prevent duplicate auto-continuations
                const threadIdForContinuation = currentThread.id;
                const autoContinuationKey = `auto_continuation_${threadIdForContinuation}`;

                // Check if we've already triggered auto-continuation for this thread
                if ((window as any)[autoContinuationKey]) {
                  console.log(
                    '[ChatHistoryStore] Auto-continuation already triggered for this thread, skipping'
                  );
                } else {
                  // Mark this thread as having triggered auto-continuation
                  (window as any)[autoContinuationKey] = true;

                  console.log(
                    '[ChatHistoryStore] Thread ends with open_notebook result - auto-continuing conversation'
                  );

                  // First, stop any running agent immediately
                  const { useChatboxStore } = await import('./chatboxStore');
                  const chatboxState = useChatboxStore.getState();

                  if (chatboxState.isProcessingMessage) {
                    console.log(
                      '[ChatHistoryStore] Stopping running agent before continuation'
                    );
                    chatboxState.cancelMessage();

                    // Wait for agent to fully stop (poll until isProcessingMessage is false)
                    await new Promise<void>(resolve => {
                      const checkStopped = () => {
                        if (!useChatboxStore.getState().isProcessingMessage) {
                          console.log(
                            '[ChatHistoryStore] Agent fully stopped'
                          );
                          resolve();
                        } else {
                          setTimeout(checkStopped, 100);
                        }
                      };
                      checkStopped();
                    });
                  }

                  // Use a 3 second delay to ensure all state is settled before continuing
                  // This prevents duplicate agents and race conditions during the launcher -> notebook swap
                  setTimeout(async () => {
                    const { services, isProcessingMessage } =
                      useChatboxStore.getState();
                    if (!isProcessingMessage && services.conversationService) {
                      console.log(
                        '[ChatHistoryStore] Triggering auto-continuation'
                      );
                      await services.conversationService.processConversation(
                        [],
                        [],
                        'agent'
                      );
                    } else {
                      console.log(
                        '[ChatHistoryStore] Skipping auto-continuation - already processing or no service'
                      );
                    }
                    // Clear the flag after continuation is triggered
                    delete (window as any)[autoContinuationKey];
                  }, 3000);
                }
              }
            }

            endTimer('ChatHistory.loadThreads.loadCurrentThreadMessages');
          } else if (currentThread) {
            // Thread exists but has no messages (new chat) -
            // still set currentThreadId so checkpoints can be created
            console.log(
              '[ChatHistoryStore] Empty thread - setting currentThreadId on chatMessagesStore:',
              currentThread.id
            );
            useChatMessagesStore.getState().setCurrentThreadId(currentThread.id);
          }
          endTimer('ChatHistory.loadThreads.TOTAL');
        } catch (error) {
          endTimer('ChatHistory.loadThreads.TOTAL');
          console.error('[ChatHistoryStore] Failed to load threads:', error);
          set(
            { isLoadingThreads: false, isLoadingHistory: false },
            false,
            'loadThreads:error'
          );
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Thread Selection
      // ─────────────────────────────────────────────────────────────

      selectThread: async (threadId: string) => {
        const { threads } = get();
        const thread = threads.find(t => t.id === threadId);

        console.log('[ChatHistoryStore] selectThread:', threadId);

        set(
          {
            currentThreadId: threadId,
            currentThreadName: thread?.name || 'New Chat'
          },
          false,
          'selectThread'
        );

        // Load messages from ChatHistoryManager into chatMessagesStore
        try {
          const { useChatboxStore } = await import('./chatboxStore');
          const { useChatUIStore } = await import('./chatUIStore');

          const chatHistoryManager =
            useChatboxStore.getState().services.chatHistoryManager;
          if (!chatHistoryManager) {
            console.warn(
              '[ChatHistoryStore] selectThread: chatHistoryManager not available'
            );
            return;
          }

          // Switch to the thread in ChatHistoryManager
          chatHistoryManager.switchToThread(threadId);
          const threadData = chatHistoryManager.getCurrentThread();

          if (threadData) {
            const llmHistory = threadData.messages || [];
            const contexts = threadData.contexts || new Map();
            const timestamps = threadData.message_timestamps || new Map();

            console.log('[ChatHistoryStore] Loading thread messages:', {
              threadId,
              messageCount: llmHistory.length
            });

            // Load checkpoints from backend before converting messages
            const currentNotebookId =
              useChatboxStore.getState().currentNotebookId;
            let checkpointManager: CheckpointManager | undefined;
            if (currentNotebookId) {
              checkpointManager = CheckpointManager.getInstance();
              checkpointManager.setCurrentNotebookId(currentNotebookId);
              await checkpointManager.loadCheckpointsForNotebook(
                currentNotebookId
              );
            }

            // Convert LLM messages to UI messages (with checkpoint lookup)
            const uiMessages = convertLlmMessagesToUiMessages(
              llmHistory,
              timestamps,
              checkpointManager
            );

            console.log(
              '[ChatHistoryStore] Converted to UI messages:',
              uiMessages.length
            );

            useChatMessagesStore
              .getState()
              .loadFromThread(uiMessages, llmHistory, contexts, threadId);

            // Show waiting reply box if the last message was a wait_user_reply
            void showLastWaitUserReplyPrompts(llmHistory);

            // Hide the new chat display if we have messages
            if (uiMessages.length > 0) {
              useChatUIStore.getState().setShowNewChatDisplay(false);
            }
          } else {
            console.warn(
              '[ChatHistoryStore] selectThread: thread data not found'
            );
          }
        } catch (error) {
          console.error(
            '[ChatHistoryStore] Failed to load thread messages:',
            error
          );
        }
      },

      setCurrentThreadId: (threadId: string | null) => {
        const { threads } = get();
        const thread = threadId ? threads.find(t => t.id === threadId) : null;

        set(
          {
            currentThreadId: threadId,
            currentThreadName: thread?.name || 'New Chat'
          },
          false,
          'setCurrentThreadId'
        );
      },

      setCurrentThreadName: (name: string) => {
        set({ currentThreadName: name }, false, 'setCurrentThreadName');
      },

      // ─────────────────────────────────────────────────────────────
      // Loading State
      // ─────────────────────────────────────────────────────────────

      setLoadingThreads: (loading: boolean) => {
        set({ isLoadingThreads: loading }, false, 'setLoadingThreads');
      },

      setLoadingHistory: (loading: boolean) => {
        set({ isLoadingHistory: loading }, false, 'setLoadingHistory');
      },

      // ─────────────────────────────────────────────────────────────
      // Persistence
      // ─────────────────────────────────────────────────────────────

      markSaved: () => {
        set(
          {
            lastSavedAt: Date.now(),
            hasUnsavedChanges: false
          },
          false,
          'markSaved'
        );
      },

      markUnsaved: () => {
        set({ hasUnsavedChanges: true }, false, 'markUnsaved');
      },

      // ─────────────────────────────────────────────────────────────
      // Reset
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set({ ...initialState }, false, 'reset');
      },

      clearForNotebook: () => {
        set(
          {
            threads: [],
            currentThreadId: null,
            currentThreadName: 'New Chat',
            hasUnsavedChanges: false
          },
          false,
          'clearForNotebook'
        );
      },

      clearHistory: () => {
        set(
          {
            threads: [],
            currentThreadId: null,
            currentThreadName: 'New Chat',
            hasUnsavedChanges: false,
            lastSavedAt: null
          },
          false,
          'clearHistory'
        );
      },

      /**
       * Sync threads from ChatHistoryManager - call this after any thread operation
       * to ensure Zustand store matches the service
       */
      syncFromManager: async () => {
        try {
          const { useChatboxStore } = await import('./chatboxStore');
          const chatHistoryManager =
            useChatboxStore.getState().services.chatHistoryManager;

          if (!chatHistoryManager) {
            console.warn(
              '[ChatHistoryStore] syncFromManager: No ChatHistoryManager available'
            );
            return;
          }

          const notebookId = useChatboxStore.getState().currentNotebookId;
          if (!notebookId) {
            console.warn('[ChatHistoryStore] syncFromManager: No notebook ID');
            return;
          }

          const rawThreads =
            chatHistoryManager.getThreadsForNotebook(notebookId) || [];
          const currentThread = chatHistoryManager.getCurrentThread();

          const threads: IThreadSummary[] = rawThreads.map((thread: any) => ({
            id: thread.id,
            name: thread.name || 'Untitled Chat',
            lastUpdated: thread.lastUpdated || Date.now(),
            messageCount: thread.messages?.length || 0,
            preview: thread.messages?.[0]?.content?.substring(0, 50) || ''
          }));

          console.log('[ChatHistoryStore] syncFromManager:', {
            threadCount: threads.length,
            currentThreadId: currentThread?.id,
            currentThreadName: currentThread?.name
          });

          set(
            {
              threads,
              currentThreadId: currentThread?.id || null,
              currentThreadName: currentThread?.name || 'New Chat'
            },
            false,
            'syncFromManager'
          );
        } catch (error) {
          console.error('[ChatHistoryStore] syncFromManager error:', error);
        }
      }
    })),
    { name: 'ChatHistoryStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectThreads = (state: IChatHistoryStore) => state.threads;
export const selectCurrentThreadId = (state: IChatHistoryStore) =>
  state.currentThreadId;
export const selectCurrentThreadName = (state: IChatHistoryStore) =>
  state.currentThreadName;
export const selectIsLoadingThreads = (state: IChatHistoryStore) =>
  state.isLoadingThreads;
export const selectIsLoadingHistory = (state: IChatHistoryStore) =>
  state.isLoadingHistory;
export const selectHasUnsavedChanges = (state: IChatHistoryStore) =>
  state.hasUnsavedChanges;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getChatHistoryState = () => useChatHistoryStore.getState();

/**
 * Subscribe to thread list changes
 */
export const subscribeToThreadList = (
  callback: (threads: IThreadSummary[]) => void
) => {
  return useChatHistoryStore.subscribe(state => state.threads, callback);
};

/**
 * Subscribe to current thread changes
 */
export const subscribeToCurrentThread = (
  callback: (threadId: string | null, name: string) => void
) => {
  return useChatHistoryStore.subscribe(
    state => ({ id: state.currentThreadId, name: state.currentThreadName }),
    ({ id, name }) => callback(id, name)
  );
};

/**
 * Subscribe to loading state
 */
export const subscribeToHistoryLoading = (
  callback: (loading: boolean) => void
) => {
  return useChatHistoryStore.subscribe(
    state => state.isLoadingHistory,
    callback
  );
};

// ═══════════════════════════════════════════════════════════════
// AUTO-CLEAR ON NOTEBOOK CHANGE
// ═══════════════════════════════════════════════════════════════

/**
 * Set up notebook change subscription to clear state immediately.
 * This MUST be called early in app initialization to ensure the
 * subscription is ready before any notebook changes.
 */
export function initChatHistoryNotebookSubscription(): void {
  // Dynamically import to avoid circular dependency
  import('./notebookEventsStore').then(({ subscribeToNotebookChange }) => {
    subscribeToNotebookChange(({ newNotebookId, oldNotebookId }) => {
      if (newNotebookId && newNotebookId !== oldNotebookId) {
        startTimer('ChatHistorySubscription.onNotebookChange');
        console.log(
          '[ChatHistoryStore] Notebook changed, clearing state immediately'
        );
        // Clear threads and messages synchronously
        useChatMessagesStore.getState().clearMessages();
        useChatHistoryStore.setState({
          threads: [],
          currentThreadId: null,
          currentThreadName: 'New Chat',
          isLoadingThreads: true,
          isLoadingHistory: true
        });
        endTimer('ChatHistorySubscription.onNotebookChange');
      }
    });
    console.log('[ChatHistoryStore] Notebook change subscription initialized');
  });
}

// Auto-initialize the subscription when module loads
initChatHistoryNotebookSubscription();
