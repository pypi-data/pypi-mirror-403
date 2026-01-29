/**
 * DemoOverlay Component
 *
 * A reusable overlay component that renders when demo mode is active.
 * Components use this to prevent user interaction during demo playback.
 */

import React from 'react';
import {
  useDemoOverlayStore,
  selectIsOverlayActive
} from '@/stores/demoOverlayStore';

export interface DemoOverlayProps {
  /** Optional z-index for the overlay */
  zIndex?: number;
  /** Optional additional class name */
  className?: string;
}

/**
 * DemoOverlay - Renders a grey overlay when demo mode is active
 *
 * Usage:
 * ```tsx
 * <div className="my-component" style={{ position: 'relative' }}>
 *   <DemoOverlay />
 *   {/* component content *\/}
 * </div>
 * ```
 */
export const DemoOverlay: React.FC<DemoOverlayProps> = ({
  zIndex = 9999,
  className = ''
}) => {
  const isActive = useDemoOverlayStore(selectIsOverlayActive);

  if (!isActive) {
    return null;
  }

  return (
    <div
      className={`sage-demo-overlay ${className}`}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(128, 128, 128, 0.3)',
        zIndex,
        cursor: 'not-allowed',
        pointerEvents: 'auto'
      }}
      title="Disabled on replay"
    />
  );
};

export default DemoOverlay;
