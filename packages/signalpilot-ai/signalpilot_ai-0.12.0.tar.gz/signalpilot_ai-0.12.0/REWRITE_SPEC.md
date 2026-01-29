# REWRITE_SPEC.md

## Migration Plan: Current State → Master Spec Target

This document outlines the remaining work to align the codebase with `00-MASTER-SPEC.md` after the initial Zustand migration and React conversion.

---

## 1. Current State Summary

### 1.1 Zustand Migration (COMPLETED)

The Zustand migration is complete with 11 stores:

| Store | Lines | Status | Notes |
|-------|-------|--------|-------|
| `appStore.ts` | 211 | Complete | Core app state |
| `appStateStore.ts` | 257 | **Needs Refactor** | Still holds service references |
| `settingsStore.ts` | 130 | Complete | Persisted to localStorage |
| `diffStore.ts` | 517 | Complete | Diff approval workflow |
| `contextStore.ts` | 144 | Complete | Chat context mentions |
| `snippetStore.ts` | 285 | Complete | Code snippets |
| `deploymentStore.ts` | 291 | Complete | Notebook deployment |
| `databaseStore.ts` | 1,666 | Complete | Database connections |
| `databaseMetadataCacheStore.ts` | 628 | Complete | Schema cache |
| `notebookEventsStore.ts` | 213 | Complete | Event emitter pattern |

### 1.2 React Migration Status

Mixed state - some components converted, others still Lumino-based:

| Category | Converted | Remaining |
|----------|-----------|-----------|
| Chat UI | Partial | ChatBoxWidget still hybrid |
| Settings | Yes | - |
| Diff Navigation | Partial | Still uses Lumino base |
| State Displays | Partial | LLMStateDisplay, PlanStateDisplay hybrid |
| Input Components | Partial | RichTextChatInput still DOM-based |

### 1.3 What's Working

- Zustand stores with devtools integration
- subscribeWithSelector middleware for external subscriptions
- Settings persistence to localStorage
- Basic React components rendering via ReactWidget
- AppStateService facade for backward compatibility

---

## 2. Gap Analysis

### 2.1 Architecture Gaps

| Gap | Current | Target (Master Spec) | Priority |
|-----|---------|---------------------|----------|
| Service instances in state | `appStateStore` holds ToolService, ChatService, etc. | Services via Context/DI, not in stores | HIGH |
| AppStateService facade | 1,286-line compatibility layer | Delete entirely | HIGH |
| Dual store pattern | `appStore` + `appStateStore` unclear split | Single `appStore` or clear domains | MEDIUM |
| UI Bridge | Not implemented | `uiBridge.ts` for sendMessage, focusInput | MEDIUM |
| Map serialization | `Map<>` in diffStore, contextStore | Convert to object/array for DevTools | LOW |

### 2.2 Component Gaps

| Component | Current State | Target | Priority |
|-----------|--------------|--------|----------|
| ChatBoxWidget | Lumino Widget with React children | Pure React `ChatPanel` | HIGH |
| ChatMessages | TypeScript DOM class | React `MessageList` | HIGH |
| ChatInputManager | TypeScript DOM class | React `ChatInput` | HIGH |
| RichTextChatInput | contentEditable DOM class | React `RichTextInput` | HIGH |
| ThreadManager | TypeScript DOM class | React `ThreadSelector` | HIGH |
| LLMStateDisplay | ReactWidget with subscriptions | Pure React component | MEDIUM |
| PlanStateDisplay | ReactWidget with Lumino Signals | Pure React component | MEDIUM |
| WaitingUserReplyBoxManager | DOM manager | React component | MEDIUM |

### 2.3 Store Gaps

| Gap | Current | Target |
|-----|---------|--------|
| No `chatStore` | Messages managed imperatively | Zustand `chatStore` with messages, threads |
| No `uiStore` | UI state scattered | Dedicated store for panels, visibility |
| appStateStore too large | 27 properties | Split into feature stores |

---

## 3. Migration Phases

### Phase A: Store Consolidation (Foundation)
**Goal**: Clean up store architecture before component migration

### Phase B: Chat Component Migration (Core UI)
**Goal**: Convert chat system to pure React

### Phase C: Supporting Components (Complete UI)
**Goal**: Convert remaining components

### Phase D: Cleanup (Final)
**Goal**: Remove legacy code, finalize architecture

---

## 4. Component Migration Checklist

### 4.1 Phase A: Store Consolidation

#### A1. Create chatStore
- [ ] Create `src/stores/chatStore.ts`
- [ ] Move message state from ChatMessages to store
- [ ] Move thread state from ThreadManager to store
- [ ] Add streaming state management
- [ ] Add tool call tracking

