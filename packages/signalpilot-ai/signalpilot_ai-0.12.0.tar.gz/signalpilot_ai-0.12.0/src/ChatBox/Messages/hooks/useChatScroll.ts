/**
 * useChatScroll Hook
 *
 * Manages scroll behavior for the chat messages panel, including:
 * - Auto-scroll to bottom when new messages arrive (if already at bottom)
 * - Track scroll position state
 * - Show/hide scroll-to-bottom button
 *
 * @example
 * ```tsx
 * const { scrollRef, scrollToBottom, isAtBottom } = useChatScroll();
 *
 * return (
 *   <div ref={scrollRef} className="messages-container">
 *     {messages.map(msg => <Message key={msg.id} {...msg} />)}
 *     {!isAtBottom && <ScrollButton onClick={scrollToBottom} />}
 *   </div>
 * );
 * ```
 */

import { useCallback, useEffect, useRef } from 'react';
import {
  selectIsThinking,
  selectMessages,
  selectScrollState,
  selectStreaming,
  useChatMessagesStore
} from '@/stores/chatMessages';
import {
  useWaitingReplyStore,
  selectIsVisible as selectWaitingReplyVisible
} from '@/stores/waitingReplyStore';

/** Threshold for considering "at bottom" (in pixels) */
const SCROLL_THRESHOLD = 50;

/** Debounce time for scroll events (in ms) */
const SCROLL_DEBOUNCE = 100;

export interface UseChatScrollResult {
  /** Ref to attach to scrollable container */
  scrollRef: React.RefObject<HTMLDivElement>;
  /** Scroll to bottom of container */
  scrollToBottom: () => void;
  /** Whether currently at bottom */
  isAtBottom: boolean;
  /** Whether to show scroll button */
  showScrollButton: boolean;
}

export function useChatScroll(): UseChatScrollResult {
  const scrollRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Track whether we're currently auto-scrolling (programmatic scroll)
  // This prevents the scroll handler from thinking the user scrolled away
  // when it's actually the LLM streaming that triggered the scroll
  const isAutoScrollingRef = useRef(false);
  const autoScrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Store state
  const messages = useChatMessagesStore(selectMessages);
  const streaming = useChatMessagesStore(selectStreaming);
  const isThinking = useChatMessagesStore(selectIsThinking);
  const scrollState = useChatMessagesStore(selectScrollState);
  const setScrollAtBottom = useChatMessagesStore(
    state => state.setScrollAtBottom
  );
  const setShowScrollButton = useChatMessagesStore(
    state => state.setShowScrollButton
  );

  // Waiting reply state - triggers auto-scroll when it appears
  const waitingReplyVisible = useWaitingReplyStore(selectWaitingReplyVisible);

  /**
   * Calculate if scrolled to bottom
   */
  const calculateIsAtBottom = useCallback(() => {
    const container = scrollRef.current;
    if (!container) return true;

    const { scrollTop, scrollHeight, clientHeight } = container;
    return scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD;
  }, []);

  /**
   * Scroll to bottom of container
   * Sets isAutoScrollingRef to prevent scroll handler from thinking user scrolled away
   */
  const scrollToBottom = useCallback(() => {
    const container = scrollRef.current;
    if (container) {
      // Mark that we're auto-scrolling - scroll events should be ignored
      isAutoScrollingRef.current = true;

      // Clear any pending auto-scroll timeout
      if (autoScrollTimeoutRef.current) {
        clearTimeout(autoScrollTimeoutRef.current);
      }

      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
      setScrollAtBottom(true);
      setShowScrollButton(false);

      // Clear auto-scrolling flag after animation completes
      // Using 500ms to cover the smooth scroll animation duration
      autoScrollTimeoutRef.current = setTimeout(() => {
        isAutoScrollingRef.current = false;
      }, 500);
    }
  }, [setScrollAtBottom, setShowScrollButton]);

  /**
   * Handle scroll events with debouncing
   * Only updates state for user-initiated scrolls, not programmatic auto-scrolls
   */
  const handleScroll = useCallback(() => {
    // Ignore scroll events triggered by programmatic auto-scrolling
    // This ensures LLM streaming doesn't accidentally disable auto-scroll
    if (isAutoScrollingRef.current) {
      return;
    }

    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current);
    }

    scrollTimeoutRef.current = setTimeout(() => {
      const atBottom = calculateIsAtBottom();
      setScrollAtBottom(atBottom);
      setShowScrollButton(!atBottom);
    }, SCROLL_DEBOUNCE);
  }, [calculateIsAtBottom, setScrollAtBottom, setShowScrollButton]);

  /**
   * Attach scroll listener
   */
  useEffect(() => {
    const container = scrollRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      if (autoScrollTimeoutRef.current) {
        clearTimeout(autoScrollTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  /**
   * Auto-scroll when messages change (if at bottom)
   * Uses scrollToBottom which properly marks the scroll as programmatic
   */
  useEffect(() => {
    if (scrollState.isAtBottom) {
      // Use requestAnimationFrame for smooth scrolling after render
      requestAnimationFrame(() => {
        const container = scrollRef.current;
        if (container) {
          // Mark as auto-scrolling to prevent scroll handler from thinking user scrolled
          isAutoScrollingRef.current = true;

          // Clear any pending auto-scroll timeout
          if (autoScrollTimeoutRef.current) {
            clearTimeout(autoScrollTimeoutRef.current);
          }

          container.scrollTop = container.scrollHeight;

          // Clear the flag after a short delay to allow scroll event to fire and be ignored
          autoScrollTimeoutRef.current = setTimeout(() => {
            isAutoScrollingRef.current = false;
          }, 100);
        }
      });
    }
  }, [
    messages.length,
    streaming.text,
    isThinking,
    waitingReplyVisible,
    scrollState.isAtBottom
  ]);

  /**
   * Initial scroll to bottom
   */
  useEffect(() => {
    scrollToBottom();
  }, []);

  return {
    scrollRef,
    scrollToBottom,
    isAtBottom: scrollState.isAtBottom,
    showScrollButton: scrollState.showScrollButton
  };
}

export default useChatScroll;
