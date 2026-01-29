/**
 * MoreOptionsPopover - React component for the more options dropdown menu
 *
 * Displays a popover with options like:
 * - Rename Chat
 * - Delete Chat
 *
 * Uses Zustand for visibility state and positioning.
 */

import * as React from 'react';
import { useCallback, useEffect, useRef } from 'react';
import { useToolbarStore } from '@/stores';

// ═══════════════════════════════════════════════════════════════
// SVG ICONS
// ═══════════════════════════════════════════════════════════════

const EditIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M11.3333 2L14 4.66667L5.66667 13H3V10.3333L11.3333 2Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const DeleteIcon = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M2 4H14M12.6667 4V13.3333C12.6667 13.6869 12.5262 14.0261 12.2761 14.2761C12.0261 14.5262 11.6869 14.6667 11.3333 14.6667H4.66667C4.31304 14.6667 3.97391 14.5262 3.72386 14.2761C3.47381 14.0261 3.33333 13.6869 3.33333 13.3333V4M5.33333 4V2.66667C5.33333 2.31304 5.47381 1.97391 5.72386 1.72386C5.97391 1.47381 6.31304 1.33333 6.66667 1.33333H9.33333C9.68696 1.33333 10.0261 1.47381 10.2761 1.72386C10.5262 1.97391 10.6667 2.31304 10.6667 2.66667V4"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// ═══════════════════════════════════════════════════════════════
// PROPS INTERFACE
// ═══════════════════════════════════════════════════════════════

export interface MoreOptionsPopoverProps {
  /** Callback when rename chat is selected */
  onRenameChat: () => void;
  /** Callback when delete chat is selected */
  onDeleteChat: () => void;
  /** Container element for positioning calculations */
  containerRef?: React.RefObject<HTMLElement>;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export function MoreOptionsPopover({
  onRenameChat,
  onDeleteChat,
  containerRef
}: MoreOptionsPopoverProps): JSX.Element | null {
  const popoverRef = useRef<HTMLDivElement>(null);

  // Toolbar store state
  const isOpen = useToolbarStore(state => state.isMoreOptionsOpen);
  const anchorRect = useToolbarStore(state => state.moreOptionsAnchorRect);
  const closeMoreOptions = useToolbarStore(state => state.closeMoreOptions);

  // Handle rename click
  const handleRenameChat = useCallback(() => {
    onRenameChat();
    closeMoreOptions();
  }, [onRenameChat, closeMoreOptions]);

  // Handle delete click
  const handleDeleteChat = useCallback(() => {
    onDeleteChat();
    closeMoreOptions();
  }, [onDeleteChat, closeMoreOptions]);

  // Handle click outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node)
      ) {
        closeMoreOptions();
      }
    };

    // Use setTimeout to avoid catching the opening click
    const timeoutId = setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen, closeMoreOptions]);

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeMoreOptions();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeMoreOptions]);

  // Calculate position
  const calculatePosition = useCallback(() => {
    if (!anchorRect || !popoverRef.current) {
      return { top: 0, left: 0 };
    }

    const popoverWidth = popoverRef.current.offsetWidth || 150;

    // Get container bounds if available
    let containerRect: DOMRect | null = null;
    if (containerRef?.current) {
      containerRect = containerRef.current.getBoundingClientRect();
    }

    // Calculate position - always below the button, right-aligned
    let top: number;
    let left: number;

    if (containerRect) {
      // Position relative to container
      // Below the button
      top = anchorRect.bottom - containerRect.top + 4;
      // Right-aligned with the button
      left = anchorRect.right - containerRect.left - popoverWidth;

      // Ensure it doesn't go off the left edge
      if (left < 8) {
        left = 8;
      }
    } else {
      // Position relative to viewport (fallback)
      // Below the button
      top = anchorRect.bottom + 4;
      // Right-aligned with the button
      left = anchorRect.right - popoverWidth;

      // Ensure it doesn't go off the left edge
      if (left < 8) {
        left = 8;
      }
    }

    return { top, left };
  }, [anchorRect, containerRef]);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  const position = calculatePosition();

  return (
    <div
      ref={popoverRef}
      className="sage-ai-more-options-popover"
      style={{
        position: 'absolute',
        top: `${position.top}px`,
        left: `${position.left}px`,
        zIndex: 9999
      }}
    >
      <div className="sage-ai-more-options-content">
        <button
          className="sage-ai-more-options-item"
          onClick={handleRenameChat}
          type="button"
        >
          <EditIcon />
          <span>Rename Chat</span>
        </button>
        <button
          className="sage-ai-more-options-item sage-ai-more-options-item-danger"
          onClick={handleDeleteChat}
          type="button"
        >
          <DeleteIcon />
          <span>Delete Chat</span>
        </button>
      </div>
    </div>
  );
}
