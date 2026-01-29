// src/stores/contextStore.ts
// PURPOSE: Manage mention context items for chat
// Replaces ContextService.ts RxJS implementation
// ~100 lines

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { useEffect, useRef } from 'react';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import { trackStateUpdate } from '../utils/performanceDebug';

// Track update count for debugging
let contextUpdateCount = 0;

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

interface IContextState {
  contextItems: Map<string, IMentionContext>;
}

interface IContextActions {
  // Item management
  addContext: (context: IMentionContext) => void;
  removeContext: (contextId: string) => void;
  setContextItems: (items: Map<string, IMentionContext>) => void;
  clearContextItems: () => void;

  // Getters
  getContextItem: (contextId: string) => IMentionContext | undefined;
  hasContextItem: (contextId: string) => boolean;
  getContextItemsByType: (type: IMentionContext['type']) => IMentionContext[];
  getCurrentContextItems: () => Map<string, IMentionContext>;
}

type IContextStore = IContextState & IContextActions;

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

export const useContextStore = create<IContextStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      contextItems: new Map(),

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      addContext: context => {
        contextUpdateCount++;
        trackStateUpdate('ContextStore', ['addContext']);
        set(state => {
          const newItems = new Map(state.contextItems);
          newItems.set(context.id, context);
          return { contextItems: newItems };
        });
      },

      removeContext: contextId => {
        contextUpdateCount++;
        trackStateUpdate('ContextStore', ['removeContext']);
        set(state => {
          const newItems = new Map(state.contextItems);
          newItems.delete(contextId);
          return { contextItems: newItems };
        });
      },

      setContextItems: items => {
        contextUpdateCount++;
        trackStateUpdate('ContextStore', ['setContextItems']);
        // Log if large number of items being set
        if (items.size > 100) {
          console.warn(
            `[ContextStore] Setting ${items.size} items - this is a lot of context items`
          );
        }
        set({ contextItems: new Map(items) });
      },

      clearContextItems: () => {
        contextUpdateCount++;
        trackStateUpdate('ContextStore', ['clearContextItems']);
        set({ contextItems: new Map() });
      },

      // ─────────────────────────────────────────────────────────────
      // Getters
      // ─────────────────────────────────────────────────────────────
      getContextItem: contextId => get().contextItems.get(contextId),

      hasContextItem: contextId => get().contextItems.has(contextId),

      getContextItemsByType: type => {
        return Array.from(get().contextItems.values()).filter(
          item => item.type === type
        );
      },

      getCurrentContextItems: () => new Map(get().contextItems)
    })),
    { name: 'ContextStore', serialize: devtoolsSerialize }
  )
);

// Debug utility
(window as any).getContextStoreUpdateCount = () => contextUpdateCount;

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectContextItems = (state: IContextStore) => state.contextItems;
export const selectContextCount = (state: IContextStore) =>
  state.contextItems.size;
export const selectContextItemsArray = (state: IContextStore) =>
  Array.from(state.contextItems.values());

// ═══════════════════════════════════════════════════════════════
// REACT HOOKS
// ═══════════════════════════════════════════════════════════════

/**
 * Hook to subscribe to context item changes.
 * @param callback - Function called when context items change
 */
export function useContextChange(
  callback: (items: Map<string, IMentionContext>) => void
): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const unsubscribe = useContextStore.subscribe(
      state => state.contextItems,
      items => callbackRef.current(items)
    );
    return unsubscribe;
  }, []);
}

/**
 * Hook to get context items of a specific type.
 * @param type - The context type to filter by
 */
export function useContextItemsByType(
  type: IMentionContext['type']
): IMentionContext[] {
  return useContextStore(state =>
    Array.from(state.contextItems.values()).filter(item => item.type === type)
  );
}

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to context changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToContextChanges(
  callback: (items: Map<string, IMentionContext>) => void
): () => void {
  return useContextStore.subscribe(state => state.contextItems, callback);
}
