/**
 * ToolExecutionHandler - Handles tool execution during LLM loop
 *
 * This encapsulates all tool execution logic, including:
 * - Sequential vs parallel execution
 * - Tool approval workflows
 * - Tool result handling
 * - Code execution confirmation
 * - Terminal command approval
 */

import { ToolService } from '../ToolService';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ActionHistory, ActionType } from '@/ChatBox/services/ActionHistory';
import { CodeConfirmationDialog } from '../../Components/CodeConfirmationDialog';
import { useChatMessagesStore } from '../../stores/chatMessages';
import { useLLMStateStore } from '../../stores/llmStateStore';
import { useDiffStore } from '../../stores/diffStore';
import { useWaitingReplyStore } from '../../stores/waitingReplyStore';
import { ILLMContext, IToolCall, IToolProcessResult } from '../LLMTypes';
import { useAppStore } from '../../stores/appStore';
import { useServicesStore } from '../../stores/servicesStore';
import { StreamingUIHandler, ToolCallInfo } from './StreamingUIHandler';
import { DiffApprovalHandler } from './DiffApprovalHandler';
import { isMCPTool } from '../../utils/toolDisplay';

// ═══════════════════════════════════════════════════════════════
// CONSTANTS
// ═══════════════════════════════════════════════════════════════

/**
 * Tools that can be executed in parallel
 * Note: notebook-run_cell and notebook-execute_cell are NOT parallelizable
 * because they interact with diff approval flow and must execute sequentially
 */
const PARALLELIZABLE_TOOLS = new Set([
  'terminal-execute_command',
  'database-read_databases',
  'database-schema_search',
  'database-search_tables',
  'web-search_dataset',
  'filesystem-read_dataset',
  'notebook-read_cells'
]);

/**
 * Tools that require approval before execution
 */
const APPROVAL_REQUIRED_TOOLS = new Set([
  'notebook-run_cell',
  'notebook-execute_cell',
  'terminal-execute_command'
]);

/**
 * Tools that stop the LLM loop when executed
 */
const LOOP_STOPPING_TOOLS = new Set(['notebook-wait_user_reply']);

// ═══════════════════════════════════════════════════════════════
// MAIN CLASS
// ═══════════════════════════════════════════════════════════════

/**
 * Handler for tool execution during the LLM loop
 */
export class ToolExecutionHandler {
  private toolService: ToolService;
  private actionHistory: ActionHistory;
  private messageComponent: ChatMessages;
  private codeConfirmationDialog: CodeConfirmationDialog;
  private streamingHandler: StreamingUIHandler | null = null;
  private diffHandler: DiffApprovalHandler | null = null;
  private notebookId: string | null = null;

  constructor(
    toolService: ToolService,
    actionHistory: ActionHistory,
    messageComponent?: ChatMessages,
    codeConfirmationDialog?: CodeConfirmationDialog
  ) {
    this.toolService = toolService;
    this.actionHistory = actionHistory;
    this.messageComponent = messageComponent!;
    this.codeConfirmationDialog = codeConfirmationDialog!;
  }

  /**
   * Set the streaming handler for accessing streaming tool call info
   */
  setStreamingHandler(handler: StreamingUIHandler): void {
    this.streamingHandler = handler;
  }

  /**
   * Set the diff handler
   */
  setDiffHandler(handler: DiffApprovalHandler): void {
    this.diffHandler = handler;
  }

  /**
   * Set the message component
   */
  setMessageComponent(component: ChatMessages): void {
    this.messageComponent = component;
  }

  /**
   * Set the code confirmation dialog
   */
  setCodeConfirmationDialog(dialog: CodeConfirmationDialog): void {
    this.codeConfirmationDialog = dialog;
  }

  /**
   * Set the notebook ID
   */
  setNotebookId(notebookId: string | null): void {
    this.notebookId = notebookId;
  }

