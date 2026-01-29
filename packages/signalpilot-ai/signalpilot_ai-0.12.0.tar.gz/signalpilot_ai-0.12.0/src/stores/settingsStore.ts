// src/stores/settingsStore.ts
// PURPOSE: User preferences and API configuration
// ~80 lines

import { create } from 'zustand';
import { devtools, persist, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface ISettingsState {
  // UI Preferences
  theme: string;
  tokenMode: boolean;
  tabAutocompleteEnabled: boolean;

  // Claude API Configuration
  claudeApiKey: string;
  claudeModelId: string;
  claudeModelUrl: string;

  // Database
  databaseUrl: string;
}

interface ISettingsActions {
  // Bulk updates
  updateSettings: (settings: Partial<ISettingsState>) => void;

  // Individual setters
  setTheme: (theme: string) => void;
  setTokenMode: (enabled: boolean) => void;
  setTabAutocompleteEnabled: (enabled: boolean) => void;
  setClaudeApiKey: (key: string) => void;
  setClaudeModelId: (modelId: string) => void;
  setClaudeModelUrl: (url: string) => void;
  setDatabaseUrl: (url: string) => void;

  // Convenience getters for non-React code
  getClaudeSettings: () => {
    claudeApiKey: string;
    claudeModelId: string;
    claudeModelUrl: string;
    databaseUrl: string;
    tabAutocompleteEnabled: boolean;
  };
}

type ISettingsStore = ISettingsState & ISettingsActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useSettingsStore = create<ISettingsStore>()(
  devtools(
    subscribeWithSelector(
      persist(
        (set, get) => ({
          // ─────────────────────────────────────────────────────────────
          // Initial State
          // ─────────────────────────────────────────────────────────────
          theme: 'light',
          tokenMode: false,
          tabAutocompleteEnabled: false,
          claudeApiKey: '',
          claudeModelId: 'claude-opus-4-5',
          claudeModelUrl: 'https://sage.alpinex.ai:8760',
          databaseUrl: '',

          // ─────────────────────────────────────────────────────────────
          // Actions
          // ─────────────────────────────────────────────────────────────
          updateSettings: settings => set(state => ({ ...state, ...settings })),

          setTheme: theme => set({ theme }),
          setTokenMode: enabled => set({ tokenMode: enabled }),
          setTabAutocompleteEnabled: enabled =>
            set({ tabAutocompleteEnabled: enabled }),
          setClaudeApiKey: key => set({ claudeApiKey: key }),
          setClaudeModelId: modelId => set({ claudeModelId: modelId }),
          setClaudeModelUrl: url => set({ claudeModelUrl: url }),
          setDatabaseUrl: url => set({ databaseUrl: url }),

          // Convenience getter for non-React code
          getClaudeSettings: () => {
            const state = get();
            return {
              claudeApiKey: state.claudeApiKey,
              claudeModelId: state.claudeModelId,
              claudeModelUrl: state.claudeModelUrl,
              databaseUrl: state.databaseUrl,
              tabAutocompleteEnabled: state.tabAutocompleteEnabled
            };
          }
        }),
        {
          name: 'sage-settings-store',
          // Only persist these specific fields to localStorage
          partialize: state => ({
            theme: state.theme,
            tokenMode: state.tokenMode,
            tabAutocompleteEnabled: state.tabAutocompleteEnabled,
            claudeApiKey: state.claudeApiKey,
            claudeModelId: state.claudeModelId,
            claudeModelUrl: state.claudeModelUrl,
            databaseUrl: state.databaseUrl
          })
        }
      )
    ),
    { name: 'SettingsStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectTheme = (state: ISettingsStore) => state.theme;
export const selectTokenMode = (state: ISettingsStore) => state.tokenMode;
export const selectTabAutocomplete = (state: ISettingsStore) =>
  state.tabAutocompleteEnabled;
export const selectClaudeApiKey = (state: ISettingsStore) => state.claudeApiKey;
export const selectClaudeModelId = (state: ISettingsStore) =>
  state.claudeModelId;
export const selectClaudeModelUrl = (state: ISettingsStore) =>
  state.claudeModelUrl;
export const selectDatabaseUrl = (state: ISettingsStore) => state.databaseUrl;

// ═══════════════════════════════════════════════════════════════
// NON-REACT HELPERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get Claude settings from the store (non-React)
 */
export function getClaudeSettings() {
  return useSettingsStore.getState().getClaudeSettings();
}

/**
 * Get Claude API key from the store (non-React)
 */
export function getClaudeApiKey(): string {
  return useSettingsStore.getState().claudeApiKey;
}

/**
 * Get Claude model URL from the store (non-React)
 */
export function getClaudeModelUrl(): string {
  return useSettingsStore.getState().claudeModelUrl;
}

/**
 * Get Claude model ID from the store (non-React)
 */
export function getClaudeModelId(): string {
  return useSettingsStore.getState().claudeModelId;
}

/**
 * Get database URL from the store (non-React)
 */
export function getDatabaseUrl(): string {
  return useSettingsStore.getState().databaseUrl;
}

/**
 * Update Claude settings (non-React)
 */
export function updateClaudeSettings(settings: {
  claudeApiKey?: string;
  claudeModelId?: string;
  claudeModelUrl?: string;
  databaseUrl?: string;
}) {
  useSettingsStore.getState().updateSettings(settings);
}
