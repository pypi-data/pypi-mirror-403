# Stores Dependency Graph

This document provides a comprehensive analysis of all Zustand stores in the Sage Agent application and their relationships with components.

## Directory Structure

```
src/stores/
├── index.ts                      # Barrel file - central exports
├── appStore.ts                   # Core application state
├── appStateStore.ts              # Zustand backing for AppStateService
├── chatUIStore.ts                # Chat UI visibility states
├── chatboxStore.ts               # Main chatbox orchestration
├── chatHistoryStore.ts           # Thread and history management
├── contextStore.ts               # Mention context items
├── databaseStore.ts              # Database configuration
├── databaseMetadataCacheStore.ts # Database metadata caching
├── deploymentStore.ts            # Deployment state
├── diffStore.ts                  # Pending code diffs
├── llmStateStore.ts              # LLM processing state display
├── mentionDropdownStore.ts       # Mention dropdown state
├── notebookEventsStore.ts        # Notebook change events
├── planStateStore.ts             # Plan processing state display
├── richTextInputStore.ts         # Rich text input state
├── settingsStore.ts              # User preferences
├── snippetStore.ts               # Saved code snippets
├── toolbarStore.ts               # Toolbar UI state
├── uiBridge.ts                   # UI-to-service communication
├── chat/                         # Chat store module
│   ├── index.ts
│   ├── chatStore.ts
│   └── types.ts
├── chatInput/                    # Chat input store module
│   └── chatInputStore.ts
└── chatMessages/                 # Chat messages store module
    ├── index.ts
    ├── store.ts
    ├── types.ts
    ├── selectors.ts
    └── subscribers.ts
```

---

## Store Dependency Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐          ┌────────────────┐                               │
│   │  appStore   │─────────►│ appStateStore  │◄─────────────────────────┐    │
│   └─────────────┘          └────────────────┘                          │    │
│                                    │                                    │    │
│                                    ▼                                    │    │
│   ┌─────────────────────────────────────────────────────────────────┐  │    │
│   │                        CHAT ECOSYSTEM                            │  │    │
│   │  ┌─────────────┐      ┌──────────────────┐                      │  │    │
│   │  │  chatStore  │◄─────│ chatMessagesStore│                      │  │    │
│   │  └──────┬──────┘      └────────┬─────────┘                      │  │    │
│   │         │                      │                                 │  │    │
│   │         ▼                      ▼                                 │  │    │
│   │  ┌─────────────┐      ┌──────────────────┐                      │  │    │
│   │  │chatboxStore │◄─────│chatHistoryStore  │                      │  │    │
│   │  └──────┬──────┘      └──────────────────┘                      │  │    │
│   │         │                      │                                 │  │    │
│   │         ▼                      ▼                                 │  │    │
│   │  ┌─────────────┐      ┌──────────────────┐                      │  │    │
│   │  │ chatUIStore │      │   toolbarStore   │                      │  │    │
│   │  └─────────────┘      └──────────────────┘                      │  │    │
│   │                                                                  │  │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │  │    │
│   │  │                    INPUT ECOSYSTEM                         │  │  │    │
│   │  │  ┌───────────────────┐      ┌────────────────┐            │  │  │    │
│   │  │  │richTextInputStore │◄─────│ chatInputStore │            │  │  │    │
│   │  │  └─────────┬─────────┘      └────────────────┘            │  │  │    │
│   │  │            │                                               │  │  │    │
│   │  │            ▼                                               │  │  │    │
│   │  │  ┌───────────────────┐      ┌────────────────┐            │  │  │    │
│   │  │  │mentionDropdownStore│◄────│  contextStore  │            │  │  │    │
│   │  │  └───────────────────┘      └────────────────┘            │  │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │  │    │
│   │                                                                  │  │    │
│   │  ┌───────────────────────────────────────────────────────────┐  │  │    │
│   │  │                   STATE DISPLAYS                           │  │  │    │
│   │  │  ┌───────────────┐          ┌────────────────┐            │  │  │    │
│   │  │  │ llmStateStore │          │ planStateStore │            │  │  │    │
│   │  │  └───────────────┘          └────────────────┘            │  │  │    │
│   │  └───────────────────────────────────────────────────────────┘  │  │    │
│   └─────────────────────────────────────────────────────────────────┘  │    │
│                                                                         │    │
│   ┌─────────────────────────────────────────────────────────────────┐  │    │
│   │                      WORKFLOW STORES                             │  │    │
│   │  ┌───────────┐  ┌──────────────────────┐                        │  │    │
│   │  │ diffStore │  │ notebookEventsStore  │                        │◄─┘    │
│   │  └───────────┘  └──────────────────────┘                        │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                     PERSISTENCE STORES                           │       │
│   │  ┌───────────────┐          ┌──────────────┐                    │       │
│   │  │ settingsStore │          │ snippetStore │                    │       │
│   │  │ (localStorage)│          │  (StateDB)   │                    │       │
│   │  └───────────────┘          └──────────────┘                    │       │
│   └─────────────────────────────────────────────────────────────────┘       │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────┐       │
│   │                      DATABASE STORES                             │       │
│   │  ┌───────────────┐                                              │       │
│   │  │ databaseStore │────────────────┐                             │       │
│   │  └───────────────┘                │                             │       │
│   │          │                        ▼                             │       │
│   │          │            ┌─────────────────────────┐               │       │
│   │          │            │databaseMetadataCacheStore│              │       │
│   │          │            └─────────────────────────┘               │       │
│   │          │                                                      │       │
│   │  ┌───────────────┐                                              │       │
│   │  │deploymentStore│                                              │       │
│   │  └───────────────┘                                              │       │
│   └─────────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Store Descriptions

