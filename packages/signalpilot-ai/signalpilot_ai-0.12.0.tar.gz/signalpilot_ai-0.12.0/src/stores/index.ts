// Barrel file for all Zustand stores

// ═══════════════════════════════════════════════════════════════
// APP STORE - Core application state
// ═══════════════════════════════════════════════════════════════
export {
  useAppStore,
  selectIsDemoMode,
  subscribeToAutoRun,
  subscribeToLauncherActive
} from './appStore';

// ═══════════════════════════════════════════════════════════════
// CHAT MODE STORE - Single source of truth for chat context/mode
// ═══════════════════════════════════════════════════════════════
export {
  useChatModeStore,
  selectContext,
  selectNotebookMode,
  selectCurrentNotebookId as selectChatModeNotebookId,
  subscribeToContextChange,
  subscribeToEffectiveModeChange,
  type ChatContext,
  type ChatMode as ChatModeType
} from './chatModeStore';

// ═══════════════════════════════════════════════════════════════
// CHAT STORE - Chat messages, threads, streaming state
// ═══════════════════════════════════════════════════════════════
export {
  useChatStore,
  selectMessages,
  selectStreaming,
  selectIsStreaming,
  selectStreamingText,
  selectIsProcessing,
  selectMode,
  selectError,
  selectCurrentThreadId,
  selectThreads,
  selectShowNewChatDisplay,
  selectMessageCount,
  selectContexts,
  subscribeToMessages,
  subscribeToStreaming,
  subscribeToProcessing,
  subscribeToMode,
  subscribeToThreads,
  subscribeToCurrentThread,
  type IChatThread,
  type IStreamingState,
  type ChatMode
} from './chat';

export {
  uiBridge,
  useUIBridgeHandlers,
  type ISendMessageOptions,
  type IUIBridgeHandlers,
  type IPartialUIBridgeHandlers
} from './uiBridge';

// ═══════════════════════════════════════════════════════════════
// SETTINGS STORE - User preferences
// ═══════════════════════════════════════════════════════════════
export {
  useSettingsStore,
  selectTheme,
  selectTokenMode,
  selectTabAutocomplete,
  selectClaudeApiKey,
  selectClaudeModelId,
  selectClaudeModelUrl,
  selectDatabaseUrl
} from './settingsStore';

// ═══════════════════════════════════════════════════════════════
// NOTEBOOK EVENTS STORE - Notebook change/rename events
// ═══════════════════════════════════════════════════════════════
export {
  useNotebookEventsStore,
  useNotebookChange,
  useNotebookRename,
  subscribeToNotebookChange,
  subscribeToNotebookRename,
  type INotebookChangeEvent,
  type INotebookRenameEvent
} from './notebookEventsStore';

// ═══════════════════════════════════════════════════════════════
// DIFF STORE - Code diff approval workflow
// ═══════════════════════════════════════════════════════════════
export {
  useDiffStore,
  useCellDiffChange,
  useApprovalStatusChange,
  useAllDiffsResolved,
  subscribeToDiffChanges,
  subscribeToApprovalStatus,
  selectPendingDiffs,
  selectNotebookId,
  selectDiffCount,
  type IDiffStateChange,
  type IApprovalStatus
} from './diffStore';

// ═══════════════════════════════════════════════════════════════
// SNIPPET STORE - Saved code snippets
// ═══════════════════════════════════════════════════════════════
export {
  useSnippetStore,
  selectSnippets,
  selectInsertedSnippetIds,
  selectIsLoaded,
  selectSnippetById,
  type ISnippet
} from './snippetStore';

// ═══════════════════════════════════════════════════════════════
// CONTEXT STORE - Chat context items
// ═══════════════════════════════════════════════════════════════
export {
  useContextStore,
  useContextChange,
  useContextItemsByType,
  subscribeToContextChanges,
  selectContextItems,
  selectContextCount,
  selectContextItemsArray
} from './contextStore';

// ═══════════════════════════════════════════════════════════════
// TOOLBAR STORE - Toolbar UI state
// ═══════════════════════════════════════════════════════════════
export {
  useToolbarStore,
  selectIsBannerOpen,
  selectIsMoreOptionsOpen,
  selectMoreOptionsAnchorRect,
  selectCanUndo,
  selectUndoDescription,
  subscribeToBannerOpen,
  subscribeToUndoState
} from './toolbarStore';

