/**
 * ChatBox Component (Pure React)
 *
 * Main chat interface component that replaces the hybrid Lumino/React ChatBoxWidget.
 * This is a pure React implementation using Zustand for state management.
 *
 * Features:
 * - Pure React rendering (no direct DOM manipulation)
 * - Zustand store integration for all state
 * - Declarative component structure
 * - Proper React lifecycle management
 *
 * Usage:
 * ```tsx
 * // In a Lumino widget wrapper
 * <JupyterLabProvider tracker={tracker} app={app}>
 *   <ChatBox initialNotebookId="notebook-123" />
 * </JupyterLabProvider>
 * ```
 *
 * State is managed through Zustand stores:
 * - useChatboxStore: Orchestration state
 * - useChatUIStore: UI visibility states
 * - useChatMessagesStore: Message display
 * - useChatInputStore: Input state
 */

import React, { useCallback, useRef, useState, useEffect } from 'react';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useChatInputStore } from '@/stores/chatInput/chatInputStore';
import { ChatBoxHeader } from './ChatBoxHeader';
import { ChatBoxContent } from './ChatBoxContent';
import { ChatBoxInput } from './ChatBoxInput';
import { LoadingOverlay } from './LoadingOverlay';
import { UpdateBanner } from './UpdateBanner';
import { StateDisplayContainer } from './StateDisplayContainer';
import { useChatBoxInit, useNotebookSync } from './hooks';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatBoxProps {
  /** Initial notebook ID to load chat for */
  initialNotebookId?: string;
  /** Optional class name for styling */
  className?: string;
  /** Callback when message is sent */
  onMessageSent?: () => void;
  /** Callback when initialization completes */
  onReady?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const ChatBox: React.FC<ChatBoxProps> = ({
  initialNotebookId,
  className = '',
  onMessageSent,
  onReady
}) => {
  // Debug logging

  const containerRef = useRef<HTMLDivElement>(null);

  // Track portal container availability to prevent inline->portal switch
  // that causes React removeChild errors
  const [portalContainer, setPortalContainer] = useState<HTMLElement | null>(
    null
  );

  useEffect(() => {
    // Set portal container after mount to ensure stable portal target
    if (containerRef.current && !portalContainer) {
      setPortalContainer(containerRef.current);
    }
  }, [portalContainer]);

  // ─────────────────────────────────────────────────────────────
  // Store State
  // ─────────────────────────────────────────────────────────────

  const { loadingOverlay } = useChatUIStore();
  const { setInputValue } = useChatInputStore();

  // ─────────────────────────────────────────────────────────────
  // Custom Hooks
  // ─────────────────────────────────────────────────────────────

  const { isReady, isInitializing } = useChatBoxInit({
    initialNotebookId,
    onReady
  });

  const { hasNotebook } = useNotebookSync();

  // ─────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────

  const handlePromptSelected = useCallback(
    (prompt: string) => {
      setInputValue(prompt);
    },
    [setInputValue]
  );

  const handleMessageSent = useCallback(() => {
    onMessageSent?.();
  }, [onMessageSent]);

  // ─────────────────────────────────────────────────────────────
  // Loading State
  // ─────────────────────────────────────────────────────────────

  if (!isReady && isInitializing) {
    return (
      <div
        ref={containerRef}
        className={`sage-ai-chatbox sage-ai-chatbox-loading ${className}`}
      >
        <div className="sage-ai-chatbox-initializing">
          <div className="sage-ai-blob-loader" />
          <span>Initializing chat...</span>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  return (
    <div ref={containerRef} className={`sage-ai-chatbox ${className}`}>
      {/* Update Banner */}
      <UpdateBanner />

      {/* Header with Toolbar and Thread Banner */}
      <ChatBoxHeader portalContainer={portalContainer} />

      {/* Main Content Area */}
      <ChatBoxContent onPromptSelected={handlePromptSelected} />

      {/* State Displays (LLM + Plan) - positioned above input */}
      <StateDisplayContainer />

      {/* Input Section */}
      <ChatBoxInput onMessageSent={handleMessageSent} />

      {/* Loading Overlay */}
      {loadingOverlay.isVisible && (
        <LoadingOverlay text={loadingOverlay.text} />
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════

export default ChatBox;

// Re-export sub-components for flexibility
export { ChatBoxHeader } from './ChatBoxHeader';
export { ChatBoxContent } from './ChatBoxContent';
export { ChatBoxInput } from './ChatBoxInput';
export { LoadingOverlay } from './LoadingOverlay';
export { UpdateBanner } from './UpdateBanner';
export { NewChatDisplay } from './NewChatDisplay';
export { StateDisplayContainer } from './StateDisplayContainer';
export { HistoryContainer } from './HistoryContainer';

// Re-export hooks
export * from './hooks';
