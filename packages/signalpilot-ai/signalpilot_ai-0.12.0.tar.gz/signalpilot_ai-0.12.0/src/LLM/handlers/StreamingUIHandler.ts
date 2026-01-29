/**
 * StreamingUIHandler - Handles all UI updates during LLM streaming
 *
 * This completely separates UI concerns from the LLM loop logic.
 * All streaming-related UI updates are centralized here.
 *
 * Also handles real-time notebook updates during streaming for
 * add_cell, edit_cell, and edit_plan operations.
 */

import { useChatMessagesStore } from '../../stores/chatMessages';
import { useLLMStateStore } from '../../stores/llmStateStore';
import { useChatUIStore } from '../../stores/chatUIStore';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ToolService } from '../ToolService';
import { NotebookDiffManager } from '../../Notebook/NotebookDiffManager';
import { IStreamingUIState, IToolUseEvent } from '../LLMTypes';
import { parse } from 'partial-json';
import { NotebookActions } from '@jupyterlab/notebook';

// ═══════════════════════════════════════════════════════════════
// TOOL CALL INFO INTERFACE
// ═══════════════════════════════════════════════════════════════

export interface ToolCallInfo {
  id: string;
  name: string;
  accumulatedInput: string;
  type?: string; // 'tool_use' or 'server_tool_use'
  cellId?: string;
  originalContent?: string;
  originalSummary?: string;
  position?: number;
  summary?: string;
  toolResult?: {
    type: 'tool_result';
    tool_use_id: string;
    content: string;
  };
  toolCallData?: any;
  operationQueue?: {
    pendingOperation?: NodeJS.Timeout;
    lastProcessedInput?: string;
  };
}

// ═══════════════════════════════════════════════════════════════
// STREAMING SNAPSHOT INTERFACES (for rollback on cancellation)
// ═══════════════════════════════════════════════════════════════

/**
 * Represents a cell that was added during streaming (for deletion on rollback)
 */
interface IAddedCellSnapshot {
  type: 'add';
  cellId: string; // tracking ID of the created cell
  toolId: string;
}

/**
 * Represents a cell that was edited during streaming (for restoration on rollback)
 */
interface IEditedCellSnapshot {
  type: 'edit';
  cellId: string;
  originalContent: string;
  originalSummary: string;
  toolId: string;
}

/**
 * Represents the plan cell state before streaming (for restoration on rollback)
 */
interface IPlanSnapshot {
  type: 'plan';
  existed: boolean;
  originalContent: string;
  toolId: string;
  cellCountBefore: number; // Track notebook cell count to detect if a cell was added
}

/**
 * Union type for all streaming change snapshots
 */
type IStreamingChangeSnapshot =
  | IAddedCellSnapshot
  | IEditedCellSnapshot
  | IPlanSnapshot;

// ═══════════════════════════════════════════════════════════════
// MAIN CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * Extended streaming state with tool call tracking
 */
export interface IExtendedStreamingState extends IStreamingUIState {
  streamingToolCalls: Map<string, ToolCallInfo>;
}

/**
 * Handler for all streaming UI updates
 */
export class StreamingUIHandler {
  private messageComponent: ChatMessages;
  private toolService: ToolService | null;
  private diffManager: NotebookDiffManager | null;
  private notebookId: string | null;
  private state: IExtendedStreamingState;

  // Snapshots of changes made during streaming (for rollback on cancellation)
  private streamingSnapshots: IStreamingChangeSnapshot[] = [];

  // Callback to cancel the current request (set by LLMLoop)
  private cancelRequestCallback: (() => void) | null = null;

  // Flag to track if open_notebook was called (to stop processing further tools)
  private openNotebookCalled: boolean = false;

  constructor(
    messageComponent: ChatMessages,
    toolService?: ToolService,
    diffManager?: NotebookDiffManager | null,
    notebookId?: string | null
  ) {
    this.messageComponent = messageComponent;
    this.toolService = toolService || null;
    this.diffManager = diffManager || null;
    this.notebookId = notebookId || null;
    this.state = {
      isStreamingMessage: false,
      isThinkingActive: false,
      activeToolCallIds: new Set(),
      streamingMessageId: null,
      streamingToolCalls: new Map()
    };
  }

  /**
   * Update the notebook ID (needed for streaming operations)
   */
  setNotebookId(notebookId: string | null): void {
    this.notebookId = notebookId;
  }

  /**
   * Set the tool service (for real-time notebook updates)
   */
  setToolService(toolService: ToolService): void {
    this.toolService = toolService;
  }