  // ═══════════════════════════════════════════════════════════════
  // MAIN ENTRY POINT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Process all tool calls from an API response
   */
  async processToolCalls(
    response: any,
    context: ILLMContext,
    messageComponent: ChatMessages
  ): Promise<IToolProcessResult> {
    const toolCalls = this.extractToolCalls(response);

    if (toolCalls.length === 0) {
      return {
        shouldContinue: true,
        hasToolCalls: false,
        toolResults: []
      };
    }

    console.log(
      `[ToolExecutionHandler] Processing ${toolCalls.length} tool calls`
    );

    const toolResults: any[] = [];
    let shouldContinue = true;

    // Process tools - batch parallelizable ones, execute others sequentially
    let i = 0;
    while (i < toolCalls.length && shouldContinue) {
      const tool = toolCalls[i];

      // Check if this tool allows parallelization (including MCP tools)
      if (this.allowsParallelization(tool.name) || isMCPTool(tool.name)) {
        // Collect consecutive parallelizable tools
        const batch: IToolCall[] = [];
        while (
          i < toolCalls.length &&
          (this.allowsParallelization(toolCalls[i].name) ||
            isMCPTool(toolCalls[i].name))
        ) {
          batch.push(toolCalls[i]);
          i++;
        }

        // Execute batch concurrently
        const batchResults = await this.executeConcurrentTools(
          batch,
          context,
          messageComponent
        );
        toolResults.push(...batchResults.results);
        shouldContinue = batchResults.shouldContinue;
      } else {
        // Execute single tool
        const result = await this.executeSingleTool(
          tool,
          context,
          messageComponent
        );
        toolResults.push(result.result);
        shouldContinue = result.shouldContinue;
        i++;
      }
    }

    return {
      shouldContinue,
      hasToolCalls: true,
      toolResults
    };
  }

  // ═══════════════════════════════════════════════════════════════
  // TOOL EXTRACTION
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if a tool allows parallelization
   */
  allowsParallelization(toolName: string): boolean {
    return PARALLELIZABLE_TOOLS.has(toolName);
  }

  // ═══════════════════════════════════════════════════════════════
  // SEQUENTIAL EXECUTION
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if a tool requires approval
   */
  requiresApproval(toolName: string): boolean {
    return APPROVAL_REQUIRED_TOOLS.has(toolName);
  }

  /**
   * Check if a tool stops the LLM loop
   */
  isLoopStoppingTool(toolName: string): boolean {
    return LOOP_STOPPING_TOOLS.has(toolName);
  }

  /**
   * Check if response has any tool calls
   */
  hasToolCalls(response: any): boolean {
    if (!response?.content) return false;
    return response.content.some(
      (c: any) => c.type === 'tool_use' || c.type === 'server_tool_use'
    );
  }

  /**
   * Extract tool calls from API response
   * Includes only 'tool_use'
   * Type 'server_tool_use' is ignored
   * Server tools are added to history but NOT executed locally (they're executed by the API).
   */
  private extractToolCalls(response: any): IToolCall[] {
    if (!response?.content) return [];

    return response.content
      .filter((c: any) => c.type === 'tool_use')
      .map((c: any) => ({
        id: c.id,
        name: c.name,
        input: c.input,
        type: c.type // Preserve the type so we can check for server_tool_use
      }));
  }

  /**
   * Check if a tool call is a server-side tool (executed by API, not locally)
   */
  private isServerToolUse(tool: IToolCall): boolean {
    return (tool as any).type === 'server_tool_use';
  }

