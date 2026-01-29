# Startup Reliability & Performance Improvement Plan V2

## Why V1 Failed: Understanding Main Thread Blocking

### The Core Problem

The V1 refactor attempted to make operations non-blocking by:
1. Changing `await initializeAuthentication()` to `void initializeAuthentication().then(...)`
2. Making widget initialization return synchronously
3. Deferring some operations with `void` prefix

**However, this approach fundamentally misunderstands how JavaScript async/await works:**

```typescript
// This still BLOCKS the main thread synchronously:
void initializeAuthentication();

// Why? Because async functions execute synchronously until their first `await`
async function initializeAuthentication() {
  // All this code runs SYNCHRONOUSLY on the main thread:
  const service = JWTAuthModalService.getInstance(); // sync
  const data = processConfig();                       // sync
  prepareRequest();                                   // sync

  // Only HERE does it yield to the event loop:
  await fetchToken();  // <-- Finally async
}
```

**Key Insight**: Using `void` or removing `await` does NOT make code non-blocking if the function does significant synchronous work before its first internal `await`.

### Evidence from Logs

The logs show JupyterLab's `activatePlugin` function waiting on our `activate` function:
```
activatePlugin @ jlab_core.e595af6ce37775e8a915.js
↓
handleEarlyAuth @ plugin.ts:507
↓
activate @ plugin.ts:523  <-- Our code blocks here
```

When our `activate` function blocks, JupyterLab cannot continue loading other plugins or rendering the UI.

---

## Root Cause Analysis

### Blocking Operation Timeline

| Operation | Time | Why It Blocks |
|-----------|------|---------------|
| `initializeDemoMode` | 168-193ms | `await useAppStore.getState().loadDemoMode()` - synchronous StateDB read |
| `initializeAuthentication` | 697-749ms | Sequential awaits: StateDB → JWT validation → Profile fetch |
| `ContextLoader.databases` | 4836ms | Dynamic import + StateDB decode + synchronous schema parsing |
| `NotebookSwitch.getNotebookFile` | 5097ms | Waits for ContextLoader to complete |
| `ChatHistory.loadThreads.setCurrentNotebook` | 740ms | StateDB reads + localStorage access |

### The Cascade Effect

```
activate() called
    ├─► initializeCaching (0.1ms) ✓
    ├─► await initializeDemoMode (193ms) ← BLOCKS JupyterLab
    ├─► await initializeAuthentication (749ms) ← BLOCKS JupyterLab
    ├─► initializeCoreServices (1ms) ✓
    └─► initializeAsyncServices
            └─► loadAllContexts()
                    └─► ContextLoader.databases (4836ms) ← Late but still blocks UI
```

---

## V2 Solution Architecture

### Core Principles

1. **Never await I/O in activate()** - JupyterLab's plugin system expects activate to return quickly
2. **Yield to event loop with `setTimeout(0)`** - Forces true async even for sync work
3. **Use `requestIdleCallback` for non-critical work** - Let browser schedule during idle time
4. **Progressive enhancement** - Show UI immediately, enhance as data loads
5. **Lazy load on demand** - Don't load database contexts until user interacts with them
6. **Use Web Workers for heavy parsing** - Keep JSON parsing off main thread

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHASE 1: INSTANT (< 10ms)                     │
│  • Create UI shells (empty containers)                              │
│  • Register commands (sync)                                          │
│  • Add widgets to shell (no content yet)                            │
│  • Return from activate()                                            │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   PHASE 2: DEFERRED (setTimeout(0))                  │
│  • Initialize caching services                                       │
│  • Set up event listeners                                           │
│  • Load cached auth state (if available)                            │
│  • Show skeleton loaders in UI                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 3: BACKGROUND (requestIdleCallback)               │
│  • Full authentication flow                                          │
│  • Database context loading (lazy)                                   │
│  • Chat history loading                                              │
│  • Snippet loading                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: ON-DEMAND (user action)                  │
│  • Database schema fetching (when user opens DB panel)              │
│  • MCP tool initialization (when user interacts with tools)         │
│  • Full kernel variable loading (when user opens variable panel)    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: True Non-Blocking Activate Function

#### 1.1 Create a Deferred Initialization Scheduler