  /**
   * Set the diff manager
   */
  setDiffManager(diffManager: NotebookDiffManager | null): void {
    this.diffManager = diffManager;
  }

  /**
   * Set the cancel request callback (called when open_notebook is detected)
   */
  setCancelRequestCallback(callback: () => void): void {
    this.cancelRequestCallback = callback;
  }

  /**
   * Check if open_notebook was called during this streaming session
   */
  wasOpenNotebookCalled(): boolean {
    return this.openNotebookCalled;
  }

  // ═══════════════════════════════════════════════════════════════
  // LIFECYCLE METHODS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Called when starting a new LLM request
   */
  onRequestStart(): void {
    console.log('[StreamingUIHandler] Request started');

    // Show thinking indicator
    this.messageComponent.addThinkingIndicator();
    this.state.isThinkingActive = true;

    // Show LLM state display
    useLLMStateStore.getState().show('Generating...');
  }

  /**
   * Called when request completes successfully
   */
  onRequestComplete(): void {
    console.log('[StreamingUIHandler] Request completed');

    this.hideThinking();
    this.finalizeStreaming();
    useLLMStateStore.getState().hide();

    // Clear snapshots on successful completion (no rollback needed)
    this.streamingSnapshots = [];
  }

  /**
   * Called when request is cancelled
   */
  onRequestCancelled(): void {
    console.log('[StreamingUIHandler] Request cancelled');
    console.log(
      `[StreamingUIHandler] Snapshots count before rollback: ${this.streamingSnapshots.length}`
    );
    if (this.streamingSnapshots.length > 0) {
      console.log(
        '[StreamingUIHandler] Snapshots:',
        JSON.stringify(
          this.streamingSnapshots.map(s => ({ type: s.type, toolId: s.toolId }))
        )
      );
    }

    this.hideThinking();

    // Rollback any notebook changes made during streaming
    this.rollbackStreamingChanges();

    this.removeStreaming();
    useLLMStateStore.getState().hide();
  }

  /**
   * Called when an error occurs
   */
  onRequestError(error: Error): void {
    console.error('[StreamingUIHandler] Request error:', error);

    this.hideThinking();

    // Rollback any notebook changes made during streaming
    this.rollbackStreamingChanges();

    this.removeStreaming();
    useLLMStateStore.getState().hide();

    // Add error message to chat
    this.messageComponent.addErrorMessage(
      error.message || 'An unexpected error occurred'
    );
  }

  // ═══════════════════════════════════════════════════════════════
  // TEXT STREAMING
  // ═══════════════════════════════════════════════════════════════

  /**
   * Hide the launcher welcome loader (called when first content streams)
   * Uses React state via chatUIStore instead of DOM manipulation
   */
  private hideLauncherLoader(): void {
    useChatUIStore.getState().setShowLauncherWelcomeLoader(false);
  }

  /**
   * Handle incoming text chunk from stream
   */
  onTextChunk(text: string): void {
    // If open_notebook was called, ignore further text chunks
    // This prevents broken/partial text from appearing after notebook switch
    if (this.openNotebookCalled) {
      return;
    }

    this.hideThinking();

    // Hide launcher loader on first content (only runs once, no-op if already hidden)
    this.hideLauncherLoader();

    if (!this.state.isStreamingMessage) {
      // Start new streaming message
      const messageId = useChatMessagesStore.getState().startStreaming();
      this.state.streamingMessageId = messageId;
      this.state.isStreamingMessage = true;
    }

    // Append text to streaming message
    useChatMessagesStore.getState().appendStreamingText(text);
  }