  /**
   * Execute a single tool
   */
  private async executeSingleTool(
    tool: IToolCall,
    context: ILLMContext,
    messageComponent: ChatMessages
  ): Promise<{ result: any; shouldContinue: boolean }> {
    console.log(`[ToolExecutionHandler] Executing tool: ${tool.name}`);

    // Check if this is a server_tool_use (executed by API, not locally)
    // Server tools are already added to llmHistory in StreamingUIHandler.onToolSearchResult
    // so we just skip them entirely here - no execution, no history addition
    if (this.isServerToolUse(tool)) {
      console.log(
        `[ToolExecutionHandler] Server tool use - skipping (handled during streaming): ${tool.name}`,
        tool.id
      );
      return { result: null, shouldContinue: true };
    }

    // Check if tool stops the loop
    if (this.isLoopStoppingTool(tool.name)) {
      // Add tool_use to LLM history BEFORE executing (same as regular tools)
      console.log(
        `[ToolExecutionHandler] Adding loop-stopping tool to history: ${tool.name}`,
        tool.id
      );
      this.messageComponent?.addToolCalls([
        {
          id: tool.id,
          name: tool.name,
          input: tool.input
        }
      ]);
      const result = await this.executeLoopStoppingTool(tool, messageComponent);
      return { result, shouldContinue: false };
    }

    // Get streaming tool call info if available
    const streamingToolCallInfo = this.streamingHandler?.getStreamingToolCall(
      tool.id
    );

    // Merge dynamically assigned cell_id from streaming (for add_cell operations)
    const mergedInput = {
      ...tool.input,
      ...(streamingToolCallInfo?.cellId
        ? { cell_id: streamingToolCallInfo.cellId }
        : {})
    };

    // Add tool_use to LLM history BEFORE processing
    this.messageComponent?.addToolCalls([
      {
        id: tool.id,
        name: tool.name,
        input: mergedInput
      }
    ]);

    // Handle code execution approval
    if (
      tool.name === 'notebook-run_cell' ||
      tool.name === 'notebook-execute_cell'
    ) {
      const shouldContinue = await this.handleCodeExecutionApproval(
        tool,
        context
      );
      if (!shouldContinue) {
        // Remove streaming tool call
        this.streamingHandler?.removeStreamingToolCall(tool.id);
        return { result: null, shouldContinue: false };
      }
    }

    // Handle terminal command approval
    if (tool.name === 'terminal-execute_command') {
      const shouldContinue = await this.handleTerminalCommandApproval(tool);
      if (!shouldContinue) {
        this.streamingHandler?.removeStreamingToolCall(tool.id);
        return { result: null, shouldContinue: false };
      }
    }

    // Show tool state in LLM display
    const llmStateStore = useLLMStateStore.getState();
    if (!llmStateStore.isDiffState()) {
      llmStateStore.showTool(tool.name);
    }

    // Capture action state before execution for undo functionality
    const actionBeforeExecution = await this.captureActionState(
      tool,
      streamingToolCallInfo
    );

    // Execute the tool
    try {
      // Check if tool was already executed during streaming
      const isStreamToolCall = streamingToolCallInfo?.toolResult;

      let result: any;
      if (isStreamToolCall) {
        result = streamingToolCallInfo!.toolResult;
      } else {
        // For run_cell, check if already executed during diff approval
        if (tool.name === 'notebook-run_cell') {
          const executedApprovedCells = await this.checkExecutedCells(
            tool.id,
            tool.input?.cell_id
          );
          if (executedApprovedCells) {
            console.log(
              '[ToolExecutionHandler] Skipping tool call - already executed'
            );
            this.streamingHandler?.removeStreamingToolCall(tool.id);
            return { result: null, shouldContinue: true };
          }
        }

        // For remove_cells, create pending diffs instead of directly removing
        // The actual removal happens when user approves the diffs
        if (
          tool.name === 'notebook-remove_cells' &&
          actionBeforeExecution?.removedCells
        ) {
          const diffManager = useServicesStore.getState().notebookDiffManager;
          if (diffManager) {
            // Use the handler's notebookId (set via setNotebookId) or fallback to tool input
            const notebookId = this.notebookId || tool.input?.notebook_path;
            for (const cell of actionBeforeExecution.removedCells) {
              if (cell && (cell.id || cell.trackingId)) {
                const cellId = cell.trackingId || cell.id;
                const content = cell.content || cell.source || '';
                const summary =
                  cell.custom?.summary ||
                  cell.metadata?.custom?.summary ||
                  'Remove cell';

                console.log(
                  `[ToolExecutionHandler] Creating remove diff for cell: ${cellId}, notebookId: ${notebookId}`
                );
                diffManager.trackRemoveCell(
                  cellId,
                  content,
                  summary,
                  notebookId
                );
              }
            }

            // Return success without actually removing cells
            // The diff approval flow will handle the actual removal
            result = { content: 'true' };
            console.log(
              '[ToolExecutionHandler] Created remove diffs, skipping direct removal'
            );
          } else {
            // Fallback: execute directly if no diff manager
            result = await this.toolService.executeTool(tool);
          }
        } else {
          result = await this.toolService.executeTool(tool);
        }
      }

      // Record action for undo capability
      this.trackActionForUndo(tool, result, actionBeforeExecution);

      // Show tool result
      if (result) {
        this.messageComponent?.addToolResult(
          tool.name,
          tool.id,
          result.content || JSON.stringify(result),
          tool.input
        );

        // Update toolSearchResult for MCP tools so the UI can show input/output
        if (isMCPTool(tool.name)) {
          useChatMessagesStore
            .getState()
            .updateToolSearchResult(
              tool.id,
              tool.input,
              result.content || result
            );
        }
      }

      // Remove streaming tool call after processing
      this.streamingHandler?.removeStreamingToolCall(tool.id);

      // Update LLM state
      if (!llmStateStore.isDiffState()) {
        llmStateStore.show('Generating...');
      }

      // Special handling for open_notebook: stop the loop and let the notebook loading
      // trigger continuation. The thread has been copied to the new notebook and will
      // be loaded when the notebook opens, at which point the conversation can continue.
      if (tool.name === 'open_notebook') {
        console.log(
          '[ToolExecutionHandler] open_notebook executed - stopping loop for notebook switch'
        );
        return { result, shouldContinue: false };
      }

      return { result, shouldContinue: true };
    } catch (error) {
      console.error(
        `[ToolExecutionHandler] Error executing ${tool.name}:`,
        error
      );
      const errorResult = {
        error: error instanceof Error ? error.message : 'Unknown error',
        success: false
      };
      this.addToolResultToHistory(tool, errorResult, true);
      this.streamingHandler?.removeStreamingToolCall(tool.id);
      return { result: errorResult, shouldContinue: true };
    }
  }

