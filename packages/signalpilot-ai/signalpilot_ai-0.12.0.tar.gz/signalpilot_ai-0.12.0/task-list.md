# Refactor Task List

Based on `00-MASTER-SPEC.md` - organized by human execution order.

---

## Current: Lumino Widget to ReactWidget Conversion

Converting pure Lumino widgets to ReactWidget (keeping DOM manipulation intact for now):

- [x] NotebookSettingsContainer (`src/NotebookSettingsContainer.tsx`)
- [x] NotebookChatContainer (`src/Notebook/NotebookChatContainer.tsx`)
- [x] ChatBoxWidget (`src/Components/chatbox.tsx`)
- [x] WelcomeComponent (`src/Components/WelcomeComponent.tsx`)
- [x] NewChatDisplayWidget (`src/Components/NewChatDisplayWidget.tsx`)
- [x] DemoControlPanel (`src/Demo/DemoControlPanel.tsx`)

---

## Phase 1: Simple React Conversion

**Goal**: Convert existing components to proper React patterns. This enables Zustand integration and makes the codebase easier to test incrementally.

### 1.1 Setup & Infrastructure
- [ ] Verify React/ReactWidget infrastructure is properly configured
- [ ] Create `src/Components/ChatBox/` directory structure for new components
- [ ] Set up component testing environment (Jest + React Testing Library)

### 1.2 Simple React Conversions Checklist

These components are already `ReactWidget`-based but need cleanup (remove RxJS subscriptions, imperative methods, class-based patterns):

| # | Component | File | Issues to Fix | Priority |
|---|-----------|------|---------------|----------|
| [ ] 1 | LLMStateDisplay | `Components/LLMStateDisplay/LLMStateDisplay.tsx` | RxJS subscriptions, imperative show/hide | HIGH |
| [ ] 2 | PlanStateDisplay | `Components/PlanStateDisplay.tsx` | Lumino Signals, imperative methods | HIGH |
| [ ] 3 | DiffNavigationWidget | `Components/DiffNavigationWidget.tsx` | RxJS subscriptions, class-based visibility | HIGH |
| [ ] 4 | MoreOptionsDisplay | `Components/MoreOptionsDisplay.tsx` | Imperative popover management | MEDIUM |
| [ ] 5 | SettingsWidget | `Components/Settings/SettingsWidget.tsx` | Service dependencies, form state | MEDIUM |
| [ ] 6 | FileExplorerWidget | `Components/FileExplorerWidget/FileExplorerWidget.tsx` | Polling, cache subscriptions | MEDIUM |
| [ ] 7 | DatabaseManagerWidget | `Components/DatabaseManagerWidget/DatabaseManagerWidget.tsx` | DatabaseStateService RxJS | MEDIUM |
| [ ] 8 | NotebookDeploymentButtonWidget | `Components/NotebookDeploymentButton.tsx` | DeploymentStateService RxJS | MEDIUM |
| [ ] 9 | SnippetCreationWidget | `Components/SnippetCreationWidget/SnippetCreationWidget.tsx` | Lumino Signals, AppStateService | MEDIUM |
| [ ] 10 | HTMLPreviewWidget | `Components/HTMLPreviewWidget.tsx` | Lifecycle methods | LOW |
| [ ] 11 | TrialBannerWidget | `Components/TrialBanner/TrialBannerWidget.tsx` | Simple wrapper (minimal changes) | LOW |
| [ ] 12 | SessionTimerBannerWidget | `Components/SessionTimerBanner/SessionTimerBannerWidget.tsx` | Session state | LOW |
| [ ] 13 | UpdateBannerWidget | `Components/UpdateBanner/UpdateBannerWidget.tsx` | Extension model | LOW |
| [ ] 14 | MCPManagerWidget | `Components/MCPManagerWidget/MCPManagerWidget.tsx` | Simple wrapper (minimal changes) | LOW |
| [ ] 15 | ReplayLoadingOverlayWidget | `Components/ReplayLoadingOverlay/ReplayLoadingOverlayWidget.tsx` | Imperative show/hide | LOW |

### 1.3 Service-Embedded ReactWidgets (Simple Cleanup)

