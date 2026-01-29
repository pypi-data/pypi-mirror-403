// Central state management for chat messages, threads, and streaming
import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { IChatMessage } from '../../types';
import { ChatMode, IChatStore, IChatThread, IStreamingState } from './types';

const generateId = () =>
  `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const createEmptyThread = (name = 'New Chat'): IChatThread => ({
  id: generateId(),
  name,
  messages: [],
  lastUpdated: Date.now(),
  contexts: new Map(),
  messageTimestamps: new Map(),
  continueButtonShown: false,
  needsContinue: false
});

const initialStreaming: IStreamingState = {
  isStreaming: false,
  streamingText: '',
  pendingToolCalls: [],
  statusText: ''
};

export const useChatStore = create<IChatStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial state
      threads: [],
      currentThreadId: null,
      currentNotebookId: null,
      messages: [],
      contexts: new Map(),
      streaming: { ...initialStreaming },
      isProcessing: false,
      isLoadingHistory: false,
      mode: 'agent' as ChatMode,
      error: null,
      showNewChatDisplay: true,

      // Thread actions
      setThreads: threads => set({ threads }, false, 'setThreads'),

      setCurrentThreadId: threadId => {
        const thread = get().threads.find(t => t.id === threadId);
        set(
          {
            currentThreadId: threadId,
            messages: thread?.messages || [],
            contexts: thread?.contexts || new Map(),
            showNewChatDisplay: !thread || thread.messages.length === 0
          },
          false,
          'setCurrentThreadId'
        );
      },

      setCurrentNotebookId: notebookId =>
        set({ currentNotebookId: notebookId }, false, 'setCurrentNotebookId'),

      createThread: name => {
        const newThread = createEmptyThread(name);
        set(
          {
            threads: [...get().threads, newThread],
            currentThreadId: newThread.id,
            messages: [],
            contexts: new Map(),
            showNewChatDisplay: true,
            error: null
          },
          false,
          'createThread'
        );
        return newThread;
      },

      deleteThread: threadId => {
        const { threads, currentThreadId } = get();
        const newThreads = threads.filter(t => t.id !== threadId);
        let newCurrentId =
          currentThreadId === threadId
            ? newThreads[0]?.id || null
            : currentThreadId;
        const newThread = newThreads.find(t => t.id === newCurrentId);
        set(
          {
            threads: newThreads,
            currentThreadId: newCurrentId,
            messages: newThread?.messages || [],
            contexts: newThread?.contexts || new Map(),
            showNewChatDisplay: !newThread || newThread.messages.length === 0
          },
          false,
          'deleteThread'
        );
      },

      renameCurrentThread: name => {
        const { threads, currentThreadId } = get();
        if (!currentThreadId) return;
        set(
          {
            threads: threads.map(t =>
              t.id === currentThreadId
                ? { ...t, name, lastUpdated: Date.now() }
                : t
            )
          },
          false,
          'renameCurrentThread'
        );
      },

      clearThreads: () =>
        set(
          {
            threads: [],
            currentThreadId: null,
            messages: [],
            contexts: new Map(),
            showNewChatDisplay: true
          },
          false,
          'clearThreads'
        ),

      // Message actions
      setMessages: messages => {
        const { threads, currentThreadId } = get();
        set(
          {
            messages,
            threads: threads.map(t =>
              t.id === currentThreadId
                ? { ...t, messages, lastUpdated: Date.now() }
                : t
            ),
            showNewChatDisplay: messages.length === 0
          },
          false,
          'setMessages'
        );
      },

      addMessage: message => {
        const { messages, threads, currentThreadId } = get();
        const messageWithId = { ...message, id: message.id || generateId() };
        const newMessages = [...messages, messageWithId];
        set(
          {
            messages: newMessages,
            threads: threads.map(t =>
              t.id === currentThreadId
                ? {
                    ...t,
                    messages: newMessages,
                    lastUpdated: Date.now(),
                    messageTimestamps: new Map(t.messageTimestamps).set(
                      messageWithId.id!,
                      Date.now()
                    )
                  }
                : t
            ),
            showNewChatDisplay: false
          },
          false,
          'addMessage'
        );
      },

      updateMessage: (messageId, updates) => {
        const { messages, threads, currentThreadId } = get();
        const updatedMessages = messages.map(m =>
          m.id === messageId ? { ...m, ...updates } : m
        );
        set(
          {
            messages: updatedMessages,
            threads: threads.map(t =>
              t.id === currentThreadId
                ? {
                    ...t,
                    messages: updatedMessages,
                    lastUpdated: Date.now()
                  }
                : t
            )
          },
          false,
          'updateMessage'
        );
      },

      clearMessages: () => {
        const { threads, currentThreadId } = get();
        set(
          {
            messages: [],
            threads: threads.map(t =>
              t.id === currentThreadId
                ? {
                    ...t,
                    messages: [],
                    lastUpdated: Date.now(),
                    messageTimestamps: new Map()
                  }
                : t
            ),
            showNewChatDisplay: true
          },
          false,
          'clearMessages'
        );
      },

      // Context actions
      setContexts: contexts => {
        const { threads, currentThreadId } = get();
        set(
          {
            contexts,
            threads: threads.map(t =>
              t.id === currentThreadId ? { ...t, contexts } : t
            )
          },
          false,
          'setContexts'
        );
      },

      addContext: context => {
        const { contexts, threads, currentThreadId } = get();
        const newContexts = new Map(contexts);
        newContexts.set(context.id, context);
        set(
          {
            contexts: newContexts,
            threads: threads.map(t =>
              t.id === currentThreadId ? { ...t, contexts: newContexts } : t
            )
          },
          false,
          'addContext'
        );
      },

      removeContext: contextId => {
        const { contexts, threads, currentThreadId } = get();
        const newContexts = new Map(contexts);
        newContexts.delete(contextId);
        set(
          {
            contexts: newContexts,
            threads: threads.map(t =>
              t.id === currentThreadId ? { ...t, contexts: newContexts } : t
            )
          },
          false,
          'removeContext'
        );
      },

      clearContexts: () => {
        const { threads, currentThreadId } = get();
        set(
          {
            contexts: new Map(),
            threads: threads.map(t =>
              t.id === currentThreadId ? { ...t, contexts: new Map() } : t
            )
          },
          false,
          'clearContexts'
        );
      },

      // Streaming actions
      startStreaming: (statusText = 'Generating...') =>
        set(
          {
            streaming: {
              isStreaming: true,
              streamingText: '',
              pendingToolCalls: [],
              statusText
            }
          },
          false,
          'startStreaming'
        ),

      updateStreamingText: (text, append = false) => {
        const { streaming } = get();
        set(
          {
            streaming: {
              ...streaming,
              streamingText: append ? streaming.streamingText + text : text
            }
          },
          false,
          'updateStreamingText'
        );
      },

      addPendingToolCall: toolCall => {
        const { streaming } = get();
        set(
          {
            streaming: {
              ...streaming,
              pendingToolCalls: [...streaming.pendingToolCalls, toolCall]
            }
          },
          false,
          'addPendingToolCall'
        );
      },

      clearPendingToolCalls: () => {
        const { streaming } = get();
        set(
          { streaming: { ...streaming, pendingToolCalls: [] } },
          false,
          'clearPendingToolCalls'
        );
      },

      setStreamingStatus: statusText => {
        const { streaming } = get();
        set(
          { streaming: { ...streaming, statusText } },
          false,
          'setStreamingStatus'
        );
      },

      endStreaming: () =>
        set({ streaming: { ...initialStreaming } }, false, 'endStreaming'),

      // UI actions
      setProcessing: isProcessing =>
        set({ isProcessing }, false, 'setProcessing'),
      setLoadingHistory: isLoadingHistory =>
        set({ isLoadingHistory }, false, 'setLoadingHistory'),
      setMode: mode => set({ mode }, false, 'setMode'),
      setError: error => set({ error }, false, 'setError'),
      setShowNewChatDisplay: showNewChatDisplay =>
        set({ showNewChatDisplay }, false, 'setShowNewChatDisplay'),

      // Utilities
      getState: () => {
        const s = get();
        return {
          threads: s.threads,
          currentThreadId: s.currentThreadId,
          currentNotebookId: s.currentNotebookId,
          messages: s.messages,
          contexts: s.contexts,
          streaming: s.streaming,
          isProcessing: s.isProcessing,
          isLoadingHistory: s.isLoadingHistory,
          mode: s.mode,
          error: s.error,
          showNewChatDisplay: s.showNewChatDisplay
        };
      },

      getCurrentThread: () => {
        const { threads, currentThreadId } = get();
        return threads.find(t => t.id === currentThreadId) || null;
      },

      syncCurrentThread: thread => {
        const { threads } = get();
        set(
          {
            threads: threads.map(t => (t.id === thread.id ? thread : t)),
            messages: thread.messages,
            contexts: thread.contexts,
            showNewChatDisplay: thread.messages.length === 0
          },
          false,
          'syncCurrentThread'
        );
      }
    })),
    { name: 'ChatStore' }
  )
);

// Selectors
export const selectMessages = (state: IChatStore) => state.messages;
export const selectStreaming = (state: IChatStore) => state.streaming;
export const selectIsStreaming = (state: IChatStore) =>
  state.streaming.isStreaming;
export const selectStreamingText = (state: IChatStore) =>
  state.streaming.streamingText;
export const selectIsProcessing = (state: IChatStore) => state.isProcessing;
export const selectMode = (state: IChatStore) => state.mode;
export const selectError = (state: IChatStore) => state.error;
export const selectCurrentThreadId = (state: IChatStore) =>
  state.currentThreadId;
export const selectThreads = (state: IChatStore) => state.threads;
export const selectShowNewChatDisplay = (state: IChatStore) =>
  state.showNewChatDisplay;
export const selectMessageCount = (state: IChatStore) => state.messages.length;
export const selectContexts = (state: IChatStore) => state.contexts;

// Non-React subscriptions
export const subscribeToMessages = (cb: (m: IChatMessage[]) => void) =>
  useChatStore.subscribe(s => s.messages, cb);

export const subscribeToStreaming = (cb: (s: IStreamingState) => void) =>
  useChatStore.subscribe(s => s.streaming, cb);

export const subscribeToProcessing = (cb: (p: boolean) => void) =>
  useChatStore.subscribe(s => s.isProcessing, cb);

export const subscribeToMode = (cb: (m: ChatMode) => void) =>
  useChatStore.subscribe(s => s.mode, cb);

export const subscribeToThreads = (cb: (t: IChatThread[]) => void) =>
  useChatStore.subscribe(s => s.threads, cb);

export const subscribeToCurrentThread = (cb: (id: string | null) => void) =>
  useChatStore.subscribe(s => s.currentThreadId, cb);
