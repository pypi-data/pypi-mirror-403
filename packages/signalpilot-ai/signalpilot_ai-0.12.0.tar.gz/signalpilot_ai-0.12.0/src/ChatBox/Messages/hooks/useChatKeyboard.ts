/**
 * useChatKeyboard Hook
 *
 * Handles keyboard shortcuts for the chat panel:
 * - Cmd/Ctrl+Enter: Click first prompt button when waiting for reply
 *
 * @example
 * ```tsx
 * const { } = useChatKeyboard({
 *   onContinue: () => sendMessage('Continue'),
 *   enabled: waitingReply.isVisible
 * });
 * ```
 */

import { useCallback, useEffect } from 'react';
import {
  useWaitingReplyStore,
  selectIsVisible
} from '@/stores/waitingReplyStore';

export interface UseChatKeyboardOptions {
  /** Callback when continue shortcut is triggered */
  onContinue?: () => void;
  /** Whether keyboard shortcuts are enabled */
  enabled?: boolean;
}

export interface UseChatKeyboardResult {
  /** Nothing returned for now, hook manages side effects */
}

export function useChatKeyboard(
  options: UseChatKeyboardOptions = {}
): UseChatKeyboardResult {
  const { onContinue, enabled = true } = options;

  const waitingReplyVisible = useWaitingReplyStore(selectIsVisible);

  /**
   * Handle keyboard shortcuts
   */
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Cmd+Enter (macOS) or Ctrl+Enter (Windows/Linux)
      if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
        // Only trigger if waiting for reply
        if (!waitingReplyVisible) return;

        event.preventDefault();
        event.stopPropagation();

        // Use first prompt button or default to "Continue"
        if (onContinue) {
          onContinue();
        }
      }
    },
    [enabled, waitingReplyVisible, onContinue]
  );

  /**
   * Attach keyboard listener
   */
  useEffect(() => {
    if (!enabled) return;

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);

  return {};
}

export default useChatKeyboard;
