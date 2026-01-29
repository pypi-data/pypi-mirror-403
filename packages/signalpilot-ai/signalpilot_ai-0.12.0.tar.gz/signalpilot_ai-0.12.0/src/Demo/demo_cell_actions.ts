import { useNotebookEventsStore } from '../stores/notebookEventsStore';
import {
  getToolService,
  getCellTrackingService
} from '../stores/servicesStore';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { NotebookActions } from '@jupyterlab/notebook';
import { IDemoToolUseBlock } from './demo';
import { timeout } from '../utils';

/**
 * Demo cell actions that bypass streaming and LLM calls for instant results
 *
 * This module provides optimized versions of notebook operations for demo mode:
 * - edit_plan: Directly parses and displays plans from tool results without LLM calls
 * - skip_to_result: Removes run_cell calls and executes NotebookActions.runAll()
 */

/**
 * Handle edit_plan tool call by directly creating/updating the plan
 * Bypasses streaming and immediately shows the plan from the tool_result
 *
 * @param toolUse The tool_use block from the assistant message
 * @param toolResultContent The content from the subsequent tool_result message
 * @param chatMessages ChatMessages instance to display the plan
 */
export async function handleEditPlan(
  toolUse: IDemoToolUseBlock,
  toolResultContent: string,
  chatMessages: ChatMessages
): Promise<void> {
  console.log('[Demo] Handling edit_plan with direct plan creation');

  if (!toolResultContent) {
    throw new Error('No plan content found in tool result');
  }

  // Get required services and notebook
  const toolService = getToolService();
  const notebookTools = toolService?.notebookTools;
  if (!notebookTools) {
    throw new Error('Notebook tools not available');
  }

  const currentNotebook = useNotebookEventsStore
    .getState()
    .getCurrentNotebook();
  if (!currentNotebook) {
    throw new Error('No active notebook');
  }

  const notebookPath = currentNotebook.context.path;
  console.log('[Demo] Creating plan cell with content:', toolResultContent);

  try {
    // Get or create plan cell
    let planCell = notebookTools.getPlanCell(notebookPath);
    if (!planCell) {
      if (useNotebookEventsStore.getState().getCurrentNotebook()) {
        notebookTools.add_cell({
          cell_type: 'code',
          source: '',
          summary: '',
          position: 0
        });
      }
      notebookTools.setFirstCellAsPlan();
      await timeout(500);
      planCell = notebookTools.getPlanCell(notebookPath);
    }

    console.log('[Demo] Retrieved plan cell:', planCell);

    if (!planCell) {
      throw new Error('[Demo] Failed to create or retrieve plan cell');
    }

    // Get tracking ID from plan cell
    const cellTrackingService = getCellTrackingService();
    const trackingMetadata =
      cellTrackingService?.getCellTrackingMetadata(planCell);
    const trackingId = trackingMetadata?.trackingId;

    if (!trackingId) {
      console.warn('[Demo] Plan cell found but has no tracking ID');
      return;
    }

    // Update plan cell with new content
    console.log('[Demo] Updating plan cell:', trackingId);
    planCell.model.sharedModel.setSource(toolResultContent);

    console.log('[Demo] Plan cell updated successfully');
  } catch (error) {
    console.error('[Demo] Error handling edit_plan:', error);
    throw error;
  }
}

/**
 * Skip to result: Remove all run_cell tool calls and execute NotebookActions.runAll()
 * This is used in skip mode to immediately execute all cells instead of streaming them
 *
 * @param messages Array of demo messages
 * @returns Modified messages array without run_cell calls
 */
