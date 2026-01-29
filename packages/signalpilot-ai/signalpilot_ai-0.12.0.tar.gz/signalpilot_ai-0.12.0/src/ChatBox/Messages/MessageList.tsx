/**
 * MessageList Component
 *
 * Renders a list of chat messages based on their type.
 * Maps UI message objects to the appropriate React components.
 *
 * @example
 * ```tsx
 * <MessageList
 *   messages={messages}
 *   onCheckpointRestore={handleRestore}
 *   onCheckpointRedo={handleRedo}
 *   onCellClick={handleCellClick}
 * />
 * ```
 */

import React, { memo, useMemo } from 'react';
import {
  ChatUIMessage,
  IAssistantUIMessage,
  IDiffApprovalUIMessage,
  IErrorUIMessage,
  ILoadingUIMessage,
  ISystemUIMessage,
  IToolCallUIMessage,
  IToolResultUIMessage,
  IUserUIMessage,
  useChatMessagesStore
} from '@/stores/chatMessages';
import { ICheckpoint } from '@/types';
import {
  AssistantMessage,
  ErrorMessage,
  LoadingIndicator,
  SystemMessage,
  ToolCallDisplay,
  UserMessage
} from '@/ChatBox/Messages';
import { DiffApprovalMessage } from '@/ChatBox/DiffApproval/DiffApprovalMessage';
import { ToolResultMessage } from './ToolResultMessage';
import { useWaitingReplyStore } from '@/stores/waitingReplyStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface MessageListProps {
  /** Array of UI messages to render */
  messages: ChatUIMessage[];
  /** Callback when checkpoint restore is clicked */
  onCheckpointRestore?: (checkpoint: ICheckpoint) => void;
  /** Callback when checkpoint redo is clicked */
  onCheckpointRedo?: () => void;
  /** Callback when a cell ID is clicked */
  onCellClick?: (cellId: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// MESSAGE RENDERERS
// ═══════════════════════════════════════════════════════════════

interface MessageRendererProps {
  message: ChatUIMessage;
  onCheckpointRestore?: (checkpoint: ICheckpoint) => void;
  onCheckpointRedo?: () => void;
  onCellClick?: (cellId: string) => void;
  isWaitingBoxVisible?: boolean;
  /** Whether this message should appear opaque (pending removal during checkpoint restore) */
  isOpaque?: boolean;
}

/**
 * Render a single message based on its type
 */
const MessageRenderer: React.FC<MessageRendererProps> = memo(
  ({
    message,
    onCheckpointRestore,
    onCheckpointRedo,
    onCellClick,
    isWaitingBoxVisible,
    isOpaque
  }) => {
    // Wrapper component to apply opaque styling
    const wrapWithOpaque = (
      content: React.ReactElement | null
    ): React.ReactElement | null => {
      if (!content) return null;
      if (isOpaque) {
        return <div className="chat-history-item-opaque">{content}</div>;
      }
      return content;
    };

    switch (message.type) {
      case 'user': {
        const userMsg = message as IUserUIMessage;
        return wrapWithOpaque(
          <UserMessage
            key={message.id}
            content={userMsg.content}
            checkpoint={userMsg.checkpoint}
            hidden={userMsg.hidden}
            onRestore={onCheckpointRestore}
            onRedo={onCheckpointRedo}
          />
        );
      }

      case 'assistant': {
        const assistantMsg = message as IAssistantUIMessage;
        return wrapWithOpaque(
          <AssistantMessage
            key={message.id}
            content={assistantMsg.content}
            showHeader={assistantMsg.showHeader}
          />
        );
      }

      case 'system': {
        const systemMsg = message as ISystemUIMessage;
        return wrapWithOpaque(
          <SystemMessage key={message.id} message={systemMsg.content} />
        );
      }

      case 'error': {
        const errorMsg = message as IErrorUIMessage;
        return wrapWithOpaque(
          <ErrorMessage key={message.id} message={errorMsg.content} />
        );
      }

      case 'tool_call': {
        const toolMsg = message as IToolCallUIMessage;
        // For wait_user_reply: during streaming it's handled by waiting reply box,
        // but for historical display we show a simple indicator
        if (toolMsg.toolName === 'notebook-wait_user_reply') {
          // During streaming, the waiting reply box handles this
          if (toolMsg.isStreaming) {
            return null;
          }
          // If the waiting reply box is currently visible (restored from history),
          // don't render the historical text - the box handles it
          if (isWaitingBoxVisible) {
            return null;
          }
          // Render a simple historical indicator with chat bubble icon
          // (only when conversation has moved past the wait_user_reply)
          return wrapWithOpaque(
            <div
              key={message.id}
              className="sage-ai-tool-call-v1"
              style={{ opacity: 0.7 }}
            >
              <div
                className="sage-ai-tool-call-icon"
                dangerouslySetInnerHTML={{
                  __html: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 11.5C21.0034 12.8199 20.6951 14.1219 20.1 15.3C19.3944 16.7118 18.3098 17.8992 16.9674 18.7293C15.6251 19.5594 14.0782 19.9994 12.5 20C11.1801 20.0035 9.87812 19.6951 8.7 19.1L3 21L4.9 15.3C4.30493 14.1219 3.99656 12.8199 4 11.5C4.00061 9.92179 4.44061 8.37488 5.27072 7.03258C6.10083 5.69028 7.28825 4.6056 8.7 3.90003C9.87812 3.30496 11.1801 2.99659 12.5 3.00003H13C15.0843 3.11502 17.053 3.99479 18.5291 5.47089C20.0052 6.94699 20.885 8.91568 21 11V11.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
                }}
              />
              <span>Waited for your reply</span>
            </div>
          );
        }
        return wrapWithOpaque(
          <ToolCallDisplay
            key={message.id}
            toolName={toolMsg.toolName}
            toolInput={toolMsg.toolInput}
            isStreaming={toolMsg.isStreaming}
            onCellClick={onCellClick}
            hasResult={toolMsg.hasResult}
            result={toolMsg.result}
            toolCallData={toolMsg.toolCallData}
            hasError={toolMsg.hasError}
            toolSearchResult={toolMsg.toolSearchResult}
          />
        );
      }

      case 'tool_result': {
        // Legacy: tool_result messages are now merged into tool_call messages
        // This case handles any remaining tool_result messages for backwards compatibility
        const resultMsg = message as IToolResultUIMessage;
        return wrapWithOpaque(
          <ToolResultMessage
            key={message.id}
            toolName={resultMsg.toolName}
            result={resultMsg.result}
            toolCallData={resultMsg.toolCallData}
            hasError={resultMsg.hasError}
            onCellClick={onCellClick}
          />
        );
      }

      case 'diff_approval': {
        const diffMsg = message as IDiffApprovalUIMessage;
        return wrapWithOpaque(
          <DiffApprovalMessage
            key={message.id}
            messageId={message.id}
            notebookPath={diffMsg.notebookPath}
            diffCells={diffMsg.diffCells}
            isHistorical={diffMsg.isHistorical}
            onCellClick={onCellClick}
          />
        );
      }

      case 'loading': {
        const loadingMsg = message as ILoadingUIMessage;
        return wrapWithOpaque(
          <LoadingIndicator key={message.id} text={loadingMsg.text} />
        );
      }

      default:
        return null;
    }
  }
);

MessageRenderer.displayName = 'MessageRenderer';

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * MessageList - Renders all chat messages
 */
export const MessageList: React.FC<MessageListProps> = memo(
  ({ messages, onCheckpointRestore, onCheckpointRedo, onCellClick }) => {
    // Use hook to properly subscribe to waiting box visibility changes
    // This ensures React knows about the dependency and re-renders appropriately
    const isWaitingBoxVisible = useWaitingReplyStore(state => state.isVisible);

    // Get the checkpoint ID being restored (if any)
    const restoringCheckpointId = useChatMessagesStore(
      state => state.restoringCheckpointId
    );

    // Compute which messages should appear opaque (after the restoring checkpoint, not including it)
    const opaqueMessageIds = useMemo(() => {
      if (!restoringCheckpointId) {
        return new Set<string>();
      }

      // Find the index of the message with this checkpoint ID
      const checkpointIndex = messages.findIndex(
        msg =>
          msg.type === 'user' &&
          (msg as IUserUIMessage).checkpoint?.id === restoringCheckpointId
      );

      if (checkpointIndex === -1) {
        return new Set<string>();
      }

      // All messages AFTER the checkpoint message should be opaque (not including the checkpoint itself)
      const opaque = new Set<string>();
      for (let i = checkpointIndex + 1; i < messages.length; i++) {
        opaque.add(messages[i].id);
      }
      return opaque;
    }, [messages, restoringCheckpointId]);

    return (
      <>
        {messages.map(message => (
          <MessageRenderer
            key={message.id}
            message={message}
            onCheckpointRestore={onCheckpointRestore}
            onCheckpointRedo={onCheckpointRedo}
            onCellClick={onCellClick}
            isWaitingBoxVisible={isWaitingBoxVisible}
            isOpaque={opaqueMessageIds.has(message.id)}
          />
        ))}
      </>
    );
  }
);

MessageList.displayName = 'MessageList';

export default MessageList;
