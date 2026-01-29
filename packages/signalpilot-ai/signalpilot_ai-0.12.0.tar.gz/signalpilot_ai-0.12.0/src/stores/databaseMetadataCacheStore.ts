// src/stores/databaseMetadataCacheStore.ts
// PURPOSE: Manage database metadata caching state
// Replaces DatabaseMetadataCache.ts RxJS implementation

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { DatabaseTools } from '../BackendTools/DatabaseTools';
import { getToolService, getSettingsRegistry } from '../stores/servicesStore';
import { getDatabaseUrl as getSettingsDatabaseUrl } from '../stores/settingsStore';
import { StateDBCachingService } from '../utils/backendCaching';
import { CachingService, SETTING_KEYS } from '../utils/caching';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IDatabaseMetadata {
  schema: string;
  tableSchemas?: { [tableName: string]: any };
  lastUpdated: number;
  url: string;
}

export interface ICacheStatus {
  isCached: boolean;
  lastUpdated: number | null;
  isExpired: boolean;
}

// ═══════════════════════════════════════════════════════════════
// STATE INTERFACE
// ═══════════════════════════════════════════════════════════════

interface IDatabaseMetadataCacheState {
  cache: IDatabaseMetadata | null;
  isLoading: boolean;
  lastError: string | null;
}

interface IDatabaseMetadataCacheActions {
  // Core methods
  getMetadata: () => Promise<string | null>;
  getCachedMetadata: () => Promise<string | null>;
  getCachedTableSchemas: () => Promise<{ [tableName: string]: any } | null>;
  refreshMetadata: (url?: string) => Promise<string | null>;
  clearCache: () => void;

  // Initialization
  loadCacheFromStateDB: () => Promise<void>;
  initializeOnStartup: () => Promise<void>;

  // Event handlers
  onSettingsChanged: () => Promise<void>;
  onKernelReady: () => Promise<void>;

  // Status
  getCacheStatus: () => ICacheStatus;

  // Internal helpers (exposed for compatibility)
  getDatabaseUrl: () => Promise<string>;
  isCacheValid: (currentUrl: string) => boolean;
}

type IDatabaseMetadataCacheStore = IDatabaseMetadataCacheState &
  IDatabaseMetadataCacheActions;

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

const CACHE_DURATION_MS = 5 * 60 * 1000; // 5 minutes
const CACHE_KEY = 'database-metadata';

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

async function isKernelAvailable(): Promise<boolean> {
  try {
    const toolService = getToolService();
    const currentNotebook = toolService?.getCurrentNotebook();
    const kernel = currentNotebook?.kernel;

    if (!kernel) {
      return false;
    }

    if (kernel.status !== 'idle' && kernel.status !== 'busy') {
      return false;
    }

    return true;
  } catch (error) {
    return false;
  }
}

