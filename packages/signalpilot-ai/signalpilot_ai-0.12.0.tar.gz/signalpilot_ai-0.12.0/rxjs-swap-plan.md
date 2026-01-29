# RxJS to Zustand Migration Plan

> **Priority:** Readability | DevEx | Human Accessibility
>
> Every store should be **instantly understandable** by any engineer in under 60 seconds.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current RxJS Inventory](#2-current-rxjs-inventory)
3. [Subscriber Components](#3-subscriber-components)
4. [Zustand Store Designs](#4-zustand-store-designs)
5. [Migration Task List](#5-migration-task-list)
6. [Testing Strategy](#6-testing-strategy)

---

## 1. Executive Summary

### What We're Replacing

| Current (RxJS)                  | Target (Zustand)       | Lines   |
|---------------------------------|------------------------|---------|
| `AppState.ts` (1425 lines)      | 5 focused stores       | ~80 each|
| `DiffStateService.ts` (531 lines)| `diffStore.ts`        | ~100    |
| `DatabaseStateService.ts` (1518 lines)| `databaseStore.ts` | ~120   |
| `ContextService.ts` (103 lines) | `contextStore.ts`      | ~60     |
| `DatabaseMetadataCache.ts` (764 lines)| `metadataCacheStore.ts`| ~80  |
| `DeploymentStateService.ts` (271 lines)| `deploymentStore.ts`| ~60   |

### Why This Migration Matters

- **Find bugs faster**: `settings bug?` → check `settingsStore.ts` (not 1400-line god object)
- **Onboard engineers faster**: Each store is self-documenting with clear actions
- **Test in isolation**: No global singletons to mock
- **No subscription management**: React hooks handle cleanup automatically

---

## 2. Current RxJS Inventory

### 2.1 Core State Services (Sources of Truth)

#### `AppState.ts` - The God Object (PRIORITY 1)
**Location:** `src/AppState.ts`
**Lines:** 1,425
**RxJS Patterns:**
- `BehaviorSubject<IAppState>` - Main state container
- `Subject` - `notebookChanged$`, `notebookRenamed$` events
- `.getValue()` - 40+ call sites
- `.next()` - State updates
- `.asObservable()` - Subscriptions

**State Categories (to split into separate stores):**
```
1. App Core (appStore)
   - isInitialized, isLauncherActive
   - currentNotebookId, currentNotebook
   - isDemoMode, isTakeoverMode, takeoverPrompt
   - autoRun, maxToolCallLimit
   - userProfile

2. Settings (settingsStore)
   - theme, tokenMode, tabAutocompleteEnabled
   - claudeApiKey, claudeModelId, claudeModelUrl
   - databaseUrl

3. Snippets (snippetStore)
   - snippets[]
   - insertedSnippets[]

4. Context Cache (contextCacheStore)
   - contextCache Map
   - contextCacheTimestamp
   - isContextLoading
   - workspaceContext
   - scannedDirectories
   - initialFileScanComplete

5. Services Registry (servicesStore) - for non-React code
   - toolService, notebookTracker, notebookTools
   - All manager references
```

---

#### `DiffStateService.ts` - Diff Management (PRIORITY 2)
**Location:** `src/Services/DiffStateService.ts`
**Lines:** 531
**RxJS Patterns:**
- `BehaviorSubject<IDiffState>` - Main state
- `.pipe(map(), distinctUntilChanged())` - Derived observables
- Multiple derived observables: `allDiffsResolved$`, `getCellStateChanges$()`, etc.

**State:**
```typescript
{
  pendingDiffs: Map<string, IPendingDiff>
  allDiffsResolved: boolean
  notebookId: string | null
}
```

**Subscribers (10 components):**
- `NotebookDiffManager.ts:68`
- `ChatMessages.ts:800, 812`
- `DiffApprovalDialog.ts:744, 753`
- `DiffNavigationWidget.tsx:53, 80`
- `DiffItem.tsx:43, 61`
- `LLMStateDisplay.tsx:33, 47`
- `LLMStateContent.tsx:79`

---

#### `DatabaseStateService.ts` - Database Credentials (PRIORITY 3)
**Location:** `src/DatabaseStateService.ts`
**Lines:** 1,518
**RxJS Patterns:**
- `BehaviorSubject<IDatabaseCredentialsState>` - Main state
- `Subject` events: `configAdded$`, `configRemoved$`, `configUpdated$`, `activeConfigChanged$`

**State:**
```typescript
{
  configurations: IDatabaseConfig[]
  activeConfigId: string | null
  activeConfig: IDatabaseConfig | null
  isInitialized: boolean
}
```

**Subscribers (5 subscription points):**
- `DatabaseManagerWidget.tsx:533, 542, 550, 556, 562`

---

#### `ContextService.ts` - Chat Context Items (PRIORITY 4)
**Location:** `src/Services/ContextService.ts`
**Lines:** 103
**RxJS Patterns:**
- `BehaviorSubject<Map<string, IMentionContext>>` - Context items

**State:**
```typescript
{
  contextItems: Map<string, IMentionContext>
}
```

**Subscribers:**
- `ChatMessages.ts:776`
- `ChatboxContext.ts:294`

---

#### `DatabaseMetadataCache.ts` - Schema Cache (PRIORITY 5)
**Location:** `src/Services/DatabaseMetadataCache.ts`
**Lines:** 764
**RxJS Patterns:**
- `BehaviorSubject<IDatabaseMetadata | null>` - Cache state

**State:**
```typescript
{
  metadata: IDatabaseMetadata | null
  // Internal: cache, refreshTimer
}
```

**Subscribers:**
- `SettingsWidget.tsx:273`

---

#### `DeploymentStateService.ts` - Deployment Tracking (PRIORITY 6)
**Location:** `src/Services/DeploymentStateService.ts`
**Lines:** 271
**RxJS Patterns:**
- `Subject<IDeploymentChange>` - Event stream (no BehaviorSubject)

**State:**
```typescript
{
  deployments: Map<string, IDeploymentData>
}
```

**Subscribers:**
- `NotebookDeploymentButton.tsx:84`

---

## 3. Subscriber Components

### Complete Subscription Map

| Component | File | Subscribes To | Line |
|-----------|------|---------------|------|
| **ThreadManager** | `ThreadManager.ts` | `AppStateService.onNotebookChanged()` | 41 |
| **widgetInitialization** | `widgetInitialization.ts` | `AppStateService.onNotebookChanged()` | 358 |
| **ChatMessages** | `ChatMessages.ts` | `contextService.subscribe()` | 776 |
| **ChatMessages** | `ChatMessages.ts` | `diffStateService.allDiffsResolved$` | 800 |
| **ChatMessages** | `ChatMessages.ts` | `diffStateService.getApprovalStatusChanges$()` | 812 |
| **ChatHistoryManager** | `ChatHistoryManager.ts` | `AppStateService.onNotebookChanged()` | 48 |
| **NotebookContextManager** | `NotebookContextManager.ts` | `AppStateService.onNotebookChanged()` | 41 |
| **NotebookChatContainer** | `NotebookChatContainer.tsx` | `AppStateService.onNotebookChanged()` | 67 |
| **ContextCacheService** | `ContextCacheService.ts` | `AppStateService.onNotebookChanged()` | 306 |
| **NotebookDiffManager** | `NotebookDiffManager.ts` | `diffStateService.diffState$` | 68 |
| **ChatBoxWidget** | `ChatBoxWidget.tsx` | `AppStateService.changes` | 1013 |
| **ChatboxContext** | `ChatboxContext.ts` | `contextService.subscribe()` | 294 |
| **DiffApprovalDialog** | `DiffApprovalDialog.ts` | `getCellStateChanges$()` | 744 |
| **DiffApprovalDialog** | `DiffApprovalDialog.ts` | `diffStateService.diffState$` | 753 |
| **DiffNavigationWidget** | `DiffNavigationWidget.tsx` | `diffStateService.diffState$` | 53 |
| **DiffNavigationWidget** | `DiffNavigationWidget.tsx` | `diffStateService.allDiffsResolved$` | 80 |
| **FileExplorerContent** | `FileExplorerContent.tsx` | `AppStateService.changes` | 163 |
| **NotebookDeploymentButton** | `NotebookDeploymentButton.tsx` | `AppStateService.changes` | 36 |
| **NotebookDeploymentButton** | `NotebookDeploymentButton.tsx` | `deploymentStateService.changes` | 84 |
| **SettingsWidget** | `SettingsWidget.tsx` | `databaseCache.metadata$` | 273 |
| **DiffItem** | `DiffItem.tsx` | `getCellStateChanges$()` | 43 |
| **DiffItem** | `DiffItem.tsx` | `diffStateService.diffState$` | 61 |
| **LLMStateDisplay** | `LLMStateDisplay.tsx` | `diffStateService.diffState$` | 33 |
| **LLMStateDisplay** | `LLMStateDisplay.tsx` | `diffStateService.allDiffsResolved$` | 47 |
| **LLMStateContent** | `LLMStateContent.tsx` | `diffStateService.diffState$` | 79 |
| **DatabaseManagerWidget** | `DatabaseManagerWidget.tsx` | `DatabaseStateService.changes` | 533 |
| **DatabaseManagerWidget** | `DatabaseManagerWidget.tsx` | `onConfigurationAdded()` | 542 |
| **DatabaseManagerWidget** | `DatabaseManagerWidget.tsx` | `onConfigurationRemoved()` | 550 |
| **DatabaseManagerWidget** | `DatabaseManagerWidget.tsx` | `onConfigurationUpdated()` | 556 |
| **DatabaseManagerWidget** | `DatabaseManagerWidget.tsx` | `onActiveConfigurationChanged()` | 562 |
| **SnippetList** | `SnippetList.tsx` | `AppStateService.changes` | 33 |

**Total: 30 subscription points across 20 components**

---

## 4. Zustand Store Designs

> **Design Principle:** Each store should be readable in one screen (~60-120 lines)

### 4.1 `appStore.ts` - Core Application State

```typescript
// src/stores/appStore.ts
// PURPOSE: Core application state - initialization, current notebook, mode flags
// ~80 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface AppState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  // Initialization
  isInitialized: boolean;
  isLauncherActive: boolean;

  // Current Context
  currentNotebookId: string | null;
  currentWorkingDirectory: string | null;

  // Mode Flags
  isDemoMode: boolean;
  isTakeoverMode: boolean;
  takeoverPrompt: string | null;
  autoRun: boolean;

  // Limits
  maxToolCallLimit: number | null;

  // User
  userProfile: any | null;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  setInitialized: (value: boolean) => void;
  setLauncherActive: (value: boolean) => void;
  setCurrentNotebook: (notebookId: string | null) => void;
  setDemoMode: (value: boolean) => void;
  setTakeoverMode: (enabled: boolean, prompt?: string | null) => void;
  setAutoRun: (value: boolean) => void;
  setMaxToolCallLimit: (limit: number | null) => void;
  setUserProfile: (profile: any | null) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial State
      isInitialized: false,
      isLauncherActive: false,
      currentNotebookId: null,
      currentWorkingDirectory: null,
      isDemoMode: false,
      isTakeoverMode: false,
      takeoverPrompt: null,
      autoRun: false,
      maxToolCallLimit: null,
      userProfile: null,

      // Actions
      setInitialized: (value) => set({ isInitialized: value }),
      setLauncherActive: (value) => set({ isLauncherActive: value }),
      setCurrentNotebook: (notebookId) => set({ currentNotebookId: notebookId }),
      setDemoMode: (value) => set({ isDemoMode: value }),
      setTakeoverMode: (enabled, prompt) =>
        set({ isTakeoverMode: enabled, takeoverPrompt: prompt ?? null }),
      setAutoRun: (value) => set({ autoRun: value }),
      setMaxToolCallLimit: (limit) => set({ maxToolCallLimit: limit }),
      setUserProfile: (profile) => set({ userProfile: profile }),
    }),
    { name: 'AppStore' }
  )
);
```

---

### 4.2 `settingsStore.ts` - User Settings

```typescript
// src/stores/settingsStore.ts
// PURPOSE: User preferences and API configuration
// ~60 lines

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface SettingsState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  theme: string;
  tokenMode: boolean;
  tabAutocompleteEnabled: boolean;

  // Claude API
  claudeApiKey: string;
  claudeModelId: string;
  claudeModelUrl: string;

  // Database
  databaseUrl: string;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  updateSettings: (settings: Partial<Omit<SettingsState, 'updateSettings'>>) => void;
  setClaudeApiKey: (key: string) => void;
  setDatabaseUrl: (url: string) => void;
}

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        // Initial State
        theme: 'light',
        tokenMode: false,
        tabAutocompleteEnabled: false,
        claudeApiKey: '',
        claudeModelId: 'claude-sonnet-4-5-20250929',
        claudeModelUrl: 'https://sage.alpinex.ai:8760',
        databaseUrl: '',

        // Actions
        updateSettings: (settings) => set((state) => ({ ...state, ...settings })),
        setClaudeApiKey: (key) => set({ claudeApiKey: key }),
        setDatabaseUrl: (url) => set({ databaseUrl: url }),
      }),
      { name: 'settings-store' }
    ),
    { name: 'SettingsStore' }
  )
);
```

---

### 4.3 `diffStore.ts` - Code Diff Approval

```typescript
// src/stores/diffStore.ts
// PURPOSE: Manage pending code diffs and approval workflow
// ~100 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { IPendingDiff } from '../types';

interface DiffState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  pendingDiffs: Map<string, IPendingDiff>;
  notebookId: string | null;

  // ═══════════════════════════════════════════════════════════════
  // COMPUTED (via selectors below)
  // ═══════════════════════════════════════════════════════════════

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  addDiff: (cellId: string, diff: IPendingDiff) => void;
  removeDiff: (cellId: string) => void;
  updateDiffApproval: (cellId: string, approved: boolean | undefined) => void;
  updateDiffToRun: (cellId: string) => void;
  updateDiffResult: (cellId: string, runResult: any) => void;
  clearDiffs: (notebookId?: string | null) => void;
  setNotebookId: (notebookId: string | null) => void;
}

export const useDiffStore = create<DiffState>()(
  devtools(
    (set, get) => ({
      // Initial State
      pendingDiffs: new Map(),
      notebookId: null,

      // Actions
      addDiff: (cellId, diff) => set((state) => {
        const newDiffs = new Map(state.pendingDiffs);
        newDiffs.set(cellId, diff);
        return { pendingDiffs: newDiffs };
      }),

      removeDiff: (cellId) => set((state) => {
        const newDiffs = new Map(state.pendingDiffs);
        newDiffs.delete(cellId);
        return { pendingDiffs: newDiffs };
      }),

      updateDiffApproval: (cellId, approved) => set((state) => {
        const newDiffs = new Map(state.pendingDiffs);
        const existing = newDiffs.get(cellId);
        if (existing) {
          newDiffs.set(cellId, {
            ...existing,
            approved,
            userDecision: approved === true ? 'approved' : approved === false ? 'rejected' : null
          });
        }
        return { pendingDiffs: newDiffs };
      }),

      updateDiffToRun: (cellId) => set((state) => {
        const newDiffs = new Map(state.pendingDiffs);
        const existing = newDiffs.get(cellId);
        if (existing) {
          newDiffs.set(cellId, { ...existing, approved: true, userDecision: 'run' });
        }
        return { pendingDiffs: newDiffs };
      }),

      updateDiffResult: (cellId, runResult) => set((state) => {
        const newDiffs = new Map(state.pendingDiffs);
        const existing = newDiffs.get(cellId);
        if (existing) {
          newDiffs.set(cellId, { ...existing, runResult });
        }
        return { pendingDiffs: newDiffs };
      }),

      clearDiffs: (notebookId) => set((state) => {
        if (!notebookId) return { pendingDiffs: new Map() };
        const newDiffs = new Map();
        state.pendingDiffs.forEach((diff, cellId) => {
          if (diff.notebookId !== notebookId) newDiffs.set(cellId, diff);
        });
        return { pendingDiffs: newDiffs };
      }),

      setNotebookId: (notebookId) => set({ notebookId }),
    }),
    { name: 'DiffStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS (for computed values)
// ═══════════════════════════════════════════════════════════════

export const selectPendingDiffCount = (state: DiffState, notebookId?: string) => {
  let count = 0;
  state.pendingDiffs.forEach((diff) => {
    if ((!notebookId || diff.notebookId === notebookId) && !diff.userDecision) count++;
  });
  return count;
};

export const selectAllDiffsResolved = (state: DiffState, notebookId?: string) => {
  const diffs = Array.from(state.pendingDiffs.values())
    .filter(d => !notebookId || d.notebookId === notebookId);
  if (diffs.length === 0) return true;
  return diffs.every(d => d.userDecision);
};

export const selectApprovalStatus = (state: DiffState, notebookId?: string) => {
  let pending = 0, approved = 0, rejected = 0;
  state.pendingDiffs.forEach((diff) => {
    if (!notebookId || diff.notebookId === notebookId) {
      if (diff.userDecision === 'approved' || diff.userDecision === 'run') approved++;
      else if (diff.userDecision === 'rejected') rejected++;
      else pending++;
    }
  });
  return { pending, approved, rejected, allResolved: pending === 0 && (approved + rejected) > 0 };
};
```

---

### 4.4 `snippetStore.ts` - Code Snippets

```typescript
// src/stores/snippetStore.ts
// PURPOSE: Manage saved code snippets
// ~70 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { ISnippet } from '../AppState';

interface SnippetState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  snippets: ISnippet[];
  insertedSnippetIds: string[];

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  setSnippets: (snippets: ISnippet[]) => void;
  addSnippet: (snippet: ISnippet) => void;
  updateSnippet: (id: string, updates: Partial<ISnippet>) => void;
  removeSnippet: (id: string) => void;

  markInserted: (snippetId: string) => void;
  unmarkInserted: (snippetId: string) => void;
  clearInserted: () => void;
}

export const useSnippetStore = create<SnippetState>()(
  devtools(
    (set) => ({
      // Initial State
      snippets: [],
      insertedSnippetIds: [],

      // Actions
      setSnippets: (snippets) => set({ snippets }),

      addSnippet: (snippet) => set((state) => ({
        snippets: [...state.snippets, snippet]
      })),

      updateSnippet: (id, updates) => set((state) => ({
        snippets: state.snippets.map(s => s.id === id ? { ...s, ...updates } : s)
      })),

      removeSnippet: (id) => set((state) => ({
        snippets: state.snippets.filter(s => s.id !== id),
        insertedSnippetIds: state.insertedSnippetIds.filter(sid => sid !== id)
      })),

      markInserted: (snippetId) => set((state) => ({
        insertedSnippetIds: state.insertedSnippetIds.includes(snippetId)
          ? state.insertedSnippetIds
          : [...state.insertedSnippetIds, snippetId]
      })),

      unmarkInserted: (snippetId) => set((state) => ({
        insertedSnippetIds: state.insertedSnippetIds.filter(id => id !== snippetId)
      })),

      clearInserted: () => set({ insertedSnippetIds: [] }),
    }),
    { name: 'SnippetStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectInsertedSnippets = (state: SnippetState) =>
  state.snippets.filter(s => state.insertedSnippetIds.includes(s.id));

export const selectIsSnippetInserted = (state: SnippetState, snippetId: string) =>
  state.insertedSnippetIds.includes(snippetId);
```

---

### 4.5 `contextStore.ts` - Chat Context Items

```typescript
// src/stores/contextStore.ts
// PURPOSE: Manage mention context items for chat
// ~50 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { IMentionContext } from '../Chat/ChatContextMenu/ChatContextLoaders';

interface ContextState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  contextItems: Map<string, IMentionContext>;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  addContext: (context: IMentionContext) => void;
  removeContext: (contextId: string) => void;
  setContextItems: (items: Map<string, IMentionContext>) => void;
  clearContextItems: () => void;
}

export const useContextStore = create<ContextState>()(
  devtools(
    (set) => ({
      // Initial State
      contextItems: new Map(),

      // Actions
      addContext: (context) => set((state) => {
        const newItems = new Map(state.contextItems);
        newItems.set(context.id, context);
        return { contextItems: newItems };
      }),

      removeContext: (contextId) => set((state) => {
        const newItems = new Map(state.contextItems);
        newItems.delete(contextId);
        return { contextItems: newItems };
      }),

      setContextItems: (items) => set({ contextItems: new Map(items) }),

      clearContextItems: () => set({ contextItems: new Map() }),
    }),
    { name: 'ContextStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectContextByType = (state: ContextState, type: string) =>
  Array.from(state.contextItems.values()).filter(item => item.type === type);

export const selectHasContext = (state: ContextState, contextId: string) =>
  state.contextItems.has(contextId);
```

---

### 4.6 `databaseConfigStore.ts` - Database Configurations

```typescript
// src/stores/databaseConfigStore.ts
// PURPOSE: Manage database connection configurations
// ~90 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { IDatabaseConfig } from '../DatabaseStateService';

interface DatabaseConfigState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  configurations: IDatabaseConfig[];
  activeConfigId: string | null;
  isInitialized: boolean;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  setConfigurations: (configs: IDatabaseConfig[]) => void;
  addConfiguration: (config: IDatabaseConfig) => void;
  updateConfiguration: (configId: string, updates: Partial<IDatabaseConfig>) => void;
  removeConfiguration: (configId: string) => void;
  setActiveConfig: (configId: string | null) => void;
  setInitialized: (value: boolean) => void;
}

export const useDatabaseConfigStore = create<DatabaseConfigState>()(
  devtools(
    (set, get) => ({
      // Initial State
      configurations: [],
      activeConfigId: null,
      isInitialized: false,

      // Actions
      setConfigurations: (configs) => set({ configurations: configs }),

      addConfiguration: (config) => set((state) => ({
        configurations: [...state.configurations, config]
      })),

      updateConfiguration: (configId, updates) => set((state) => ({
        configurations: state.configurations.map(c =>
          c.id === configId ? { ...c, ...updates, updatedAt: new Date().toISOString() } : c
        )
      })),

      removeConfiguration: (configId) => set((state) => ({
        configurations: state.configurations.filter(c => c.id !== configId),
        activeConfigId: state.activeConfigId === configId ? null : state.activeConfigId
      })),

      setActiveConfig: (configId) => set({ activeConfigId: configId }),

      setInitialized: (value) => set({ isInitialized: value }),
    }),
    { name: 'DatabaseConfigStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectActiveConfig = (state: DatabaseConfigState) =>
  state.configurations.find(c => c.id === state.activeConfigId) ?? null;

export const selectConfigById = (state: DatabaseConfigState, configId: string) =>
  state.configurations.find(c => c.id === configId) ?? null;

export const selectConfigsByType = (state: DatabaseConfigState, type: string) =>
  state.configurations.filter(c => c.type === type);
```

---

### 4.7 `deploymentStore.ts` - Notebook Deployments

```typescript
// src/stores/deploymentStore.ts
// PURPOSE: Track deployed notebooks
// ~50 lines

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { IDeploymentData } from '../Services/DeploymentStateService';

interface DeploymentState {
  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  deployments: Map<string, IDeploymentData>;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  setDeployment: (notebookPath: string, deployment: IDeploymentData) => void;
  removeDeployment: (notebookPath: string) => void;
  clearDeployments: () => void;
}

export const useDeploymentStore = create<DeploymentState>()(
  devtools(
    (set) => ({
      // Initial State
      deployments: new Map(),

      // Actions
      setDeployment: (notebookPath, deployment) => set((state) => {
        const newDeployments = new Map(state.deployments);
        newDeployments.set(notebookPath, deployment);
        return { deployments: newDeployments };
      }),

      removeDeployment: (notebookPath) => set((state) => {
        const newDeployments = new Map(state.deployments);
        newDeployments.delete(notebookPath);
        return { deployments: newDeployments };
      }),

      clearDeployments: () => set({ deployments: new Map() }),
    }),
    { name: 'DeploymentStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsDeployed = (state: DeploymentState, notebookPath: string) =>
  state.deployments.has(notebookPath);

export const selectDeployment = (state: DeploymentState, notebookPath: string) =>
  state.deployments.get(notebookPath);
```

---

### 4.8 `notebookEventsStore.ts` - Notebook Change Events

```typescript
// src/stores/notebookEventsStore.ts
// PURPOSE: Replacement for Subject-based notebook events
// ~40 lines

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

interface NotebookEventsState {
  // ═══════════════════════════════════════════════════════════════
  // STATE (for triggering reactions)
  // ═══════════════════════════════════════════════════════════════

  lastNotebookChange: {
    oldNotebookId: string | null;
    newNotebookId: string | null;
    fromLauncher?: boolean;
    timestamp: number;
  } | null;

  lastNotebookRename: {
    oldNotebookId: string;
    newNotebookId: string;
    timestamp: number;
  } | null;

  // ═══════════════════════════════════════════════════════════════
  // ACTIONS
  // ═══════════════════════════════════════════════════════════════

  notifyNotebookChanged: (oldId: string | null, newId: string | null, fromLauncher?: boolean) => void;
  notifyNotebookRenamed: (oldId: string, newId: string) => void;
}

export const useNotebookEventsStore = create<NotebookEventsState>()(
  devtools(
    subscribeWithSelector(
      (set) => ({
        lastNotebookChange: null,
        lastNotebookRename: null,

        notifyNotebookChanged: (oldId, newId, fromLauncher) => set({
          lastNotebookChange: { oldNotebookId: oldId, newNotebookId: newId, fromLauncher, timestamp: Date.now() }
        }),

        notifyNotebookRenamed: (oldId, newId) => set({
          lastNotebookRename: { oldNotebookId: oldId, newNotebookId: newId, timestamp: Date.now() }
        }),
      })
    ),
    { name: 'NotebookEventsStore' }
  )
);
```

---

## 5. Migration Task List

### Phase 1: Setup & Infrastructure (Week 1)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 1.1 | Install Zustand | `package.json` | P0 | 5 min |
| 1.2 | Create `src/stores/` directory structure | - | P0 | 10 min |
| 1.3 | Create `appStore.ts` | `src/stores/appStore.ts` | P0 | 30 min |
| 1.4 | Create `settingsStore.ts` | `src/stores/settingsStore.ts` | P0 | 20 min |
| 1.5 | Create `notebookEventsStore.ts` | `src/stores/notebookEventsStore.ts` | P0 | 20 min |
| 1.6 | Create store index file | `src/stores/index.ts` | P0 | 10 min |

### Phase 2: Diff State Migration (Week 1-2)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 2.1 | Create `diffStore.ts` | `src/stores/diffStore.ts` | P1 | 45 min |
| 2.2 | Add parallel sync from DiffStateService | `DiffStateService.ts` | P1 | 30 min |
| 2.3 | Migrate `DiffNavigationWidget.tsx` | Component | P1 | 30 min |
| 2.4 | Migrate `DiffItem.tsx` | Component | P1 | 30 min |
| 2.5 | Migrate `LLMStateDisplay.tsx` | Component | P1 | 30 min |
| 2.6 | Migrate `LLMStateContent.tsx` | Component | P1 | 20 min |
| 2.7 | Migrate `DiffApprovalDialog.ts` | Component | P1 | 45 min |
| 2.8 | Migrate `NotebookDiffManager.ts` | Manager | P1 | 30 min |
| 2.9 | Migrate `ChatMessages.ts` (diff subs) | Component | P1 | 30 min |
| 2.10 | Remove DiffStateService RxJS | Cleanup | P1 | 20 min |

### Phase 3: Context & Snippet Migration (Week 2)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 3.1 | Create `contextStore.ts` | `src/stores/contextStore.ts` | P2 | 20 min |
| 3.2 | Create `snippetStore.ts` | `src/stores/snippetStore.ts` | P2 | 25 min |
| 3.3 | Migrate `ChatMessages.ts` (context sub) | Component | P2 | 20 min |
| 3.4 | Migrate `ChatboxContext.ts` | Component | P2 | 20 min |
| 3.5 | Migrate `SnippetList.tsx` | Component | P2 | 20 min |
| 3.6 | Remove ContextService RxJS | Cleanup | P2 | 15 min |

### Phase 4: AppState Migration (Week 2-3)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 4.1 | Add parallel sync AppState → Zustand | `AppState.ts` | P1 | 45 min |
| 4.2 | Migrate `ChatBoxWidget.tsx` | Component | P1 | 45 min |
| 4.3 | Migrate `ThreadManager.ts` | Manager | P1 | 30 min |
| 4.4 | Migrate `NotebookContextManager.ts` | Manager | P1 | 30 min |
| 4.5 | Migrate `NotebookChatContainer.tsx` | Component | P1 | 30 min |
| 4.6 | Migrate `ChatHistoryManager.ts` | Manager | P1 | 30 min |
| 4.7 | Migrate `ContextCacheService.ts` | Service | P1 | 30 min |
| 4.8 | Migrate `FileExplorerContent.tsx` | Component | P2 | 20 min |
| 4.9 | Migrate `NotebookDeploymentButton.tsx` | Component | P2 | 20 min |
| 4.10 | Migrate `widgetInitialization.ts` | Initialization | P1 | 30 min |

### Phase 5: Database State Migration (Week 3)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 5.1 | Create `databaseConfigStore.ts` | `src/stores/databaseConfigStore.ts` | P2 | 30 min |
| 5.2 | Create `deploymentStore.ts` | `src/stores/deploymentStore.ts` | P3 | 20 min |
| 5.3 | Migrate `DatabaseManagerWidget.tsx` | Component | P2 | 45 min |
| 5.4 | Migrate `SettingsWidget.tsx` | Component | P3 | 20 min |
| 5.5 | Migrate `NotebookDeploymentButton.tsx` (deployment) | Component | P3 | 20 min |

### Phase 6: Cleanup & Removal (Week 4)

| # | Task | File(s) | Priority | Est. Effort |
|---|------|---------|----------|-------------|
| 6.1 | Remove RxJS from AppState.ts | `AppState.ts` | P1 | 1 hour |
| 6.2 | Remove DiffStateService.ts | Delete file | P1 | 15 min |
| 6.3 | Remove ContextService.ts RxJS | `ContextService.ts` | P2 | 15 min |
| 6.4 | Remove DatabaseStateService RxJS | `DatabaseStateService.ts` | P2 | 30 min |
| 6.5 | Remove DeploymentStateService RxJS | `DeploymentStateService.ts` | P3 | 15 min |
| 6.6 | Remove DatabaseMetadataCache RxJS | `DatabaseMetadataCache.ts` | P3 | 15 min |
| 6.7 | Update all imports | All files | P1 | 1 hour |
| 6.8 | Remove RxJS dependency (if fully unused) | `package.json` | P1 | 5 min |
| 6.9 | Final testing & verification | - | P0 | 2 hours |

---

## 6. Testing Strategy

### Per-Component Migration Testing

For each component migration:

1. **Before Migration**: Document current behavior
2. **During Migration**: Run app, verify same behavior
3. **After Migration**:
   - Verify state updates correctly
   - Verify no memory leaks (subscriptions cleaned up)
   - Verify React DevTools shows correct state

## Quick Reference

### Zustand Patterns Used

| Pattern | When to Use | Example |
|---------|-------------|---------|
| `set({ key: value })` | Simple state update | `set({ isInitialized: true })` |
| `set((state) => ...)` | Update based on current state | Adding to Map/Array |
| `devtools()` | All stores (debugging) | Wrap store creation |
| `persist()` | Settings that survive reload | `settingsStore` |
| `subscribeWithSelector()` | Event-like behavior | `notebookEventsStore` |

### Migration Checklist Per Component

- [ ] Identify RxJS subscriptions in component
- [ ] Map subscriptions to Zustand selectors
- [ ] Replace `.subscribe()` with `useStore()` hook
- [ ] Remove subscription cleanup code
- [ ] Test component behavior
- [ ] Update imports

---

## Summary

**Total Stores to Create:** 8
**Total Components to Migrate:** 20
**Total Subscription Points to Replace:** 30

**Expected Outcome:**
- ~60-120 lines per store (vs 1400+ line god object)
- Zero manual subscription management
- DevTools integration for debugging
- Instant state updates with React hooks