| # | Component | File | Priority |
|---|-----------|------|----------|
| [ ] 16 | FirstRunModalWidget | `Services/FirstRunModalService.ts` | LOW |
| [ ] 17 | LoginSuccessToastWidget | `Services/LoginSuccessModalService.ts` | LOW |
| [ ] 18 | JWTAuthModalWidget | `Services/JWTAuthModalService.ts` | LOW |

### 1.4 Phase 1 Validation Checkpoint
- [ ] All converted components render correctly
- [ ] No RxJS subscriptions in converted components
- [ ] Components use React hooks properly
- [ ] TypeScript compiles without errors
- [ ] Existing functionality preserved

---

## Phase 2: Zustand Conversion

**Goal**: Replace RxJS `BehaviorSubject` patterns with Zustand stores. Keep the app behavior similar to current RxJS patterns but use Zustand's simpler mental model.

### 2.1 Install & Setup Zustand
- [ ] Run `npm install zustand`
- [ ] Create `src/stores/` directory
- [ ] Create `src/stores/index.ts` for exports

### 2.2 Create Zustand Stores

| # | Store | Key State | Priority |
|---|-------|-----------|----------|
| [ ] 1 | `appStore.ts` | isInitialized, currentNotebookId, settings, isDemoMode, isTakeoverMode | HIGH |
| [ ] 2 | `chatStore.ts` | messages, streamingMessageId, currentThreadId, threads, requestStatus, currentToolCall | HIGH |
| [ ] 3 | `diffStore.ts` | pendingDiffs, currentDiffIndex, diffOrder | HIGH |
| [ ] 4 | `contextStore.ts` | contextCache, workspaceContext, snippets, scannedDirectories | MEDIUM |
| [ ] 5 | `uiStore.ts` | UI-specific state (visibility flags, etc.) | MEDIUM |
| [ ] 6 | `uiBridge.ts` | sendMessage, focusInput, setInputValue, getInputValue, scrollToBottom | MEDIUM |

### 2.3 Parallel State Sync (Temporary Bridge)
- [ ] Add Zustand sync to `AppStateService.setState()` calls
- [ ] Both systems run in parallel during migration
- [ ] Verify state consistency between RxJS and Zustand

### 2.4 Migrate Consumers to Zustand

| # | Consumer | Current Pattern | Priority |
|---|----------|-----------------|----------|
| [ ] 1 | ChatBoxWidget | RxJS subscriptions | HIGH |
| [ ] 2 | ChatMessages | RxJS subscriptions | HIGH |
| [ ] 3 | ConversationService | AppStateService calls | HIGH |
| [ ] 4 | ThreadManager | RxJS subscriptions | HIGH |
| [ ] 5 | NotebookDiffManager | RxJS subscriptions | HIGH |
| [ ] 6 | LLMStateDisplay | RxJS subscriptions | MEDIUM |
| [ ] 7 | PlanStateDisplay | Lumino Signals | MEDIUM |
| [ ] 8 | Settings components | AppStateService | MEDIUM |

### 2.5 Phase 2 Validation Checkpoint
- [ ] All stores working with TypeScript interfaces
- [ ] Consumers using Zustand selectors
- [ ] State updates propagate correctly
- [ ] Parallel sync working (RxJS and Zustand in agreement)

---

## Phase 3: Modularization & Significant Rewrites

**Goal**: This is the major rewrite phase. Convert all remaining Lumino widgets and DOM managers to React, remove circular dependencies, and clean up the architecture.

### 3.1 Significant Rewrites Checklist

These components require full rewrites (Lumino widgets and native DOM managers):

#### 3.1.1 Lumino Widget-Based (Full Conversion to React)

| # | Component | File | Lines | Priority |
|---|-----------|------|-------|----------|
| [ ] 1 | ChatBoxWidget | `Components/chatbox.ts` | 1,887 | **CRITICAL** |
| [ ] 2 | NotebookChatContainer | `Notebook/NotebookChatContainer.ts` | ~150 | HIGH |
| [ ] 3 | NewChatDisplayWidget | `Components/NewChatDisplayWidget.ts` | ~200 | MEDIUM |
| [ ] 4 | NotebookSettingsContainer | `NotebookSettingsContainer.ts` | ~80 | MEDIUM |
| [ ] 5 | WelcomeComponent | `Components/WelcomeComponent.ts` | ~120 | LOW |
| [ ] 6 | DemoControlPanel | `Demo/DemoControlPanel.ts` | ~200 | LOW |

