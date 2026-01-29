/**
 * ChatMessagesService
 *
 * The main service class for managing chat messages in the Sage AI extension.
 * Uses Zustand store for state management and React components for rendering.
 *
 * @example
 * ```typescript
 * const chatMessages = new ChatMessagesService({
 *   container,
 *   historyManager,
 *   notebookTools,
 *   onScrollDownButtonDisplay: onScroll
 * });
 *
 * chatMessages.addUserMessage("Hello");
 * chatMessages.addToolCalls([...]);
 * const history = chatMessages.getMessageHistory();
 * ```
 */

import React from 'react';
import { NotebookTools } from '@/Notebook/NotebookTools';
import { IChatMessage, ICheckpoint, IToolCall } from '@/types';
import { ChatHistoryManager, IChatThread } from './ChatHistoryManager';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import {
  getChatMessagesState,
  IDiffCellUI,
  IToolCallUIMessage,
  useChatMessagesStore
} from '@/stores/chatMessages';
import { CheckpointManager } from '@/Services/CheckpointManager';
import { getNotebookDiffManager } from '@/stores/servicesStore';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { isLauncherNotebookId } from '@/stores/chatModeStore';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { useWaitingReplyStore } from '@/stores/waitingReplyStore';
import { getIsDemoActivelyRunning } from '@/Demo/demo';
import { IMountedComponent, mountComponent } from '@/utils/reactMount';
import { ChatMessagesPanel } from '@/ChatBox/Messages/ChatMessagesPanel';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IChatMessagesServiceConfig {
  /** Container element to render messages into */
  container?: HTMLElement;
  /** Chat history manager for persistence */
  historyManager: ChatHistoryManager;
  /** Notebook tools for cell operations */
  notebookTools: NotebookTools;
  /** Callback when scroll button should be displayed */
  onScrollDownButtonDisplay: () => void;
}

// ═══════════════════════════════════════════════════════════════
// SERVICE CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * ChatMessagesService - Main service class for managing chat messages.
 * Uses Zustand for state management and React for rendering.
 */
export class ChatMessagesService {
  private historyManager: ChatHistoryManager;
  private notebookTools: NotebookTools;
  private onScrollDownButtonDisplay: () => void;
  private checkpointManager: CheckpointManager;
  private continueCallback: (() => void) | null = null;
  private promptCallback: ((prompt: string) => void) | null = null;
  private container: HTMLElement | null = null;
  private mountedComponent: IMountedComponent | null = null;

  constructor(config: IChatMessagesServiceConfig) {
    console.log('[ChatMessagesService] Constructor called with config:', {
      hasContainer: !!config.container,
      hasHistoryManager: !!config.historyManager,
      hasNotebookTools: !!config.notebookTools
    });

    this.historyManager = config.historyManager;
    this.notebookTools = config.notebookTools;
    this.onScrollDownButtonDisplay = config.onScrollDownButtonDisplay;
    this.checkpointManager = CheckpointManager.getInstance();
    this.container = config.container || null;

    // Mount React component if container provided
    if (this.container) {
      this.mountReactComponent();
    } else {
      console.warn(
        '[ChatMessagesService] No container provided, React component will not be mounted'
      );
    }
  }

  get messageHistory(): IChatMessage[] {
    return getChatMessagesState().llmHistory;
  }

  set messageHistory(value: IChatMessage[]) {
    // When setting to empty array, clear the store
    if (value.length === 0) {
      useChatMessagesStore.getState().clearMessages();
      useChatMessagesStore.getState().clearLlmHistory();
    }
    // Note: Setting to a non-empty array is not supported through this setter
    // Use loadFromThread() instead
  }

  // ============================================================
  // Message History
  // ============================================================

  /**
   * Unmount the React component (for cleanup)
   */
  dispose(): void {
    if (this.mountedComponent) {
      this.mountedComponent.unmount();
      this.mountedComponent = null;
    }
  }

  getMessageHistory(): IChatMessage[] {
    return getChatMessagesState().getLlmHistory();
  }

