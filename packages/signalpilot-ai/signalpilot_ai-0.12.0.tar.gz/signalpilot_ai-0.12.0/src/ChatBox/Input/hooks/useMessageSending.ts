/**
 * useMessageSending Hook
 *
 * Handles the core message sending logic:
 * - Validates input and dependencies
 * - Processes @mentions into context tags
 * - Sends messages via ConversationService
 * - Manages processing state and error handling
 * - Supports hidden messages (for compression, etc.)
 */
import { useCallback, useRef } from 'react';
import { IChatService } from '@/LLM/IChatService';
import { ConversationService } from '@/LLM';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ChatUIHelper } from '@/ChatBox/services/ChatUIHelper';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { usePlanStateStore } from '@/stores/planStateStore';
import { useWaitingReplyStore } from '@/stores/waitingReplyStore';
import { NotebookCellStateService } from '@/Services/NotebookCellStateService';
import { convertMentionsToContextTags } from '@/utils/contextTagUtils';
import { ChatRequestStatus, ICheckpoint } from '@/types';
import { useChatStore } from '@/stores/chat';
import { useChatInputStore } from '@/stores/chatInput';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import {
  buildContextMessage,
  buildWorkingDirectoryMessage
} from '@/ChatBox/utils/contextUtils';

export interface MessageSendingDependencies {
  chatService: IChatService;
  conversationService: ConversationService;
  messageComponent: ChatMessages;
  uiHelper: ChatUIHelper;
  chatHistoryManager?: ChatHistoryManager | null;
}

export interface UseMessageSendingOptions {
  dependencies: MessageSendingDependencies | null;
  activeContexts: Map<string, IMentionContext>;
  onResetChat?: () => void;
  onMessageSent?: () => void;
  onAddToHistory?: (message: string) => void;
  clearInput?: () => void;
}

export interface UseMessageSendingReturn {
  /** Send a message to the AI */
  sendMessage: (cellContext?: string, hidden?: boolean) => Promise<void>;
  /** Continue the conversation without new user input */
  continueMessage: (cellContext?: string) => Promise<void>;
  /** Check if currently processing */
  isProcessing: boolean;
  /** Set a checkpoint to restore after sending */
  setCheckpointToRestore: (checkpoint: ICheckpoint | null) => void;
  /** Get the current checkpoint */
  getCheckpointToRestore: () => ICheckpoint | null;
}

/**
 * Hook for message sending and conversation flow.
 *
 * Handles:
 * - Input validation
 * - @mention to context tag conversion
 * - Conversation processing via ConversationService
 * - Error handling (auth errors, general errors)
 * - Processing state management
 * - Notebook state caching
 */
