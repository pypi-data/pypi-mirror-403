// src/stores/notebookEventsStore.ts
// PURPOSE: Consolidated notebook state and events management
// Replaces AppStateService notebook methods and Subject-based events
//
// CRITICAL: This store handles notebook change events that drive core app functionality.
// Components should use the React hooks (useNotebookChange, useNotebookRename) to subscribe.

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { useEffect, useRef } from 'react';
import { NotebookPanel } from '@jupyterlab/notebook';
import { startTimer, endTimer } from '../utils/performanceDebug';

// Static import of chatMessagesStore to avoid async delay
import { useChatMessagesStore } from './chatMessages';

// ═══════════════════════════════════════════════════════════════
// EXTERNAL NOTEBOOK REFERENCE (stored outside Zustand for performance)
// ═══════════════════════════════════════════════════════════════
// PERFORMANCE: NotebookPanel is a complex JupyterLab widget that causes
// 600ms+ delays when stored in Zustand state due to middleware processing.
// By storing it externally, we avoid devtools/subscribeWithSelector overhead.
let _currentNotebookRef: NotebookPanel | null = null;

/**
 * Get the current notebook panel reference.
 * This is stored outside Zustand for performance reasons.
 */
export function getCurrentNotebookRef(): NotebookPanel | null {
  return _currentNotebookRef;
}

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface INotebookChangeEvent {
  oldNotebookId: string | null;
  newNotebookId: string | null;
  fromLauncher?: boolean;
  timestamp: number;
}

export interface INotebookRenameEvent {
  oldNotebookId: string;
  newNotebookId: string;
  timestamp: number;
}

interface INotebookEventsState {
  // Current notebook state
  // NOTE: currentNotebook is stored externally in _currentNotebookRef for performance
  currentNotebookId: string | null;

  // Last events (for triggering reactions)
  lastNotebookChange: INotebookChangeEvent | null;
  lastNotebookRename: INotebookRenameEvent | null;
}

interface INotebookEventsActions {
  // Getters
  getCurrentNotebookId: () => string | null;
  getCurrentNotebook: () => NotebookPanel | null;

  // Setters
  setCurrentNotebook: (
    notebook: NotebookPanel | null,
    notebookId?: string | null
  ) => void;
  setCurrentNotebookId: (notebookId: string | null) => void;

  // Notebook ID update (for renames)
  updateNotebookId: (oldNotebookId: string, newNotebookId: string) => void;

  // Event emitters (replaces Subject.next())
  notifyNotebookChanged: (
    oldId: string | null,
    newId: string | null,
    fromLauncher?: boolean
  ) => void;
  notifyNotebookRenamed: (oldId: string, newId: string) => void;

  // Aliases for backwards compatibility
  triggerNotebookChange: (
    oldNotebookId: string | null,
    newNotebookId: string | null,
    fromLauncher?: boolean
  ) => void;

  // Launcher-specific: clear notebook ref without triggering change events
  // Used when switching to launcher - we keep the last notebook ID but clear the ref
  clearForLauncher: () => void;
}

type INotebookEventsStore = INotebookEventsState & INotebookEventsActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useNotebookEventsStore = create<INotebookEventsStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      currentNotebookId: null,
      lastNotebookChange: null,
      lastNotebookRename: null,

      // ─────────────────────────────────────────────────────────────
      // Getters
      // ─────────────────────────────────────────────────────────────
      getCurrentNotebookId: () => get().currentNotebookId,

      // Returns external ref (stored outside Zustand for performance)
      getCurrentNotebook: () => _currentNotebookRef,

      // ─────────────────────────────────────────────────────────────
      // Setters
      // ─────────────────────────────────────────────────────────────
      setCurrentNotebook: (notebook, notebookId) => {
        startTimer('Store.setCurrentNotebook');
        const oldNotebookId = get().currentNotebookId;
        const newNotebookId = notebookId ?? (notebook ? 'unknown' : null);

        // PERFORMANCE: Store notebook reference externally (not in Zustand)
        // This avoids 600ms+ middleware overhead from processing the complex object
        _currentNotebookRef = notebook;

        if (oldNotebookId !== newNotebookId) {
          // IMMEDIATELY clear chat messages SYNCHRONOUSLY before any async work
          // Using static import to avoid dynamic import delay
          startTimer('Store.clearMessages');
          useChatMessagesStore.getState().clearMessages();
          endTimer('Store.clearMessages');

          startTimer('Store.setNotebookState');
          set({
            currentNotebookId: newNotebookId
          });
          endTimer('Store.setNotebookState');

          // Emit notebook change event
          startTimer('Store.notifyNotebookChanged');
          get().notifyNotebookChanged(oldNotebookId, newNotebookId);
          endTimer('Store.notifyNotebookChanged');
        }
        // Note: If ID is the same, we already updated _currentNotebookRef above
        endTimer('Store.setCurrentNotebook');
      },

      setCurrentNotebookId: notebookId => {
        const oldNotebookId = get().currentNotebookId;

        if (oldNotebookId !== notebookId) {
          // Clear external notebook ref when only ID is set
          _currentNotebookRef = null;
          set({
            currentNotebookId: notebookId
          });
          // Emit notebook change event
          get().notifyNotebookChanged(oldNotebookId, notebookId);
        }
      },

      updateNotebookId: (oldNotebookId, newNotebookId) => {
        const currentId = get().currentNotebookId;

        // Update current notebook ID if it matches the old one
        if (currentId === oldNotebookId) {
          // Clear external notebook ref during rename
          _currentNotebookRef = null;
          set({
            currentNotebookId: newNotebookId
          });
        }

        // Emit notebook rename event
        get().notifyNotebookRenamed(oldNotebookId, newNotebookId);
      },

      // ─────────────────────────────────────────────────────────────
      // Event Emitters
      // ─────────────────────────────────────────────────────────────
      notifyNotebookChanged: (oldId, newId, fromLauncher) => {
        console.log(
          `[NotebookEventsStore] Notebook changed: ${oldId} -> ${newId}`,
          fromLauncher ? '(from launcher)' : ''
        );
        set({
          lastNotebookChange: {
            oldNotebookId: oldId,
            newNotebookId: newId,
            fromLauncher,
            timestamp: Date.now()
          }
        });
      },

      notifyNotebookRenamed: (oldId, newId) => {
        console.log(
          `[NotebookEventsStore] Notebook renamed: ${oldId} -> ${newId}`
        );
        set({
          lastNotebookRename: {
            oldNotebookId: oldId,
            newNotebookId: newId,
            timestamp: Date.now()
          }
        });
      },

      // Alias for backwards compatibility
      triggerNotebookChange: (oldId, newId, fromLauncher) => {
        get().notifyNotebookChanged(oldId, newId, fromLauncher);
      },

      // Clear notebook reference for launcher mode without triggering change events
      // This allows us to "pause" notebook context while in launcher
      // The notebook ID is preserved so when we return, we can detect if it's the same notebook
      clearForLauncher: () => {
        console.log(
          '[NotebookEventsStore] Clearing notebook ref for launcher (no change event)'
        );
        _currentNotebookRef = null;
        // Note: We intentionally do NOT clear currentNotebookId or emit change events
        // This prevents race conditions when switching to launcher
      }
    })),
    {
      name: 'NotebookEventsStore',
      // PERFORMANCE: Disable serialization to prevent expensive NotebookPanel serialization
      // NotebookPanel is a complex JupyterLab widget that takes 800ms+ to serialize
      serialize: false
    }
  )
);

