import { NotebookActions } from '@jupyterlab/notebook';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ToolService } from './ToolService';
import { IChatService } from './IChatService';
import { ICheckpoint } from '../types';
import { NotebookStateService } from '../Notebook/NotebookStateService';
import { CodeConfirmationDialog } from '../Components/CodeConfirmationDialog';
import { RejectionFeedbackDialog } from '../Components/RejectionFeedbackDialog';
import {
  ActionHistory,
  ActionType,
  IActionHistoryEntry
} from '@/ChatBox/services/ActionHistory';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { Contents } from '@jupyterlab/services';
import { getNotebookContextManager } from '../stores/servicesStore';
import { useAppStore } from '../stores/appStore';
import { usePlanStateStore } from '../stores/planStateStore';
import { useLLMStateStore } from '../stores/llmStateStore';
import { useChatMessagesStore } from '../stores/chatMessages';
import {
  NotebookCellStateService,
  ICachedCellState
} from '../Services/NotebookCellStateService';
import { CheckpointManager } from '../Services/CheckpointManager';
import { ChatMode, ILLMLoopConfig, LLMLoop } from './index';
import { AnthropicService } from './Anthropic/AnthropicService';
import { useChatModeStore } from '../stores/chatModeStore';

export interface ILoadingIndicatorManager {
  updateLoadingIndicator(text?: string): void;

  /**
   * @deprecated
   */
  removeLoadingIndicator(): void;

  hideLoadingIndicator(): void;
}

/**
 * Service responsible for processing conversations with AI
 */
export class ConversationService {
  public chatService: IChatService;
  private toolService: ToolService;
  private messageComponent: ChatMessages;
  private notebookStateService: NotebookStateService;
  private codeConfirmationDialog: CodeConfirmationDialog;
  private loadingManager: ILoadingIndicatorManager;
  private chatHistory: HTMLDivElement;
  private actionHistory: ActionHistory;
  private diffManager: NotebookDiffManager | null = null;
  private isActiveToolExecution: boolean = false; // Track if we're in a tool execution phase
  private notebookId: string | null = null;
  private streamingElement: HTMLDivElement | null = null; // Element for streaming text
  private contentManager: Contents.IManager;

  // Update the property to handle multiple templates
  private templates: Array<{ name: string; content: string }> = [];

  // Store the notebook state before restoration so we can redo
  private preRestorationNotebookState: any = null;

  constructor(
    chatService: IChatService,
    toolService: ToolService,
    contentManager: Contents.IManager,
    messageComponent: ChatMessages,
    chatHistory: HTMLDivElement,
    actionHistory: ActionHistory,
    loadingManager: ILoadingIndicatorManager,
    diffManager?: NotebookDiffManager
  ) {
    this.chatService = chatService;
    this.toolService = toolService;
    this.messageComponent = messageComponent;
    this.chatHistory = chatHistory;
    this.loadingManager = loadingManager;
    this.diffManager = diffManager || null;
    this.actionHistory = actionHistory;
    this.contentManager = contentManager;

    // Initialize dependent services
    this.notebookStateService = new NotebookStateService(toolService);
    this.codeConfirmationDialog = new CodeConfirmationDialog(
      chatHistory,
      messageComponent
    );

    // Ensure chat service has the full conversation history
    this.syncChatServiceHistory();
  }

  public updateNotebookId(newId: string): void {
    this.notebookId = newId;
    this.notebookStateService.updateNotebookId(newId);
  }

  /**
   * Set the autorun flag
   * @param enabled Whether to automatically run code without confirmation
   */
  public setAutoRun(enabled: boolean): void {
    useAppStore.getState().setAutoRun(enabled);
  }

  /**
   * Set the current notebook ID
   * @param notebookId ID of the notebook to interact with
   */
  public setNotebookId(notebookId: string): void {
    this.notebookId = notebookId;
    console.log(`[ConversationService] Set notebook ID: ${notebookId}`);
  }