async function waitForKernel(maxWaitMs: number = 30000): Promise<boolean> {
  const startTime = Date.now();
  const checkInterval = 1000;

  while (Date.now() - startTime < maxWaitMs) {
    if (await isKernelAvailable()) {
      return true;
    }
    await new Promise(resolve => setTimeout(resolve, checkInterval));
  }

  return false;
}

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDatabaseMetadataCacheStore =
  create<IDatabaseMetadataCacheStore>()(
    devtools(
      subscribeWithSelector((set, get) => ({
        // ─────────────────────────────────────────────────────────────
        // Initial State
        // ─────────────────────────────────────────────────────────────
        cache: null,
        isLoading: false,
        lastError: null,

        // ─────────────────────────────────────────────────────────────
        // Get Database URL
        // ─────────────────────────────────────────────────────────────
        getDatabaseUrl: async () => {
          try {
            // Method 1: Try settings registry
            if (CachingService.isAvailable()) {
              try {
                const url = await CachingService.getStringSetting(
                  SETTING_KEYS.DATABASE_URL,
                  ''
                );
                if (url && url.trim() !== '') {
                  return url;
                }
              } catch (settingsError) {
                console.warn(
                  '[DatabaseMetadataCacheStore] Settings registry error:',
                  settingsError
                );
              }
            }

            // Method 2: Try settings store
            try {
              const settingsUrl = getSettingsDatabaseUrl();
              if (settingsUrl && settingsUrl.trim() !== '') {
                return settingsUrl;
              }
            } catch (settingsError) {
              console.warn(
                '[DatabaseMetadataCacheStore] Settings store error:',
                settingsError
              );
            }

            // Method 3: Try direct settings registry
            try {
              const settingsRegistry = getSettingsRegistry();
              if (settingsRegistry) {
                const settings = await settingsRegistry.load(
                  'signalpilot-ai:plugin'
                );
                const databaseUrl = settings.get('databaseUrl')
                  .composite as string;
                if (databaseUrl && databaseUrl.trim() !== '') {
                  return databaseUrl;
                }
              }
            } catch (directSettingsError) {
              console.warn(
                '[DatabaseMetadataCacheStore] Direct settings error:',
                directSettingsError
              );
            }

            return '';
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Unexpected error getting database URL:',
              error
            );
            return '';
          }
        },

        // ─────────────────────────────────────────────────────────────
        // Cache Validity Check
        // ─────────────────────────────────────────────────────────────
        isCacheValid: (currentUrl: string) => {
          const { cache } = get();
          if (!cache) return false;
          if (cache.url !== currentUrl) return false;
          const cacheAge = Date.now() - cache.lastUpdated;
          return cacheAge < CACHE_DURATION_MS;
        },

        // ─────────────────────────────────────────────────────────────
        // Core Methods
        // ─────────────────────────────────────────────────────────────
        getMetadata: async () => {
          const currentUrl = await get().getDatabaseUrl();
          if (!currentUrl || currentUrl.trim() === '') return null;

          if (get().isCacheValid(currentUrl)) {
            console.log('[DatabaseMetadataCacheStore] Using cached metadata');
            return get().cache!.schema;
          }

          return await get().refreshMetadata(currentUrl);
        },

        getCachedMetadata: async () => {
          const currentUrl = await get().getDatabaseUrl();
          if (!currentUrl || currentUrl.trim() === '') return null;

          if (get().isCacheValid(currentUrl)) {
            return get().cache!.schema;
          }

          return null;
        },

        getCachedTableSchemas: async () => {
          const currentUrl = await get().getDatabaseUrl();
          if (!currentUrl || currentUrl.trim() === '') return null;

          if (get().isCacheValid(currentUrl)) {
            return get().cache?.tableSchemas || null;
          }

          return null;
        },

        refreshMetadata: async (url?: string) => {
          const databaseUrl = url || (await get().getDatabaseUrl());

          if (!databaseUrl || databaseUrl.trim() === '') {
            get().clearCache();
            return null;
          }

          console.log(
            '[DatabaseMetadataCacheStore] Fetching fresh database metadata...'
          );
          set({ isLoading: true, lastError: null });

          const kernelAvailable = await isKernelAvailable();
          if (!kernelAvailable) {
            console.log(
              '[DatabaseMetadataCacheStore] Kernel not available, waiting...'
            );
            const kernelReady = await waitForKernel(15000);

            if (!kernelReady) {
              console.warn(
                '[DatabaseMetadataCacheStore] Kernel not available after waiting'
              );
              set({ isLoading: false });
              return null;
            }
          }

          try {
            const databaseTools = new DatabaseTools();
            const schemaResult =
              await databaseTools.getDatabaseMetadataAsText(databaseUrl);

            if (schemaResult && !schemaResult.startsWith('Error:')) {
              let parsedResult;
              try {
                parsedResult = JSON.parse(schemaResult);
              } catch (e) {
                parsedResult = { result: schemaResult };
              }

              const newCache: IDatabaseMetadata = {
                schema: parsedResult.result || schemaResult,
                tableSchemas: parsedResult.table_schemas || {},
                lastUpdated: Date.now(),
                url: databaseUrl
              };

              set({ cache: newCache, isLoading: false, lastError: null });

              // Save to StateDB
              try {
                await StateDBCachingService.setObjectValue(CACHE_KEY, newCache);
              } catch (saveError) {
                console.error(
                  '[DatabaseMetadataCacheStore] Failed to save cache:',
                  saveError
                );
              }

              console.log(
                '[DatabaseMetadataCacheStore] Database metadata cached successfully'
              );
              return newCache.schema;
            } else {
              console.warn(
                '[DatabaseMetadataCacheStore] Failed to fetch database metadata:',
                schemaResult
              );
              get().clearCache();
              set({
                isLoading: false,
                lastError: schemaResult || 'Unknown error'
              });
              return null;
            }
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Error fetching database metadata:',
              error
            );

            const errorString = error?.toString() || '';
            if (
              errorString.includes('kernel') ||
              errorString.includes('No kernel available')
            ) {
              set({ isLoading: false });
              return null;
            }

            get().clearCache();
            set({ isLoading: false, lastError: errorString });
            return null;
          }
        },

        clearCache: () => {
          set({ cache: null, lastError: null });
          void StateDBCachingService.removeValue(CACHE_KEY).catch(error => {
            console.error(
              '[DatabaseMetadataCacheStore] Failed to clear StateDB cache:',
              error
            );
          });
          console.log('[DatabaseMetadataCacheStore] Cache cleared');
        },

        // ─────────────────────────────────────────────────────────────
        // Initialization
        // ─────────────────────────────────────────────────────────────
        loadCacheFromStateDB: async () => {
          try {
            const cachedData =
              await StateDBCachingService.getObjectValue<IDatabaseMetadata | null>(
                CACHE_KEY,
                null
              );

            if (cachedData) {
              set({ cache: cachedData });
              console.log(
                '[DatabaseMetadataCacheStore] Loaded cache from StateDB'
              );
            }
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Failed to load cache from StateDB:',
              error
            );
          }
        },

        initializeOnStartup: async () => {
          console.log(
            '[DatabaseMetadataCacheStore] Starting initialization...'
          );

          // Load existing cache first
          await get().loadCacheFromStateDB();

          // Wait for settings to load
          await new Promise(resolve => setTimeout(resolve, 2000));

          try {
            const databaseUrl = await get().getDatabaseUrl();

            if (databaseUrl && databaseUrl.trim() !== '') {
              const kernelAvailable = await isKernelAvailable();
              if (kernelAvailable) {
                get()
                  .refreshMetadata(databaseUrl)
                  .catch(error => {
                    console.warn(
                      '[DatabaseMetadataCacheStore] Startup initialization failed:',
                      error
                    );
                  });
              } else {
                console.log(
                  '[DatabaseMetadataCacheStore] Kernel not available during initialization'
                );
              }
            }
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Error during initialization:',
              error
            );
          }
        },

        // ─────────────────────────────────────────────────────────────
        // Event Handlers
        // ─────────────────────────────────────────────────────────────
        onSettingsChanged: async () => {
          console.log(
            '[DatabaseMetadataCacheStore] Settings changed, checking database URL...'
          );
          try {
            const currentUrl = await get().getDatabaseUrl();
            const { cache } = get();

            if (cache && cache.url !== currentUrl) {
              console.log(
                '[DatabaseMetadataCacheStore] Database URL changed, clearing cache...'
              );
              get().clearCache();

              if (currentUrl && currentUrl.trim() !== '') {
                const kernelAvailable = await isKernelAvailable();
                if (kernelAvailable) {
                  get()
                    .refreshMetadata(currentUrl)
                    .catch(error => {
                      console.warn(
                        '[DatabaseMetadataCacheStore] Failed to refresh after settings change:',
                        error
                      );
                    });
                }
              }
            } else if (!cache && currentUrl && currentUrl.trim() !== '') {
              const kernelAvailable = await isKernelAvailable();
              if (kernelAvailable) {
                get()
                  .refreshMetadata(currentUrl)
                  .catch(error => {
                    console.warn(
                      '[DatabaseMetadataCacheStore] Failed to initialize after settings change:',
                      error
                    );
                  });
              }
            }
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Error handling settings change:',
              error
            );
          }
        },

        onKernelReady: async () => {
          console.log(
            '[DatabaseMetadataCacheStore] Kernel ready event received...'
          );

          try {
            const databaseUrl = await get().getDatabaseUrl();

            if (databaseUrl && databaseUrl.trim() !== '') {
              if (!get().cache || !get().isCacheValid(databaseUrl)) {
                console.log(
                  '[DatabaseMetadataCacheStore] Refreshing metadata now that kernel is ready...'
                );
                await get().refreshMetadata(databaseUrl);
              }
            }
          } catch (error) {
            console.error(
              '[DatabaseMetadataCacheStore] Error handling kernel ready event:',
              error
            );
          }
        },

        // ─────────────────────────────────────────────────────────────
        // Status
        // ─────────────────────────────────────────────────────────────
        getCacheStatus: () => {
          const { cache } = get();
          if (!cache) {
            return { isCached: false, lastUpdated: null, isExpired: false };
          }

          const cacheAge = Date.now() - cache.lastUpdated;
          const isExpired = cacheAge >= CACHE_DURATION_MS;

          return {
            isCached: true,
            lastUpdated: cache.lastUpdated,
            isExpired
          };
        }
      })),
      { name: 'DatabaseMetadataCacheStore' }
    )
  );

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectCache = (state: IDatabaseMetadataCacheStore) => state.cache;
export const selectIsLoading = (state: IDatabaseMetadataCacheStore) =>
  state.isLoading;
