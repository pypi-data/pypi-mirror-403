/**
 * ChatInputContainer exports
 *
 * React-based chat input management component that replaces
 * the imperative ChatInputManager class.
 */
export { ChatInputContainer } from './ChatInputContainer';
export type {
  ChatInputContainerProps,
  ChatInputContainerRef,
  ChatInputDependencies,
  ChatMode,
  CellContext
} from './types';

// Re-export hooks for external use
export {
  useMessageHistory,
  useMessageSending,
  useTokenProgress
} from './hooks';
