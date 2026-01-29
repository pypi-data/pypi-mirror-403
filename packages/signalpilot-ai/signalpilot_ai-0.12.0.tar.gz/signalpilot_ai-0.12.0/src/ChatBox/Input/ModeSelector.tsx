/**
 * ModeSelector Component
 *
 * A dropdown selector for choosing the chat mode (Agent, Ask, or Hands-on).
 * Uses React Bootstrap Dropdown for simple, reliable dropdown behavior.
 *
 * Features:
 * - Displays current mode with shiny gradient icon and title
 * - Dropdown menu with all available modes
 * - Automatically disables during message processing via Zustand
 *
 * Uses Zustand chatStore for mode state.
 */
import React, { forwardRef, useCallback } from 'react';
import Dropdown from 'react-bootstrap/Dropdown';
import { useChatStore } from '@/stores/chat';
import { ChatMode } from '@/stores/chat/types';

/**
 * Custom toggle component for the dropdown.
 * Required for React Bootstrap to properly handle click events on a custom element.
 */
interface CustomToggleProps {
  children: React.ReactNode;
  onClick: (e: React.MouseEvent<HTMLDivElement>) => void;
  className?: string;
  isDisabled?: boolean;
  mode: string;
}

const CustomToggle = forwardRef<HTMLDivElement, CustomToggleProps>(
  ({ children, onClick, className, isDisabled, mode }, ref) => (
    <div
      ref={ref}
      className={className}
      onClick={e => {
        e.preventDefault();
        if (!isDisabled) {
          onClick(e);
        }
      }}
      style={
        isDisabled
          ? { opacity: 0.5, cursor: 'not-allowed' }
          : { cursor: 'pointer' }
      }
      data-mode={mode}
      title="Select chat mode"
    >
      {children}
    </div>
  )
);

/**
 * Mode configuration with icon, title, and description
 */
interface ModeConfig {
  id: ChatMode;
  title: string;
  description: string;
}

/**
 * Available chat modes
 */
const MODES: ModeConfig[] = [
  {
    id: 'agent',
    title: 'Agent',
    description: 'Prepare datasets. Build models. Test ideas.'
  },
  {
    id: 'ask',
    title: 'Ask',
    description: 'Ask SignalPilot about your notebook or your data.'
  },
  {
    id: 'fast',
    title: 'Hands-on',
    description: 'Manually decide what gets added to the context.'
  }
];

/**
 * Agent Mode Shiny Icon (sparkles with gradient)
 * Used for the display in the selector button
 */
const AgentModeShinyIcon: React.FC = () => (
  <svg
    width="13"
    height="14"
    viewBox="0 0 13 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5.38237 8.89564C5.33401 8.70819 5.2363 8.53712 5.09941 8.40023C4.96252 8.26333 4.79145 8.16563 4.60399 8.11727L1.28087 7.26035C1.22417 7.24426 1.17427 7.21011 1.13874 7.16309C1.10321 7.11607 1.08398 7.05874 1.08398 6.99981C1.08398 6.94087 1.10321 6.88355 1.13874 6.83653C1.17427 6.78951 1.22417 6.75536 1.28087 6.73927L4.60399 5.88181C4.79138 5.8335 4.96241 5.73587 5.09929 5.59908C5.23618 5.46229 5.33392 5.29133 5.38237 5.10398L6.23928 1.78085C6.25521 1.72393 6.28932 1.67379 6.33642 1.63806C6.38351 1.60234 6.44099 1.58301 6.5001 1.58301C6.5592 1.58301 6.61669 1.60234 6.66378 1.63806C6.71087 1.67379 6.74498 1.72393 6.76091 1.78085L7.61728 5.10398C7.66564 5.29143 7.76335 5.4625 7.90024 5.59939C8.03713 5.73628 8.2082 5.83399 8.39566 5.88235L11.7188 6.73873C11.7759 6.75449 11.8263 6.78856 11.8622 6.83573C11.8982 6.88289 11.9176 6.94053 11.9176 6.99981C11.9176 7.05909 11.8982 7.11673 11.8622 7.16389C11.8263 7.21105 11.7759 7.24513 11.7188 7.26089L8.39566 8.11727C8.2082 8.16563 8.03713 8.26333 7.90024 8.40023C7.76335 8.53712 7.66564 8.70819 7.61728 8.89564L6.76037 12.2188C6.74444 12.2757 6.71033 12.3258 6.66324 12.3616C6.61614 12.3973 6.55866 12.4166 6.49955 12.4166C6.44045 12.4166 6.38296 12.3973 6.33587 12.3616C6.28878 12.3258 6.25467 12.2757 6.23874 12.2188L5.38237 8.89564Z"
      fill="url(#paint0_linear_agent_shiny)"
    />
    <path
      d="M10.8335 2.125V4.29167"
      stroke="url(#paint1_linear_agent_shiny)"
      strokeWidth="0.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M11.9167 3.2085H9.75"
      stroke="url(#paint2_linear_agent_shiny)"
      strokeWidth="0.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M2.1665 9.7085V10.7918"
      stroke="url(#paint3_linear_agent_shiny)"
      strokeWidth="0.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M2.70833 10.25H1.625"
      stroke="url(#paint4_linear_agent_shiny)"
      strokeWidth="0.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <defs>
      <linearGradient
        id="paint0_linear_agent_shiny"
        x1="1.08398"
        y1="1.58301"
        x2="11.9176"
        y2="12.4166"
        gradientUnits="userSpaceOnUse"
      >
        <stop stopColor="#FEC163" />
        <stop offset="1" stopColor="#DE4313" />
      </linearGradient>
      <linearGradient
        id="paint1_linear_agent_shiny"
        x1="10.8335"
        y1="2.125"
        x2="12.4823"
        y2="2.88598"
        gradientUnits="userSpaceOnUse"
      >
        <stop stopColor="#FEC163" />
        <stop offset="1" stopColor="#DE4313" />
      </linearGradient>
      <linearGradient
        id="paint2_linear_agent_shiny"
        x1="9.75"
        y1="3.2085"
        x2="10.511"
        y2="4.85728"
        gradientUnits="userSpaceOnUse"
      >
        <stop stopColor="#FEC163" />
        <stop offset="1" stopColor="#DE4313" />
      </linearGradient>
      <linearGradient
        id="paint3_linear_agent_shiny"
        x1="2.1665"
        y1="9.7085"
        x2="3.24638"
        y2="10.7053"
        gradientUnits="userSpaceOnUse"
      >
        <stop stopColor="#FEC163" />
        <stop offset="1" stopColor="#DE4313" />
      </linearGradient>
      <linearGradient
        id="paint4_linear_agent_shiny"
        x1="1.625"
        y1="10.25"
        x2="2.62181"
        y2="11.3299"
        gradientUnits="userSpaceOnUse"
      >
        <stop stopColor="#FEC163" />
        <stop offset="1" stopColor="#DE4313" />
      </linearGradient>
    </defs>
  </svg>
);

