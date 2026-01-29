/**
 * LazyContextLoader
 *
 * Provides on-demand, non-blocking loading of expensive context data
 * (databases, datasets, tables) instead of loading everything at startup.
 *
 * Key Features:
 * - Lazy loading: Data is only fetched when first requested
 * - Caching: Results are cached to avoid repeated expensive operations
 * - Loading states: Integrates with LoadingStateStore for UI feedback
 * - Background pre-fetching: Can pre-load data when the app is idle
 * - Stale-while-revalidate: Returns cached data immediately, refreshes in background
 */

import {
  useLoadingStateStore,
  getLoadingState
} from '../../stores/loadingStateStore';
import { IMentionContext } from './ChatContextLoaders';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export type ContextType =
  | 'databases'
  | 'datasets'
  | 'tables'
  | 'snippets'
  | 'variables'
  | 'cells';

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  isStale: boolean;
}

interface LoadingState {
  isLoading: boolean;
  promise: Promise<IMentionContext[]> | null;
}

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════

// Cache TTL in milliseconds (5 minutes for databases, 2 minutes for others)
const CACHE_TTL: Record<ContextType, number> = {
  databases: 5 * 60 * 1000,
  datasets: 2 * 60 * 1000,
  tables: 5 * 60 * 1000,
  snippets: 30 * 1000,
  variables: 10 * 1000,
  cells: 5 * 1000
};

// ═══════════════════════════════════════════════════════════════
// LAZY CONTEXT LOADER CLASS
// ═══════════════════════════════════════════════════════════════

class LazyContextLoaderImpl {
  private cache = new Map<ContextType, CacheEntry<IMentionContext[]>>();
  private loadingStates = new Map<ContextType, LoadingState>();
  private loaders = new Map<ContextType, () => Promise<IMentionContext[]>>();
  private isInitialized = false;

  /**
   * Register a loader function for a context type
   */
  registerLoader(
    type: ContextType,
    loader: () => Promise<IMentionContext[]>
  ): void {
    this.loaders.set(type, loader);
    this.loadingStates.set(type, { isLoading: false, promise: null });
  }

  /**
   * Initialize the loader with ChatContextLoaders instance
   */
  initialize(loaderInstance: {
    loadDatabases: () => Promise<IMentionContext[]>;
    loadDatasets: (path?: string) => Promise<IMentionContext[]>;
    loadTables: () => Promise<IMentionContext[]>;
    loadSnippets: () => Promise<IMentionContext[]>;
    loadVariables: () => Promise<IMentionContext[]>;
    loadCells: () => Promise<IMentionContext[]>;
  }): void {
    if (this.isInitialized) {
      console.log('[LazyContextLoader] Already initialized');
      return;
    }

    this.registerLoader('databases', () => loaderInstance.loadDatabases());
    this.registerLoader('datasets', () => loaderInstance.loadDatasets());
    this.registerLoader('tables', () => loaderInstance.loadTables());
    this.registerLoader('snippets', () => loaderInstance.loadSnippets());
    this.registerLoader('variables', () => loaderInstance.loadVariables());
    this.registerLoader('cells', () => loaderInstance.loadCells());

    this.isInitialized = true;
    console.log('[LazyContextLoader] Initialized with all loaders');
  }

  /**
   * Get cached data if available and not expired
   */
  private getCached(type: ContextType): CacheEntry<IMentionContext[]> | null {
    const entry = this.cache.get(type);
    if (!entry) return null;

    const ttl = CACHE_TTL[type];
    const age = Date.now() - entry.timestamp;
    const isExpired = age > ttl;

    if (isExpired) {
      entry.isStale = true;
    }

    return entry;
  }

  /**
   * Set cache entry
   */
  private setCache(type: ContextType, data: IMentionContext[]): void {
    this.cache.set(type, {
      data,
      timestamp: Date.now(),
      isStale: false
    });
  }

  /**
   * Update loading state in the global store
   */
  private updateGlobalLoadingState(
    type: ContextType,
    isLoading: boolean
  ): void {
    const featureMap: Partial<
      Record<ContextType, keyof ReturnType<typeof getLoadingState>['features']>
    > = {
      databases: 'databaseContext',
      datasets: 'datasetContext',
      snippets: 'snippetContext'
    };

    const feature = featureMap[type];
    if (feature) {
      useLoadingStateStore.getState().setFeatureLoading(feature, isLoading);
    }
  }

  /**
   * Load context data with caching and deduplication
   *
   * @param type - The type of context to load
   * @param options - Loading options
   * @returns Promise resolving to the context data
   */
  async load(
    type: ContextType,
    options: {
      forceRefresh?: boolean;
      staleWhileRevalidate?: boolean;
    } = {}
  ): Promise<IMentionContext[]> {
    const { forceRefresh = false, staleWhileRevalidate = true } = options;

    // Check if we have a valid cache entry
    const cached = this.getCached(type);

    // If we have fresh cache and not forcing refresh, return immediately
    if (cached && !cached.isStale && !forceRefresh) {
      console.log(`[LazyContextLoader] Returning fresh cache for ${type}`);
      return cached.data;
    }

    // If we have stale cache and staleWhileRevalidate is enabled,
    // return stale data immediately and refresh in background
    if (cached && cached.isStale && staleWhileRevalidate) {
      console.log(
        `[LazyContextLoader] Returning stale cache for ${type}, refreshing in background`
      );
      this.refreshInBackground(type);
      return cached.data;
    }

    // Check if we're already loading this type
    const loadingState = this.loadingStates.get(type);
    if (loadingState?.isLoading && loadingState.promise) {
      console.log(
        `[LazyContextLoader] Already loading ${type}, waiting for existing promise`
      );
      return loadingState.promise;
    }

    // Start loading
    return this.doLoad(type);
  }