  /**
   * Handle complete text (non-streaming)
   */
  onTextComplete(text: string): void {
    // If open_notebook was called, ignore further text
    if (this.openNotebookCalled) {
      return;
    }

    this.hideThinking();

    // If we were streaming, finalize it first
    if (this.state.isStreamingMessage) {
      this.finalizeStreamingMessage();
    }

    // Add the complete assistant message via store
    if (text && text.trim()) {
      useChatMessagesStore.getState().addAssistantMessage(text);
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // TOOL STREAMING
  // ═══════════════════════════════════════════════════════════════

  /**
   * Handle tool use events from streaming
   */
  onToolUseEvent(toolUse: IToolUseEvent): void {
    // If open_notebook was already called, ignore all further tool events
    // This prevents additional tools from being processed after the notebook switch
    if (this.openNotebookCalled) {
      console.log(
        '[StreamingUIHandler] Ignoring tool event after open_notebook:',
        toolUse.type,
        toolUse.name
      );
      return;
    }

    switch (toolUse.type) {
      case 'tool_use':
      case 'server_tool_use':
        this.onToolStart(
          toolUse.id,
          toolUse.name || 'unknown',
          toolUse.input,
          toolUse.type
        );
        break;
      case 'tool_use_delta':
        this.onToolUpdate(toolUse.id, toolUse.input_delta);
        break;
      case 'tool_use_stop':
        this.onToolComplete(toolUse.id, toolUse.input);
        break;
    }
  }

  /**
   * Handle tool use start
   */
  onToolStart(
    toolId: string,
    toolName: string,
    input?: any,
    type?: string
  ): void {
    this.hideThinking();

    // Hide launcher loader on first content (tool start)
    this.hideLauncherLoader();

    if (!this.state.activeToolCallIds.has(toolId)) {
      console.log('[StreamingUIHandler] Tool started:', toolName, toolId, type);

      // IMPORTANT: Finalize any current streaming message before adding tool call
      // This ensures correct ordering: text1 -> tool_call -> text2
      // Without this, all text accumulates in one message that appears before tool calls
      if (this.state.isStreamingMessage) {
        this.finalizeStreamingMessage();
      }

      // Add tool call to store
      useChatMessagesStore.getState().startStreamingToolCall(toolId, toolName);
      this.state.activeToolCallIds.add(toolId);

      // Track tool call info for streaming operations
      this.state.streamingToolCalls.set(toolId, {
        id: toolId,
        name: toolName,
        accumulatedInput: '',
        type: type // 'tool_use' or 'server_tool_use'
      });

      // Update LLM state display using store directly
      const llmState = useLLMStateStore.getState();
      if (!llmState.isDiffState()) {
        llmState.showTool(toolName);
      }

      // CRITICAL: If open_notebook is called, set the flag to stop processing further tools
      // This prevents duplicate agents and broken history when switching from launcher to notebook
      if (toolName === 'open_notebook') {
        console.log(
          '[StreamingUIHandler] open_notebook detected - will ignore further tool events'
        );
        this.openNotebookCalled = true;
      }
    }
  }

  /**
   * Handle tool use update (delta)
   */
  onToolUpdate(toolId: string, partialInput: any): void {
    if (!this.state.activeToolCallIds.has(toolId) || !partialInput) {
      return;
    }

    const toolCallInfo = this.state.streamingToolCalls.get(toolId);
    if (!toolCallInfo) {
      return;
    }

    // Accumulate input
    toolCallInfo.accumulatedInput += partialInput;

    // Handle real-time notebook updates with queue
    this.handleToolUseDeltaWithQueue(toolId, toolCallInfo, partialInput);
  }

  /**
   * Handle tool use complete
   */
  onToolComplete(toolId: string, input?: any): void {
    if (!this.state.activeToolCallIds.has(toolId)) {
      return;
    }

    console.log('[StreamingUIHandler] Tool completed:', toolId);

    const toolCallInfo = this.state.streamingToolCalls.get(toolId);

    // Process any remaining queued operations
    if (toolCallInfo?.operationQueue?.pendingOperation) {
      clearTimeout(toolCallInfo.operationQueue.pendingOperation);
      toolCallInfo.operationQueue.pendingOperation = undefined;

      // Process remaining input
      const codeRegex = /"(?:source|new_source)"\s*:\s*"((?:[^"\\]|\\.)*)/;
      const match = toolCallInfo.accumulatedInput.match(codeRegex);
      if (match && match[1]) {
        const code = JSON.parse(`"${match[1]}"`);
        this.handleRealTimeNotebookUpdates(toolCallInfo, code, toolId, false);
      }
    }

    // Finalize the tool in the notebook (apply final state)
    if (toolCallInfo && input) {
      this.finalizeToolInNotebook(toolCallInfo, input);
    }

    // Store the final tool data
    if (toolCallInfo) {
      toolCallInfo.toolCallData = input;
    }