// ═══════════════════════════════════════════════════════════════
// LLM STATE STORE - LLM processing state display
// ═══════════════════════════════════════════════════════════════
export {
  useLLMStateStore,
  LLMDisplayState,
  selectLLMState,
  selectIsVisible as selectLLMIsVisible,
  selectDisplayState,
  selectIsDiffState,
  selectIsUsingToolState,
  subscribeToLLMVisibility,
  subscribeToLLMDisplayState,
  subscribeToLLMState,
  type ILLMState
} from './llmStateStore';

// ═══════════════════════════════════════════════════════════════
// PLAN STATE STORE - Plan processing state display
// ═══════════════════════════════════════════════════════════════
export {
  usePlanStateStore,
  selectPlanState,
  selectPlanIsVisible,
  selectPlanCurrentStep,
  selectPlanNextStep,
  selectPlanSource,
  selectPlanIsLoading,
  subscribeToPlanVisibility,
  subscribeToPlanState,
  subscribeToPlanLoading,
  type IPlanState
} from './planStateStore';

// ═══════════════════════════════════════════════════════════════
// CHATBOX STORE - Main chatbox orchestration state
// ═══════════════════════════════════════════════════════════════
export {
  useChatboxStore,
  selectIsReady,
  selectIsFullyInitialized,
  selectIsInitializing,
  selectCurrentNotebookId,
  selectIsProcessingMessage,
  selectHasShownWelcomeMessage,
  selectServices,
  getChatboxState,
  subscribeToChatbox,
  subscribeToNotebookId,
  subscribeToProcessing as subscribeToProcessingMessage,
  subscribeToReady,
  type IChatboxState,
  type IChatboxActions,
  type IChatboxServices
} from './chatboxStore';

// ═══════════════════════════════════════════════════════════════
// CHAT UI STORE - Chat UI visibility states
// ═══════════════════════════════════════════════════════════════
export {
  useChatUIStore,
  selectShowNewChatDisplay as selectChatUIShowNewChatDisplay,
  selectShowHistoryWidget,
  selectChatHistoryLoading,
  selectLoadingOverlay,
  selectShowUpdateBanner,
  getChatUIState,
  subscribeToNewChatDisplay,
  subscribeToHistoryWidget,
  subscribeToLoading,
  type IChatUIState,
  type IChatUIActions,
  type ILoadingOverlayState
} from './chatUIStore';

// ═══════════════════════════════════════════════════════════════
// CHAT HISTORY STORE - Thread and history management
// ═══════════════════════════════════════════════════════════════
export {
  useChatHistoryStore,
  selectThreads as selectHistoryThreads,
  selectCurrentThreadId as selectHistoryCurrentThreadId,
  selectCurrentThreadName,
  selectIsLoadingThreads,
  selectIsLoadingHistory,
  selectHasUnsavedChanges,
  getChatHistoryState,
  subscribeToThreadList,
  subscribeToCurrentThread as subscribeToCurrentHistoryThread,
  subscribeToHistoryLoading,
  type IChatHistoryState,
  type IChatHistoryActions,
  type IThreadSummary
} from './chatHistoryStore';

// ═══════════════════════════════════════════════════════════════
// RICH TEXT INPUT STORE - Rich text input state
// ═══════════════════════════════════════════════════════════════
export {
  useRichTextInputStore,
  selectPlainText,
  selectIsEmpty,
  selectIsFocused,
  selectFocusRequested as selectRichTextFocusRequested,
  selectActiveContexts,
  selectPendingTextInsert,
  selectPendingClear,
  selectPendingSetText,
  getRichTextInputState,
  subscribeToPlainText,
  subscribeToFocusRequest,
  type IRichTextInputState,
  type IRichTextInputActions,
  type ITextInsertRequest
} from './richTextInputStore';

// ═══════════════════════════════════════════════════════════════
// CHAT INPUT STORE - Chat input state (extended)
// ═══════════════════════════════════════════════════════════════
export {
  useChatInputStore,
  selectInputValue,
  selectPlaceholder as selectInputPlaceholder,
  selectTokenCount,
  selectIsCompacting,
  selectShowNewPromptCta,
  selectFocusRequested,
  selectPendingMessageOp,
  selectContextRowKey,
  getChatInputState,
  subscribeToInputValue,
  subscribeToFocusRequested,
  subscribeToPendingMessageOp,
  type ChatInputState,
  type ChatInputActions,
  type ChatInputStore,
  type IPendingMessageOp
} from './chatInput/chatInputStore';