#### 3.1.2 Native TypeScript DOM Managers (Full Conversion to React)

| # | Component | File | Lines | Priority |
|---|-----------|------|-------|----------|
| [ ] 7 | ChatInputManager | `Chat/ChatInputManager.ts` | 1,716 | **CRITICAL** |
| [ ] 8 | ChatMessages | `Chat/ChatMessages.ts` | 3,314 | **CRITICAL** |
| [ ] 9 | RichTextChatInput | `Chat/RichTextChatInput.ts` | ~300 | **CRITICAL** |
| [ ] 10 | ThreadManager | `ThreadManager.ts` | 494 | HIGH |
| [ ] 11 | WaitingUserReplyBoxManager | `Notebook/WaitingUserReplyBoxManager.ts` | ~150 | HIGH |
| [ ] 12 | CheckpointRestorationModal | `Components/CheckpointRestorationModal.ts` | ~150 | MEDIUM |
| [ ] 13 | JwtTokenDialog | `Components/JwtTokenDialog.ts` | ~200 | LOW |
| [ ] 14 | CodebaseManager | `CodebaseManager.ts` | ~300 | LOW |

#### 3.1.3 Helper/Utility DOM Classes

| # | Component | File | Priority |
|---|-----------|------|----------|
| [ ] 15 | ChatContextMenu | `Chat/ChatContextMenu/ChatContextMenu.ts` | MEDIUM |
| [ ] 16 | ContextCellHighlighter | `Chat/ChatContextMenu/ContextCellHighlighter.ts` | LOW |
| [ ] 17 | NotebookDiffTools | `Notebook/NotebookDiffTools.ts` | MEDIUM |
| [ ] 18 | InlineDiffService | `Notebook/InlineDiffService.ts` | MEDIUM |

#### 3.1.4 CodeMirror Widgets (Special Handling)

| # | Component | File | Priority |
|---|-----------|------|----------|
| [ ] 19 | InlineCompletionWidget | `Components/InlineCompletionWidget.tsx` | MEDIUM |
| [ ] 20 | GhostTextWidget | `Components/InlineCompletionWidget.tsx` | MEDIUM |

### 3.2 Build New React Chat Panel

Create the new React component tree:

```
ChatPanelWidget (ReactWidget wrapper)
└── ChatPanel (React)
    ├── ChatHeader
    │   ├── ThreadSelector
    │   ├── NewChatButton
    │   └── SettingsButton
    ├── MessageList
    │   ├── Message (repeated)
    │   │   ├── UserMessage
    │   │   ├── AssistantMessage
    │   │   │   └── StreamingContent
    │   │   └── ToolCallMessage
    │   │       ├── ToolCallCard
    │   │       └── ToolResultCard
    │   └── TypingIndicator
    ├── ApprovalDialog (conditional)
    ├── DiffNavigator (conditional)
    └── ChatInput
        ├── MentionInput (RichTextInput replacement)
        ├── AttachmentList
        └── SendButton
```

| # | Task | Components | Priority |
|---|------|------------|----------|
| [ ] 1 | Create leaf components | TypingIndicator, SendButton, NewChatButton | HIGH |
| [ ] 2 | Create message components | UserMessage, StreamingMessage, AssistantMessage | HIGH |
| [ ] 3 | Create tool call components | ToolCallCard, ToolResultCard, ToolCallMessage | HIGH |
| [ ] 4 | Create Message wrapper | Message (switches on role) | HIGH |
| [ ] 5 | Create MessageList | MessageList with auto-scroll | HIGH |
| [ ] 6 | Create ChatInput | RichTextInput (contentEditable), AttachmentList | HIGH |
| [ ] 7 | Create ChatHeader | ThreadSelector, buttons | MEDIUM |
| [ ] 8 | Create ApprovalDialog | Tool approval flow | HIGH |
| [ ] 9 | Create DiffNavigator | Diff accept/reject navigation | HIGH |
| [ ] 10 | Create ChatPanel | Root component | HIGH |
| [ ] 11 | Create ChatPanelWidget | ReactWidget wrapper for JupyterLab | HIGH |

### 3.3 Remove Circular Dependencies
- [ ] Audit `AppStateService` for circular references
- [ ] Remove component references from state (use UI Bridge pattern)
- [ ] Extract shared interfaces to prevent import cycles
- [ ] Verify no service → component → service chains

