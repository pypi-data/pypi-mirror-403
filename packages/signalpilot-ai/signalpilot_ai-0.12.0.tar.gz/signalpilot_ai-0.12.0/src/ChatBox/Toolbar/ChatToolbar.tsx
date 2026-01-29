/**
 * ChatToolbar - React component for the chat toolbar
 *
 * Displays:
 * - Thread selector button (opens thread banner)
 * - Thread name display
 * - Auto-run toggle
 * - New chat button
 * - More options button
 */

import * as React from 'react';
import { useCallback, useRef } from 'react';
import { useAppStore, useToolbarStore } from '@/stores';
import { DemoOverlay } from '@/Components/DemoOverlay';

// ═══════════════════════════════════════════════════════════════
// SVG ICONS
// ═══════════════════════════════════════════════════════════════

const MenuIcon = () => (
  <svg
    width="20"
    height="21"
    viewBox="0 0 20 21"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M2.5 10.5H17.5M2.5 5.5H17.5M2.5 15.5H17.5"
      stroke="#949494"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const PlusIcon = () => (
  <svg
    width="16"
    height="17"
    viewBox="0 0 16 17"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M3.3335 8.49992H12.6668M8.00016 3.83325V13.1666"
      stroke="var(--jp-ui-font-color0)"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const MoreOptionsIcon = () => (
  <svg
    width="18"
    height="19"
    viewBox="0 0 18 19"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M9 10.25C9.41421 10.25 9.75 9.91421 9.75 9.5C9.75 9.08579 9.41421 8.75 9 8.75C8.58579 8.75 8.25 9.08579 8.25 9.5C8.25 9.91421 8.58579 10.25 9 10.25Z"
      stroke="var(--jp-ui-font-color0)"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M14.25 10.25C14.6642 10.25 15 9.91421 15 9.5C15 9.08579 14.6642 8.75 14.25 8.75C13.8358 8.75 13.5 9.08579 13.5 9.5C13.5 9.91421 13.8358 10.25 14.25 10.25Z"
      stroke="var(--jp-ui-font-color0)"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M3.75 10.25C4.16421 10.25 4.5 9.91421 4.5 9.5C4.5 9.08579 4.16421 8.75 3.75 8.75C3.33579 8.75 3 9.08579 3 9.5C3 9.91421 3.33579 10.25 3.75 10.25Z"
      stroke="var(--jp-ui-font-color0)"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// ═══════════════════════════════════════════════════════════════
// PROPS INTERFACE
// ═══════════════════════════════════════════════════════════════

export interface ChatToolbarProps {
  /** Current thread name to display */
  threadName: string;
  /** Callback when new chat is clicked */
  onNewChat: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export function ChatToolbar({
  threadName,
  onNewChat
}: ChatToolbarProps): JSX.Element {
  const moreOptionsButtonRef = useRef<HTMLButtonElement>(null);

  // App store state
  const autoRun = useAppStore(state => state.autoRun);
  const setAutoRun = useAppStore(state => state.setAutoRun);

  // Toolbar store state
  const openBanner = useToolbarStore(state => state.openBanner);
  const openMoreOptions = useToolbarStore(state => state.openMoreOptions);
  const isMoreOptionsOpen = useToolbarStore(state => state.isMoreOptionsOpen);

  // Handlers
  const handleThreadSelectorClick = useCallback(() => {
    openBanner();
  }, [openBanner]);

  const handleAutoRunChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setAutoRun(e.target.checked);
    },
    [setAutoRun]
  );

  const handleMoreOptionsClick = useCallback(() => {
    if (moreOptionsButtonRef.current) {
      const rect = moreOptionsButtonRef.current.getBoundingClientRect();
      openMoreOptions(rect);
    }
  }, [openMoreOptions]);

  return (
    <div className="sage-ai-toolbar" style={{ position: 'relative' }}>
      {/* Demo overlay - renders when demo mode is active */}
      <DemoOverlay />

      {/* Thread Selector Button */}
      <button
        className="sage-ai-icon-button-md sage-ai-thread-selector-button"
        onClick={handleThreadSelectorClick}
        title="Select conversation thread"
        type="button"
      >
        <MenuIcon />
      </button>

      {/* Thread Name Display */}
      <span className="sage-ai-thread-name">{threadName}</span>

      {/* Autorun Toggle */}
      <div className="sage-ai-checkbox-container sage-ai-autorun-toggle sage-ai-control-base">
        <input
          id="sage-ai-autorun"
          type="checkbox"
          className="sage-ai-checkbox sage-ai-toggle-input"
          checked={autoRun}
          onChange={handleAutoRunChange}
          title="Automatically run code without confirmation"
        />
        <label
          htmlFor="sage-ai-autorun"
          className="sage-ai-checkbox-label sage-ai-toggle-label"
          title="Automatically run code without confirmation"
        >
          <span className="sage-ai-toggle-switch"></span>
          Auto Run
        </label>
      </div>

      {/* New Chat Button */}
      <button
        className="sage-ai-reset-button sage-ai-control-base"
        onClick={onNewChat}
        title="Start a new chat"
        type="button"
      >
        <PlusIcon />
      </button>

      {/* More Options Button */}
      <button
        ref={moreOptionsButtonRef}
        className="sage-ai-more-options-button sage-ai-icon-button-md"
        onClick={handleMoreOptionsClick}
        title="More options"
        type="button"
        aria-expanded={isMoreOptionsOpen}
        aria-haspopup="true"
      >
        <MoreOptionsIcon />
      </button>
    </div>
  );
}