  /**
   * Handles the case when a cell execution is rejected
   */
  public async handleCellRejection(
    mode: 'agent' | 'ask' | 'fast' = 'agent'
  ): Promise<void> {
    this.messageComponent.addSystemMessage(
      'Cell execution rejected. Asking for corrections based on user feedback...'
    );

    const rejectionDialog = new RejectionFeedbackDialog();
    const rejectionReason = await rejectionDialog.showDialog();

    // Add the special user feedback message
    const rejectionMessage = {
      role: 'user',
      content: `I rejected the previous cell execution because: ${rejectionReason}`
    };

    // Add the feedback to the visible message history
    this.messageComponent.addUserMessage(
      `I rejected the previous cell execution because: ${rejectionReason}`
    );

    // Process conversation with just the new rejection message
    await this.processConversation([rejectionMessage], [], mode);
  }

  /**
   * Process conversation using the new LLMLoop system.
   * This is the main entry point for conversation processing.
   *
   * @param newMessages New messages to add to the conversation
   * @param systemPromptMessages Additional system prompt messages
   * @param mode The chat mode (agent, ask, fast)
   */
  // Flag to prevent concurrent conversation processing
  private static isConversationInProgress: boolean = false;
  // Invocation counter to prevent stale processConversation calls from
  // resetting the flag when a new invocation has already started.
  private static currentInvocationId: number = 0;

  /**
   * Force-reset the conversation in-progress flag.
   * Used when sendMessage needs to force-cancel a stuck conversation loop
   * (e.g., when diff approval is pending and user sends a new message).
   * Bumps the invocation counter so the old call won't interfere.
   */
  public static forceReset(): void {
    if (ConversationService.isConversationInProgress) {
      console.log(
        '[ConversationService] Force-resetting conversation in-progress flag'
      );
      ConversationService.isConversationInProgress = false;
      // Bump the counter so the old invocation's cleanup is a no-op
      ConversationService.currentInvocationId++;
    }
  }

  /**
   * Check if a conversation is currently in progress
   */
  public static isInProgress(): boolean {
    return ConversationService.isConversationInProgress;
  }

  public async processConversation(
    newMessages: any[],
    systemPromptMessages: string[] = [],
    mode: 'agent' | 'ask' | 'fast' = 'agent'
  ): Promise<void> {
    // Prevent concurrent conversation processing
    if (ConversationService.isConversationInProgress) {
      console.warn(
        '[ConversationService] Conversation already in progress, skipping duplicate call'
      );
      return;
    }

    ConversationService.isConversationInProgress = true;
    const myInvocationId = ++ConversationService.currentInvocationId;

    const perfStart = performance.now();
    console.log(
      '[PERF] ConversationService.processConversation (LLMLoop) - START'
    );

    // Helper: only reset the flag if this invocation is still the current one
    const resetIfCurrent = () => {
      if (ConversationService.currentInvocationId === myInvocationId) {
        ConversationService.isConversationInProgress = false;
      }
    };

    // Get the effective mode from the centralized chat mode store
    // This is the single source of truth for chat context (launcher vs notebook)
    const effectiveMode: ChatMode = useChatModeStore
      .getState()
      .getEffectiveMode();
    console.log(
      `[ConversationService] Using mode from ChatModeStore: ${effectiveMode} (requested: ${mode})`
    );

    // Handle template contexts - add to LLM history
    if (this.templates && this.templates.length > 0) {
      const { addToLlmHistory } = useChatMessagesStore.getState();
      for (const template of this.templates) {
        addToLlmHistory({
          role: 'user',
          content: `I'm providing the template "${template.name}" as additional context for our conversation:\n\n${template.content}`
        });
      }
      this.templates.length = 0; // Clear templates after use
    }

    // Add loading indicator
    this.loadingManager.updateLoadingIndicator();

    try {
      // Create LLMLoop with all required dependencies
      const llmLoop = this.createLLMLoop();
      if (!llmLoop) {
        throw new Error('Failed to create LLM loop - missing dependencies');
      }

      // Process the conversation
      const result = await llmLoop.process(
        this.notebookId,
        effectiveMode,
        systemPromptMessages
      );

      const perfEnd = performance.now();
      console.log(
        `[PERF] ConversationService.processConversation (LLMLoop) - Complete (${(perfEnd - perfStart).toFixed(2)}ms)`
      );

      // Handle result
      if (!result.success) {
        if (result.error) {
          throw result.error;
        }
      }

      if (result.cancelled) {
        console.log('[ConversationService] Request was cancelled');
        resetIfCurrent();
        return;
      }

      if (result.needsFreshContext) {
        resetIfCurrent();
        await this.handleCellRejection(mode);
        return;
      }
    } catch (error) {
      resetIfCurrent();

      // If cancelled, just return without showing an error
      if (this.chatService.isRequestCancelled()) {
        console.log('Request was cancelled, skipping error handling');
        this.loadingManager.removeLoadingIndicator();
        return;
      }

      this.loadingManager.removeLoadingIndicator();
      throw error;
    }

    resetIfCurrent();
    this.loadingManager.removeLoadingIndicator();
  }

