/**
 * ChatMessages Store
 *
 * Main Zustand store for chat message state management.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import {
  IAssistantUIMessage,
  IChatMessagesStore,
  IDiffApprovalUIMessage,
  IErrorUIMessage,
  ILoadingUIMessage,
  ISystemUIMessage,
  IToolCallUIMessage,
  IToolResultUIMessage,
  IUserUIMessage
} from './types';

// Lazy import to avoid circular dependency
const getWaitingReplyStore = () =>
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  require('../waitingReplyStore').useWaitingReplyStore;

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

/** Generate a unique message ID */
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatMessagesStore = create<IChatMessagesStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      messages: [],
      llmHistory: [],
      streaming: {
        isStreaming: false,
        text: '',
        messageId: null
      },
      isThinking: false,
      specialDisplay: 'none',
      lastMessageType: null,
      currentThreadId: null,
      mentionContexts: new Map(),
      scrollState: {
        isAtBottom: true,
        showScrollButton: false,
        scrollToBottomCounter: 0
      },
      checkpointToRestore: null,
      restoringCheckpointId: null,

      // ─────────────────────────────────────────────────────────────
      // Message Management Actions
      // ─────────────────────────────────────────────────────────────
      addUserMessage: (content, checkpoint, options) => {
        const id = generateMessageId();
        const message: IUserUIMessage = {
          id,
          type: 'user',
          timestamp: Date.now(),
          content,
          checkpoint,
          hidden: options?.hidden,
          isCollapsed: false
        };
        set(state => {
          // When adding a user message, also clean up any wait_user_reply tool calls
          // from previous turns since the user is now responding
          const filteredMessages = state.messages.filter(msg => {
            if (msg.type === 'tool_call') {
              const toolCall = msg as IToolCallUIMessage;
              if (toolCall.toolName === 'notebook-wait_user_reply') {
                console.log(
                  '[ChatMessagesStore] Removing wait_user_reply on new user message:',
                  msg.id
                );
                return false;
              }
            }
            return true;
          });

          return {
            messages: [...filteredMessages, message],
            lastMessageType: 'user',
            specialDisplay: 'none' // Clear any special display
          };
        });
        // Hide waiting reply box when user sends a message
        try {
          getWaitingReplyStore().getState().hide();
        } catch (e) {
          // Store may not be initialized yet during startup
        }
        return id;
      },

      addAssistantMessage: (content, showHeader = true) => {
        const id = generateMessageId();
        const message: IAssistantUIMessage = {
          id,
          type: 'assistant',
          timestamp: Date.now(),
          content,
          showHeader
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'assistant'
        }));
        return id;
      },

      addSystemMessage: content => {
        const id = generateMessageId();
        const message: ISystemUIMessage = {
          id,
          type: 'system',
          timestamp: Date.now(),
          content
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'system'
        }));
        return id;
      },

      addErrorMessage: content => {
        const id = generateMessageId();
        const message: IErrorUIMessage = {
          id,
          type: 'error',
          timestamp: Date.now(),
          content
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'error'
        }));
        return id;
      },

      addToolCall: (toolName, toolInput, toolCallId) => {
        // Skip wait_user_reply - it's handled separately by the waiting reply box
        if (toolName === 'notebook-wait_user_reply') {
          return '';
        }

        // DEDUPLICATION: Skip if toolCallId already exists in messages
        if (toolCallId) {
          const existingToolCall = get().messages.find(
            msg =>
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).toolCallId === toolCallId
          );
          if (existingToolCall) {
            return existingToolCall.id;
          }
        }

        const id = generateMessageId();
        const message: IToolCallUIMessage = {
          id,
          type: 'tool_call',
          timestamp: Date.now(),
          toolName,
          toolInput,
          toolCallId,
          isStreaming: true
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'tool_call'
        }));
        return id;
      },

      updateToolCall: (id, updates) => {
        set(state => ({
          messages: state.messages.map(msg =>
            msg.id === id && msg.type === 'tool_call'
              ? { ...msg, ...updates }
              : msg
          )
        }));
      },

      addToolResult: (toolName, toolUseId, result, toolCallData, hasError) => {
        // Find the existing tool_call message and update it with result
        // This avoids creating duplicate messages - one message per tool call
        const existingToolCall = get().messages.find(
          msg =>
            msg.type === 'tool_call' &&
            (msg as IToolCallUIMessage).toolCallId === toolUseId
        );

        if (existingToolCall) {
          // Update existing tool_call message with result data
          set(state => ({
            messages: state.messages.map(msg =>
              msg.id === existingToolCall.id && msg.type === 'tool_call'
                ? {
                    ...msg,
                    result,
                    toolCallData,
                    hasError,
                    hasResult: true,
                    isStreaming: false
                  }
                : msg
            )
          }));
          return existingToolCall.id;
        }

        // Fallback: create a new tool_result message if no matching tool_call found
        // This shouldn't happen in normal flow, but keeps backward compatibility
        const id = generateMessageId();
        const message: IToolResultUIMessage = {
          id,
          type: 'tool_result',
          timestamp: Date.now(),
          toolName,
          toolUseId,
          result,
          toolCallData,
          hasError
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'tool_result'
        }));
        return id;
      },

      addDiffApproval: (notebookPath, diffCells, isHistorical) => {
        console.log('[ChatMessagesStore] addDiffApproval called', {
          notebookPath,
          diffCellsCount: diffCells?.length,
          isHistorical
        });

        // DEDUPLICATION: For active (non-historical) diff approvals, replace any existing active one
        if (!isHistorical) {
          const existingActiveDiff = get().messages.find(
            msg =>
              msg.type === 'diff_approval' &&
              !(msg as IDiffApprovalUIMessage).isHistorical
          );
          if (existingActiveDiff) {
            console.log(
              '[ChatMessagesStore] Replacing existing active diff approval:',
              existingActiveDiff.id
            );
            // Remove the existing active diff before adding new one
            set(state => ({
              messages: state.messages.filter(
                msg => msg.id !== existingActiveDiff.id
              )
            }));
          }
        }

        const id = generateMessageId();
        const message: IDiffApprovalUIMessage = {
          id,
          type: 'diff_approval',
          timestamp: Date.now(),
          notebookPath,
          diffCells: diffCells || [],
          isHistorical
        };
        console.log('[ChatMessagesStore] Adding diff approval message:', {
          id,
          diffCellsLength: message.diffCells.length,
          isHistorical: message.isHistorical
        });
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'diff_approval'
        }));
        console.log(
          '[ChatMessagesStore] Messages after adding:',
          get().messages.length
        );
        return id;
      },

      addLoading: (text = 'Loading...') => {
        const id = generateMessageId();
        const message: ILoadingUIMessage = {
          id,
          type: 'loading',
          timestamp: Date.now(),
          text
        };
        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'loading'
        }));
        return id;
      },

      removeMessage: id => {
        set(state => ({
          messages: state.messages.filter(msg => msg.id !== id)
        }));
      },

      removeToolCallsByName: toolName => {
        console.log(
          '[ChatMessagesStore] Removing tool calls with name:',
          toolName
        );
        set(state => ({
          messages: state.messages.filter(msg => {
            if (msg.type === 'tool_call') {
              return (msg as IToolCallUIMessage).toolName !== toolName;
            }
            return true;
          })
        }));
      },

      clearMessages: () => {
        set({
          messages: [],
          llmHistory: [],
          lastMessageType: null,
          streaming: { isStreaming: false, text: '', messageId: null },
          isThinking: false,
          mentionContexts: new Map(),
          scrollState: {
            isAtBottom: true,
            showScrollButton: false,
            scrollToBottomCounter: 0
          }
        });
      },

      setMessages: messages => {
        set({
          messages,
          lastMessageType:
            messages.length > 0 ? messages[messages.length - 1].type : null
        });
      },

      markDiffApprovalHistorical: id => {
        console.log(
          '[ChatMessagesStore] Marking diff approval as historical:',
          id
        );
        set(state => ({
          messages: state.messages.map(msg => {
            if (msg.id === id && msg.type === 'diff_approval') {
              return { ...msg, isHistorical: true } as IDiffApprovalUIMessage;
            }
            return msg;
          })
        }));
      },

      updateDiffApprovalCells: (id, diffCells) => {
        console.log(
          '[ChatMessagesStore] Updating diff approval cells:',
          id,
          diffCells.length
        );
        set(state => ({
          messages: state.messages.map(msg => {
            if (msg.id === id && msg.type === 'diff_approval') {
              return { ...msg, diffCells } as IDiffApprovalUIMessage;
            }
            return msg;
          })
        }));
      },

      getActiveDiffApproval: () => {
        const { messages } = get();
        return (
          (messages.find(
            msg =>
              msg.type === 'diff_approval' &&
              !(msg as IDiffApprovalUIMessage).isHistorical
          ) as IDiffApprovalUIMessage) || null
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Streaming Actions
      // ─────────────────────────────────────────────────────────────
      startStreaming: () => {
        const messageId = generateMessageId();
        const { lastMessageType } = get();

        // Add assistant message to the array immediately so it appears before tool calls
        const message: IAssistantUIMessage = {
          id: messageId,
          type: 'assistant',
          timestamp: Date.now(),
          content: '', // Will be updated as text streams in
          showHeader: lastMessageType === 'user'
        };

        set(state => ({
          messages: [...state.messages, message],
          streaming: {
            isStreaming: true,
            text: '',
            messageId
          },
          isThinking: false, // Hide thinking when streaming starts
          lastMessageType: 'assistant'
        }));
        return messageId;
      },

      updateStreamingText: text => {
        const { streaming } = get();
        // Update both the streaming state and the message in the array
        set(state => ({
          streaming: { ...state.streaming, text },
          messages: state.messages.map(msg =>
            msg.id === streaming.messageId && msg.type === 'assistant'
              ? { ...msg, content: text }
              : msg
          )
        }));
      },

      appendStreamingText: text => {
        const { streaming } = get();
        const newText = streaming.text + text;
        // Update both the streaming state and the message in the array
        set(state => ({
          streaming: {
            ...state.streaming,
            text: newText
          },
          messages: state.messages.map(msg =>
            msg.id === streaming.messageId && msg.type === 'assistant'
              ? { ...msg, content: newText }
              : msg
          )
        }));
      },

      finalizeStreaming: () => {
        const { streaming } = get();
        if (streaming.isStreaming) {
          // Message is already in the array, just clear streaming state
          // If there's no text, remove the empty message
          if (!streaming.text && streaming.messageId) {
            set(state => ({
              messages: state.messages.filter(
                msg => msg.id !== streaming.messageId
              ),
              streaming: { isStreaming: false, text: '', messageId: null }
            }));
          } else {
            set({
              streaming: { isStreaming: false, text: '', messageId: null }
            });
          }
        } else {
          set({
            streaming: { isStreaming: false, text: '', messageId: null }
          });
        }
      },

      cancelStreaming: () => {
        set({
          streaming: { isStreaming: false, text: '', messageId: null }
        });
      },

      // ─────────────────────────────────────────────────────────────
      // Streaming Tool Call Actions (Unified with messages array)
      // ─────────────────────────────────────────────────────────────

      startStreamingToolCall: (toolCallId, toolName) => {
        // Skip wait_user_reply - it's handled separately by the waiting reply box
        if (toolName === 'notebook-wait_user_reply') {
          return '';
        }

        // Check if already exists in messages (avoid duplicates)
        const existing = get().messages.find(
          msg =>
            msg.type === 'tool_call' &&
            (msg as IToolCallUIMessage).toolCallId === toolCallId
        );
        if (existing) {
          console.log(
            '[ChatMessagesStore] Tool call already exists in messages:',
            toolCallId
          );
          return existing.id;
        }

        // Add to messages array with isStreaming: true
        const id = generateMessageId();
        const message: IToolCallUIMessage = {
          id,
          type: 'tool_call',
          timestamp: Date.now(),
          toolName,
          toolInput: {},
          toolCallId,
          isStreaming: true
        };

        console.log(
          '[ChatMessagesStore] startStreamingToolCall - Adding NEW tool call:',
          {
            messageId: id,
            toolCallId,
            toolName,
            currentMessageCount: get().messages.length
          }
        );

        set(state => ({
          messages: [...state.messages, message],
          lastMessageType: 'tool_call'
        }));

        console.log(
          '[ChatMessagesStore] Started streaming tool call in messages:',
          toolCallId
        );
        return id;
      },

      updateStreamingToolCall: (toolCallId, toolInput) => {
        set(state => {
          const existingIndex = state.messages.findIndex(
            msg =>
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).toolCallId === toolCallId
          );

          if (existingIndex === -1) {
            return state;
          }

          // Skip update if toolInput is undefined/null
          if (toolInput == null) {
            return state;
          }

          const messages = [...state.messages];
          const existing = messages[existingIndex] as IToolCallUIMessage;

          // Merge new toolInput with existing to preserve properties like cell_id
          const mergedToolInput = {
            ...existing.toolInput,
            ...toolInput
          };

          messages[existingIndex] = {
            ...existing,
            toolInput: mergedToolInput
          };

          return { messages };
        });
      },

      updateToolSearchResult: (toolCallId, input, result) => {
        set(state => {
          const existingIndex = state.messages.findIndex(
            msg =>
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).toolCallId === toolCallId
          );

          if (existingIndex === -1) {
            return state;
          }

          const messages = [...state.messages];
          const existing = messages[existingIndex] as IToolCallUIMessage;
          const updatedMessage = {
            ...existing,
            toolSearchResult: { input, result },
            isStreaming: false // Tool search is complete
          };
          messages[existingIndex] = updatedMessage;

          return { messages };
        });
      },

      finalizeStreamingToolCall: toolCallId => {
        set(state => {
          const existingIndex = state.messages.findIndex(
            msg =>
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).toolCallId === toolCallId
          );

          if (existingIndex === -1) {
            console.warn(
              '[ChatMessagesStore] finalizeStreamingToolCall: toolCallId not found in messages:',
              toolCallId
            );
            return state;
          }

          const messages = [...state.messages];
          const existing = messages[existingIndex] as IToolCallUIMessage;
          messages[existingIndex] = {
            ...existing,
            isStreaming: false
          };

          console.log(
            '[ChatMessagesStore] Finalized streaming tool call:',
            toolCallId
          );
          return { messages };
        });
      },

      cancelStreamingToolCall: toolCallId => {
        set(state => ({
          messages: state.messages.filter(
            msg =>
              !(
                msg.type === 'tool_call' &&
                (msg as IToolCallUIMessage).toolCallId === toolCallId
              )
          )
        }));
      },

      getStreamingToolCalls: () => {
        return get()
          .messages.filter(
            msg =>
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).isStreaming === true
          )
          .map(msg => {
            const toolCall = msg as IToolCallUIMessage;
            return {
              id: msg.id,
              toolCallId: toolCall.toolCallId || '',
              toolName: toolCall.toolName,
              toolInput: toolCall.toolInput,
              isStreaming: true,
              startedAt: msg.timestamp
            };
          });
      },

      clearAllStreamingToolCalls: () => {
        const hasStreaming = get().messages.some(
          msg =>
            msg.type === 'tool_call' &&
            (msg as IToolCallUIMessage).isStreaming === true
        );

        if (!hasStreaming) {
          return;
        }

        console.log(
          '[ChatMessagesStore] Finalizing all streaming tool calls in messages'
        );

        set(state => ({
          messages: state.messages.map(msg => {
            if (
              msg.type === 'tool_call' &&
              (msg as IToolCallUIMessage).isStreaming === true
            ) {
              return { ...msg, isStreaming: false };
            }
            return msg;
          })
        }));
      },

      // ─────────────────────────────────────────────────────────────
      // Thinking Indicator Actions
      // ─────────────────────────────────────────────────────────────
      showThinking: () => {
        set({ isThinking: true });
      },

      hideThinking: () => {
        set({ isThinking: false });
      },

      // ─────────────────────────────────────────────────────────────
      // Special Display Actions
      // ─────────────────────────────────────────────────────────────
      showAuthenticationCard: () => {
        set({ specialDisplay: 'authentication' });
      },

      showSubscriptionCard: () => {
        set({ specialDisplay: 'subscription' });
      },

      clearSpecialDisplay: () => {
        set({ specialDisplay: 'none' });
      },

      // ─────────────────────────────────────────────────────────────
      // LLM History Management
      // ─────────────────────────────────────────────────────────────
      addToLlmHistory: message => {
        set(state => ({
          llmHistory: [...state.llmHistory, message]
        }));
      },

      setLlmHistory: history => {
        set({ llmHistory: history });
      },

      clearLlmHistory: () => {
        set({ llmHistory: [] });
      },

      // ─────────────────────────────────────────────────────────────
      // Context Management
      // ─────────────────────────────────────────────────────────────
      addMentionContext: context => {
        set(state => {
          const newContexts = new Map(state.mentionContexts);
          newContexts.set(context.id, context);
          return { mentionContexts: newContexts };
        });
      },

      removeMentionContext: contextId => {
        set(state => {
          const newContexts = new Map(state.mentionContexts);
          newContexts.delete(contextId);
          return { mentionContexts: newContexts };
        });
      },

      setMentionContexts: contexts => {
        set({ mentionContexts: new Map(contexts) });
      },

      clearMentionContexts: () => {
        set({ mentionContexts: new Map() });
      },

      // ─────────────────────────────────────────────────────────────
      // Thread Management
      // ─────────────────────────────────────────────────────────────
      setCurrentThreadId: threadId => {
        set({ currentThreadId: threadId });
      },

      loadFromThread: (uiMessages, llmHistory, contexts, threadId) => {
        set({
          messages: uiMessages,
          llmHistory,
          mentionContexts: new Map(contexts),
          currentThreadId: threadId,
          lastMessageType:
            uiMessages.length > 0
              ? uiMessages[uiMessages.length - 1].type
              : null,
          specialDisplay: 'none',
          streaming: { isStreaming: false, text: '', messageId: null },
          isThinking: false,
          scrollState: {
            isAtBottom: true,
            showScrollButton: false,
            scrollToBottomCounter: 0
          }
        });
      },

      // ─────────────────────────────────────────────────────────────
      // Scroll Management
      // ─────────────────────────────────────────────────────────────
      setScrollAtBottom: isAtBottom => {
        set(state => ({
          scrollState: { ...state.scrollState, isAtBottom }
        }));
      },

      setShowScrollButton: show => {
        set(state => ({
          scrollState: { ...state.scrollState, showScrollButton: show }
        }));
      },

      scrollToBottom: () => {
        set(state => ({
          scrollState: {
            ...state.scrollState,
            scrollToBottomCounter: state.scrollState.scrollToBottomCounter + 1
          }
        }));
      },

      // ─────────────────────────────────────────────────────────────
      // Checkpoint Management (UI-level only)
      // ─────────────────────────────────────────────────────────────
      setCheckpointToRestore: checkpoint => {
        set({ checkpointToRestore: checkpoint });
      },

      getCheckpointToRestore: () => {
        return get().checkpointToRestore;
      },

      setRestoringCheckpointId: checkpointId => {
        set({ restoringCheckpointId: checkpointId });
      },

      removeMessagesAfterCheckpoint: checkpointId => {
        set(state => {
          // Find the index of the message with this checkpoint ID
          const checkpointIndex = state.messages.findIndex(
            msg =>
              msg.type === 'user' &&
              (msg as IUserUIMessage).checkpoint?.id === checkpointId
          );

          if (checkpointIndex === -1) {
            console.warn(
              '[ChatMessagesStore] Checkpoint not found:',
              checkpointId
            );
            return state;
          }

          // Remove all messages from the checkpoint message onwards (including the checkpoint message itself)
          const newMessages = state.messages.slice(0, checkpointIndex);

          console.log(
            '[ChatMessagesStore] Removing messages after checkpoint:',
            {
              checkpointId,
              originalCount: state.messages.length,
              newCount: newMessages.length
            }
          );

          return {
            messages: newMessages,
            restoringCheckpointId: null
          };
        });
      },

      // ─────────────────────────────────────────────────────────────
      // Loading Text Management
      // ─────────────────────────────────────────────────────────────
      updateLoadingText: text => {
        const { messages } = get();
        const loadingMessage = messages.find(m => m.type === 'loading');

        if (loadingMessage) {
          // Update existing loading message
          set(state => ({
            messages: state.messages.map(msg =>
              msg.id === loadingMessage.id
                ? ({ ...msg, text } as ILoadingUIMessage)
                : msg
            )
          }));
        } else {
          // Add new loading message
          const id = generateMessageId();
          const message: ILoadingUIMessage = {
            id,
            type: 'loading',
            timestamp: Date.now(),
            text
          };
          set(state => ({
            messages: [...state.messages, message]
          }));
        }
      },

      removeLoadingText: () => {
        set(state => ({
          messages: state.messages.filter(msg => msg.type !== 'loading')
        }));
      },

      // ─────────────────────────────────────────────────────────────
      // Assistant Message Updates
      // ─────────────────────────────────────────────────────────────
      updateAssistantMessage: (messageId, content) => {
        set(state => ({
          messages: state.messages.map(msg =>
            msg.id === messageId && msg.type === 'assistant'
              ? { ...msg, content }
              : msg
          )
        }));
      },

      finalizeAssistantMessage: messageId => {
        // For now, this just marks the streaming as complete if this was a streaming message
        const { streaming } = get();
        if (streaming.messageId === messageId) {
          set({
            streaming: { isStreaming: false, text: '', messageId: null }
          });
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Getters
      // ─────────────────────────────────────────────────────────────
      getMessage: id => get().messages.find(msg => msg.id === id),

      getMessagesByType: type =>
        get().messages.filter(msg => msg.type === type),

      getLlmHistory: () => get().llmHistory,

      getMentionContexts: () => get().mentionContexts,

      getLastUserMessage: () => {
        const { messages } = get();
        for (let i = messages.length - 1; i >= 0; i--) {
          if (messages[i].type === 'user') {
            return messages[i] as IUserUIMessage;
          }
        }
        return null;
      },

      getLastAssistantMessage: () => {
        const { messages } = get();
        for (let i = messages.length - 1; i >= 0; i--) {
          if (messages[i].type === 'assistant') {
            return messages[i] as IAssistantUIMessage;
          }
        }
        return null;
      }
    })),
    { name: 'ChatMessagesStore' }
  )
);
