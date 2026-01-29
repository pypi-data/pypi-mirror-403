/**
 * ChatBoxHeader Component
 *
 * Header section of the ChatBox containing toolbar and thread banner.
 * Pure React implementation integrating existing components.
 */

import React, { useCallback, useRef } from 'react';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useChatUIStore } from '@/stores/chatUIStore';
import { ChatToolbar } from './Toolbar/ChatToolbar';
import { MoreOptionsPopover } from './Toolbar/MoreOptionsPopover';
import { ThreadBanner, ThreadItem } from './Toolbar/ThreadBanner';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatBoxHeaderProps {
  /** Container element for thread banner portal */
  portalContainer?: HTMLElement | null;
  /** Callback when new chat is requested */
  onNewChat?: () => void;
  /** Callback when rename is requested */
  onRename?: () => void;
  /** Callback when delete is requested */
  onDelete?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const ChatBoxHeader: React.FC<ChatBoxHeaderProps> = ({
  portalContainer,
  onNewChat,
  onRename,
  onDelete
}) => {
  const headerRef = useRef<HTMLDivElement>(null);

  const {
    threads,
    currentThreadId,
    currentThreadName,
    selectThread,
    isLoadingHistory
  } = useChatHistoryStore();

  const { currentNotebookId } = useChatboxStore();

  // Handle callbacks
  const handleNewChat = useCallback(() => {
    useChatboxStore.getState().createNewChat();
    onNewChat?.();
  }, [onNewChat]);

  const handleRename = useCallback(() => {
    const { services } = useChatboxStore.getState();
    const chatHistoryManager = services.chatHistoryManager;

    if (!chatHistoryManager) {
      console.warn('[ChatBoxHeader] No chatHistoryManager available');
      return;
    }

    const currentThread = chatHistoryManager.getCurrentThread();
    if (!currentThread) {
      useChatMessagesStore
        .getState()
        .addSystemMessage('No active chat to rename.');
      return;
    }

    const newName = prompt('Enter new chat name:', currentThread.name);
    if (newName && newName.trim() !== '' && newName !== currentThread.name) {
      const success = chatHistoryManager.renameCurrentThread(newName.trim());
      if (success) {
        // Sync Zustand from ChatHistoryManager (single source of truth)
        void useChatHistoryStore.getState().syncFromManager();
        useChatMessagesStore
          .getState()
          .addSystemMessage(`Chat renamed to: ${newName.trim()}`);
      } else {
        useChatMessagesStore
          .getState()
          .addSystemMessage('Failed to rename chat.');
      }
    }
    onRename?.();
  }, [onRename]);

  const handleDelete = useCallback(async () => {
    const { services } = useChatboxStore.getState();
    const chatHistoryManager = services.chatHistoryManager;

    if (!chatHistoryManager) {
      console.warn('[ChatBoxHeader] No chatHistoryManager available');
      return;
    }

    const currentThread = chatHistoryManager.getCurrentThread();
    if (!currentThread) {
      useChatMessagesStore
        .getState()
        .addSystemMessage('No active chat to delete.');
      return;
    }

    const confirmDelete = confirm(
      `Are you sure you want to delete the chat "${currentThread.name}"? This action cannot be undone.`
    );
    if (confirmDelete) {
      const deletedThreadName = currentThread.name;
      const success = chatHistoryManager.deleteThread(currentThread.id);
      if (success) {
        // Sync Zustand from ChatHistoryManager (single source of truth)
        await useChatHistoryStore.getState().syncFromManager();

        useChatMessagesStore
          .getState()
          .addSystemMessage(`Chat "${deletedThreadName}" has been deleted.`);

        const newCurrentThread = chatHistoryManager.getCurrentThread();
        if (newCurrentThread) {
          // Select the new current thread
          await useChatHistoryStore
            .getState()
            .selectThread(newCurrentThread.id);
          if (newCurrentThread.messages.length === 0) {
            useChatUIStore.getState().setShowNewChatDisplay(true);
          }
        } else {
          // No threads left, show new chat display
          useChatUIStore.getState().setShowNewChatDisplay(true);
          useChatMessagesStore.getState().clearMessages();
        }
      } else {
        useChatMessagesStore
          .getState()
          .addSystemMessage('Failed to delete chat.');
      }
    }
    onDelete?.();
  }, [onDelete]);

  const handleSelectThread = useCallback(
    (threadId: string) => {
      void selectThread(threadId);
    },
    [selectThread]
  );

  // Convert threads to ThreadItem format
  const threadItems: ThreadItem[] = threads.map(thread => ({
    id: thread.id,
    name: thread.name || 'New Chat',
    lastUpdated: thread.lastUpdated || Date.now()
  }));

  return (
    <div ref={headerRef} className="sage-ai-chatbox-header">
      {/* Chat Toolbar */}
      <ChatToolbar
        threadName={currentThreadName || 'New Chat'}
        onNewChat={handleNewChat}
      />

      {/* More Options Popover */}
      <MoreOptionsPopover
        onRenameChat={handleRename}
        onDeleteChat={handleDelete}
        containerRef={headerRef}
      />

      {/* Thread Banner (slide-out panel) */}
      <ThreadBanner
        threads={threadItems}
        currentThreadId={currentThreadId}
        onSelectThread={handleSelectThread}
        hasNotebook={!!currentNotebookId}
        portalContainer={portalContainer}
        isLoading={isLoadingHistory}
      />
    </div>
  );
};

export default ChatBoxHeader;