  /**
   * Check if there are any actions that can be undone
   * @returns True if there are actions in the history
   */
  public canUndo(): boolean {
    return this.actionHistory.canUndo();
  }

  /**
   * Get the description of the last action
   * @returns Description of the last action or null if none
   */
  public getLastActionDescription(): string | null {
    return this.actionHistory.getLastActionDescription();
  }

  /**
   * Start checkpoint restoration
   * @param checkpoint The checkpoint to restore
   */
  public async startCheckpointRestoration(
    checkpoint: ICheckpoint
  ): Promise<void> {
    console.log(
      '[ConversationService] Restoring to checkpoint:',
      checkpoint.id
    );

    try {
      if (!this.notebookId) {
        throw 'No notebook ID available for restoration';
      }

      this.loadingManager.updateLoadingIndicator('Restoring checkpoint...');

      // Save the current notebook state BEFORE restoring (for redo)
      this.preRestorationNotebookState =
        NotebookCellStateService.getCurrentNotebookState(this.notebookId);
      console.log(
        '[ConversationService] Saved pre-restoration notebook state:',
        this.preRestorationNotebookState?.length,
        'cells'
      );
      console.log(
        '[ConversationService] Pre-restoration state contents:',
        this.preRestorationNotebookState?.map((c: ICachedCellState) => ({
          index: c.index,
          id: c.id,
          contentLen: c.content?.length
        }))
      );

      // Check checkpoint state
      console.log(
        '[ConversationService] Checkpoint notebookState:',
        checkpoint.notebookState?.length,
        'cells'
      );
      console.log(
        '[ConversationService] Checkpoint state contents:',
        checkpoint.notebookState?.map((c: ICachedCellState) => ({
          index: c.index,
          id: c.id,
          contentLen: c.content?.length
        }))
      );

      // Actually restore the notebook to the checkpoint state
      if (!checkpoint.notebookState || checkpoint.notebookState.length === 0) {
        console.warn('[ConversationService] Checkpoint has no notebook state!');
      }
      await this.applyNotebookState(checkpoint.notebookState);

      // Cache the restored state
      await NotebookCellStateService.cacheNotebookState(
        this.notebookId,
        checkpoint.notebookState
      );

      // Mark messages after the checkpoint as opaque (pending removal)
      // This uses the store-based approach instead of DOM manipulation
      useChatMessagesStore.getState().setRestoringCheckpointId(checkpoint.id);

      this.loadingManager.hideLoadingIndicator();

      useLLMStateStore.getState().showRunKernelButton();

      console.log('[ConversationService] Checkpoint restoration completed');
    } catch (error) {
      console.error(
        '[ConversationService] Error during checkpoint restoration:',
        error
      );
      this.loadingManager.hideLoadingIndicator();
      this.messageComponent.addErrorMessage(
        'Failed to restore checkpoint. Please try again.'
      );
    }
  }

  public async finishCheckpointRestoration(
    checkpoint: ICheckpoint
  ): Promise<void> {
    console.log('[ConversationService] Finishing checkpoint restoration');

    // Remove all messages after the checkpoint from the UI
    useChatMessagesStore
      .getState()
      .removeMessagesAfterCheckpoint(checkpoint.id);

    // Clear the checkpoint to restore
    useChatMessagesStore.getState().setCheckpointToRestore(null);

    // Call the message component to update LLM history and persistent storage
    await this.messageComponent.restoreToCheckpoint(checkpoint);
  }

