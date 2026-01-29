/**
 * useTokenProgress Hook
 *
 * Manages token progress calculation and display.
 * Handles token counting from message history and compression requests.
 */
import { useCallback } from 'react';
import { IChatMessage } from '@/types';
import { checkTokenLimit, MAX_RECOMMENDED_TOKENS } from '@/utils/tokenUtils';
import { useChatInputStore } from '@/stores/chatInput';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';

export interface UseTokenProgressOptions {
  messageComponent: ChatMessages | null;
  onCompressRequest?: (message: string) => Promise<void>;
  onTokenPercentageChange?: (percentage: number) => void;
}

export interface UseTokenProgressReturn {
  /** Current token count */
  tokenCount: number;
  /** Whether currently compacting */
  isCompacting: boolean;
  /** Maximum recommended tokens */
  maxTokens: number;
  /** Update token progress from messages */
  updateTokenProgress: (messages?: IChatMessage[]) => void;
  /** Handle compress history request */
  handleCompact: () => Promise<void>;
}

/**
 * Hook for managing token progress and compression.
 *
 * Features:
 * - Calculates tokens from persisted usage data or estimation
 * - Updates progress indicator
 * - Handles compression requests
 * - Notifies parent of token percentage changes
 */
export function useTokenProgress({
  messageComponent,
  onCompressRequest,
  onTokenPercentageChange
}: UseTokenProgressOptions): UseTokenProgressReturn {
  const { currentTokenCount, isCompacting, setTokenCount, setCompacting } =
    useChatInputStore();

  /**
   * Update token progress from message history.
   * Uses persisted usage data when available, falls back to estimation.
   */
  const updateTokenProgress = useCallback(
    (messages?: IChatMessage[]) => {
      const conversationHistory =
        messages || messageComponent?.getMessageHistory() || [];

      // Try to calculate from persisted usage data first
      let totalTokens = 0;
      let hasUsageData = false;

      for (const message of conversationHistory) {
        if (message.usage) {
          hasUsageData = true;
          // Sum: cache_creation + cache_read + input + output tokens
          totalTokens +=
            (message.usage.cache_creation_input_tokens || 0) +
            (message.usage.cache_read_input_tokens || 0) +
            (message.usage.input_tokens || 0) +
            (message.usage.output_tokens || 0);
        }
      }

      // Fall back to estimation if no usage data
      const tokenLimitCheck = checkTokenLimit(conversationHistory);
      const actualTokens = hasUsageData
        ? totalTokens
        : tokenLimitCheck.estimatedTokens;

      // Update store
      setTokenCount(actualTokens);

      // Calculate percentage for CTA visibility
      const percentage = Math.min(
        Math.round((actualTokens / MAX_RECOMMENDED_TOKENS) * 100),
        100
      );

      // Notify parent of percentage change
      onTokenPercentageChange?.(percentage);
    },
    [messageComponent, setTokenCount, onTokenPercentageChange]
  );

  /**
   * Handle compress history button click.
   * Sends a hidden message to trigger compression.
   */
  const handleCompact = useCallback(async () => {
    if (!messageComponent || isCompacting) {
      return;
    }

    setCompacting(true);

    try {
      // Request compression via callback
      if (onCompressRequest) {
        await onCompressRequest(
          'Please compress the chat history to reduce token usage. Keep the 10 most recent messages uncompressed.'
        );
      }
    } catch (error) {
      console.error('[useTokenProgress] Error compressing:', error);
      messageComponent.addSystemMessage(
        `⚠️ Error compressing chat history: ${error instanceof Error ? error.message : String(error)}`
      );
    } finally {
      // Re-enable after short delay
      setTimeout(() => {
        setCompacting(false);
      }, 500);
    }
  }, [messageComponent, isCompacting, setCompacting, onCompressRequest]);

  return {
    tokenCount: currentTokenCount,
    isCompacting,
    maxTokens: MAX_RECOMMENDED_TOKENS,
    updateTokenProgress,
    handleCompact
  };
}
