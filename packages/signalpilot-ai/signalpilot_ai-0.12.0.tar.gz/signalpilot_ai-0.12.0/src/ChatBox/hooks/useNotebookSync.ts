/**
 * useNotebookSync Hook
 *
 * Handles synchronization between the ChatBox and the current notebook:
 * - Tracks notebook changes
 * - Updates chat context when notebook changes
 * - Manages cell context tracking
 */

import { useCallback, useEffect } from 'react';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useAppStore } from '@/stores/appStore';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface UseNotebookSyncOptions {
  /** Callback when notebook changes */
  onNotebookChange?: (notebookId: string | null) => void;
  /** Callback when cell is added to context */
  onCellAddedToContext?: (cellId: string) => void;
  /** Callback when cell is removed from context */
  onCellRemovedFromContext?: (cellId: string) => void;
}

export interface UseNotebookSyncReturn {
  /** Current notebook ID */
  notebookId: string | null;
  /** Current notebook path */
  notebookPath: string | null;
  /** Whether a notebook is currently active */
  hasNotebook: boolean;
  /** Update the notebook ID */
  updateNotebookId: (id: string) => void;
  /** Handle cell added to context */
  onCellAddedToContext: (path: string) => void;
  /** Handle cell removed from context */
  onCellRemovedFromContext: (path: string) => void;
}

// ═══════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════

export function useNotebookSync(
  options: UseNotebookSyncOptions = {}
): UseNotebookSyncReturn {
  const {
    onNotebookChange,
    onCellAddedToContext: onCellAddedCallback,
    onCellRemovedFromContext: onCellRemovedCallback
  } = options;

  // Store state
  const {
    currentNotebookId,
    currentNotebookPath,
    updateNotebookId: storeUpdateNotebookId,
    reinitializeForNotebook
  } = useChatboxStore();

  const currentNotebook = useAppStore(state => state.currentNotebook);

  // Sync with app store's current notebook
  useEffect(() => {
    const newNotebookId = currentNotebook?.id || null;

    if (newNotebookId && newNotebookId !== currentNotebookId) {
      console.log('[useNotebookSync] Notebook changed:', newNotebookId);
      void reinitializeForNotebook(newNotebookId);
      onNotebookChange?.(newNotebookId);
    }
  }, [
    currentNotebook?.id,
    currentNotebookId,
    reinitializeForNotebook,
    onNotebookChange
  ]);

  // Update notebook ID
  const updateNotebookId = useCallback(
    (id: string) => {
      storeUpdateNotebookId(id);
    },
    [storeUpdateNotebookId]
  );

  // Handle cell added to context
  const handleCellAddedToContext = useCallback(
    (path: string) => {
      console.log('[useNotebookSync] Cell added to context:', path);
      // Context UI updates are handled by React components subscribing to stores
      onCellAddedCallback?.(path);
    },
    [onCellAddedCallback]
  );

  // Handle cell removed from context
  const handleCellRemovedFromContext = useCallback(
    (path: string) => {
      console.log('[useNotebookSync] Cell removed from context:', path);
      // Context UI updates are handled by React components subscribing to stores
      onCellRemovedCallback?.(path);
    },
    [onCellRemovedCallback]
  );

  return {
    notebookId: currentNotebookId,
    notebookPath: currentNotebookPath,
    hasNotebook: !!currentNotebookId,
    updateNotebookId,
    onCellAddedToContext: handleCellAddedToContext,
    onCellRemovedFromContext: handleCellRemovedFromContext
  };
}

export default useNotebookSync;
