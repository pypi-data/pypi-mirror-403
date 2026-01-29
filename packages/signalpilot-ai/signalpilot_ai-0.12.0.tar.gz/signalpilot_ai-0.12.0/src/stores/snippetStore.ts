// src/stores/snippetStore.ts
// PURPOSE: Manage saved code snippets and their insertion state
// ~120 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import { STATE_DB_KEYS, StateDBCachingService } from '../utils/backendCaching';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ISnippet {
  id: string;
  title: string;
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

interface ISnippetState {
  snippets: ISnippet[];
  insertedSnippetIds: string[];
  isLoaded: boolean;
}

interface ISnippetActions {
  // CRUD operations
  setSnippets: (snippets: ISnippet[]) => Promise<void>;
  addSnippet: (snippet: ISnippet) => Promise<void>;
  updateSnippet: (id: string, updates: Partial<ISnippet>) => Promise<void>;
  removeSnippet: (id: string) => Promise<void>;

  // Insertion tracking
  markInserted: (snippetId: string) => Promise<void>;
  unmarkInserted: (snippetId: string) => Promise<void>;
  clearInserted: () => Promise<void>;

  // Persistence
  loadFromStateDB: () => Promise<void>;

  // Utility
  generateSnippetId: () => string;
  isSnippetInserted: (snippetId: string) => boolean;
  getInsertedSnippets: () => ISnippet[];
}

type ISnippetStore = ISnippetState & ISnippetActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useSnippetStore = create<ISnippetStore>()(
  devtools(
    (set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      snippets: [],
      insertedSnippetIds: [],
      isLoaded: false,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      setSnippets: async snippets => {
        set({ snippets });
        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.SNIPPETS,
            snippets
          );
        } catch (error) {
          console.error('[SnippetStore] Failed to persist snippets:', error);
        }
      },

      addSnippet: async snippet => {
        const newSnippets = [...get().snippets, snippet];
        set({ snippets: newSnippets });
        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.SNIPPETS,
            newSnippets
          );
        } catch (error) {
          console.error('[SnippetStore] Failed to persist snippets:', error);
        }
      },

      updateSnippet: async (id, updates) => {
        console.log('[SnippetStore] Updating snippet:', id, updates);
        const updatedSnippets = get().snippets.map(s =>
          s.id === id
            ? { ...s, ...updates, updatedAt: new Date().toISOString() }
            : s
        );
        set({ snippets: updatedSnippets });
        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.SNIPPETS,
            updatedSnippets
          );
          console.log('[SnippetStore] Successfully persisted updated snippets');
        } catch (error) {
          console.error('[SnippetStore] Failed to persist snippets:', error);
        }
      },

      removeSnippet: async id => {
        const state = get();
        const filteredSnippets = state.snippets.filter(s => s.id !== id);
        const filteredInserted = state.insertedSnippetIds.filter(
          sid => sid !== id
        );

        set({
          snippets: filteredSnippets,
          insertedSnippetIds: filteredInserted
        });

        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.SNIPPETS,
            filteredSnippets
          );
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.INSERTED_SNIPPETS,
            filteredInserted
          );
        } catch (error) {
          console.error('[SnippetStore] Failed to persist snippets:', error);
        }
      },

      markInserted: async snippetId => {
        const state = get();
        if (!state.insertedSnippetIds.includes(snippetId)) {
          const newInserted = [...state.insertedSnippetIds, snippetId];
          set({ insertedSnippetIds: newInserted });
          try {
            await StateDBCachingService.setObjectValue(
              STATE_DB_KEYS.INSERTED_SNIPPETS,
              newInserted
            );
            console.log(
              '[SnippetStore] Marked snippet as inserted:',
              snippetId
            );
          } catch (error) {
            console.error(
              '[SnippetStore] Failed to persist inserted snippets:',
              error
            );
          }
        }
      },

      unmarkInserted: async snippetId => {
        const state = get();
        const newInserted = state.insertedSnippetIds.filter(
          id => id !== snippetId
        );
        set({ insertedSnippetIds: newInserted });
        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.INSERTED_SNIPPETS,
            newInserted
          );
          console.log('[SnippetStore] Unmarked snippet:', snippetId);
        } catch (error) {
          console.error(
            '[SnippetStore] Failed to persist inserted snippets:',
            error
          );
        }
      },

      clearInserted: async () => {
        set({ insertedSnippetIds: [] });
        try {
          await StateDBCachingService.setObjectValue(
            STATE_DB_KEYS.INSERTED_SNIPPETS,
            []
          );
          console.log('[SnippetStore] Cleared all inserted snippets');
        } catch (error) {
          console.error(
            '[SnippetStore] Failed to clear inserted snippets:',
            error
          );
        }
      },

      loadFromStateDB: async () => {
        try {
          // Load snippets
          const snippets = await StateDBCachingService.getObjectValue<
            ISnippet[]
          >(STATE_DB_KEYS.SNIPPETS, []);

          // Migrate snippets for unique IDs
          const usedIds = new Set<string>();
          let needsUpdate = false;
          const migratedSnippets = snippets.map((snippet, index) => {
            const hasValidId =
              snippet.id &&
              typeof snippet.id === 'string' &&
              snippet.id.trim().length > 0;
            const isDuplicate = hasValidId && usedIds.has(snippet.id);

            if (!hasValidId || isDuplicate) {
              needsUpdate = true;
              const newId = uuidv4();
              usedIds.add(newId);
              console.log(
                `[SnippetStore] Migrating snippet #${index} "${snippet.title}" with new ID`
              );
              return {
                ...snippet,
                id: newId,
                updatedAt: new Date().toISOString()
              };
            }
            usedIds.add(snippet.id);
            return snippet;
          });

          if (needsUpdate) {
            await StateDBCachingService.setObjectValue(
              STATE_DB_KEYS.SNIPPETS,
              migratedSnippets
            );
          }

          // Load inserted snippets
          const insertedSnippetIds = await StateDBCachingService.getObjectValue<
            string[]
          >(STATE_DB_KEYS.INSERTED_SNIPPETS, []);

          set({
            snippets: migratedSnippets,
            insertedSnippetIds,
            isLoaded: true
          });

          console.log(
            `[SnippetStore] Loaded ${migratedSnippets.length} snippets, ${insertedSnippetIds.length} inserted`
          );
        } catch (error) {
          console.error('[SnippetStore] Failed to load from StateDB:', error);
          set({ isLoaded: true }); // Mark as loaded even on error
        }
      },

      generateSnippetId: () => uuidv4(),

      isSnippetInserted: snippetId => {
        return get().insertedSnippetIds.includes(snippetId);
      },

      getInsertedSnippets: () => {
        const state = get();
        return state.snippets.filter(s =>
          state.insertedSnippetIds.includes(s.id)
        );
      }
    }),
    { name: 'SnippetStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectSnippets = (state: ISnippetStore) => state.snippets;
export const selectInsertedSnippetIds = (state: ISnippetStore) =>
  state.insertedSnippetIds;
export const selectIsLoaded = (state: ISnippetStore) => state.isLoaded;
export const selectSnippetById = (state: ISnippetStore, id: string) =>
  state.snippets.find(s => s.id === id);
