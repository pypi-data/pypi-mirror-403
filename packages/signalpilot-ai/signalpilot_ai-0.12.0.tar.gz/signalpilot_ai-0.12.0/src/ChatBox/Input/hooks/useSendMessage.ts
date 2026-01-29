/**
 * useSendMessage Hook
 *
 * Handles sending and continuing messages to the AI service.
 * Contains the core business logic for message processing.
 */
import { useCallback, useState } from 'react';
import { ChatInputDependencies } from '../types';
import { useChatStore } from '@/stores/chat';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatUIStore } from '@/stores/chatUIStore';
import { usePlanStateStore } from '@/stores/planStateStore';
import { useWaitingReplyStore } from '@/stores/waitingReplyStore';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { NotebookCellStateService } from '@/Services/NotebookCellStateService';
import { convertMentionsToContextTags } from '@/utils/contextTagUtils';
import { ChatRequestStatus, DiffApprovalStatus, ICheckpoint } from '@/types';
import { ConversationService } from '@/LLM/ConversationService';
import { useDiffStore } from '@/stores/diffStore';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import {
  buildContextMessage,
  buildWorkingDirectoryMessage
} from '@/ChatBox/utils/contextUtils';

export interface UseSendMessageOptions {
  dependencies: ChatInputDependencies | null;
  chatHistoryManager?: ChatHistoryManager | null;
  activeContexts: Map<string, IMentionContext>;
  modeName: 'agent' | 'ask' | 'fast';
  getInputValue: () => string;
  clearInput: () => void;
  addToHistory: (message: string) => void;
  onResetChat?: () => void;
  onMessageSent?: () => void;
}

export interface UseSendMessageReturn {
  sendMessage: (
    cellContext?: string,
    hidden?: boolean,
    directMessage?: string
  ) => Promise<void>;
  continueMessage: (cellContext?: string) => Promise<void>;
  isProcessingMessage: boolean;
  setIsProcessingMessage: (value: boolean) => void;
  checkpointToRestore: ICheckpoint | null;
  setCheckpointToRestore: (checkpoint: ICheckpoint | null) => void;
}

