/**
 * SystemMessage Component
 *
 * Displays system messages in the chat (e.g., mode changes, status updates).
 * These messages are not saved to history.
 */
import React from 'react';

export interface SystemMessageProps {
  /** The message content (can contain HTML) */
  message: string;
}

/**
 * SystemMessage - Displays informational system messages
 */
export const SystemMessage: React.FC<SystemMessageProps> = ({ message }) => {
  return (
    <div className="sage-ai-message sage-ai-system-message">
      <p
        className="sage-ai-system-message-text"
        dangerouslySetInnerHTML={{ __html: message }}
      />
    </div>
  );
};

export default SystemMessage;
