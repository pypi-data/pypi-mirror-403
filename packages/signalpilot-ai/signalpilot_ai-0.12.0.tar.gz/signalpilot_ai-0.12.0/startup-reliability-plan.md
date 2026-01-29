# Startup Reliability & Performance Improvement Plan

## Executive Summary

This plan addresses three key issues identified from log analysis:
1. **UI Flash Issue**: Users see "New Message" component before chat history loads
2. **Slow Operations**: Several initialization steps take 500ms-5000ms+
3. **Race Conditions**: Multiple components initialize asynchronously without coordination

---

## Current State Analysis

### Startup Timeline (from logs)

```
0ms     - Plugin activation begins
0.1ms   - initializeCaching completes (✓ fast)
168-193ms - initializeDemoMode (🔴 SLOW - awaits DB initialization)
697-749ms - initializeAuthentication (🔴 SLOW - JWT + profile fetch)
1ms     - initializeCoreServices (✓ fast)
4836ms  - ContextLoader.databases (🔴 VERY SLOW)
5097ms  - NotebookSwitch.getNotebookFile (🔴 blocks on context)
740ms   - ChatHistory.loadThreads.setCurrentNotebook (🔴 SLOW)
765ms   - useChatBoxInit.doInitialize.TOTAL (🔴 SLOW)
```

### Key Issues Identified

#### Issue 1: UI Flash - "New Message" Before History
**Root Cause**: `ChatBox` renders content immediately after `isReady=true`, but chat history loading happens asynchronously. The `NewChatDisplay` component shows before `loadThreads` completes.

**Evidence from logs**:
```
Line 308: [ChatContainerContent] Rendering with notebookId: null
Line 312: [ChatboxStore] Marked as ready and fully initialized
Line 572: [ChatContainerContent] Rendering with notebookId: nb_xxx
Line 608: [ChatboxStore] Clearing messages for notebook switch
Line 858-861: [ChatHistoryManager] Loaded 1 threads (740ms later!)
Line 946: Current thread after setCurrentNotebook (message count: 1)
Line 1127: [ChatboxStore] Marked as ready and fully initialized (AGAIN)
```

#### Issue 2: Blocking Operations in Critical Path

| Operation | Time | Blocking? | Can Defer? |
|-----------|------|-----------|------------|
| `initializeDemoMode` | 168-193ms | Yes | Yes - DB init can be async |
| `initializeAuthentication` | 697-749ms | Yes | Partially - UI needs auth state |
| `ContextLoader.databases` | 4836ms | Partially | Yes - defer until needed |
| `loadThreads.setCurrentNotebook` | 740ms | Yes | Needs optimization |

#### Issue 3: Duplicate Initializations

From notebook load logs:
- `useChatBoxInit.useEffect.triggered` fires **5 times**
- `ChatHistory.loadThreads.TOTAL` fires **3 times**
- `loadNotebookFromStorage` called multiple times for same notebook

---

## Implementation Plan

### Phase 1: Add Loading States to Components (UI Polish)

#### 1.1 Create Global Loading State Store

Create `src/stores/loadingStateStore.ts`:
```typescript
interface LoadingStateStore {
  // Granular loading states
  isServicesInitialized: boolean;
  isAuthInitialized: boolean;
  isChatHistoryLoading: boolean;
  isContextLoading: boolean;

  // Derived state for UI
  get isAppReady(): boolean;
  get isChatReady(): boolean;

  // Actions
  setServicesInitialized: (value: boolean) => void;
  setAuthInitialized: (value: boolean) => void;
  setChatHistoryLoading: (value: boolean) => void;
  setContextLoading: (value: boolean) => void;
}
```

#### 1.2 Update ChatBox Component

Modify `src/ChatBox/index.tsx`:
```typescript
// Current (problematic):
if (!isReady && isInitializing) {
  return <LoadingState />;
}

// Proposed:
const isChatHistoryLoading = useLoadingStateStore(s => s.isChatHistoryLoading);

// Show loader while chat history is loading
if (!isReady || isChatHistoryLoading) {
  return (
    <div className="sage-ai-chatbox sage-ai-chatbox-loading">
      <ChatBoxHeader portalContainer={null} /> {/* Keep header visible */}
      <div className="sage-ai-chatbox-content-loading">
        <div className="sage-ai-blob-loader" />
        <span>{isChatHistoryLoading ? 'Loading chat history...' : 'Initializing...'}</span>
      </div>
      <ChatBoxInput disabled /> {/* Disabled input maintains layout */}
    </div>
  );
}
```

