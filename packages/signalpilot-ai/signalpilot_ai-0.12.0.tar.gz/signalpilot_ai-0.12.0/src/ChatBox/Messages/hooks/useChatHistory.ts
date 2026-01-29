/**
 * useChatHistory Hook
 *
 * Manages the synchronization between:
 * - UI messages (what's displayed)
 * - LLM history (what's sent to the API)
 * - Persistent storage (ChatHistoryManager)
 *
 * Also handles thread operations like loading from saved threads.
 *
 * @example
 * ```tsx
 * const {
 *   addUserMessage,
 *   addAssistantMessage,
 *   loadThread,
 *   getLlmHistory
 * } = useChatHistory(historyManager);
 *
 * // Add a message (updates both UI and LLM history)
 * addUserMessage('Hello', checkpoint);
 *
 * // Load a saved thread
 * await loadThread(savedThread);
 * ```
 */

import { useCallback, useEffect, useRef } from 'react';
import { IChatMessage, ICheckpoint } from '@/types';
import {
  ChatHistoryManager,
  IChatThread
} from '@/ChatBox/services/ChatHistoryManager';
import {
  ChatUIMessage,
  IAssistantUIMessage,
  IDiffApprovalUIMessage,
  IDiffCellUI,
  IToolCallUIMessage,
  IUserUIMessage,
  useChatMessagesStore
} from '@/stores/chatMessages';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { isToolSearchTool, isMCPTool } from '@/utils/toolDisplay';
import { useWaitingReplyStore } from '@/stores/waitingReplyStore';
import { getIsDemoActivelyRunning } from '@/Demo/demo';

export interface UseChatHistoryOptions {
  /** Chat history manager for persistence */
  historyManager: ChatHistoryManager;
  /** Auto-persist changes to storage */
  autoPersist?: boolean;
}

export interface UseChatHistoryResult {
  /** Add a user message to both UI and LLM history */
  addUserMessage: (
    content: string,
    checkpoint?: ICheckpoint,
    options?: { hidden?: boolean }
  ) => string;
  /** Add an assistant message to both UI and LLM history */
  addAssistantMessage: (content: string, showHeader?: boolean) => string;
  /** Add tool calls to both UI and LLM history */
  addToolCalls: (
    toolCalls: Array<{ name: string; id: string; input: any }>
  ) => string[];
  /** Add a tool result */
  addToolResult: (
    toolName: string,
    toolUseId: string,
    result: any,
    toolCallData: any
  ) => string;
  /** Add a diff approval record */
  addDiffApproval: (notebookPath?: string, diffCells?: IDiffCellUI[]) => string;
  /** Load from a saved thread */
  loadThread: (thread: IChatThread) => Promise<void>;
  /** Get current LLM history */
  getLlmHistory: () => IChatMessage[];
  /** Get current thread ID */
  currentThreadId: string | null;
  /** Generate thread name from message */
  generateThreadName: (message: string) => string;
  /** Rename current thread */
  renameThread: (name: string) => void;
  /** Persist current state to storage */
  persistToStorage: () => void;
}

/** Generate unique message ID */
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

