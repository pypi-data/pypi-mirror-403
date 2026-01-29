/**
 * HistoryContainer Component (Pure React)
 *
 * Container for chat history/thread list display.
 * Integrates with chatHistoryStore to provide thread data.
 *
 * Note: Threads are loaded via chatboxStore.reinitializeForNotebook() when
 * notebooks switch, so we don't need to call loadThreads here.
 */

import React, { useCallback } from 'react';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useChatboxStore } from '@/stores/chatboxStore';
import { ThreadBanner, ThreadItem } from './Toolbar/ThreadBanner';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface HistoryContainerProps {
  /** Portal container for ThreadBanner */
  portalContainer?: HTMLElement | null;
  /** Callback when thread is selected */
  onThreadSelected?: (threadId: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const HistoryContainer: React.FC<HistoryContainerProps> = ({
  portalContainer,
  onThreadSelected
}) => {
  // Store state
  // Note: loadThreads is handled by chatboxStore.reinitializeForNotebook()
  // when notebooks switch, so we only subscribe to threads here
  const { threads, currentThreadId, isLoadingHistory, selectThread } =
    useChatHistoryStore();

  const { showHistoryWidget } = useChatUIStore();
  const { currentNotebookId } = useChatboxStore();

  // Handle thread selection
  const handleSelectThread = useCallback(
    (threadId: string) => {
      void selectThread(threadId);
      onThreadSelected?.(threadId);
    },
    [selectThread, onThreadSelected]
  );

  // Convert threads to ThreadItem format
  const threadItems: ThreadItem[] = threads.map(thread => ({
    id: thread.id,
    name: thread.name || 'New Chat',
    lastUpdated: thread.lastUpdated || Date.now()
  }));

  // Debug: Log thread counts
  console.log(
    `[HistoryContainer] Store has ${threads.length} threads, passing ${threadItems.length} to ThreadBanner`
  );

  // Don't render if history widget is not shown
  if (!showHistoryWidget) {
    return null;
  }

  return (
    <ThreadBanner
      threads={threadItems}
      currentThreadId={currentThreadId}
      onSelectThread={handleSelectThread}
      hasNotebook={!!currentNotebookId}
      portalContainer={portalContainer}
      isLoading={isLoadingHistory}
    />
  );
};

export default HistoryContainer;
