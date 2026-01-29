/**
 * NewPromptCTA - A React component that displays a call-to-action
 * when the chat context is becoming bloated (token usage >= 40%).
 *
 * Suggests the user start a new chat to improve response quality.
 *
 * Styles are defined in style/base.css under .sage-ai-new-prompt-cta
 */
import * as React from 'react';
import {
  selectShowNewPromptCta,
  useChatInputStore
} from '@/stores/chatInput/chatInputStore';

export interface NewPromptCTAProps {
  /** Callback when "Start a New Chat" is clicked */
  onNewChat: () => void;
}

/**
 * NewPromptCTA component - displays when token usage is high
 */
export const NewPromptCTA: React.FC<NewPromptCTAProps> = ({ onNewChat }) => {
  const showCta = useChatInputStore(selectShowNewPromptCta);

  if (!showCta) {
    return null;
  }

  const handleNewChatClick = (e: React.MouseEvent) => {
    e.preventDefault();
    onNewChat();
  };

  return (
    <div className="sage-ai-new-prompt-cta">
      <p>Context bloated?</p>
      <a href="#" onClick={handleNewChatClick}>
        Start a New Chat
      </a>
    </div>
  );
};

export default NewPromptCTA;
