import * as React from 'react';
import {
  APPROVE_ICON,
  ARROW_DOWN_ICON,
  ARROW_UP_ICON,
  REJECT_ICON,
  RUN_ICON
} from './icons';
import {
  useDiffStore,
  selectIsRunAllLoading,
  selectIsRejectAllLoading,
  selectIsApproveAllLoading,
  selectIsAnyActionLoading
} from '@/stores/diffStore';

interface IDiffNavigationContentProps {
  isVisible: boolean;
  currentDiff: number;
  totalDiffs: number;
  isRunContext: boolean;
  /** Whether there are any runnable diffs (add/edit) - remove diffs can't be run */
  hasRunnableDiffs?: boolean;
  onNavigatePrevious: () => void;
  onNavigateNext: () => void;
  onRejectAll: () => void | Promise<void>;
  onAcceptAll: () => void | Promise<void>;
  onAcceptAndRunAll: () => void | Promise<void>;
}

export function DiffNavigationContent({
  isVisible,
  currentDiff,
  totalDiffs,
  isRunContext,
  hasRunnableDiffs = true,
  onNavigatePrevious,
  onNavigateNext,
  onRejectAll,
  onAcceptAll,
  onAcceptAndRunAll
}: IDiffNavigationContentProps): JSX.Element | null {
  // Use shared loading state from diffStore
  const isRunLoading = useDiffStore(selectIsRunAllLoading);
  const isRejectLoading = useDiffStore(selectIsRejectAllLoading);
  const isApproveLoading = useDiffStore(selectIsApproveAllLoading);
  const isAnyLoading = useDiffStore(selectIsAnyActionLoading);
  const { setRunAllLoading, setRejectAllLoading, setApproveAllLoading } =
    useDiffStore.getState();

  if (!isVisible || totalDiffs === 0) {
    return null;
  }

  return (
    <div className="sage-ai-diff-navigation-floating-content">
      {/* Navigation Section (Left) */}
      <div className="sage-ai-diff-navigation-navigation-section">
        <button
          className="sage-ai-diff-navigation-nav-button sage-ai-diff-navigation-prev-button"
          onClick={onNavigatePrevious}
          title="Previous cell"
        >
          <ARROW_UP_ICON.react className="sage-ai-diff-navigation-nav-icon" />
        </button>
        <span className="sage-ai-diff-navigation-counter-display">
          {currentDiff} / {totalDiffs}
        </span>
        <button
          className="sage-ai-diff-navigation-nav-button sage-ai-diff-navigation-next-button"
          onClick={onNavigateNext}
          title="Next cell"
        >
          <ARROW_DOWN_ICON.react className="sage-ai-diff-navigation-nav-icon" />
        </button>
      </div>

      {/* Action Buttons Section (Right) */}
      <div className="sage-ai-diff-navigation-button-section">
        <button
          className={`sage-ai-diff-navigation-action-button sage-ai-diff-navigation-reject-button ${isRejectLoading ? 'sage-ai-btn-loading' : ''}`}
          disabled={isAnyLoading}
          onClick={async () => {
            setRejectAllLoading(true);
            try {
              await onRejectAll();
            } finally {
              setRejectAllLoading(false);
            }
          }}
        >
          {isRejectLoading ? (
            <span className="sage-ai-btn-spinner" />
          ) : (
            <REJECT_ICON.react className="sage-ai-diff-navigation-action-icon" />
          )}
          <span>{totalDiffs > 1 ? 'Reject All' : 'Reject'}</span>
        </button>
        <button
          className={`sage-ai-diff-navigation-action-button sage-ai-diff-navigation-approve-button ${isApproveLoading ? 'sage-ai-btn-loading' : ''}`}
          disabled={isAnyLoading}
          onClick={async () => {
            setApproveAllLoading(true);
            try {
              await onAcceptAll();
            } finally {
              setApproveAllLoading(false);
            }
          }}
        >
          {isApproveLoading ? (
            <span className="sage-ai-btn-spinner" />
          ) : (
            <APPROVE_ICON.react className="sage-ai-diff-navigation-action-icon" />
          )}
          <span>{totalDiffs > 1 ? 'Approve All' : 'Approve'}</span>
        </button>
        {/* Only show Run button if in run context AND there are runnable diffs (add/edit) */}
        {isRunContext && hasRunnableDiffs && (
          <button
            className={`sage-ai-diff-navigation-action-button sage-ai-diff-navigation-accept-run-button ${isRunLoading ? 'sage-ai-btn-loading' : ''}`}
            disabled={isAnyLoading}
            onClick={async () => {
              setRunAllLoading(true);
              try {
                await onAcceptAndRunAll();
              } finally {
                setRunAllLoading(false);
              }
            }}
          >
            {isRunLoading ? (
              <span className="sage-ai-btn-spinner" />
            ) : (
              <RUN_ICON.react className="sage-ai-diff-navigation-action-icon" />
            )}
            <span>{totalDiffs > 1 ? 'Run All' : 'Run'}</span>
          </button>
        )}
      </div>
    </div>
  );
}
