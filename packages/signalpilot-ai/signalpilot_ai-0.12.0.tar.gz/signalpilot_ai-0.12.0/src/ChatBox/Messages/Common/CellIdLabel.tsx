/**
 * CellIdLabel Component
 *
 * Clickable cell ID label for notebook navigation.
 * Pure React implementation - no DOM manipulation.
 */

import React, { memo, useCallback, useMemo } from 'react';

// ===============================================================
// CONSTANTS
// ===============================================================

/** Tools that should have clickable cell ID labels */
const CELL_NAVIGATION_TOOLS = [
  'notebook-add_cell',
  'notebook-edit_cell',
  'notebook-run_cell'
];

/** Pattern to match valid cell IDs */
const CELL_ID_PATTERN = /^cell_(\d+)$/;

// ===============================================================
// TYPES
// ===============================================================

export interface CellIdLabelProps {
  /** Tool name */
  toolName: string;
  /** Tool call data */
  toolCallData: any;
  /** Tool result */
  result?: any;
  /** Callback when cell label is clicked */
  onCellClick?: (cellId: string) => void;
}

// ===============================================================
// UTILITY FUNCTIONS
// ===============================================================

/**
 * Extract cell ID from tool result or tool call data
 */
function extractCellId(result: any, toolCallData: any): string {
  // Check result string (e.g., "cell_5")
  if (typeof result === 'string' && CELL_ID_PATTERN.test(result)) {
    return result;
  }

  // Check nested tool call data structure
  const nestedCellId = toolCallData?.assistant?.content?.[0]?.input?.cell_id;
  if (typeof nestedCellId === 'string' && CELL_ID_PATTERN.test(nestedCellId)) {
    return nestedCellId;
  }

  // Check direct cell_id property
  if (
    typeof toolCallData?.cell_id === 'string' &&
    CELL_ID_PATTERN.test(toolCallData.cell_id)
  ) {
    return toolCallData.cell_id;
  }

  return '';
}

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * CellIdLabel - Clickable cell navigation label
 */
export const CellIdLabel: React.FC<CellIdLabelProps> = memo(
  ({ toolName, toolCallData, result, onCellClick }) => {
    // Only render for cell-related tools
    const shouldRender = CELL_NAVIGATION_TOOLS.includes(toolName);

    // Extract cell ID
    const cellId = useMemo(
      () => extractCellId(result, toolCallData),
      [result, toolCallData]
    );

    // Handle click
    const handleClick = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        if (cellId && onCellClick) {
          onCellClick(cellId);
        }
      },
      [cellId, onCellClick]
    );

    // Don't render if not applicable
    if (!shouldRender || !cellId || !CELL_ID_PATTERN.test(cellId)) {
      return null;
    }

    return (
      <div
        className="sage-ai-tool-call-cell"
        onClick={handleClick}
        title="Click to scroll to cell"
      >
        {cellId}
      </div>
    );
  }
);

CellIdLabel.displayName = 'CellIdLabel';

export default CellIdLabel;