// ═══════════════════════════════════════════════════════════════
// REACT HOOKS FOR SUBSCRIBING TO EVENTS
// ═══════════════════════════════════════════════════════════════

/**
 * Hook to subscribe to notebook change events.
 * Calls the callback whenever a notebook change occurs.
 *
 * @param callback - Function to call when notebook changes
 *
 * @example
 * useNotebookChange((event) => {
 *   console.log('Notebook changed from', event.oldNotebookId, 'to', event.newNotebookId);
 * });
 */
export function useNotebookChange(
  callback: (event: INotebookChangeEvent) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    // Subscribe to changes in lastNotebookChange
    const unsubscribe = useNotebookEventsStore.subscribe(
      state => state.lastNotebookChange,
      (lastChange, prevChange) => {
        // Only fire if this is a new event (different timestamp)
        if (lastChange && lastChange.timestamp !== prevChange?.timestamp) {
          callbackRef.current(lastChange);
        }
      }
    );

    return unsubscribe;
  }, []);
}

/**
 * Hook to subscribe to notebook rename events.
 * Calls the callback whenever a notebook is renamed.
 *
 * @param callback - Function to call when notebook is renamed
 *
 * @example
 * useNotebookRename((event) => {
 *   console.log('Notebook renamed from', event.oldNotebookId, 'to', event.newNotebookId);
 * });
 */
export function useNotebookRename(
  callback: (event: INotebookRenameEvent) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    // Subscribe to changes in lastNotebookRename
    const unsubscribe = useNotebookEventsStore.subscribe(
      state => state.lastNotebookRename,
      (lastRename, prevRename) => {
        // Only fire if this is a new event (different timestamp)
        if (lastRename && lastRename.timestamp !== prevRename?.timestamp) {
          callbackRef.current(lastRename);
        }
      }
    );

    return unsubscribe;
  }, []);
}

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTION (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to notebook change events from non-React code.
 * Returns an unsubscribe function.
 *
 * @param callback - Function to call when notebook changes
 * @returns Unsubscribe function
 *
 * @example
 * const unsubscribe = subscribeToNotebookChange((event) => {
 *   console.log('Notebook changed:', event);
 * });
 * // Later: unsubscribe();
 */
export function subscribeToNotebookChange(
  callback: (event: INotebookChangeEvent) => void
): () => void {
  return useNotebookEventsStore.subscribe(
    state => state.lastNotebookChange,
    (lastChange, prevChange) => {
      if (lastChange && lastChange.timestamp !== prevChange?.timestamp) {
        callback(lastChange);
      }
    }
  );
}

/**
 * Subscribe to notebook rename events from non-React code.
 * Returns an unsubscribe function.
 *
 * @param callback - Function to call when notebook is renamed
 * @returns Unsubscribe function
 */
export function subscribeToNotebookRename(
  callback: (event: INotebookRenameEvent) => void
): () => void {
  return useNotebookEventsStore.subscribe(
    state => state.lastNotebookRename,
    (lastRename, prevRename) => {
      if (lastRename && lastRename.timestamp !== prevRename?.timestamp) {
        callback(lastRename);
      }
    }
  );
}