#### 1.3 Add Loading States to ChatBoxContent

Modify `src/ChatBox/ChatBoxContent.tsx`:
```typescript
const { messages } = useChatMessagesStore();
const isChatHistoryLoading = useLoadingStateStore(s => s.isChatHistoryLoading);

// Don't show NewChatDisplay until history is confirmed loaded
if (isChatHistoryLoading) {
  return <MessageListSkeleton />;
}

if (messages.length === 0) {
  return <NewChatDisplay />;
}
```

#### 1.4 Create Skeleton Components

Create `src/ChatBox/components/MessageListSkeleton.tsx`:
```typescript
export const MessageListSkeleton: React.FC = () => (
  <div className="sage-ai-message-list-skeleton">
    {[1, 2, 3].map(i => (
      <div key={i} className="sage-ai-message-skeleton">
        <div className="sage-ai-skeleton-avatar" />
        <div className="sage-ai-skeleton-content">
          <div className="sage-ai-skeleton-line" style={{ width: '60%' }} />
          <div className="sage-ai-skeleton-line" style={{ width: '80%' }} />
          <div className="sage-ai-skeleton-line" style={{ width: '40%' }} />
        </div>
      </div>
    ))}
  </div>
);
```

### Phase 2: Optimize Initialization Order

#### 2.1 Defer Non-Critical Operations

Modify `src/SignalPilot/initialization.ts`:

```typescript
// CURRENT (blocking):
export async function initializeDemoMode(replayId: string | null): Promise<void> {
  startTimer('initializeDemoMode');
  await useAppStore.getState().loadDemoMode();
  // DatabaseStateService init is already async - but we await it indirectly
  void import('../stores/databaseStore').then(...)
  endTimer('initializeDemoMode');
}

// PROPOSED (non-blocking):
export function initializeDemoMode(replayId: string | null): void {
  // Fire and forget - let it complete in background
  useAppStore.getState().loadDemoMode().catch(console.error);

  if (replayId) {
    useAppStore.getState().setDemoMode(true);
  }

  // DB init is already non-blocking, keep as-is
  void import('../stores/databaseStore').then(...)
}
```

#### 2.2 Parallelize Context Loading

Modify `src/ChatBox/Context/ContextCacheService.ts`:

```typescript
// CURRENT: Sequential with timeout issues
const loaders = [
  { name: 'snippets', load: loadSnippets },
  { name: 'datasets', load: loadDatasets },
  // ... including databases (4800ms!)
];

// PROPOSED: Two-tier loading
const criticalLoaders = [
  { name: 'snippets', load: loadSnippets },    // Fast, needed for UI
  { name: 'cells', load: loadCells },           // Fast, needed for context
];

const deferredLoaders = [
  { name: 'databases', load: loadDatabases },   // Slow, can load later
  { name: 'tables', load: loadTables },         // Depends on databases
  { name: 'variables', load: loadVariables },   // Needs kernel
];

// Load critical first, then deferred
await Promise.all(criticalLoaders.map(l => timedLoad(l)));
setContextLoading(false); // UI can proceed

// Load deferred in background
Promise.all(deferredLoaders.map(l => timedLoad(l))).catch(console.error);
```

#### 2.3 Add Initialization Phases

Modify `src/SignalPilot/activateSignalPilot.ts`:

```typescript
// Define clear phases
enum InitPhase {
  CRITICAL = 'critical',     // Must complete before UI
  SERVICES = 'services',     // Core services
  ASYNC = 'async',          // Can load in background
  DEFERRED = 'deferred',    // Load after UI visible
}

// Phase 1: Critical (UI can't render without these)
await Promise.all([
  initializeCaching(settingRegistry),
  initializeDemoModeSync(replayId),  // New sync version
]);

// Phase 2: Services (needed for basic functionality)
const services = initializeCoreServices(context);

// Phase 3: Signal UI Ready
signalSignalpilotInitialized();
useLoadingStateStore.getState().setServicesInitialized(true);

// Phase 4: Async operations (don't block)
void initializeAsyncServices(context, services);
void initializeAuthentication().then(() => {
  useLoadingStateStore.getState().setAuthInitialized(true);
});
```