Create `src/utils/deferredInit.ts`:

```typescript
/**
 * DeferredInit - Schedules work to run without blocking the main thread
 */

type Priority = 'critical' | 'high' | 'normal' | 'idle';

interface DeferredTask {
  name: string;
  fn: () => Promise<void> | void;
  priority: Priority;
}

class DeferredInitScheduler {
  private criticalQueue: DeferredTask[] = [];
  private highQueue: DeferredTask[] = [];
  private normalQueue: DeferredTask[] = [];
  private idleQueue: DeferredTask[] = [];
  private isProcessing = false;

  /**
   * Schedule a task to run later without blocking
   */
  schedule(name: string, fn: () => Promise<void> | void, priority: Priority = 'normal'): void {
    const task = { name, fn, priority };
    switch (priority) {
      case 'critical':
        this.criticalQueue.push(task);
        break;
      case 'high':
        this.highQueue.push(task);
        break;
      case 'normal':
        this.normalQueue.push(task);
        break;
      case 'idle':
        this.idleQueue.push(task);
        break;
    }

    if (!this.isProcessing) {
      this.startProcessing();
    }
  }

  private startProcessing(): void {
    this.isProcessing = true;

    // Process critical tasks immediately but still yield to event loop
    if (this.criticalQueue.length > 0) {
      setTimeout(() => this.processCriticalQueue(), 0);
    } else if (this.highQueue.length > 0) {
      setTimeout(() => this.processHighQueue(), 0);
    } else if (this.normalQueue.length > 0) {
      // Use requestIdleCallback for normal priority
      this.scheduleIdleWork(() => this.processNormalQueue());
    } else if (this.idleQueue.length > 0) {
      this.scheduleIdleWork(() => this.processIdleQueue());
    } else {
      this.isProcessing = false;
    }
  }

  private scheduleIdleWork(callback: () => void): void {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(
        () => callback(),
        { timeout: 2000 } // Ensure it runs within 2 seconds even if busy
      );
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(callback, 50);
    }
  }

  private async processCriticalQueue(): Promise<void> {
    while (this.criticalQueue.length > 0) {
      const task = this.criticalQueue.shift()!;
      try {
        console.log(`[DeferredInit] Running critical: ${task.name}`);
        await task.fn();
      } catch (error) {
        console.error(`[DeferredInit] Critical task failed: ${task.name}`, error);
      }
    }
    this.startProcessing();
  }

  private async processHighQueue(): Promise<void> {
    // Process one at a time, yielding between each
    const task = this.highQueue.shift();
    if (task) {
      try {
        console.log(`[DeferredInit] Running high: ${task.name}`);
        await task.fn();
      } catch (error) {
        console.error(`[DeferredInit] High task failed: ${task.name}`, error);
      }
    }

    // Yield to event loop, then continue
    setTimeout(() => this.startProcessing(), 0);
  }

  private async processNormalQueue(): Promise<void> {
    // Process in batches during idle time
    const batchSize = 3;
    const batch = this.normalQueue.splice(0, batchSize);

    for (const task of batch) {
      try {
        console.log(`[DeferredInit] Running normal: ${task.name}`);
        await task.fn();
      } catch (error) {
        console.error(`[DeferredInit] Normal task failed: ${task.name}`, error);
      }
    }

    this.startProcessing();
  }

  private async processIdleQueue(): Promise<void> {
    const task = this.idleQueue.shift();
    if (task) {
      try {
        console.log(`[DeferredInit] Running idle: ${task.name}`);
        await task.fn();
      } catch (error) {
        console.error(`[DeferredInit] Idle task failed: ${task.name}`, error);
      }
    }
    this.startProcessing();
  }
}

export const deferredInit = new DeferredInitScheduler();
```

#### 1.2 Refactor activateSignalPilot

