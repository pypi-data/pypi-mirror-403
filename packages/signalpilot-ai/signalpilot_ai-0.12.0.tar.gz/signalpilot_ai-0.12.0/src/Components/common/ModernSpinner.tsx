/**
 * ModernSpinner
 *
 * A beautiful, modern loading spinner component with gradient animations.
 * Designed to replace the thinking state for chat message loading and
 * provide visual feedback during initialization.
 *
 * Features:
 * - Multiple sizes (xs, sm, md, lg, xl)
 * - Gradient color animation
 * - Optional pulsing ring effect
 * - Optional loading text with animated dots
 * - Works on both light and dark backgrounds
 * - Accessible with proper ARIA attributes
 */

import * as React from 'react';

export type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type SpinnerVariant = 'default' | 'subtle' | 'primary';

interface IModernSpinnerProps {
  /** Size of the spinner */
  size?: SpinnerSize;
  /** Visual variant */
  variant?: SpinnerVariant;
  /** Optional loading text to display below spinner */
  text?: string;
  /** Show animated dots after text */
  showDots?: boolean;
  /** Show pulsing ring effect */
  showPulseRing?: boolean;
  /** Custom className */
  className?: string;
  /** Center the spinner in its container */
  centered?: boolean;
  /** Inline display (for use in text) */
  inline?: boolean;
}

// Size configurations
const sizeConfig: Record<SpinnerSize, { width: number; stroke: number }> = {
  xs: { width: 16, stroke: 2 },
  sm: { width: 24, stroke: 2.5 },
  md: { width: 36, stroke: 3 },
  lg: { width: 48, stroke: 3.5 },
  xl: { width: 64, stroke: 4 }
};

// Variant colors
const variantColors: Record<
  SpinnerVariant,
  { primary: string; secondary: string }
> = {
  default: { primary: '#4a90e2', secondary: '#7eb3ff' },
  subtle: {
    primary: 'var(--jp-ui-font-color2, #888)',
    secondary: 'var(--jp-ui-font-color3, #aaa)'
  },
  primary: { primary: '#3b82f6', secondary: '#60a5fa' }
};

export const ModernSpinner: React.FC<IModernSpinnerProps> = ({
  size = 'md',
  variant = 'default',
  text,
  showDots = false,
  showPulseRing = false,
  className = '',
  centered = false,
  inline = false
}) => {
  const { width, stroke } = sizeConfig[size];
  const colors = variantColors[variant];
  const radius = (width - stroke) / 2;
  const circumference = radius * 2 * Math.PI;
  const gradientId = React.useId();

  const spinnerElement = (
    <div
      className={`sage-modern-spinner sage-modern-spinner--${size} ${className}`}
      style={{
        display: inline ? 'inline-flex' : 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: text ? '12px' : '0',
        ...(centered && !inline ? { margin: '0 auto' } : {})
      }}
      role="status"
      aria-label={text || 'Loading'}
    >
      {/* Spinner container */}
      <div
        className="sage-modern-spinner__container"
        style={{
          position: 'relative',
          width: `${width}px`,
          height: `${width}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {/* Pulse ring (optional) */}
        {showPulseRing && (
          <div
            className="sage-modern-spinner__pulse-ring"
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              width: `${width + 16}px`,
              height: `${width + 16}px`,
              borderRadius: '50%',
              border: `2px solid ${colors.primary}`,
              opacity: 0.3,
              transform: 'translate(-50%, -50%)',
              animation:
                'sage-spinner-pulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite'
            }}
          />
        )}

        {/* SVG Spinner */}
        <svg
          className="sage-modern-spinner__svg"
          width={width}
          height={width}
          viewBox={`0 0 ${width} ${width}`}
          style={{
            animation:
              'sage-spinner-rotate 1.5s cubic-bezier(0.4, 0, 0.2, 1) infinite',
            filter: `drop-shadow(0 0 ${width / 8}px ${colors.primary}40)`
          }}
        >
          {/* Gradient definition */}
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={colors.primary} />
              <stop offset="50%" stopColor={colors.secondary} />
              <stop offset="100%" stopColor={colors.primary} />
            </linearGradient>
          </defs>

          {/* Background track */}
          <circle
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={stroke}
            opacity={0.1}
          />

          {/* Animated arc */}
          <circle
            className="sage-modern-spinner__arc"
            cx={width / 2}
            cy={width / 2}
            r={radius}
            fill="none"
            stroke={`url(#${gradientId})`}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.75}
            style={{
              animation: 'sage-spinner-dash 1.5s ease-in-out infinite',
              transformOrigin: 'center'
            }}
          />
        </svg>
      </div>

      {/* Loading text (optional) */}
      {text && (
        <div
          className="sage-modern-spinner__text"
          style={{
            fontSize: size === 'xs' || size === 'sm' ? '12px' : '14px',
            color: 'var(--jp-ui-font-color1, #333)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'baseline',
            gap: '2px'
          }}
        >
          <span>{text}</span>
          {showDots && (
            <span className="sage-modern-spinner__dots">
              <span
                style={{
                  animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
                  animationDelay: '0s'
                }}
              >
                .
              </span>
              <span
                style={{
                  animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
                  animationDelay: '0.15s'
                }}
              >
                .
              </span>
              <span
                style={{
                  animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
                  animationDelay: '0.3s'
                }}
              >
                .
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  );

  return spinnerElement;
};

/**
 * Inline spinner for use within text or buttons
 */
export const InlineSpinner: React.FC<{
  size?: SpinnerSize;
  className?: string;
}> = ({ size = 'xs', className = '' }) => {
  return (
    <ModernSpinner size={size} variant="subtle" inline className={className} />
  );
};

/**
 * Full-screen loading overlay with spinner
 */
interface ILoadingOverlayProps {
  text?: string;
  visible?: boolean;
  transparent?: boolean;
}

export const LoadingOverlay: React.FC<ILoadingOverlayProps> = ({
  text = 'Loading',
  visible = true,
  transparent = false
}) => {
  if (!visible) return null;

  return (
    <div
      className="sage-modern-loading-overlay"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: transparent
          ? 'transparent'
          : 'var(--jp-layout-color1, rgba(255, 255, 255, 0.9))',
        backdropFilter: transparent ? 'none' : 'blur(2px)',
        zIndex: 100
      }}
    >
      <ModernSpinner size="lg" text={text} showDots showPulseRing centered />
    </div>
  );
};

/**
 * Chat message loading indicator (replaces thinking state)
 */
interface IChatLoadingIndicatorProps {
  message?: string;
}

export const ChatLoadingIndicator: React.FC<IChatLoadingIndicatorProps> = ({
  message = 'Thinking'
}) => {
  return (
    <div
      className="sage-chat-loading-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '16px',
        backgroundColor: 'var(--jp-layout-color2, #f5f5f5)',
        borderRadius: '12px',
        maxWidth: 'fit-content'
      }}
    >
      <ModernSpinner size="sm" variant="primary" />
      <span
        className="sage-chat-loading-indicator__text"
        style={{
          fontSize: '14px',
          color: 'var(--jp-ui-font-color1, #333)',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'baseline'
        }}
      >
        {message}
        <span
          className="sage-modern-spinner__dots"
          style={{ marginLeft: '2px' }}
        >
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0s'
            }}
          >
            .
          </span>
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0.15s'
            }}
          >
            .
          </span>
          <span
            style={{
              animation: 'sage-spinner-dot 1.4s ease-in-out infinite',
              animationDelay: '0.3s'
            }}
          >
            .
          </span>
        </span>
      </span>
    </div>
  );
};

export default ModernSpinner;
