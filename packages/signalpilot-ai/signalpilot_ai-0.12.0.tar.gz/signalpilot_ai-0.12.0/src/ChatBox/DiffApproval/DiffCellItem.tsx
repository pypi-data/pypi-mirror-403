/**
 * DiffCellItem Component
 *
 * Displays a single cell diff with header, content, and action buttons.
 */

import React, { memo, useCallback, useState } from 'react';
import { IDiffCellUI } from '@/stores/chatMessages';
import { getNotebookTools } from '@/stores/servicesStore';
import { CellDecision } from './types';
import { DiffMergeView } from './DiffMergeView';
import {
  CellActionButtons,
  CollapseIcon,
  ExpandIcon
} from './DiffActionButtons';

// ===============================================================
// TYPES
// ===============================================================

export interface DiffCellItemProps {
  /** Cell data */
  cell: IDiffCellUI;
  /** Current decision state */
  decision: CellDecision;
  /** Approve callback */
  onApprove: (cellId: string) => void;
  /** Reject callback */
  onReject: (cellId: string) => void;
  /** Run callback */
  onRun: (cellId: string) => void;
}

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * DiffCellItem - Single cell in the diff approval list
 *
 * Features:
 * - Collapsible header with cell ID
 * - CodeMirror merge view for diff visualization
 * - Expandable content area
 * - Action buttons (approve/reject/run)
 */
export const DiffCellItem: React.FC<DiffCellItemProps> = memo(
  ({ cell, decision, onApprove, onReject, onRun }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isContentVisible, setIsContentVisible] = useState(true);

    // Handle cell ID click - scroll to cell in notebook
    const handleCellIdClick = useCallback(() => {
      getNotebookTools()?.scrollToCellById(cell.cellId);
    }, [cell.cellId]);

    // Toggle content visibility
    const handleToggleContent = useCallback(
      (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsContentVisible(!isContentVisible);
      },
      [isContentVisible]
    );

    // Toggle expanded state
    const handleToggleExpand = useCallback(() => {
      setIsExpanded(!isExpanded);
    }, [isExpanded]);

    // Determine cell state class
    const getStateClass = (): string => {
      if (decision.userDecision === 'run') return 'sage-ai-diff-run';
      if (decision.approved === true) return 'sage-ai-diff-approved';
      if (decision.approved === false) return 'sage-ai-diff-rejected';
      return '';
    };

    return (
      <div
        className={`sage-ai-diff-cell-item ${getStateClass()}`}
        data-cell-id={cell.cellId}
      >
        {/* Header */}
        <div className="sage-ai-diff-cell-header">
          {/* Collapse toggle */}
          <span
            className="sage-ai-diff-content-collapse-icon"
            onClick={handleToggleContent}
            title={isContentVisible ? 'Collapse' : 'Expand'}
          >
            <CollapseIcon />
          </span>

          {/* Cell ID - clickable to scroll to cell */}
          <span
            className="sage-ai-diff-cell-id-label"
            onClick={handleCellIdClick}
            title="Click to scroll to cell"
          >
            {cell.cellId}
          </span>

          {/* Action buttons */}
          <CellActionButtons
            cellId={cell.cellId}
            decision={decision}
            onApprove={onApprove}
            onReject={onReject}
            onRun={onRun}
            diffType={cell.type}
          />
        </div>

        {/* Diff content */}
        {isContentVisible && (
          <div
            className={`sage-ai-diff-content ${isExpanded ? 'sage-ai-diff-expanded' : ''}`}
            onClick={handleToggleExpand}
            title={isExpanded ? 'Click to collapse' : 'Click to expand'}
          >
            <DiffMergeView
              originalContent={cell.originalContent || ''}
              newContent={cell.newContent || ''}
            />

            {/* Gradient overlay for collapsed state */}
            {!isExpanded && (
              <div className="sage-ai-diff-gradient-overlay">
                <ExpandIcon />
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
);

DiffCellItem.displayName = 'DiffCellItem';

export default DiffCellItem;
