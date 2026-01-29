// src/stores/appStore.ts
// PURPOSE: Core application state - initialization, current notebook, mode flags
// Single source of truth for app-wide flags (migrated from AppStateService)

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { NotebookPanel } from '@jupyterlab/notebook';
import { StateDBCachingService, STATE_DB_KEYS } from '../utils/backendCaching';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IAppState {
  // Initialization
  isInitialized: boolean;
  isLauncherActive: boolean;

  // Current Context
  currentNotebookId: string | null;
  currentNotebook: NotebookPanel | null;
  currentWorkingDirectory: string | null;
  setupManager: 'conda' | 'venv' | 'uv' | 'system' | null;

  // Workspace context
  workspaceContext: any | null;

  // Welcome tour
  hasCompletedWelcomeTour: boolean;

  // Mode Flags
  isDemoMode: boolean;
  isTakeoverMode: boolean;
  takeoverPrompt: string | null;
  autoRun: boolean;

  // Limits
  maxToolCallLimit: number | null;

  // User
  userProfile: any | null;
}

interface IAppActions {
  // Setters
  setInitialized: (value: boolean) => void;
  setLauncherActive: (value: boolean) => void;
  setCurrentNotebook: (
    notebook: NotebookPanel | null,
    notebookId?: string | null
  ) => void;
  setCurrentNotebookId: (notebookId: string | null) => void;
  setCurrentWorkingDirectory: (directory: string | null) => void;
  setSetupManager: (
    setupManager: 'conda' | 'venv' | 'uv' | 'system' | null
  ) => void;
  setWorkspaceContext: (context: any | null) => void;
  setHasCompletedWelcomeTour: (value: boolean) => void;
  loadWelcomeTourState: () => Promise<void>;
  setDemoMode: (value: boolean, persist?: boolean) => Promise<void>;
  loadDemoMode: () => Promise<void>;
  setTakeoverMode: (enabled: boolean, prompt?: string | null) => void;
  setAutoRun: (value: boolean) => void;
  setMaxToolCallLimit: (limit: number | null) => void;
  setUserProfile: (profile: any | null) => void;

  // Getters (for non-React code compatibility)
  getState: () => IAppState;
}