    useChatMessagesStore.getState().finalizeStreamingToolCall(toolId);
  }

  /**
   * Handle tool result display
   */
  onToolResult(
    toolName: string,
    toolUseId: string,
    result: any,
    toolCallData?: any,
    hasError: boolean = false
  ): void {
    useChatMessagesStore
      .getState()
      .addToolResult(toolName, toolUseId, result, toolCallData, hasError);
  }

  /**
   * Handle tool search result (for server_tool_use like tool_search_tool_regex)
   *
   * IMPORTANT: server_tool_use is an internal API operation for tool search.
   * The API handles it internally and does NOT expect us to send back the
   * tool_result for server_tool_use blocks. We only update the UI state here,
   * but do NOT add anything to LLM history.
   */
  onToolSearchResult(toolUseId: string, result: any): void {
    const toolCallInfo = this.state.streamingToolCalls.get(toolUseId);
    if (toolCallInfo) {
      let input = {};
      try {
        input = toolCallInfo.accumulatedInput
          ? JSON.parse(toolCallInfo.accumulatedInput)
          : {};
      } catch (e) {
        console.warn(
          '[StreamingUIHandler] Failed to parse tool input for tool search:',
          e
        );
      }

      // Update UI state only - DO NOT add to LLM history
      // server_tool_use is handled internally by the API and should not be echoed back
      useChatMessagesStore
        .getState()
        .updateToolSearchResult(toolUseId, input, result);

      console.log(
        '[StreamingUIHandler] Tool search completed (UI only, not added to LLM history):',
        {
          toolUseId,
          input,
          result
        }
      );
    }
  }

  /**
   * Update the loading indicator text
   */
  updateLoadingIndicator(text: string): void {
    useLLMStateStore.getState().show(text);
  }

  /**
   * Show waiting for user indicator
   */
  showWaitingForUser(): void {
    useLLMStateStore.getState().show('Waiting for your response...', true);
  }

  /**
   * Get current streaming state
   */
  getState(): IStreamingUIState {
    return { ...this.state };
  }

  /**
   * Check if currently streaming
   */
  isStreaming(): boolean {
    return (
      this.state.isStreamingMessage || this.state.activeToolCallIds.size > 0
    );
  }

  /**
   * Reset state for new request
   */
  reset(): void {
    // Clear any pending operations
    for (const toolCallInfo of this.state.streamingToolCalls.values()) {
      if (toolCallInfo.operationQueue?.pendingOperation) {
        clearTimeout(toolCallInfo.operationQueue.pendingOperation);
      }
    }

    this.state = {
      isStreamingMessage: false,
      isThinkingActive: false,
      activeToolCallIds: new Set(),
      streamingMessageId: null,
      streamingToolCalls: new Map()
    };

    // Clear streaming snapshots for new request
    this.streamingSnapshots = [];

    // Reset the open_notebook flag for new request
    this.openNotebookCalled = false;
  }

  /**
   * Get streaming tool calls for use by tool execution
   */
  getStreamingToolCalls(): Map<string, ToolCallInfo> {
    return this.state.streamingToolCalls;
  }

  // ═══════════════════════════════════════════════════════════════
  // LOADING INDICATOR
  // ═══════════════════════════════════════════════════════════════

  /**
   * Get a specific streaming tool call by ID
   */
  getStreamingToolCall(toolId: string): ToolCallInfo | undefined {
    return this.state.streamingToolCalls.get(toolId);
  }

  /**
   * Remove a streaming tool call after it's been processed
   */
  removeStreamingToolCall(toolId: string): void {
    this.state.streamingToolCalls.delete(toolId);
  }

  // ═══════════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Handle tool use delta with queue system to prevent rapid operations
   */
  private handleToolUseDeltaWithQueue(
    toolId: string,
    toolCallInfo: ToolCallInfo,
    _partialInput: any
  ): void {
    // Initialize queue if not exists
    if (!toolCallInfo.operationQueue) {
      toolCallInfo.operationQueue = {};
    }

    // Extract code from partial JSON
    const codeRegex =
      /"(?:source|new_source|updated_plan_string)"\s*:\s*"((?:[^"\\]|\\.)*)/;
    const match = toolCallInfo.accumulatedInput.match(codeRegex);

    if (!match || !match[1]) {
      return;
    }

    const code = JSON.parse(`"${match[1]}"`);

    // Clear any pending operations
    if (toolCallInfo.operationQueue.pendingOperation) {
      clearTimeout(toolCallInfo.operationQueue.pendingOperation);
    }

    // Check if this is a significantly different input to avoid unnecessary operations
    const currentInput = toolCallInfo.accumulatedInput;
    if (toolCallInfo.operationQueue.lastProcessedInput === currentInput) {
      return; // Skip if input hasn't changed
    }

    // Queue the operation with a short debounce delay (100ms)
    toolCallInfo.operationQueue.pendingOperation = setTimeout(() => {
      try {
        this.handleRealTimeNotebookUpdates(toolCallInfo, code, toolId, true);

        // Update streaming tool call in the store via ID
        if (this.state.activeToolCallIds.has(toolId)) {
          const partialToolUse = this.buildPartialToolUse(toolCallInfo, code);
          useChatMessagesStore
            .getState()
            .updateStreamingToolCall(toolId, partialToolUse);
        }

        // Mark this input as processed
        toolCallInfo.operationQueue!.lastProcessedInput = currentInput;
      } catch (error) {
        console.error('Error in queued notebook operation:', error);
      }

      // Clear the pending operation
      toolCallInfo.operationQueue!.pendingOperation = undefined;
    }, 100); // 100ms debounce
  }

  /**
   * Build partial tool use object for UI updates
   */
  private buildPartialToolUse(toolCallInfo: ToolCallInfo, code: string): any {
    const partialToolUse: any = {
      type: 'tool_use',
      id: toolCallInfo.id,
      name: toolCallInfo.name,
      input: {
        is_streaming: true
      }
    };

    if (toolCallInfo.name === 'notebook-edit_plan') {
      partialToolUse.input.updated_plan_string = code;
    } else if (toolCallInfo.name === 'notebook-add_cell') {
      partialToolUse.input.source = code;
      if (toolCallInfo.cellId) {
        partialToolUse.input.cell_id = toolCallInfo.cellId;
      }
    } else if (toolCallInfo.name === 'notebook-edit_cell') {
      partialToolUse.input.new_source = code;
      if (toolCallInfo.cellId) {
        partialToolUse.input.cell_id = toolCallInfo.cellId;
      }
    }

    return partialToolUse;
  }

  /**
   * Handle real-time notebook updates during streaming
   */
  private handleRealTimeNotebookUpdates(
    toolCallInfo: ToolCallInfo,
    code: string,
    toolId: string,
    isStreaming: boolean
  ): void {
    if (!this.toolService) {
      return;
    }

    const isAddCell = toolCallInfo.name === 'notebook-add_cell';
    const isEditCell = toolCallInfo.name === 'notebook-edit_cell';
    const isEditPlan = toolCallInfo.name === 'notebook-edit_plan';

    if (isEditPlan) {
      // Record plan state for rollback (only once per edit_plan tool call)
      const planAlreadyRecorded = this.streamingSnapshots.some(
        s => s.type === 'plan' && (s as IPlanSnapshot).toolId === toolId
      );
      if (!planAlreadyRecorded) {
        this.capturePlanStateForRollback(toolId);
      }

      this.toolService.notebookTools?.stream_edit_plan({
        partial_plan: code,
        notebook_path: this.notebookId
      });
    }

    if (isAddCell) {
      this.handleAddCellStreaming(toolCallInfo, code, toolId);
    }

    if (isEditCell) {
      this.handleEditCellStreaming(toolCallInfo, code, toolId);
    }
  }

  /**
   * Capture plan cell state for potential rollback
   */
  private capturePlanStateForRollback(toolId: string): void {
    if (!this.toolService?.notebookTools) {
      return;
    }

    try {
      const current = this.toolService.notebookTools.getCurrentNotebook(
        this.notebookId
      );
      if (!current) {
        return;
      }

      const { notebook } = current;
      let planContent = '';
      let planExists = false;
      const cellCountBefore = notebook.widgets.length;

      // Find the plan cell by checking for sage_cell_type === 'plan' metadata
      for (let i = 0; i < notebook.widgets.length; i++) {
        const cell = notebook.widgets[i];
        const metadata: any = cell?.model?.sharedModel?.getMetadata() || {};
        if (metadata.custom?.sage_cell_type === 'plan') {
          planContent = cell.model.sharedModel.getSource() || '';
          planExists = true;
          break;
        }
      }

      this.streamingSnapshots.push({
        type: 'plan',
        existed: planExists,
        originalContent: planContent,
        toolId: toolId,
        cellCountBefore: cellCountBefore
      });

      console.log(
        `[StreamingUIHandler] Plan cell state recorded for rollback (existed: ${planExists}, cellCount: ${cellCountBefore}, content length: ${planContent.length})`
      );
    } catch (error) {
      console.warn(
        '[StreamingUIHandler] Could not capture plan state for rollback:',
        error
      );
    }
  }

  /**
   * Handle add cell streaming
   */
  private handleAddCellStreaming(
    toolCallInfo: ToolCallInfo,
    code: string,
    toolId: string
  ): void {
    if (!this.toolService) {
      return;
    }

    try {
      const partialJson = parse(toolCallInfo.accumulatedInput);
      if (partialJson.position) {
        toolCallInfo.position = partialJson.position;
      }
    } catch (error) {
      console.error('Invalid JSON in accumulated input:', error);
      return;
    }

    const cellTypeRegex = /"cell_type"\s*:\s*"([^"]*)"/;
    const cellTypeMatch = toolCallInfo.accumulatedInput.match(cellTypeRegex);
    const cellType = cellTypeMatch ? cellTypeMatch[1] : null;

    const cellSummaryRegex = /"summary"\s*:\s*"([^"]*)"/;
    const cellSummaryMatch =
      toolCallInfo.accumulatedInput.match(cellSummaryRegex);
    const cellSummary = cellSummaryMatch
      ? cellSummaryMatch[1]
      : 'Cell being created by AI...';

    const validCellTypes = ['code', 'markdown'];
    if (!cellType || !validCellTypes.includes(cellType)) {
      return;
    }

    if (!toolCallInfo.cellId) {
      // First delta: create the cell
      try {
        const newCellId = this.toolService.notebookTools?.add_cell({
          cell_type: cellType,
          summary: cellSummary,
          source: code,
          notebook_path: this.notebookId,
          position: toolCallInfo.position
        });

        if (!newCellId) {
          throw new Error('Failed to create new cell, no ID returned');
        }

        toolCallInfo.cellId = newCellId;
        toolCallInfo.toolResult = {
          type: 'tool_result',
          tool_use_id: toolId,
          content: newCellId || ''
        };

        // Record this cell creation for potential rollback
        this.streamingSnapshots.push({
          type: 'add',
          cellId: newCellId,
          toolId: toolId
        });

        console.log(
          `[StreamingUIHandler] New cell created with ID: ${newCellId} (recorded for rollback)`
        );
      } catch (error) {
        console.error('Error creating new cell during streaming:', error);
      }
    } else {
      // Subsequent deltas: edit the cell
      try {
        this.toolService.notebookTools?.edit_cell({
          cell_id: toolCallInfo.cellId,
          summary: cellSummary,
          new_source: code,
          is_tracking_id: true,
          notebook_path: this.notebookId
        });
      } catch (error) {
        console.error('Error editing existing cell during streaming:', error);
      }
    }
  }

  /**
   * Handle edit cell streaming
   */
  private handleEditCellStreaming(
    toolCallInfo: ToolCallInfo,
    code: string,
    toolId: string
  ): void {
    if (!this.toolService) {
      return;
    }

    if (!toolCallInfo.cellId) {
      const cellIdRegex = /"cell_id"\s*:\s*"([^"]*)"/;
      const cellIdMatch = toolCallInfo.accumulatedInput.match(cellIdRegex);
      if (cellIdMatch && cellIdMatch[1]) {
        toolCallInfo.cellId = cellIdMatch[1];

        // Get the original content for diff tracking and rollback
        try {
          const cellInfo = this.toolService.notebookTools?.findCellByAnyId(
            toolCallInfo.cellId,
            this.notebookId
          );
          if (cellInfo) {
            toolCallInfo.originalContent =
              cellInfo.cell.model.sharedModel.getSource() || '';
            toolCallInfo.originalSummary =
              (cellInfo.cell.model.sharedModel.metadata?.custom as any)
                ?.summary || '';

            // Record this edit for potential rollback (only once per cell)
            const alreadyRecorded = this.streamingSnapshots.some(
              s =>
                s.type === 'edit' &&
                (s as IEditedCellSnapshot).cellId === toolCallInfo.cellId
            );
            if (!alreadyRecorded) {
              this.streamingSnapshots.push({
                type: 'edit',
                cellId: toolCallInfo.cellId,
                originalContent: toolCallInfo.originalContent || '',
                originalSummary: toolCallInfo.originalSummary || '',
                toolId: toolId
              });
              console.log(
                `[StreamingUIHandler] Edit cell ${toolCallInfo.cellId} original state recorded for rollback`
              );
            }
          }
        } catch (error) {
          console.warn('Could not get original content for diff:', error);
        }
      }
    }

    if (!toolCallInfo.cellId) {
      return;
    }

    // Handle diff calculation for partial streaming
    let finalContent = code;
    if (toolCallInfo.originalContent) {
      if (code.length < toolCallInfo.originalContent.length) {
        finalContent =
          code + toolCallInfo.originalContent.substring(code.length);
      } else {
        finalContent = code;
      }
    }

    const result = this.toolService.notebookTools?.edit_cell({
      cell_id: toolCallInfo.cellId,
      new_source: finalContent,
      summary: toolCallInfo.summary || 'Cell being updated by AI...',
      is_tracking_id: toolCallInfo.cellId.startsWith('cell_'),
      notebook_path: this.notebookId
    });

    toolCallInfo.toolResult = {
      type: 'tool_result',
      tool_use_id: toolId,
      content: result ? 'true' : 'false'
    };
  }

  /**
   * Finalize tool in notebook after streaming completes
   */
  private finalizeToolInNotebook(toolCallInfo: ToolCallInfo, input: any): void {
    if (!this.toolService) {
      return;
    }

    if (toolCallInfo.name === 'notebook-edit_cell') {
      this.toolService.notebookTools?.edit_cell({
        cell_id: input.cell_id,
        new_source: input.new_source || '',
        summary: input.summary || '',
        is_tracking_id: true,
        notebook_path: this.notebookId
      });

      this.diffManager?.trackEditCell(
        input.cell_id,
        toolCallInfo.originalContent || '',
        input.new_source,
        input.summary,
        this.notebookId
      );
    }

    if (toolCallInfo.name === 'notebook-add_cell') {
      this.toolService.notebookTools?.edit_cell({
        cell_id: toolCallInfo.cellId!,
        new_source: input.source || '',
        summary: input.summary || '',
        is_tracking_id: true,
        notebook_path: this.notebookId
      });

      this.diffManager?.trackAddCell(
        toolCallInfo.cellId!,
        input.source,
        input.summary,
        this.notebookId
      );
    }
  }

  /**
   * Hide thinking indicator if active
   */
  private hideThinking(): void {
    if (this.state.isThinkingActive) {
      this.messageComponent.removeThinkingIndicator();
      useChatMessagesStore.getState().hideThinking();
      this.state.isThinkingActive = false;
    }
  }

  /**
   * Finalize all streaming operations
   */
  private finalizeStreaming(): void {
    this.finalizeStreamingMessage();
    this.finalizeStreamingToolCalls();
  }

  /**
   * Finalize streaming message
   * Uses messageComponent.finalizeStreamingMessage() to ensure the message
   * is added to LLM history and persisted to storage
   */
  private finalizeStreamingMessage(): void {
    if (this.state.isStreamingMessage) {
      // Use the service method which adds to LLM history and persists
      void this.messageComponent.finalizeStreamingMessage();
      this.state.isStreamingMessage = false;
      this.state.streamingMessageId = null;
    }
  }

  /**
   * Finalize all streaming tool calls
   */
  private finalizeStreamingToolCalls(): void {
    for (const toolId of this.state.activeToolCallIds) {
      useChatMessagesStore.getState().finalizeStreamingToolCall(toolId);
    }
    this.state.activeToolCallIds.clear();
    useChatMessagesStore.getState().clearAllStreamingToolCalls();
  }

  /**
   * Rollback all streaming changes to the notebook
   * This reverses any add_cell, edit_cell, and edit_plan operations
   * that occurred during streaming.
   */
  private rollbackStreamingChanges(): void {
    console.log(
      `[StreamingUIHandler] rollbackStreamingChanges called - toolService: ${!!this.toolService}, notebookTools: ${!!this.toolService?.notebookTools}, snapshots: ${this.streamingSnapshots.length}`
    );

    if (!this.toolService?.notebookTools) {
      console.log(
        '[StreamingUIHandler] No toolService or notebookTools, cannot rollback'
      );
      return;
    }

    if (this.streamingSnapshots.length === 0) {
      console.log('[StreamingUIHandler] No streaming snapshots to rollback');
      return;
    }

    console.log(
      `[StreamingUIHandler] Rolling back ${this.streamingSnapshots.length} streaming changes`
    );

    // Process snapshots in reverse order (LIFO) to properly undo nested changes
    const snapshotsToProcess = [...this.streamingSnapshots].reverse();

    for (const snapshot of snapshotsToProcess) {
      try {
        switch (snapshot.type) {
          case 'add': {
            // Delete cells that were added during streaming
            const addSnapshot = snapshot as IAddedCellSnapshot;
            console.log(
              `[StreamingUIHandler] Rollback: Removing added cell ${addSnapshot.cellId}`
            );
            this.toolService.notebookTools.remove_cells({
              cell_ids: [addSnapshot.cellId],
              notebook_path: this.notebookId,
              remove_from_notebook: true,
              save_checkpoint: false // Don't save checkpoint for rollback
            });
            break;
          }

          case 'edit': {
            // Restore original content for edited cells
            const editSnapshot = snapshot as IEditedCellSnapshot;
            console.log(
              `[StreamingUIHandler] Rollback: Restoring cell ${editSnapshot.cellId} to original content (length: ${editSnapshot.originalContent.length})`
            );

            // Find the cell first to ensure it exists
            const cellInfo = this.toolService.notebookTools.findCellByAnyId(
              editSnapshot.cellId,
              this.notebookId
            );

            if (cellInfo) {
              // Directly set the source on the cell to ensure rollback works
              cellInfo.cell.model.sharedModel.setSource(
                editSnapshot.originalContent
              );

              // Also update metadata summary if we have it
              if (editSnapshot.originalSummary) {
                const metadata: any =
                  cellInfo.cell.model.sharedModel.getMetadata() || {};
                if (metadata.custom) {
                  metadata.custom.summary = editSnapshot.originalSummary;
                }
                if (metadata.cell_tracker) {
                  metadata.cell_tracker.summary = editSnapshot.originalSummary;
                }
                cellInfo.cell.model.sharedModel.setMetadata(metadata);
              }

              console.log(
                `[StreamingUIHandler] Rollback: Successfully restored cell ${editSnapshot.cellId}`
              );
            } else {
              console.warn(
                `[StreamingUIHandler] Rollback: Could not find cell ${editSnapshot.cellId} for restoration`
              );
            }
            break;
          }

          case 'plan': {
            // Restore original plan content
            const planSnapshot = snapshot as IPlanSnapshot;
            console.log(
              `[StreamingUIHandler] Rollback: Restoring plan cell (existed: ${planSnapshot.existed}, originalContent length: ${planSnapshot.originalContent.length}, cellCountBefore: ${planSnapshot.cellCountBefore})`
            );

            const current = this.toolService.notebookTools.getCurrentNotebook(
              this.notebookId
            );
            if (!current) {
              console.warn(
                '[StreamingUIHandler] Rollback: No notebook found for plan rollback'
              );
              break;
            }

            const { notebook } = current;
            const currentCellCount = notebook.widgets.length;

            // Find the plan cell by its metadata
            let planCellIndex = -1;
            for (let i = 0; i < notebook.widgets.length; i++) {
              const cell = notebook.widgets[i];
              const metadata: any =
                cell?.model?.sharedModel?.getMetadata() || {};
              if (metadata.custom?.sage_cell_type === 'plan') {
                planCellIndex = i;
                break;
              }
            }

            if (planSnapshot.existed) {
              // Plan existed before, restore its original content
              if (planCellIndex !== -1) {
                const planCell = notebook.widgets[planCellIndex];
                planCell.model.sharedModel.setSource(
                  planSnapshot.originalContent
                );
                console.log(
                  `[StreamingUIHandler] Rollback: Restored plan cell content to original (${planSnapshot.originalContent.length} chars)`
                );
              } else {
                console.warn(
                  '[StreamingUIHandler] Rollback: Plan existed but cell not found'
                );
              }
            } else {
              // Plan didn't exist before streaming
              // Check if a cell was added (cell count increased)
              const cellWasAdded =
                currentCellCount > planSnapshot.cellCountBefore;

              if (planCellIndex !== -1) {
                // Plan cell found by metadata, delete it
                notebook.activeCellIndex = planCellIndex;
                NotebookActions.deleteCells(notebook);
                console.log(
                  `[StreamingUIHandler] Rollback: Deleted plan cell at index ${planCellIndex} (found by metadata)`
                );
              } else if (cellWasAdded && notebook.widgets.length > 0) {
                // Plan cell not found by metadata, but a cell was added
                // Check if the first cell looks like a plan cell (position 0, markdown type)
                const firstCell = notebook.widgets[0];
                const firstCellType = firstCell?.model?.type;
                if (firstCellType === 'markdown') {
                  notebook.activeCellIndex = 0;
                  NotebookActions.deleteCells(notebook);
                  console.log(
                    `[StreamingUIHandler] Rollback: Deleted first markdown cell (likely the new plan cell)`
                  );
                } else {
                  console.log(
                    `[StreamingUIHandler] Rollback: Cell was added but first cell is not markdown, skipping deletion`
                  );
                }
              } else {
                console.log(
                  '[StreamingUIHandler] Rollback: No plan cell to delete'
                );
              }
            }
            break;
          }
        }
      } catch (error) {
        console.error(
          `[StreamingUIHandler] Error during rollback of ${snapshot.type}:`,
          error
        );
        // Continue with other rollbacks even if one fails
      }
    }

    // Clear snapshots after rollback
    this.streamingSnapshots = [];
    console.log('[StreamingUIHandler] Streaming rollback complete');
  }

  /**
   * Remove streaming content (for cancellation)
   */
  private removeStreaming(): void {
    // Cancel streaming message
    if (this.state.isStreamingMessage) {
      useChatMessagesStore.getState().cancelStreaming();
      this.state.isStreamingMessage = false;
      this.state.streamingMessageId = null;
    }

    // Cancel streaming tool calls
    for (const toolId of this.state.activeToolCallIds) {
      useChatMessagesStore.getState().cancelStreamingToolCall(toolId);
    }
    this.state.activeToolCallIds.clear();
  }
}
