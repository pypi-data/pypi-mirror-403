/**
 * DiffApproval Types
 *
 * Shared type definitions for diff approval components.
 */

import { IDiffCellUI } from '@/stores/chatMessages';

/**
 * Decision state for a single cell
 */
export interface CellDecision {
  approved?: boolean;
  userDecision?: 'approved' | 'rejected' | 'run';
  runResult?: any;
  isRunning?: boolean;
}

/**
 * Props for the main diff approval dialog
 */
export interface DiffApprovalDialogProps {
  notebookPath?: string;
  diffCells: IDiffCellUI[];
  onComplete?: () => void;
}

/**
 * Actions returned by the useDiffApproval hook
 */
export interface DiffApprovalActions {
  approveCell: (cellId: string) => void;
  rejectCell: (cellId: string) => void;
  runCell: (cellId: string) => Promise<void>;
  approveAll: () => Promise<void>;
  rejectAll: () => Promise<void>;
}

/**
 * State returned by the useDiffApproval hook
 */
export interface DiffApprovalState {
  cellDecisions: Map<string, CellDecision>;
  isAllDecided: boolean;
}
