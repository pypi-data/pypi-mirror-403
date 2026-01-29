/**
 * LoadingIndicator Component
 *
 * Loading spinner with text matching the original ChatContextMenu styling
 */
import React from 'react';
import { LoadingIndicatorProps } from './types';

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = 'Loading contexts...'
}) => {
  return (
    <div className="sage-ai-mention-loading">
      <div className="sage-ai-mention-loading-spinner" />
      <span className="sage-ai-mention-loading-text">{message}</span>
    </div>
  );
};

export default LoadingIndicator;