  /**
   * Handle code execution approval
   */
  private async handleCodeExecutionApproval(
    tool: IToolCall,
    context: ILLMContext
  ): Promise<boolean> {
    // Check for pending diffs before code execution
    if (this.diffHandler) {
      await this.diffHandler.handlePendingDiffs(this.notebookId, true);
    }

    const diffManager = useServicesStore.getState().notebookDiffManager;

    // Check if diffs were rejected
    if (diffManager?.hasRejectedDiffs()) {
      this.messageComponent?.addSystemMessage(
        '❌ Changes were rejected. Code execution has been cancelled.'
      );

      if (tool.input?.cell_id) {
        this.messageComponent?.addToolResult(
          'notebook-run_cell',
          tool.id,
          'User rejected changes, cell was not added or executed.',
          {
            cell_id: tool.input?.cell_id,
            notebook_path: this.notebookId
          }
        );
      }

      useDiffStore.getState().clearDiffs(null);
      return false;
    }

    // Check if user has made approval decisions that should stop the LLM loop
    if (this.diffHandler?.checkForApprovalDecisions()) {
      console.log(
        '[ToolExecutionHandler] User made approval decisions - stopping LLM loop'
      );

      this.messageComponent?.addToolResult(
        'notebook-run_cell',
        tool.id,
        'user accepted changes but did not run the cell.',
        { cell_id: tool.input?.cell_id, notebook_path: this.notebookId }
      );

      return false;
    }

    // Handle code execution confirmation
    let shouldRun = false;

    if (useAppStore.getState().autoRun) {
      shouldRun = true;
      this.messageComponent?.addSystemMessage(
        'Automatically running code (auto-run is enabled).'
      );
    } else if (diffManager && diffManager.shouldRunImmediately()) {
      shouldRun = true;
      this.messageComponent?.addSystemMessage(
        'Running code immediately after approving changes.'
      );
    } else {
      // Show confirmation dialog
      const llmState = useLLMStateStore.getState();
      if (this.codeConfirmationDialog) {
        llmState.showRunCellTool(
          () => this.codeConfirmationDialog.triggerApproval(),
          () => this.codeConfirmationDialog.triggerRejection()
        );
      }

      if (this.codeConfirmationDialog) {
        shouldRun = await this.codeConfirmationDialog.showConfirmation(
          tool.input.cell_id || tool.input.cellId || ''
        );
      }

      if (shouldRun) {
        llmState.show();
      } else {
        llmState.hide();
        this.messageComponent?.removeLoadingText();
      }
    }

    return shouldRun;
  }