### 3.4 Remove AppStateService & RxJS
- [ ] Remove `AppStateService` class
- [ ] Remove RxJS dependency from `package.json`
- [ ] Update all imports throughout codebase
- [ ] Delete old Lumino widget files
- [ ] Delete old DOM manager files

### 3.5 Phase 3 Validation Checkpoint
- [ ] All 38 components converted or wrapped
- [ ] No RxJS in codebase
- [ ] No circular dependencies
- [ ] All Zustand stores sole source of truth
- [ ] TypeScript compiles without errors
- [ ] ESLint passes

---

## Phase 4: Bug Fix & Polish

**Goal**: Budget ~1 day for testing and fixing issues caused by the refactor.

### 4.1 End-to-End Testing
- [ ] Test: Open notebook → Chat appears
- [ ] Test: Send message → Stream response displays
- [ ] Test: Tool call → Approval dialog → Execute → Result displays
- [ ] Test: Diff appears → Accept/Reject → Cell updated
- [ ] Test: Thread persistence → Close/reopen → History restored
- [ ] Test: Thread switching → Messages update correctly
- [ ] Test: Context menu → Add/remove cells from context
- [ ] Test: Settings → Changes persist
- [ ] Test: Database connection → Metadata loads
- [ ] Test: File explorer → Files display correctly

### 4.2 Regression Testing
- [ ] Run full Jest test suite
- [ ] Fix any failing tests
- [ ] Add new tests for converted components
- [ ] Verify test coverage maintained

### 4.3 Performance Validation
- [ ] Benchmark message rendering (< 5% regression)
- [ ] Benchmark streaming performance
- [ ] Check memory usage (no leaks from old subscriptions)
- [ ] Verify smooth scrolling in long conversations

### 4.4 Final Cleanup
- [ ] Remove dead code
- [ ] Update imports
- [ ] Fix any TypeScript errors
- [ ] Run ESLint and fix issues
- [ ] Update README if needed

### 4.5 Definition of Done
- [ ] All tests passing
- [ ] No console errors
- [ ] All features work as before
- [ ] Performance acceptable
- [ ] Code review complete

---

## Summary: Component Categories

### Simple React Conversions (18 components)
Components already using ReactWidget that need RxJS/imperative cleanup:
1. LLMStateDisplay
2. PlanStateDisplay
3. DiffNavigationWidget
4. MoreOptionsDisplay
5. SettingsWidget
6. FileExplorerWidget
7. DatabaseManagerWidget
8. NotebookDeploymentButtonWidget
9. SnippetCreationWidget
10. HTMLPreviewWidget
11. TrialBannerWidget
12. SessionTimerBannerWidget
13. UpdateBannerWidget
14. MCPManagerWidget
15. ReplayLoadingOverlayWidget
16. FirstRunModalWidget
17. LoginSuccessToastWidget
18. JWTAuthModalWidget

### Significant Rewrites (20 components)
Components requiring full conversion from Lumino/DOM to React:

**Critical (core chat functionality):**
1. ChatBoxWidget (1,887 lines)
2. ChatMessages (3,314 lines)
3. ChatInputManager (1,716 lines)
4. RichTextChatInput (~300 lines)

**High Priority:**
5. NotebookChatContainer
6. ThreadManager
7. WaitingUserReplyBoxManager

**Medium Priority:**
8. NewChatDisplayWidget
9. NotebookSettingsContainer
10. CheckpointRestorationModal
11. ChatContextMenu
12. NotebookDiffTools
13. InlineDiffService
14. InlineCompletionWidget
15. GhostTextWidget

**Low Priority:**
16. WelcomeComponent
17. DemoControlPanel
18. JwtTokenDialog
19. CodebaseManager
20. ContextCellHighlighter

---

## Estimated Timeline

| Phase | Tasks | Estimated Days |
|-------|-------|----------------|
| Phase 1: Simple React Conversion | 18 components | 3-4 days |
| Phase 2: Zustand Conversion | 6 stores + consumer migration | 3-4 days |
| Phase 3: Modularization & Rewrites | 20 components + new chat panel | 6-8 days |
| Phase 4: Bug Fix & Polish | Testing + fixes | 1-2 days |
| **Total** | | **~15 days (3 weeks)** |

---

*Generated from 00-MASTER-SPEC.md*
*Last Updated: December 2024*