  /**
   * Redo (cancel restoration) - restore the notebook to the state it was in before restore was clicked
   */
  public async redoActions(_checkpoint: ICheckpoint): Promise<void> {
    console.log(
      '[ConversationService] Redoing - restoring pre-restoration notebook state'
    );
    console.log('[ConversationService] this.notebookId:', this.notebookId);
    console.log(
      '[ConversationService] this.preRestorationNotebookState:',
      this.preRestorationNotebookState?.length,
      'cells'
    );

    if (!this.notebookId) {
      console.warn('[ConversationService] No notebook ID for redo');
      return;
    }

    if (!this.preRestorationNotebookState) {
      console.warn(
        '[ConversationService] No pre-restoration state saved - this should not happen if restore was clicked first'
      );
      return;
    }

    try {
      // Actually restore the notebook cells to pre-restoration state
      await this.applyNotebookState(this.preRestorationNotebookState);

      // Cache the restored state
      await NotebookCellStateService.cacheNotebookState(
        this.notebookId,
        this.preRestorationNotebookState
      );

      // Clear the saved state
      this.preRestorationNotebookState = null;

      console.log(
        '[ConversationService] Pre-restoration notebook state restored'
      );
    } catch (error) {
      console.error(
        '[ConversationService] Error restoring pre-restoration state:',
        error
      );
    }
  }

  /**
   * Apply a notebook state by editing cells to match the target state
   */
  private async applyNotebookState(
    targetState: ICachedCellState[]
  ): Promise<void> {
    if (!this.toolService.notebookTools || !this.notebookId) {
      console.warn(
        '[ConversationService] Cannot apply notebook state - no notebook tools'
      );
      return;
    }

    console.log(
      '[ConversationService] Applying notebook state with',
      targetState.length,
      'cells'
    );

    // Get current notebook state
    const currentState = NotebookCellStateService.getCurrentNotebookState(
      this.notebookId
    );
    if (!currentState) {
      console.warn('[ConversationService] Cannot get current notebook state');
      return;
    }

    console.log(
      '[ConversationService] Current state has',
      currentState.length,
      'cells'
    );

    // Restore each cell by index - simpler and more reliable
    for (const targetCell of targetState) {
      const currentCell = currentState[targetCell.index];

      if (currentCell) {
        // Cell exists at this index - edit it if content differs
        if (currentCell.content !== targetCell.content) {
          console.log(
            '[ConversationService] Restoring cell at index',
            targetCell.index,
            'id:',
            currentCell.id,
            '-> content length:',
            targetCell.content.length
          );
          try {
            this.toolService.notebookTools.edit_cell({
              cell_id: currentCell.id, // Use current cell's ID since that's what exists in notebook
              new_source: targetCell.content,
              summary: 'Restoring checkpoint',
              notebook_path: this.notebookId,
              show_diff: false
            });
          } catch (error) {
            console.warn(
              '[ConversationService] Error restoring cell at index',
              targetCell.index,
              error
            );
          }
        }
      } else {
        // Cell doesn't exist at this index - add it
        console.log(
          '[ConversationService] Adding cell at index',
          targetCell.index,
          'type:',
          targetCell.type,
          'content length:',
          targetCell.content.length
        );
        try {
          this.toolService.notebookTools.add_cell({
            cell_type: targetCell.type || 'code',
            source: targetCell.content,
            summary: 'Restoring checkpoint',
            notebook_path: this.notebookId,
            position: targetCell.index,
            show_diff: false
          });
        } catch (error) {
          console.warn(
            '[ConversationService] Error adding cell at index',
            targetCell.index,
            error
          );
        }
      }
    }

    // Remove extra cells (cells in current that are beyond target length)
    if (currentState.length > targetState.length) {
      const cellIdsToRemove: string[] = [];
      for (let i = targetState.length; i < currentState.length; i++) {
        cellIdsToRemove.push(currentState[i].id);
      }

      if (cellIdsToRemove.length > 0) {
        console.log(
          '[ConversationService] Removing',
          cellIdsToRemove.length,
          'extra cells'
        );
        try {
          this.toolService.notebookTools.remove_cells({
            cell_ids: cellIdsToRemove,
            notebook_path: this.notebookId,
            remove_from_notebook: true
          });
        } catch (error) {
          console.warn('[ConversationService] Error removing cells', error);
        }
      }
    }

    console.log('[ConversationService] Notebook state applied');
  }