export const selectLastError = (state: IDatabaseMetadataCacheStore) =>
  state.lastError;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to metadata cache changes.
 */
export function subscribeToMetadataChanges(
  callback: (cache: IDatabaseMetadata | null) => void
): () => void {
  return useDatabaseMetadataCacheStore.subscribe(
    state => state.cache,
    callback
  );
}

// ═══════════════════════════════════════════════════════════════
// CONVENIENCE ACCESSORS
// ═══════════════════════════════════════════════════════════════

/**
 * Get the current store state directly.
 */
export function getDatabaseMetadataCacheState() {
  return useDatabaseMetadataCacheStore.getState();
}

// ═══════════════════════════════════════════════════════════════
// AUTO-REFRESH MANAGER (module-level)
// ═══════════════════════════════════════════════════════════════

let refreshTimer: NodeJS.Timeout | null = null;

export function startAutoRefresh(): void {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }

  refreshTimer = setInterval(async () => {
    try {
      const state = useDatabaseMetadataCacheStore.getState();
      const currentUrl = await state.getDatabaseUrl();

      if (currentUrl && currentUrl.trim() !== '' && state.cache) {
        const kernelAvailable = await isKernelAvailable();
        if (kernelAvailable) {
          console.log(
            '[DatabaseMetadataCacheStore] Auto-refreshing database metadata...'
          );
          await state.refreshMetadata(currentUrl);
        }
      }
    } catch (error) {
      console.warn('[DatabaseMetadataCacheStore] Auto-refresh failed:', error);
    }
  }, CACHE_DURATION_MS);
}