### Core Application Stores

#### `appStore.ts`
**Purpose:** Core application state - initialization, current notebook, mode flags

| State | Type | Description |
|-------|------|-------------|
| `isInitialized` | boolean | App initialization status |
| `isLauncherActive` | boolean | Launcher visibility |
| `currentNotebookId` | string \| null | Active notebook ID |
| `currentNotebook` | NotebookPanel \| null | Active notebook reference |
| `currentWorkingDirectory` | string \| null | Current working directory |
| `isDemoMode` | boolean | Demo mode flag |
| `isTakeoverMode` | boolean | Takeover mode flag |
| `autoRun` | boolean | Auto-run setting |
| `maxToolCallLimit` | number \| null | Tool call limit |
| `userProfile` | any \| null | User profile data |

#### `appStateStore.ts`
**Purpose:** Zustand backing store for AppStateService - centralized application state with service references

Contains references to all core services, managers, UI containers, and settings.

---

### Chat Ecosystem

#### `chat/chatStore.ts`
**Purpose:** Chat messages, threads, streaming state

| State | Type | Description |
|-------|------|-------------|
| `messages` | IAssistantMessage[] | Chat messages |
| `threads` | IChatThread[] | Chat threads |
| `currentThreadId` | string \| null | Active thread |
| `streaming` | IStreamingState | Streaming state |
| `isProcessing` | boolean | Processing flag |
| `mode` | ChatMode | Current chat mode |
| `contexts` | IMentionContext[] | Active contexts |

#### `chatMessagesStore` (chatMessages/store.ts)
**Purpose:** Chat messages UI state - messages, streaming, contexts, scroll

| State | Type | Description |
|-------|------|-------------|
| `messages` | ChatUIMessage[] | UI-formatted messages |
| `llmHistory` | IChatMessage[] | Raw LLM format messages |
| `streaming` | IStreamingState | Streaming state |
| `isThinking` | boolean | Thinking indicator |
| `waitingReply` | IWaitingReplyState | User reply state |
| `mentionContexts` | Map | Active mention contexts |
| `scrollState` | IScrollState | Scroll position |

**Message Types:** user, assistant, system, error, tool_call, tool_result, diff_approval, loading

#### `chatboxStore.ts`
**Purpose:** Main chatbox orchestration state - initialization, notebook tracking, service references

| State | Type | Description |
|-------|------|-------------|
| `isReady` | boolean | Ready state |
| `isFullyInitialized` | boolean | Full initialization |
| `currentNotebookId` | string \| null | Current notebook |
| `isProcessingMessage` | boolean | Processing flag |
| `isCancelled` | boolean | Cancellation flag |
| `services` | IChatboxServices | Service references |

#### `chatHistoryStore.ts`
**Purpose:** Thread and history management

| State | Type | Description |
|-------|------|-------------|
| `threads` | IThreadSummary[] | Thread list |
| `currentThreadId` | string \| null | Active thread |
| `currentThreadName` | string | Thread name |
| `userMessageHistory` | string[] | Message history |
| `hasUnsavedChanges` | boolean | Unsaved flag |

**Dependencies:** Imports `chatMessagesStore`, `chatUIStore` for cross-store updates

#### `chatUIStore.ts`
**Purpose:** Chat UI visibility states

