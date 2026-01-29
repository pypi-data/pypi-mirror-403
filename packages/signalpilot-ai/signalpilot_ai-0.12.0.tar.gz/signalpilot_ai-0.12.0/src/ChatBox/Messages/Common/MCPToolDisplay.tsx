/**
 * MCPToolDisplay Component
 *
 * Displays MCP tool input/output in a collapsible panel.
 * Pure React implementation - no DOM manipulation.
 */

import React, { memo, useMemo } from 'react';
import { CollapsibleSection } from './CollapsibleSection';
import { JsonHighlight } from './JsonHighlight';

// ===============================================================
// TYPES
// ===============================================================

export interface MCPToolDisplayProps {
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
 * Extract input data from MCP tool call structure
 */
function extractMCPInput(toolCallData: any): any {
  try {
    if (toolCallData?.assistant?.content?.[0]?.input !== undefined) {
      return toolCallData.assistant.content[0].input;
    }
  } catch {
    // Fall through
  }
  return toolCallData;
}

/**
 * Extract output data from MCP tool result structure
 */
function extractMCPOutput(result: any): any {
  try {
    let parsed = result;
    if (typeof result === 'string') {
      try {
        parsed = JSON.parse(result);
      } catch {
        return result;
      }
    }

    if (parsed?.content?.text !== undefined) {
      return parsed.content.text;
    }

    if (Array.isArray(parsed?.content)) {
      if (
        parsed.content.length === 1 &&
        parsed.content[0]?.text !== undefined
      ) {
        return parsed.content[0].text;
      }
      return parsed.content;
    }

    if (parsed?.content !== undefined) {
      return parsed.content;
    }

    return parsed;
  } catch {
    return result;
  }
}

// ===============================================================
// STYLES
// ===============================================================

const styles = {
  section: {
    background: 'var(--jp-layout-color1)',
    padding: '8px'
  } as React.CSSProperties,
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
  } as React.CSSProperties
};

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * MCPToolDisplay - Collapsible MCP tool input/output display
 */
export const MCPToolDisplay: React.FC<MCPToolDisplayProps> = memo(
  ({ header, toolCallData, result, className }) => {
    // Extract and format data
    const inputData = useMemo(
      () => extractMCPInput(toolCallData),
      [toolCallData]
    );
    const outputData = useMemo(() => extractMCPOutput(result), [result]);

    return (
      <CollapsibleSection
        header={header}
        className={`sage-ai-mcp-tool ${className || ''}`}
      >
        {/* Input Section */}
        <div className="sage-ai-mcp-section" style={styles.inputSection}>
          <div style={styles.label}>Input</div>
          <JsonHighlight data={inputData} />
        </div>

        {/* Output Section */}
        <div className="sage-ai-mcp-section" style={styles.outputSection}>
          <div style={styles.label}>Output</div>
          <JsonHighlight data={outputData} />
        </div>
      </CollapsibleSection>
    );
  }
);

MCPToolDisplay.displayName = 'MCPToolDisplay';

export default MCPToolDisplay;
