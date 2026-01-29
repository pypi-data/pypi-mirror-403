/**
 * LLMTypes - Shared types for the LLM loop system
 *
 * This file contains all types used across the LLM loop,
 * context gathering, and streaming handlers.
 */

import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ToolService } from './ToolService';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { AnthropicService } from './Anthropic/AnthropicService';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { ActionHistory } from '@/ChatBox/services/ActionHistory';
import { IChatService } from './IChatService';
import { CodeConfirmationDialog } from '../Components/CodeConfirmationDialog';
import { ILoadingIndicatorManager } from './ConversationService';
import { NotebookStateService } from '../Notebook/NotebookStateService';

// ═══════════════════════════════════════════════════════════════
// MODES
// ═══════════════════════════════════════════════════════════════

/**
 * Chat mode types
 */
export type ChatMode = 'agent' | 'ask' | 'fast' | 'welcome';

// ═══════════════════════════════════════════════════════════════
// CONTEXT TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Context gathered for LLM requests
 */
export interface ILLMContext {
  // Core context
  systemPrompt: string;
  conversationHistory: any[];

  // Dynamic context (gathered fresh each request)
  notebookSummary: string;
  notebookCells: string;
  kernelVariables: string;
  databaseConfigs: string;
  workspaceContext: string;
  userSnippets: string;
  userSelectedCells: string;

  // Metadata
  notebookId: string | null;
  mode: ChatMode;
  autoRun: boolean;
}

// ═══════════════════════════════════════════════════════════════
// LOOP CONFIG
// ═══════════════════════════════════════════════════════════════

/**
 * Configuration for the LLM loop
 */
export interface ILLMLoopConfig {
  anthropicService: AnthropicService;
  toolService: ToolService;
  messageComponent: ChatMessages;
  notebookContextManager: NotebookContextManager;
  diffManager: NotebookDiffManager | null;
  actionHistory: ActionHistory;
  chatHistory: HTMLDivElement;
  loadingManager: ILoadingIndicatorManager;
  codeConfirmationDialog: CodeConfirmationDialog;
}

/**
 * Result of an LLM loop iteration
 */
export interface ILLMLoopResult {
  success: boolean;
  cancelled: boolean;
  error?: Error;
  needsFreshContext?: boolean;
}

// ═══════════════════════════════════════════════════════════════
// STREAMING UI STATE
// ═══════════════════════════════════════════════════════════════

/**
 * State for streaming UI operations
 */
export interface IStreamingUIState {
  isStreamingMessage: boolean;
  isThinkingActive: boolean;
  activeToolCallIds: Set<string>;
  streamingMessageId: string | null;
}

// ═══════════════════════════════════════════════════════════════
// TOOL HANDLING
// ═══════════════════════════════════════════════════════════════

/**
 * Tool use event types from streaming
 */
export type ToolUseEventType =
  | 'tool_use'
  | 'server_tool_use'
  | 'tool_use_delta'
  | 'tool_use_stop';

/**
 * Tool use event from streaming
 */
export interface IToolUseEvent {
  type: ToolUseEventType;
  id: string;
  name?: string;
  input?: any;
  input_delta?: any;
}

/**
 * Tool call extracted from response
 */
export interface IToolCall {
  id: string;
  name: string;
  input: any;
}

/**
 * Result of processing tool calls
 */
export interface IToolProcessResult {
  shouldContinue: boolean;
  hasToolCalls: boolean;
  toolResults: any[];
}

// ═══════════════════════════════════════════════════════════════
// DIFF HANDLING
// ═══════════════════════════════════════════════════════════════

/**
 * Result of diff approval handling
 */
export interface IDiffApprovalResult {
  approved: boolean;
  rejected: boolean;
  partial?: boolean;
}

// ═══════════════════════════════════════════════════════════════
// API RESPONSE
// ═══════════════════════════════════════════════════════════════

/**
 * Simplified API response interface
 */
export interface IAPIResponse {
  content?: Array<{
    type: string;
    text?: string;
    id?: string;
    name?: string;
    input?: any;
  }>;
  cancelled?: boolean;
  needsFreshContext?: boolean;
  usage?: {
    input_tokens?: number;
    output_tokens?: number;
    cache_creation_input_tokens?: number;
    cache_read_input_tokens?: number;
  };
}

// ═══════════════════════════════════════════════════════════════
// STREAMING CALLBACKS
// ═══════════════════════════════════════════════════════════════

/**
 * Callbacks for streaming operations
 */
export interface IStreamingCallbacks {
  onTextChunk: (text: string) => void;
  onToolUse: (toolUse: IToolUseEvent) => void;
  onError?: (error: Error) => void;
}

// ═══════════════════════════════════════════════════════════════
// CONVERSATION CONTEXT (for compatibility with existing code)
// ═══════════════════════════════════════════════════════════════

/**
 * Conversation context passed through utility functions
 * This maintains compatibility with existing ConversationServiceUtils
 */
export interface IConversationContext {
  chatService: IChatService;
  toolService: ToolService;
  messageComponent: ChatMessages;
  notebookStateService: NotebookStateService;
  codeConfirmationDialog: CodeConfirmationDialog;
  loadingManager: ILoadingIndicatorManager;
  diffManager: NotebookDiffManager | null;
  actionHistory: ActionHistory;
  notebookId: string | null;
  templates: Array<{ name: string; content: string }>;
  isActiveToolExecution: boolean;
  chatHistory: HTMLDivElement;
}

// ═══════════════════════════════════════════════════════════════
// STREAMING STATE (for compatibility with existing code)
// ═══════════════════════════════════════════════════════════════

/**
 * Streaming state for tracking active streaming operations
 * This maintains compatibility with existing ConversationServiceUtils
 */
export interface IStreamingState {
  isStreamingMessage: boolean;
  isThinkingIndicatorActive: boolean;
  activeStreamingToolCallIds: Set<string>;
  streamingToolCalls?: Map<string, any>;
  operationQueue: Record<string, any>;
}
