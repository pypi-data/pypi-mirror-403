/**
 * ChatInputContainer Hooks Index
 *
 * Custom hooks for chat input functionality.
 */

// Input controls (value, selection, focus)
export { useInputControls } from './useInputControls';
export type { UseInputControlsReturn } from './useInputControls';

// Message history navigation
export { useMessageHistory } from './useMessageHistory';

// Message sending
export { useSendMessage } from './useSendMessage';
export type {
  UseSendMessageOptions,
  UseSendMessageReturn
} from './useSendMessage';

// Re-export existing hooks
export { useMessageSending } from './useMessageSending';
export type {
  MessageSendingDependencies,
  UseMessageSendingOptions,
  UseMessageSendingReturn
} from './useMessageSending';

export { useTokenProgress } from './useTokenProgress';
export type {
  UseTokenProgressOptions,
  UseTokenProgressReturn
} from './useTokenProgress';