### Phase 3: Fix Duplicate Initialization

#### 3.1 Add Initialization Guards

Modify `src/ChatBox/hooks/useChatBoxInit.ts`:

```typescript
// Add initialization tracking at module level
const initializationInProgress = new Map<string, Promise<void>>();

const doInitialize = useCallback(async (notebookId: string) => {
  // Prevent duplicate initialization
  const existing = initializationInProgress.get(notebookId);
  if (existing) {
    console.log('[useChatBoxInit] Already initializing, waiting...');
    return existing;
  }

  const initPromise = (async () => {
    try {
      // Signal loading state
      useLoadingStateStore.getState().setChatHistoryLoading(true);

      // ... existing initialization code ...

    } finally {
      useLoadingStateStore.getState().setChatHistoryLoading(false);
      initializationInProgress.delete(notebookId);
    }
  })();

  initializationInProgress.set(notebookId, initPromise);
  return initPromise;
}, [...]);
```

#### 3.2 Consolidate Notebook Change Handlers

The current code has multiple listeners for notebook changes:
1. `NotebookChatContainer.switchToNotebook`
2. `useChatBoxInit.useEffect`
3. `chatHistoryStore` notebook subscription
4. `NotebookEventsStore` subscribers

**Proposed consolidation**:

```typescript
// Single source of truth for notebook changes
// In notebookEventsStore.ts:

export const subscribeToNotebookChange = (
  handler: NotebookChangeHandler,
  options: { priority: 'high' | 'normal' | 'low' } = { priority: 'normal' }
) => {
  // Handlers execute in priority order
  // Only one initialization can run at a time
};

// Remove duplicate handlers:
// - NotebookChatContainer no longer subscribes directly
// - useChatBoxInit watches store state only
// - chatHistoryStore clears state immediately, loads async
```

### Phase 4: Optimize Slow Operations

#### 4.1 Database Context Loading

**Current**: `ContextLoader.databases` takes 4836ms

**Root Cause**: Loading database configurations involves:
1. Reading from StateDB
2. Decoding configurations
3. Fetching schema metadata (network calls)

**Optimization**:
```typescript
// In ChatContextLoaders.ts:

export async function loadDatabases(): Promise<DatabaseContext[]> {
  // Phase 1: Return cached configs immediately
  const cachedConfigs = DatabaseStateService.getCachedConfigs();
  if (cachedConfigs.length > 0) {
    return cachedConfigs; // Return immediately
  }

  // Phase 2: Load full configs in background
  void DatabaseStateService.loadConfigurations().then(configs => {
    // Update context cache when ready
    ContextCacheService.updateDatabaseContexts(configs);
  });

  return []; // Return empty for now
}
```

#### 4.2 Chat History Loading

**Current**: `loadThreads.setCurrentNotebook` takes 740ms

**Root Cause**: Synchronous StateDB reads + localStorage access

**Optimization**:
```typescript
// In ChatHistoryManager.ts:

// Add in-memory cache
private notebookCache = new Map<string, NotebookData>();

async loadNotebookFromStorage(notebookId: string): Promise<void> {
  // Check memory cache first
  if (this.notebookCache.has(notebookId)) {
    console.log('[ChatHistoryManager] Using cached notebook data');
    return;
  }

  // Load from IndexedDB instead of StateDB for better performance
  const data = await this.indexedDBService.get(notebookId);
  this.notebookCache.set(notebookId, data);
}

// Pre-load recently accessed notebooks
async preloadRecentNotebooks(): Promise<void> {
  const recentIds = await this.getRecentNotebookIds();
  await Promise.all(recentIds.slice(0, 5).map(id =>
    this.loadNotebookFromStorage(id)
  ));
}
```

### Phase 5: Testing & Validation

#### 5.1 Add Performance Markers