```typescript
export async function activateSignalPilot(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  // ... other params
): Promise<void> {
  const startTime = performance.now();
  console.log('[SignalPilot] Activation starting...');

  // ═══════════════════════════════════════════════════════════════
  // PHASE 1: INSTANT - Synchronous setup only (< 10ms)
  // No await, no I/O, no heavy computation
  // ═══════════════════════════════════════════════════════════════

  // Initialize loading state store (sync, just creates store)
  const loadingStore = useLoadingStateStore.getState();
  loadingStore.setCurrentPhase(LoadingPhase.STARTING);

  // Create empty UI shells (sync widget creation)
  const tracker = createWidgetTracker();
  const chatShell = createChatContainerShell(app, tracker);
  const settingsShell = createSettingsContainerShell(app, tracker);

  // Add shells to JupyterLab (sync)
  app.shell.add(chatShell, 'right', { rank: 1, activate: false });
  app.shell.add(settingsShell, 'right', { rank: 2 });

  // Register commands (sync)
  registerCoreCommands(app, palette);

  console.log(`[SignalPilot] Phase 1 complete: ${performance.now() - startTime}ms`);

  // ═══════════════════════════════════════════════════════════════
  // PHASE 2: DEFERRED - Schedule all async work
  // These will run after activate() returns
  // ═══════════════════════════════════════════════════════════════

  // Critical: Caching must be ready before other services
  deferredInit.schedule('initializeCaching', async () => {
    await initializeCaching(settingRegistry);
    loadingStore.setServicesInitialized(true);
  }, 'critical');

  // Critical: Core services needed for basic functionality
  deferredInit.schedule('initializeCoreServices', () => {
    const services = initializeCoreServices(app, notebooks, documentManager, settingRegistry);
    // Hydrate the UI shells with actual content
    hydrateWidgets(chatShell, settingsShell, services);
    loadingStore.setCoreServicesReady(true);
  }, 'critical');

  // High: Authentication (user needs to know if logged in)
  deferredInit.schedule('initializeAuthentication', async () => {
    loadingStore.setCurrentPhase(LoadingPhase.AUTHENTICATION);
    await initializeAuthenticationNonBlocking();
    loadingStore.setAuthInitialized(true);
  }, 'high');

  // Normal: Demo mode (not urgent)
  deferredInit.schedule('initializeDemoMode', () => {
    initializeDemoModeNonBlocking(replayId);
  }, 'normal');

  // Normal: Async services
  deferredInit.schedule('initializeAsyncServices', async () => {
    loadingStore.setCurrentPhase(LoadingPhase.CONTEXTS);
    await initializeAsyncServicesNonBlocking(notebooks);
    loadingStore.setContextsLoaded(true);
  }, 'normal');

  // Idle: Workspace context (nice to have)
  deferredInit.schedule('fetchWorkspaceContext', fetchWorkspaceContext, 'idle');

  // Idle: Snippets (nice to have)
  deferredInit.schedule('loadSnippets', loadSnippets, 'idle');

  // Idle: Database contexts (load on demand instead)
  // Note: We DON'T eagerly load database contexts anymore

  console.log(`[SignalPilot] Phase 2 scheduled: ${performance.now() - startTime}ms`);

  // Signal that basic initialization is complete
  // Callbacks will run as deferred tasks complete
  signalSignalpilotInitialized();

  console.log(`[SignalPilot] Activation complete: ${performance.now() - startTime}ms`);
  // activate() returns here, JupyterLab can continue loading
}
```

### Phase 2: Lazy Database Context Loading

The biggest blocker is `ContextLoader.databases` at 4836ms. This should be lazy loaded.

#### 2.1 Create Lazy Context Loading System

```typescript
// src/ChatBox/Context/LazyContextLoader.ts

export class LazyContextLoader {
  private loadedContexts = new Map<string, boolean>();
  private loadingPromises = new Map<string, Promise<void>>();

  /**
   * Get database contexts - loads on first access
   */
  async getDatabaseContexts(): Promise<IMentionContext[]> {
    if (!this.loadedContexts.get('databases')) {
      // Show loading indicator
      useContextStore.getState().setDatabasesLoading(true);

      try {
        if (!this.loadingPromises.has('databases')) {
          this.loadingPromises.set('databases', this.loadDatabasesAsync());
        }
        await this.loadingPromises.get('databases');
        this.loadedContexts.set('databases', true);
      } finally {
        useContextStore.getState().setDatabasesLoading(false);
      }
    }

    return useContextStore.getState().databaseContexts;
  }

  private async loadDatabasesAsync(): Promise<void> {
    // Break up work with yielding
    await this.yieldToEventLoop();

    const { getDatabases } = await import('./databaseHelper');
    await this.yieldToEventLoop();

    const contexts = await getDatabases();
    await this.yieldToEventLoop();

    useContextStore.getState().setDatabaseContexts(contexts);
  }

  private yieldToEventLoop(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 0));
  }
}
```

