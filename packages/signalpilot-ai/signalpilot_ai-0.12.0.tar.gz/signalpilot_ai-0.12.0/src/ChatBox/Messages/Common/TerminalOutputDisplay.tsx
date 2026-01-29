/**
 * TerminalOutputDisplay Component
 *
 * Displays terminal command output (stdout/stderr) in a collapsible panel.
 * Pure React implementation - no DOM manipulation.
 */

import React, { memo, useCallback, useMemo, useState } from 'react';

// ===============================================================
// TYPES
// ===============================================================

export interface TerminalOutputDisplayProps {
  /** Header content (icon, command name, etc.) */
  header: React.ReactNode;
  /** Terminal result with stdout/stderr */
  result: any;
  /** Custom class name */
  className?: string;
}

interface ParsedOutput {
  stdout: string;
  stderr: string;
}

// ===============================================================
// STYLES
// ===============================================================

const styles = {
  container: {
    display: 'block',
    cursor: 'pointer'
  } as React.CSSProperties,
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '0 8px'
  } as React.CSSProperties,
  content: {
    margin: '4px 8px 0 8px',
    padding: '8px',
    background: 'var(--jp-layout-color1)',
    borderRadius: '3px',
    overflowX: 'auto',
    maxHeight: '300px',
    overflowY: 'auto',
    fontFamily: 'var(--jp-code-font-family)',
    fontSize: '11px',
    lineHeight: 1.4,
    borderLeft: '2px solid var(--jp-border-color2)',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word'
  } as React.CSSProperties,
  stdout: {
    color: 'var(--jp-ui-font-color1)'
  } as React.CSSProperties,
  stderr: {
    color: 'var(--jp-error-color0)'
  } as React.CSSProperties
};

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * TerminalOutputDisplay - Collapsible terminal output display
 */
export const TerminalOutputDisplay: React.FC<TerminalOutputDisplayProps> = memo(
  ({ header, result, className }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    // Parse the result
    const parsed = useMemo((): ParsedOutput => {
      try {
        const data = typeof result === 'string' ? JSON.parse(result) : result;
        return {
          stdout: data.stdout || '',
          stderr: data.stderr || ''
        };
      } catch {
        return { stdout: '', stderr: '' };
      }
    }, [result]);

    // Don't render if no output
    if (!parsed.stdout && !parsed.stderr) {
      return null;
    }

    const handleToggle = useCallback((e: React.MouseEvent) => {
      e.stopPropagation();
      setIsExpanded(prev => !prev);
    }, []);

    return (
      <div
        className={`sage-ai-terminal-output clickable ${className || ''}`}
        style={styles.container}
        onClick={handleToggle}
      >
        {/* Header */}
        <div style={styles.header}>{header}</div>

        {/* Content (collapsible) */}
        {isExpanded && (
          <pre
            className="sage-ai-terminal-output-content"
            style={styles.content}
          >
            {parsed.stdout && (
              <span style={styles.stdout}>{parsed.stdout}</span>
            )}
            {parsed.stdout && parsed.stderr && '\n'}
            {parsed.stderr && (
              <span style={styles.stderr}>{parsed.stderr}</span>
            )}
          </pre>
        )}
      </div>
    );
  }
);

TerminalOutputDisplay.displayName = 'TerminalOutputDisplay';

export default TerminalOutputDisplay;
