// src/stores/planStateStore.ts
// PURPOSE: Plan State Display - manages the plan processing state shown above chat input
// Replaces the ReactWidget-based PlanStateDisplay with a pure Zustand store

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Interface for the Plan state
 */
export interface IPlanState {
  isVisible: boolean;
  currentStep?: string;
  nextStep?: string;
  source?: string;
  isLoading: boolean;
}

interface IPlanStateActions {
  /**
   * Update the plan state with current and next step information
   */
  updatePlan: (
    currentStep?: string,
    nextStep?: string,
    source?: string,
    isLoading?: boolean
  ) => void;

  /**
   * Show the plan state display
   */
  show: () => void;

  /**
   * Hide the plan state display
   */
  hide: () => void;

  /**
   * Set the loading state
   */
  setLoading: (loading: boolean) => void;

  /**
   * Update only the current step text
   */
  updateCurrentStep: (currentStep: string) => void;

  /**
   * Update only the next step text
   */
  updateNextStep: (nextStep: string) => void;

  /**
   * Update only the source content
   */
  updateSource: (source: string) => void;

  /**
   * Reset to initial state
   */
  reset: () => void;
}

type IPlanStateStore = IPlanState & IPlanStateActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IPlanState = {
  isVisible: false,
  currentStep: undefined,
  nextStep: undefined,
  source: undefined,
  isLoading: false
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const usePlanStateStore = create<IPlanStateStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      updatePlan: (
        currentStep?: string,
        nextStep?: string,
        source?: string,
        isLoading?: boolean
      ) => {
        const shouldShow = !!(currentStep || nextStep);

        set({
          isVisible: shouldShow,
          currentStep,
          nextStep,
          source,
          isLoading: isLoading ?? !!currentStep
        });
      },

      show: () =>
        set({
          isVisible: true
        }),

      hide: () =>
        set({
          isVisible: false
        }),

      setLoading: (loading: boolean) =>
        set({
          isLoading: loading
        }),

      updateCurrentStep: (currentStep: string) =>
        set({
          currentStep,
          isVisible: true
        }),

      updateNextStep: (nextStep: string) =>
        set({
          nextStep
        }),

      updateSource: (source: string) =>
        set({
          source
        }),

      reset: () => set(initialState)
    })),
    { name: 'PlanStateStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectPlanState = (state: IPlanStateStore): IPlanState => ({
  isVisible: state.isVisible,
  currentStep: state.currentStep,
  nextStep: state.nextStep,
  source: state.source,
  isLoading: state.isLoading
});

export const selectPlanIsVisible = (state: IPlanStateStore) => state.isVisible;
export const selectPlanCurrentStep = (state: IPlanStateStore) =>
  state.currentStep;
export const selectPlanNextStep = (state: IPlanStateStore) => state.nextStep;
export const selectPlanSource = (state: IPlanStateStore) => state.source;
export const selectPlanIsLoading = (state: IPlanStateStore) => state.isLoading;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript/Lumino widgets)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to plan state visibility changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToPlanVisibility(
  callback: (isVisible: boolean) => void
): () => void {
  return usePlanStateStore.subscribe(
    state => state.isVisible,
    (isVisible, prevIsVisible) => {
      if (isVisible !== prevIsVisible) {
        callback(isVisible);
      }
    }
  );
}

/**
 * Subscribe to full plan state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToPlanState(
  callback: (state: IPlanState) => void
): () => void {
  return usePlanStateStore.subscribe(
    state => selectPlanState(state),
    (current, prev) => {
      // Only trigger if something actually changed
      if (
        current.isVisible !== prev.isVisible ||
        current.currentStep !== prev.currentStep ||
        current.nextStep !== prev.nextStep ||
        current.source !== prev.source ||
        current.isLoading !== prev.isLoading
      ) {
        callback(current);
      }
    }
  );
}

/**
 * Subscribe to plan loading state changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToPlanLoading(
  callback: (isLoading: boolean) => void
): () => void {
  return usePlanStateStore.subscribe(
    state => state.isLoading,
    (isLoading, prevIsLoading) => {
      if (isLoading !== prevIsLoading) {
        callback(isLoading);
      }
    }
  );
}
