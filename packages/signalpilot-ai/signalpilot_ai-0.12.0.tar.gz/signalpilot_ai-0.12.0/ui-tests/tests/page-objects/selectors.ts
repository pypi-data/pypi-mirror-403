/**
 * Centralized selectors for UI tests
 * All component selectors should be defined here for easy maintenance
 *
 * Updated to match the refactored React-based ChatBox architecture
 */

export const Selectors = {
  // JupyterLab Core
  jupyterlab: {
    mainDockPanel: '#jp-main-dock-panel',
    launcherCard:
      '.jp-LauncherCard[title="Python 3 (ipykernel)"][role="button"]',
    commandPalette: '#modal-command-palette',
    commandPaletteInput: '.lm-CommandPalette-input',
    commandPaletteContent: '.lm-CommandPalette-content'
  },

  // Chat Interface (React-based ChatBox)
  chat: {
    // Container - the Lumino widget wrapper
    container: '#sage-ai-chat-container',
    containerClass: '.sage-ai-chat-container',
    containerInner: '.sage-ai-chat-container-inner',

    // Main chatbox component
    chatbox: '.sage-ai-chatbox',
    chatboxLoading: '.sage-ai-chatbox-loading',

    // Header
    header: '.sage-ai-chatbox-header',

    // Content area
    content: '.sage-ai-chatbox-content',
    messagesContainer: '.sage-ai-messages-container',

    // Input section (ChatInputContainer)
    inputContainer: '.sage-ai-input-container',
    inputRow: '.sage-ai-input-row',
    inputWrapper: '.sage-ai-chatbox-wrapper',
    contextRowContainer: '.sage-ai-context-row-container',

    // Rich text input
    richTextInputContainer: '.sage-ai-rich-text-input-container',
    richTextInput: '.sage-ai-rich-chat-input',
    richTextInputWrapper: '.sage-ai-rich-chat-input-wrapper',

    // Buttons
    sendButton: '.sage-ai-send-button',
    cancelButton: '.sage-ai-cancel-button',
    addContextButton: 'button:has-text("Add Context")',

    // Mode selector
    modeSelectorContainer: '.sage-ai-mode-selector-container',

    // Token progress
    tokenProgressContainer: '.sage-ai-token-progress-container-wrapper',

    // Mention dropdown
    mentionDropdownContainer: '.sage-ai-mention-dropdown-container',

    // Legacy selectors (for backwards compatibility)
    widget: '.sage-ai-chatbox',
    widgetWithId: '#sage-ai-chat-container .sage-ai-chatbox',
    input:
      '.sage-ai-rich-chat-input, .sage-ai-input-row input, .sage-ai-input-row [contenteditable="true"]',
    toolbar: '.sage-ai-chatbox-header'
  },

  // Auth/Setup
  auth: {
    welcomeDismissButton:
      'button.sage-ai-jwt-auth-dismiss-btn.btn.btn-outline-secondary',
    jwtTokenInput:
      'input[type="password"].sage-ai-dialog-input[placeholder*="JWT token"]',
    dialogInput: '.sage-ai-dialog-input[placeholder*="JWT token"]',
    submitButton: 'button.sage-ai-dialog-submit-button',
    okButton: 'button.sage-ai-dialog-submit-button:has-text("OK")',
    // Support both local (signalpilot-ai:) and non-local (signalpilot-ai-internal:) command IDs
    testModeCommand: '[data-command$=":activate-test-mode"]'
  },

  // LLM State Display
  llmState: {
    // Widget wrapper
    widget: '.sage-ai-llm-state-widget',

    // Main display container
    display: '.sage-ai-llm-state-display',

    // State-specific classes
    generating: '.sage-ai-llm-state-display.sage-ai-generating',
    diffState: '.sage-ai-llm-state-display.sage-ai-diff-state',

    // Waiting states
    waitingForUser: '.sage-ai-waiting-for-user',
    waitingReplyContainer: '.sage-ai-waiting-reply-container',
    waitingReplyText: '.sage-ai-waiting-reply-text'
  },

  // Messages
  messages: {
    // Base message class
    message: '.sage-ai-message',

    // Message types
    userMessage: '.sage-ai-message.sage-ai-user-message',
    aiMessage: '.sage-ai-message.sage-ai-ai-message',
    systemMessage: '.sage-ai-message.sage-ai-system-message',
    errorMessage: '.sage-ai-message.sage-ai-error-message',
    streamingMessage: '.sage-ai-message.sage-ai-streaming-message',
    thinkingMessage: '.sage-ai-message.sage-ai-thinking-message',
    loadingMessage: '.sage-ai-message.sage-ai-loading',

    // Message parts
    messageHeader: '.sage-ai-message-header',
    messageContent: '.sage-ai-message-content',
    markdownContent: '.sage-ai-markdown-content'
  },

  // Diff Components
  diff: {
    // Diff List
    list: '.sage-ai-diff-list',
    item: '.sage-ai-diff-item',
    itemWithHover: '.sage-ai-diff-item.sage-ai-diff-item-hover-actions',
    summaryBar: '.sage-ai-diff-summary-bar',

    // Diff cell items
    cellItem: '.sage-ai-diff-cell-item',
    cellHeader: '.sage-ai-diff-cell-header',
    cellIdLabel: '.sage-ai-diff-cell-id-label',
    cellContent: '.sage-ai-diff-content',

    // Diff Item Actions (hover buttons)
    actions: '.sage-ai-diff-actions',
    rejectButton: '.sage-ai-diff-btn.sage-ai-diff-reject',
    approveButton: '.sage-ai-diff-btn.sage-ai-diff-approve',
    reapplyButton: '.sage-ai-diff-btn.sage-ai-diff-reapply',

    // Bulk action buttons (in summary bar)
    rejectAll: '.sage-ai-diff-btn.sage-ai-diff-reject-all',
    approveAll: '.sage-ai-diff-btn.sage-ai-diff-approve-all',

    // Run button (for DiffItem hover actions)
    runButton: '.sage-ai-diff-btn.sage-ai-diff-run',

    // Action buttons (aliases for hover action buttons in DiffItem)
    actionReject: '.sage-ai-diff-btn.sage-ai-diff-reject',
    actionRun: '.sage-ai-diff-btn.sage-ai-diff-run',
    actionApprove: '.sage-ai-diff-btn.sage-ai-diff-approve',

    // Navigation Buttons (DiffNavigationContent)
    navigationSection: '.sage-ai-diff-navigation-button-section',
    navigationRejectAll: '.sage-ai-diff-navigation-reject-button',
    navigationApproveAll: '.sage-ai-diff-navigation-approve-button',
    navigationRunAll: '.sage-ai-diff-navigation-accept-run-button',

    // Icons (inside navigation buttons)
    rejectIcon: 'svg',
    approveIcon: 'svg',

    // Approval dialog
    approvalDialog: '.sage-ai-diff-approval-dialog-embedded',
    approvalMessage: '.sage-ai-diff-approval-message',
    historicalDiff: '.sage-ai-diff-approval-historical',

    // Icons and indicators
    spinner: '.sage-ai-diff-spinner',
    gradientOverlay: '.sage-ai-diff-gradient-overlay'
  },

  // CodeMirror Diff Components
  codeMirror: {
    changedLine: '.cm-changedLine',
    chunkButtons: '.cm-chunkButtons',
    rejectButton: 'button[name="reject"]',
    acceptButton: 'button[name="accept"]'
  },

  // Loading/Generating Indicators
  indicators: {
    // Loading overlay
    loadingOverlay: '.sage-ai-loading-overlay',
    loadingContent: '.sage-ai-loading-content',
    loadingText: '.sage-ai-loading-text',

    // Blob loader (initializing)
    blobLoader: '.sage-ai-blob-loader',

    // Generating state
    generating: '.sage-ai-generating',

    // Loading message
    loading: '.sage-ai-loading',

    // Spinners
    spinner: '.sage-ai-diff-spinner',
    btnSpinner: '.sage-ai-btn-spinner',
    bannerSpinner: '.sage-ai-banner-spinner',
    updateBannerSpinner: '.sage-ai-update-banner-spinner',

    // Button loading state
    btnLoading: '.sage-ai-btn-loading',

    // Chat loading
    chatLoading: '.sage-ai-chat-loading',
    chatInputLoading: '.sage-ai-chat-input-loading'
  },

  // Toolbar
  toolbar: {
    chatToolbar: '.sage-ai-chatbox-header',
    threadBanner: '.sage-ai-thread-banner',
    moreOptionsPopover: '.sage-ai-more-options-popover'
  },

  // New Chat / Welcome Display
  newChat: {
    display: '.sage-ai-new-chat-display',
    promptCta: '.sage-ai-new-prompt-cta',
    promptCtaButton: '.sage-ai-new-prompt-cta-button'
  }
} as const;

/**
 * Timeout constants for different operations
 */
export const Timeouts = {
  short: 500,
  medium: 1000,
  long: 2000,
  selector: 5000,
  navigation: 10000,
  modal: 30000,
  response: 60000,
  test: 30000,
  longTest: 600000
} as const;
