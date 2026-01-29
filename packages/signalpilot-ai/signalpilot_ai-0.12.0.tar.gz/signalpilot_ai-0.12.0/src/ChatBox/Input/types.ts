/**
 * ChatInputContainer Types
 *
 * Type definitions for the ChatInputContainer component that replaces
 * the imperative ChatInputManager class with a React-based approach.
 */
import { Contents } from '@jupyterlab/services';
import { IChatService } from '@/LLM/IChatService';
import { ConversationService } from '@/LLM';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ChatUIHelper } from '@/ChatBox/services/ChatUIHelper';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import { ToolService } from '@/LLM/ToolService';
import { IChatMessage, ICheckpoint } from '@/types';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

export type ChatMode = 'agent' | 'ask' | 'fast';

/**
 * Dependencies needed by ChatInputContainer.
 * These are services that must be initialized before the component can function.
 */
export interface ChatInputDependencies {
  chatService: IChatService;
  conversationService: ConversationService;
  messageComponent: ChatMessages;
  uiHelper: ChatUIHelper;
}

/**
 * Props for the ChatInputContainer component.
 */
export interface ChatInputContainerProps {
  /** Chat history manager for thread/history operations (optional - some features disabled if not provided) */
  chatHistoryManager?: ChatHistoryManager | null;
  /** JupyterLab content manager for file operations */
  contentManager: Contents.IManager;
  /** Tool service for AI tools */
  toolService: ToolService;

  /**
   * Optional dependencies - can be set later via ref.setDependencies()
   * This allows the component to mount before all services are ready.
   */
  initialDependencies?: ChatInputDependencies;

  /** Callback when a context is selected from mention dropdown */
  onContextSelected?: (context: IMentionContext) => void;
  /** Callback when a context is removed */
  onContextRemoved?: (contextId: string) => void;
  /** Callback to reset the chat */
  onResetChat?: () => void;
  /** Callback when mode changes */
  onModeSelected?: (mode: ChatMode) => void;
  /** Callback after a message is sent (before processing completes) */
  onMessageSent?: () => void;
  /** Callback to cancel the current message */
  onCancel?: () => void;

  /** Initial placeholder text */
  placeholder?: string;
}

/**
 * Ref interface for imperative control of ChatInputContainer.
 * Used by ChatBoxWidget to interact with the input.
 */
export interface ChatInputContainerRef {
  // Message operations
  /** Send a message to the AI. If directMessage is provided, uses that instead of reading from input. */
  sendMessage: (
    cellContext?: string,
    hidden?: boolean,
    directMessage?: string
  ) => Promise<void>;
  /** Continue the conversation without new user input */
  continueMessage: (cellContext?: string) => Promise<void>;

  // Input control
  /** Focus the input element */
  focus: () => void;
  /** Clear the input */
  clearInput: () => void;
  /** Get current input value */
  getCurrentInputValue: () => string;
  /** Set input value */
  setInputValue: (value: string) => void;

  // History
  /** Load user message history */
  loadUserMessageHistory: () => Promise<void>;

  // Token progress
  /** Update token progress from messages */
  updateTokenProgress: (messages?: IChatMessage[]) => void;

  // Context management
  /** Re-render the context row */
  renderContextRow: () => void;
  /** Get active contexts */
  getActiveContexts: () => Map<string, IMentionContext>;

  // Configuration
  /** Set placeholder text */
  setPlaceholder: (placeholder: string) => void;

  // Processing state
  /** Check if currently processing a message */
  getIsProcessingMessage: () => boolean;
  /** Set processing state (used by external cancel) */
  setIsProcessingMessage: (value: boolean) => void;

  // Checkpoint
  /** Get checkpoint to restore */
  getCheckpointToRestore: () => ICheckpoint | null;
  /** Set checkpoint to restore */
  setCheckpointToRestore: (checkpoint: ICheckpoint | null) => void;

  // Dependencies
  /** Set dependencies after initial mount */
  setDependencies: (deps: ChatInputDependencies) => void;
}

// Re-export CellContext from ContextRow for convenience
export type { CellContext } from './ContextRow';
