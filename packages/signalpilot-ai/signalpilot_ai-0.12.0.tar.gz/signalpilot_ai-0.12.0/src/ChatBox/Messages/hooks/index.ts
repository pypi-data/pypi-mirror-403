/**
 * Chat Messages Hooks
 *
 * Custom React hooks for managing chat message functionality.
 * These hooks encapsulate common patterns and side effects.
 */

export { useChatScroll } from './useChatScroll';
export type { UseChatScrollResult } from './useChatScroll';

export { useChatKeyboard } from './useChatKeyboard';
export type {
  UseChatKeyboardOptions,
  UseChatKeyboardResult
} from './useChatKeyboard';

export { useChatCheckpoint } from './useChatCheckpoint';
export type {
  UseChatCheckpointOptions,
  UseChatCheckpointResult
} from './useChatCheckpoint';

export { useChatHistory } from './useChatHistory';
export type {
  UseChatHistoryOptions,
  UseChatHistoryResult
} from './useChatHistory';
