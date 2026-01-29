// Chat store types
import { IChatMessage, IToolCall } from '../../types';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

export interface IChatThread {
  id: string;
  name: string;
  messages: IChatMessage[];
  lastUpdated: number;
  contexts: Map<string, IMentionContext>;
  messageTimestamps: Map<string, number>;
  continueButtonShown?: boolean;
  needsContinue?: boolean;
  agent?: string;
}

export interface IStreamingState {
  isStreaming: boolean;
  streamingText: string;
  pendingToolCalls: IToolCall[];
  statusText: string;
}

export type ChatMode = 'agent' | 'ask' | 'fast';

export interface IChatState {
  threads: IChatThread[];
  currentThreadId: string | null;
  currentNotebookId: string | null;
  messages: IChatMessage[];
  contexts: Map<string, IMentionContext>;
  streaming: IStreamingState;
  isProcessing: boolean;
  isLoadingHistory: boolean;
  mode: ChatMode;
  error: string | null;
  showNewChatDisplay: boolean;
}

export interface IChatActions {
  // Thread actions
  setThreads: (threads: IChatThread[]) => void;
  setCurrentThreadId: (threadId: string | null) => void;
  setCurrentNotebookId: (notebookId: string | null) => void;
  createThread: (name?: string) => IChatThread;
  deleteThread: (threadId: string) => void;
  renameCurrentThread: (name: string) => void;
  clearThreads: () => void;

  // Message actions
  setMessages: (messages: IChatMessage[]) => void;
  addMessage: (message: IChatMessage) => void;
  updateMessage: (messageId: string, updates: Partial<IChatMessage>) => void;
  clearMessages: () => void;

  // Context actions
  setContexts: (contexts: Map<string, IMentionContext>) => void;
  addContext: (context: IMentionContext) => void;
  removeContext: (contextId: string) => void;
  clearContexts: () => void;

  // Streaming actions
  startStreaming: (statusText?: string) => void;
  updateStreamingText: (text: string, append?: boolean) => void;
  addPendingToolCall: (toolCall: IToolCall) => void;
  clearPendingToolCalls: () => void;
  setStreamingStatus: (statusText: string) => void;
  endStreaming: () => void;

  // UI actions
  setProcessing: (isProcessing: boolean) => void;
  setLoadingHistory: (isLoading: boolean) => void;
  setMode: (mode: ChatMode) => void;
  setError: (error: string | null) => void;
  setShowNewChatDisplay: (show: boolean) => void;

  // Utilities
  getState: () => IChatState;
  getCurrentThread: () => IChatThread | null;
  syncCurrentThread: (thread: IChatThread) => void;
}

export type IChatStore = IChatState & IChatActions;