/**
 * Agent Mode Icon (sparkles) - for dropdown options
 */
const AgentModeIcon: React.FC = () => (
  <svg
    width="15"
    height="14"
    viewBox="0 0 15 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12.1666 1.74998V4.08331M13.3333 2.91665H11M2.83329 9.91665V11.0833M3.41663 10.5H2.24996M6.29651 9.04165C6.24443 8.83977 6.1392 8.65554 5.99178 8.50812C5.84436 8.3607 5.66013 8.25548 5.45826 8.2034L1.87951 7.28057C1.81845 7.26324 1.76471 7.22646 1.72645 7.17583C1.68818 7.12519 1.66748 7.06345 1.66748 6.99998C1.66748 6.93651 1.68818 6.87478 1.72645 6.82414C1.76471 6.7735 1.81845 6.73673 1.87951 6.7194L5.45826 5.79598C5.66006 5.74395 5.84424 5.63882 5.99166 5.49151C6.13907 5.34419 6.24434 5.16008 6.29651 4.95832L7.21934 1.37957C7.2365 1.31827 7.27323 1.26427 7.32394 1.2258C7.37466 1.18733 7.43656 1.1665 7.50022 1.1665C7.56387 1.1665 7.62577 1.18733 7.67649 1.2258C7.7272 1.26427 7.76394 1.31827 7.78109 1.37957L8.70334 4.95832C8.75542 5.16019 8.86064 5.34442 9.00806 5.49184C9.15548 5.63926 9.33972 5.74449 9.54159 5.79657L13.1203 6.71882C13.1819 6.73579 13.2362 6.77249 13.2748 6.82328C13.3135 6.87407 13.3345 6.93614 13.3345 6.99998C13.3345 7.06382 13.3135 7.1259 13.2748 7.17669C13.2362 7.22748 13.1819 7.26417 13.1203 7.28115L9.54159 8.2034C9.33972 8.25548 9.15548 8.3607 9.00806 8.50812C8.86064 8.65554 8.75542 8.83977 8.70334 9.04165L7.78051 12.6204C7.76335 12.6817 7.72662 12.7357 7.6759 12.7742C7.62519 12.8126 7.56329 12.8335 7.49963 12.8335C7.43598 12.8335 7.37407 12.8126 7.32336 12.7742C7.27265 12.7357 7.23591 12.6817 7.21876 12.6204L6.29651 9.04165Z"
      stroke="var(--jp-ui-font-color1)"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Ask Mode Icon (question bubble)
 */
const AskModeIcon: React.FC = () => (
  <svg
    width="15"
    height="14"
    viewBox="0 0 15 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5.80232 5.25021C5.93946 4.86035 6.21016 4.53161 6.56646 4.3222C6.92276 4.1128 7.34167 4.03626 7.749 4.10613C8.15633 4.17599 8.52579 4.38777 8.79195 4.70393C9.0581 5.0201 9.20377 5.42026 9.20315 5.83354C9.20315 7.00021 7.45315 7.58354 7.45315 7.58354M7.49984 9.91683H7.50567M5.10817 11.6669C6.22151 12.238 7.50222 12.3927 8.71952 12.1031C9.93682 11.8135 11.0107 11.0986 11.7475 10.0873C12.4844 9.076 12.8358 7.83477 12.7385 6.58728C12.6412 5.3398 12.1015 4.16809 11.2167 3.2833C10.3319 2.39852 9.16023 1.85884 7.91274 1.76152C6.66526 1.6642 5.42403 2.01563 4.41273 2.7525C3.40144 3.48937 2.68657 4.5632 2.39697 5.78051C2.10736 6.99781 2.26205 8.27852 2.83317 9.39186L1.6665 12.8335L5.10817 11.6669Z"
      stroke="var(--jp-ui-font-color1)"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Hands-on Mode Icon (tree/branches)
 */
const HandsOnModeIcon: React.FC = () => (
  <svg
    width="15"
    height="14"
    viewBox="0 0 15 14"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M7.49982 2.91678C7.50051 2.68346 7.45453 2.45236 7.3646 2.23708C7.27467 2.02179 7.14259 1.82666 6.97614 1.66316C6.80969 1.49967 6.61223 1.3711 6.39537 1.28504C6.17851 1.19897 5.94662 1.15714 5.71336 1.162C5.48009 1.16686 5.25015 1.21832 5.03707 1.31335C4.82398 1.40838 4.63205 1.54506 4.47255 1.71535C4.31306 1.88564 4.18923 2.0861 4.10835 2.30495C4.02747 2.5238 3.99116 2.75661 4.00157 2.98969M7.49982 2.91678V10.5001M7.49982 2.91678C7.49913 2.68346 7.54507 2.45236 7.635 2.23708C7.72494 2.02179 7.85701 1.82666 8.02346 1.66316C8.18991 1.49967 8.38737 1.3711 8.60423 1.28504C8.8211 1.19897 9.05298 1.15714 9.28624 1.162C9.51951 1.16686 9.74945 1.21832 9.96254 1.31335C10.1756 1.40838 10.3676 1.54506 10.527 1.71535C10.6865 1.88564 10.8104 2.0861 10.8913 2.30495C10.9721 2.5238 11.0084 2.75661 10.998 2.98969C11.3409 3.07786 11.6592 3.24289 11.9289 3.47229C12.1986 3.7017 12.4125 3.98945 12.5545 4.31377C12.6964 4.63809 12.7628 4.99047 12.7484 5.34421C12.734 5.69795 12.6393 6.04379 12.4715 6.35553M4.00157 2.98969C3.65869 3.07786 3.34036 3.24289 3.0707 3.47229C2.80105 3.7017 2.58713 3.98945 2.44514 4.31377C2.30316 4.63809 2.23685 4.99047 2.25121 5.34421C2.26558 5.69795 2.36026 6.04379 2.52807 6.35553M4.00157 2.98969C4.0131 3.27187 4.09268 3.54704 4.23365 3.79175M2.52807 6.35553C2.23301 6.59524 2.00098 6.90341 1.85218 7.25324C1.70338 7.60307 1.64231 7.98396 1.67428 8.36277C1.70625 8.74158 1.8303 9.10685 2.03562 9.42679C2.24095 9.74673 2.52134 10.0117 2.8524 10.1985M2.52807 6.35553C2.63478 6.26861 2.74897 6.19187 2.86931 6.12508M2.8524 10.1985C2.81152 10.5148 2.83592 10.8362 2.92409 11.1427C3.01226 11.4492 3.16233 11.7343 3.36503 11.9806C3.56773 12.2268 3.81876 12.4289 4.10261 12.5743C4.38647 12.7197 4.69712 12.8054 5.01539 12.8261C5.33366 12.8467 5.65278 12.8019 5.95305 12.6944C6.25331 12.5869 6.52835 12.4189 6.76118 12.201C6.994 11.983 7.17967 11.7196 7.30671 11.4271C7.43376 11.1345 7.49948 10.819 7.49982 10.5001M2.8524 10.1985C3.20256 10.396 3.59774 10.5002 3.99975 10.5M7.49982 10.5001C7.50016 10.819 7.56585 11.1345 7.69289 11.4271C7.81993 11.7196 8.0056 11.983 8.23842 12.201C8.47125 12.4189 8.74629 12.5869 9.04656 12.6944C9.34683 12.8019 9.66595 12.8467 9.98421 12.8261C10.3025 12.8054 10.6131 12.7197 10.897 12.5743C11.1808 12.4289 11.4319 12.2268 11.6346 11.9806C11.8373 11.7343 11.9873 11.4492 12.0755 11.1427C12.1637 10.8362 12.1881 10.5148 12.1472 10.1985M12.4715 6.35553C12.7666 6.59524 12.9986 6.90341 13.1474 7.25324C13.2962 7.60307 13.3573 7.98396 13.3253 8.36277C13.2934 8.74158 13.1693 9.10685 12.964 9.42679C12.7587 9.74673 12.4783 10.0117 12.1472 10.1985M12.4715 6.35553C12.3648 6.26861 12.2506 6.19187 12.1303 6.12508M12.1472 10.1985C11.797 10.396 11.4018 10.5002 10.9998 10.5M9.24978 7.58341C8.76004 7.41113 8.33238 7.0975 8.02088 6.68217C7.70939 6.26684 7.52804 5.76847 7.49978 5.25008C7.47151 5.76847 7.29017 6.26684 6.97867 6.68217C6.66717 7.0975 6.23952 7.41113 5.74978 7.58341M10.7659 3.79175C10.9071 3.54709 10.987 3.27189 10.9987 2.98966"
      stroke="var(--jp-ui-font-color1)"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Dropdown Arrow Icon
 */
const ArrowIcon: React.FC = () => (
  <svg
    width="13"
    height="12"
    viewBox="0 0 13 12"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M9.5 7.5L6.5 4.5L3.5 7.5"
      stroke="var(--jp-ui-font-color2, #ADADAD)"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Get the icon component for a mode (used in dropdown options)
 */
function getModeIcon(mode: ChatMode): React.FC {
  switch (mode) {
    case 'agent':
      return AgentModeIcon;
    case 'ask':
      return AskModeIcon;
    case 'fast':
      return HandsOnModeIcon;
    default:
      return AgentModeIcon;
  }
}

export interface ModeSelectorProps {
  /** Callback when mode is selected */
  onModeChange?: (mode: ChatMode) => void;
  /** Whether the selector is disabled (e.g., during processing) */
  disabled?: boolean;
  /** Optional className for additional styling */
  className?: string;
}

/**
 * ModeSelector - Dropdown for selecting chat mode
 *
 * Uses React Bootstrap Dropdown for reliable dropdown behavior.
 * Automatically disables when isProcessing is true from the store.
 */
export const ModeSelector: React.FC<ModeSelectorProps> = ({
  onModeChange,
  disabled = false,
  className = ''
}) => {
  // Get current mode and processing state from store
  const mode = useChatStore(state => state.mode);
  const setMode = useChatStore(state => state.setMode);
  const isProcessing = useChatStore(state => state.isProcessing);

  // Disabled if explicitly disabled OR if processing
  const isDisabled = disabled || isProcessing;

  // Get current mode config
  const currentMode = MODES.find(m => m.id === mode) || MODES[0];

  // Handle mode selection
  const handleSelect = useCallback(
    (eventKey: string | null) => {
      if (eventKey) {
        const newMode = eventKey as ChatMode;
        setMode(newMode);
        onModeChange?.(newMode);
      }
    },
    [setMode, onModeChange]
  );

  return (
    <Dropdown
      onSelect={handleSelect}
      drop="up"
      className={`sage-ai-mode-selector-dropdown ${className}`}
    >
      <Dropdown.Toggle
        as={CustomToggle}
        className={`sage-ai-mode-selector ${isDisabled ? 'disabled' : ''}`}
        isDisabled={isDisabled}
        mode={mode}
      >
        <div className="sage-ai-mode-display">
          <div className="sage-ai-mode-option-icon">
            <AgentModeShinyIcon />
          </div>
          <div className="sage-ai-mode-option-text">{currentMode.title}</div>
        </div>
        <div className="sage-ai-mode-selector-arrow">
          <ArrowIcon />
        </div>
      </Dropdown.Toggle>

      <Dropdown.Menu className="sage-ai-mode-dropdown">
        {MODES.map(modeConfig => {
          const ModeIcon = getModeIcon(modeConfig.id);
          return (
            <Dropdown.Item
              key={modeConfig.id}
              eventKey={modeConfig.id}
              className="sage-ai-mode-option"
              active={modeConfig.id === mode}
            >
              <div className="sage-ai-mode-option-icon">
                <ModeIcon />
              </div>
              <div className="sage-ai-mode-option-text">
                <div className="sage-ai-mode-option-title">
                  {modeConfig.title}
                </div>
                <div className="sage-ai-mode-option-description">
                  {modeConfig.description}
                </div>
              </div>
            </Dropdown.Item>
          );
        })}
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default ModeSelector;
