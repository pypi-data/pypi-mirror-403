/**
 * ToolCallDisplay Component
 *
 * Displays a tool call in the chat. A single component handles both:
 * - Streaming state: "SignalPilot is adding a cell..."
 * - Completed state: "Added cell_X" (when hasResult is true)
 *
 * This unifies tool_call and tool_result into one display, avoiding duplicate
 * messages in the chat.
 *
 * @example
 * ```tsx
 * // Streaming tool call
 * <ToolCallDisplay
 *   toolName="notebook-add_cell"
 *   toolInput={{ cell_id: "cell_1" }}
 *   isStreaming={true}
 * />
 *
 * // Completed tool call with result
 * <ToolCallDisplay
 *   toolName="notebook-add_cell"
 *   toolInput={{ cell_id: "cell_1" }}
 *   hasResult={true}
 *   result="cell_1"
 * />
 * ```
 */
import React, { useCallback, useMemo } from 'react';
import {
  getToolDisplayMessage,
  getToolIcon,
  isToolSearchTool,
  isMCPTool
} from '@/utils/toolDisplay';
import { ToolSearchDisplay, MCPToolDisplay } from '../Common';

export interface ToolCallDisplayProps {
  /** The name of the tool being called */
  toolName: string;

  /** The input parameters for the tool */
  toolInput?: Record<string, any>;

  /** Whether this is a streaming (in-progress) tool call */
  isStreaming?: boolean;

  /** Callback when cell ID label is clicked (for scrolling to cell) */
  onCellClick?: (cellId: string) => void;

  /** Whether the tool has completed with a result */
  hasResult?: boolean;

  /** The result data from tool execution */
  result?: any;

  /** Original tool call data */
  toolCallData?: any;

  /** Whether the result has an error */
  hasError?: boolean;

  /** Tool search result (for server_tool_use tools) */
  toolSearchResult?: {
    input: any;
    result: any;
  };
}

/**
 * Extract cell ID from tool input if present
 */
function extractCellId(
  toolName: string,
  toolInput?: Record<string, any>
): string | null {
  if (!toolInput) return null;

  // Tools that can have a cell ID
  const cellIdTools = [
    'notebook-add_cell',
    'notebook-edit_cell',
    'notebook-run_cell'
  ];
  if (!cellIdTools.includes(toolName)) return null;

  // Check various places where cell_id might be
  const cellId = toolInput.cell_id;
  if (typeof cellId === 'string' && /^cell_\d+$/.test(cellId)) {
    return cellId;
  }

  return null;
}

/**
 * Extract cell ID from result string if it matches pattern
 */
function extractCellIdFromResult(result: any): string | null {
  if (typeof result === 'string' && /^cell_\d+$/.test(result)) {
    return result;
  }
  return null;
}

/**
 * Check if result contains an error
 */
function hasResultError(result: any): boolean {
  try {
    if (typeof result === 'string') {
      const parsed = JSON.parse(result);
      return parsed?.error === true;
    }
  } catch {
    // Not JSON
  }
  return false;
}

/**
 * ToolCallDisplay - Shows a tool call with icon, text, and optional cell ID
 *
 * CSS Classes:
 * - .sage-ai-tool-call-v1: Main container
 * - .sage-ai-streaming-tool-call: Added when streaming
 * - .sage-ai-tool-call-icon: Icon container
 * - .sage-ai-loading-text: Loading/action text
 * - .sage-ai-tool-call-cell: Clickable cell ID label
 * - .clickable: Added when cell ID is present
 * - .error-state: Added when hasError is true
 */
