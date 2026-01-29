/**
 * LoadingStateStore
 *
 * Zustand store for managing application-wide loading states during initialization.
 * This store enables the UI to show appropriate loading indicators (spinners, skeletons)
 * while different parts of the application initialize in the background.
 *
 * Key Design Principles:
 * - Never block the main thread
 * - Show immediate UI feedback
 * - Track granular loading states for different subsystems
 * - Support progressive loading (show what's ready, indicate what's loading)
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Initialization phases for the application
 */
export type InitPhase =
  | 'not_started'
  | 'shell_ready' // UI shell is visible
  | 'core_ready' // Core services initialized
  | 'background_loading' // Background tasks running
  | 'fully_ready'; // Everything loaded

/**
 * Individual feature loading states
 */
export interface IFeatureLoadingStates {
  // Core services
  coreServices: boolean;
  toolService: boolean;
  notebookContext: boolean;

  // Chat system
  chatContainer: boolean;
  chatHistory: boolean;
  messageList: boolean;

  // Context loaders (can be lazy-loaded)
  databaseContext: boolean;
  datasetContext: boolean;
  snippetContext: boolean;

  // Widgets
  settingsWidget: boolean;
  diffNavigation: boolean;
  fileExplorer: boolean;

  // Authentication & Config
  authentication: boolean;
  configuration: boolean;
}

/**
 * Loading state with optional progress
 */
export interface ILoadingDetail {
  isLoading: boolean;
  progress?: number; // 0-100, optional
  message?: string;
  error?: string;
}

/**
 * Full loading state store
 */
export interface ILoadingState {
  // Overall initialization phase
  phase: InitPhase;

  // Feature-level loading states
  features: IFeatureLoadingStates;

  // Detailed loading info for specific operations
  details: {
    chatHistoryLoad: ILoadingDetail;
    databaseContextLoad: ILoadingDetail;
    initialNotebookSwitch: ILoadingDetail;
  };

  // Timing metrics (for debugging/telemetry)
  metrics: {
    activateStart?: number;
    shellReadyAt?: number;
    coreReadyAt?: number;
    fullyReadyAt?: number;
  };
}

/**
 * Loading state actions
 */
export interface ILoadingStateActions {
  // Phase transitions
  setPhase: (phase: InitPhase) => void;
  advanceToShellReady: () => void;
  advanceToCoreReady: () => void;
  advanceToBackgroundLoading: () => void;
  advanceToFullyReady: () => void;

  // Feature loading updates
  setFeatureLoading: (
    feature: keyof IFeatureLoadingStates,
    isLoading: boolean
  ) => void;
  setFeatureReady: (feature: keyof IFeatureLoadingStates) => void;
  setMultipleFeaturesReady: (features: (keyof IFeatureLoadingStates)[]) => void;

  // Detailed loading updates
  setChatHistoryLoading: (detail: Partial<ILoadingDetail>) => void;
  setDatabaseContextLoading: (detail: Partial<ILoadingDetail>) => void;
  setInitialNotebookSwitchLoading: (detail: Partial<ILoadingDetail>) => void;

  // Metrics
  recordActivateStart: () => void;
  recordMetric: (
    metric: keyof ILoadingState['metrics'],
    timestamp?: number
  ) => void;

  // Utility
  isFeatureReady: (feature: keyof IFeatureLoadingStates) => boolean;
  areAllFeaturesReady: (features: (keyof IFeatureLoadingStates)[]) => boolean;
  getLoadingFeatures: () => (keyof IFeatureLoadingStates)[];

  // Reset
  reset: () => void;
}

type ILoadingStateStore = ILoadingState & ILoadingStateActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialFeatureStates: IFeatureLoadingStates = {
  coreServices: true,
  toolService: true,
  notebookContext: true,
  chatContainer: true,
  chatHistory: true,
  messageList: true,
  databaseContext: true,
  datasetContext: true,
  snippetContext: true,
  settingsWidget: true,
  diffNavigation: true,
  fileExplorer: true,
  authentication: true,
  configuration: true
};

const initialLoadingDetail: ILoadingDetail = {
  isLoading: false,
  progress: undefined,
  message: undefined,
  error: undefined
};