export function useSendMessage({
  dependencies,
  chatHistoryManager,
  activeContexts,
  modeName,
  getInputValue,
  clearInput,
  addToHistory,
  onResetChat,
  onMessageSent
}: UseSendMessageOptions): UseSendMessageReturn {
  const [isProcessingMessage, setIsProcessingMessageState] = useState(false);

  // Read checkpoint from the store (set by useChatCheckpoint.restore())
  const checkpointToRestore = useChatMessagesStore(
    state => state.checkpointToRestore
  );
  const setCheckpointToRestore = useChatMessagesStore(
    state => state.setCheckpointToRestore
  );

  const setIsProcessingMessage = useCallback((value: boolean) => {
    setIsProcessingMessageState(value);
    useChatStore.getState().setProcessing(value);
    useChatboxStore.getState().setIsProcessingMessage(value);
    // Hide new chat display when processing starts
    if (value) {
      useChatUIStore.getState().setShowNewChatDisplay(false);
    }
  }, []);

  /**
   * Send a message to the AI service
   */
  const sendMessage = useCallback(
    async (
      cellContext?: string,
      hidden?: boolean,
      directMessage?: string
    ): Promise<void> => {
      const perfStart = performance.now();
      console.log('[PERF] useSendMessage.sendMessage - START');

      // Enhanced dependency logging
      console.log('[useSendMessage] Checking dependencies:', {
        hasDependencies: !!dependencies,
        chatService: !!dependencies?.chatService,
        conversationService: !!dependencies?.conversationService,
        messageComponent: !!dependencies?.messageComponent,
        uiHelper: !!dependencies?.uiHelper
      });

      if (!dependencies) {
        console.error(
          '[useSendMessage] Dependencies not set - this indicates services were not initialized'
        );
        console.error(
          '[useSendMessage] Check useChatBoxInit logs for initialization issues'
        );
        return;
      }

      const { chatService, conversationService, messageComponent, uiHelper } =
        dependencies;

      // Use directMessage if provided, otherwise read from input
      const userInput = directMessage || getInputValue();
      console.log('[useSendMessage] userInput:', userInput);
      if (!userInput) {
        console.log('[useSendMessage] Early return - empty input');
        return;
      }

      if (checkpointToRestore) {
        await conversationService.finishCheckpointRestoration(
          checkpointToRestore
        );
      }

      // Hide waiting reply box
      useWaitingReplyStore.getState().hide();

      // Handle reset command
      if (userInput.toLowerCase() === 'reset') {
        onResetChat?.();
        clearInput();
        return;
      }

      // Add to history
      addToHistory(userInput);

      // Notify message sent
      onMessageSent?.();

      // Set processing state
      setIsProcessingMessage(true);
      usePlanStateStore.getState().setLoading(true);

      // Reset UI state
      uiHelper.resetToGeneratingState('Generating...');

      // Check API initialization
      if (!chatService.isInitialized()) {
        messageComponent.addSystemMessage(
          'API key is not set. Please configure it in the settings.'
        );
        setIsProcessingMessage(false);
        usePlanStateStore.getState().setLoading(false);
        uiHelper.hideLoadingIndicator();
        return;
      }

      const systemMessages: string[] = [];

      // Clear input
      clearInput();

      // Convert mentions to context tags
      const processedResult = convertMentionsToContextTags(
        userInput,
        activeContexts
      );
      const processedUserInput = processedResult.message;
      const unresolvedMentions = processedResult.unresolvedMentions;
      console.log('[useSendMessage] Original:', userInput);
      console.log('[useSendMessage] Processed:', processedUserInput);
      if (unresolvedMentions.length > 0) {
        console.log(
          '[useSendMessage] Unresolved mentions:',
          unresolvedMentions
        );
      }

      // Display user message
      messageComponent.addUserMessage(processedUserInput, hidden);

      const newUserMessage = { role: 'user', content: processedUserInput };

      try {
        const currentNotebookId =
          useNotebookEventsStore.getState().currentNotebookId;
        if (currentNotebookId) {
          conversationService.setNotebookId(currentNotebookId);

          const cellChanges =
            await NotebookCellStateService.detectChanges(currentNotebookId);
          const changesSummary =
            NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
          if (changesSummary) {
            systemMessages.push(changesSummary);
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

        // Force-cancel any stuck conversation before starting a new one.
        // This handles the case where the LLM loop is stuck waiting for diff approval
        // (e.g., user approved without run but the signal didn't unblock the loop).
        if (ConversationService.isInProgress()) {
          console.log(
            '[useSendMessage] Conversation in progress - force-cancelling before new message'
          );

          // Cancel the API request
          chatService.cancelRequest();

          // Finalize any streaming message from the previous conversation
          messageComponent.finalizeStreamingMessage();

          // Emit the finished signal on the diff manager to unblock any waiting promise
          try {
            const diffManager = getNotebookDiffManager();
            diffManager._finishedProcessingDiffs.emit(
              DiffApprovalStatus.APPROVED
            );
          } catch {
            // DiffManager not initialized - nothing to unblock
          }

          // Accept all pending diffs (mark as approved without run)
          const pendingDiffs = useDiffStore.getState().pendingDiffs;
          for (const diff of pendingDiffs.values()) {
            if (!diff.userDecision) {
              diff.userDecision = 'approved';
            }
          }

          // Force-reset the conversation flag
          ConversationService.forceReset();
        }

        getNotebookDiffManager().clearDiffs();

        const perfBeforeConversation = performance.now();
        console.log(
          `[PERF] Before processConversation (${(perfBeforeConversation - perfStart).toFixed(2)}ms)`
        );

        await conversationService.processConversation(
          messages,
          systemMessages,
          modeName
        );

        const perfAfterConversation = performance.now();
        console.log(
          `[PERF] After processConversation (${(perfAfterConversation - perfBeforeConversation).toFixed(2)}ms)`
        );

        if (currentNotebookId) {
          await NotebookCellStateService.cacheCurrentNotebookState(
            currentNotebookId
          );
        }
      } catch (error) {
        console.error('Error in conversation processing:', error);

        if (chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          const isAuthError =
            errorMessage.includes('authentication_error') ||
            errorMessage.includes('Invalid API key') ||
            (errorMessage.includes('401') && errorMessage.includes('error'));

          if (isAuthError) {
            messageComponent.displaySubscriptionCard();
          } else {
            messageComponent.addErrorMessage(`${errorMessage}`);
          }
        }
      } finally {
        setIsProcessingMessage(false);
        usePlanStateStore.getState().setLoading(false);
      }
    },
    [
      dependencies,
      getInputValue,
      checkpointToRestore,
      clearInput,
      addToHistory,
      onResetChat,
      onMessageSent,
      activeContexts,
      modeName,
      setIsProcessingMessage
    ]
  );

  /**
   * Continue the conversation without new user input
   */
  const continueMessage = useCallback(
    async (cellContext?: string): Promise<void> => {
      if (!dependencies) {
        console.error('Dependencies not set');
        return;
      }

      const { chatService, conversationService, messageComponent, uiHelper } =
        dependencies;

      if (checkpointToRestore) {
        await conversationService.finishCheckpointRestoration(
          checkpointToRestore
        );
      }

      useWaitingReplyStore.getState().hide();

      setIsProcessingMessage(true);
      usePlanStateStore.getState().setLoading(true);

      uiHelper.resetToGeneratingState('Generating...');

      if (!chatService.isInitialized()) {
        messageComponent.addSystemMessage(
          'API key is not set. Please configure it in the settings.'
        );
        setIsProcessingMessage(false);
        usePlanStateStore.getState().setLoading(false);
        uiHelper.hideLoadingIndicator();
        return;
      }

      const systemMessages: string[] = [];

      try {
        const currentNotebookId =
          useNotebookEventsStore.getState().currentNotebookId;
        if (currentNotebookId) {
          conversationService.setNotebookId(currentNotebookId);

          const cellChanges =
            await NotebookCellStateService.detectChanges(currentNotebookId);
          const changesSummary =
            NotebookCellStateService.generateChangeSummaryMessage(cellChanges);
          if (changesSummary) {
            systemMessages.push(changesSummary);
          }
        }

        const messages: Array<{ role: string; content: string }> = [];
        if (cellContext) {
          systemMessages.push(cellContext);
        }

        const mentionContexts = messageComponent.getMentionContexts();
        if (mentionContexts.size > 0) {
          systemMessages.push(buildContextMessage(mentionContexts));
        }

        systemMessages.push(buildWorkingDirectoryMessage());

        // Force-cancel any stuck conversation before continuing
        if (ConversationService.isInProgress()) {
          console.log(
            '[useSendMessage] continueMessage: Conversation in progress - force-cancelling'
          );
          chatService.cancelRequest();
          try {
            const diffManager = getNotebookDiffManager();
            diffManager._finishedProcessingDiffs.emit(
              DiffApprovalStatus.APPROVED
            );
          } catch {
            // DiffManager not initialized - nothing to unblock
          }
          const pendingDiffs = useDiffStore.getState().pendingDiffs;
          for (const diff of pendingDiffs.values()) {
            if (!diff.userDecision) {
              diff.userDecision = 'approved';
            }
          }
          ConversationService.forceReset();
        }

        getNotebookDiffManager().clearDiffs();

        await conversationService.processConversation(
          messages,
          systemMessages,
          modeName
        );

        if (currentNotebookId) {
          await NotebookCellStateService.cacheCurrentNotebookState(
            currentNotebookId
          );
        }
      } catch (error) {
        console.error('Error in conversation processing:', error);

        if (chatService.getRequestStatus() !== ChatRequestStatus.CANCELLED) {
          const errorMessage =
            error instanceof Error ? error.message : String(error);
          const isAuthError =
            errorMessage.includes('authentication_error') ||
            errorMessage.includes('Invalid API key') ||
            (errorMessage.includes('401') && errorMessage.includes('error'));

          if (isAuthError) {
            messageComponent.displaySubscriptionCard();
          } else {
            messageComponent.addErrorMessage(`${errorMessage}`);
          }
        }
      } finally {
        setIsProcessingMessage(false);
        usePlanStateStore.getState().setLoading(false);

        const currentThread = chatHistoryManager?.getCurrentThread();
        if (currentThread && currentThread.needsContinue) {
          currentThread.needsContinue = false;
          console.log('[useSendMessage] Set needsContinue to false');
        }
      }
    },
    [
      dependencies,
      checkpointToRestore,
      modeName,
      chatHistoryManager,
      setIsProcessingMessage
    ]
  );

  return {
    sendMessage,
    continueMessage,
    isProcessingMessage,
    setIsProcessingMessage,
    checkpointToRestore,
    setCheckpointToRestore
  };
}