  async loadFromThread(thread: IChatThread): Promise<void> {
    console.log(
      '[ChatMessagesService] loadFromThread called for thread:',
      thread.id,
      'with',
      thread.messages.length,
      'messages'
    );
    const store = useChatMessagesStore.getState();

    // Convert LLM messages to UI messages
    const uiMessages = this.convertThreadToUIMessages(thread);
    console.log(
      '[ChatMessagesService] Converted to',
      uiMessages.length,
      'UI messages'
    );

    // Load into store
    store.loadFromThread(
      uiMessages,
      thread.messages,
      thread.contexts || new Map(),
      thread.id
    );
    console.log('[ChatMessagesService] loadFromThread complete');

    // Token progress is updated via the React ChatInputContainer
  }

  getMentionContexts(): Map<string, IMentionContext> {
    return getChatMessagesState().getMentionContexts();
  }

  setMentionContexts(contexts: Map<string, IMentionContext>): void {
    useChatMessagesStore.getState().setMentionContexts(contexts);
  }

  // ============================================================
  // Context Management
  // ============================================================

  addMentionContext(context: IMentionContext): void {
    useChatMessagesStore.getState().addMentionContext(context);
  }

  removeMentionContext(contextId: string): void {
    useChatMessagesStore.getState().removeMentionContext(contextId);
  }

  addContinueButton(): void {
    // Handled by React component, no-op
  }

  removeContinueButton(): void {
    // Handled by React component, no-op
  }

  // ============================================================
  // Continue Button / Waiting Reply
  // ============================================================

  showWaitingReplyBox(recommendedPrompts?: string[]): void {
    useWaitingReplyStore.getState().show(recommendedPrompts);
  }

  hideWaitingReplyBox(): void {
    useWaitingReplyStore.getState().hide();
  }

  setContinueCallback(callback: () => void): void {
    this.continueCallback = callback;
  }

  setPromptCallback(callback: (prompt: string) => void): void {
    this.promptCallback = callback;
  }

  updateContinueButtonVisibility(): void {
    // Handled reactively by the store
  }

  addThinkingIndicator(): void {
    console.log('[ChatMessagesService] addThinkingIndicator called');
    useChatMessagesStore.getState().showThinking();
  }

  removeThinkingIndicator(): void {
    console.log('[ChatMessagesService] removeThinkingIndicator called');
    useChatMessagesStore.getState().hideThinking();
  }

  // ============================================================
  // Streaming
  // ============================================================

  addStreamingAIMessage(): void {
    console.log('[ChatMessagesService] addStreamingAIMessage called');
    useChatMessagesStore.getState().startStreaming();
  }

  async updateStreamingMessage(text: string): Promise<void> {
    // IMPORTANT: Use appendStreamingText to APPEND text, not replace it
    useChatMessagesStore.getState().appendStreamingText(text);
    this.onScrollDownButtonDisplay();
  }

  removeStreamingMessage(): void {
    console.log('[ChatMessagesService] removeStreamingMessage called');
    // Cancel streaming without finalizing (for cancellation)
    const store = useChatMessagesStore.getState();
    store.cancelStreaming();
  }

  async finalizeStreamingMessage(_is_demo = false): Promise<void> {
    console.log('[ChatMessagesService] finalizeStreamingMessage called');
    const store = useChatMessagesStore.getState();
    const { streaming } = store;

    if (streaming.text) {
      // Add to LLM history
      store.addToLlmHistory({
        role: 'assistant',
        content: streaming.text
      });

      // Get fresh state after modification (store snapshot is now stale)
      const updatedStore = useChatMessagesStore.getState();

      // Persist with fresh state
      this.historyManager.updateCurrentThreadMessages(
        updatedStore.llmHistory,
        updatedStore.mentionContexts
      );
    }

    store.finalizeStreaming();
  }

  /**
   * Start a streaming tool call - adds to store
   */
  addStreamingToolCall(toolCallId: string, toolName: string): void {
    console.log(
      '[ChatMessagesService] addStreamingToolCall called:',
      toolName,
      toolCallId
    );
    useChatMessagesStore
      .getState()
      .startStreamingToolCall(toolCallId, toolName);
  }

  /**
   * Update a streaming tool call with new data
   */
  updateStreamingToolCall(toolCallId: string, toolUse: any): void {
    console.log(
      '[ChatMessagesService] updateStreamingToolCall called:',
      toolCallId,
      toolUse?.name
    );

    const store = useChatMessagesStore.getState();

    // Update the streaming tool call with accumulated input
    const toolInput = toolUse?.input || {};
    store.updateStreamingToolCall(toolCallId, toolInput);
  }