  // ═══════════════════════════════════════════════════════════════
  // CONCURRENT EXECUTION
  // ═══════════════════════════════════════════════════════════════

  /**
   * Handle terminal command approval
   */
  private async handleTerminalCommandApproval(
    tool: IToolCall
  ): Promise<boolean> {
    const command = tool.input?.command || '';

    // If autorun is enabled, execute immediately
    if (useAppStore.getState().autoRun) {
      this.messageComponent?.addSystemMessage(
        `Automatically executing terminal command (auto-run is enabled): ${command}`
      );
      return true;
    }

    // Show confirmation dialog for terminal command
    const llmState = useLLMStateStore.getState();
    if (this.codeConfirmationDialog) {
      llmState.showRunTerminalCommandTool(
        () => this.codeConfirmationDialog.triggerApproval(),
        () => this.codeConfirmationDialog.triggerRejection()
      );
    }

    let shouldRun = false;
    if (this.codeConfirmationDialog) {
      shouldRun = await this.codeConfirmationDialog.showConfirmation(command);
    }

    if (shouldRun) {
      llmState.show();
    } else {
      llmState.hide();
      this.messageComponent?.removeLoadingText();
    }

    return shouldRun;
  }

  // ═══════════════════════════════════════════════════════════════
  // SPECIAL TOOL HANDLERS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if cells were executed during diff approval
   */
  private async checkExecutedCells(
    toolId: string,
    cellId?: string
  ): Promise<boolean> {
    const diffManager = useServicesStore.getState().notebookDiffManager;
    if (!diffManager) {
      return false;
    }

    const pendingDiffs = useDiffStore.getState().pendingDiffs;
    for (const diff of pendingDiffs.values()) {
      if (
        diff.cellId === cellId &&
        diff.userDecision === 'run' &&
        diff.runResult
      ) {
        // Cell was already executed during diff approval
        this.messageComponent?.addToolResult(
          'notebook-run_cell',
          toolId,
          JSON.stringify(diff.runResult),
          { cell_id: cellId, notebook_path: this.notebookId }
        );
        return true;
      }
    }

    return false;
  }

  /**
   * Capture action state before execution for undo functionality
   */
  private async captureActionState(
    tool: IToolCall,
    streamingToolCallInfo?: ToolCallInfo
  ): Promise<any> {
    if (tool.name === 'notebook-edit_cell') {
      try {
        const cellInfo = await this.toolService.executeTool({
          id: 'get_cell_before_edit',
          name: 'notebook-get_cell_info',
          input: { cell_id: tool.input.cell_id }
        });

        if (cellInfo && cellInfo.content) {
          const cellData = JSON.parse(cellInfo.content);
          return {
            originalCell: cellData,
            originalContent: streamingToolCallInfo?.originalContent || '',
            originalSummary: streamingToolCallInfo?.originalSummary || '',
            newSource: tool.input.new_source,
            cellId: tool.input.cell_id,
            cell_id: tool.input.cell_id,
            summary: tool.input.summary
          };
        }
      } catch (err) {
        console.error('Failed to get cell info before edit:', err);
      }
    } else if (tool.name === 'notebook-remove_cells') {
      try {
        const cellsToRemove = tool.input.cell_ids || [];
        const cellInfoPromises = cellsToRemove.map((cellId: string) =>
          this.toolService.executeTool({
            id: `get_cell_before_remove_${cellId}`,
            name: 'notebook-get_cell_info',
            input: { cell_id: cellId }
          })
        );

        const cellInfoResults = await Promise.all(cellInfoPromises);
        const removedCells = cellInfoResults
          .map(result =>
            result && result.content ? JSON.parse(result.content) : null
          )
          .filter(cell => cell !== null);

        if (removedCells.length > 0) {
          return { removedCells };
        }
      } catch (err) {
        console.error('Failed to get cell info before removal:', err);
      }
    }

    return null;
  }