const initialState: ILoadingState = {
  phase: 'not_started',
  features: initialFeatureStates,
  details: {
    chatHistoryLoad: { ...initialLoadingDetail },
    databaseContextLoad: { ...initialLoadingDetail },
    initialNotebookSwitch: { ...initialLoadingDetail }
  },
  metrics: {}
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useLoadingStateStore = create<ILoadingStateStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Phase Transitions
      // ─────────────────────────────────────────────────────────────

      setPhase: (phase: InitPhase) => {
        set({ phase }, false, 'setPhase');
      },

      advanceToShellReady: () => {
        set(
          state => ({
            phase: 'shell_ready',
            metrics: {
              ...state.metrics,
              shellReadyAt: performance.now()
            }
          }),
          false,
          'advanceToShellReady'
        );
        console.log('[LoadingState] Phase: shell_ready');
      },

      advanceToCoreReady: () => {
        set(
          state => ({
            phase: 'core_ready',
            metrics: {
              ...state.metrics,
              coreReadyAt: performance.now()
            }
          }),
          false,
          'advanceToCoreReady'
        );
        console.log('[LoadingState] Phase: core_ready');
      },

      advanceToBackgroundLoading: () => {
        set(
          { phase: 'background_loading' },
          false,
          'advanceToBackgroundLoading'
        );
        console.log('[LoadingState] Phase: background_loading');
      },

      advanceToFullyReady: () => {
        set(
          state => ({
            phase: 'fully_ready',
            metrics: {
              ...state.metrics,
              fullyReadyAt: performance.now()
            }
          }),
          false,
          'advanceToFullyReady'
        );

        // Log timing summary
        const { metrics } = get();
        if (metrics.activateStart) {
          const totalTime = performance.now() - metrics.activateStart;
          const shellTime = metrics.shellReadyAt
            ? metrics.shellReadyAt - metrics.activateStart
            : 'N/A';
          const coreTime = metrics.coreReadyAt
            ? metrics.coreReadyAt - metrics.activateStart
            : 'N/A';
          console.log(
            `[LoadingState] Phase: fully_ready | Total: ${totalTime.toFixed(0)}ms | Shell: ${shellTime}ms | Core: ${coreTime}ms`
          );
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Feature Loading Updates
      // ─────────────────────────────────────────────────────────────

      setFeatureLoading: (
        feature: keyof IFeatureLoadingStates,
        isLoading: boolean
      ) => {
        set(
          state => ({
            features: {
              ...state.features,
              [feature]: isLoading
            }
          }),
          false,
          `setFeatureLoading:${feature}`
        );
      },

      setFeatureReady: (feature: keyof IFeatureLoadingStates) => {
        set(
          state => ({
            features: {
              ...state.features,
              [feature]: false
            }
          }),
          false,
          `setFeatureReady:${feature}`
        );
        console.log(`[LoadingState] Feature ready: ${feature}`);
      },

      setMultipleFeaturesReady: (features: (keyof IFeatureLoadingStates)[]) => {
        set(
          state => {
            const newFeatures = { ...state.features };
            features.forEach(feature => {
              newFeatures[feature] = false;
            });
            return { features: newFeatures };
          },
          false,
          'setMultipleFeaturesReady'
        );
        console.log(`[LoadingState] Features ready: ${features.join(', ')}`);
      },

      // ─────────────────────────────────────────────────────────────
      // Detailed Loading Updates
      // ─────────────────────────────────────────────────────────────

      setChatHistoryLoading: (detail: Partial<ILoadingDetail>) => {
        set(
          state => ({
            details: {
              ...state.details,
              chatHistoryLoad: {
                ...state.details.chatHistoryLoad,
                ...detail
              }
            }
          }),
          false,
          'setChatHistoryLoading'
        );
      },

      setDatabaseContextLoading: (detail: Partial<ILoadingDetail>) => {
        set(
          state => ({
            details: {
              ...state.details,
              databaseContextLoad: {
                ...state.details.databaseContextLoad,
                ...detail
              }
            }
          }),
          false,
          'setDatabaseContextLoading'
        );
      },

      setInitialNotebookSwitchLoading: (detail: Partial<ILoadingDetail>) => {
        set(
          state => ({
            details: {
              ...state.details,
              initialNotebookSwitch: {
                ...state.details.initialNotebookSwitch,
                ...detail
              }
            }
          }),
          false,
          'setInitialNotebookSwitchLoading'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Metrics
      // ─────────────────────────────────────────────────────────────

      recordActivateStart: () => {
        set(
          state => ({
            phase: 'not_started',
            metrics: {
              ...state.metrics,
              activateStart: performance.now()
            }
          }),
          false,
          'recordActivateStart'
        );
        console.log('[LoadingState] Activation started');
      },

      recordMetric: (
        metric: keyof ILoadingState['metrics'],
        timestamp?: number
      ) => {
        set(
          state => ({
            metrics: {
              ...state.metrics,
              [metric]: timestamp ?? performance.now()
            }
          }),
          false,
          `recordMetric:${metric}`
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Utility
      // ─────────────────────────────────────────────────────────────

      isFeatureReady: (feature: keyof IFeatureLoadingStates) => {
        return !get().features[feature];
      },

      areAllFeaturesReady: (features: (keyof IFeatureLoadingStates)[]) => {
        const state = get();
        return features.every(feature => !state.features[feature]);
      },

      getLoadingFeatures: () => {
        const state = get();
        return (
          Object.keys(state.features) as (keyof IFeatureLoadingStates)[]
        ).filter(feature => state.features[feature]);
      },

      // ─────────────────────────────────────────────────────────────
      // Reset
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set({ ...initialState }, false, 'reset');
      }
    })),
    { name: 'LoadingStateStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectPhase = (state: ILoadingStateStore) => state.phase;
export const selectFeatures = (state: ILoadingStateStore) => state.features;
export const selectDetails = (state: ILoadingStateStore) => state.details;
export const selectMetrics = (state: ILoadingStateStore) => state.metrics;

// Computed selectors
export const selectIsShellReady = (state: ILoadingStateStore) =>
  state.phase !== 'not_started';
export const selectIsCoreReady = (state: ILoadingStateStore) =>
  state.phase === 'core_ready' ||
  state.phase === 'background_loading' ||
  state.phase === 'fully_ready';
export const selectIsFullyReady = (state: ILoadingStateStore) =>
  state.phase === 'fully_ready';

// Feature-specific selectors
export const selectIsChatHistoryLoading = (state: ILoadingStateStore) =>
  state.features.chatHistory;
export const selectIsDatabaseContextLoading = (state: ILoadingStateStore) =>
  state.features.databaseContext;
export const selectIsMessageListLoading = (state: ILoadingStateStore) =>
  state.features.messageList;

// Detail selectors
export const selectChatHistoryLoadDetail = (state: ILoadingStateStore) =>
  state.details.chatHistoryLoad;
export const selectDatabaseContextLoadDetail = (state: ILoadingStateStore) =>
  state.details.databaseContextLoad;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getLoadingState = () => useLoadingStateStore.getState();

/**
 * Subscribe to phase changes
 */
export const subscribeToPhase = (callback: (phase: InitPhase) => void) => {
  return useLoadingStateStore.subscribe(state => state.phase, callback);
};

/**
 * Subscribe to a specific feature loading state
 */
export const subscribeToFeatureLoading = (
  feature: keyof IFeatureLoadingStates,
  callback: (isLoading: boolean) => void
) => {
  return useLoadingStateStore.subscribe(
    state => state.features[feature],
    callback
  );
};

/**
 * Wait for a feature to be ready
 */
export const waitForFeature = (
  feature: keyof IFeatureLoadingStates
): Promise<void> => {
  return new Promise(resolve => {
    const state = useLoadingStateStore.getState();
    if (!state.features[feature]) {
      resolve();
      return;
    }

    const unsubscribe = useLoadingStateStore.subscribe(
      s => s.features[feature],
      isLoading => {
        if (!isLoading) {
          unsubscribe();
          resolve();
        }
      }
    );
  });
};

/**
 * Wait for core services to be ready
 */
export const waitForCoreReady = (): Promise<void> => {
  return new Promise(resolve => {
    const state = useLoadingStateStore.getState();
    if (
      state.phase === 'core_ready' ||
      state.phase === 'background_loading' ||
      state.phase === 'fully_ready'
    ) {
      resolve();
      return;
    }

    const unsubscribe = useLoadingStateStore.subscribe(
      s => s.phase,
      phase => {
        if (
          phase === 'core_ready' ||
          phase === 'background_loading' ||
          phase === 'fully_ready'
        ) {
          unsubscribe();
          resolve();
        }
      }
    );
  });
};