  /**
   * Remove a streaming tool call (for cancellation)
   */
  removeStreamingToolCall(toolCallId: string): void {
    console.log(
      '[ChatMessagesService] removeStreamingToolCall called:',
      toolCallId
    );
    useChatMessagesStore.getState().cancelStreamingToolCall(toolCallId);
  }

  /**
   * Finalize a streaming tool call - converts from streaming to permanent message
   */
  finalizeStreamingToolCall(toolCallId: string, _is_demo = false): void {
    console.log(
      '[ChatMessagesService] finalizeStreamingToolCall called:',
      toolCallId
    );
    useChatMessagesStore.getState().finalizeStreamingToolCall(toolCallId);
  }

  /**
   * Update a tool call with tool search result (for server_tool_use)
   */
  updateToolSearchResult(toolCallId: string, input: any, result: any): void {
    console.log(
      '[ChatMessagesService] updateToolSearchResult called:',
      toolCallId
    );
    useChatMessagesStore
      .getState()
      .updateToolSearchResult(toolCallId, input, result);
  }

  setWelcomeMessageHiddenMode(_hidden: boolean): void {
    // Handled by store state
  }

  async restoreToCheckpoint(checkpoint: ICheckpoint): Promise<void> {
    console.log(
      '[ChatMessagesService] restoreToCheckpoint called:',
      checkpoint.id
    );

    const store = useChatMessagesStore.getState();

    // Restore LLM history to the checkpoint state (excluding the checkpoint user message itself)
    const newLlmHistory = checkpoint.messageHistory.filter(
      msg => msg.id !== checkpoint.userMessageId
    );

    // Update the store with restored history and contexts
    store.setLlmHistory(newLlmHistory);
    store.setMentionContexts(new Map(checkpoint.contexts));

    // Persist the restored state
    this.historyManager.updateCurrentThreadMessages(
      newLlmHistory,
      new Map(checkpoint.contexts)
    );

    // Clear checkpoints after this one
    this.checkpointManager.clearCheckpointsAfter(checkpoint.id);

    console.log('[ChatMessagesService] LLM history and contexts restored');
  }

  addUserMessage(message: string, hidden = false, _is_demo = false): void {
    console.log('[ChatMessagesService] addUserMessage called:', {
      message,
      hidden
    });

    const store = useChatMessagesStore.getState();
    console.log(
      '[ChatMessagesService] Current store state - messages count:',
      store.messages.length
    );

    // Generate ID
    const id = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    // Create message object
    const userMessage: IChatMessage = {
      role: 'user',
      content: message,
      id,
      hidden
    };

    // Add to LLM history FIRST so checkpoint captures it
    store.addToLlmHistory(userMessage);

    // Get fresh state after adding to history
    const storeAfterHistory = useChatMessagesStore.getState();

    // Create checkpoint BEFORE adding to UI (so we can pass it to the message)
    let checkpoint: ICheckpoint | undefined;
    try {
      const notebookId = useNotebookEventsStore.getState().currentNotebookId;
      const threadId = storeAfterHistory.currentThreadId;
      console.log('[ChatMessagesService] Checkpoint conditions:', {
        notebookId,
        threadId,
        _is_demo,
        willCreate: !!(notebookId && threadId && !_is_demo)
      });
      if (notebookId && threadId && !_is_demo && !isLauncherNotebookId(notebookId)) {
        this.checkpointManager.setCurrentNotebookId(notebookId);
        checkpoint = this.checkpointManager.createCheckpoint(
          message,
          storeAfterHistory.llmHistory,
          storeAfterHistory.mentionContexts,
          threadId,
          id
        );
        console.log(
          '[ChatMessagesService] Created checkpoint:',
          checkpoint?.id
        );
      } else {
        console.warn(
          '[ChatMessagesService] Checkpoint NOT created - missing:',
          !notebookId ? 'notebookId' : '',
          !threadId ? 'threadId' : '',
          _is_demo ? 'is_demo=true' : ''
        );
      }
    } catch (error) {
      console.error('[ChatMessagesService] Error creating checkpoint:', error);
    }

    // Add to UI with checkpoint
    console.log(
      '[ChatMessagesService] Calling store.addUserMessage with checkpoint:',
      !!checkpoint
    );
    store.addUserMessage(message, checkpoint, { hidden });
    console.log(
      '[ChatMessagesService] After addUserMessage - messages count:',
      useChatMessagesStore.getState().messages.length
    );

    // Get fresh state after modifications (store snapshot is now stale)
    const updatedStore = useChatMessagesStore.getState();

    // Persist with fresh state
    this.historyManager.updateCurrentThreadMessages(
      updatedStore.llmHistory,
      updatedStore.mentionContexts
    );

    // Auto-rename thread if first message
    const currentThread = this.historyManager.getCurrentThread();
    console.log('[ChatMessagesService] Auto-rename check:', {
      threadName: currentThread?.name,
      threadId: currentThread?.id,
      hidden,
      shouldCheck: currentThread?.name === 'New Chat' && !hidden
    });

    if (currentThread?.name === 'New Chat' && !hidden) {
      const visibleUserMessages = updatedStore.llmHistory.filter(
        msg => msg.role === 'user' && !msg.hidden
      ).length;

      console.log(
        '[ChatMessagesService] Visible user messages:',
        visibleUserMessages
      );

      if (visibleUserMessages === 1) {
        const threadName = this.generateThreadName(message);
        console.log('[ChatMessagesService] Renaming thread to:', threadName);
        this.historyManager.renameCurrentThread(threadName);

        // Sync Zustand from ChatHistoryManager (single source of truth)
        console.log(
          '[ChatMessagesService] Syncing Zustand from ChatHistoryManager after rename'
        );
        void useChatHistoryStore.getState().syncFromManager();
      }
    }

    // Hide waiting reply
    useWaitingReplyStore.getState().hide();

    // Token progress is updated via the React ChatInputContainer
  }