  // ═══════════════════════════════════════════════════════════════
  // HISTORY MANAGEMENT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Track action for undo functionality
   */
  private trackActionForUndo(
    tool: IToolCall,
    result: any,
    actionBeforeExecution: any
  ): void {
    // Map tool names to action types
    let actionType: ActionType | null = null;
    let actionData: any = {
      toolId: tool.id,
      toolName: tool.name,
      input: tool.input,
      result
    };

    switch (tool.name) {
      case 'notebook-add_cell':
        actionType = ActionType.ADD_CELL;
        // Get the streaming tool call info for the cell ID
        const streamingInfo = this.streamingHandler?.getStreamingToolCall(
          tool.id
        );
        actionData = {
          ...actionData,
          trackingId: streamingInfo?.cellId || result?.content,
          cellId: streamingInfo?.cellId || result?.content,
          newContent: tool.input.source,
          originalCellType: tool.input.cell_type,
          summary: tool.input.summary
        };
        break;
      case 'notebook-edit_cell':
        actionType = ActionType.EDIT_CELL;
        if (actionBeforeExecution) {
          actionData = {
            ...actionData,
            trackingId: tool.input.cell_id,
            cellId: tool.input.cell_id,
            originalContent: actionBeforeExecution.originalContent,
            originalSummary: actionBeforeExecution.originalSummary,
            newContent: tool.input.new_source,
            summary: tool.input.summary
          };
        }
        break;
      case 'notebook-remove_cells':
        actionType = ActionType.REMOVE_CELLS;
        if (actionBeforeExecution?.removedCells) {
          actionData = {
            ...actionData,
            removedCells: actionBeforeExecution.removedCells
          };
        }
        break;
      case 'notebook-edit_plan':
        actionType = ActionType.EDIT_PLAN;
        break;
    }

    if (actionType) {
      this.actionHistory.addActionWithCheckpoint(
        actionType,
        actionData,
        `${tool.name}: ${this.getToolDescription(tool)}`
      );
    }
  }

