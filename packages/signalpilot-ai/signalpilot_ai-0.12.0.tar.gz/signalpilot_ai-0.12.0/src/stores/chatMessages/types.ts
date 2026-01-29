/**
 * ChatMessages Store Types
 *
 * Type definitions for the chat messages Zustand store.
 */

import { IChatMessage, ICheckpoint } from '../../types';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

// ═══════════════════════════════════════════════════════════════
// MESSAGE TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Types of displayable messages in the chat
 */
export type ChatMessageType =
  | 'user'
  | 'assistant'
  | 'system'
  | 'error'
  | 'tool_call'
  | 'tool_result'
  | 'diff_approval'
  | 'thinking'
  | 'loading';

/**
 * Base interface for all chat UI messages
 */
export interface IChatUIMessage {
  /** Unique ID for this UI message */
  id: string;
  /** Type of message */
  type: ChatMessageType;
  /** Timestamp when message was added */
  timestamp: number;
  /** Whether this message is hidden from view */
  hidden?: boolean;
}

/**
 * User message display data
 */
export interface IUserUIMessage extends IChatUIMessage {
  type: 'user';
  /** The message content */
  content: string;
  /** Associated checkpoint for rollback (if any) */
  checkpoint?: ICheckpoint;
  /** Whether the message content is collapsed */
  isCollapsed?: boolean;
}

/**
 * Assistant message display data
 */
export interface IAssistantUIMessage extends IChatUIMessage {
  type: 'assistant';
  /** The message content (markdown) */
  content: string;
  /** Whether to show the SignalPilot header */
  showHeader?: boolean;
}

/**
 * System message display data
 */
export interface ISystemUIMessage extends IChatUIMessage {
  type: 'system';
  /** The message content (may contain HTML) */
  content: string;
}

/**
 * Error message display data
 */
export interface IErrorUIMessage extends IChatUIMessage {
  type: 'error';
  /** The error message */
  content: string;
}

/**
 * Tool call display data
 *
 * A single message that represents both the tool call and its result.
 * Starts as a streaming tool call, then gets updated with result when complete.
 */
export interface IToolCallUIMessage extends IChatUIMessage {
  type: 'tool_call';
  /** Tool name */
  toolName: string;
  /** Tool input parameters */
  toolInput: Record<string, any>;
  /** Tool call ID from API */
  toolCallId?: string;
  /** Whether this is still streaming/in-progress */
  isStreaming?: boolean;
  /** Whether the tool call resulted in an error */
  hasError?: boolean;
  /** Error message if any */
  errorMessage?: string;
  /** Tool result (populated when tool execution completes) */
  result?: any;
  /** Original tool call data for result display */
  toolCallData?: any;
  /** Whether the result has been received */
  hasResult?: boolean;
  /** Tool search result (for server_tool_use tools like tool_search_tool_regex) */
  toolSearchResult?: {
    input: any;
    result: any;
  };
}

/**
 * Tool result display data
 */
export interface IToolResultUIMessage extends IChatUIMessage {
  type: 'tool_result';
  /** Tool name that produced this result */
  toolName: string;
  /** Tool use ID this result corresponds to */
  toolUseId: string;
  /** The result data */
  result: any;
  /** Original tool call data (for MCP displays) */
  toolCallData: any;
  /** Whether the result contains an error */
  hasError?: boolean;
  /** Error message if any */
  errorMessage?: string;
}

/**
 * Diff cell data for diff approval message
 */
export interface IDiffCellUI {
  cellId: string;
  type: 'add' | 'edit' | 'remove';
  originalContent?: string;
  newContent?: string;
  displaySummary?: string;
}

/**
 * Diff approval display data
 */
export interface IDiffApprovalUIMessage extends IChatUIMessage {
  type: 'diff_approval';
  /** Notebook path this diff applies to */
  notebookPath?: string;
  /** Diff cells to display */
  diffCells: IDiffCellUI[];
  /** Whether this is a historical (non-interactive) display */
  isHistorical?: boolean;
}

/**
 * Loading indicator display data
 */
export interface ILoadingUIMessage extends IChatUIMessage {
  type: 'loading';
  /** Loading text to display */
  text: string;
}

/**
 * Union type for all UI message types
 */
export type ChatUIMessage =
  | IUserUIMessage
  | IAssistantUIMessage
  | ISystemUIMessage
  | IErrorUIMessage
  | IToolCallUIMessage
  | IToolResultUIMessage
  | IDiffApprovalUIMessage
  | ILoadingUIMessage;

// ═══════════════════════════════════════════════════════════════
// STATE TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Streaming state for the current assistant response
 */
export interface IStreamingState {
  /** Whether currently streaming */
  isStreaming: boolean;
  /** Current accumulated text */
  text: string;
  /** ID of the streaming message */
  messageId: string | null;
}

/**
 * Special display state (auth card, subscription card)
 */
export type SpecialDisplayState = 'none' | 'authentication' | 'subscription';

/**
 * Scroll state for the chat container
 */
