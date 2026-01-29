/**
 * UpdateBanner Component (Pure React)
 *
 * Displays an update banner when a new version is available.
 * This is a pure React implementation using Zustand stores.
 */

import React, { useCallback, useState } from 'react';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useAppStore } from '@/stores/appStore'; // ═══════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface UpdateBannerProps {
  /** Current installed version */
  currentVersion?: string;
  /** Latest available version */
  latestVersion?: string;
  /** Whether this is a major version update */
  isMajorUpdate?: boolean;
  /** Callback when update is triggered */
  onUpdate?: () => Promise<void>;
  /** Callback when "Ask Me Later" is clicked */
  onAskLater?: () => void;
  /** Callback when "Decline" is clicked */
  onDecline?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const UpdateBanner: React.FC<UpdateBannerProps> = ({
  currentVersion,
  latestVersion,
  isMajorUpdate = false,
  onUpdate,
  onAskLater,
  onDecline
}) => {
  const { showUpdateBanner, dismissUpdateBanner } = useChatUIStore();
  const isDemoMode = useAppStore(state => state.isDemoMode);
  const [isUpdating, setIsUpdating] = useState(false);

  // Don't render if not visible or in demo mode
  if (!showUpdateBanner || isDemoMode) {
    return null;
  }

  const showActions = !isUpdating && !isMajorUpdate;

  const handleUpdate = useCallback(async () => {
    setIsUpdating(true);
    try {
      await onUpdate?.();
      dismissUpdateBanner();
    } catch (error) {
      console.error('[UpdateBanner] Update failed:', error);
    } finally {
      setIsUpdating(false);
    }
  }, [onUpdate, dismissUpdateBanner]);

  const handleAskLater = useCallback(() => {
    onAskLater?.();
    dismissUpdateBanner();
  }, [onAskLater, dismissUpdateBanner]);

  const handleDecline = useCallback(() => {
    onDecline?.();
    dismissUpdateBanner();
  }, [onDecline, dismissUpdateBanner]);

  return (
    <div className="sage-ai-update-banner">
      <div className="sage-ai-update-banner-content">
        <div className="sage-ai-update-banner-icon">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
              fill="currentColor"
            />
          </svg>
        </div>
        <div className="sage-ai-update-banner-text">
          <div className="sage-ai-update-banner-title">
            {isMajorUpdate
              ? 'SignalPilot is auto-updating to a major version'
              : 'SignalPilot needs to update'}
          </div>
          {currentVersion && latestVersion && (
            <div className="sage-ai-update-banner-version">
              v{currentVersion} → v{latestVersion}
              {isMajorUpdate && ' (Major Version)'}
            </div>
          )}
          {isMajorUpdate && (
            <div className="sage-ai-update-banner-description">
              Major version updates are applied automatically for important
              improvements and security fixes.
            </div>
          )}
        </div>
        {showActions && (
          <div className="sage-ai-update-banner-actions">
            <button
              className="sage-ai-update-banner-button sage-ai-update-banner-button-update"
              onClick={handleUpdate}
              disabled={isUpdating}
            >
              {isUpdating ? 'Updating...' : 'Update'}
            </button>
            <button
              className="sage-ai-update-banner-button sage-ai-update-banner-button-later"
              onClick={handleAskLater}
              disabled={isUpdating}
            >
              Ask Me Later
            </button>
            <button
              className="sage-ai-update-banner-button sage-ai-update-banner-button-decline"
              onClick={handleDecline}
              disabled={isUpdating}
            >
              Decline
            </button>
          </div>
        )}
        {(isUpdating || isMajorUpdate) && (
          <div className="sage-ai-update-banner-progress">
            <div className="sage-ai-update-banner-spinner" />
            <span>{isUpdating ? 'Updating...' : 'Preparing update...'}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UpdateBanner;
