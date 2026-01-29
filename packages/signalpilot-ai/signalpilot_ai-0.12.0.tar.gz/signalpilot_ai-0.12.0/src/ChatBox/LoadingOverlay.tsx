/**
 * LoadingOverlay Component
 *
 * Full-screen loading overlay for the ChatBox.
 * Displays a loading indicator with optional text.
 */

import React from 'react';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface LoadingOverlayProps {
  /** Loading text to display */
  text?: string;
  /** Whether to show the overlay (controlled by parent) */
  visible?: boolean;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  text = 'Loading...',
  visible = true
}) => {
  if (!visible) {
    return null;
  }

  return (
    <div className="sage-ai-loading-overlay">
      <div className="sage-ai-loading-content">
        <div className="sage-ai-blob-loader" />
        {text && <span className="sage-ai-loading-text">{text}</span>}
      </div>
    </div>
  );
};

export default LoadingOverlay;
