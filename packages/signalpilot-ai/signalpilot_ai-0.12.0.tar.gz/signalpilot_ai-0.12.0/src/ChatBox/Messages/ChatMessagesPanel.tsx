/**
 * ChatMessagesPanel Component
 *
 * Main container for the chat messages UI. This is the primary React component
 * that replaces the imperative DOM-based ChatMessages class.
 *
 * Features:
 * - Renders all message types from the Zustand store
 * - Handles streaming messages
 * - Shows thinking indicator
 * - Shows waiting reply box
 * - Shows authentication/subscription cards
 * - Auto-scroll behavior
 * - Keyboard shortcuts (Cmd/Ctrl+Enter)
 *
 * @example
 * ```tsx
 * <ChatMessagesPanel
 *   notebookTools={notebookTools}
 *   historyManager={historyManager}
 *   onSendMessage={handleSend}
 *   onCheckpointRestore={handleRestore}
 *   onCheckpointRedo={handleRedo}
 * />
 * ```
 */

import React, {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef
} from 'react';
import {
  selectIsThinking,
  selectMessages,
  selectSpecialDisplay,
  selectStreaming,
  useChatMessagesStore
} from '@/stores/chatMessages';
import {
  useChatHistoryStore,
  selectIsLoadingHistory
} from '@/stores/chatHistoryStore';
import {
  useChatUIStore,
  selectShowLauncherWelcomeLoader
} from '@/stores/chatUIStore';
import {
  useWaitingReplyStore,
  selectIsVisible as selectWaitingReplyVisible,
  selectRecommendedPrompts
} from '@/stores/waitingReplyStore';
import { IChatMessage, ICheckpoint } from '@/types';
import { NotebookTools } from '@/Notebook/NotebookTools';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import {
  AuthenticationCard,
  SubscriptionCard,
  ThinkingIndicator,
  WaitingUserReplyBox
} from '@/ChatBox/Messages';
import { MessageList } from './MessageList';
import { useChatKeyboard } from './hooks/useChatKeyboard';
import { useChatCheckpoint } from './hooks/useChatCheckpoint';
import { useChatHistory } from './hooks/useChatHistory';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatMessagesPanelProps {
  /** Notebook tools for cell navigation */
  notebookTools: NotebookTools;
  /** Chat history manager for persistence */
  historyManager: ChatHistoryManager;
  /** Callback when user sends a message */
  onSendMessage?: (message: string) => void;
  /** Callback when checkpoint restore is requested */
  onCheckpointRestore?: (checkpoint: ICheckpoint) => Promise<void>;
  /** Callback when checkpoint redo is requested */
  onCheckpointRedo?: () => void;
  /** Callback when waiting reply prompt is clicked */
  onWaitingReplyPrompt?: (prompt: string) => void;
  /** Callback when continue button is clicked */
  onContinue?: () => void;
  /** Callback when authentication is triggered */
  onAuthenticate?: () => void;
  /** CSS class name */
  className?: string;
}

/**
 * Imperative API exposed via ref
 */
