/**
 * LLM Module - Main export file
 *
 * This module contains the refactored LLM loop system with:
 * - LLMLoop: The main processing loop
 * - LLMContext: Context gathering
 * - Handlers: UI, Tool Execution, Diff Approval
 * - ConversationService: Main conversation processing service
 * - Anthropic: Anthropic API integration
 * - Services: Tool service, chat service interface, skills config
 */

// Main loop
export { LLMLoop, createLLMLoop } from './LLMLoop';

// Context gathering
export { LLMContextGatherer } from './LLMContext';

// Handlers
export {
  StreamingUIHandler,
  ToolCallInfo,
  IExtendedStreamingState
} from './handlers/StreamingUIHandler';
export { ToolExecutionHandler } from './handlers/ToolExecutionHandler';
export { DiffApprovalHandler } from './handlers/DiffApprovalHandler';

// Conversation Service
export {
  ConversationService,
  ILoadingIndicatorManager
} from './ConversationService';

// Anthropic
export { AnthropicService } from './Anthropic/AnthropicService';
export { AnthropicStreamHandler } from './Anthropic/AnthropicStreamHandler';
export { AnthropicMessageCreator } from './Anthropic/AnthropicMessageCreator';

// Services
export { ToolService, ToolCall } from './ToolService';
export { IChatService, CancelledRequest } from './IChatService';
export * from './SkillsConfig';

// Types
export * from './LLMTypes';
