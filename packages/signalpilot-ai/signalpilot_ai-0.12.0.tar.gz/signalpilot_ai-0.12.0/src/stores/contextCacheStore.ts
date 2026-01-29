// src/stores/contextCacheStore.ts
// PURPOSE: Manage context cache for mention dropdown (available contexts by category)
// Separate from contextStore which manages selected/active context items

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';

// Cache refresh threshold in milliseconds (30 seconds)
const CACHE_REFRESH_THRESHOLD = 30000;

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IContextCacheState {
  // Cache of context items by category (snippets, data, variable, etc.)
  contextCache: Map<string, IMentionContext[]>;
  // Timestamp of last cache update
  contextCacheTimestamp: number;
  // Whether contexts are currently being loaded
  isContextLoading: boolean;
}

interface IContextCacheActions {
  // Cache management
  getCachedContexts: () => Map<string, IMentionContext[]>;
  setCachedContexts: (contexts: Map<string, IMentionContext[]>) => void;
  updateContextCategory: (
    category: string,
    contexts: IMentionContext[]
  ) => void;

  // Loading state
  isLoading: () => boolean;
  setLoading: (loading: boolean) => void;

  // Cache freshness
  getCacheAge: () => number;
  shouldRefresh: () => boolean;

  // Clear cache
  clearCache: () => void;

  // Invalidate cache (mark as stale so next access triggers refresh)
  invalidateCache: () => void;
}

type IContextCacheStore = IContextCacheState & IContextCacheActions;

// ═══════════════════════════════════════════════════════════════
// DEVTOOLS SERIALIZATION
// ═══════════════════════════════════════════════════════════════

const devtoolsSerialize = {
  replacer: (_key: string, value: any) => {
    if (value instanceof Map) {
      return `[Map: ${value.size} entries]`;
    }
    return value;
  }
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useContextCacheStore = create<IContextCacheStore>()(
  devtools(
    (set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      contextCache: new Map(),
      contextCacheTimestamp: 0,
      isContextLoading: false,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────

      getCachedContexts: () => {
        return get().contextCache;
      },

      setCachedContexts: (contexts: Map<string, IMentionContext[]>) => {
        set({
          contextCache: new Map(contexts),
          contextCacheTimestamp: Date.now(),
          isContextLoading: false
        });
      },

      updateContextCategory: (
        category: string,
        contexts: IMentionContext[]
      ) => {
        const currentCache = get().contextCache;
        const newCache = new Map(currentCache);
        newCache.set(category, contexts);
        set({
          contextCache: newCache,
          contextCacheTimestamp: Date.now()
        });
      },

      isLoading: () => {
        return get().isContextLoading;
      },

      setLoading: (loading: boolean) => {
        set({ isContextLoading: loading });
      },

      getCacheAge: () => {
        return Date.now() - get().contextCacheTimestamp;
      },

      shouldRefresh: () => {
        const cacheAge = get().getCacheAge();
        return cacheAge > CACHE_REFRESH_THRESHOLD;
      },

      clearCache: () => {
        set({
          contextCache: new Map(),
          contextCacheTimestamp: 0,
          isContextLoading: false
        });
      },

      invalidateCache: () => {
        set({ contextCacheTimestamp: 0 });
      }
    }),
    { name: 'ContextCacheStore', serialize: devtoolsSerialize }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectContextCache = (state: IContextCacheStore) =>
  state.contextCache;
export const selectIsContextLoading = (state: IContextCacheStore) =>
  state.isContextLoading;
export const selectCacheTimestamp = (state: IContextCacheStore) =>
  state.contextCacheTimestamp;
