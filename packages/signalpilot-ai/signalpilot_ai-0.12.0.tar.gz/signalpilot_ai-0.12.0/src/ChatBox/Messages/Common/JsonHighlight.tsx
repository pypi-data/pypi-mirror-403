/**
 * JsonHighlight Component
 *
 * Displays JSON with syntax highlighting.
 * Pure React implementation using the existing jsonHighlightUtils.
 */

import React, { memo, useMemo } from 'react';
import { formatJsonWithHighlight } from './jsonHighlightUtils';

// ===============================================================
// TYPES
// ===============================================================

export interface JsonHighlightProps {
  /** JSON data to display (object or string) */
  data: any;
  /** Maximum height before scrolling */
  maxHeight?: number;
  /** Custom class name */
  className?: string;
}

// ===============================================================
// STYLES
// ===============================================================

const preStyles: React.CSSProperties = {
  margin: 0,
  padding: '8px',
  background: 'var(--jp-layout-color2)',
  borderRadius: '3px',
  overflowX: 'auto',
  overflowY: 'auto',
  fontFamily: 'var(--jp-code-font-family)',
  fontSize: '11px',
  lineHeight: 1.4,
  color: 'var(--jp-ui-font-color1)'
};

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * JsonHighlight - Syntax-highlighted JSON display
 */
export const JsonHighlight: React.FC<JsonHighlightProps> = memo(
  ({ data, maxHeight = 300, className }) => {
    // Format the JSON with syntax highlighting
    const highlightedHtml = useMemo(() => {
      const jsonString =
        typeof data === 'string' ? data : JSON.stringify(data, null, 2);
      return formatJsonWithHighlight(jsonString);
    }, [data]);

    return (
      <pre
        className={`sage-ai-mcp-json ${className || ''}`}
        style={{ ...preStyles, maxHeight }}
        dangerouslySetInnerHTML={{ __html: highlightedHtml }}
      />
    );
  }
);

JsonHighlight.displayName = 'JsonHighlight';

export default JsonHighlight;