export function stopAutoRefresh(): void {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

// ═══════════════════════════════════════════════════════════════
// COMPATIBILITY WRAPPER (for easier migration)
// ═══════════════════════════════════════════════════════════════

/**
 * Compatibility wrapper that mirrors the old DatabaseMetadataCache singleton API.
 */
export const DatabaseMetadataCache = {
  getInstance: () => ({
    getMetadata: () => useDatabaseMetadataCacheStore.getState().getMetadata(),
    getCachedMetadata: () =>
      useDatabaseMetadataCacheStore.getState().getCachedMetadata(),
    getCachedTableSchemas: () =>
      useDatabaseMetadataCacheStore.getState().getCachedTableSchemas(),
    refreshMetadata: (url?: string) =>
      useDatabaseMetadataCacheStore.getState().refreshMetadata(url),
    clearCache: () => useDatabaseMetadataCacheStore.getState().clearCache(),
    getCacheStatus: () =>
      useDatabaseMetadataCacheStore.getState().getCacheStatus(),
    initializeOnStartup: () =>
      useDatabaseMetadataCacheStore.getState().initializeOnStartup(),
    onSettingsChanged: () =>
      useDatabaseMetadataCacheStore.getState().onSettingsChanged(),
    onKernelReady: () =>
      useDatabaseMetadataCacheStore.getState().onKernelReady(),
    stopAutoRefresh,
    dispose: () => {
      stopAutoRefresh();
      useDatabaseMetadataCacheStore.getState().clearCache();
    },
    // Observable compatibility
    metadata$: {
      subscribe: (callback: (cache: IDatabaseMetadata | null) => void) => {
        const unsubscribe = subscribeToMetadataChanges(callback);
        return { unsubscribe };
      }
    }
  })
};

// Initialize auto-refresh when module loads
startAutoRefresh();