export function useMessageSending({
  dependencies,
  activeContexts,
  onResetChat,
  onMessageSent,
  onAddToHistory,
  clearInput
}: UseMessageSendingOptions): UseMessageSendingReturn {
  const checkpointRef = useRef<ICheckpoint | null>(null);

  // Get mode from chat store
  const mode = useChatStore(state => state.mode);
  const setProcessing = useChatStore(state => state.setProcessing);
  const isProcessing = useChatStore(state => state.isProcessing);

  // Get input value from input store
  const inputValue = useChatInputStore(state => state.inputValue);

  /**
   * Send a message to the AI service.
   * @param cellContext Optional cell context to include
   * @param hidden If true, don't show the message in UI
   */
  const sendMessage = useCallback(
    async (cellContext?: string, hidden?: boolean): Promise<void> => {
      const perfStart = performance.now();
      console.log('[PERF] useMessageSending.sendMessage - START');

      // Check dependencies
      if (!dependencies) {
        console.error(
          '[useMessageSending] Dependencies not set. Cannot send message.'
        );
        return;
      }

      const {
        chatService,
        conversationService,
        messageComponent,
        uiHelper,
        chatHistoryManager
      } = dependencies;

      const userInput = inputValue.trim();
      if (!userInput || isProcessing) {
        return;
      }

      // Handle checkpoint restoration
      if (checkpointRef.current) {
        await conversationService.finishCheckpointRestoration(
          checkpointRef.current
        );
        checkpointRef.current = null;
      }

      // Hide waiting reply box when user sends a message
      useWaitingReplyStore.getState().hide();

      // Handle reset command
      if (userInput.toLowerCase() === 'reset') {
        onResetChat?.();
        clearInput?.();
        return;
      }

      // Add to history
      onAddToHistory?.(userInput);

      // Notify message sent (triggers switch to history widget)
      onMessageSent?.();

      // Set processing state
      setProcessing(true);
      usePlanStateStore.getState().setLoading(true);

      // Reset LLM state display
      uiHelper.resetToGeneratingState('Generating...');

      // Check API initialization
      if (!chatService.isInitialized()) {
        messageComponent.addSystemMessage(
          '❌ API key is not set. Please configure it in the settings.'
        );
        setProcessing(false);
        usePlanStateStore.getState().setLoading(false);
        uiHelper.hideLoadingIndicator();
        return;
      }

      const systemMessages: string[] = [];

      // Clear input
      clearInput?.();

      // Convert @mentions to context tags
      const processedResult = convertMentionsToContextTags(
        userInput,
        activeContexts
      );
      const processedUserInput = processedResult.message;
      const unresolvedMentions = processedResult.unresolvedMentions;
      console.log('[useMessageSending] Original message:', userInput);
      console.log(
        '[useMessageSending] Processed message with context tags:',
        processedUserInput
      );
      if (unresolvedMentions.length > 0) {
        console.log(
          '[useMessageSending] Unresolved mentions:',
          unresolvedMentions
        );
      }

      // Display user message in UI
      messageComponent.addUserMessage(processedUserInput, hidden);

      // Create message for API
      const newUserMessage = { role: 'user', content: processedUserInput };

      try {
        // Ensure conversation service knows the notebook
        const currentNotebookId =
          useNotebookEventsStore.getState().currentNotebookId;
        if (currentNotebookId) {
          conversationService.setNotebookId(currentNotebookId);

          // Detect notebook changes
          const cellChanges =
            await NotebookCellStateService.detectChanges(currentNotebookId);
          const changesSummary =
            NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
          if (changesSummary) {
            systemMessages.push(changesSummary);
            console.log(
              '[useMessageSending] Detected notebook changes, added to system messages'
            );
          }
        }

        const messages = [newUserMessage];

        if (cellContext) {
          systemMessages.push(cellContext);
        }

        const mentionContexts = messageComponent.getMentionContexts();
        if (mentionContexts.size > 0) {
          systemMessages.push(buildContextMessage(mentionContexts));
        }

        systemMessages.push(buildWorkingDirectoryMessage());

        // Add message about unresolved mentions if any
        if (unresolvedMentions.length > 0) {
          const mentionList = unresolvedMentions.map(m => `@${m}`).join(', ');
          systemMessages.push(
            `The following mentions could not be resolved: ${mentionList}. ` +
              `The context for these mentions was not found. ` +
              `Please ask the user to add these contexts again using the @ mention feature, or proceed without them.`
          );
        }

        // Clear diffs before processing
        getNotebookDiffManager().clearDiffs();

        const perfBeforeConversation = performance.now();
        console.log(
          `[PERF] useMessageSending.sendMessage - Before processConversation (${(perfBeforeConversation - perfStart).toFixed(2)}ms elapsed)`
        );

        // Process conversation
        await conversationService.processConversation(
          messages,
          systemMessages,
          mode
        );

        const perfAfterConversation = performance.now();
        console.log(
          `[PERF] useMessageSending.sendMessage - After processConversation (${(perfAfterConversation - perfBeforeConversation).toFixed(2)}ms)`
        );

        // Cache notebook state after successful processing
        if (currentNotebookId) {
          await NotebookCellStateService.cacheCurrentNotebookState(
            currentNotebookId
          );
        }
        console.log(
          '[useMessageSending] Cached notebook state after message processing'
        );
      } catch (error) {
        console.error('Error in conversation processing:', error);

        // Only show error if not cancelled
        if (chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);

          // Check for auth errors
          const isAuthError =
            errorMessage.includes('authentication_error') ||
            errorMessage.includes('Invalid API key') ||
            (errorMessage.includes('401') && errorMessage.includes('error'));

          if (isAuthError) {
            messageComponent.displaySubscriptionCard();
          } else {
            messageComponent.addErrorMessage(`❌ ${errorMessage}`);
          }
        }
      } finally {
        setProcessing(false);
        usePlanStateStore.getState().setLoading(false);
      }
    },
    [
      dependencies,
      inputValue,
      isProcessing,
      activeContexts,
      mode,
      setProcessing,
      onResetChat,
      onAddToHistory,
      onMessageSent,
      clearInput
    ]
  );

  /**
   * Continue the conversation without new user input.
   * Used for continuation after tool calls, etc.
   */
  const continueMessage = useCallback(
    async (cellContext?: string): Promise<void> => {
      if (!dependencies) {
        console.error(
          '[useMessageSending] Dependencies not set. Cannot continue message.'
        );
        return;
      }

      if (isProcessing) {
        return;
      }

      const {
        chatService,
        conversationService,
        messageComponent,
        uiHelper,
        chatHistoryManager
      } = dependencies;

      // Handle checkpoint restoration
      if (checkpointRef.current) {
        await conversationService.finishCheckpointRestoration(
          checkpointRef.current
        );
        checkpointRef.current = null;
      }

      // Hide waiting reply box
      useWaitingReplyStore.getState().hide();

      // Set processing state
      setProcessing(true);
      usePlanStateStore.getState().setLoading(true);

      // Reset LLM state display
      uiHelper.resetToGeneratingState('Generating...');

      // Check API initialization
      if (!chatService.isInitialized()) {
        messageComponent.addSystemMessage(
          '❌ API key is not set. Please configure it in the settings.'
        );
        setProcessing(false);
        usePlanStateStore.getState().setLoading(false);
        uiHelper.hideLoadingIndicator();
        return;
      }

      const systemMessages: string[] = [];

      try {
        // Ensure conversation service knows the notebook
        const currentNotebookId =
          useNotebookEventsStore.getState().currentNotebookId;
        if (currentNotebookId) {
          conversationService.setNotebookId(currentNotebookId);

          // Detect notebook changes
          const cellChanges =
            await NotebookCellStateService.detectChanges(currentNotebookId);
          const changesSummary =
            NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
          if (changesSummary) {
            systemMessages.push(changesSummary);
            console.log(
              '[useMessageSending] Detected notebook changes, added to system messages'
            );
          }
        }

        // No new user message for continue
        const messages: Array<{ role: string; content: string }> = [];

        if (cellContext) {
          systemMessages.push(cellContext);
        }

        const mentionContexts = messageComponent.getMentionContexts();
        if (mentionContexts.size > 0) {
          systemMessages.push(buildContextMessage(mentionContexts));
        }

        systemMessages.push(buildWorkingDirectoryMessage());

        // Clear diffs before processing
        getNotebookDiffManager().clearDiffs();

        // Process conversation
        await conversationService.processConversation(
          messages,
          systemMessages,
          mode
        );

        // Cache notebook state after successful processing
        if (currentNotebookId) {
          await NotebookCellStateService.cacheCurrentNotebookState(
            currentNotebookId
          );
        }
        console.log(
          '[useMessageSending] Cached notebook state after continuing message'
        );
      } catch (error) {
        console.error('Error in conversation processing:', error);

        // Only show error if not cancelled
        if (chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);

          // Check for auth errors
          const isAuthError =
            errorMessage.includes('authentication_error') ||
            errorMessage.includes('Invalid API key') ||
            (errorMessage.includes('401') && errorMessage.includes('error'));

          if (isAuthError) {
            messageComponent.displaySubscriptionCard();
          } else {
            messageComponent.addErrorMessage(`❌ ${errorMessage}`);
          }
        }
      } finally {
        setProcessing(false);
        usePlanStateStore.getState().setLoading(false);

        // Reset needsContinue flag
        const currentThread = chatHistoryManager?.getCurrentThread();
        if (currentThread && currentThread.needsContinue) {
          currentThread.needsContinue = false;
          console.log(
            '[useMessageSending] Set needsContinue to false after continueMessage finished'
          );
        }
      }
    },
    [dependencies, isProcessing, mode, setProcessing]
  );

  const setCheckpointToRestore = useCallback(
    (checkpoint: ICheckpoint | null) => {
      checkpointRef.current = checkpoint;
    },
    []
  );

  const getCheckpointToRestore = useCallback(() => {
    return checkpointRef.current;
  }, []);

  return {
    sendMessage,
    continueMessage,
    isProcessing,
    setCheckpointToRestore,
    getCheckpointToRestore
  };
}