  /**
   * Run all cells after checkpoint restoration
   */
  public async runAllCellsAfterRestore(): Promise<void> {
    console.log(
      '[ConversationService] Running all cells after checkpoint restoration'
    );

    try {
      // Add loading indicator
      this.loadingManager.updateLoadingIndicator('Running all cells...');

      // Get all code cells and run them
      if (this.notebookId && this.toolService.notebookTools) {
        const cellData = this.toolService.notebookTools.read_cells({
          notebook_path: this.notebookId,
          include_outputs: false,
          include_metadata: true
        });

        if (cellData && cellData.cells) {
          const codeCells = cellData.cells.filter(
            (cell: any) => cell.type === 'code'
          );

          for (const cell of codeCells) {
            try {
              await this.toolService.notebookTools.run_cell({
                cell_id: cell.trackingId || cell.id,
                notebook_path: this.notebookId
              });
            } catch (error) {
              console.warn(
                '[ConversationService] Error running cell:',
                cell.id,
                error
              );
            }
          }
        }
      }

      this.loadingManager.hideLoadingIndicator();
      console.log('[ConversationService] All cells execution completed');
    } catch (error) {
      console.error('[ConversationService] Error running all cells:', error);
      this.loadingManager.hideLoadingIndicator();
      this.messageComponent.addErrorMessage(
        'Failed to run all cells. Please run them manually.'
      );
    }
  }

