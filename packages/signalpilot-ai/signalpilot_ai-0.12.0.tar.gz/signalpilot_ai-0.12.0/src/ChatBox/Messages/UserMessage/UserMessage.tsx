/**
 * UserMessage Component
 *
 * Displays a user message in the chat with:
 * - Styled context mentions (@cell, @variable, etc.)
 * - Collapsible content for long messages (> 65px)
 * - Checkpoint rollback/redo functionality
 *
 * @example
 * ```tsx
 * <UserMessage
 *   content="Analyze @cell_1 and create a chart"
 *   checkpoint={checkpoint}
 *   onRestore={(checkpoint) => handleRestore(checkpoint)}
 *   onRedo={() => handleRedo()}
 * />
 * ```
 */
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { ICheckpoint } from '@/types';
import {
  renderContextTagsAsStyled,
  renderUnresolvedMentions
} from '@/utils/contextTagUtils';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useAppStore } from '@/stores/appStore';

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

/** Height threshold for collapsible content (in pixels) */
const COLLAPSE_THRESHOLD = 65;

/** Rollback icon SVG */
const ROLLBACK_ICON = `<svg width="13" height="13" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M5.99984 9.83341L2.6665 6.50008M2.6665 6.50008L5.99984 3.16675M2.6665 6.50008H9.6665C10.148 6.50008 10.6248 6.59492 11.0697 6.77919C11.5145 6.96346 11.9187 7.23354 12.2592 7.57402C12.5997 7.9145 12.8698 8.31871 13.0541 8.76357C13.2383 9.20844 13.3332 9.68523 13.3332 10.1667C13.3332 10.6483 13.2383 11.1251 13.0541 11.5699C12.8698 12.0148 12.5997 12.419 12.2592 12.7595C11.9187 13.1 11.5145 13.37 11.0697 13.5543C10.6248 13.7386 10.148 13.8334 9.6665 13.8334H7.33317" stroke="var(--jp-ui-font-color2)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>`;

// ═══════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Escape HTML special characters in text
 */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Process user message content:
 * 1. Render context tags as styled mentions
 * 2. Escape HTML in non-mention parts
 * 3. Render unresolved @mentions with warning icon
 * 4. Convert newlines to <br> tags
 *
 * @param message - Raw user message
 * @returns HTML string safe for dangerouslySetInnerHTML
 */
