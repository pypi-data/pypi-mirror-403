/**
 * DemoControlPanel Component
 *
 * A floating control panel for demo mode.
 * Provides options to either try the demo interactively or skip to results.
 */

import React, { useCallback } from 'react';
import {
  useDemoControlStore,
  selectIsVisible,
  selectIsDemoFinished,
  selectShowSkipButton
} from '@/stores/demoControlStore';

// ═══════════════════════════════════════════════════════════════
// ICONS
// ═══════════════════════════════════════════════════════════════

const DemoIcon: React.FC = () => (
  <svg
    width="14"
    height="14"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M12 2L2 7l10 5 10-5-10-5z" />
    <path d="M2 17l10 5 10-5" />
    <path d="M2 12l10 5 10-5" />
  </svg>
);

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const DemoControlPanel: React.FC = () => {
  // Store state
  const isVisible = useDemoControlStore(selectIsVisible);
  const isDemoFinished = useDemoControlStore(selectIsDemoFinished);
  const showSkipButton = useDemoControlStore(selectShowSkipButton);
  const onTryIt = useDemoControlStore(state => state.onTryIt);
  const onSkip = useDemoControlStore(state => state.onSkip);
  const hideSkipButton = useDemoControlStore(state => state.hideSkipButton);

  // Handlers
  const handleTryIt = useCallback(() => {
    hideSkipButton();
    onTryIt?.();
  }, [hideSkipButton, onTryIt]);

  const handleSkip = useCallback(() => {
    hideSkipButton();
    onSkip?.();
  }, [hideSkipButton, onSkip]);

  // Don't render if not visible
  if (!isVisible) {
    return null;
  }

  // Determine button text based on demo finished state
  const tryItButtonText = isDemoFinished ? 'Login to Chat' : 'Try it Yourself';

  return (
    <div className="sage-ai-demo-control-panel">
      <div className="sage-ai-demo-control-container">
        {/* Title */}
        <div className="sage-ai-demo-control-title">
          <DemoIcon />
          Demo Mode
        </div>

        {/* Buttons */}
        <div className="sage-ai-demo-control-buttons">
          <button
            className="sage-ai-demo-control-button sage-ai-demo-control-try"
            onClick={handleTryIt}
            type="button"
          >
            <span>{tryItButtonText}</span>
          </button>

          {showSkipButton && (
            <button
              className="sage-ai-demo-control-button sage-ai-demo-control-skip"
              onClick={handleSkip}
              type="button"
            >
              <span>Results</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DemoControlPanel;
