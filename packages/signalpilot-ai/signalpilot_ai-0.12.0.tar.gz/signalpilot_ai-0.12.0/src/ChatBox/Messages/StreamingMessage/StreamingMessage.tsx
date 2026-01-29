/**
 * StreamingMessage Component
 *
 * Displays a streaming AI message that updates in real-time.
 * Uses Zustand store for reactive updates without prop drilling.
 *
 * Features:
 * - Real-time markdown rendering as text streams in
 * - Animated cursor at the end of content (via CSS ::after)
 * - SignalPilot AI header (optional)
 * - Automatic scroll handling
 *
 * Pure React implementation - cursor is handled via CSS pseudo-element.
 *
 * @example
 * ```tsx
 * // The component subscribes to streaming state from the store
 * <StreamingMessage showHeader={true} />
 * ```
 */
import React, { useEffect, useState } from 'react';
import { marked } from 'marked';
import {
  selectIsStreaming,
  selectStreamingText,
  useChatMessagesStore
} from '@/stores/chatMessages';

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

/** SignalPilot AI header icon (gradient star) */
const SIGNALPILOT_ICON = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M6.6243 10.3334C6.56478 10.1026 6.44453 9.89209 6.27605 9.72361C6.10757 9.55513 5.89702 9.43488 5.6663 9.37536L1.5763 8.32069C1.50652 8.30089 1.44511 8.25886 1.40138 8.20099C1.35765 8.14312 1.33398 8.07256 1.33398 8.00002C1.33398 7.92749 1.35765 7.85693 1.40138 7.79906C1.44511 7.74119 1.50652 7.69916 1.5763 7.67936L5.6663 6.62402C5.89693 6.56456 6.10743 6.44441 6.2759 6.27605C6.44438 6.10769 6.56468 5.89728 6.6243 5.66669L7.67897 1.57669C7.69857 1.50664 7.74056 1.44492 7.79851 1.40095C7.85647 1.35699 7.92722 1.33319 7.99997 1.33319C8.07271 1.33319 8.14346 1.35699 8.20142 1.40095C8.25938 1.44492 8.30136 1.50664 8.32097 1.57669L9.37497 5.66669C9.43449 5.89741 9.55474 6.10796 9.72322 6.27644C9.8917 6.44492 10.1023 6.56517 10.333 6.62469L14.423 7.67869C14.4933 7.69809 14.5553 7.74003 14.5995 7.79808C14.6437 7.85612 14.6677 7.92706 14.6677 8.00002C14.6677 8.07298 14.6437 8.14393 14.5995 8.20197C14.5553 8.26002 14.4933 8.30196 14.423 8.32136L10.333 9.37536C10.1023 9.43488 9.8917 9.55513 9.72322 9.72361C9.55474 9.89209 9.43449 10.1026 9.37497 10.3334L8.3203 14.4234C8.3007 14.4934 8.25871 14.5551 8.20075 14.5991C8.1428 14.6431 8.07205 14.6669 7.9993 14.6669C7.92656 14.6669 7.85581 14.6431 7.79785 14.5991C7.73989 14.5551 7.69791 14.4934 7.6783 14.4234L6.6243 10.3334Z" fill="url(#paint0_linear_streaming)"/>
  <path d="M13.333 2V4.66667" stroke="url(#paint1_linear_streaming)" stroke-width="0.984615" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M14.6667 3.33331H12" stroke="url(#paint2_linear_streaming)" stroke-width="0.984615" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M2.66699 11.3333V12.6666" stroke="url(#paint3_linear_streaming)" stroke-width="0.984615" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M3.33333 12H2" stroke="url(#paint4_linear_streaming)" stroke-width="0.984615" stroke-linecap="round" stroke-linejoin="round"/>
  <defs>
  <linearGradient id="paint0_linear_streaming" x1="1.33398" y1="1.33319" x2="14.6677" y2="14.6669" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FEC163"/>
  <stop offset="1" stop-color="#DE4313"/>
  </linearGradient>
  <linearGradient id="paint1_linear_streaming" x1="13.333" y1="2" x2="15.0864" y2="2.65753" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FEC163"/>
  <stop offset="1" stop-color="#DE4313"/>
  </linearGradient>
  <linearGradient id="paint2_linear_streaming" x1="12" y1="3.33331" x2="12.6575" y2="5.08674" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FEC163"/>
  <stop offset="1" stop-color="#DE4313"/>
  </linearGradient>
  <linearGradient id="paint3_linear_streaming" x1="2.66699" y1="11.3333" x2="3.94699" y2="12.2933" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FEC163"/>
  <stop offset="1" stop-color="#DE4313"/>
  </linearGradient>
  <linearGradient id="paint4_linear_streaming" x1="2" y1="12" x2="2.96" y2="13.28" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FEC163"/>
  <stop offset="1" stop-color="#DE4313"/>
  </linearGradient>
  </defs>
</svg>`;

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface StreamingMessageProps {
  /** Whether to show the SignalPilot AI header */
  showHeader?: boolean;

  /** Whether this streaming message should be hidden (welcome pre-load mode) */
  hidden?: boolean;

  /** Content to display (for imperative mode - alternative to store) */
  content?: string;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * StreamingMessage - Renders a streaming AI response with live updates
 *
 * CSS Classes:
 * - .sage-ai-message.sage-ai-ai-message.sage-ai-streaming-message: Main container
 * - .sage-ai-message-header: Header container
 * - .sage-ai-message-header-image: Header icon
 * - .sage-ai-message-header-title: Header title text
 * - .sage-ai-message-content.sage-ai-streaming-content: Content wrapper
 * - .sage-ai-streaming-cursor: Animated cursor at end of content
 */
export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  showHeader = true,
  hidden = false,
  content: propContent
}) => {
  // ─────────────────────────────────────────────────────────────
  // Store State (for reactive mode)
  // ─────────────────────────────────────────────────────────────

  const storeStreamingText = useChatMessagesStore(selectStreamingText);
  const isStreaming = useChatMessagesStore(selectIsStreaming);

  // Use prop content if provided, otherwise use store
  const streamingText = propContent ?? storeStreamingText;

  // ─────────────────────────────────────────────────────────────
  // Local State
  // ─────────────────────────────────────────────────────────────

  /** Rendered HTML content */
  const [renderedHtml, setRenderedHtml] = useState<string>('');

  // ─────────────────────────────────────────────────────────────
  // Effects
  // ─────────────────────────────────────────────────────────────

  /**
   * Render markdown when streaming text changes
   */
  useEffect(() => {
    let mounted = true;

    if (!streamingText) {
      setRenderedHtml('');
      return;
    }

    // Configure marked for streaming
    marked.setOptions({
      gfm: true,
      breaks: false
    });

    // marked.parse can return string or Promise<string>
    const parseMarkdown = async () => {
      try {
        const html = await marked.parse(streamingText);
        if (mounted) {
          setRenderedHtml(html);
        }
      } catch (err: unknown) {
        console.error('[StreamingMessage] Markdown parse error:', err);
        if (mounted) {
          setRenderedHtml(streamingText);
        }
      }
    };

    void parseMarkdown();

    return () => {
      mounted = false;
    };
  }, [streamingText]);

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  // Don't render if not streaming and no content (for store mode)
  if (!propContent && !isStreaming && !streamingText) {
    return null;
  }

  return (
    <div
      className="sage-ai-message sage-ai-ai-message sage-ai-streaming-message"
      style={hidden ? { display: 'none' } : undefined}
    >
      {/* Header */}
      <div
        className="sage-ai-message-header"
        style={showHeader ? undefined : { display: 'none' }}
      >
        <div
          className="sage-ai-message-header-image"
          dangerouslySetInnerHTML={{ __html: SIGNALPILOT_ICON }}
        />
        <span className="sage-ai-message-header-title">SignalPilot AI</span>
      </div>

      {/* Content with streaming cursor (cursor via CSS ::after) */}
      <div
        className="sage-ai-message-content sage-ai-streaming-content sage-ai-markdown-content"
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
      />
    </div>
  );
};

export default StreamingMessage;
