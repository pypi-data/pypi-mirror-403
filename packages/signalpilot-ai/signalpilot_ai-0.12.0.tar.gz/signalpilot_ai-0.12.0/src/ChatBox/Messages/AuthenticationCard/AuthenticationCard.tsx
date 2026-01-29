/**
 * AuthenticationCard Component
 *
 * Displays a login prompt card when the user is not authenticated.
 * Includes a shield icon, instructional text, and a login button.
 *
 * This card clears the chat container and replaces it with the auth prompt.
 *
 * @example
 * ```tsx
 * <AuthenticationCard onLogin={() => JupyterAuthService.openLoginPage()} />
 * ```
 */
import React, { useCallback } from 'react'; // Shield icon SVG component

// Shield icon SVG component
const ShieldIcon: React.FC = () => (
  <svg
    width="32"
    height="32"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1Z"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M9 12L11 14L15 10"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// Login arrow icon SVG component
const LoginIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M15 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H15"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M10 17L15 12L10 7"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M15 12H3"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export interface AuthenticationCardProps {
  /** Callback when login button is clicked */
  onLogin: () => void;
}

/**
 * AuthenticationCard - Prompts user to log in
 *
 * Styling is handled by CSS classes:
 * - .sage-ai-auth-card: Card container
 * - .sage-ai-auth-card-content: Inner content wrapper
 * - .sage-ai-auth-icon: Icon container
 * - .sage-ai-auth-header: Title and description
 * - .sage-ai-auth-login-button: Primary action button
 */
export const AuthenticationCard: React.FC<AuthenticationCardProps> = ({
  onLogin
}) => {
  const handleLogin = useCallback(() => {
    onLogin();
  }, [onLogin]);

  return (
    <div className="sage-ai-auth-card">
      <div className="sage-ai-auth-card-content">
        {/* Shield icon */}
        <div className="sage-ai-auth-icon">
          <ShieldIcon />
        </div>

        {/* Header text */}
        <div className="sage-ai-auth-header">
          <h3>Authentication Required</h3>
          <p>Please log in to start chatting with SignalPilot AI</p>
        </div>

        {/* Login button */}
        <button
          className="sage-ai-auth-login-button sage-ai-button sage-ai-button-primary"
          onClick={handleLogin}
        >
          <LoginIcon />
          Log In
        </button>
      </div>
    </div>
  );
};

export default AuthenticationCard;