  /**
   * Undo the last action
   * @returns True if an action was undone, false if no actions to undo
   */
  public async undoLastAction(): Promise<boolean> {
    const action = this.actionHistory.popLastAction();
    if (!action) {
      return false;
    }

    try {
      this.loadingManager.updateLoadingIndicator('Undoing action...');

      switch (action.type) {
        case ActionType.ADD_CELL:
          await this.undoAddCell(action);
          break;

        case ActionType.EDIT_CELL:
          await this.undoEditCell(action);
          break;

        case ActionType.REMOVE_CELLS:
          await this.undoRemoveCells(action);
          break;
        case ActionType.EDIT_PLAN:
          await this.undoEditPlan(action);
          break;
      }

      // Add a system message to indicate the action was undone
      this.messageComponent.addSystemMessage(
        `✓ Undid action: ${action.description}`
      );
      this.loadingManager.removeLoadingIndicator();
      return true;
    } catch (error) {
      console.error('Error undoing action:', error);
      this.messageComponent.addErrorMessage(
        `Failed to undo action: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
      this.loadingManager.removeLoadingIndicator();
      return false;
    }
  }

  /**
   * Clear the action history
   */
  public clearActionHistory(): void {
    this.actionHistory.clear();
  }

  /**
   * Sync the chat service's history with the message component's history
   * This ensures the LLM has full context of the conversation
   */
  private syncChatServiceHistory(): void {
    // Get current message history from the message component
    const messageHistory = this.messageComponent.getMessageHistory();

    if (messageHistory.length > 0) {
      this.messageComponent.scrollToBottom();
    }

    console.log(
      `Synchronized ${messageHistory.length} messages to chat service history`
    );
  }

  /**
   * Create an LLMLoop instance with the current service state
   */
  private createLLMLoop(): LLMLoop | null {
    let notebookContextManager;
    try {
      notebookContextManager = getNotebookContextManager();
    } catch (error) {
      console.error(
        '[ConversationService] NotebookContextManager not available:',
        error
      );
      return null;
    }

    const config: ILLMLoopConfig = {
      anthropicService: this.chatService as AnthropicService,
      toolService: this.toolService,
      messageComponent: this.messageComponent,
      notebookContextManager,
      diffManager: this.diffManager,
      actionHistory: this.actionHistory,
      chatHistory: this.chatHistory,
      loadingManager: this.loadingManager,
      codeConfirmationDialog: this.codeConfirmationDialog
    };

    return new LLMLoop(config);
  }

  /**
   * Undo all actions from the checkpoint chain, starting from the oldest checkpoint
   */
  private async undoActions(checkpoint: ICheckpoint): Promise<void> {
    console.log(
      '[ConversationService] Undoing all actions from checkpoint chain'
    );

    // Helper to recursively collect all checkpoints from oldest to newest
    const allNotebookCheckpoints =
      CheckpointManager.getInstance().getCheckpoints();

    const collectCheckpoints = (
      cp: ICheckpoint,
      allCheckpoints: ICheckpoint[] = []
    ): ICheckpoint[] => {
      if (cp.nextCheckpointId) {
        // Find the next checkpoint by id
        const next = allNotebookCheckpoints.find(
          c => c.id === cp.nextCheckpointId
        );
        if (next) {
          collectCheckpoints(next, allCheckpoints);
        }
      }
      allCheckpoints.push(cp);
      return allCheckpoints;
    };

    // Collect all checkpoints from oldest to the current one (inclusive)
    const checkpointsToUndo = collectCheckpoints(checkpoint, []);

    // Collect all actions in order (oldest checkpoint first)
    const allActions: IActionHistoryEntry[] = [];
    for (const cp of checkpointsToUndo) {
      if (cp.actionHistory && cp.actionHistory.length > 0) {
        allActions.push(...cp.actionHistory);
      }
    }

    console.log(
      '[ConversationService] Total actions to undo from all checkpoints:',
      allActions.length
    );

    for (let i = 0; i < allActions.length; i++) {
      const action = allActions[i];
      console.log('[ConversationService] Undoing action:', action.description);

      try {
        switch (action.type) {
          case 'add_cell':
            await this.undoAddCell(action);
            break;
          case 'edit_cell':
            await this.undoEditCell(action);
            break;
          case 'remove_cells':
            await this.undoRemoveCells(action);
            break;
          case 'edit_plan':
            await this.undoEditPlan(action);
            break;
        }
      } catch (error) {
        console.warn(
          '[ConversationService] Error undoing action:',
          action.description,
          error
        );
      }
    }

    console.log('[ConversationService] All checkpoint actions undone');
  }

  /**
   * Redo adding a cell
   */
  private async redoAddCell(action: IActionHistoryEntry): Promise<void> {
    // Use trackingId if available, fallback to cellId for backward compatibility
    const trackingId = action.data.trackingId || action.data.cellId;

    // Re-add the cell using the same parameters
    await this.toolService.executeTool({
      id: 'redo_add_cell',
      name: 'notebook-add_cell',
      input: {
        cell_type: action.data.originalCellType, // Default to code cell type
        source: action.data.newContent || action.data.source || '',
        summary: action.data.summary || 'Redone by checkpoint restoration',
        tracking_id: trackingId, // Reuse the same tracking ID
        run_cell: action.data.originalCellType === 'markdown'
      }
    });
  }

  /**
   * Redo editing a cell
   */
  private async redoEditCell(action: IActionHistoryEntry): Promise<void> {
    // Use trackingId if available, fallback to cellId for backward compatibility
    const trackingId = action.data.trackingId || action.data.cellId;

    // Apply the edit again using the new content
    await this.toolService.executeTool({
      id: 'redo_edit_cell',
      name: 'notebook-edit_cell',
      input: {
        cell_id: trackingId,
        new_source: action.data.newContent,
        summary: action.data.summary || 'Redone by checkpoint restoration',
        is_tracking_id: true
      }
    });
  }

  /**
   * Redo removing cells
   */
  private async redoRemoveCells(action: IActionHistoryEntry): Promise<void> {
    const cellId = action.data.cellId;
    if (cellId) {
      await this.toolService.executeTool({
        id: 'redo_remove_cells',
        name: 'notebook-remove_cells',
        input: {
          cell_ids: [cellId],
          remove_from_notebook: true
        }
      });
    }
  }

  /**
   * Redo editing the plan
   */
  private async redoEditPlan(action: IActionHistoryEntry): Promise<void> {
    const newContent = action.data.newContent || '';
    const current = this.toolService.notebookTools?.getCurrentNotebook(
      this.notebookId
    );
    if (!current) {
      console.error('No notebook found for redo edit_plan');
      return;
    }

    const { notebook } = current;

    const firstCell = notebook.widgets[0];

    if (!firstCell) {
      return;
    }

    // Apply the plan edit again
    firstCell.model.sharedModel.setSource(newContent);
    const metadata = (firstCell.model.sharedModel.getMetadata() || {}) as any;
    if (!metadata.custom) {
      metadata.custom = {};
    }

    // For redo, we need to use the new values that were applied
    // Since we don't have newCurrentStep/newNextStep in the interface,
    // we'll use the summary or leave them empty
    metadata.custom.current_step_string = '';
    metadata.custom.next_step_string = '';
    metadata.custom.sage_cell_type = 'plan';
    metadata.cell_tracker.trackingId = 'planning_cell';

    firstCell.model.sharedModel.setMetadata(metadata);

    NotebookActions.changeCellType(notebook, 'markdown');

    await NotebookActions.runCells(
      notebook,
      [notebook.widgets[0]],
      current.widget?.sessionContext
    );

    await usePlanStateStore.getState().updatePlan('', '', newContent, false);
  }

  /**
   * Undo adding a cell
   */
  private async undoAddCell(action: IActionHistoryEntry): Promise<void> {
    // Use trackingId if available, fallback to cellId for backward compatibility
    const trackingId = action.data.trackingId || action.data.cellId;

    // Remove the added cell using tracking ID
    await this.toolService.executeTool({
      id: 'undo_add_cell',
      name: 'notebook-remove_cells',
      input: {
        cell_ids: [trackingId],
        remove_from_notebook: true
      }
    });
  }

  /**
   * Undo editing the plan
   */
  private async undoEditPlan(action: IActionHistoryEntry): Promise<void> {
    const oldPlan = action.data.oldPlan || '';
    const planExisted = action.data.planExisted || false;
    const current = this.toolService.notebookTools?.getCurrentNotebook(
      this.notebookId
    );
    if (!current) {
      console.error('No notebook found for edit_plan');
      return;
    }

    const { notebook } = current;

    const firstCell = notebook.widgets[0];

    if (!firstCell) {
      return;
    }

    if (planExisted) {
      // This means the plan was already there, so we just need to update it
      firstCell.model.sharedModel.setSource(oldPlan);
      const metadata = (firstCell.model.sharedModel.getMetadata() || {}) as any;
      if (!metadata.custom) {
        metadata.custom = {};
      }

      metadata.custom.current_step_string = action.data.oldCurrentStep;
      metadata.custom.next_step_string = action.data.oldNextStep;

      firstCell.model.sharedModel.setMetadata(metadata);

      void usePlanStateStore
        .getState()
        .updatePlan(
          action.data.oldCurrentStep || '',
          action.data.oldNextStep,
          oldPlan,
          false
        );
    } else {
      // This means the plan was not there, so we need to delete the plan cell
      this.toolService.notebookTools!.activateCell(firstCell);
      NotebookActions.deleteCells(notebook);
    }
  }

  /**
   * Undo editing a cell
   */
  private async undoEditCell(action: IActionHistoryEntry): Promise<void> {
    // Use trackingId if available, fallback to cellId for backward compatibility
    const trackingId = action.data.trackingId || action.data.cellId;

    // Restore the original cell content using tracking ID
    await this.toolService.executeTool({
      id: 'undo_edit_cell',
      name: 'notebook-edit_cell',
      input: {
        cell_id: trackingId,
        new_source: action.data.originalContent,
        summary: action.data.originalSummary || 'Restored by undo',
        is_tracking_id: true
      }
    });
  }

  /**
   * Undo removing cells
   */
  private async undoRemoveCells(action: IActionHistoryEntry): Promise<void> {
    const cellId = action.data.cellId;
    if (cellId) {
      const metadata = action.data.metadata;
      await this.toolService.executeTool({
        id: 'undo_remove_cell',
        name: 'notebook-add_cell',
        input: {
          cell_type: 'code',
          source: action.data.oldContent,
          summary: metadata.custom?.summary || 'Restored by undo',
          position: metadata.custom?.index, // Use index from custom metadata if available
          tracking_id: cellId // Provide tracking ID to reuse
        }
      });
    }
  }
}
