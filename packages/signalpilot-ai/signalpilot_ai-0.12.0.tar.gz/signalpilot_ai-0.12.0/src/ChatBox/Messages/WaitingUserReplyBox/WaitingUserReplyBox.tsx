/**
 * WaitingUserReplyBox Component
 *
 * Displays a waiting state when the AI is paused and needs user input.
 * Shows prompt suggestion buttons and a continue button.
 *
 * Features:
 * - Informational text explaining the pause
 * - Dynamic prompt buttons (suggested responses)
 * - Continue button for simple continuation
 * - Visibility controlled via Zustand store
 *
 * @example
 * ```tsx
 * <WaitingUserReplyBox
 *   onPromptClick={(prompt) => sendMessage(prompt)}
 * />
 * ```
 */
import React, { useCallback, useState, useEffect } from 'react';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useChatboxStore } from '@/stores/chatboxStore';
import {
  useWaitingReplyStore,
  selectIsVisible,
  selectRecommendedPrompts
} from '@/stores/waitingReplyStore';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { isLauncherNotebookId } from '@/stores/chatModeStore';
import { CheckpointManager } from '@/Services/CheckpointManager';
import { ICheckpoint } from '@/types';
import { getIsDemoActivelyRunning } from '@/Demo/demo';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface WaitingUserReplyBoxProps {
  /**
   * Callback when a prompt button is clicked
   * @param prompt - The prompt text to send
   */
  onPromptClick?: (prompt: string) => void;

  /**
   * Callback when continue button is clicked
   */
  onContinueClick?: () => void;

  /**
   * Override visibility (for imperative usage)
   * If undefined, uses store state
   */
  isVisible?: boolean;

  /**
   * Override prompt buttons (for imperative usage)
   * If undefined, uses store state
   */
  promptButtons?: string[];
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * WaitingUserReplyBox - Shows waiting state with prompt suggestions
 *
 * CSS Classes:
 * - .sage-ai-waiting-reply-container: Main container
 * - .sage-ai-waiting-reply-container.visible: When visible
 * - .sage-ai-waiting-reply-text: Informational text
 * - .sage-ai-prompt-buttons-container: Container for prompt buttons
 * - .sage-ai-prompt-button: Individual prompt button
 * - .sage-ai-continue-button: Continue button
 */
export const WaitingUserReplyBox: React.FC<WaitingUserReplyBoxProps> = ({
  onPromptClick,
  onContinueClick,
  isVisible: propIsVisible,
  promptButtons: propPromptButtons
}) => {
  // ─────────────────────────────────────────────────────────────
  // Store State (using waitingReplyStore as single source of truth)
  // ─────────────────────────────────────────────────────────────

  const storeIsVisible = useWaitingReplyStore(selectIsVisible);
  const storePromptButtons = useWaitingReplyStore(selectRecommendedPrompts);

  // Use props if provided, otherwise use store
  const isVisible = propIsVisible ?? storeIsVisible;
  const promptButtons = propPromptButtons ?? storePromptButtons;
  const showContinueButton = promptButtons.length === 0;

  // Check if demo is actively running to disable buttons
  const [isDemoRunning, setIsDemoRunning] = useState(
    getIsDemoActivelyRunning()
  );

  // Poll for demo state changes (since it's not a reactive store)
  useEffect(() => {
    if (!isVisible) return;

    const checkDemoState = () => {
      const running = getIsDemoActivelyRunning();
      if (running !== isDemoRunning) {
        setIsDemoRunning(running);
      }
    };

    // Check immediately and then periodically
    checkDemoState();
    const interval = setInterval(checkDemoState, 500);

    return () => clearInterval(interval);
  }, [isVisible, isDemoRunning]);

  // ─────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────

  /**
   * Send a message to the LLM through the conversation service
   */
  const sendMessageToLLM = useCallback(
    async (message: string) => {
      const { services, isProcessingMessage, setIsProcessingMessage } =
        useChatboxStore.getState();
      const { conversationService } = services;

      // User explicitly clicking a prompt button should always send the message
      // Reset the processing flag if it's stuck from a previous session
      if (isProcessingMessage) {
        console.log(
          '[WaitingUserReplyBox] Resetting stuck isProcessingMessage flag'
        );
        setIsProcessingMessage(false);
      }

      if (!conversationService) {
        console.error('[WaitingUserReplyBox] No conversationService available');
        if (onPromptClick) {
          onPromptClick(message);
        }
        return;
      }

      try {
        setIsProcessingMessage(true);

        const store = useChatMessagesStore.getState();

        // Generate message ID
        const id = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

        // Create the user message for the LLM
        const userMessage = {
          role: 'user' as const,
          content: message,
          id
        };

        // Add to LLM history FIRST so checkpoint captures it
        store.addToLlmHistory(userMessage);

        // Create checkpoint (skip for launcher context)
        let checkpoint: ICheckpoint | undefined;
        const notebookId = useNotebookEventsStore.getState().currentNotebookId;
        const threadId = useChatMessagesStore.getState().currentThreadId;
        if (notebookId && threadId && !isLauncherNotebookId(notebookId)) {
          try {
            const checkpointManager = CheckpointManager.getInstance();
            checkpointManager.setCurrentNotebookId(notebookId);
            const storeAfterHistory = useChatMessagesStore.getState();
            checkpoint = checkpointManager.createCheckpoint(
              message,
              storeAfterHistory.llmHistory,
              storeAfterHistory.mentionContexts,
              threadId,
              id
            );
          } catch (error) {
            console.error('[WaitingUserReplyBox] Error creating checkpoint:', error);
          }
        }

        // Add user message to the UI with checkpoint
        store.addUserMessage(message, checkpoint);

        console.log('[WaitingUserReplyBox] Sending message to LLM:', message);

        // Process the conversation
        await conversationService.processConversation(
          [userMessage],
          [],
          'agent'
        );
      } catch (error) {
        console.error('[WaitingUserReplyBox] Error sending message:', error);
      }
    },
    [onPromptClick]
  );

  /**
   * Handle prompt button click
   */
  const handlePromptClick = useCallback(
    (prompt: string) => {
      console.log('[WaitingUserReplyBox] Prompt button clicked:', prompt);

      // Hide waiting reply box via store
      useWaitingReplyStore.getState().hide();

      // Send the message to the LLM
      void sendMessageToLLM(prompt);
    },
    [sendMessageToLLM]
  );

  /**
   * Handle continue button click
   */
  const handleContinueClick = useCallback(() => {
    console.log('[WaitingUserReplyBox] Continue button clicked');

    // Hide waiting reply box via store
    useWaitingReplyStore.getState().hide();

    // Send continue message to the LLM
    void sendMessageToLLM('Continue');
  }, [sendMessageToLLM]);

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  // Build container classes
  const containerClasses = [
    'sage-ai-waiting-reply-container',
    isVisible && 'visible'
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={containerClasses}>
      {/* Informational text */}
      <div className="sage-ai-waiting-reply-text">
        {isDemoRunning
          ? 'Demo in progress - buttons disabled'
          : 'SignalPilot will continue working after you reply'}
      </div>

      {/* Prompt buttons container */}
      <div
        className="sage-ai-prompt-buttons-container"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          marginTop: '12px'
        }}
      >
        {promptButtons.map((prompt, index) => (
          <button
            key={`prompt-${index}-${prompt}`}
            className="sage-ai-prompt-button"
            onClick={() => handlePromptClick(prompt)}
            disabled={isDemoRunning}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Continue button (shown when no specific prompts or as fallback) */}
      {showContinueButton && (
        <button
          className="sage-ai-continue-button"
          onClick={handleContinueClick}
          disabled={isDemoRunning}
        >
          Continue
        </button>
      )}
    </div>
  );
};

export default WaitingUserReplyBox;