**Test Checkpoint A1**: Store can add/update/remove messages, switch threads

#### A2. Create uiBridge
- [ ] Create `src/stores/uiBridge.ts`
- [ ] Define IUIBridge interface
- [ ] Implement bridge registration
- [ ] Add sendMessage, focusInput, getInputValue, setInputValue

**Test Checkpoint A2**: External code can call sendMessage via bridge

#### A3. Refactor appStateStore
- [ ] Remove service instances (ToolService, ChatService, etc.)
- [ ] Move services to React Context or service locator
- [ ] Remove UI container references
- [ ] Keep only serializable state

**Test Checkpoint A3**: Services accessible without stores, DevTools shows clean state

#### A4. Merge/clarify appStore + appStateStore
- [ ] Audit both stores for overlap
- [ ] Consolidate into single appStore OR
- [ ] Define clear domain boundaries
- [ ] Update all consumers

**Test Checkpoint A4**: Single clear store hierarchy, no confusion

---

### 4.2 Phase B: Chat Component Migration

#### B1. MessageList Component
**Current**: `src/Chat/ChatMessages.ts` (imperative DOM)
**Target**: `src/Components/Chat/MessageList.tsx`

- [ ] Create MessageList.tsx
- [ ] Create UserMessage.tsx
- [ ] Create AssistantMessage.tsx
- [ ] Create StreamingMessage.tsx with cursor
- [ ] Create ToolCallCard.tsx with expand/collapse
- [ ] Connect to chatStore for messages
- [ ] Implement auto-scroll on new messages
- [ ] Add markdown rendering

**Test Checkpoint B1**: Messages render correctly, streaming works, tool calls display

#### B2. ChatInput Component
**Current**: `src/Chat/ChatInputManager.ts` + `src/Chat/RichTextChatInput.ts`
**Target**: `src/Components/Chat/ChatInput.tsx`

- [ ] Create ChatInput.tsx
- [ ] Create RichTextInput.tsx (contentEditable wrapper)
- [ ] Create MentionInput.tsx for @ mentions
- [ ] Create SendButton.tsx
- [ ] Register with UI Bridge
- [ ] Handle Enter to send, Shift+Enter for newline
- [ ] Connect to contextStore for mentions

**Test Checkpoint B2**: Input works, mentions work, send triggers message flow

#### B3. ChatHeader Component
**Current**: Part of ChatBoxWidget
**Target**: `src/Components/Chat/ChatHeader.tsx`

- [ ] Create ChatHeader.tsx
- [ ] Create ThreadSelector.tsx
- [ ] Create NewChatButton.tsx
- [ ] Create MoreOptionsButton.tsx
- [ ] Connect to chatStore for threads

**Test Checkpoint B3**: Thread switching works, new chat creates thread

#### B4. ChatPanel Component
**Current**: `src/Components/ChatboxWidget/ChatBoxWidget.tsx` (hybrid)
**Target**: `src/Components/Chat/ChatPanel.tsx`

- [ ] Create ChatPanel.tsx as pure React root
- [ ] Compose MessageList, ChatInput, ChatHeader
- [ ] Create ChatPanelWidget.tsx (ReactWidget wrapper)
- [ ] Wire up to ConversationService
- [ ] Handle abort/cancel

**Test Checkpoint B4**: Full chat flow works - send message → stream → tool calls → response

#### B5. State Display Components
**Current**: `src/Components/LLMStateDisplay/`, `src/Components/PlanStateDisplay.tsx`
**Target**: Pure React components

- [ ] Create LLMStateIndicator.tsx
- [ ] Create PlanIndicator.tsx
- [ ] Remove Lumino base class
- [ ] Remove manual subscriptions (use hooks)
- [ ] Connect to relevant stores

**Test Checkpoint B5**: States display correctly, no subscription leaks

#### B6. Diff Navigation Component
**Current**: `src/Components/DiffNavigationWidget.tsx`
**Target**: `src/Components/Chat/DiffNavigator.tsx`

- [ ] Create DiffNavigator.tsx
- [ ] Connect to diffStore
- [ ] Implement accept/reject all
- [ ] Implement navigation between diffs

**Test Checkpoint B6**: Diffs navigate correctly, accept/reject works

#### B7. Approval Dialog Component
**Current**: Inline in ChatMessages
**Target**: `src/Components/Chat/ApprovalDialog.tsx`

- [ ] Create ApprovalDialog.tsx
- [ ] Show tool call details
- [ ] Handle approve/reject
- [ ] Connect to chatStore requestStatus