export interface IScrollState {
  /** Whether user is scrolled to bottom */
  isAtBottom: boolean;
  /** Whether to show scroll-to-bottom button */
  showScrollButton: boolean;
  /** Counter to trigger scroll to bottom (incremented when scroll is requested) */
  scrollToBottomCounter: number;
}

/**
 * Streaming tool call state
 */
export interface IStreamingToolCall {
  /** Unique ID for this streaming tool call */
  id: string;
  /** Tool call ID from the LLM */
  toolCallId: string;
  /** Tool name */
  toolName: string;
  /** Accumulated tool input (as it streams) */
  toolInput: any;
  /** Whether this tool call is still streaming */
  isStreaming: boolean;
  /** Timestamp when streaming started */
  startedAt: number;
}

// ═══════════════════════════════════════════════════════════════
// STORE STATE
// ═══════════════════════════════════════════════════════════════

export interface IChatMessagesState {
  /** All displayed UI messages */
  messages: ChatUIMessage[];

  /** LLM message history (sent to API) */
  llmHistory: IChatMessage[];

  /** Current streaming state */
  streaming: IStreamingState;

  /** Whether thinking indicator is shown */
  isThinking: boolean;

  /** Special display mode (replaces messages with card) */
  specialDisplay: SpecialDisplayState;

  /** ID of the last message type added (for grouping) */
  lastMessageType: ChatMessageType | null;

  /** Current thread ID for persistence */
  currentThreadId: string | null;

  /** Mention contexts (@cell, @file references) */
  mentionContexts: Map<string, IMentionContext>;

  /** Scroll state */
  scrollState: IScrollState;

  /** Checkpoint stored for potential restoration */
  checkpointToRestore: ICheckpoint | null;

  /** ID of checkpoint currently being restored (messages after this become opaque) */
  restoringCheckpointId: string | null;
}

// ═══════════════════════════════════════════════════════════════
// STORE ACTIONS
// ═══════════════════════════════════════════════════════════════

export interface IChatMessagesActions {
  // ─────────────────────────────────────────────────────────────
  // Message Management
  // ─────────────────────────────────────────────────────────────

  /** Add a user message */
  addUserMessage: (
    content: string,
    checkpoint?: ICheckpoint,
    options?: { hidden?: boolean }
  ) => string;

  /** Add an assistant message */
  addAssistantMessage: (content: string, showHeader?: boolean) => string;

  /** Add a system message */
  addSystemMessage: (content: string) => string;

  /** Add an error message */
  addErrorMessage: (content: string) => string;

  /** Add a tool call message */
  addToolCall: (
    toolName: string,
    toolInput: Record<string, any>,
    toolCallId?: string
  ) => string;

  /** Update a tool call (e.g., mark as error) */
  updateToolCall: (
    id: string,
    updates: Partial<Omit<IToolCallUIMessage, 'id' | 'type' | 'timestamp'>>
  ) => void;

  /** Add a tool result message */
  addToolResult: (
    toolName: string,
    toolUseId: string,
    result: any,
    toolCallData: any,
    hasError?: boolean
  ) => string;

  /** Add a diff approval message */
  addDiffApproval: (
    notebookPath?: string,
    diffCells?: IDiffCellUI[],
    isHistorical?: boolean
  ) => string;

  /** Add a loading indicator */
  addLoading: (text?: string) => string;

  /** Remove a message by ID */
  removeMessage: (id: string) => void;

  /** Remove all tool call messages with a specific tool name */
  removeToolCallsByName: (toolName: string) => void;

  /** Clear all messages */
  clearMessages: () => void;

  /** Set UI messages (for restoring state) */
  setMessages: (messages: ChatUIMessage[]) => void;

  /** Mark a diff approval as historical (after user approved/rejected) */
  markDiffApprovalHistorical: (id: string) => void;

  /** Update diff approval cells data */
  updateDiffApprovalCells: (id: string, diffCells: IDiffCellUI[]) => void;

  /** Find an active (non-historical) diff approval message */
  getActiveDiffApproval: () => IDiffApprovalUIMessage | null;

  // ─────────────────────────────────────────────────────────────
  // Streaming State
  // ─────────────────────────────────────────────────────────────

  /** Start streaming a new assistant message */
  startStreaming: () => string;

  /** Update streaming text */
  updateStreamingText: (text: string) => void;

  /** Append to streaming text */
  appendStreamingText: (text: string) => void;

  /** Finalize streaming (convert to regular message) */
  finalizeStreaming: () => void;

  /** Cancel streaming */
  cancelStreaming: () => void;

  // ─────────────────────────────────────────────────────────────
  // Streaming Tool Calls
  // ─────────────────────────────────────────────────────────────

  /** Start a streaming tool call */
  startStreamingToolCall: (toolCallId: string, toolName: string) => string;

  /** Update a streaming tool call with new input data */
  updateStreamingToolCall: (toolCallId: string, toolInput: any) => void;

  /** Update a tool call with tool search result (for server_tool_use) */
  updateToolSearchResult: (toolCallId: string, input: any, result: any) => void;

