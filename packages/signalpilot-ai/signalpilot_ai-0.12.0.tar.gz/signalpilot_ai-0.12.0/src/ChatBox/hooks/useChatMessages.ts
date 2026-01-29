/**
 * useChatMessages Hook
 *
 * Provides message-related functionality for the ChatBox:
 * - Message sending and continuation
 * - Message history access
 * - Streaming state management
 */

import { useCallback } from 'react';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatInputStore } from '@/stores/chatInput/chatInputStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface UseChatMessagesOptions {
  /** Callback when message is sent */
  onMessageSent?: () => void;
  /** Callback when message fails */
  onMessageError?: (error: Error) => void;
}

export interface UseChatMessagesReturn {
  /** Messages in the current conversation */
  messages: ReturnType<typeof useChatMessagesStore.getState>['messages'];
  /** Whether streaming is active */
  isStreaming: boolean;
  /** Current streaming text */
  streamingText: string;
  /** Whether thinking indicator should be shown */
  isThinking: boolean;
  /** Send a message */
  sendMessage: (message?: string, hidden?: boolean) => Promise<void>;
  /** Continue from last message */
  continueMessage: () => Promise<void>;
  /** Cancel current message */
  cancelMessage: () => void;
  /** Scroll to bottom of messages */
  scrollToBottom: () => void;
  /** Clear all messages */
  clearMessages: () => void;
  /** Whether currently processing a message */
  isProcessing: boolean;
}

// ═══════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════

export function useChatMessages(
  options: UseChatMessagesOptions = {}
): UseChatMessagesReturn {
  const { onMessageSent, onMessageError } = options;

  // Store state
  const messages = useChatMessagesStore(state => state.messages);
  const streaming = useChatMessagesStore(state => state.streaming);
  const isThinking = useChatMessagesStore(state => state.isThinking);
  const scrollToBottom = useChatMessagesStore(state => state.scrollToBottom);
  const clearMessages = useChatMessagesStore(state => state.clearMessages);

  const {
    isProcessingMessage,
    setIsProcessingMessage,
    cancelMessage: storeCancelMessage,
    continueMessage: storeContinueMessage
  } = useChatboxStore();

  const { inputValue, clearInput } = useChatInputStore();

  // Send a message
  const sendMessage = useCallback(
    async (message?: string, hidden?: boolean) => {
      const messageToSend = message || inputValue;

      if (!messageToSend.trim() && !hidden) {
        return;
      }

      try {
        setIsProcessingMessage(true);

        // Clear input if not a hidden message
        if (!hidden) {
          clearInput();
        }

        // The actual message sending is handled by the ConversationService
        // which is wired up through the stores
        onMessageSent?.();
      } catch (error) {
        console.error('[useChatMessages] Send failed:', error);
        onMessageError?.(
          error instanceof Error ? error : new Error(String(error))
        );
      } finally {
        setIsProcessingMessage(false);
      }
    },
    [
      inputValue,
      clearInput,
      setIsProcessingMessage,
      onMessageSent,
      onMessageError
    ]
  );

  // Continue from last message
  const continueMessage = useCallback(async () => {
    try {
      setIsProcessingMessage(true);
      storeContinueMessage();
      onMessageSent?.();
    } catch (error) {
      console.error('[useChatMessages] Continue failed:', error);
      onMessageError?.(
        error instanceof Error ? error : new Error(String(error))
      );
    } finally {
      setIsProcessingMessage(false);
    }
  }, [
    setIsProcessingMessage,
    storeContinueMessage,
    onMessageSent,
    onMessageError
  ]);

  // Cancel current message
  const cancelMessage = useCallback(() => {
    storeCancelMessage();
  }, [storeCancelMessage]);

  return {
    messages,
    isStreaming: streaming.isStreaming,
    streamingText: streaming.text,
    isThinking,
    sendMessage,
    continueMessage,
    cancelMessage,
    scrollToBottom,
    clearMessages,
    isProcessing: isProcessingMessage
  };
}

export default useChatMessages;