#### 2.2 Trigger Database Loading on User Interaction

```typescript
// In database-related UI components:

const DatabaseContextPanel: React.FC = () => {
  const { databases, isLoading } = useContextStore(s => ({
    databases: s.databaseContexts,
    isLoading: s.databasesLoading
  }));

  useEffect(() => {
    // Load databases when panel mounts (user opened it)
    const loader = LazyContextLoader.getInstance();
    loader.getDatabaseContexts();
  }, []);

  if (isLoading) {
    return <DatabaseSkeleton />;
  }

  return <DatabaseList databases={databases} />;
};
```

### Phase 3: Non-Blocking Authentication Flow

#### 3.1 Split Authentication into Phases

```typescript
// src/SignalPilot/initialization.ts

/**
 * Non-blocking authentication initialization
 * Returns immediately, completes in background
 */
export function initializeAuthenticationNonBlocking(): void {
  // Phase 1: Check cached auth state (sync, fast)
  const cachedToken = getCachedAuthToken(); // From memory/localStorage
  if (cachedToken) {
    useAppStore.getState().setAuthState({
      isAuthenticated: true,
      token: cachedToken,
      isValidating: true // Will validate in background
    });
  }

  // Phase 2: Validate token in background (truly async)
  setTimeout(async () => {
    try {
      const isValid = await validateTokenAsync(cachedToken);
      if (isValid) {
        // Phase 3: Load profile in background
        requestIdleCallback(async () => {
          try {
            const profile = await loadUserProfile();
            useAppStore.getState().setUserProfile(profile);
          } catch (error) {
            console.warn('[Auth] Profile load failed:', error);
          }
        });
      } else {
        useAppStore.getState().setAuthState({ isAuthenticated: false });
      }
    } catch (error) {
      console.warn('[Auth] Token validation failed:', error);
      useAppStore.getState().setAuthState({ isAuthenticated: false });
    }
  }, 0);
}
```

### Phase 4: Skeleton Loading States

#### 4.1 Create Loading State Store

```typescript
// src/stores/loadingStateStore.ts

import { create } from 'zustand';

export enum LoadingPhase {
  STARTING = 'starting',
  SERVICES = 'services',
  AUTHENTICATION = 'authentication',
  CONTEXTS = 'contexts',
  READY = 'ready'
}

interface LoadingStateStore {
  currentPhase: LoadingPhase;
  servicesInitialized: boolean;
  authInitialized: boolean;
  coreServicesReady: boolean;
  contextsLoaded: boolean;
  chatHistoryLoading: boolean;
  databasesLoading: boolean;

  // Derived
  isAppReady: boolean;
  isChatReady: boolean;

  // Actions
  setCurrentPhase: (phase: LoadingPhase) => void;
  setServicesInitialized: (value: boolean) => void;
  setAuthInitialized: (value: boolean) => void;
  setCoreServicesReady: (value: boolean) => void;
  setContextsLoaded: (value: boolean) => void;
  setChatHistoryLoading: (value: boolean) => void;
  setDatabasesLoading: (value: boolean) => void;
}

export const useLoadingStateStore = create<LoadingStateStore>((set, get) => ({
  currentPhase: LoadingPhase.STARTING,
  servicesInitialized: false,
  authInitialized: false,
  coreServicesReady: false,
  contextsLoaded: false,
  chatHistoryLoading: false,
  databasesLoading: false,

  get isAppReady() {
    const state = get();
    return state.servicesInitialized && state.coreServicesReady;
  },

  get isChatReady() {
    const state = get();
    return state.isAppReady && !state.chatHistoryLoading;
  },

  setCurrentPhase: (phase) => set({ currentPhase: phase }),
  setServicesInitialized: (value) => set({ servicesInitialized: value }),
  setAuthInitialized: (value) => set({ authInitialized: value }),
  setCoreServicesReady: (value) => set({ coreServicesReady: value }),
  setContextsLoaded: (value) => set({ contextsLoaded: value }),
  setChatHistoryLoading: (value) => set({ chatHistoryLoading: value }),
  setDatabasesLoading: (value) => set({ databasesLoading: value }),
}));
```

