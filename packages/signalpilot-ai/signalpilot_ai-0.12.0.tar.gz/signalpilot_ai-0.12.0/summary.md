# Zustand Migration Summary

**Branch:** `app-refactor-v2`

## Overview

We are migrating the Sage Agent JupyterLab extension from RxJS-based state management to Zustand. The goal is to eliminate all RxJS subscriptions and replace them with Zustand stores and React hooks for better developer experience and maintainability.

## Stores Created

These stores exist in `src/stores/`:

| Store | Purpose | Status |
|-------|---------|--------|
| `appStore.ts` | Core app state (initialization, current notebook, modes) | Active |
| `settingsStore.ts` | User preferences and API configuration | Active |
| `notebookEventsStore.ts` | Notebook change/rename events | Active |
| `diffStore.ts` | Code diff approval workflow | **Fully Migrated** |
| `snippetStore.ts` | Saved code snippets | Active |
| `contextStore.ts` | Chat context items (@mentions) | Active |
| `servicesStore.ts` | Service instance registry | Active |

---

## Session 1 - December 31, 2024

### Work Completed

1. **Created `servicesStore.ts`** - Central registry for service instances
2. **Migrated React Components** from `AppStateService.changes`:
   - `SnippetList.tsx` → `useSnippetStore` hook
   - `FileExplorerContent.tsx` → `useAppStore(selectIsDemoMode)`
   - `NotebookDeploymentButton.tsx` → `useAppStore` selector
3. **Migrated `ChatBoxWidget.tsx`** (Lumino Widget) to Zustand subscriptions
4. **Enhanced Stores** with `subscribeWithSelector` middleware
5. **Fixed `onNotebookChanged` subscription pattern** in 5 files
6. **Fixed thread name update timing**
7. **Fixed launcher/notebook state sync**

---

## Session 2 - January 5, 2025

### DiffStateService → diffStore Migration (COMPLETED)

Successfully migrated all consumers of `DiffStateService` to use `diffStore` and deleted the original RxJS service.

#### New Functions Added to `diffStore.ts`
- `subscribeToAllDiffsResolved()` - for non-React code
- `subscribeToCellDiffChange()` - for non-React code
- `getDiffState()` - convenience accessor
- `setNotebookPath()` - backwards compatibility alias

#### Files Migrated

| File | Type | Changes |
|------|------|---------|
| `NotebookDiffManager.ts` | Service | RxJS → Zustand subscribe |
| `DiffApprovalDialog.ts` | Component | RxJS → Zustand subscribe |
| `DiffNavigationWidget.tsx` | ReactWidget | RxJS → Zustand subscribe |
| `LLMStateDisplay.tsx` | ReactWidget | RxJS → Zustand subscribe |
| `LLMStateContent.tsx` | React | RxJS → Zustand subscribe |
| `DiffItem.tsx` | React | RxJS → Zustand subscribe |
| `ChatMessages.ts` | Service | RxJS → Zustand subscribe |
| `ConversationService.ts` | Service | RxJS → Zustand getState |
| `ConversationServiceUtils.ts` | Utils | RxJS → Zustand getState |

#### Deleted
- `src/Services/DiffStateService.ts` - Original RxJS-based service

---

## What's Left to Migrate

### High Priority
- [ ] `AppStateService.changes` BehaviorSubject - Remove and migrate remaining consumers
- [ ] `DeploymentStateService` - Migrate RxJS patterns

### Medium Priority
- [ ] `ContextService` - May have RxJS patterns
- [ ] `NotebookCellStateService` - Check for RxJS usage

### Final Cleanup
- [ ] Refactor `AppState.ts` to be thin wrapper or remove
- [ ] Remove all RxJS dependencies from package.json
- [ ] Final testing of all migrated components

---

## Architecture Notes

### Subscription Patterns

**For React components:** Use hooks directly
```typescript
const isDemoMode = useAppStore(selectIsDemoMode);
```

**For Lumino Widgets / TypeScript classes:** Use subscription functions
```typescript
this.unsubscribes.push(
  subscribeToDiffChanges((pendingDiffs, notebookId) => {
    // handle changes
  })
);
// In dispose():
this.unsubscribes.forEach(unsub => unsub());
```

### State Sync Strategy (Temporary)
During migration, `AppStateService` methods sync to both:
1. The old BehaviorSubject state (for legacy code)
2. The new Zustand store (for migrated code)

This will be removed once all consumers are migrated.

---

## File Locations

- Stores: `src/stores/`
- Main state: `src/AppState.ts`
- Services: `src/Services/`

## Testing Checklist

After any changes, verify:
- [ ] Diff approval workflow (approve/reject/run cells)
- [ ] Notebook switching updates thread name correctly
- [ ] Launcher ↔ notebook transitions work properly
- [ ] Auto-run checkbox syncs correctly
- [ ] Settings changes trigger service reinitialization
- [ ] Snippets can be inserted/removed
- [ ] File explorer respects demo mode
