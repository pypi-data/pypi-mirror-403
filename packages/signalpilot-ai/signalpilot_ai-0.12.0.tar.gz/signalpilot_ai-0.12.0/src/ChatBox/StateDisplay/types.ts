import { IPendingDiff } from '@/types'; // Re-export from store for backwards compatibility

// Re-export from store for backwards compatibility
// The canonical definition is now in the store
export { LLMDisplayState, type ILLMState } from '@/stores/llmStateStore';

/**
 * Props for DiffItem component
 */
export interface IDiffItemProps {
  diff: IPendingDiff;
  showActionsOnHover?: boolean;
}
