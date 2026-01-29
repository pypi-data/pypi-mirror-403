/**
 * ChatBoxContent Component
 *
 * Main content area of the ChatBox containing:
 * - State displays (LLM state, Plan state)
 * - New chat display
 * - Chat messages panel
 *
 * Pure React implementation integrating existing components.
 */

import React, { useCallback } from 'react';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { NewChatDisplay } from './NewChatDisplay';
import { ChatMessagesPanel } from './Messages/ChatMessagesPanel';
import { getNotebookTools } from '@/stores/servicesStore';
import { useChatScroll } from './Messages/hooks/useChatScroll';
import { ChatHistoryLoadingOverlay } from '@/Components/common/Skeletons';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatBoxContentProps {
  /** Callback when a recommended prompt is selected */
  onPromptSelected?: (prompt: string) => void;
  /** Callback when continue is clicked */
  onContinue?: () => void;
  /** Callback when authentication is triggered */
  onAuthenticate?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const ChatBoxContent: React.FC<ChatBoxContentProps> = ({
  onPromptSelected,
  onContinue,
  onAuthenticate
}) => {
  // Use the scroll hook - this manages auto-scroll and tracks user vs programmatic scrolls
  const { scrollRef, scrollToBottom, showScrollButton } = useChatScroll();

  const { showNewChatDisplay, setShowNewChatDisplay, showLauncherWelcomeLoader } = useChatUIStore();
  const { messages } = useChatMessagesStore();
  const { isProcessingMessage, services } = useChatboxStore();
  const { isLoadingHistory, isLoadingThreads } = useChatHistoryStore();

  // Get required services for ChatMessagesPanel
  const notebookTools = getNotebookTools();
  const { chatHistoryManager } = services;

  // Show loading while threads/history are being loaded
  const isLoadingChatState = isLoadingHistory || isLoadingThreads;

  // ─────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────

  const handlePromptSelected = useCallback(
    (prompt: string) => {
      setShowNewChatDisplay(false);
      onPromptSelected?.(prompt);
    },
    [setShowNewChatDisplay, onPromptSelected]
  );

  const handleScrollToBottom = useCallback(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  // Show new chat display only when:
  // 1. Not loading history/threads AND
  // 2. Not processing a message (LLM is working) AND
  // 3. Not showing the launcher welcome loader AND
  // 4. showNewChatDisplay is true OR no messages
  const shouldShowNewChat =
    !isLoadingChatState &&
    !isProcessingMessage &&
    !showLauncherWelcomeLoader &&
    (showNewChatDisplay || messages.length === 0);

  // Show messages panel when:
  // 1. Not loading AND
  // 2. (Not showing new chat OR LLM is processing OR showing launcher welcome loader)
  const shouldShowMessages =
    !isLoadingChatState && (!shouldShowNewChat || isProcessingMessage || showLauncherWelcomeLoader);

  return (
    <div ref={scrollRef} className="sage-ai-chatbox-content">
      {/* Loading State - shown while loading history/threads */}
      <ChatHistoryLoadingOverlay
        visible={isLoadingChatState}
        message="Loading chat history"
      />

      {/* New Chat Display */}
      {shouldShowNewChat && (
        <NewChatDisplay onPromptSelected={handlePromptSelected} />
      )}

      {/* Chat Messages Area */}
      {shouldShowMessages && notebookTools && chatHistoryManager && (
        <ChatMessagesPanel
          notebookTools={notebookTools}
          historyManager={chatHistoryManager}
          onContinue={onContinue}
          onAuthenticate={onAuthenticate}
          className="sage-ai-messages-container"
        />
      )}

      {/* Scroll to Bottom Button */}
      {showScrollButton && (
        <button
          className="sage-ai-scroll-to-bottom"
          onClick={handleScrollToBottom}
          aria-label="Scroll to bottom"
        >
          <svg
            width="12"
            height="12"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M4 6L8 10L12 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

export default ChatBoxContent;
