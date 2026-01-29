/**
 * SendButton Component
 *
 * A circular button that toggles between send and cancel states.
 * - When idle with content: Shows send icon, clicking sends the message
 * - When processing: Shows stop icon, clicking cancels the operation
 * - When idle without content: Shows disabled send icon (lighter color)
 *
 * Uses LLMStateStore for reliable processing state (same source as LLMStateDisplay).
 */
import React, { useCallback } from 'react';
import { useLLMStateStore, LLMDisplayState } from '@/stores/llmStateStore';
import {
  useDemoOverlayStore,
  selectShowSendSpinner
} from '@/stores/demoOverlayStore';

/**
 * SendIcon - Arrow pointing up
 * @param color - Stroke color for the icon
 */
const SendIcon: React.FC<{ color?: string }> = ({ color = '#7A7A7A' }) => (
  <svg
    width="16"
    height="17"
    viewBox="0 0 16 17"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M8.00016 13.1665L8.00016 3.83317M8.00016 3.83317L3.3335 8.49984M8.00016 3.83317L12.6668 8.49984"
      stroke={color}
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * StopIcon - Square for cancel action
 */
const StopIcon: React.FC = () => (
  <svg
    width="16"
    height="17"
    viewBox="0 0 16 17"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <rect
      x="2.70605"
      y="13.7935"
      width="10.5874"
      height="10.5874"
      rx="3"
      transform="rotate(-90 2.70605 13.7935)"
      fill="var(--jp-ui-inverse-font-color1, #ffffff)"
    />
  </svg>
);

/**
 * SpinnerIcon - Animated spinner for demo mode
 */
const SpinnerIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="#7A7A7A"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10" opacity="0.25" />
    <path d="M12 2a10 10 0 0 1 10 10" opacity="0.75">
      <animateTransform
        attributeName="transform"
        type="rotate"
        from="0 12 12"
        to="360 12 12"
        dur="1s"
        repeatCount="indefinite"
      />
    </path>
  </svg>
);

export interface SendButtonProps {
  /** Whether the input field has content */
  hasContent: boolean;
  /** Callback when send button is clicked (only called when hasContent is true and not processing) */
  onSend: () => void;
  /** Callback when cancel button is clicked (only called when processing) */
  onCancel: () => void;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * SendButton - Toggles between send and cancel based on processing state
 *
 * State behavior:
 * - isProcessing=true: Always shows stop icon and is enabled (for cancellation)
 * - isProcessing=false, hasContent=true: Shows send icon, enabled
 * - isProcessing=false, hasContent=false: Shows send icon, disabled
 *
 * Uses LLMStateStore for reliable state detection (same source as LLMStateDisplay).
 */
export const SendButton: React.FC<SendButtonProps> = ({
  hasContent,
  onSend,
  onCancel,
  className = ''
}) => {
  // Subscribe to LLM state - this is the reliable source of truth
  // (same store used by LLMStateDisplay which always works correctly)
  const llmState = useLLMStateStore(state => state.state);
  const isVisible = useLLMStateStore(state => state.isVisible);
  const waitingForUser = useLLMStateStore(state => state.waitingForUser);
  const toolName = useLLMStateStore(state => state.toolName);

  // Subscribe to demo overlay state for spinner
  const showDemoSpinner = useDemoOverlayStore(selectShowSendSpinner);

  // Determine if LLM is processing (should show stop button)
  // Match the logic used by LLMStateDisplay:
  // - GENERATING state (unless waiting for user input)
  // - USING_TOOL state (unless it's run_cell/terminal which show Run/Reject buttons)
  const isProcessing =
    isVisible &&
    ((llmState === LLMDisplayState.GENERATING && !waitingForUser) ||
      (llmState === LLMDisplayState.USING_TOOL &&
        toolName !== 'notebook-run_cell' &&
        toolName !== 'terminal-execute_command'));

  // Determine button state
  const isEnabled = isProcessing || hasContent;
  const showStopIcon = isProcessing;

  // Build class names based on state
  const buttonClasses = [
    showStopIcon ? 'sage-ai-cancel-button' : 'sage-ai-send-button',
    isEnabled ? 'enabled' : 'disabled',
    className
  ]
    .filter(Boolean)
    .join(' ');

  // Handle click - either cancel or send based on state
  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      e.preventDefault();
      e.stopPropagation();

      if (isProcessing) {
        // Always allow cancellation when processing
        onCancel();
      } else if (hasContent) {
        // Only send when there's content and not processing
        onSend();
      }
    },
    [isProcessing, hasContent, onSend, onCancel]
  );

  // Determine icon color based on state
  // Enabled: white/inverse color, Disabled: gray (#7A7A7A)
  const iconColor = isEnabled
    ? 'var(--jp-ui-inverse-font-color0, #ffffff)'
    : '#7A7A7A';

  // Determine which icon to show
  const renderIcon = () => {
    if (showDemoSpinner) {
      return <SpinnerIcon />;
    }
    if (showStopIcon) {
      return <StopIcon />;
    }
    return <SendIcon color={iconColor} />;
  };

  // Determine aria label and title
  const getLabel = () => {
    if (showDemoSpinner) return 'Demo in progress';
    if (showStopIcon) return 'Cancel';
    return 'Send message';
  };

  const getTitle = () => {
    if (showDemoSpinner) return 'Demo in progress';
    if (showStopIcon) return 'Cancel generation';
    return 'Send message';
  };

  return (
    <button
      type="button"
      className={buttonClasses}
      onClick={handleClick}
      disabled={!isEnabled || showDemoSpinner}
      aria-label={getLabel()}
      title={getTitle()}
    >
      {renderIcon()}
    </button>
  );
};

export default SendButton;