#### 4.2 Create Shell/Skeleton Components

```typescript
// src/Components/Skeletons/ChatBoxSkeleton.tsx

export const ChatBoxSkeleton: React.FC = () => (
  <div className="sage-ai-chatbox sage-ai-chatbox-skeleton">
    <div className="sage-ai-chatbox-header-skeleton">
      <div className="sage-ai-skeleton-bar" style={{ width: '120px' }} />
    </div>
    <div className="sage-ai-chatbox-content-skeleton">
      <div className="sage-ai-blob-loader" />
      <span className="sage-ai-loading-text">Loading chat...</span>
    </div>
    <div className="sage-ai-chatbox-input-skeleton">
      <div className="sage-ai-skeleton-input" />
    </div>
  </div>
);

// CSS
.sage-ai-skeleton-bar {
  height: 16px;
  background: linear-gradient(
    90deg,
    var(--jp-layout-color2) 25%,
    var(--jp-layout-color3) 50%,
    var(--jp-layout-color2) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

#### 4.3 Progressive Enhancement Pattern

```typescript
// src/Notebook/NotebookChatContainer.tsx

export const NotebookChatContainer: React.FC = () => {
  const { coreServicesReady, chatHistoryLoading } = useLoadingStateStore(s => ({
    coreServicesReady: s.coreServicesReady,
    chatHistoryLoading: s.chatHistoryLoading
  }));

  // Show skeleton immediately
  if (!coreServicesReady) {
    return <ChatBoxSkeleton />;
  }

  // Show skeleton with header while loading history
  if (chatHistoryLoading) {
    return (
      <div className="sage-ai-chatbox">
        <ChatBoxHeader />
        <MessageListSkeleton />
        <ChatBoxInput disabled placeholder="Loading chat history..." />
      </div>
    );
  }

  // Full component
  return <ChatBox />;
};
```

### Phase 5: Fix Duplicate Initialization Guards

#### 5.1 Module-Level Initialization Lock

```typescript
// src/ChatBox/hooks/useChatBoxInit.ts

// Module-level state to prevent duplicates
const initializationState = {
  inProgress: new Set<string>(),
  completed: new Set<string>(),
  promises: new Map<string, Promise<void>>()
};

export function useChatBoxInit() {
  const doInitialize = useCallback(async (notebookId: string) => {
    // Already completed for this notebook
    if (initializationState.completed.has(notebookId)) {
      console.log('[useChatBoxInit] Already initialized:', notebookId);
      return;
    }

    // Already in progress - wait for existing promise
    if (initializationState.inProgress.has(notebookId)) {
      console.log('[useChatBoxInit] Waiting for existing init:', notebookId);
      await initializationState.promises.get(notebookId);
      return;
    }

    // Start new initialization
    initializationState.inProgress.add(notebookId);
    useLoadingStateStore.getState().setChatHistoryLoading(true);

    const promise = (async () => {
      try {
        await initializeForNotebook(notebookId);
        initializationState.completed.add(notebookId);
      } finally {
        initializationState.inProgress.delete(notebookId);
        useLoadingStateStore.getState().setChatHistoryLoading(false);
      }
    })();

    initializationState.promises.set(notebookId, promise);
    await promise;
  }, []);

  return { doInitialize };
}
```

### Phase 6: Optimize Chat History Loading

The 740ms `ChatHistory.loadThreads.setCurrentNotebook` is primarily StateDB reads.

#### 6.1 Implement Memory-First Pattern

```typescript
// src/ChatBox/services/ChatHistoryManager.ts

export class ChatHistoryManager {
  // In-memory cache
  private notebookCache = new Map<string, NotebookData>();
  private loadPromises = new Map<string, Promise<void>>();

