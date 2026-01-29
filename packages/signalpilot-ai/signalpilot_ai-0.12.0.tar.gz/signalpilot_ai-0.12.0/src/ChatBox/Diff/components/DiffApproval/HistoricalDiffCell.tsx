/**
 * HistoricalDiffCell Component
 *
 * Renders a single historical diff cell with:
 * - Collapsible header with cell ID
 * - CodeMirror merge view showing the diff (via DiffMergeView)
 * - Reapply button for edit-type diffs
 *
 * Uses DiffMergeView component for CodeMirror integration.
 *
 * @example
 * ```tsx
 * <HistoricalDiffCell
 *   cellId="cell_1"
 *   type="edit"
 *   originalContent="x = 1"
 *   newContent="x = 2"
 *   onCellClick={handleCellClick}
 *   onReapply={handleReapply}
 * />
 * ```
 */

import React, { memo, useCallback, useState } from 'react';
import { DiffMergeView } from './DiffMergeView';
import { REAPPLY_ICON } from '@/Components/icons';

// ===============================================================
// TYPES
// ===============================================================

export interface HistoricalDiffCellProps {
  /** Cell identifier */
  cellId: string;
  /** Type of change (add, edit, remove) */
  type: string;
  /** Original cell content */
  originalContent: string;
  /** New cell content */
  newContent: string;
  /** Display summary for the change */
  displaySummary?: string;
  /** Notebook path for context */
  notebookPath?: string;
  /** Callback when cell ID is clicked */
  onCellClick?: (cellId: string) => void;
  /** Callback when reapply button is clicked */
  onReapply?: (cellId: string) => void;
}

// ===============================================================
// SUB-COMPONENTS
// ===============================================================

const CollapseIcon: React.FC<{ onClick: () => void }> = ({ onClick }) => (
  <span
    className="sage-ai-diff-content-collapse-icon"
    onClick={onClick}
    role="button"
    tabIndex={0}
    onKeyDown={e => e.key === 'Enter' && onClick()}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="15"
      height="15"
      viewBox="0 0 10 10"
      fill="none"
    >
      <path
        d="M2.62081 5.95419C2.58175 5.99293 2.55076 6.03901 2.5296 6.08979C2.50845 6.14056 2.49756 6.19502 2.49756 6.25003C2.49756 6.30503 2.50845 6.35949 2.5296 6.41027C2.55076 6.46104 2.58175 6.50712 2.62081 6.54586L4.70414 8.62919C4.74288 8.66825 4.78896 8.69924 4.83973 8.7204C4.89051 8.74155 4.94497 8.75244 4.99997 8.75244C5.05498 8.75244 5.10944 8.74155 5.16021 8.7204C5.21099 8.69924 5.25707 8.66825 5.29581 8.62919L7.37914 6.54586C7.41819 6.50712 7.44919 6.46104 7.47035 6.41027C7.4915 6.35949 7.50239 6.30503 7.50239 6.25003C7.50239 6.19502 7.4915 6.14056 7.47035 6.08979C7.44919 6.03901 7.41819 5.99293 7.37914 5.95419C7.34041 5.91514 7.29432 5.88414 7.24355 5.86299C7.19277 5.84183 7.13831 5.83094 7.08331 5.83094C7.0283 5.83094 6.97384 5.84183 6.92307 5.86299C6.87229 5.88414 6.82621 5.91514 6.78747 5.95419L4.99997 7.74586L3.21247 5.95419C3.17374 5.91514 3.12766 5.88414 3.07688 5.86299C3.02611 5.84183 2.97165 5.83094 2.91664 5.83094C2.86164 5.83094 2.80718 5.84183 2.7564 5.86299C2.70563 5.88414 2.65954 5.91514 2.62081 5.95419ZM4.70414 1.37086L2.62081 3.45419C2.58196 3.49304 2.55114 3.53916 2.53012 3.58992C2.50909 3.64068 2.49827 3.69508 2.49827 3.75003C2.49827 3.86098 2.54235 3.9674 2.62081 4.04586C2.65966 4.08471 2.70578 4.11553 2.75654 4.13655C2.8073 4.15758 2.8617 4.1684 2.91664 4.1684C3.0276 4.1684 3.13401 4.12432 3.21247 4.04586L4.99997 2.25419L6.78747 4.04586C6.82621 4.08491 6.87229 4.11591 6.92307 4.13706C6.97384 4.15822 7.0283 4.16911 7.08331 4.16911C7.13831 4.16911 7.19277 4.15822 7.24355 4.13706C7.29432 4.11591 7.34041 4.08491 7.37914 4.04586C7.41819 4.00712 7.44919 3.96104 7.47035 3.91027C7.4915 3.85949 7.50239 3.80503 7.50239 3.75003C7.50239 3.69502 7.4915 3.64056 7.47035 3.58979C7.44919 3.53901 7.41819 3.49293 7.37914 3.45419L5.29581 1.37086C5.25707 1.33181 5.21099 1.30081 5.16021 1.27965C5.10944 1.2585 5.05498 1.24761 4.99997 1.24761C4.94497 1.24761 4.89051 1.2585 4.83973 1.27965C4.78896 1.30081 4.74288 1.33181 4.70414 1.37086Z"
        fill="#999999"
      />
    </svg>
  </span>
);