```typescript
// In performanceDebug.ts:

export const CRITICAL_THRESHOLDS = {
  'initializeDemoMode': 50,
  'initializeAuthentication': 200,
  'ContextLoader.databases': 100,
  'ChatHistory.loadThreads.TOTAL': 100,
  'useChatBoxInit.doInitialize.TOTAL': 200,
};

export function validateStartupPerformance(): void {
  const metrics = getPerformanceMetrics();
  const violations = [];

  for (const [operation, threshold] of Object.entries(CRITICAL_THRESHOLDS)) {
    const time = metrics[operation];
    if (time > threshold) {
      violations.push(`${operation}: ${time}ms (threshold: ${threshold}ms)`);
    }
  }

  if (violations.length > 0) {
    console.warn('[Performance] Threshold violations:', violations);
  }
}
```

#### 5.2 Add Loading State Tests

```typescript
// In __tests__/startup.test.ts:

describe('Startup Loading States', () => {
  it('shows loading indicator before chat history loads', async () => {
    render(<ChatBox />);

    // Should show loading state
    expect(screen.getByText('Loading chat history...')).toBeInTheDocument();

    // Should NOT show NewChatDisplay yet
    expect(screen.queryByText('New Chat')).not.toBeInTheDocument();

    // Wait for history to load
    await waitFor(() => {
      expect(screen.queryByText('Loading chat history...')).not.toBeInTheDocument();
    });
  });

  it('prevents duplicate initialization', async () => {
    const spy = jest.spyOn(chatHistoryStore, 'loadThreads');

    // Trigger multiple notebook changes rapidly
    notebookEventsStore.setState({ currentNotebookId: 'nb1' });
    notebookEventsStore.setState({ currentNotebookId: 'nb1' });
    notebookEventsStore.setState({ currentNotebookId: 'nb1' });

    await flushPromises();

    // Should only initialize once
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
```

---

## Implementation Order

### Sprint 1: UI Loading States (High Impact, Low Risk)
1. Create `loadingStateStore.ts`
2. Add `MessageListSkeleton` component
3. Update `ChatBox` to use loading states
4. Update `ChatBoxContent` to show skeleton during load
5. Wire loading states in `useChatBoxInit` and `chatHistoryStore`

### Sprint 2: Initialization Optimization (Medium Impact, Medium Risk)
1. Make `initializeDemoMode` non-blocking
2. Implement two-tier context loading
3. Add initialization guards to prevent duplicates
4. Optimize `ChatHistoryManager` with caching

### Sprint 3: Architecture Improvements (High Impact, Higher Risk)
1. Consolidate notebook change handlers
2. Implement initialization phases
3. Add IndexedDB for chat history (optional)
4. Add performance validation

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to first paint | ~500ms | <200ms |
| Time to interactive chat | ~6000ms | <1000ms |
| UI flash occurrences | Every load | Never |
| Duplicate initializations | 3-5x | 1x |
| `initializeDemoMode` | 168ms | <50ms |
| `ContextLoader.databases` (blocking) | 4836ms | <100ms (deferred) |
| `ChatHistory.loadThreads` | 745ms | <100ms |

---

## Rollback Plan

Each phase can be rolled back independently:
1. **Loading states**: Remove `loadingStateStore` usage, revert to `isReady` check
2. **Initialization**: Revert `initialization.ts` changes, restore `await` calls
3. **Architecture**: Feature flag new handlers, fall back to existing

---

## Files to Modify

### New Files
- `src/stores/loadingStateStore.ts`
- `src/ChatBox/components/MessageListSkeleton.tsx`
- `src/ChatBox/components/MessageListSkeleton.css`

### Modified Files
- `src/ChatBox/index.tsx` - Add loading states
- `src/ChatBox/ChatBoxContent.tsx` - Use skeleton during load
- `src/ChatBox/hooks/useChatBoxInit.ts` - Add guards, wire loading states
- `src/stores/chatHistoryStore.ts` - Signal loading state
- `src/SignalPilot/initialization.ts` - Defer non-critical operations
- `src/SignalPilot/activateSignalPilot.ts` - Add initialization phases
- `src/ChatBox/Context/ContextCacheService.ts` - Two-tier loading
- `src/ChatBox/services/ChatHistoryManager.ts` - Add caching