  /**
   * Execute multiple tools concurrently
   */
  private async executeConcurrentTools(
    tools: IToolCall[],
    context: ILLMContext,
    messageComponent: ChatMessages
  ): Promise<{ results: any[]; shouldContinue: boolean }> {
    console.log(
      `[ToolExecutionHandler] Executing ${tools.length} tools concurrently`
    );

    // Step 1: Show all dialogs concurrently and collect approval results
    const approvalPromises = tools.map(async tool => {
      const toolName = tool.name;

      // Handle code execution approval
      if (
        toolName === 'notebook-run_cell' ||
        toolName === 'notebook-execute_cell'
      ) {
        const shouldContinue = await this.handleCodeExecutionApproval(
          tool,
          context
        );
        return { tool, approved: shouldContinue, shouldContinue };
      }

      // Handle terminal command approval
      if (toolName === 'terminal-execute_command') {
        const shouldContinue = await this.handleTerminalCommandApproval(tool);
        return { tool, approved: shouldContinue, shouldContinue };
      }

      return { tool, approved: true, shouldContinue: true };
    });

    const approvalResults = await Promise.all(approvalPromises);

    // Check if any tool was rejected and should stop processing
    for (const result of approvalResults) {
      if (!result.shouldContinue) {
        // Clean up ALL streaming tool calls when any is rejected
        for (const tool of tools) {
          this.streamingHandler?.removeStreamingToolCall(tool.id);
        }

        // Hide LLM state display and stop the flow
        const llmState = useLLMStateStore.getState();
        if (!llmState.isDiffState()) {
          llmState.hide();
        }

        return { results: [], shouldContinue: false };
      }
    }

    // Step 2: Execute all approved tools concurrently
    const executionPromises = approvalResults
      .filter(result => result.approved)
      .map(async ({ tool }) => {
        // Get streaming tool call info if available
        const streamingToolCallInfo =
          this.streamingHandler?.getStreamingToolCall(tool.id);

        // Merge dynamically assigned cell_id from streaming
        const mergedInput = {
          ...tool.input,
          ...(streamingToolCallInfo?.cellId
            ? { cell_id: streamingToolCallInfo.cellId }
            : {})
        };

        // Check if this is a server_tool_use - skip entirely (handled during streaming)
        if (this.isServerToolUse(tool)) {
          console.log(
            `[ToolExecutionHandler] Server tool use in batch - skipping (handled during streaming): ${tool.name}`
          );
          return { tool, result: null, success: true };
        }

        // Add tool_use to LLM history BEFORE processing
        this.messageComponent?.addToolCalls([
          {
            id: tool.id,
            name: tool.name,
            input: mergedInput
          }
        ]);

        // Capture action state before execution
        const actionBeforeExecution = await this.captureActionState(
          tool,
          streamingToolCallInfo
        );

        // Show tool state in LLM display
        const llmStateForTool = useLLMStateStore.getState();
        if (!llmStateForTool.isDiffState()) {
          llmStateForTool.showTool(tool.name);
        }

        try {
          // Check if tool was already executed during streaming
          const isStreamToolCall = streamingToolCallInfo?.toolResult;

          let result: any;
          if (isStreamToolCall) {
            result = streamingToolCallInfo!.toolResult;
          } else {
            // For run_cell, check if already executed during diff approval
            if (tool.name === 'notebook-run_cell') {
              const executedApprovedCells = await this.checkExecutedCells(
                tool.id,
                tool.input?.cell_id
              );
              if (executedApprovedCells) {
                console.log(
                  '[ToolExecutionHandler] Skipping concurrent tool - already executed'
                );
                this.streamingHandler?.removeStreamingToolCall(tool.id);
                return { tool, result: null, success: true };
              }
            }

            // For remove_cells, create pending diffs instead of directly removing
            // The actual removal happens when user approves the diffs
            if (
              tool.name === 'notebook-remove_cells' &&
              actionBeforeExecution?.removedCells
            ) {
              const diffManager =
                useServicesStore.getState().notebookDiffManager;
              if (diffManager) {
                // Use the handler's notebookId (set via setNotebookId) or fallback to tool input
                const notebookId = this.notebookId || tool.input?.notebook_path;
                for (const cell of actionBeforeExecution.removedCells) {
                  if (cell && (cell.id || cell.trackingId)) {
                    const cellId = cell.trackingId || cell.id;
                    const content = cell.content || cell.source || '';
                    const summary =
                      cell.custom?.summary ||
                      cell.metadata?.custom?.summary ||
                      'Remove cell';

                    console.log(
                      `[ToolExecutionHandler] Creating remove diff for cell: ${cellId}, notebookId: ${notebookId}`
                    );
                    diffManager.trackRemoveCell(
                      cellId,
                      content,
                      summary,
                      notebookId
                    );
                  }
                }

                // Return success without actually removing cells
                result = { content: 'true' };
                console.log(
                  '[ToolExecutionHandler] Created remove diffs in batch, skipping direct removal'
                );
              } else {
                result = await this.toolService.executeTool(tool);
              }
            } else {
              result = await this.toolService.executeTool(tool);
            }
          }

          // Track action for undo functionality
          this.trackActionForUndo(tool, result, actionBeforeExecution);

          // Show tool result
          if (result) {
            this.messageComponent?.addToolResult(
              tool.name,
              tool.id,
              result.content || JSON.stringify(result),
              tool.input
            );

            // Update toolSearchResult for MCP tools so the UI can show input/output
            if (isMCPTool(tool.name)) {
              useChatMessagesStore
                .getState()
                .updateToolSearchResult(
                  tool.id,
                  tool.input,
                  result.content || result
                );
            }
          }

          // Remove streaming tool call after processing
          this.streamingHandler?.removeStreamingToolCall(tool.id);

          return { tool, result, success: true };
        } catch (error) {
          console.error(
            `[ToolExecutionHandler] Error executing ${tool.name}:`,
            error
          );
          const errorResult = {
            error: error instanceof Error ? error.message : 'Unknown error',
            success: false
          };
          this.addToolResultToHistory(tool, errorResult, true);
          this.streamingHandler?.removeStreamingToolCall(tool.id);
          return { tool, result: errorResult, success: false };
        }
      });

    const results = await Promise.all(executionPromises);

    // Update LLM state
    const llmStateAfterExec = useLLMStateStore.getState();
    if (!llmStateAfterExec.isDiffState()) {
      llmStateAfterExec.show('Generating...');
    }

    return {
      results: results.map(r => r.result),
      shouldContinue: true
    };
  }