type IAppStore = IAppState & IAppActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useAppStore = create<IAppStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      isInitialized: false,
      isLauncherActive: false,
      currentNotebookId: null,
      currentNotebook: null,
      currentWorkingDirectory: null,
      setupManager: null,
      workspaceContext: null,
      hasCompletedWelcomeTour: false,
      isDemoMode: false,
      isTakeoverMode: false,
      takeoverPrompt: null,
      autoRun: false,
      maxToolCallLimit: null,
      userProfile: null,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      setInitialized: value => set({ isInitialized: value }),

      setLauncherActive: value => {
        if (get().isLauncherActive !== value) {
          set({ isLauncherActive: value });
          console.log(`[AppStore] Launcher active state changed: ${value}`);
        }
      },

      setCurrentNotebook: (notebook, notebookId) => {
        const newNotebookId = notebookId ?? (notebook ? 'unknown' : null);
        set({
          currentNotebook: notebook,
          currentNotebookId: newNotebookId
        });
      },

      setCurrentNotebookId: notebookId => {
        set({
          currentNotebookId: notebookId,
          currentNotebook: null // Clear notebook reference when only ID is set
        });
      },

      setCurrentWorkingDirectory: directory => {
        set({ currentWorkingDirectory: directory });
      },

      setSetupManager: setupManager => {
        set({ setupManager });
      },

      setWorkspaceContext: context => {
        set({ workspaceContext: context });
        console.log('[AppStore] Workspace context set');
      },

      setHasCompletedWelcomeTour: value => {
        set({ hasCompletedWelcomeTour: value });
      },

      loadWelcomeTourState: async () => {
        try {
          const completed = await StateDBCachingService.getValue(
            STATE_DB_KEYS.WELCOME_TOUR_COMPLETED,
            false
          );
          set({ hasCompletedWelcomeTour: completed as boolean });
          console.log('[AppStore] Loaded welcome tour state:', completed);
        } catch (error) {
          console.error('[AppStore] Failed to load welcome tour state:', error);
          set({ hasCompletedWelcomeTour: false });
        }
      },

      setDemoMode: async (value, persist = true) => {
        set({ isDemoMode: value });
        console.log('[AppStore] Demo mode set to:', value);
        if (persist) {
          try {
            await StateDBCachingService.setValue(
              STATE_DB_KEYS.IS_DEMO_MODE,
              value
            );
          } catch (error) {
            console.error('[AppStore] Failed to persist demo mode:', error);
          }
        }
      },

      loadDemoMode: async () => {
        try {
          const isDemoMode = await StateDBCachingService.getValue(
            STATE_DB_KEYS.IS_DEMO_MODE,
            false
          );
          set({ isDemoMode: isDemoMode as boolean });
          console.log('[AppStore] Loaded demo mode from cache:', isDemoMode);
        } catch (error) {
          console.error('[AppStore] Failed to load demo mode:', error);
          set({ isDemoMode: false });
        }
      },

      setTakeoverMode: (enabled, prompt) => {
        set({
          isTakeoverMode: enabled,
          takeoverPrompt: prompt ?? null
        });
        console.log(
          '[AppStore] Takeover mode set to:',
          enabled,
          'with prompt:',
          prompt
        );
      },

      setAutoRun: value => {
        set({ autoRun: value });
        console.log(
          `[AppStore] Auto-run mode ${value ? 'enabled' : 'disabled'}`
        );
      },

      setMaxToolCallLimit: limit => set({ maxToolCallLimit: limit }),

      setUserProfile: profile => {
        set({ userProfile: profile });
        console.log(
          '[AppStore] User profile set:',
          profile ? 'loaded' : 'cleared'
        );
      },

      // For non-React code compatibility
      getState: () => {
        const state = get();
        return {
          isInitialized: state.isInitialized,
          isLauncherActive: state.isLauncherActive,
          currentNotebookId: state.currentNotebookId,
          currentNotebook: state.currentNotebook,
          currentWorkingDirectory: state.currentWorkingDirectory,
          setupManager: state.setupManager,
          workspaceContext: state.workspaceContext,
          hasCompletedWelcomeTour: state.hasCompletedWelcomeTour,
          isDemoMode: state.isDemoMode,
          isTakeoverMode: state.isTakeoverMode,
          takeoverPrompt: state.takeoverPrompt,
          autoRun: state.autoRun,
          maxToolCallLimit: state.maxToolCallLimit,
          userProfile: state.userProfile
        };
      }
    })),
    { name: 'AppStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS (for optimized re-renders)
// ═══════════════════════════════════════════════════════════════

export const selectIsDemoMode = (state: IAppStore) => state.isDemoMode;
export const selectWorkspaceContext = (state: IAppStore) =>
  state.workspaceContext;
export const selectHasCompletedWelcomeTour = (state: IAppStore) =>
  state.hasCompletedWelcomeTour;
export const selectCurrentWorkingDirectory = (state: IAppStore) =>
  state.currentWorkingDirectory;

// ═══════════════════════════════════════════════════════════════
// NON-REACT HELPERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get workspace context (non-React)
 */
export function getWorkspaceContext(): any | null {
  return useAppStore.getState().workspaceContext;
}

/**
 * Set workspace context (non-React)
 */
export function setWorkspaceContext(context: any | null): void {
  useAppStore.getState().setWorkspaceContext(context);
}

/**
 * Check if welcome tour has been completed (non-React)
 */
export async function hasCompletedWelcomeTour(): Promise<boolean> {
  const state = useAppStore.getState();
  // If already loaded in state, return it
  if (state.hasCompletedWelcomeTour) {
    return true;
  }
  // Otherwise load from storage
  await state.loadWelcomeTourState();
  return useAppStore.getState().hasCompletedWelcomeTour;
}

/**
 * Get current working directory (non-React)
 */
export function getCurrentWorkingDirectory(): string | null {
  return useAppStore.getState().currentWorkingDirectory;
}

export function getSetupManager(): 'conda' | 'venv' | 'uv' | 'system' | null {
  return useAppStore.getState().setupManager;
}

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript/Lumino widgets)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to autoRun changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToAutoRun(
  callback: (autoRun: boolean) => void
): () => void {
  return useAppStore.subscribe(
    state => state.autoRun,
    (autoRun, prevAutoRun) => {
      if (autoRun !== prevAutoRun) {
        callback(autoRun);
      }
    }
  );
}

/**
 * Subscribe to isLauncherActive changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToLauncherActive(
  callback: (isLauncherActive: boolean) => void
): () => void {
  return useAppStore.subscribe(
    state => state.isLauncherActive,
    (isLauncherActive, prevIsLauncherActive) => {
      if (isLauncherActive !== prevIsLauncherActive) {
        callback(isLauncherActive);
      }
    }
  );
}
