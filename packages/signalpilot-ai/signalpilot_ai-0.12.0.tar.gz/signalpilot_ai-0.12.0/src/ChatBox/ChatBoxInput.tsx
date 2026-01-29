/**
 * ChatBoxInput Component
 *
 * Input section of the ChatBox.
 * Uses the existing ChatInputContainer component.
 */

import React, { useCallback, useMemo, useRef } from 'react';
import { useChatboxStore } from '@/stores/chatboxStore';
import {
  ChatInputContainer,
  ChatInputContainerRef,
  ChatInputDependencies
} from './Input';
import { getToolService, useServicesStore } from '@/stores/servicesStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatBoxInputProps {
  /** Callback when message is sent */
  onMessageSent?: () => void;
  /** Callback when cancel is clicked */
  onCancel?: () => void;
  /** Callback when context is selected */
  onContextSelected?: (context: any) => void;
  /** Callback when context is removed */
  onContextRemoved?: (contextId: string) => void;
  /** Callback when reset chat is requested */
  onResetChat?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const ChatBoxInput: React.FC<ChatBoxInputProps> = ({
  onMessageSent,
  onCancel,
  onContextSelected,
  onContextRemoved,
  onResetChat
}) => {
  const inputContainerRef = useRef<ChatInputContainerRef>(null);

  const { createNewChat, services } = useChatboxStore();

  // Get services from servicesStore
  const toolService = getToolService();
  const contentManager = useServicesStore.getState().contentManager;
  const chatService = useServicesStore.getState().chatService;

  // Get services from chatboxStore (created by useChatBoxInit)
  const {
    chatHistoryManager,
    conversationService,
    messageComponent,
    uiHelper
  } = services;

  // Build dependencies for ChatInputContainer
  const initialDependencies = useMemo<ChatInputDependencies | undefined>(() => {
    if (
      !chatService ||
      !conversationService ||
      !messageComponent ||
      !uiHelper
    ) {
      return undefined;
    }
    return {
      chatService,
      conversationService,
      messageComponent,
      uiHelper
    };
  }, [chatService, conversationService, messageComponent, uiHelper]);

  // ─────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────

  const handleMessageSent = useCallback(() => {
    onMessageSent?.();
  }, [onMessageSent]);

  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  const handleResetChat = useCallback(() => {
    createNewChat();
    onResetChat?.();
  }, [createNewChat, onResetChat]);

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  // Show loading state if services not ready
  if (!toolService || !contentManager) {
    return (
      <div className="sage-ai-input-section">
        <div className="sage-ai-chat-input-loading">
          Initializing services...
        </div>
      </div>
    );
  }

  return (
    <div className="sage-ai-input-section">
      {/* Chat Input Container - uses existing component */}
      <ChatInputContainer
        ref={inputContainerRef}
        chatHistoryManager={chatHistoryManager}
        toolService={toolService}
        contentManager={contentManager}
        initialDependencies={initialDependencies}
        onMessageSent={handleMessageSent}
        onCancel={handleCancel}
        onContextSelected={onContextSelected}
        onContextRemoved={onContextRemoved}
        onResetChat={handleResetChat}
      />
    </div>
  );
};

export default ChatBoxInput;
