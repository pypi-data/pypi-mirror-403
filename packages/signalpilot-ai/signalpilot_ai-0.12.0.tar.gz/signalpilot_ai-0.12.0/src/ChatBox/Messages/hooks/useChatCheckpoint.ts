/**
 * useChatCheckpoint Hook
 *
 * Manages checkpoint operations for the chat, allowing users to:
 * - Create checkpoints when sending messages
 * - Restore to previous checkpoints (undo AI changes)
 * - Redo checkpointed changes
 *
 * @example
 * ```tsx
 * const { createCheckpoint, restore, redo, isRestoring } = useChatCheckpoint();
 *
 * // When user sends message
 * const checkpoint = createCheckpoint(userMessage);
 *
 * // User clicks restore
 * await restore(checkpoint);
 *
 * // User clicks redo
 * redo();
 * ```
 */

import { useCallback, useState } from 'react';
import { IChatMessage, ICheckpoint } from '@/types';
import { CheckpointManager } from '@/Services/CheckpointManager';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { isLauncherNotebookId } from '@/stores/chatModeStore';
import { useDiffStore } from '@/stores/diffStore';
import { useLLMStateStore } from '@/stores/llmStateStore';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatInputStore } from '@/stores/chatInput/chatInputStore';
import {
  selectLlmHistory,
  selectMentionContexts,
  useChatMessagesStore
} from '@/stores/chatMessages';

export interface UseChatCheckpointOptions {
  /** Thread ID for checkpoint storage */
  threadId?: string;
}

export interface UseChatCheckpointResult {
  /** Create a checkpoint for a user message */
  createCheckpoint: (userMessage: IChatMessage) => ICheckpoint | null;
  /** Restore to a checkpoint */
  restore: (checkpoint: ICheckpoint) => Promise<void>;
  /** Redo after restoring */
  redo: () => void;
  /** Whether currently restoring */
  isRestoring: boolean;
  /** Current checkpoint being restored */
  restoringCheckpoint: ICheckpoint | null;
  /** Find checkpoint by user message ID */
  findByMessageId: (messageId: string) => ICheckpoint | undefined;
  /** Find checkpoint by message content */
  findByContent: (content: string) => ICheckpoint | undefined;
}

export function useChatCheckpoint(
  options: UseChatCheckpointOptions = {}
): UseChatCheckpointResult {
  const { threadId } = options;

  const [isRestoring, setIsRestoring] = useState(false);
  const [restoringCheckpoint, setRestoringCheckpoint] =
    useState<ICheckpoint | null>(null);

  // Store state
  const llmHistory = useChatMessagesStore(selectLlmHistory);
  const mentionContexts = useChatMessagesStore(selectMentionContexts);

  // Get checkpoint manager singleton
  const checkpointManager = CheckpointManager.getInstance();

  /**
   * Create a checkpoint for a user message
   */
  const createCheckpoint = useCallback(
    (userMessage: IChatMessage): ICheckpoint | null => {
      try {
        const currentNotebookId =
          useNotebookEventsStore.getState().currentNotebookId;
        if (!currentNotebookId || isLauncherNotebookId(currentNotebookId)) {
          console.warn('[useChatCheckpoint] No notebook ID available or on launcher');
          return null;
        }

        const currentThreadId =
          threadId || useChatMessagesStore.getState().currentThreadId;
        if (!currentThreadId) {
          console.warn('[useChatCheckpoint] No thread ID available');
          return null;
        }

        checkpointManager.setCurrentNotebookId(currentNotebookId);

        const userMessageContent =
          typeof userMessage.content === 'string'
            ? userMessage.content
            : JSON.stringify(userMessage.content);

        const checkpoint = checkpointManager.createCheckpoint(
          userMessageContent,
          llmHistory,
          mentionContexts,
          currentThreadId,
          userMessage.id
        );

        return checkpoint;
      } catch (error) {
        console.error('[useChatCheckpoint] Error creating checkpoint:', error);
        return null;
      }
    },
    [threadId, llmHistory, mentionContexts, checkpointManager]
  );

  /**
   * Restore to a checkpoint
   */
  const restore = useCallback(
    async (checkpoint: ICheckpoint): Promise<void> => {
      try {
        setIsRestoring(true);
        setRestoringCheckpoint(checkpoint);

        // Set input value for editing
        useChatInputStore.getState().setInputValue(checkpoint.userMessage);

        // Store checkpoint in the messages store so useSendMessage can access it
        useChatMessagesStore.getState().setCheckpointToRestore(checkpoint);

        // Cancel any in-progress message
        useChatboxStore.getState().cancelMessage();

        // Clear pending diffs
        getNotebookDiffManager().rejectAndRevertDiffsImmediately();
        useDiffStore
          .getState()
          .clearDiffs(useNotebookEventsStore.getState().currentNotebookId);

        // Use ConversationService for the actual restoration
        const conversationService =
          useChatboxStore.getState().services.conversationService;
        if (conversationService) {
          await conversationService.startCheckpointRestoration(checkpoint);
        }
      } catch (error) {
        console.error('[useChatCheckpoint] Error restoring checkpoint:', error);
        setIsRestoring(false);
        setRestoringCheckpoint(null);
        useChatMessagesStore.getState().setCheckpointToRestore(null);
        useChatMessagesStore.getState().setRestoringCheckpointId(null);
      }
    },
    []
  );

  /**
   * Redo after restoring (cancel restoration)
   */
  const redo = useCallback(() => {
    // Read checkpoint from store (more reliable than local state)
    const checkpointFromStore =
      useChatMessagesStore.getState().checkpointToRestore;
    const checkpoint = restoringCheckpoint || checkpointFromStore;

    if (!checkpoint) {
      console.warn(
        '[useChatCheckpoint] redo called but no checkpoint to restore'
      );
      return;
    }

    console.log(
      '[useChatCheckpoint] redo called for checkpoint:',
      checkpoint.id
    );

    // Clear input
    useChatInputStore.getState().setInputValue('');

    // Redo all actions from the checkpoint (restores pre-restoration notebook state)
    const conversationService =
      useChatboxStore.getState().services.conversationService;
    if (conversationService) {
      void conversationService.redoActions(checkpoint);
    }

    useLLMStateStore.getState().hide();

    // Clear restoration state in the store
    useChatMessagesStore.getState().setCheckpointToRestore(null);
    useChatMessagesStore.getState().setRestoringCheckpointId(null);

    setIsRestoring(false);
    setRestoringCheckpoint(null);
  }, [restoringCheckpoint]);

  /**
   * Find checkpoint by user message ID
   */
  const findByMessageId = useCallback(
    (messageId: string): ICheckpoint | undefined => {
      return (
        checkpointManager.findCheckpointByUserMessageId(messageId) ?? undefined
      );
    },
    [checkpointManager]
  );

  /**
   * Find checkpoint by message content
   */
  const findByContent = useCallback(
    (content: string): ICheckpoint | undefined => {
      return (
        checkpointManager.findCheckpointByUserMessage(content) ?? undefined
      );
    },
    [checkpointManager]
  );

  return {
    createCheckpoint,
    restore,
    redo,
    isRestoring,
    restoringCheckpoint,
    findByMessageId,
    findByContent
  };
}

export default useChatCheckpoint;