  async loadNotebookFromStorage(notebookId: string): Promise<void> {
    // Check memory cache first (instant)
    if (this.notebookCache.has(notebookId)) {
      console.log('[ChatHistoryManager] Using cached data');
      return;
    }

    // Already loading - wait for it
    if (this.loadPromises.has(notebookId)) {
      await this.loadPromises.get(notebookId);
      return;
    }

    // Load from StateDB
    const promise = this.loadFromStateDBAsync(notebookId);
    this.loadPromises.set(notebookId, promise);

    try {
      await promise;
    } finally {
      this.loadPromises.delete(notebookId);
    }
  }

  private async loadFromStateDBAsync(notebookId: string): Promise<void> {
    // Yield before StateDB access
    await new Promise(r => setTimeout(r, 0));

    const data = await StateDBCachingService.getValue(notebookId);

    // Yield after potentially heavy decode
    await new Promise(r => setTimeout(r, 0));

    if (data) {
      this.notebookCache.set(notebookId, data);
    }
  }

  // Pre-warm cache during idle time
  preloadRecentNotebooks(): void {
    requestIdleCallback(async () => {
      const recentIds = await this.getRecentNotebookIds();
      for (const id of recentIds.slice(0, 3)) {
        await this.loadNotebookFromStorage(id);
      }
    });
  }
}
```

### Phase 7: Web Worker for Heavy JSON Processing (Optional Enhancement)

For very large database schemas, use a Web Worker:

```typescript
// src/workers/schemaParser.worker.ts

self.onmessage = (event) => {
  const { type, data } = event.data;

  if (type === 'PARSE_SCHEMA') {
    try {
      const parsed = JSON.parse(data);
      const processed = processSchema(parsed);
      self.postMessage({ type: 'SCHEMA_PARSED', data: processed });
    } catch (error) {
      self.postMessage({ type: 'SCHEMA_ERROR', error: error.message });
    }
  }
};

function processSchema(schema: any): any {
  // Heavy processing here
  // ...
}

