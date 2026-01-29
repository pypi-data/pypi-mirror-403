/**
 * ErrorMessage Component
 *
 * Displays error messages in the chat (e.g., API failures, validation errors).
 * These messages are styled distinctly with error colors and are NOT saved to history.
 *
 * @example
 * ```tsx
 * <ErrorMessage message="Failed to connect to the server" />
 * ```
 */
import React from 'react';

export interface ErrorMessageProps {
  /** The error message to display */
  message: string;
}

/**
 * ErrorMessage - Displays error notifications in the chat
 *
 * Styling is handled by CSS classes:
 * - .sage-ai-message: Base message styling
 * - .sage-ai-error-message: Error-specific styling (red color, italic)
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return <div className="sage-ai-message sage-ai-error-message">{message}</div>;
};

export default ErrorMessage;
