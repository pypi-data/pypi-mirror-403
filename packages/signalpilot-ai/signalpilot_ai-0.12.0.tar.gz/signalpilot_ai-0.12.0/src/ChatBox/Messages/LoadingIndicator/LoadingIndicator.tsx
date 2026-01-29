/**
 * LoadingIndicator Component
 *
 * Displays an animated loading indicator with customizable text.
 * Used while waiting for AI responses or processing operations.
 *
 * Features:
 * - Animated blob loader (pulsating gradient)
 * - Customizable loading text
 *
 * @example
 * ```tsx
 * <LoadingIndicator text="Generating..." />
 * <LoadingIndicator text="Processing request..." />
 * ```
 */
import React from 'react';

export interface LoadingIndicatorProps {
  /** The loading text to display (default: "Generating...") */
  text?: string;
}

/**
 * LoadingIndicator - Shows animated blob with loading text
 *
 * Styling is handled by CSS classes:
 * - .sage-ai-message.sage-ai-loading: Container with flex layout
 * - .sage-ai-blob-loader: Animated pulsating blob
 */
export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  text = 'Generating...'
}) => {
  return (
    <div className="sage-ai-message sage-ai-loading">
      {/* Animated blob loader */}
      <div className="sage-ai-blob-loader" />

      {/* Loading text */}
      <span>{text}</span>
    </div>
  );
};

export default LoadingIndicator;