// Usage in main thread:
const worker = new Worker(new URL('./schemaParser.worker.ts', import.meta.url));
worker.postMessage({ type: 'PARSE_SCHEMA', data: largeSchemaJSON });
worker.onmessage = (event) => {
  if (event.data.type === 'SCHEMA_PARSED') {
    updateUIWithSchema(event.data.data);
  }
};
```

---

## Implementation Order

### Sprint 1: True Non-Blocking Activate (CRITICAL)

1. Create `DeferredInitScheduler` utility
2. Refactor `activateSignalPilot` to:
   - Return immediately with empty shells
   - Schedule all work via deferred scheduler
3. Create shell/skeleton components
4. Test that JupyterLab loads instantly

**Success Criteria**: `activate()` returns in < 50ms

### Sprint 2: Loading State System

1. Implement `useLoadingStateStore`
2. Add skeleton components for ChatBox, Settings
3. Wire loading states to UI components
4. Test progressive enhancement flow

**Success Criteria**: Users see skeleton UI immediately, content progressively appears

### Sprint 3: Lazy Database Loading

1. Implement `LazyContextLoader`
2. Remove eager database loading from startup
3. Add database loading trigger on panel mount
4. Add loading indicator for databases

**Success Criteria**: `ContextLoader.databases` no longer in startup path

### Sprint 4: Authentication Optimization

1. Implement non-blocking auth flow
2. Add cached auth state check
3. Defer profile loading to idle time
4. Test auth flow doesn't block

**Success Criteria**: Auth completes in background, UI shows immediately

### Sprint 5: Initialization Guards & History Optimization

1. Add module-level init guards
2. Implement memory-first chat history
3. Add pre-warming during idle time
4. Test duplicate prevention

**Success Criteria**: Single initialization per notebook, faster history loads

---

## Success Metrics

| Metric | Current | Target V2 |
|--------|---------|-----------|
| `activate()` return time | ~1000ms+ | < 50ms |
| Time to visible UI (skeleton) | ~500ms | < 100ms |
| Time to interactive chat | ~6000ms | < 500ms (skeleton), < 2000ms (full) |
| `initializeDemoMode` (blocking) | 168ms | 0ms (deferred) |
| `initializeAuthentication` (blocking) | 749ms | 0ms (deferred) |
| `ContextLoader.databases` (blocking) | 4836ms | 0ms (lazy loaded) |
| Duplicate initializations | 3-5x | 1x |

---

## Testing Strategy

### Unit Tests

```typescript
describe('DeferredInitScheduler', () => {
  it('processes critical tasks before high priority', async () => {
    const order: string[] = [];

    deferredInit.schedule('high', () => order.push('high'), 'high');
    deferredInit.schedule('critical', () => order.push('critical'), 'critical');

    await flushDeferredTasks();

    expect(order).toEqual(['critical', 'high']);
  });

  it('yields to event loop between tasks', async () => {
    let mainThreadBlocked = true;

    deferredInit.schedule('task', () => {
      // This should not block
    }, 'normal');

    // This should run before the scheduled task
    setTimeout(() => { mainThreadBlocked = false; }, 0);

    await flushDeferredTasks();

    expect(mainThreadBlocked).toBe(false);
  });
});
```

### Integration Tests

```typescript
describe('Startup Performance', () => {
  it('activate() returns within 50ms', async () => {
    const start = performance.now();
    await activateSignalPilot(...);
    const duration = performance.now() - start;

    expect(duration).toBeLessThan(50);
  });

  it('shows skeleton UI immediately', async () => {
    await activateSignalPilot(...);

    const chatContainer = document.querySelector('.sage-ai-chatbox');
    expect(chatContainer).toBeInTheDocument();

    const skeleton = document.querySelector('.sage-ai-chatbox-skeleton');
    expect(skeleton).toBeInTheDocument();
  });
});
```

### Manual Testing Checklist

- [ ] Open JupyterLab - launcher loads instantly
- [ ] Chat sidebar shows skeleton immediately
- [ ] Skeleton transitions to content smoothly
- [ ] Opening database panel triggers loading indicator
- [ ] Switching notebooks shows loading state briefly
- [ ] No console errors during startup
- [ ] Performance timings show < 50ms activate

---

## Rollback Plan

Each change is isolated:

1. **DeferredInitScheduler**: Remove usage, restore `await` calls
2. **Loading States**: Remove store usage, restore direct render
3. **Lazy Database**: Restore eager loading in `initializeAsyncServices`
4. **Auth Changes**: Restore blocking auth flow
5. **Init Guards**: Remove guards, allow duplicates (less efficient but works)

---

## Files to Create

- `src/utils/deferredInit.ts`
- `src/stores/loadingStateStore.ts`
- `src/Components/Skeletons/ChatBoxSkeleton.tsx`
- `src/Components/Skeletons/MessageListSkeleton.tsx`
- `src/Components/Skeletons/skeletons.css`
- `src/ChatBox/Context/LazyContextLoader.ts`

## Files to Modify

- `src/SignalPilot/activateSignalPilot.ts` - Complete refactor
- `src/SignalPilot/initialization.ts` - Non-blocking versions of init functions
- `src/SignalPilot/widgetInitialization.ts` - Create shells instead of full widgets
- `src/Notebook/NotebookChatContainer.tsx` - Add loading states
- `src/ChatBox/hooks/useChatBoxInit.ts` - Add guards
- `src/ChatBox/services/ChatHistoryManager.ts` - Memory-first pattern
- `src/ChatBox/Context/ContextCacheService.ts` - Lazy loading support

---

## References

- [Unblocking the Main Thread: Refactoring from Sync to Async in JavaScript](https://brightinventions.pl/blog/refactoring-from-sync-to-async-in-javascript/)
- [Window: requestIdleCallback() method - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Window/requestIdleCallback)
- [How to yield to the main thread](https://www.corewebvitals.io/pagespeed/yield-to-main-thread)
- [JavaScript Workers vs. Main Thread](https://dinushansriskandaraja.medium.com/javascript-workers-vs-main-thread-improving-web-performance-a790e07d38b0)
- [Minimize Main Thread Work for Website Performance](https://www.chetaru.com/minimize-main-thread-work/)
- [JupyterLab Extension Tutorial](https://jupyterlab.readthedocs.io/en/stable/extension/extension_tutorial.html)
- [Building AI Extensions for JupyterLab](https://notebook-intelligence.github.io/notebook-intelligence/blog/2025/02/05/building-ai-extensions-for-jupyterlab.html)
