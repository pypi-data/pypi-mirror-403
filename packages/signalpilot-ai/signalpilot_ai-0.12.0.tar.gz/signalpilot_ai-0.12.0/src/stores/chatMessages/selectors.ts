/**
 * ChatMessages Store Selectors
 *
 * Selector functions for accessing store state.
 */

import { IChatMessagesStore } from './types';

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectMessages = (state: IChatMessagesStore) => state.messages;
export const selectLlmHistory = (state: IChatMessagesStore) => state.llmHistory;
export const selectStreaming = (state: IChatMessagesStore) => state.streaming;
export const selectIsStreaming = (state: IChatMessagesStore) =>
  state.streaming.isStreaming;
export const selectStreamingText = (state: IChatMessagesStore) =>
  state.streaming.text;
export const selectIsThinking = (state: IChatMessagesStore) => state.isThinking;
export const selectSpecialDisplay = (state: IChatMessagesStore) =>
  state.specialDisplay;
export const selectLastMessageType = (state: IChatMessagesStore) =>
  state.lastMessageType;
export const selectCurrentThreadId = (state: IChatMessagesStore) =>
  state.currentThreadId;
export const selectMentionContexts = (state: IChatMessagesStore) =>
  state.mentionContexts;
export const selectScrollState = (state: IChatMessagesStore) =>
  state.scrollState;
export const selectScrollToBottomCounter = (state: IChatMessagesStore) =>
  state.scrollState.scrollToBottomCounter;
