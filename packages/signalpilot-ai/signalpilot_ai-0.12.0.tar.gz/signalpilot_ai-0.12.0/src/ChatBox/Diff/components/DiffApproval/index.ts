/**
 * DiffApproval Module
 *
 * React components for diff approval functionality.
 * For hooks, see @/ChatBox/Diff/hooks
 */

// Types
export * from './types';

// Hook (re-export from hooks folder for backward compatibility)
export { useDiffApproval } from '../../hooks/useDiffApproval';

// Components
export { ActiveDiffApprovalDialog } from './ActiveDiffApprovalDialog';
export { DiffCellItem } from './DiffCellItem';
export { DiffMergeView } from './DiffMergeView';
export {
  CellActionButtons,
  BulkActionButtons,
  ApproveIcon,
  RejectIcon,
  RunIcon,
  Spinner,
  CollapseIcon,
  ExpandIcon
} from './DiffActionButtons';

// Default export
export { ActiveDiffApprovalDialog as default } from './ActiveDiffApprovalDialog';