  // ============================================================
  // Checkpoint
  // ============================================================

  addSystemMessage(message: string): void {
    console.log('[ChatMessagesService] addSystemMessage called:', message);
    useChatMessagesStore.getState().addSystemMessage(message);
    console.log(
      '[ChatMessagesService] After addSystemMessage - messages count:',
      useChatMessagesStore.getState().messages.length
    );
  }

  // ============================================================
  // Add Messages
  // ============================================================

  addErrorMessage(message: string): void {
    console.log('[ChatMessagesService] addErrorMessage called:', message);
    useChatMessagesStore.getState().addErrorMessage(message);
    console.log(
      '[ChatMessagesService] After addErrorMessage - messages count:',
      useChatMessagesStore.getState().messages.length
    );
  }

  /**
   * Add a loading indicator to the chat.
   * Uses Zustand store - no DOM manipulation.
   *
   * @returns The message ID of the loading indicator
   */
  addLoadingIndicator(text = 'Generating...'): string {
    console.log(
      '[ChatMessagesService] addLoadingIndicator called with text:',
      text
    );
    const id = useChatMessagesStore.getState().addLoading(text);
    console.log('[ChatMessagesService] Loading indicator added with id:', id);
    console.log(
      '[ChatMessagesService] Messages count after addLoading:',
      useChatMessagesStore.getState().messages.length
    );
    return id;
  }

  addToolCalls(toolCalls: IToolCall[]): void {
    if (!toolCalls?.length) return;
    console.log(
      '[ChatMessagesService] addToolCalls called:',
      toolCalls.map(t => ({ name: t.name, id: t.id }))
    );

    toolCalls.forEach(toolCall => {
      // Get fresh state for each check to avoid stale snapshot issues
      const store = useChatMessagesStore.getState();

      // Check if tool call already exists in messages (including streaming ones)
      const existingIndex = store.messages.findIndex(
        m =>
          m.type === 'tool_call' &&
          (m as IToolCallUIMessage).toolCallId === toolCall.id
      );

      if (existingIndex !== -1) {
        // Update existing tool call's input (e.g., to add generated cell_id)
        store.updateStreamingToolCall(toolCall.id, toolCall.input);
      } else {
        // Add new tool call
        store.addToolCall(toolCall.name, toolCall.input, toolCall.id);
      }

      // Always add to LLM history
      console.log(
        '[ChatMessagesService] Adding tool_use to llmHistory:',
        toolCall.name,
        toolCall.id
      );
      store.addToLlmHistory({
        role: 'assistant',
        content: [
          {
            type: 'tool_use',
            id: toolCall.id,
            name: toolCall.name,
            input: toolCall.input
          }
        ]
      });
    });

    // Get fresh state for persist
    const finalStore = useChatMessagesStore.getState();

    // Persist
    this.historyManager.updateCurrentThreadMessages(
      finalStore.llmHistory,
      finalStore.mentionContexts
    );
  }

