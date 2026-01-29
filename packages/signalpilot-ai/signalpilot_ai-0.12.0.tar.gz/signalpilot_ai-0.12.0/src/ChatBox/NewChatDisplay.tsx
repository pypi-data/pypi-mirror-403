/**
 * NewChatDisplay Component (Pure React)
 *
 * Displays the welcome screen when there are no messages in the current chat.
 * Shows recommended prompts that the user can click to start a conversation.
 */

import React, { useCallback } from 'react';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useChatInputStore } from '@/stores/chatInput/chatInputStore'; // ═══════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface NewChatDisplayProps {
  /** Recommended prompts to display */
  recommendedPrompts?: string[];
  /** Callback when a prompt is selected */
  onPromptSelected?: (prompt: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// DEFAULT PROMPTS
// ═══════════════════════════════════════════════════════════════

const DEFAULT_PROMPTS = [
  'Help me analyze my data',
  'Create a visualization',
  'Explain this dataset',
  'Write a function to process data'
];

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const NewChatDisplay: React.FC<NewChatDisplayProps> = ({
  recommendedPrompts = DEFAULT_PROMPTS,
  onPromptSelected
}) => {
  const { showNewChatDisplay, setShowNewChatDisplay } = useChatUIStore();
  const { setInputValue } = useChatInputStore();

  const handlePromptClick = useCallback(
    (prompt: string) => {
      // Set the prompt as input value
      setInputValue(prompt);
      // Hide the new chat display
      setShowNewChatDisplay(false);
      // Call callback if provided
      onPromptSelected?.(prompt);
    },
    [setInputValue, setShowNewChatDisplay, onPromptSelected]
  );

  // Don't render if not visible
  if (!showNewChatDisplay) {
    return null;
  }

  return (
    <div className="sage-ai-new-chat-display">
      <div className="sage-ai-new-chat-container">
        {/* Title Section */}
        <div className="sage-ai-new-chat-title-section">
          <h2 className="sage-ai-new-chat-title">New Chat</h2>
          <p className="sage-ai-new-chat-help">How can I help you?</p>
        </div>

        {/* Prompts Section */}
        {/*<div className="sage-ai-new-chat-prompts-section">*/}
        {/*  <div className="sage-ai-new-chat-prompts-list">*/}
        {/*    {recommendedPrompts.map((prompt, index) => (*/}
        {/*      <button*/}
        {/*        key={index}*/}
        {/*        className="sage-ai-new-chat-prompt-button"*/}
        {/*        onClick={() => handlePromptClick(prompt)}*/}
        {/*      >*/}
        {/*        {prompt}*/}
        {/*      </button>*/}
        {/*    ))}*/}
        {/*  </div>*/}
        {/*</div>*/}
      </div>
    </div>
  );
};

export default NewChatDisplay;
