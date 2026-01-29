/**
 * CollapsibleSection Component
 *
 * A reusable collapsible section with header and expandable content.
 * Pure React implementation - no DOM manipulation.
 */

import React, { memo, ReactNode, useCallback, useState } from 'react';

// ===============================================================
// ICONS
// ===============================================================

const ChevronIcon: React.FC<{ isExpanded: boolean }> = ({ isExpanded }) => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    style={{
      transition: 'transform 0.2s ease',
      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
      color: 'var(--jp-ui-font-color2)'
    }}
  >
    <path
      d="M6 9L12 15L18 9"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// ===============================================================
// TYPES
// ===============================================================

export interface CollapsibleSectionProps {
  /** Content to display in the always-visible header */
  header: ReactNode;
  /** Content to show when expanded */
  children: ReactNode;
  /** Initial expanded state */
  defaultExpanded?: boolean;
  /** Callback when toggled */
  onToggle?: (isExpanded: boolean) => void;
  /** Custom class name */
  className?: string;
  /** Whether to show the expand arrow */
  showArrow?: boolean;
}

// ===============================================================
// STYLES
// ===============================================================

const styles = {
  container: {
    display: 'block'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '10px',
    padding: '0 8px',
    cursor: 'pointer'
  } as React.CSSProperties,
  headerContent: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    flex: 1
  } as React.CSSProperties,
  content: {
    margin: '8px 8px 4px 8px',
    display: 'flex',
    flexDirection: 'column' as const
  } as React.CSSProperties,
  contentHidden: {
    display: 'none'
  }
};

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * CollapsibleSection - Expandable/collapsible content section
 */
export const CollapsibleSection: React.FC<CollapsibleSectionProps> = memo(
  ({
    header,
    children,
    defaultExpanded = false,
    onToggle,
    className,
    showArrow = true
  }) => {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    const handleToggle = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        const newState = !isExpanded;
        setIsExpanded(newState);
        onToggle?.(newState);
      },
      [isExpanded, onToggle]
    );

    return (
      <div className={className} style={styles.container}>
        {/* Header (clickable) */}
        <div style={styles.header} onClick={handleToggle}>
          <div style={styles.headerContent}>{header}</div>
          {showArrow && <ChevronIcon isExpanded={isExpanded} />}
        </div>

        {/* Collapsible content */}
        <div style={isExpanded ? styles.content : styles.contentHidden}>
          {children}
        </div>
      </div>
    );
  }
);

CollapsibleSection.displayName = 'CollapsibleSection';

export default CollapsibleSection;
