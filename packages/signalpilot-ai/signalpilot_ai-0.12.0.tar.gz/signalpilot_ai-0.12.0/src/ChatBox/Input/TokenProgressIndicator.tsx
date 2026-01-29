/**
 * TokenProgressIndicator Component
 *
 * Displays a circular progress indicator showing token usage for the current
 * conversation. Includes:
 * - Circular SVG progress bar with color coding (blue < 40%, orange 40-70%, red >= 70%)
 * - Tooltip showing exact token count
 * - "Compact" button that appears when usage >= 40% to compress chat history
 *
 * This is a controlled component - parent manages the token count state.
 */
import React, { useCallback, useMemo, useState } from 'react';

/** Default maximum recommended tokens before compression is suggested */
const DEFAULT_MAX_TOKENS = 60000;

/** Circle geometry constants */
const CIRCLE_RADIUS = 9;
const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * CIRCLE_RADIUS; // ~56.55

export interface TokenProgressIndicatorProps {
  /** Current token count */
  tokenCount: number;
  /** Maximum recommended tokens (default: 60000) */
  maxTokens?: number;
  /** Callback when compact button is clicked */
  onCompact?: () => void;
  /** Whether the compact operation is in progress */
  isCompacting?: boolean;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * Get the stroke color based on usage percentage
 */
function getStrokeColor(percentage: number): string {
  if (percentage >= 70) {
    return '#e74c3c'; // Red for high usage
  } else if (percentage >= 40) {
    return '#f39c12'; // Orange for medium-high usage
  }
  return '#4a90e2'; // Blue for normal usage
}

/**
 * Format token count for display (e.g., 1.2k, 10k)
 */
function formatTokenCount(count: number): string {
  if (count >= 1000) {
    return (count / 1000).toFixed(count < 10000 ? 1 : 0) + 'k';
  }
  return count.toLocaleString();
}

/**
 * TokenProgressIndicator - Shows circular token usage progress
 */
export const TokenProgressIndicator: React.FC<TokenProgressIndicatorProps> = ({
  tokenCount,
  maxTokens = DEFAULT_MAX_TOKENS,
  onCompact,
  isCompacting = false,
  className = ''
}) => {
  // Local state for tooltip visibility (CSS handles this, but kept for accessibility)
  const [isHovered, setIsHovered] = useState(false);

  // Calculate percentage and offset for SVG circle
  const { percentage, strokeOffset, strokeColor } = useMemo(() => {
    const pct = Math.min(Math.round((tokenCount / maxTokens) * 100), 100);
    const offset = CIRCLE_CIRCUMFERENCE - (pct / 100) * CIRCLE_CIRCUMFERENCE;
    const color = getStrokeColor(pct);
    return { percentage: pct, strokeOffset: offset, strokeColor: color };
  }, [tokenCount, maxTokens]);

  // Show compact button when >= 40%
  const showCompactButton = percentage >= 40;

  // Format tooltip text
  const tooltipText = useMemo(() => {
    const tokenDisplay = formatTokenCount(tokenCount);
    const maxDisplay = formatTokenCount(maxTokens);
    return `${tokenDisplay} / ${maxDisplay} tokens (${percentage}%)`;
  }, [tokenCount, maxTokens, percentage]);

  // Handle compact button click
  const handleCompact = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onCompact && !isCompacting) {
        onCompact();
      }
    },
    [onCompact, isCompacting]
  );

  return (
    <div
      className={`sage-ai-token-progress-wrapper ${className}`}
      style={{
        backgroundColor: showCompactButton
          ? 'var(--jp-layout-color1)'
          : 'transparent'
      }}
    >
      {/* Circular progress indicator */}
      <div
        className="sage-ai-token-progress-container"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          style={{ transform: 'rotate(-90deg)' }}
        >
          {/* Background circle */}
          <circle
            cx="12"
            cy="12"
            r={CIRCLE_RADIUS}
            fill="none"
            stroke="var(--jp-border-color3)"
            strokeWidth="3"
          />
          {/* Progress circle */}
          <circle
            cx="12"
            cy="12"
            r={CIRCLE_RADIUS}
            fill="none"
            stroke={strokeColor}
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${CIRCLE_CIRCUMFERENCE} ${CIRCLE_CIRCUMFERENCE}`}
            strokeDashoffset={strokeOffset}
            className="sage-ai-token-progress-stroke"
          />
        </svg>

        {/* Tooltip */}
        <div className="sage-ai-token-progress-tooltip" role="tooltip">
          {tooltipText}
        </div>
      </div>

      {/* Compact button - only shown when usage >= 40% */}
      {showCompactButton && (
        <button
          type="button"
          className="sage-ai-compress-button visible"
          onClick={handleCompact}
          disabled={isCompacting}
          title="Compact tokens"
          style={{
            opacity: isCompacting ? 0.5 : 1,
            cursor: isCompacting ? 'wait' : 'pointer'
          }}
        >
          Compact
        </button>
      )}
    </div>
  );
};

export default TokenProgressIndicator;