export function skipToResult(messages: any[]): any[] {
  console.log('[Demo] Applying skip-to-result: removing run_cell calls');

  const filteredMessages = messages.map(message => {
    if (message.role !== 'assistant') {
      return message;
    }

    // Filter out run_cell tool calls from assistant messages
    if (Array.isArray(message.content)) {
      const filteredContent = message.content.filter((block: any) => {
        if (block.type === 'tool_use' && block.name === 'notebook-run_cell') {
          console.log('[Demo] Removing run_cell tool call:', block.id);
          return false;
        }
        return true;
      });

      return {
        ...message,
        content: filteredContent
      };
    }

    return message;
  });

  // Also remove corresponding tool_result messages for run_cell
  const runCellToolIds = new Set<string>();
  messages.forEach(msg => {
    if (msg.role === 'assistant' && Array.isArray(msg.content)) {
      msg.content.forEach((block: any) => {
        if (block.type === 'tool_use' && block.name === 'notebook-run_cell') {
          runCellToolIds.add(block.id);
        }
      });
    }
  });

  // Filter out tool_result messages for run_cell
  const finalMessages = filteredMessages.filter(msg => {
    if (msg.role === 'user' && Array.isArray(msg.content)) {
      const hasRunCellResult = msg.content.some(
        (block: any) =>
          block.type === 'tool_result' && runCellToolIds.has(block.tool_use_id)
      );
      if (hasRunCellResult && msg.content.length === 1) {
        console.log('[Demo] Removing tool_result for run_cell');
        return false;
      }
      // If there are multiple content blocks, filter out just the run_cell result
      if (hasRunCellResult) {
        msg.content = msg.content.filter(
          (block: any) =>
            !(
              block.type === 'tool_result' &&
              runCellToolIds.has(block.tool_use_id)
            )
        );
      }
    }
    return true;
  });

  console.log(
    `[Demo] Filtered ${messages.length - finalMessages.length} run_cell related messages`
  );

  return finalMessages;
}

/**
 * Execute all cells in the current notebook
 * This is called after skip-to-result to run all generated cells at once
 *
 * NOTE: We run cells sequentially instead of using NotebookActions.runAll()
 * because runAll() executes cells in parallel, which can cause JupyterLab's
 * Table of Contents plugin to crash with "Cannot read properties of undefined
 * (reading 'isRunning')" errors. The ToC's updateRunningStatus method iterates
 * over cells while execution events are firing, and some cells may not be
 * properly synchronized in its internal tracking.
 */
export async function executeAllCells(): Promise<void> {
  console.log('[Demo] Executing all cells in notebook sequentially');

  const currentNotebook = useNotebookEventsStore
    .getState()
    .getCurrentNotebook();
  if (!currentNotebook) {
    console.error('[Demo] No active notebook for execution');
    return;
  }

  const notebook = currentNotebook.content;
  const sessionContext = currentNotebook.context.sessionContext;

  try {
    // Get all code cells that need to be executed
    const cells = notebook.widgets.filter(cell => cell.model.type === 'code');
    console.log(`[Demo] Found ${cells.length} code cells to execute`);

    // Run cells sequentially to avoid ToC synchronization issues
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      console.log(`[Demo] Executing cell ${i + 1}/${cells.length}`);

      try {
        await NotebookActions.runCells(notebook, [cell], sessionContext);
      } catch (cellError) {
        // Log but continue with remaining cells
        console.warn(`[Demo] Error executing cell ${i + 1}:`, cellError);
      }

      // Small delay between cells to allow JupyterLab to sync state
      await timeout(50);
    }

    console.log('[Demo] All cells executed successfully');
  } catch (error) {
    console.error('[Demo] Error executing cells:', error);
  }
}

/**
 * Check if a tool call is edit_plan
 */
export function isEditPlanTool(toolName: string): boolean {
  return toolName === 'notebook-edit_plan';
}

/**
 * Check if a tool call is run_cell
 */
export function isRunCellTool(toolName: string): boolean {
  return toolName === 'notebook-run_cell';
}

/**
 * Process messages for demo mode with optimizations
 * - Replace edit_plan with direct plan creation
 * - Optionally skip run_cell calls
 *
 * @param messages Original demo messages
 * @param skipMode Whether to apply skip-to-result optimizations
 * @returns Processed messages ready for demo
 */
export function processDemoMessages(
  messages: any[],
  skipMode: boolean = false
): any[] {
  let processed = messages;

  if (skipMode) {
    // Apply skip-to-result filtering
    processed = skipToResult(processed);
  }

  return processed;
}