  // ═══════════════════════════════════════════════════════════════
  // UTILITY METHODS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Execute a tool that stops the LLM loop
   */
  private async executeLoopStoppingTool(
    tool: IToolCall,
    messageComponent: ChatMessages
  ): Promise<any> {
    console.log(`[ToolExecutionHandler] Loop stopping tool: ${tool.name}`);

    if (tool.name === 'notebook-wait_user_reply') {
      return this.handleWaitUserReply(tool, messageComponent);
    }

    // Default execution for other loop-stopping tools
    const result = await this.toolService.executeTool(tool);
    this.addToolResultToHistory(tool, result);
    return result;
  }

  /**
   * Handle the wait_user_reply tool
   */
  private async handleWaitUserReply(
    tool: IToolCall,
    _messageComponent: ChatMessages
  ): Promise<any> {
    // Support both field names: recommended_next_prompts (from LLM) and prompt_buttons (legacy)
    const promptButtons =
      tool.input?.recommended_next_prompts || tool.input?.prompt_buttons || [];
    const userMessage =
      tool.input?.message || 'What would you like to do next?';

    console.log(
      '[ToolExecutionHandler] handleWaitUserReply - tool.input:',
      tool.input
    );
    console.log(
      '[ToolExecutionHandler] handleWaitUserReply - promptButtons:',
      promptButtons
    );

    // Show the waiting for reply UI
    useWaitingReplyStore.getState().show(promptButtons);
    useLLMStateStore.getState().show('Waiting for your response...', true);

    // Add assistant message if provided via store
    // if (userMessage) {
    //   useChatMessagesStore.getState().addAssistantMessage(userMessage);
    // }

    // Return a result that indicates waiting
    const result = {
      status: 'waiting_for_user',
      message: 'Waiting for user input'
    };

    this.addToolResultToHistory(tool, result);
    return result;
  }

  /**
   * Add tool result to LLM history
   */
  private addToolResultToHistory(
    tool: IToolCall,
    result: any,
    isError: boolean = false
  ): void {
    const toolResultMessage = {
      role: 'user',
      content: [
        {
          type: 'tool_result',
          tool_use_id: tool.id,
          content: JSON.stringify(result),
          is_error: isError
        }
      ]
    };

    useChatMessagesStore.getState().addToLlmHistory(toolResultMessage);
  }

  /**
   * Get a human-readable description of a tool call
   */
  private getToolDescription(tool: IToolCall): string {
    switch (tool.name) {
      case 'notebook-add_cell':
        return `Added ${tool.input?.cell_type || 'code'} cell`;
      case 'notebook-edit_cell':
        return `Edited cell ${tool.input?.cell_id || 'unknown'}`;
      case 'notebook-remove_cells':
        return `Removed ${(tool.input?.cell_ids || []).length} cell(s)`;
      case 'notebook-edit_plan':
        return 'Updated plan';
      case 'notebook-run_cell':
        return `Ran cell ${tool.input?.cell_id || 'unknown'}`;
      default:
        return tool.name;
    }
  }
}