export const ToolCallDisplay: React.FC<ToolCallDisplayProps> = ({
  toolName,
  toolInput = {},
  isStreaming = false,
  onCellClick,
  hasResult = false,
  result,
  toolCallData,
  hasError = false,
  toolSearchResult
}) => {
  // Get the icon HTML for this tool
  const iconHtml = useMemo(() => getToolIcon(toolName), [toolName]);

  // Get the display message for this tool
  // Use toolCallData for completed state if available, otherwise use toolInput
  const displayMessage = useMemo(
    () =>
      getToolDisplayMessage(
        toolName,
        hasResult && toolCallData ? toolCallData : toolInput
      ),
    [toolName, toolInput, hasResult, toolCallData]
  );

  // Extract cell ID - check multiple sources
  const cellId = useMemo(() => {
    // First check toolInput
    const fromInput = extractCellId(toolName, toolInput);
    if (fromInput) return fromInput;

    // Then check result (for add_cell, result is the new cell_id)
    if (hasResult) {
      const fromResult = extractCellIdFromResult(result);
      if (fromResult) return fromResult;

      // Check toolCallData
      const fromToolCallData = extractCellId(toolName, toolCallData);
      if (fromToolCallData) return fromToolCallData;
    }

    return null;
  }, [toolName, toolInput, hasResult, result, toolCallData]);

  // Check for errors in result
  const showError = useMemo(() => {
    return hasError || (hasResult && hasResultError(result));
  }, [hasError, hasResult, result]);

  // Handle cell click
  const handleClick = useCallback(() => {
    if (cellId && onCellClick) {
      onCellClick(cellId);
    }
  }, [cellId, onCellClick]);

  // Check if this is a tool search tool or MCP tool
  const isToolSearch = isToolSearchTool(toolName);
  const isMCP = isMCPTool(toolName);

  // Build class names
  const containerClasses = [
    'sage-ai-tool-call-v1',
    isStreaming &&
      !hasResult &&
      !toolSearchResult &&
      'sage-ai-streaming-tool-call',
    cellId && 'clickable',
    showError && 'error-state',
    (isToolSearch || isMCP || toolSearchResult) && 'sage-ai-mcp-tool'
  ]
    .filter(Boolean)
    .join(' ');

  // Header content for collapsible displays (tool search, MCP tools)
  // Wrapped in a single container to ensure proper flex layout
  const headerContent = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <div
        className="sage-ai-tool-call-icon"
        dangerouslySetInnerHTML={{ __html: iconHtml }}
      />
      <span
        className={
          isStreaming && !hasResult && !toolSearchResult
            ? 'sage-ai-loading-text'
            : undefined
        }
        dangerouslySetInnerHTML={{ __html: displayMessage }}
      />
    </div>
  );

  // If this is a tool search with results, render the expandable display
  if (isToolSearch && toolSearchResult) {
    return (
      <div
        className={containerClasses}
        data-tool-call-name={toolName}
        style={{ display: 'block' }}
      >
        <ToolSearchDisplay
          header={headerContent}
          toolCallData={toolSearchResult.input}
          result={toolSearchResult.result}
        />
      </div>
    );
  }

  // If this is an MCP tool with results, render the expandable MCP display
  if (isMCP && toolSearchResult) {
    return (
      <div
        className={containerClasses}
        data-tool-call-name={toolName}
        style={{ display: 'block' }}
      >
        <MCPToolDisplay
          header={headerContent}
          toolCallData={toolSearchResult.input}
          result={toolSearchResult.result}
        />
      </div>
    );
  }

  // Standard tool call display
  return (
    <div
      className={containerClasses}
      data-tool-call-name={toolName}
      onClick={cellId ? handleClick : undefined}
      style={cellId ? { cursor: 'pointer' } : undefined}
    >
      {/* Tool icon */}
      <div
        className="sage-ai-tool-call-icon"
        dangerouslySetInnerHTML={{ __html: iconHtml }}
      />

      {/* Loading/action text */}
      <span
        className={
          isStreaming && !hasResult ? 'sage-ai-loading-text' : undefined
        }
        dangerouslySetInnerHTML={{ __html: displayMessage }}
      />

      {/* Cell ID label (if applicable) */}
      {cellId && <div className="sage-ai-tool-call-cell">{cellId}</div>}
    </div>
  );
};

export default ToolCallDisplay;
