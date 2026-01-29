/**
 * DiffActionButtons Component
 *
 * Action buttons for diff approval: approve, reject, run.
 * Includes icons and loading states.
 */

import React, { memo } from 'react';
import { CellDecision } from './types'; // ===============================================================

// ===============================================================
// ICONS
// ===============================================================

export const ApproveIcon: React.FC = () => (
  <svg
    width="15"
    height="16"
    viewBox="0 0 15 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12.5 4.25L5.625 11.125L2.5 8"
      stroke="#22C55E"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const RejectIcon: React.FC = () => (
  <svg
    width="15"
    height="16"
    viewBox="0 0 15 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M11.25 4.25L3.75 11.75M3.75 4.25L11.25 11.75"
      stroke="#FF2323"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const RunIcon: React.FC = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
  >
    <path
      d="M4 2.91583C4 2.52025 4.43762 2.28133 4.77038 2.49524L12.6791 7.57941C12.9852 7.77623 12.9852 8.22377 12.6791 8.42059L4.77038 13.5048C4.43762 13.7187 4 13.4798 4 13.0842V2.91583Z"
      fill="#3B82F6"
      stroke="#3B82F6"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M13.1018 5.35787L6.45639 9.55022L5.34214 7.88071"
      stroke="#1A1A1A"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export const Spinner: React.FC = () => <div className="sage-ai-diff-spinner" />;

export const CollapseIcon: React.FC = () => (
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
);

export const ExpandIcon: React.FC = () => (
  <svg width="14px" height="14px" viewBox="0 0 24 24" fill="none">
    <path
      d="M5.70711 9.71069C5.31658 10.1012 5.31658 10.7344 5.70711 11.1249L10.5993 16.0123C11.3805 16.7927 12.6463 16.7924 13.4271 16.0117L18.3174 11.1213C18.708 10.7308 18.708 10.0976 18.3174 9.70708C17.9269 9.31655 17.2937 9.31655 16.9032 9.70708L12.7176 13.8927C12.3271 14.2833 11.6939 14.2832 11.3034 13.8927L7.12132 9.71069C6.7308 9.32016 6.09763 9.32016 5.70711 9.71069Z"
      fill="#999999"
    />
  </svg>
);

// ===============================================================
// CELL ACTION BUTTONS
// ===============================================================

interface CellActionButtonsProps {
  cellId: string;
  decision: CellDecision;
  onApprove: (cellId: string) => void;
  onReject: (cellId: string) => void;
  onRun: (cellId: string) => void;
  /** Diff type - 'remove' diffs don't show Run button */
  diffType?: 'add' | 'edit' | 'remove';
}

/**
 * CellActionButtons - Approve/Reject/Run buttons for a single cell
 */
export const CellActionButtons: React.FC<CellActionButtonsProps> = memo(
  ({ cellId, decision, onApprove, onReject, onRun, diffType }) => {
    const isRunning = decision.isRunning;
    const isDecided =
      decision.approved !== undefined || decision.userDecision === 'run';

    // Remove diffs don't have a "run" option - only accept/reject
    const isRemoveDiff = diffType === 'remove';

    // Show spinner when running
    if (isRunning) {
      return (
        <div className="sage-ai-diff-hover-buttons">
          <Spinner />
        </div>
      );
    }

    // Show decided state
    if (isDecided) {
      return (
        <div className="sage-ai-diff-hover-buttons">
          {decision.approved === true && (
            <button className="sage-ai-diff-approve-button disabled" disabled>
              <ApproveIcon />
            </button>
          )}
          {decision.approved === false && (
            <button className="sage-ai-diff-reject-button disabled" disabled>
              <RejectIcon />
            </button>
          )}
          {decision.userDecision === 'run' &&
            decision.runResult &&
            !isRemoveDiff && (
              <button className="sage-ai-diff-run-button disabled" disabled>
                <RunIcon />
              </button>
            )}
        </div>
      );
    }

    // Show action buttons for undecided cells
    return (
      <div className="sage-ai-diff-hover-buttons">
        <button
          className="sage-ai-diff-reject-button"
          title="Reject this change"
          onClick={e => {
            e.stopPropagation();
            onReject(cellId);
          }}
        >
          <RejectIcon />
        </button>
        <button
          className="sage-ai-diff-approve-button"
          title={isRemoveDiff ? 'Accept deletion' : 'Approve this change'}
          onClick={e => {
            e.stopPropagation();
            onApprove(cellId);
          }}
        >
          <ApproveIcon />
        </button>
        {/* Don't show Run button for remove diffs - deletion has no "run" concept */}
        {!isRemoveDiff && (
          <button
            className="sage-ai-diff-run-button"
            title="Apply and run immediately"
            onClick={e => {
              e.stopPropagation();
              onRun(cellId);
            }}
          >
            <RunIcon />
          </button>
        )}
      </div>
    );
  }
);

CellActionButtons.displayName = 'CellActionButtons';

// ===============================================================
// BULK ACTION BUTTONS
// ===============================================================

interface BulkActionButtonsProps {
  onApproveAll: () => void;
  onRejectAll: () => void;
  isRunContext?: boolean;
}

/**
 * BulkActionButtons - Approve All / Reject All buttons
 */
export const BulkActionButtons: React.FC<BulkActionButtonsProps> = memo(
  ({ onApproveAll, onRejectAll, isRunContext = true }) => {
    return (
      <div className="sage-ai-inline-diff-actions">
        <button className="sage-ai-reject-button" onClick={onRejectAll}>
          Reject All
        </button>
        <button className="sage-ai-confirm-button" onClick={onApproveAll}>
          {isRunContext ? 'Approve All and Run' : 'Approve All'}
        </button>
      </div>
    );
  }
);

BulkActionButtons.displayName = 'BulkActionButtons';

export default CellActionButtons;
