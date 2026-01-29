/**
 * SubscriptionCard Component
 *
 * Displays a subscription prompt card when the user's subscription is invalid/expired.
 * Includes a star icon, instructional text, and a button to view subscription plans.
 *
 * This card clears the chat container and replaces it with the subscription prompt.
 *
 * @example
 * ```tsx
 * <SubscriptionCard onSubscribe={() => window.open(subscriptionUrl, '_blank')} />
 * ```
 */
import React, { useCallback } from 'react'; // Star/sparkle icon SVG component

// Star/sparkle icon SVG component
const StarIcon: React.FC = () => (
  <svg
    width="32"
    height="32"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 2L13.09 8.26L22 9L13.09 9.74L12 16L10.91 9.74L2 9L10.91 8.26L12 2Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 21L12 17L16 21"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// Small star icon for button
const StarIconSmall: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 2L13.09 8.26L22 9L13.09 9.74L12 16L10.91 9.74L2 9L10.91 8.26L12 2Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M8 21L12 17L16 21"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export interface SubscriptionCardProps {
  /** Callback when subscribe button is clicked */
  onSubscribe: () => void;
}

/**
 * SubscriptionCard - Prompts user to subscribe
 *
 * Reuses the same CSS classes as AuthenticationCard:
 * - .sage-ai-auth-card: Card container
 * - .sage-ai-auth-card-content: Inner content wrapper
 * - .sage-ai-auth-icon: Icon container
 * - .sage-ai-auth-header: Title and description
 * - .sage-ai-auth-login-button: Primary action button
 */
export const SubscriptionCard: React.FC<SubscriptionCardProps> = ({
  onSubscribe
}) => {
  const handleSubscribe = useCallback(() => {
    onSubscribe();
  }, [onSubscribe]);

  return (
    <div className="sage-ai-auth-card">
      <div className="sage-ai-auth-card-content">
        {/* Star icon */}
        <div className="sage-ai-auth-icon">
          <StarIcon />
        </div>

        {/* Header text */}
        <div className="sage-ai-auth-header">
          <h3>Subscription Required</h3>
          <p>
            You need an active subscription to continue using SignalPilot AI.
            Choose a plan that works for you and unlock the full potential of
            AI-powered coding assistance.
          </p>
        </div>

        {/* Subscribe button */}
        <button
          className="sage-ai-auth-login-button sage-ai-button sage-ai-button-primary"
          onClick={handleSubscribe}
        >
          <StarIconSmall />
          View Subscription Plans
        </button>
      </div>
    </div>
  );
};

export default SubscriptionCard;
