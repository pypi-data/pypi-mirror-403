/**
 * ActionHistoryStore
 *
 * Zustand store for managing undo/redo action history.
 * Replaces direct access to ActionHistory class.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES (from ActionHistory.ts)
// ═══════════════════════════════════════════════════════════════

/**
 * Types of actions that can be undone
 */
export enum ActionType {
  ADD_CELL = 'add_cell',
  EDIT_CELL = 'edit_cell',
  REMOVE_CELLS = 'remove_cells',
  EDIT_PLAN = 'edit_plan'
}

/**
 * Interface for cell data in removed cells
 */
export interface IRemovedCellData {
  trackingId?: string;
  content: string;
  type: string;
  custom?: {
    summary?: string;
    index?: number;
    [key: string]: any;
  };
}

/**
 * Interface for a history action entry
 */
export interface IActionHistoryEntry {
  type: ActionType;
  data: {
    trackingId?: string;
    trackingIds?: string[];
    cellId?: string;
    cellIds?: string[];
    originalContent?: string;
    originalSummary?: string;
    newContent?: string;
    summary?: string;
    removedCells?: IRemovedCellData[];
    planExisted?: boolean;
    oldPlan?: string;
    oldCurrentStep?: string;
    oldNextStep?: string;
    source?: string;
    newSource?: string;
    metadata?: any;
    oldContent?: string;
    originalCellType?: string;
  };
  timestamp: number;
  description: string;
}

// ═══════════════════════════════════════════════════════════════
// STATE & ACTIONS
// ═══════════════════════════════════════════════════════════════

export interface IActionHistoryState {
  /** Stack of action history entries */
  history: IActionHistoryEntry[];
  /** Whether there are actions that can be undone */
  canUndo: boolean;
  /** Description of the last action */
  lastActionDescription: string | null;
}

export interface IActionHistoryActions {
  /** Add an action to the history */
  addAction: (
    type: ActionType,
    data: IActionHistoryEntry['data'],
    description: string
  ) => void;
  /** Add an action with checkpoint integration */
  addActionWithCheckpoint: (
    type: ActionType,
    data: IActionHistoryEntry['data'],
    description: string
  ) => void;
  /** Get the last action without removing it */
  getLastAction: () => IActionHistoryEntry | null;
  /** Remove and return the last action */
  popLastAction: () => IActionHistoryEntry | null;
  /** Get all actions */
  getAllActions: () => IActionHistoryEntry[];
  /** Clear all history */
  clear: () => void;
}

export type IActionHistoryStore = IActionHistoryState & IActionHistoryActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IActionHistoryState = {
  history: [],
  canUndo: false,
  lastActionDescription: null
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useActionHistoryStore = create<IActionHistoryStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────

      addAction: (
        type: ActionType,
        data: IActionHistoryEntry['data'],
        description: string
      ) => {
        const entry: IActionHistoryEntry = {
          type,
          data,
          timestamp: Date.now(),
          description
        };

        set(
          state => ({
            history: [...state.history, entry],
            canUndo: true,
            lastActionDescription: description
          }),
          false,
          'addAction'
        );

        console.log(`[ActionHistoryStore] Added action: ${description}`);
      },

      addActionWithCheckpoint: (
        type: ActionType,
        data: IActionHistoryEntry['data'],
        description: string
      ) => {
        // Add the action to history
        get().addAction(type, data, description);

        // Also add to current checkpoint if available
        // Import dynamically to avoid circular dependencies
        try {
          const {
            CheckpointManager
          } = require('../Services/CheckpointManager');
          const checkpointManager = CheckpointManager.getInstance();
          const entry: IActionHistoryEntry = {
            type,
            data,
            timestamp: Date.now(),
            description
          };
          checkpointManager.addActionToCurrentCheckpoint(entry);
        } catch (error) {
          console.warn(
            '[ActionHistoryStore] Could not add action to checkpoint:',
            error
          );
        }
      },

      getLastAction: () => {
        const { history } = get();
        if (history.length === 0) {
          return null;
        }
        return history[history.length - 1];
      },

      popLastAction: () => {
        const { history } = get();
        if (history.length === 0) {
          return null;
        }

        const action = history[history.length - 1];
        const newHistory = history.slice(0, -1);

        set(
          {
            history: newHistory,
            canUndo: newHistory.length > 0,
            lastActionDescription:
              newHistory.length > 0
                ? newHistory[newHistory.length - 1].description
                : null
          },
          false,
          'popLastAction'
        );

        console.log('[ActionHistoryStore] Action popped for undo:', action);
        return action;
      },

      getAllActions: () => {
        return [...get().history];
      },

      clear: () => {
        set(initialState, false, 'clear');
        console.log('[ActionHistoryStore] Action history cleared');
      }
    })),
    { name: 'ActionHistoryStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectCanUndo = (state: IActionHistoryStore) => state.canUndo;
export const selectLastActionDescription = (state: IActionHistoryStore) =>
  state.lastActionDescription;
export const selectHistory = (state: IActionHistoryStore) => state.history;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API
// ═══════════════════════════════════════════════════════════════

/**
 * Get current action history state (for non-React code)
 */
export function getActionHistoryState(): IActionHistoryState {
  const state = useActionHistoryStore.getState();
  return {
    history: state.history,
    canUndo: state.canUndo,
    lastActionDescription: state.lastActionDescription
  };
}

/**
 * Subscribe to canUndo changes
 */
export function subscribeToCanUndo(
  callback: (canUndo: boolean) => void
): () => void {
  return useActionHistoryStore.subscribe(state => state.canUndo, callback);
}

/**
 * Subscribe to last action description changes
 */
export function subscribeToLastActionDescription(
  callback: (description: string | null) => void
): () => void {
  return useActionHistoryStore.subscribe(
    state => state.lastActionDescription,
    callback
  );
}