export function processUserMessageContent(message: string): string {
  // Render context tags as styled mentions
  const processedMessage = renderContextTagsAsStyled(message);

  // Split by mention spans to preserve them while escaping other content
  const mentionSpanRegex =
    /<span class="sage-ai-mention[^"]*"[^>]*>[^<]*<\/span>/g;
  const parts = processedMessage.split(mentionSpanRegex);
  const mentions = processedMessage.match(mentionSpanRegex) || [];

  // Rebuild with escaped text parts and preserved mentions
  let result = '';
  for (let i = 0; i < parts.length; i++) {
    // Escape the text part and convert newlines
    let escapedPart = escapeHtml(parts[i]).replace(/\n/g, '<br>');
    // Render any unresolved @mentions with warning icon
    escapedPart = renderUnresolvedMentions(escapedPart);
    result += escapedPart;
    if (mentions[i]) {
      result += mentions[i];
    }
  }

  return result;
}

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface UserMessageProps {
  /** The raw message content */
  content: string;

  /** Associated checkpoint for rollback (if any) */
  checkpoint?: ICheckpoint;

  /** Whether the message is hidden from view */
  hidden?: boolean;

  /** Whether this is a demo message (no checkpoint controls) */
  isDemo?: boolean;

  /** Callback when restore checkpoint is clicked */
  onRestore?: (checkpoint: ICheckpoint) => void;

  /** Callback when redo checkpoint is clicked */
  onRedo?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * UserMessage - Renders a user message with checkpoint controls
 *
 * CSS Classes:
 * - .sage-ai-message.sage-ai-user-message: Main container
 * - .sage-ai-message-content.sage-ai-user-message-content: Content wrapper
 * - .collapsed: Applied when content is collapsed
 * - .collapsible: Applied when content can be collapsed
 * - .sage-ai-rollback-element: Rollback button container
 * - .sage-ai-rollback-icon: Icon within rollback button
 * - .sage-ai-rollback-tooltip: Hover tooltip
 * - .sage-ai-restore-redo-element: Redo button (shown after restore)
 */
export const UserMessage: React.FC<UserMessageProps> = ({
  content,
  checkpoint,
  hidden = false,
  isDemo = false,
  onRestore,
  onRedo
}) => {
  // ─────────────────────────────────────────────────────────────
  // State
  // ─────────────────────────────────────────────────────────────

  /** Whether content is currently collapsed */
  const [isCollapsed, setIsCollapsed] = useState(false);

  /** Whether content can be collapsed (height > threshold) */
  const [isCollapsible, setIsCollapsible] = useState(false);

  /** Ref to content element for height measurement */
  const contentRef = useRef<HTMLDivElement>(null);

  // Debug: log checkpoint presence for this message
  useEffect(() => {
    console.log('[UserMessage] Rendered:', {
      contentPreview: content.substring(0, 50),
      hasCheckpoint: !!checkpoint,
      checkpointId: checkpoint?.id,
      isDemo
    });
  }, [content, checkpoint, isDemo]);

  // Check if this message's checkpoint is currently being restored (from store)
  const restoringCheckpointId = useChatMessagesStore(
    state => state.restoringCheckpointId
  );
  const showRedo = checkpoint?.id === restoringCheckpointId;

  // Hide checkpoint controls on the launcher (no notebook to restore to)
  const isLauncherActive = useAppStore(state => state.isLauncherActive);

  // ─────────────────────────────────────────────────────────────
  // Effects
  // ─────────────────────────────────────────────────────────────

  /**
   * Check if content should be collapsible based on height
   */
  useEffect(() => {
    if (contentRef.current) {
      const height = contentRef.current.offsetHeight;
      if (height >= COLLAPSE_THRESHOLD) {
        setIsCollapsible(true);
        setIsCollapsed(true);
      }
    }
  }, [content]);

  // ─────────────────────────────────────────────────────────────
  // Memoized Values
  // ─────────────────────────────────────────────────────────────

  /** Processed HTML content with styled mentions */
  const processedContent = useMemo(
    () => processUserMessageContent(content),
    [content]
  );

  // ─────────────────────────────────────────────────────────────
  // Handlers
  // ─────────────────────────────────────────────────────────────

  /** Toggle collapsed state when clicking content */
  const handleContentClick = useCallback(() => {
    if (isCollapsible) {
      setIsCollapsed(prev => !prev);
    }
  }, [isCollapsible]);

  /** Handle restore checkpoint click */
  const handleRestore = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (checkpoint && onRestore) {
        onRestore(checkpoint);
        // showRedo is now controlled by store's restoringCheckpointId
      }
    },
    [checkpoint, onRestore]
  );

  /** Handle redo click */
  const handleRedo = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onRedo) {
        onRedo();
        // showRedo is now controlled by store's restoringCheckpointId
      }
    },
    [onRedo]
  );

  // ─────────────────────────────────────────────────────────────
  // Render
  // ─────────────────────────────────────────────────────────────

  // Build content class names
  const contentClasses = [
    'sage-ai-message-content',
    'sage-ai-user-message-content',
    isCollapsible && 'collapsible',
    isCollapsed && 'collapsed'
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      className="sage-ai-message sage-ai-user-message"
      data-checkpoint-id={checkpoint?.id}
      style={hidden ? { display: 'none' } : undefined}
    >
      {/* Message content */}
      <div
        ref={contentRef}
        className={contentClasses}
        onClick={handleContentClick}
        dangerouslySetInnerHTML={{ __html: processedContent }}
      />

      {/* Checkpoint controls (only if not demo mode, not launcher, and checkpoint exists) */}
      {!isDemo && !isLauncherActive && checkpoint && (
        <>
          {/* Rollback button */}
          <div className="sage-ai-rollback-element" onClick={handleRestore}>
            <span className="sage-ai-rollback-tooltip">Restore checkpoint</span>
            <span
              className="sage-ai-rollback-icon"
              dangerouslySetInnerHTML={{ __html: ROLLBACK_ICON }}
            />
          </div>

          {/* Redo button (shown after restore) */}
          <div
            className="sage-ai-restore-redo-element"
            onClick={handleRedo}
            style={showRedo ? { display: 'block' } : undefined}
          >
            Redo checkpoint
          </div>
        </>
      )}
    </div>
  );
};

export default UserMessage;