// ═══════════════════════════════════════════════════════════════
// CHAT MESSAGES STORE - Chat messages UI state (extended)
// ═══════════════════════════════════════════════════════════════
export {
  useChatMessagesStore,
  selectMessages as selectChatMessages,
  selectLlmHistory,
  selectStreaming as selectChatStreaming,
  selectIsStreaming as selectChatIsStreaming,
  selectStreamingText as selectChatStreamingText,
  selectIsThinking,
  selectSpecialDisplay,
  selectLastMessageType,
  selectCurrentThreadId as selectChatCurrentThreadId,
  selectMentionContexts as selectChatMentionContexts,
  selectScrollState,
  selectScrollToBottomCounter,
  getChatMessagesState,
  subscribeToChatMessages,
  subscribeToMessages as subscribeToChatMessagesArray,
  subscribeToLlmHistory,
  subscribeToScrollToBottom,
  subscribeToStreaming as subscribeToChatStreaming,
  type ChatMessageType,
  type IChatUIMessage,
  type IUserUIMessage,
  type IAssistantUIMessage,
  type ISystemUIMessage,
  type IErrorUIMessage,
  type IToolCallUIMessage,
  type IToolResultUIMessage,
  type IDiffApprovalUIMessage,
  type ILoadingUIMessage,
  type ChatUIMessage,
  type IStreamingState as IChatStreamingState,
  type SpecialDisplayState,
  type IScrollState as IChatScrollState,
  type IStreamingToolCall,
  type IDiffCellUI
} from './chatMessages';

// ═══════════════════════════════════════════════════════════════
// WAITING REPLY STORE - Waiting user reply box state
// ═══════════════════════════════════════════════════════════════
export {
  useWaitingReplyStore,
  selectIsVisible as selectWaitingReplyIsVisible,
  selectRecommendedPrompts,
  selectContinueButtonShown,
  getWaitingReplyState,
  subscribeToWaitingReplyVisibility,
  type IWaitingReplyState as IWaitingReplyStoreState,
  type IWaitingReplyActions,
  type IWaitingReplyStore
} from './waitingReplyStore';

// ═══════════════════════════════════════════════════════════════
// ACTION HISTORY STORE - Undo/redo action history
// ═══════════════════════════════════════════════════════════════
export {
  useActionHistoryStore,
  ActionType,
  selectCanUndo as selectActionCanUndo,
  selectLastActionDescription,
  selectHistory as selectActionHistory,
  getActionHistoryState,
  subscribeToCanUndo,
  subscribeToLastActionDescription,
  type IActionHistoryEntry,
  type IRemovedCellData,
  type IActionHistoryState,
  type IActionHistoryActions,
  type IActionHistoryStore
} from './actionHistoryStore';

// ═══════════════════════════════════════════════════════════════
// DEMO OVERLAY STORE - Demo mode overlay state
// ═══════════════════════════════════════════════════════════════
export {
  useDemoOverlayStore,
  selectIsOverlayActive,
  selectShowSendSpinner,
  activateDemoOverlays,
  deactivateDemoOverlays
} from './demoOverlayStore';

// ═══════════════════════════════════════════════════════════════
// DEMO CONTROL STORE - Demo control panel state
// ═══════════════════════════════════════════════════════════════
export {
  useDemoControlStore,
  selectIsVisible as selectDemoControlIsVisible,
  selectIsDemoFinished,
  selectShowSkipButton,
  showDemoControls,
  hideDemoControls,
  markDemoFinished,
  getDemoFinished
} from './demoControlStore';

// ═══════════════════════════════════════════════════════════════
// LOADING STATE STORE - App initialization loading states
// ═══════════════════════════════════════════════════════════════
export {
  useLoadingStateStore,
  selectPhase,
  selectFeatures,
  selectDetails,
  selectMetrics,
  selectIsShellReady,
  selectIsCoreReady,
  selectIsFullyReady,
  selectIsChatHistoryLoading as selectLoadingStateChatHistoryLoading,
  selectIsDatabaseContextLoading,
  selectIsMessageListLoading,
  selectChatHistoryLoadDetail,
  selectDatabaseContextLoadDetail,
  getLoadingState,
  subscribeToPhase,
  subscribeToFeatureLoading,
  waitForFeature,
  waitForCoreReady,
  type InitPhase,
  type IFeatureLoadingStates,
  type ILoadingDetail,
  type ILoadingState,
  type ILoadingStateActions
} from './loadingStateStore';