export interface ChatMessagesPanelHandle {
  /** Scroll to bottom of chat */
  scrollToBottom: () => void;
  /** Get LLM history for API calls */
  getLlmHistory: () => IChatMessage[];
  /** Add a user message */
  addUserMessage: (
    content: string,
    checkpoint?: ICheckpoint,
    options?: { hidden?: boolean }
  ) => string;
  /** Add an assistant message */
  addAssistantMessage: (content: string, showHeader?: boolean) => string;
  /** Create a checkpoint */
  createCheckpoint: (userMessage: IChatMessage) => ICheckpoint | null;
  /** Restore to a checkpoint */
  restoreCheckpoint: (checkpoint: ICheckpoint) => Promise<void>;
  /** Get the container element */
  getContainer: () => HTMLDivElement | null;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * ChatMessagesPanel - Main chat messages container
 */
export const ChatMessagesPanel = memo(
  forwardRef<ChatMessagesPanelHandle, ChatMessagesPanelProps>(
    (
      {
        notebookTools,
        historyManager,
        onSendMessage,
        onCheckpointRestore,
        onCheckpointRedo,
        onWaitingReplyPrompt,
        onContinue,
        onAuthenticate,
        className
      },
      ref
    ) => {
      // Store state
      const messages = useChatMessagesStore(selectMessages);
      const streaming = useChatMessagesStore(selectStreaming);
      const isThinking = useChatMessagesStore(selectIsThinking);
      const specialDisplay = useChatMessagesStore(selectSpecialDisplay);

      // Waiting reply state from dedicated store
      const waitingReplyVisible = useWaitingReplyStore(
        selectWaitingReplyVisible
      );
      const waitingReplyPrompts = useWaitingReplyStore(
        selectRecommendedPrompts
      );

      // Loading state from chat history store - shows loading immediately on notebook switch
      const isLoadingHistory = useChatHistoryStore(selectIsLoadingHistory);

      // Launcher welcome loader state - shows while preparing workspace context
      const showLauncherWelcomeLoader = useChatUIStore(
        selectShowLauncherWelcomeLoader
      );

      // Container ref for imperative API
      const containerRef = useRef<HTMLDivElement>(null);

      // Get scrollToBottom from store (scroll is now managed by parent ChatBoxContent)
      const scrollToBottom = useChatMessagesStore(
        state => state.scrollToBottom
      );

      // Keyboard shortcuts for continue
      useChatKeyboard({
        onContinue,
        enabled: waitingReplyVisible
      });

      const {
        createCheckpoint,
        restore: restoreCheckpoint,
        redo: redoCheckpoint
      } = useChatCheckpoint();

      const { addUserMessage, addAssistantMessage, getLlmHistory } =
        useChatHistory({
          historyManager
        });

      // Handle cell click (scroll to cell in notebook)
      const handleCellClick = useCallback(
        (cellId: string) => {
          void notebookTools.scrollToCellById(cellId);
        },
        [notebookTools]
      );

      // Handle checkpoint restore
      const handleCheckpointRestore = useCallback(
        async (checkpoint: ICheckpoint) => {
          if (onCheckpointRestore) {
            await onCheckpointRestore(checkpoint);
          } else {
            await restoreCheckpoint(checkpoint);
          }
        },
        [onCheckpointRestore, restoreCheckpoint]
      );

      // Handle checkpoint redo
      const handleCheckpointRedo = useCallback(() => {
        if (onCheckpointRedo) {
          onCheckpointRedo();
        } else {
          redoCheckpoint();
        }
      }, [onCheckpointRedo, redoCheckpoint]);

      // Handle waiting reply prompt click
      const handlePromptClick = useCallback(
        (prompt: string) => {
          onWaitingReplyPrompt?.(prompt);
        },
        [onWaitingReplyPrompt]
      );

      // Expose imperative API
      useImperativeHandle(
        ref,
        () => ({
          scrollToBottom,
          getLlmHistory,
          addUserMessage,
          addAssistantMessage,
          createCheckpoint,
          restoreCheckpoint,
          getContainer: () => containerRef.current
        }),
        [
          scrollToBottom,
          getLlmHistory,
          addUserMessage,
          addAssistantMessage,
          createCheckpoint,
          restoreCheckpoint
        ]
      );

      // Note: Auto-scroll is handled by useChatScroll hook which properly tracks
      // user vs programmatic scrolls. No need for duplicate effect here.

      // Build class name
      const containerClass = ['sage-ai-chat-messages-panel', className]
        .filter(Boolean)
        .join(' ');

      // Handle login callback
      const handleLogin = useCallback(() => {
        onAuthenticate?.();
      }, [onAuthenticate]);

      // Handle subscribe callback
      const handleSubscribe = useCallback(() => {
        // Default: could open subscription page
        console.log('[ChatMessagesPanel] Subscribe clicked');
      }, []);

      // Render special displays (authentication/subscription cards)
      if (specialDisplay === 'authentication') {
        return (
          <div ref={containerRef} className={containerClass}>
            <AuthenticationCard onLogin={handleLogin} />
          </div>
        );
      }

      if (specialDisplay === 'subscription') {
        return (
          <div ref={containerRef} className={containerClass}>
            <SubscriptionCard onSubscribe={handleSubscribe} />
          </div>
        );
      }

      // Show loading indicator during notebook switch (when loading history and no messages yet)
      if (isLoadingHistory && messages.length === 0) {
        return (
          <div ref={containerRef} className={containerClass}>
            <div className="sage-ai-chat-loading">
              <ThinkingIndicator />
            </div>
          </div>
        );
      }

      return (
        <div ref={containerRef} className={containerClass}>
          {/* Launcher welcome loader - shows while preparing workspace context */}
          {showLauncherWelcomeLoader && (
            <div className="sage-launcher-welcome-loader">
              <div className="loader-spinner" />
              <div className="loader-text">Preparing your workspace...</div>
            </div>
          )}

          {/* Message list */}
          <MessageList
            messages={messages}
            onCheckpointRestore={handleCheckpointRestore}
            onCheckpointRedo={handleCheckpointRedo}
            onCellClick={handleCellClick}
          />

          {/* Thinking indicator */}
          {isThinking && <ThinkingIndicator />}

          {/* NOTE: Streaming assistant messages are now rendered as part of MessageList.
              The message is added to the array in startStreaming() and updated in real-time.
              Streaming tool calls also use the isStreaming flag on IToolCallUIMessage. */}

          {/* Waiting reply box */}
          {waitingReplyVisible && (
            <WaitingUserReplyBox
              promptButtons={waitingReplyPrompts}
              onPromptClick={handlePromptClick}
              onContinueClick={onContinue}
            />
          )}
        </div>
      );
    }
  )
);

ChatMessagesPanel.displayName = 'ChatMessagesPanel';

export default ChatMessagesPanel;