  addToolResult(
    toolName: string,
    toolUseId: string,
    result: any,
    toolCallData: any,
    _is_demo = false
  ): void {
    const store = useChatMessagesStore.getState();

    // Check for errors
    let hasError = false;
    try {
      if (typeof result === 'string') {
        const parsed = JSON.parse(result);
        hasError = parsed?.error === true;
      }
    } catch {
      // Not JSON
    }

    // Add to UI
    store.addToolResult(toolName, toolUseId, result, toolCallData, hasError);

    // Add to LLM history
    store.addToLlmHistory({
      role: 'user',
      content: [
        {
          type: 'tool_result',
          tool_use_id: toolUseId,
          content: result
        }
      ]
    });

    // Get fresh state after modification (store snapshot is now stale)
    const updatedStore = useChatMessagesStore.getState();

    // Persist with fresh state
    this.historyManager.updateCurrentThreadMessages(
      updatedStore.llmHistory,
      updatedStore.mentionContexts
    );
  }

  addDiffApprovalDialog(
    notebookPath?: string,
    diffCells?: any[],
    _renderImmediately = false
  ): void {
    console.log('[ChatMessagesService] addDiffApprovalDialog called', {
      notebookPath,
      diffCellsCount: diffCells?.length,
      diffCells
    });

    const store = useChatMessagesStore.getState();

    // Convert to IDiffCellUI format
    const formattedCells: IDiffCellUI[] = (diffCells || []).map(cell => ({
      cellId: cell.cellId,
      type: cell.type,
      originalContent: cell.originalContent || '',
      newContent: cell.newContent || '',
      displaySummary: cell.displaySummary || `${cell.type} cell`
    }));

    console.log('[ChatMessagesService] Formatted cells:', formattedCells);

    // Add to UI
    const messageId = store.addDiffApproval(notebookPath, formattedCells, true);
    console.log(
      '[ChatMessagesService] Added diff approval with ID:',
      messageId
    );
    console.log(
      '[ChatMessagesService] Current messages count:',
      store.messages.length
    );

    // Add to LLM history (as special message type)
    store.addToLlmHistory({
      role: 'diff_approval' as any,
      content: [
        {
          type: 'diff_approval',
          id: `diff_approval_${Date.now()}`,
          timestamp: new Date().toISOString(),
          notebook_path: notebookPath,
          diff_cells: formattedCells
        }
      ]
    });

    // Get fresh state after modification (store snapshot is now stale)
    const updatedStore = useChatMessagesStore.getState();

    // Persist with fresh state
    this.historyManager.updateCurrentThreadMessages(
      updatedStore.llmHistory,
      updatedStore.mentionContexts
    );
  }

  displayAuthenticationCard(): void {
    useChatMessagesStore.getState().showAuthenticationCard();
  }

  displaySubscriptionCard(): void {
    useChatMessagesStore.getState().showSubscriptionCard();
  }

  removeLoadingText(): void {
    console.log('[ChatMessagesService] removeLoadingText called');
    // Remove any loading type messages
    const store = useChatMessagesStore.getState();
    const loadingMessages = store.messages.filter(
      msg => msg.type === 'loading'
    );
    console.log(
      '[ChatMessagesService] Found',
      loadingMessages.length,
      'loading messages to remove'
    );
    loadingMessages.forEach(msg => {
      console.log('[ChatMessagesService] Removing loading message:', msg.id);
      store.removeMessage(msg.id);
    });
    console.log(
      '[ChatMessagesService] Messages count after removeLoadingText:',
      useChatMessagesStore.getState().messages.length
    );
  }

  // ============================================================
  // Special Cards
  // ============================================================

  scrollToBottom(): void {
    // Trigger scroll via store state
    useChatMessagesStore.getState().setScrollAtBottom(true);
    this.onScrollDownButtonDisplay();
  }

  isFullyScrolledToBottom(): boolean {
    return getChatMessagesState().scrollState.isAtBottom;
  }

  // ============================================================
  // Loading State Management
  // ============================================================

  handleScroll(): void {
    if (this.isFullyScrolledToBottom()) {
      this.scrollToBottom();
    } else {
      this.onScrollDownButtonDisplay();
    }
  }

