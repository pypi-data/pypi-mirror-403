/**
 * Skeleton Components
 *
 * Loading placeholder components that mimic the structure of actual content.
 * Used during initialization to provide immediate visual feedback while
 * data is being loaded in the background.
 *
 * Design Principles:
 * - Match the visual structure of the actual content
 * - Use subtle shimmer animations
 * - Support both light and dark themes
 * - Accessible with proper ARIA attributes
 */

import * as React from 'react';
import { ModernSpinner } from './ModernSpinner';

// ═══════════════════════════════════════════════════════════════
// BASE SKELETON COMPONENT
// ═══════════════════════════════════════════════════════════════

interface ISkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<ISkeletonProps> = ({
  width = '100%',
  height = '16px',
  borderRadius = '4px',
  className = '',
  style
}) => {
  return (
    <div
      className={`sage-skeleton ${className}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        borderRadius:
          typeof borderRadius === 'number' ? `${borderRadius}px` : borderRadius,
        ...style
      }}
      aria-hidden="true"
    />
  );
};

// ═══════════════════════════════════════════════════════════════
// MESSAGE SKELETON
// ═══════════════════════════════════════════════════════════════

interface IMessageSkeletonProps {
  type: 'user' | 'assistant';
  lines?: number;
}

export const MessageSkeleton: React.FC<IMessageSkeletonProps> = ({
  type,
  lines = 2
}) => {
  const isUser = type === 'user';

  return (
    <div
      className={`sage-message-skeleton sage-message-skeleton--${type}`}
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '12px',
        padding: '8px 0'
      }}
    >
      {/* Avatar placeholder (only for assistant) */}
      {!isUser && (
        <Skeleton
          width={32}
          height={32}
          borderRadius="50%"
          className="sage-message-skeleton__avatar"
        />
      )}

      {/* Message content */}
      <div
        className="sage-message-skeleton__content"
        style={{
          flex: 1,
          maxWidth: isUser ? '70%' : '85%',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px'
        }}
      >
        <div
          className={`sage-message-skeleton__bubble sage-message-skeleton__bubble--${type}`}
          style={{
            padding: '12px 16px',
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}
        >
          {Array.from({ length: lines }).map((_, i) => (
            <Skeleton
              key={i}
              height={14}
              width={i === lines - 1 ? '60%' : '100%'}
              borderRadius={3}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// MESSAGE LIST SKELETON
// ═══════════════════════════════════════════════════════════════

interface IMessageListSkeletonProps {
  messageCount?: number;
}

export const MessageListSkeleton: React.FC<IMessageListSkeletonProps> = ({
  messageCount = 3
}) => {
  // Generate a realistic-looking conversation pattern
  const messages = React.useMemo(() => {
    const result: Array<{ type: 'user' | 'assistant'; lines: number }> = [];
    for (let i = 0; i < messageCount; i++) {
      // Alternate between user and assistant
      const type = i % 2 === 0 ? 'user' : 'assistant';
      // User messages are typically shorter
      const lines = type === 'user' ? 1 : Math.floor(Math.random() * 2) + 2;
      result.push({ type, lines });
    }
    return result;
  }, [messageCount]);

  return (
    <div
      className="sage-message-list-skeleton"
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: '16px',
        gap: '16px'
      }}
      role="status"
      aria-label="Loading messages"
    >
      {messages.map((msg, index) => (
        <MessageSkeleton key={index} type={msg.type} lines={msg.lines} />
      ))}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// CHATBOX SKELETON
// ═══════════════════════════════════════════════════════════════

interface IChatBoxSkeletonProps {
  showHeader?: boolean;
  showInput?: boolean;
  message?: string;
}

export const ChatBoxSkeleton: React.FC<IChatBoxSkeletonProps> = ({
  showHeader = true,
  showInput = true,
  message = 'Loading chat'
}) => {
  return (
    <div
      className="sage-chatbox-skeleton"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: 'var(--jp-layout-color1, #fff)'
      }}
      role="status"
      aria-label={message}
    >
      {/* Header skeleton */}
      {showHeader && (
        <div
          className="sage-chatbox-skeleton__header"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 16px',
            borderBottom: '1px solid var(--jp-border-color1, #e0e0e0)'
          }}
        >
          <Skeleton width={120} height={20} borderRadius={4} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <Skeleton width={32} height={32} borderRadius={6} />
            <Skeleton width={32} height={32} borderRadius={6} />
          </div>
        </div>
      )}

      {/* Content area with centered spinner */}
      <div
        className="sage-chatbox-skeleton__content"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '32px',
          gap: '16px'
        }}
      >
        <ModernSpinner
          size="lg"
          variant="primary"
          text={message}
          showDots
          showPulseRing
        />
      </div>

      {/* Input skeleton */}
      {showInput && (
        <div
          className="sage-chatbox-skeleton__input"
          style={{
            padding: '12px 16px',
            borderTop: '1px solid var(--jp-border-color1, #e0e0e0)'
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: '8px'
            }}
          >
            <Skeleton height={40} borderRadius={20} style={{ flex: 1 }} />
            <Skeleton width={40} height={40} borderRadius={20} />
          </div>
        </div>
      )}
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// CHAT HISTORY LOADING OVERLAY
// ═══════════════════════════════════════════════════════════════

interface IChatHistoryLoadingOverlayProps {
  visible?: boolean;
  message?: string;
}

export const ChatHistoryLoadingOverlay: React.FC<
  IChatHistoryLoadingOverlayProps
> = ({ visible = true, message = 'Loading chat history' }) => {
  if (!visible) return null;

  return (
    <div
      className="sage-ai-chat-history-loading-overlay"
      role="status"
      aria-label={message}
    >
      <ModernSpinner
        size="lg"
        variant="primary"
        text={message}
        showDots
        showPulseRing
        centered
      />
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION LOADING
// ═══════════════════════════════════════════════════════════════

interface IInitializationLoadingProps {
  phase?: 'starting' | 'loading_services' | 'loading_ui' | 'ready';
  customMessage?: string;
}

const phaseMessages: Record<string, string> = {
  starting: 'Starting up',
  loading_services: 'Loading services',
  loading_ui: 'Preparing interface',
  ready: 'Ready'
};

export const InitializationLoading: React.FC<IInitializationLoadingProps> = ({
  phase = 'starting',
  customMessage
}) => {
  const message = customMessage || phaseMessages[phase] || 'Loading';

  return (
    <div className="sage-init-loading-container">
      <ModernSpinner size="xl" variant="primary" showPulseRing />
      <div className="sage-init-loading-container__message">
        {message}
        <span
          className="sage-modern-spinner__dots"
          style={{ marginLeft: '2px' }}
        >
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0s'
            }}
          >
            .
          </span>
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0.15s'
            }}
          >
            .
          </span>
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0.3s'
            }}
          >
            .
          </span>
        </span>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// CONTEXT LOADING INDICATOR
// ═══════════════════════════════════════════════════════════════

interface IContextLoadingIndicatorProps {
  type: 'database' | 'dataset' | 'snippet' | 'file';
  isLoading?: boolean;
}

const contextTypeLabels: Record<string, string> = {
  database: 'Loading databases',
  dataset: 'Loading datasets',
  snippet: 'Loading snippets',
  file: 'Loading files'
};

export const ContextLoadingIndicator: React.FC<
  IContextLoadingIndicatorProps
> = ({ type, isLoading = true }) => {
  if (!isLoading) return null;

  return (
    <div
      className="sage-context-loading-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        backgroundColor: 'var(--jp-layout-color2, #f5f5f5)',
        borderRadius: '6px',
        fontSize: '12px',
        color: 'var(--jp-ui-font-color2, #666)'
      }}
    >
      <ModernSpinner size="xs" variant="subtle" />
      <span>{contextTypeLabels[type] || 'Loading'}</span>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════

export default {
  Skeleton,
  MessageSkeleton,
  MessageListSkeleton,
  ChatBoxSkeleton,
  ChatHistoryLoadingOverlay,
  InitializationLoading,
  ContextLoadingIndicator
};
