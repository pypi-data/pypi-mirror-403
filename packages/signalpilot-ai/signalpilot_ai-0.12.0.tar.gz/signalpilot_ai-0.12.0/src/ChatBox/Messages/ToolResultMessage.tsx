/**
 * ToolResultMessage Component
 *
 * Displays the result of a tool execution, including:
 * - Success/error state styling
 * - Cell ID links for cell-related tools
 * - Collapsible displays for MCP tools and terminal output
 *
 * Uses Common components for consistent, reusable UI elements.
 *
 * @example
 * ```tsx
 * <ToolResultMessage
 *   toolName="notebook-run_cell"
 *   result='{"output": "42"}'
 *   toolCallData={{ cell_id: "cell_5" }}
 *   onCellClick={(id) => scrollToCell(id)}
 * />
 * ```
 */

import React, { memo, useCallback, useMemo } from 'react';
import {
  getToolDisplayMessage,
  getToolIcon,
  isMCPTool,
  isToolSearchTool
} from '@/utils/toolDisplay';
import { getResultError } from './Common/toolResultUtils';
import {
  MCPToolDisplay,
  TerminalOutputDisplay,
  ToolSearchDisplay
} from './Common';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ToolResultMessageProps {
  /** Name of the tool */
  toolName: string;
  /** Tool execution result */
  result: any;
  /** Original tool call data */
  toolCallData: any;
  /** Whether the result has an error */
  hasError?: boolean;
  /** Callback when a cell ID is clicked */
  onCellClick?: (cellId: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

/** Pattern to match valid cell IDs */
const CELL_ID_PATTERN = /^cell_(\d+)$/;

/** Tools that support cell ID display */
const CELL_ID_TOOLS = [
  'notebook-add_cell',
  'notebook-edit_cell',
  'notebook-run_cell'
];

// ═══════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Extract cell ID from tool result or call data
 */
function extractCellId(
  toolName: string,
  result: any,
  toolCallData: any
): string | null {
  if (!CELL_ID_TOOLS.includes(toolName)) return null;

  // Check result string
  if (typeof result === 'string' && CELL_ID_PATTERN.test(result)) {
    return result;
  }

  // Check nested structure
  const nestedCellId = toolCallData?.assistant?.content?.[0]?.input?.cell_id;
  if (typeof nestedCellId === 'string' && CELL_ID_PATTERN.test(nestedCellId)) {
    return nestedCellId;
  }

  // Check direct property
  if (
    typeof toolCallData?.cell_id === 'string' &&
    CELL_ID_PATTERN.test(toolCallData.cell_id)
  ) {
    return toolCallData.cell_id;
  }

  return null;
}

// ═══════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * ToolResultMessage - Renders a completed tool result
 */
export const ToolResultMessage: React.FC<ToolResultMessageProps> = memo(
  ({ toolName, result, toolCallData, hasError, onCellClick }) => {
    // Get tool display info
    const iconHtml = useMemo(() => getToolIcon(toolName), [toolName]);
    const displayMessage = useMemo(
      () => getToolDisplayMessage(toolName, toolCallData),
      [toolName, toolCallData]
    );

    // Check for errors in result
    const errorMessage = useMemo(() => {
      const err = getResultError(result);
      return typeof err === 'string' ? err : undefined;
    }, [result]);

    // Extract cell ID
    const cellId = useMemo(
      () => extractCellId(toolName, result, toolCallData),
      [toolName, result, toolCallData]
    );

    // Build class names
    const containerClasses = [
      'sage-ai-tool-call-v1',
      (hasError || errorMessage) && 'error-state',
      cellId && 'clickable',
      isMCPTool(toolName) && 'sage-ai-mcp-tool'
    ]
      .filter(Boolean)
      .join(' ');

    // Create header content
    const headerContent = (
      <>
        <div
          className="sage-ai-tool-call-icon"
          dangerouslySetInnerHTML={{ __html: iconHtml }}
        />
        <span dangerouslySetInnerHTML={{ __html: displayMessage }} />
        {cellId && <div className="sage-ai-tool-call-cell">{cellId}</div>}
      </>
    );

    // Determine which display to use
    const isTerminalTool = toolName === 'terminal-execute_command';
    const isToolSearch = isToolSearchTool(toolName);
    const isMCP = isMCPTool(toolName);

    // Handle edit_plan special case
    const handleContainerClick = useCallback(() => {
      if (toolName === 'notebook-edit_plan') {
        // TODO: Scroll to plan cell
      } else if (cellId && onCellClick) {
        onCellClick(cellId);
      }
    }, [toolName, cellId, onCellClick]);

    // Terminal output display
    if (isTerminalTool) {
      return (
        <div
          className={containerClasses}
          data-tool-call-name={toolName}
          title={errorMessage}
          style={{ display: 'block' }}
        >
          <TerminalOutputDisplay result={result} header={headerContent} />
        </div>
      );
    }

    // Tool search display (tool_search_tool_regex, tool_search_tool_bm25)
    if (isToolSearch) {
      return (
        <div
          className={`${containerClasses} sage-ai-tool-search`}
          data-tool-call-name={toolName}
          title={errorMessage}
          style={{ display: 'block' }}
        >
          <ToolSearchDisplay
            toolCallData={toolCallData}
            result={result}
            header={headerContent}
          />
        </div>
      );
    }

    // MCP tool display
    if (isMCP) {
      return (
        <div
          className={containerClasses}
          data-tool-call-name={toolName}
          title={errorMessage}
          style={{ display: 'block' }}
        >
          <MCPToolDisplay
            toolCallData={toolCallData}
            result={result}
            header={headerContent}
          />
        </div>
      );
    }

    // Standard tool result display
    return (
      <div
        className={containerClasses}
        data-tool-call-name={toolName}
        onClick={
          cellId || toolName === 'notebook-edit_plan'
            ? handleContainerClick
            : undefined
        }
        title={errorMessage}
        style={
          cellId || toolName === 'notebook-edit_plan'
            ? { cursor: 'pointer' }
            : undefined
        }
      >
        {headerContent}
      </div>
    );
  }
);

ToolResultMessage.displayName = 'ToolResultMessage';

export default ToolResultMessage;