  /** Finalize a streaming tool call (convert to regular tool_call message) */
  finalizeStreamingToolCall: (toolCallId: string) => void;

  /** Cancel/remove a streaming tool call */
  cancelStreamingToolCall: (toolCallId: string) => void;

  /** Get all streaming tool calls as array */
  getStreamingToolCalls: () => IStreamingToolCall[];

  /** Clear all streaming tool calls (cleanup after finalization) */
  clearAllStreamingToolCalls: () => void;

  // ─────────────────────────────────────────────────────────────
  // Thinking Indicator
  // ─────────────────────────────────────────────────────────────

  /** Show thinking indicator */
  showThinking: () => void;

  /** Hide thinking indicator */
  hideThinking: () => void;

  // ─────────────────────────────────────────────────────────────
  // Special Display
  // ─────────────────────────────────────────────────────────────

  /** Show authentication card */
  showAuthenticationCard: () => void;

  /** Show subscription card */
  showSubscriptionCard: () => void;

  /** Clear special display (return to normal messages) */
  clearSpecialDisplay: () => void;

  // ─────────────────────────────────────────────────────────────
  // LLM History Management
  // ─────────────────────────────────────────────────────────────

  /** Add a message to LLM history */
  addToLlmHistory: (message: IChatMessage) => void;

  /** Set the entire LLM history */
  setLlmHistory: (history: IChatMessage[]) => void;

  /** Clear LLM history */
  clearLlmHistory: () => void;

  // ─────────────────────────────────────────────────────────────
  // Context Management
  // ─────────────────────────────────────────────────────────────

  /** Add a mention context */
  addMentionContext: (context: IMentionContext) => void;

  /** Remove a mention context */
  removeMentionContext: (contextId: string) => void;

  /** Set all mention contexts */
  setMentionContexts: (contexts: Map<string, IMentionContext>) => void;

  /** Clear all mention contexts */
  clearMentionContexts: () => void;

  // ─────────────────────────────────────────────────────────────
  // Thread Management
  // ─────────────────────────────────────────────────────────────

  /** Set current thread ID */
  setCurrentThreadId: (threadId: string | null) => void;

  /** Load from a thread (restores messages, history, and contexts) */
  loadFromThread: (
    uiMessages: ChatUIMessage[],
    llmHistory: IChatMessage[],
    contexts: Map<string, IMentionContext>,
    threadId: string
  ) => void;

  // ─────────────────────────────────────────────────────────────
  // Scroll Management
  // ─────────────────────────────────────────────────────────────

  /** Set scroll at bottom state */
  setScrollAtBottom: (isAtBottom: boolean) => void;

  /** Set show scroll button state */
  setShowScrollButton: (show: boolean) => void;

  /** Request scroll to bottom (component listens to counter) */
  scrollToBottom: () => void;

  // ─────────────────────────────────────────────────────────────
  // Checkpoint Management (UI-level only)
  // ─────────────────────────────────────────────────────────────

  /** Store a checkpoint reference for potential restoration */
  setCheckpointToRestore: (checkpoint: ICheckpoint | null) => void;

  /** Get the stored checkpoint */
  getCheckpointToRestore: () => ICheckpoint | null;

  /** Set the restoring checkpoint ID (messages after this will appear opaque) */
  setRestoringCheckpointId: (checkpointId: string | null) => void;

  /** Remove all messages after the checkpoint with the given ID */
  removeMessagesAfterCheckpoint: (checkpointId: string) => void;

  // ─────────────────────────────────────────────────────────────
  // Loading Text Management
  // ─────────────────────────────────────────────────────────────

  /** Update the text of an existing loading message, or add one */
  updateLoadingText: (text: string) => void;

  /** Remove the loading message */
  removeLoadingText: () => void;

  // ─────────────────────────────────────────────────────────────
  // Assistant Message Updates
  // ─────────────────────────────────────────────────────────────

  /** Update an existing assistant message content */
  updateAssistantMessage: (messageId: string, content: string) => void;

  /** Finalize an assistant message (mark as complete) */
  finalizeAssistantMessage: (messageId: string) => void;

  // ─────────────────────────────────────────────────────────────
  // Getters
  // ─────────────────────────────────────────────────────────────

  /** Get message by ID */
  getMessage: (id: string) => ChatUIMessage | undefined;

  /** Get all messages of a specific type */
  getMessagesByType: (type: ChatMessageType) => ChatUIMessage[];

  /** Get LLM history */
  getLlmHistory: () => IChatMessage[];

  /** Get mention contexts */
  getMentionContexts: () => Map<string, IMentionContext>;

  /** Get the last user message */
  getLastUserMessage: () => IUserUIMessage | null;

  /** Get the last assistant message */
  getLastAssistantMessage: () => IAssistantUIMessage | null;
}

// ═══════════════════════════════════════════════════════════════
// STORE TYPE
// ═══════════════════════════════════════════════════════════════

export type IChatMessagesStore = IChatMessagesState & IChatMessagesActions;
