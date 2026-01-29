/**
 * ToolSearchDisplay Component
 *
 * Displays tool search results in a collapsible panel.
 * Shows the search input and list of found tool names.
 * Used for server tools like tool_search_tool_regex and tool_search_tool_bm25.
 */

import React, { memo, useMemo } from 'react';
import { CollapsibleSection } from './CollapsibleSection';
import { JsonHighlight } from './JsonHighlight';

// ===============================================================
// TYPES
// ===============================================================

export interface ToolSearchDisplayProps {
  /** Header content (icon, tool name, etc.) */
  header: React.ReactNode;
  /** Tool call input data */
  toolCallData: any;
  /** Tool result */
  result: any;
  /** Custom class name */
  className?: string;
}

// ===============================================================
// UTILITY FUNCTIONS
// ===============================================================

/**
 * Extract input data from tool search call structure
 */
function extractToolSearchInput(toolCallData: any): any {
  try {
    if (toolCallData?.assistant?.content?.[0]?.input !== undefined) {
      return toolCallData.assistant.content[0].input;
    }
    if (toolCallData?.input !== undefined) {
      return toolCallData.input;
    }
  } catch {
    // Fall through
  }
  return toolCallData;
}

/**
 * Extract tool names from tool search result
 */
function extractToolSearchOutput(result: any): string[] {
  try {
    let parsed = result;
    if (typeof result === 'string') {
      try {
        parsed = JSON.parse(result);
      } catch {
        return [result];
      }
    }

    // Handle error responses
    if (parsed?.type === 'error' || parsed?.error) {
      const errorMsg =
        parsed?.error?.message ||
        parsed?.message ||
        parsed?.error ||
        'Unknown error';
      return [`Error: ${errorMsg}`];
    }

    // Handle nested content structure (API might return { content: { tool_references: [...] } })
    if (
      parsed?.content?.tool_references &&
      Array.isArray(parsed.content.tool_references)
    ) {
      return parsed.content.tool_references.map(
        (ref: any) => ref.tool_name || ref.name || String(ref)
      );
    }

    // Handle tool_references array
    if (parsed?.tool_references && Array.isArray(parsed.tool_references)) {
      return parsed.tool_references.map(
        (ref: any) => ref.tool_name || ref.name || String(ref)
      );
    }

    // Handle type-specific result
    if (
      parsed?.type === 'tool_search_tool_search_result' &&
      parsed?.tool_references
    ) {
      return parsed.tool_references.map(
        (ref: any) => ref.tool_name || ref.name || String(ref)
      );
    }

    // Handle direct array of tool names
    if (Array.isArray(parsed)) {
      return parsed.map((item: any) =>
        typeof item === 'string'
          ? item
          : item?.tool_name || item?.name || String(item)
      );
    }

    return [String(parsed)];
  } catch {
    return [String(result)];
  }
}

// ===============================================================
// STYLES
// ===============================================================

const styles = {
  inputSection: {
    background: 'var(--jp-layout-color1)',
    borderRadius: '3px 3px 0 0',
    padding: '8px'
  } as React.CSSProperties,
  outputSection: {
    background: 'var(--jp-layout-color1)',
    borderRadius: '0 0 3px 3px',
    padding: '8px'
  } as React.CSSProperties,
  label: {
    fontWeight: 400,
    fontSize: '11px',
    color: 'var(--jp-ui-font-color2)',
    marginBottom: '8px'
  } as React.CSSProperties,
  toolList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  } as React.CSSProperties,
  toolItem: {
    padding: '4px 8px',
    background: 'var(--jp-layout-color2)',
    borderRadius: '3px',
    fontFamily: 'var(--jp-code-font-family)',
    fontSize: '11px',
    color: 'var(--jp-ui-font-color1)'
  } as React.CSSProperties,
  emptyMessage: {
    color: 'var(--jp-ui-font-color2)',
    fontStyle: 'italic',
    fontSize: '11px'
  } as React.CSSProperties
};

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * ToolSearchDisplay - Collapsible tool search input/output display
 */
export const ToolSearchDisplay: React.FC<ToolSearchDisplayProps> = memo(
  ({ header, toolCallData, result, className }) => {
    // Extract and format data
    const inputData = useMemo(
      () => extractToolSearchInput(toolCallData),
      [toolCallData]
    );
    const toolNames = useMemo(() => extractToolSearchOutput(result), [result]);

    return (
      <CollapsibleSection
        header={header}
        className={`sage-ai-tool-search ${className || ''}`}
      >
        {/* Input Section */}
        <div className="sage-ai-mcp-section" style={styles.inputSection}>
          <div style={styles.label}>Search Query</div>
          <JsonHighlight data={inputData} />
        </div>

        {/* Output Section - List of found tools */}
        <div className="sage-ai-mcp-section" style={styles.outputSection}>
          <div style={styles.label}>Found Tools ({toolNames.length})</div>
          {toolNames.length > 0 ? (
            <div style={styles.toolList}>
              {toolNames.map((name, index) => (
                <div key={index} style={styles.toolItem}>
                  {name}
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.emptyMessage}>No tools found</div>
          )}
        </div>
      </CollapsibleSection>
    );
  }
);

ToolSearchDisplay.displayName = 'ToolSearchDisplay';

export default ToolSearchDisplay;