| State | Type | Description |
|-------|------|-------------|
| `showNewChatDisplay` | boolean | New chat visibility |
| `showHistoryWidget` | boolean | History widget visibility |
| `chatHistoryLoading` | boolean | Loading state |
| `loadingOverlay` | object | Loading overlay state |
| `scroll` | object | Scroll state |
| `isMoreOptionsOpen` | boolean | Toolbar menu state |

---

### Input Ecosystem

#### `chatInputStore.ts`
**Purpose:** Chat input state - input value, tokens, mention dropdown

| State | Type | Description |
|-------|------|-------------|
| `inputValue` | string | Current input |
| `tokenCount` | number | Token count |
| `mentionDropdownVisible` | boolean | Dropdown visibility |
| `currentMentionStart` | number | Mention start position |
| `isProcessingMessage` | boolean | Processing flag |
| `pendingMessageOp` | object \| null | Pending operation |

#### `richTextInputStore.ts`
**Purpose:** Rich text input state - content, focus, active contexts

| State | Type | Description |
|-------|------|-------------|
| `plainText` | string | Plain text content |
| `isEmpty` | boolean | Empty state |
| `isFocused` | boolean | Focus state |
| `activeContexts` | Map | Active mention contexts |
| `pendingTextInsert` | object \| null | Pending insert |
| `pendingClear` | boolean | Pending clear flag |

#### `mentionDropdownStore.ts`
**Purpose:** Mention dropdown state - visibility, navigation, search

| State | Type | Description |
|-------|------|-------------|
| `isVisible` | boolean | Visibility |
| `currentView` | 'categories' \| 'items' | Current view |
| `selectedCategory` | string \| null | Selected category |
| `selectedIndex` | number | Selected index |
| `searchText` | string | Search query |
| `mentionStart` | number | Mention start position |

#### `contextStore.ts`
**Purpose:** Manage mention context items for chat

| State | Type | Description |
|-------|------|-------------|
| `contextItems` | Map<string, IMentionContext> | Context items |

---

### State Display Stores

#### `llmStateStore.ts`
**Purpose:** LLM State Display - processing state shown above chat input

| State | Type | Description |
|-------|------|-------------|
| `isVisible` | boolean | Visibility |
| `state` | LLMDisplayState | Current state (IDLE, GENERATING, USING_TOOL, DIFF, RUN_KERNEL) |
| `text` | string | Display text |
| `toolName` | string \| undefined | Active tool name |
| `diffs` | IPendingDiff[] \| undefined | Pending diffs |
| `waitingForUser` | boolean | Waiting flag |

#### `planStateStore.ts`
**Purpose:** Plan State Display - plan processing state shown above chat input

| State | Type | Description |
|-------|------|-------------|
| `isVisible` | boolean | Visibility |
| `currentStep` | string \| undefined | Current step |
| `nextStep` | string \| undefined | Next step |
| `source` | string \| undefined | Plan source |
| `isLoading` | boolean | Loading state |

---

### Workflow Stores

#### `diffStore.ts`
**Purpose:** Manage pending code diffs and approval workflow

| State | Type | Description |
|-------|------|-------------|
| `pendingDiffs` | Map<string, IPendingDiff> | Pending diffs |
| `notebookId` | string \| null | Current notebook |

#### `toolbarStore.ts`
**Purpose:** Toolbar UI state

| State | Type | Description |
|-------|------|-------------|
| `isBannerOpen` | boolean | Banner state |
| `isMoreOptionsOpen` | boolean | More options state |
| `canUndo` | boolean | Undo availability |
| `undoDescription` | string | Undo description |

#### `notebookEventsStore.ts`
**Purpose:** Notebook change/rename events

| State | Type | Description |
|-------|------|-------------|
| `lastNotebookChange` | INotebookChangeEvent \| null | Last change event |
| `lastNotebookRename` | INotebookRenameEvent \| null | Last rename event |

---

### Persistence Stores

#### `settingsStore.ts`
**Purpose:** User preferences and API configuration

**Persistence:** localStorage via devtools persist middleware

| State | Type | Description |
|-------|------|-------------|
| `theme` | string | UI theme |
| `tokenMode` | boolean | Token mode setting |
| `tabAutocompleteEnabled` | boolean | Autocomplete setting |
| `claudeApiKey` | string | API key |
| `claudeModelId` | string | Model ID |
| `claudeModelUrl` | string | Model URL |
| `databaseUrl` | string | Database URL |

#### `snippetStore.ts`
**Purpose:** Manage saved code snippets

**Persistence:** StateDB

| State | Type | Description |
|-------|------|-------------|
| `snippets` | ISnippet[] | Saved snippets |
| `insertedSnippetIds` | string[] | Inserted snippet IDs |
| `isLoaded` | boolean | Load state |

