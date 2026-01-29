/**
 * ThreadBanner - React component for the thread selection sidebar
 *
 * Displays a slide-out panel with all chat threads for the current notebook.
 * Users can select a thread to switch to it, or the list shows "No chat history"
 * if there are no threads.
 *
 * Uses a React Portal to render at the chatbox level for proper positioning.
 */

import * as React from 'react';
import { useCallback, useEffect, useRef } from 'react';
// @ts-ignore - createPortal types may not be available in all environments
import { createPortal } from 'react-dom';
import { useToolbarStore } from '@/stores';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ThreadItem {
  id: string;
  name: string;
  lastUpdated: number;
}

export interface ThreadBannerProps {
  /** List of threads to display */
  threads: ThreadItem[];
  /** ID of the currently active thread */
  currentThreadId: string | null;
  /** Callback when a thread is selected */
  onSelectThread: (threadId: string) => void;
  /** Whether a notebook is currently selected */
  hasNotebook: boolean;
  /** Container element for the portal (chatbox node) */
  portalContainer?: HTMLElement | null;
  /** Whether threads are currently loading */
  isLoading?: boolean;
}

// ═══════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════

/**
 * Format a date as a string.
 * Example: "7/1/25 · 12:00 PM"
 */
function formatDate(timestamp: number): string {
  return (
    new Date(timestamp).toLocaleDateString('en-US', {
      month: 'numeric',
      day: 'numeric',
      year: '2-digit'
    }) +
    ' · ' +
    new Date(timestamp).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  );
}

/**
 * Filter thread list - no filtering needed since all threads should be shown.
 * Previously this filtered "New Chat" duplicates, but that caused issues
 * when a thread named "New Chat" had actual messages.
 */
function filterNewChatThreads(threads: ThreadItem[]): ThreadItem[] {
  // Show all threads - filtering is handled by ChatHistoryManager during save
  return threads;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export function ThreadBanner({
  threads,
  currentThreadId,
  onSelectThread,
  hasNotebook,
  portalContainer,
  isLoading = false
}: ThreadBannerProps): JSX.Element | null {
  const bannerRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // Toolbar store state
  const isBannerOpen = useToolbarStore(state => state.isBannerOpen);
  const closeBanner = useToolbarStore(state => state.closeBanner);

  // Sort threads by last updated (most recent first) and filter
  const sortedThreads = [...threads].sort(
    (a, b) => b.lastUpdated - a.lastUpdated
  );
  const displayThreads = filterNewChatThreads(sortedThreads);

  // Debug: Log thread counts at each stage
  // console.log(`[ThreadBanner] Received ${threads.length} threads, sorted ${sortedThreads.length}, displaying ${displayThreads.length}`);

  // Handle thread selection
  const handleSelectThread = useCallback(
    (threadId: string) => {
      onSelectThread(threadId);
      closeBanner();
    },
    [onSelectThread, closeBanner]
  );

  // Handle overlay click
  const handleOverlayClick = useCallback(() => {
    closeBanner();
  }, [closeBanner]);

  // Handle close button click
  const handleCloseClick = useCallback(() => {
    closeBanner();
  }, [closeBanner]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isBannerOpen) {
        closeBanner();
      }
    };

    if (isBannerOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isBannerOpen, closeBanner]);

  // Render content based on state
  const renderContent = () => {
    // Show loading spinner while loading
    if (isLoading) {
      return (
        <div className="sage-ai-banner-loading">
          <div className="sage-ai-banner-spinner" />
          <div className="sage-ai-banner-loading-text">Loading chats...</div>
        </div>
      );
    }

    if (!hasNotebook) {
      return <div className="sage-ai-banner-empty">No notebook selected</div>;
    }

    if (displayThreads.length === 0) {
      return <div className="sage-ai-banner-empty">No chat history</div>;
    }

    return displayThreads.map(thread => (
      <div
        key={thread.id}
        className={`sage-ai-banner-thread-item ${
          thread.id === currentThreadId ? 'active' : ''
        }`}
        onClick={() => handleSelectThread(thread.id)}
        role="button"
        tabIndex={0}
        onKeyDown={e => {
          if (e.key === 'Enter' || e.key === ' ') {
            handleSelectThread(thread.id);
          }
        }}
      >
        <div className="sage-ai-banner-thread-name">{thread.name}</div>
        <div className="sage-ai-banner-thread-date">
          {formatDate(thread.lastUpdated)}
        </div>
      </div>
    ));
  };

  const bannerContent = (
    <>
      {/* Overlay */}
      <div
        ref={overlayRef}
        className={`sage-ai-banner-overlay ${isBannerOpen ? 'visible' : ''}`}
        style={{ display: isBannerOpen ? 'block' : 'none' }}
        onClick={handleOverlayClick}
      />

      {/* Banner */}
      <div
        ref={bannerRef}
        className={`sage-ai-left-side-banner ${isBannerOpen ? 'visible' : ''}`}
        style={{ display: isBannerOpen ? 'block' : 'none' }}
      >
        <div className="sage-ai-banner-header">
          <h3>All Chats</h3>
          <button
            className="sage-ai-icon-close sage-ai-icon-button-sm"
            onClick={handleCloseClick}
            type="button"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="sage-ai-banner-content">
          <div className="sage-ai-banner-threads">{renderContent()}</div>
        </div>
      </div>
    </>
  );

  // Always use portal - don't render inline to prevent removeChild errors
  // when switching from inline to portal rendering
  if (!portalContainer) {
    return null;
  }

  return createPortal(bannerContent, portalContainer);
}