const ExpandArrowIcon: React.FC = () => (
  <svg
    width="14px"
    height="14px"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5.70711 9.71069C5.31658 10.1012 5.31658 10.7344 5.70711 11.1249L10.5993 16.0123C11.3805 16.7927 12.6463 16.7924 13.4271 16.0117L18.3174 11.1213C18.708 10.7308 18.708 10.0976 18.3174 9.70708C17.9269 9.31655 17.2937 9.31655 16.9032 9.70708L12.7176 13.8927C12.3271 14.2833 11.6939 14.2832 11.3034 13.8927L7.12132 9.71069C6.7308 9.32016 6.09763 9.32016 5.70711 9.71069Z"
      fill="#999999"
    />
  </svg>
);

// ===============================================================
// COMPONENT
// ===============================================================

/**
 * HistoricalDiffCell - Renders a single diff cell for historical display
 */
export const HistoricalDiffCell: React.FC<HistoricalDiffCellProps> = memo(
  ({
    cellId,
    type,
    originalContent,
    newContent,
    displaySummary,
    notebookPath,
    onCellClick,
    onReapply
  }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isContentHidden, setIsContentHidden] = useState(false);

    // Calculate if content is compressable based on line count
    // This avoids DOM queries by estimating from content
    const isCompressable = React.useMemo(() => {
      const originalLines = originalContent.split('\n').length;
      const newLines = newContent.split('\n').length;
      return Math.max(originalLines, newLines) > 9;
    }, [originalContent, newContent]);

    // Determine if reapply button should be shown
    const isPlanCell =
      cellId === 'planning_cell' || cellId.startsWith('planning_') || false;
    const showReapplyButton = type === 'edit' && !isPlanCell;

    // Handle cell ID click
    const handleCellIdClick = useCallback(() => {
      onCellClick?.(cellId);
    }, [cellId, onCellClick]);

    // Handle collapse icon click
    const handleCollapseClick = useCallback(() => {
      setIsContentHidden(prev => !prev);
    }, []);

    // Handle diff content click (expand/collapse)
    const handleContentClick = useCallback(() => {
      if (!isCompressable) return;
      setIsExpanded(prev => !prev);
    }, [isCompressable]);

    // Handle reapply button click
    const handleReapplyClick = useCallback(() => {
      onReapply?.(cellId);
    }, [cellId, onReapply]);

    // Build wrapper class names
    const wrapperClasses = [
      'sage-ai-diff-content-wrapper',
      isExpanded && 'sage-ai-diff-expanded'
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div className="sage-ai-diff-cell-item" data-cell-id={cellId}>
        {/* Header */}
        <div className="sage-ai-diff-cell-header">
          <CollapseIcon onClick={handleCollapseClick} />
          <span
            className="sage-ai-diff-cell-id-label"
            onClick={handleCellIdClick}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && handleCellIdClick()}
          >
            {cellId}
          </span>

          {/* Hover buttons */}
          <div className="sage-ai-diff-hover-buttons">
            {showReapplyButton && (
              <button
                className="sage-ai-diff-reapply-button"
                onClick={handleReapplyClick}
                title="Reapply this change"
                dangerouslySetInnerHTML={{ __html: REAPPLY_ICON.svgstr }}
              />
            )}
          </div>
        </div>

        {/* Diff Content - using DiffMergeView component */}
        {!isContentHidden && (
          <div
            className={wrapperClasses}
            style={{ cursor: isCompressable ? 'pointer' : 'default' }}
            title={
              isExpanded
                ? 'Click to collapse diff content'
                : 'Click to expand diff content'
            }
            onClick={handleContentClick}
          >
            <div className="sage-ai-diff-content-inner">
              <DiffMergeView
                originalContent={originalContent}
                newContent={newContent}
              />
            </div>

            {/* Gradient overlay for collapsible content */}
            {isCompressable && !isExpanded && (
              <div className="sage-ai-diff-gradient-overlay">
                <ExpandArrowIcon />
              </div>
            )}
          </div>
        )}
      </div>
    );
  }
);

HistoricalDiffCell.displayName = 'HistoricalDiffCell';

export default HistoricalDiffCell;