  /**
   * Actually perform the load operation
   */
  private async doLoad(type: ContextType): Promise<IMentionContext[]> {
    const loader = this.loaders.get(type);
    if (!loader) {
      console.warn(
        `[LazyContextLoader] No loader registered for type: ${type}`
      );
      return [];
    }

    // Update loading state
    this.updateGlobalLoadingState(type, true);

    const promise = (async () => {
      try {
        console.log(`[LazyContextLoader] Loading ${type}...`);
        const startTime = performance.now();

        const data = await loader();

        const elapsed = performance.now() - startTime;
        console.log(
          `[LazyContextLoader] Loaded ${type} in ${elapsed.toFixed(0)}ms (${data.length} items)`
        );

        // Cache the result
        this.setCache(type, data);

        return data;
      } catch (error) {
        console.error(`[LazyContextLoader] Error loading ${type}:`, error);

        // Return cached data on error if available
        const cached = this.cache.get(type);
        if (cached) {
          console.log(
            `[LazyContextLoader] Returning cached data after error for ${type}`
          );
          return cached.data;
        }

        return [];
      } finally {
        // Update loading states
        this.loadingStates.set(type, { isLoading: false, promise: null });
        this.updateGlobalLoadingState(type, false);
      }
    })();

    // Store the promise for deduplication
    this.loadingStates.set(type, { isLoading: true, promise });

    return promise;
  }

  /**
   * Refresh data in the background without blocking
   */
  private refreshInBackground(type: ContextType): void {
    // Use requestIdleCallback for true background loading
    if ('requestIdleCallback' in window) {
      (window as Window).requestIdleCallback(
        () => {
          void this.doLoad(type);
        },
        { timeout: 5000 }
      );
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(() => {
        void this.doLoad(type);
      }, 100);
    }
  }

  /**
   * Pre-load multiple context types in the background
   * Call this during idle time to warm the cache
   */
  prefetch(types: ContextType[]): void {
    console.log(`[LazyContextLoader] Prefetching: ${types.join(', ')}`);

    // Schedule prefetch during idle time
    if ('requestIdleCallback' in window) {
      (window as Window).requestIdleCallback(
        () => {
          for (const type of types) {
            // Only prefetch if not already cached
            if (!this.getCached(type)) {
              void this.load(type, { staleWhileRevalidate: false });
            }
          }
        },
        { timeout: 10000 }
      );
    } else {
      setTimeout(() => {
        for (const type of types) {
          if (!this.getCached(type)) {
            void this.load(type, { staleWhileRevalidate: false });
          }
        }
      }, 500);
    }
  }

  /**
   * Invalidate cache for a specific type
   */
  invalidate(type: ContextType): void {
    this.cache.delete(type);
    console.log(`[LazyContextLoader] Invalidated cache for ${type}`);
  }

  /**
   * Invalidate all caches
   */
  invalidateAll(): void {
    this.cache.clear();
    console.log('[LazyContextLoader] Invalidated all caches');
  }

  /**
   * Check if a context type is currently loading
   */
  isLoading(type: ContextType): boolean {
    return this.loadingStates.get(type)?.isLoading ?? false;
  }

  /**
   * Check if a context type has cached data
   */
  hasCachedData(type: ContextType): boolean {
    return this.cache.has(type);
  }

  /**
   * Get cache status for debugging
   */
  getCacheStatus(): Record<
    ContextType,
    { cached: boolean; age: number; isStale: boolean }
  > {
    const status: Record<
      string,
      { cached: boolean; age: number; isStale: boolean }
    > = {};

    for (const type of [
      'databases',
      'datasets',
      'tables',
      'snippets',
      'variables',
      'cells'
    ] as ContextType[]) {
      const entry = this.cache.get(type);
      status[type] = {
        cached: !!entry,
        age: entry ? Date.now() - entry.timestamp : 0,
        isStale: entry?.isStale ?? false
      };
    }

    return status as Record<
      ContextType,
      { cached: boolean; age: number; isStale: boolean }
    >;
  }

  /**
   * Reset the loader (for testing)
   */
  reset(): void {
    this.cache.clear();
    this.loadingStates.clear();
    this.loaders.clear();
    this.isInitialized = false;
    console.log('[LazyContextLoader] Reset');
  }
}

// ═══════════════════════════════════════════════════════════════
// SINGLETON EXPORT
// ═══════════════════════════════════════════════════════════════

export const LazyContextLoader = new LazyContextLoaderImpl();

// ═══════════════════════════════════════════════════════════════
// UTILITY HOOKS FOR REACT COMPONENTS
// ═══════════════════════════════════════════════════════════════

/**
 * Check if lazy context loader is initialized
 */
export function isLazyContextLoaderInitialized(): boolean {
  return LazyContextLoader['isInitialized'];
}

/**
 * Initialize the lazy context loader with a ChatContextLoaders instance
 */
export function initializeLazyContextLoader(
  loaderInstance: Parameters<typeof LazyContextLoader.initialize>[0]
): void {
  LazyContextLoader.initialize(loaderInstance);
}