**Test Checkpoint B7**: Approval flow works end-to-end

#### B8. WaitingUserReply Component
**Current**: `src/Notebook/WaitingUserReplyBoxManager.ts`
**Target**: `src/Components/Chat/WaitingUserReplyBox.tsx`

- [ ] Create WaitingUserReplyBox.tsx
- [ ] Handle user reply input
- [ ] Connect to relevant store state

**Test Checkpoint B8**: User reply prompts work correctly

---

### 4.3 Phase C: Supporting Components

#### C1. Settings Components
**Current**: `src/Components/Settings/SettingsWidget.tsx`
**Status**: Mostly converted

- [ ] Audit for any remaining imperative patterns
- [ ] Ensure pure React with hooks
- [ ] Connect to settingsStore

**Test Checkpoint C1**: All settings save and persist correctly

#### C2. File Explorer
**Current**: `src/Components/FileExplorerWidget/FileExplorerWidget.tsx`
**Status**: Partial conversion

- [ ] Remove polling patterns
- [ ] Use store subscriptions
- [ ] Ensure pure React

**Test Checkpoint C2**: File tree renders, selection works

#### C3. Database Manager
**Current**: `src/Components/DatabaseManagerWidget/DatabaseManagerWidget.tsx`
**Status**: Partial conversion

- [ ] Remove DatabaseStateService RxJS
- [ ] Connect to databaseStore
- [ ] Ensure pure React

**Test Checkpoint C3**: Database connections work, metadata displays

#### C4. Snippet Components
**Current**: `src/Components/SnippetCreationWidget/`
**Status**: Partial conversion

- [ ] Remove Lumino Signals
- [ ] Remove AppStateService usage
- [ ] Connect to snippetStore

**Test Checkpoint C4**: Snippet creation/insertion works

#### C5. Banner Components
**Current**: Various banner widgets
**Status**: Simple wrappers, mostly done

- [ ] TrialBannerWidget - verify pure React
- [ ] SessionTimerBannerWidget - verify pure React
- [ ] UpdateBannerWidget - verify pure React

**Test Checkpoint C5**: Banners display correctly

#### C6. Modal Components
**Current**: Service-embedded modals
**Target**: React components

- [ ] FirstRunModal - convert to React
- [ ] LoginSuccessToast - convert to React
- [ ] JWTAuthModal - convert to React
- [ ] CheckpointRestorationModal - convert to React

**Test Checkpoint C6**: Modals open/close correctly

#### C7. Welcome & Demo Components
**Current**: Lumino widgets
**Status**: Low priority

- [ ] WelcomeComponent - convert to React
- [ ] NewChatDisplayWidget - convert to React
- [ ] DemoControlPanel - convert to React

**Test Checkpoint C7**: Welcome flow works, demo mode works

---

### 4.4 Phase D: Cleanup

#### D1. Delete Legacy Code
- [ ] Delete `src/Chat/ChatMessages.ts`
- [ ] Delete `src/Chat/ChatInputManager.ts`
- [ ] Delete `src/Chat/RichTextChatInput.ts`
- [ ] Delete `src/ThreadManager.ts`
- [ ] Delete old Lumino widget files
- [ ] Delete `src/AppState.ts` (AppStateService)

**Test Checkpoint D1**: Build succeeds, no dead imports

#### D2. Remove RxJS
- [ ] Search for remaining RxJS usage
- [ ] Convert any remaining subscriptions
- [ ] Remove rxjs from package.json
- [ ] Verify no Observable/BehaviorSubject imports

**Test Checkpoint D2**: Build succeeds without RxJS

#### D3. Final Store Cleanup
- [ ] Convert Map to object in diffStore if needed
- [ ] Convert Map to object in contextStore if needed
- [ ] Verify all stores are serializable
- [ ] Verify Redux DevTools works for all stores

**Test Checkpoint D3**: DevTools shows all state correctly

#### D4. Documentation Update
- [ ] Update CLAUDE.md with new architecture
- [ ] Update README with component structure
- [ ] Add store documentation
- [ ] Add component documentation

**Test Checkpoint D4**: New developer can understand architecture

---

## 5. Verification Checkpoints

### Checkpoint 1: After Phase A (Store Foundation)
Run these verifications:
```bash
# Build succeeds
jlpm build

# All tests pass
jlpm test

# Verify store state in DevTools
# - chatStore has messages array
# - uiBridge is registered
# - appStateStore has no service instances
```

### Checkpoint 2: After Phase B (Core Chat UI)
Manual verification:
- [ ] Send a message → response streams correctly
- [ ] Tool calls display with expand/collapse
- [ ] Approval dialog appears for restricted tools
- [ ] Accept/reject diffs works
- [ ] Thread switching works
- [ ] New chat creates new thread
- [ ] Message history loads correctly

