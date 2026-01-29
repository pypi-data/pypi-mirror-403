/**
 * ChatMessages Store Subscribers
 *
 * Non-React API for subscribing to store changes from TypeScript services.
 */

import { useChatMessagesStore } from './store';
import { ChatUIMessage, IChatMessagesState, IStreamingState } from './types';
import { IChatMessage } from '../../types';

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getChatMessagesState = () => useChatMessagesStore.getState();

/**
 * Subscribe to store changes (for use outside React)
 */
export const subscribeToChatMessages = (
  callback: (state: IChatMessagesState) => void
) => {
  return useChatMessagesStore.subscribe(callback);
};

/**
 * Subscribe to specific state changes
 */
export const subscribeToMessages = (
  callback: (messages: ChatUIMessage[]) => void
) => {
  return useChatMessagesStore.subscribe(state => state.messages, callback);
};

export const subscribeToLlmHistory = (
  callback: (history: IChatMessage[]) => void
) => {
  return useChatMessagesStore.subscribe(state => state.llmHistory, callback);
};

/**
 * Subscribe to scroll to bottom requests
 */
export const subscribeToScrollToBottom = (
  callback: (counter: number) => void
) => {
  return useChatMessagesStore.subscribe(
    state => state.scrollState.scrollToBottomCounter,
    callback
  );
};

/**
 * Subscribe to streaming state changes
 */
export const subscribeToStreaming = (
  callback: (streaming: IStreamingState) => void
) => {
  return useChatMessagesStore.subscribe(state => state.streaming, callback);
};
