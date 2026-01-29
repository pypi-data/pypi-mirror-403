/**
 * Diff Services
 *
 * Non-DOM services for diff orchestration and state management.
 * For JupyterLab-specific code, see @/Jupyter/Diff/
 */

export { NotebookDiffManager } from './DiffManager';
export {
  DiffApprovalDialog,
  type IDiffApprovalCallbacks
} from './DiffApprovalManager';