---

### Database Stores

#### `databaseStore.ts`
**Purpose:** Manage database configuration state

**Persistence:** StateDB with encryption

**Supported Types:** MySQL, PostgreSQL, Snowflake, Databricks

| State | Type | Description |
|-------|------|-------------|
| `configurations` | IDatabaseConfig[] | Database configs |
| `activeConfigId` | string \| null | Active config ID |
| `activeConfig` | IDatabaseConfig \| null | Active config |
| `isInitialized` | boolean | Initialization state |

#### `databaseMetadataCacheStore.ts`
**Purpose:** Manage database metadata caching state

**Persistence:** StateDB with 5-minute TTL

| State | Type | Description |
|-------|------|-------------|
| `cache` | IDatabaseMetadata \| null | Cached metadata |
| `isLoading` | boolean | Loading state |
| `lastError` | string \| null | Last error |

#### `deploymentStore.ts`
**Purpose:** Manage deployment state for notebooks

| State | Type | Description |
|-------|------|-------------|
| `deployments` | Map<string, IDeploymentData> | Deployment data |
| `lastChange` | IDeploymentChange \| null | Last change event |

---

## Component-to-Store Mapping

| Component | Stores Used |
|-----------|-------------|
| **ChatBoxWidget** | chatboxStore, chatUIStore, chatInputStore, llmStateStore, planStateStore |
| **ChatInputContainer** | chatInputStore, richTextInputStore, mentionDropdownStore |
| **RichTextInput** | richTextInputStore, mentionDropdownStore, contextStore |
| **MentionDropdown** | mentionDropdownStore |
| **ChatMessages** | chatMessagesStore, chatUIStore |
| **ChatToolbar** | toolbarStore, chatHistoryStore, chatStore |
| **LLMStateDisplay** | llmStateStore |
| **PlanStateDisplay** | planStateStore |
| **DiffApproval** | diffStore |
| **HistoryContainer** | chatHistoryStore, chatUIStore |
| **ChatBoxHeader** | chatUIStore, toolbarStore |
| **UpdateBanner** | chatUIStore |
| **NewChatDisplay** | chatUIStore |
| **ChatBoxContent** | chatMessagesStore, chatHistoryStore |
| **SendButton** | chatStore |
| **MoreOptionsPopover** | chatUIStore |
| **NotebookChatContainer** | chatboxStore |

---

## Store Inter-Dependencies

### Primary Dependencies

```
chatHistoryStore ──────► chatMessagesStore
       │
       └──────────────► chatUIStore

chatboxStore ──────────► chatHistoryStore
       │
       ├──────────────► chatMessagesStore
       │
       ├──────────────► chatUIStore
       │
       ├──────────────► llmStateStore
       │
       └──────────────► planStateStore

richTextInputStore ────► contextStore
       │
       └──────────────► mentionDropdownStore

databaseMetadataCacheStore ──► databaseStore
```

### Cross-Store Update Flows

1. **Thread Selection Flow:**
   ```
   chatHistoryStore.selectThread()
       → chatMessagesStore.loadFromThread()
       → chatUIStore.setShowHistoryWidget(false)
   ```

2. **New Chat Flow:**
   ```
   chatboxStore.createNewChat()
       → chatMessagesStore.clearMessages()
       → chatHistoryStore.clearForNotebook()
       → chatUIStore.setShowNewChatDisplay(true)
   ```

3. **Message Send Flow:**
   ```
   chatInputStore (input)
       → richTextInputStore (rich text)
       → contextStore (contexts)
       → chatMessagesStore (add message)
       → llmStateStore (show processing)
   ```

---

## State Persistence Strategy

| Store | Persistence Method | Notes |
|-------|-------------------|-------|
| settingsStore | localStorage | Via Zustand persist middleware |
| snippetStore | StateDB | Encrypted |
| databaseStore | StateDB | Encrypted credentials |
| databaseMetadataCacheStore | StateDB | 5-minute TTL |
| chatHistoryStore | ChatHistoryManager service | Thread-based |
| All others | In-memory | Session-scoped |

---

## Architectural Patterns

1. **Module-based Organization:** Chat, chatInput, and chatMessages use nested module structures with separate type files
2. **Selector Pattern:** Optimized re-renders via granular selectors exported from each store
3. **Subscription Support:** Non-React code can subscribe to all stores via `subscribeTo*` functions
4. **Action Bundling:** Related updates grouped in single actions to prevent intermediate states
5. **Non-React API:** All stores export `get*State()` functions for use in services
6. **Compatibility Wrappers:** Old service APIs wrapped for gradual migration
