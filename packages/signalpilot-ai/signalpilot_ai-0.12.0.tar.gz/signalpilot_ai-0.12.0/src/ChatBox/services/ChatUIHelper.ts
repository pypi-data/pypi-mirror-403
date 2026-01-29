import { ChatMessages } from './ChatMessagesService';
import { LLMStateDisplay } from '@/ChatBox/StateDisplay/LLMStateDisplay';

/**
 * Helper class for LLM state display management.
 *
 * This class provides a thin wrapper around LLMStateDisplay and ChatMessages
 * for managing loading states during message processing.
 *
 * Note: Button state management (updateSendButton, disableSendButton, updateAgentModeElement)
 * has been removed as these are now handled by React components (SendButton, ModeSelector).
 */
export class ChatUIHelper {
  private messageComponent: ChatMessages;
  private llmStateDisplay: LLMStateDisplay;
  private isShowingConfirmation: boolean = false;

  constructor(
    _chatHistory: HTMLDivElement, // Kept for API compatibility, not used
    messageComponent: ChatMessages,
    llmStateDisplay: LLMStateDisplay
  ) {
    this.messageComponent = messageComponent;
    this.llmStateDisplay = llmStateDisplay;
  }

  /**
   * Set whether a confirmation dialog is currently showing
   */
  public setShowingConfirmation(isShowing: boolean): void {
    this.isShowingConfirmation = isShowing;
  }

  /**
   * Reset the LLM state display to generating state, clearing any diff or tool state.
   * This is used when starting a new message to ensure we show the generating state.
   */
  public resetToGeneratingState(text: string = 'Generating...'): void {
    // Hide the waiting reply box since LLM is now generating
    this.messageComponent.hideWaitingReplyBox();
    // Force show LLM state display in generating mode, clearing any existing state
    this.llmStateDisplay.show(text);
  }

  /**
   * Update the loading indicator.
   * Uses LLM state display with priority logic.
   */
  public updateLoadingIndicator(text: string = 'Generating...'): void {
    // Don't show loading indicator during confirmation dialogs
    if (this.isShowingConfirmation) {
      this.llmStateDisplay.hide();
      return;
    }

    // Don't override diff state or tool state - they have higher priority
    if (
      this.llmStateDisplay.isDiffState() ||
      this.llmStateDisplay.isUsingToolState()
    ) {
      return;
    }

    // Hide the waiting reply box since LLM is now generating
    this.messageComponent.hideWaitingReplyBox();
    // Show LLM state display with the status text
    this.llmStateDisplay.show(text);
  }

  /**
   * Remove the loading indicator (no-op, kept for API compatibility)
   */
  public removeLoadingIndicator(): void {}

  /**
   * Hide the loading indicator
   */
  public hideLoadingIndicator(): void {
    this.llmStateDisplay.hide();
  }
}