export function useChatHistory(
  options: UseChatHistoryOptions
): UseChatHistoryResult {
  const { historyManager, autoPersist = true } = options;

  // Ref to track if we should auto-persist
  const shouldPersistRef = useRef(false);

  // Store actions
  const store = useChatMessagesStore();

  /**
   * Generate a thread name from first message
   */
  const generateThreadName = useCallback((message: string): string => {
    // Remove context tags
    const processed = message
      .replace(/<[^>]*_CONTEXT>[^<]*<\/[^>]*_CONTEXT>/gi, '')
      .trim();

    const words = processed.split(/\s+/);
    const selected = words.slice(0, Math.min(8, words.length));
    let name = selected.join(' ');

    if (name.length > 30) {
      name = name.substring(0, 27) + '...';
    }

    return name || 'New Chat';
  }, []);

  /**
   * Persist current state to storage
   */
  const persistToStorage = useCallback(() => {
    const { llmHistory, mentionContexts } = store;
    historyManager.updateCurrentThreadMessages(llmHistory, mentionContexts);
  }, [historyManager, store]);

  /**
   * Add a user message
   */
  const addUserMessage = useCallback(
    (
      content: string,
      checkpoint?: ICheckpoint,
      options?: { hidden?: boolean }
    ): string => {
      // Add to UI messages
      const uiId = store.addUserMessage(content, checkpoint, options);

      // Add to LLM history
      const llmMessage: IChatMessage = {
        role: 'user',
        content,
        id: uiId,
        hidden: options?.hidden
      };
      store.addToLlmHistory(llmMessage);

      // Auto-persist
      if (autoPersist) {
        shouldPersistRef.current = true;
      }

      // Auto-rename thread if first non-hidden message
      const currentThread = historyManager.getCurrentThread();
      if (currentThread?.name === 'New Chat' && !options?.hidden) {
        const visibleUserMessages = store.llmHistory.filter(
          msg => msg.role === 'user' && !msg.hidden
        ).length;
        // +1 because we just added one
        if (visibleUserMessages === 0) {
          const threadName = generateThreadName(content);
          historyManager.renameCurrentThread(threadName);
          // Sync Zustand from ChatHistoryManager (single source of truth)
          void useChatHistoryStore.getState().syncFromManager();
        }
      }

      return uiId;
    },
    [store, historyManager, autoPersist, generateThreadName]
  );

  /**
   * Add an assistant message
   */
  const addAssistantMessage = useCallback(
    (content: string, showHeader?: boolean): string => {
      // Add to UI messages
      const uiId = store.addAssistantMessage(content, showHeader);

      // Add to LLM history
      const llmMessage: IChatMessage = {
        role: 'assistant',
        content,
        id: uiId
      };
      store.addToLlmHistory(llmMessage);

      // Auto-persist
      if (autoPersist) {
        shouldPersistRef.current = true;
      }

      return uiId;
    },
    [store, autoPersist]
  );

  /**
   * Add tool calls
   */
  const addToolCalls = useCallback(
    (toolCalls: Array<{ name: string; id: string; input: any }>): string[] => {
      const uiIds: string[] = [];

      // Add to UI messages (one per tool call)
      for (const toolCall of toolCalls) {
        const uiId = store.addToolCall(
          toolCall.name,
          toolCall.input,
          toolCall.id
        );
        uiIds.push(uiId);
      }

      // Add to LLM history (as single message with all tool uses)
      const llmMessage: IChatMessage = {
        role: 'assistant',
        content: toolCalls.map(tc => ({
          type: 'tool_use',
          id: tc.id,
          name: tc.name,
          input: tc.input
        }))
      };
      store.addToLlmHistory(llmMessage);

      // Auto-persist
      if (autoPersist) {
        shouldPersistRef.current = true;
      }

      return uiIds;
    },
    [store, autoPersist]
  );

  /**
   * Add a tool result
   */
  const addToolResult = useCallback(
    (
      toolName: string,
      toolUseId: string,
      result: any,
      toolCallData: any
    ): string => {
      // Check for errors
      let hasError = false;
      try {
        if (typeof result === 'string') {
          const parsed = JSON.parse(result);
          hasError = parsed?.error === true;
        }
      } catch {
        // Not JSON, not an error
      }

      // Add to UI messages
      const uiId = store.addToolResult(
        toolName,
        toolUseId,
        result,
        toolCallData,
        hasError
      );

      // Add to LLM history
      const llmMessage: IChatMessage = {
        role: 'user',
        content: [
          {
            type: 'tool_result',
            tool_use_id: toolUseId,
            content: result
          }
        ]
      };
      store.addToLlmHistory(llmMessage);

      // Auto-persist
      if (autoPersist) {
        shouldPersistRef.current = true;
      }

      return uiId;
    },
    [store, autoPersist]
  );

  /**
   * Add a diff approval record
   */
  const addDiffApproval = useCallback(
    (notebookPath?: string, diffCells?: IDiffCellUI[]): string => {
      // Add to UI messages
      const uiId = store.addDiffApproval(notebookPath, diffCells, false);

      // Add to LLM history (as special message type)
      const llmMessage: IChatMessage = {
        role: 'diff_approval' as any,
        content: [
          {
            type: 'diff_approval',
            id: uiId,
            timestamp: new Date().toISOString(),
            notebook_path: notebookPath,
            diff_cells: diffCells
          }
        ]
      };
      store.addToLlmHistory(llmMessage);

      // Auto-persist
      if (autoPersist) {
        shouldPersistRef.current = true;
      }

      return uiId;
    },
    [store, autoPersist]
  );

  /**
   * Load from a saved thread
   */
  const loadThread = useCallback(
    async (thread: IChatThread): Promise<void> => {
      // STEP 1: Build a map of tool_use_id → tool_result content
      // This allows us to correlate tool calls with their results
      const toolResultMap = new Map<string, any>();
      for (const msg of thread.messages) {
        if (msg.role === 'user' && Array.isArray(msg.content)) {
          for (const content of msg.content) {
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

      // STEP 2: Convert LLM messages to UI messages
      const uiMessages: ChatUIMessage[] = [];

      for (const msg of thread.messages) {
        if (msg.role === 'user') {
          // Skip tool results in UI (they're shown inline with tool calls)
          if (
            Array.isArray(msg.content) &&
            msg.content[0]?.type === 'tool_result'
          ) {
            continue;
          }

          const content =
            typeof msg.content === 'string'
              ? msg.content
              : msg.content[0]?.text || JSON.stringify(msg.content);

          const userMsg: IUserUIMessage = {
            id: msg.id || generateMessageId(),
            type: 'user',
            timestamp: Date.now(),
            content,
            hidden: msg.hidden
          };
          uiMessages.push(userMsg);
        } else if (msg.role === 'assistant') {
          // Process ALL content items in assistant messages
          // A message can have both text AND tool_use items
          if (Array.isArray(msg.content)) {
            for (const contentItem of msg.content) {
              if (contentItem.type === 'text' && contentItem.text) {
                // Text content - create assistant message
                const assistantMsg: IAssistantUIMessage = {
                  id: msg.id || generateMessageId(),
                  type: 'assistant',
                  timestamp: Date.now(),
                  content: contentItem.text,
                  showHeader: true
                };
                uiMessages.push(assistantMsg);
              } else if (
                contentItem.type === 'tool_use' ||
                contentItem.type === 'server_tool_use'
              ) {
                // Tool use - create tool call message
                const result = toolResultMap.get(contentItem.id);
                const hasResult = result !== undefined;

                const isToolSearch = isToolSearchTool(contentItem.name);
                const isMCP = isMCPTool(contentItem.name);

                const toolMsg: IToolCallUIMessage = {
                  id: generateMessageId(),
                  type: 'tool_call',
                  timestamp: Date.now(),
                  toolName: contentItem.name,
                  toolInput: contentItem.input,
                  toolCallId: contentItem.id,
                  isStreaming: false,
                  hasResult,
                  result,
                  toolSearchResult:
                    (isToolSearch || isMCP) && hasResult
                      ? { input: contentItem.input, result }
                      : undefined
                };
                uiMessages.push(toolMsg);
              }
            }
          } else if (typeof msg.content === 'string' && msg.content) {
            // Simple string content
            const assistantMsg: IAssistantUIMessage = {
              id: msg.id || generateMessageId(),
              type: 'assistant',
              timestamp: Date.now(),
              content: msg.content,
              showHeader: true
            };
            uiMessages.push(assistantMsg);
          }
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
              id: diffContent.id || generateMessageId(),
              type: 'diff_approval',
              timestamp: Date.now(),
              notebookPath: diffContent.notebook_path,
              diffCells,
              isHistorical: true // Historical diffs are always non-interactive
            };
            uiMessages.push(diffMsg);
          }
        }
      }

      // Load into store
      store.loadFromThread(
        uiMessages,
        thread.messages,
        thread.contexts || new Map(),
        thread.id
      );

      // STEP 3: Check if the conversation ended with an unanswered wait_user_reply
      // If so, restore the waiting reply box UI
      const lastToolCall = uiMessages
        .filter(msg => msg.type === 'tool_call')
        .pop() as IToolCallUIMessage | undefined;

      if (lastToolCall?.toolName === 'notebook-wait_user_reply') {
        // Check if there's a user message after this tool call in the original messages
        // Find the position of the wait_user_reply in the original messages
        let foundWaitUserReply = false;
        let hasUserResponseAfter = false;

        for (const msg of thread.messages) {
          if (msg.role === 'assistant' && Array.isArray(msg.content)) {
            for (const content of msg.content) {
              if (
                content.type === 'tool_use' &&
                content.name === 'notebook-wait_user_reply'
              ) {
                foundWaitUserReply = true;
              }
            }
          } else if (foundWaitUserReply && msg.role === 'user') {
            // Check if this is a real user message (not a tool_result)
            if (
              typeof msg.content === 'string' ||
              (Array.isArray(msg.content) &&
                msg.content[0]?.type !== 'tool_result')
            ) {
              hasUserResponseAfter = true;
              break;
            }
          }
        }

        // If we found wait_user_reply but no user response after, show the waiting reply box
        // Skip if demo is actively running - demo handles its own flow
        if (foundWaitUserReply && !hasUserResponseAfter) {
          if (getIsDemoActivelyRunning()) {
            console.log(
              '[useChatHistory] Skipping waiting reply box - demo is actively running'
            );
          } else {
            console.log(
              '[useChatHistory] Restoring waiting reply box from history'
            );
            // Extract recommended prompts from the tool input if available
            const prompts = lastToolCall.toolInput?.recommended_prompts || [
              'Continue'
            ];
            useWaitingReplyStore.getState().show(prompts);
          }
        }
      }
    },
    [store]
  );

  /**
   * Get LLM history
   */
  const getLlmHistory = useCallback((): IChatMessage[] => {
    return store.getLlmHistory();
  }, [store]);

  /**
   * Rename current thread
   */
  const renameThread = useCallback(
    (name: string) => {
      historyManager.renameCurrentThread(name);
      // Sync Zustand from ChatHistoryManager (single source of truth)
      void useChatHistoryStore.getState().syncFromManager();
    },
    [historyManager]
  );

  /**
   * Auto-persist effect (debounced)
   */
  useEffect(() => {
    if (!shouldPersistRef.current) return;

    const timeout = setTimeout(() => {
      persistToStorage();
      shouldPersistRef.current = false;
    }, 500);

    return () => clearTimeout(timeout);
  }, [store.llmHistory, store.mentionContexts, persistToStorage]);

  return {
    addUserMessage,
    addAssistantMessage,
    addToolCalls,
    addToolResult,
    addDiffApproval,
    loadThread,
    getLlmHistory,
    currentThreadId: store.currentThreadId,
    generateThreadName,
    renameThread,
    persistToStorage
  };
}

export default useChatHistory;