  /**
   * Mount the ChatMessagesPanel React component into the container
   */
  private mountReactComponent(): void {
    if (!this.container) {
      console.error(
        '[ChatMessagesService] Cannot mount React component: no container'
      );
      return;
    }

    console.log(
      '[ChatMessagesService] Mounting ChatMessagesPanel React component'
    );

    const element = React.createElement(ChatMessagesPanel, {
      notebookTools: this.notebookTools,
      historyManager: this.historyManager,
      // Note: onCheckpointRestore is not provided - the ChatMessagesPanel uses useChatCheckpoint hook
      // which handles the restoration flow correctly (setting input, marking messages opaque, etc.)
      onContinue: () => {
        console.log('[ChatMessagesService] onContinue callback triggered');
        if (this.continueCallback) {
          this.continueCallback();
        }
      },
      onWaitingReplyPrompt: (prompt: string) => {
        console.log(
          '[ChatMessagesService] onWaitingReplyPrompt callback triggered:',
          prompt
        );
        if (this.promptCallback) {
          this.promptCallback(prompt);
        }
      }
    });

    this.mountedComponent = mountComponent(this.container, element);
    console.log('[ChatMessagesService] React component mounted successfully');
  }

  private convertThreadToUIMessages(thread: IChatThread): any[] {
    const uiMessages: any[] = [];
    const generateId = () =>
      `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    // Track tool calls to associate results with them
    let lastToolGroup: { toolCallIds: string[] } | null = null;

    console.log(
      '[ChatMessagesService] convertThreadToUIMessages called, message count:',
      thread.messages.length
    );

    // Find the last wait_user_reply tool call to show its recommended prompts
    // But only if the user hasn't already replied after it
    let lastWaitUserReplyPrompts: string[] | undefined;
    let waitUserReplyIndex = -1;

    for (let i = thread.messages.length - 1; i >= 0; i--) {
      const msg = thread.messages[i];
      // Debug: log each message we're checking
      if (msg.role === 'assistant' && Array.isArray(msg.content)) {
        const toolUse = msg.content.find(
          (c: any) => c.type === 'tool_use' || c.type === 'server_tool_use'
        );
        if (toolUse) {
          console.log(
            '[ChatMessagesService] Found tool_use at index',
            i,
            ':',
            toolUse.name
          );
        }
      }

      if (
        msg.role === 'assistant' &&
        Array.isArray(msg.content) &&
        (msg.content[0]?.type === 'tool_use' ||
          msg.content[0]?.type === 'server_tool_use') &&
        msg.content[0]?.name === 'notebook-wait_user_reply'
      ) {
        lastWaitUserReplyPrompts =
          msg.content[0].input?.recommended_next_prompts;
        waitUserReplyIndex = i;
        console.log(
          '[ChatMessagesService] Found wait_user_reply at index',
          i,
          'with prompts:',
          lastWaitUserReplyPrompts
        );
        break;
      }
    }

    // Check if user has already replied after the wait_user_reply tool call
    // If so, don't show the waiting reply box
    if (waitUserReplyIndex >= 0 && lastWaitUserReplyPrompts) {
      for (let i = waitUserReplyIndex + 1; i < thread.messages.length; i++) {
        const msg = thread.messages[i];
        // Check for non-hidden user messages with actual text content (not tool_result)
        if (
          msg.role === 'user' &&
          !msg.hidden &&
          typeof msg.content === 'string' &&
          msg.content.trim().length > 0
        ) {
          console.log(
            '[ChatMessagesService] User already replied after wait_user_reply at index',
            i,
            '- not showing waiting reply box'
          );
          lastWaitUserReplyPrompts = undefined;
          break;
        }
      }
    }

    for (const msg of thread.messages) {
      if (msg.role === 'user') {
        // Handle tool results - render them alongside their tool calls
        if (
          Array.isArray(msg.content) &&
          msg.content[0]?.type === 'tool_result'
        ) {
          // Tool results are tracked but don't need separate UI messages
          // The tool call display shows the completed state
          continue;
        }

        const content =
          typeof msg.content === 'string'
            ? msg.content
            : msg.content[0]?.text || JSON.stringify(msg.content);

        // Look up checkpoint for this user message
        let checkpoint: ICheckpoint | undefined;
        if (msg.id) {
          checkpoint =
            this.checkpointManager.findCheckpointByUserMessageId(msg.id) ??
            undefined;
        }
        if (!checkpoint) {
          checkpoint =
            this.checkpointManager.findCheckpointByUserMessage(content) ??
            undefined;
        }

        lastToolGroup = null; // Reset tool group on user message
        uiMessages.push({
          id: msg.id || generateId(),
          type: 'user',
          timestamp: Date.now(),
          content,
          hidden: msg.hidden,
          checkpoint
        });
      } else if (msg.role === 'assistant') {
        // Tool uses
        if (
          Array.isArray(msg.content) &&
          (msg.content[0]?.type === 'tool_use' ||
            msg.content[0]?.type === 'server_tool_use')
        ) {
          lastToolGroup = { toolCallIds: [] };
          for (const toolUse of msg.content) {
            if (
              toolUse.type === 'tool_use' ||
              toolUse.type === 'server_tool_use'
            ) {
              // Skip wait_user_reply tool calls - they're handled separately
              // by showing the waiting reply box with recommended prompts
              if (toolUse.name === 'notebook-wait_user_reply') {
                continue;
              }
              lastToolGroup.toolCallIds.push(toolUse.id);
              uiMessages.push({
                id: generateId(),
                type: 'tool_call',
                timestamp: Date.now(),
                toolName: toolUse.name,
                toolInput: toolUse.input,
                toolCallId: toolUse.id,
                isStreaming: false
              });
            }
          }
        } else {
          lastToolGroup = null;
          const content =
            typeof msg.content === 'string'
              ? msg.content
              : msg.content[0]?.text || '';

          if (content) {
            uiMessages.push({
              id: msg.id || generateId(),
              type: 'assistant',
              timestamp: Date.now(),
              content,
              showHeader: true
            });
          }
        }
      } else if (msg.role === 'diff_approval') {
        // Handle diff approval messages from history
        lastToolGroup = null;
        if (
          Array.isArray(msg.content) &&
          msg.content[0]?.type === 'diff_approval'
        ) {
          const diffContent = msg.content[0];
          const diffCells = (diffContent.diff_cells || []).map((cell: any) => ({
            cellId: cell.cellId,
            type: cell.type,
            originalContent: cell.originalContent || '',
            newContent: cell.newContent || '',
            displaySummary: cell.displaySummary || `${cell.type} cell`
          }));

          uiMessages.push({
            id: diffContent.id || generateId(),
            type: 'diff_approval',
            timestamp: Date.now(),
            notebookPath: diffContent.notebook_path,
            diffCells,
            isHistorical: true // Historical diffs are always non-interactive
          });
        }
      }
    }

    // If we found a wait_user_reply with prompts, show the waiting reply box
    // But skip if demo is actively running - demo handles its own flow
    if (lastWaitUserReplyPrompts && lastWaitUserReplyPrompts.length > 0) {
      if (getIsDemoActivelyRunning()) {
        console.log(
          '[ChatMessagesService] Skipping showWaitingReply - demo is actively running'
        );
      } else {
        console.log(
          '[ChatMessagesService] Scheduling showWaitingReply with prompts:',
          lastWaitUserReplyPrompts
        );
        // Schedule showing the waiting reply box after messages load
        setTimeout(() => {
          // Double-check demo state in case it changed
          if (getIsDemoActivelyRunning()) {
            console.log(
              '[ChatMessagesService] Skipping showWaitingReply in timeout - demo started'
            );
            return;
          }
          console.log('[ChatMessagesService] Calling showWaitingReply now');
          useWaitingReplyStore.getState().show(lastWaitUserReplyPrompts);
          console.log(
            '[ChatMessagesService] waitingReply state after call:',
            useWaitingReplyStore.getState()
          );
        }, 500); // Increased timeout to ensure UI is ready
      }
    } else {
      console.log(
        '[ChatMessagesService] No wait_user_reply prompts found to show'
      );
    }

    return uiMessages;
  }

  private generateThreadName(message: string): string {
    const processed = message
      .replace(/<[^>]*_CONTEXT>[^<]*<\/[^>]*_CONTEXT>/gi, '')
      .trim();

    const words = processed.split(/\s+/);
    const selected = words.slice(0, Math.min(8, words.length));
    let name = selected.join(' ');

    if (name.length > 30) {
      name = name.substring(0, 27) + '...';
    }

    return name || 'New Chat';
  }
}

export default ChatMessagesService;

// Alias for backwards compatibility
export { ChatMessagesService as ChatMessages };