### Checkpoint 3: After Phase C (Supporting Components)
Manual verification:
- [ ] Settings panel opens and saves
- [ ] File explorer shows files
- [ ] Database manager connects/disconnects
- [ ] Snippets can be created and inserted
- [ ] All banners display when triggered

### Checkpoint 4: After Phase D (Final)
Full regression test:
```bash
# Clean build
jlpm clean:all && jlpm build

# All tests pass
jlpm test

# Lint passes
jlpm lint:check

# No RxJS
grep -r "from 'rxjs'" src/ # Should return nothing
grep -r "BehaviorSubject" src/ # Should return nothing
```

---

## 6. Component File Mapping

### New File Structure

```
src/
├── stores/
│   ├── appStore.ts          (exists, keep)
│   ├── chatStore.ts         (NEW)
│   ├── diffStore.ts         (exists, keep)
│   ├── contextStore.ts      (exists, keep)
│   ├── settingsStore.ts     (exists, keep)
│   ├── snippetStore.ts      (exists, keep)
│   ├── deploymentStore.ts   (exists, keep)
│   ├── databaseStore.ts     (exists, keep)
│   ├── uiBridge.ts          (NEW)
│   └── index.ts
├── Components/
│   ├── Chat/                 (NEW directory)
│   │   ├── ChatPanel.tsx
│   │   ├── ChatPanelWidget.tsx
│   │   ├── MessageList.tsx
│   │   ├── Message.tsx
│   │   ├── UserMessage.tsx
│   │   ├── AssistantMessage.tsx
│   │   ├── StreamingMessage.tsx
│   │   ├── ToolCallCard.tsx
│   │   ├── ChatInput.tsx
│   │   ├── RichTextInput.tsx
│   │   ├── MentionInput.tsx
│   │   ├── SendButton.tsx
│   │   ├── ChatHeader.tsx
│   │   ├── ThreadSelector.tsx
│   │   ├── NewChatButton.tsx
│   │   ├── DiffNavigator.tsx
│   │   ├── ApprovalDialog.tsx
│   │   ├── WaitingUserReplyBox.tsx
│   │   ├── LLMStateIndicator.tsx
│   │   └── PlanIndicator.tsx
│   ├── Settings/             (exists, audit)
│   ├── FileExplorer/         (exists, audit)
│   ├── Database/             (exists, audit)
│   └── ...
├── services/                 (NEW - service locator)
│   └── ServiceContext.tsx
└── ...
```

### Files to Delete

```
DELETE: src/AppState.ts
DELETE: src/Chat/ChatMessages.ts
DELETE: src/Chat/ChatInputManager.ts
DELETE: src/Chat/RichTextChatInput.ts
DELETE: src/ThreadManager.ts
DELETE: src/Components/ChatboxWidget/ChatBoxWidget.tsx (after ChatPanel done)
DELETE: src/Notebook/WaitingUserReplyBoxManager.ts (after React version done)
DELETE: src/stores/appStateStore.ts (after refactor)
```

---

## 7. Estimated Effort

| Phase | Tasks | Estimated Days |
|-------|-------|----------------|
| Phase A: Store Consolidation | 4 tasks | 2-3 days |
| Phase B: Chat Components | 8 tasks | 5-7 days |
| Phase C: Supporting Components | 7 tasks | 3-4 days |
| Phase D: Cleanup | 4 tasks | 2-3 days |
| **Total** | **23 tasks** | **12-17 days** |

---

## 8. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking chat during migration | Keep ChatBoxWidget working until ChatPanel complete |
| Message history loss | Test persistence at each checkpoint |
| Streaming interruption | Verify streaming at Checkpoint 2 |
| contentEditable quirks | Test RichTextInput extensively |
| Service access issues | Create ServiceContext before removing from stores |

---

## 9. Success Criteria

The migration is complete when:

1. **No Lumino Widgets**: All UI is React components wrapped in ReactWidget
2. **No RxJS**: Zero Observable/BehaviorSubject usage
3. **No AppStateService**: Deleted entirely
4. **Clean Stores**: No service instances in stores, all serializable
5. **UI Bridge**: External code uses bridge for chat interactions
6. **All Tests Pass**: `jlpm test` succeeds
7. **DevTools Work**: All store state visible in Redux DevTools
8. **Feature Parity**: All existing features work identically

---

*Document Version: 1.0*
*Created: January 2026*
*Based on: 00-MASTER-SPEC.md v2.1*
