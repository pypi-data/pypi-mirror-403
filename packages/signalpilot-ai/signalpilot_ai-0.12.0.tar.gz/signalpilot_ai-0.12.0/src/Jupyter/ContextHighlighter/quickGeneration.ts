/**
 * Quick Generation / Inline Edit Logic
 *
 * Handles the AI-powered inline editing functionality (Cmd+K).
 * Supports both edit_selection (selected lines) and edit_full_cell modes.
 */

import { parse as parseBestEffortJson } from 'best-effort-json-parser';
import { INotebookTracker } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';
import { NotebookTools } from '../../Notebook/NotebookTools';
import { getChatService, getConfig } from '../../stores/servicesStore';
import { inlineDiffService } from '../Diff/InlineDiffService';
import { IEditOperation, IEditSelectionResponse } from './types';
import { CellHistoryManager, updateUndoButtonState } from './cellHistory';

/**
 * Configuration for quick generation
 */
export interface QuickGenConfig {
  notebookTracker: INotebookTracker;
  notebookTools: NotebookTools;
  historyManager: CellHistoryManager;
  abortController: AbortController | null;
  setAbortController: (controller: AbortController | null) => void;
}

/**
 * Calculate end line for selection, handling edge cases
 */
export function calculateEndLine(
  end: { line: number; column: number } | undefined,
  cellLines: string[]
): { line: number; column: number } {
  if (!end) {
    return { line: 0, column: 0 };
  }
  if (end.line >= cellLines.length) {
    return {
      line: cellLines.length - 1,
      column: cellLines[cellLines.length - 1]?.length || 0
    };
  }
  return end;
}

/**
 * Show diff view for a cell after AI modification using InlineDiffService
 */
export function showDiffView(
  cell: Cell,
  originalContent: string,
  newContent: string
): void {
  try {
    inlineDiffService.showInlineDiff(cell, originalContent, newContent);
    console.log(
      '[QuickGeneration] Inline diff displayed using InlineDiffService'
    );
  } catch (error) {
    console.error('Error showing diff view:', error);
  }
}

/**
 * Try to parse JSON and extract complete edit operations
 */
function tryParseOperations(text: string): IEditOperation[] {
  try {
    const parsedResponse = parseBestEffortJson(
      text.trim()
    ) as IEditSelectionResponse;

    if (
      parsedResponse?.operations &&
      Array.isArray(parsedResponse.operations)
    ) {
      return parsedResponse.operations.filter(
        (op: IEditOperation) =>
          op.line !== undefined &&
          op.action &&
          ['KEEP', 'MODIFY', 'REMOVE', 'INSERT'].includes(op.action)
      );
    }
  } catch {
    // JSON parsing failed
  }
  return [];
}

/**
 * Apply edit operations to cell lines
 */
function applyOperationsToLines(
  cellLines: string[],
  operations: IEditOperation[]
): string[] {
  if (operations.length === 0) {
    return cellLines;
  }

  const updatedLines = [...cellLines];
  let lineOffset = 0;

  // Sort operations by line number
  const sortedOperations = operations.sort((a, b) => a.line - b.line);

  for (const operation of sortedOperations) {
    const actualLineIndex = operation.line - 1 + lineOffset;

    switch (operation.action) {
      case 'KEEP':
        break;
      case 'MODIFY':
        if (
          actualLineIndex < updatedLines.length &&
          operation.content !== undefined
        ) {
          updatedLines[actualLineIndex] = operation.content;
        }
        break;
      case 'REMOVE':
        if (actualLineIndex < updatedLines.length) {
          updatedLines.splice(actualLineIndex, 1);
          lineOffset--;
        }
        break;
      case 'INSERT':
        if (
          actualLineIndex <= updatedLines.length &&
          operation.content !== undefined
        ) {
          updatedLines.splice(actualLineIndex, 0, operation.content);
          lineOffset++;
        }
        break;
    }
  }

  return updatedLines;
}

/**
 * Extract code from response, handling markdown code blocks
 */
function extractCodeFromResponse(response: string): string {
  const codeBlockPattern = /```(?:python|py)?\s*([\s\S]*?)```/i;
  const match = response.match(codeBlockPattern);

  if (match) {
    return match[1].replace(/^\s*(python|py)\s*\n?/i, '').trim();
  }

  return response.trim();
}

/**
 * Handle edit_selection mode with streaming
 */
async function handleEditSelection(
  config: QuickGenConfig,
  cellId: string,
  cellLines: string[],
  startLine: number,
  endLine: number,
  selectedLines: string[],
  contextMessage: string,
  systemPrompt: string
): Promise<boolean | 'cancelled'> {
  const targetCell = config.notebookTools.findCellByTrackingId(cellId);
  if (!targetCell) {
    throw new Error(`Could not find cell with ID ${cellId}`);
  }

  let accumulatedResponse = '';
  let lastAppliedOperations: IEditOperation[] = [];

  const chatService = getChatService();
  const response = await chatService.sendEphemeralMessage(
    contextMessage,
    systemPrompt,
    'claude-3-5-haiku-latest',
    (textChunk: string) => {
      accumulatedResponse += textChunk;

      const currentOperations = tryParseOperations(accumulatedResponse);

      if (currentOperations.length > 0) {
        const operationsChanged =
          currentOperations.length !== lastAppliedOperations.length ||
          currentOperations.some((op, idx) => {
            const lastOp = lastAppliedOperations[idx];
            return (
              !lastOp ||
              op.line !== lastOp.line ||
              op.action !== lastOp.action ||
              op.content !== lastOp.content
            );
          });

        if (operationsChanged) {
          const updatedLines = applyOperationsToLines(
            cellLines,
            currentOperations
          );
          targetCell.cell.model.sharedModel.setSource(updatedLines.join('\n'));
          lastAppliedOperations = [...currentOperations];
        }
      }
    },
    undefined,
    undefined,
    'cmd-k'
  );

  config.setAbortController(null);

  if (typeof response === 'object') {
    // Cancelled
    const metadata: any = targetCell.cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;
    if (trackingId) {
      config.historyManager.restoreOnCancel(trackingId, targetCell.cell);
    }
    return 'cancelled';
  }

  // Final application
  const finalOperations = tryParseOperations(response);
  if (finalOperations.length > 0) {
    const updatedLines = applyOperationsToLines(cellLines, finalOperations);
    targetCell.cell.model.sharedModel.setSource(updatedLines.join('\n'));
    console.log(
      `Applied ${finalOperations.length} edit_selection operations to lines ${startLine + 1}-${endLine + 1}`
    );
    return true;
  }

  console.error('No valid operations found in response');
  return false;
}

/**
 * Handle edit_full_cell mode with streaming
 */
async function handleEditFullCell(
  config: QuickGenConfig,
  cellId: string,
  cellLines: string[],
  contextMessage: string,
  systemPrompt: string
): Promise<boolean | 'cancelled'> {
  const targetCell = config.notebookTools.findCellByTrackingId(cellId);
  if (!targetCell) {
    throw new Error(`Could not find cell with ID ${cellId}`);
  }

  let accumulatedResponse = '';
  let codeContent = '';
  let isInCodeBlock = false;
  const codeBlockStartPattern = /```(?:python|py)?\s*/i;
  const codeBlockEndPattern = /```/;

  const chatService = getChatService();
  const response = await chatService.sendEphemeralMessage(
    contextMessage,
    systemPrompt,
    'claude-3-5-haiku-latest',
    (textChunk: string) => {
      accumulatedResponse += textChunk;

      // Handle code extraction for streaming
      if (!isInCodeBlock) {
        const startMatch = accumulatedResponse.match(codeBlockStartPattern);
        if (startMatch) {
          isInCodeBlock = true;
          codeContent = accumulatedResponse.substring(
            accumulatedResponse.indexOf(startMatch[0]) + startMatch[0].length
          );
          codeContent = codeContent.replace(/^\s*(python|py)\s*\n?/i, '');
        } else {
          codeContent = accumulatedResponse;
        }
      } else {
        if (codeBlockEndPattern.test(textChunk)) {
          isInCodeBlock = false;
          const endIndex = codeContent.lastIndexOf('```');
          if (endIndex !== -1) {
            codeContent = codeContent.substring(0, endIndex);
          }
          codeContent = codeContent.replace(/^\s*(python|py)\s*\n?/i, '');
        } else {
          codeContent += textChunk;
        }
      }

      // Progressive transformation
      if (codeContent.includes('\n')) {
        const newCodeLines = codeContent.split('\n');
        const displayLines = [...cellLines];

        const linesToReplace = Math.min(newCodeLines.length, cellLines.length);
        for (let i = 0; i < linesToReplace; i++) {
          if (newCodeLines[i] !== undefined) {
            displayLines[i] = newCodeLines[i];
          }
        }

        if (newCodeLines.length > cellLines.length) {
          for (let i = cellLines.length; i < newCodeLines.length; i++) {
            if (newCodeLines[i] !== undefined) {
              displayLines.push(newCodeLines[i]);
            }
          }
        }

        targetCell.cell.model.sharedModel.setSource(displayLines.join('\n'));
      } else if (codeContent.trim() && !codeContent.includes('\n')) {
        const displayLines = [...cellLines];
        if (displayLines.length > 0) {
          displayLines[0] = codeContent.trim();
        } else {
          displayLines.push(codeContent.trim());
        }
        targetCell.cell.model.sharedModel.setSource(displayLines.join('\n'));
      }
    },
    undefined,
    undefined,
    'cmd-k'
  );

  config.setAbortController(null);

  if (typeof response === 'object') {
    // Cancelled
    const metadata: any = targetCell.cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;
    if (trackingId) {
      config.historyManager.restoreOnCancel(trackingId, targetCell.cell);
    }
    return 'cancelled';
  }

  // Final cleanup
  let finalCode = codeContent.trim();
  if (!finalCode && response.trim()) {
    finalCode = extractCodeFromResponse(response);
  } else if (finalCode) {
    finalCode = finalCode
      .replace(/^```(?:python|py)?\s*/i, '')
      .replace(/```$/, '')
      .replace(/^\s*(python|py)\s*\n?/i, '')
      .trim();
  }

  if (finalCode) {
    targetCell.cell.model.sharedModel.setSource(finalCode);
    console.log(`Applied edit_full_cell response to cell ${cellId}`);
    return true;
  }

  return false;
}

/**
 * Main prompt submission handler for quick generation
 */
export async function onPromptSubmit(
  config: QuickGenConfig,
  cell: Cell,
  promptText: string
): Promise<boolean | 'cancelled'> {
  console.log('Prompt submitted for cell:', promptText);

  // Get cell ID
  const cellId =
    (cell as any).model?.sharedModel.getMetadata()?.cell_tracker?.trackingId ||
    (cell as any).model?.id ||
    (cell as any).id ||
    '[unknown]';

  if (cellId === '[unknown]') {
    console.error('Could not determine cell ID');
    return false;
  }

  const activeCell = config.notebookTracker.activeCell;
  if (!activeCell) {
    console.warn('No active cell');
    return false;
  }

  const editor = activeCell.editor;
  const selection = editor?.getSelection();
  const cellLines = editor?.model.sharedModel.source.split('\n') || [];
  const endSelection = calculateEndLine(selection?.end, cellLines);
  const selectedText = editor?.model.sharedModel.source.substring(
    editor.getOffsetAt(selection?.start || { line: 0, column: 0 }),
    editor.getOffsetAt(endSelection)
  );

  const hasSelection = selectedText && selectedText.trim().length > 0;
  const startLine = selection?.start?.line || 0;
  const endLine = endSelection.line;
  const selectedLines = cellLines.slice(startLine, endLine + 1);

  const appConfig = getConfig();
  const modeConfig = hasSelection
    ? appConfig.edit_selection
    : appConfig.edit_full_cell;
  const modeLabel = hasSelection ? 'edit_selection' : 'edit_full_cell';
  const systemPrompt = modeConfig.system_prompt;

  // Build context message
  const cellContent = config.notebookTools
    .findCellByTrackingId(cellId)
    ?.cell.model.sharedModel.getSource();
  const previousCellContent = config.notebookTools
    .findCellByIndex(
      (config.notebookTools.findCellByTrackingId(cellId)?.index || 0) - 1
    )
    ?.cell?.model?.sharedModel.getSource();

  let contextMessage: string;

  if (hasSelection) {
    const selectionRangeLines = selectedLines
      .map((line, index) => {
        const lineNum = startLine + index + 1;
        return `${lineNum.toString().padStart(3, ' ')}: ${line}`;
      })
      .join('\n');

    const fullCellLines = cellLines
      .map((line, index) => {
        const lineNum = index + 1;
        return `${lineNum.toString().padStart(3, ' ')}:${line}`;
      })
      .join('\n');

    contextMessage = `EDIT SELECTION MODE: Edit the selected lines (${startLine + 1}-${endLine + 1}) using structured operations.

FULL CELL CONTEXT:
\`\`\`
${fullCellLines}
\`\`\`

SELECTED LINES TO EDIT (${startLine + 1}-${endLine + 1}):
\`\`\`
${selectionRangeLines}
\`\`\`

Return a JSON object with operations for each line in the selection range. Use KEEP, MODIFY, REMOVE, or INSERT actions. Consider the full cell context when making edits.

User request: ${promptText}`;
  } else {
    contextMessage = `EDIT FULL CELL MODE: Edit and improve the complete cell.

CELL TO EDIT:
\`\`\`
${cellContent}
\`\`\`

PREVIOUS CELL CONTENT:
\`\`\`
${previousCellContent}
\`\`\`

Return only the fully edited cell. Apply your quantitative expertise to improve the code.

User request: ${promptText}`;
  }

  try {
    const abortController = new AbortController();
    config.setAbortController(abortController);

    const chatService = getChatService();
    chatService.initializeRequest(abortController);

    let result: boolean | 'cancelled';

    if (hasSelection) {
      result = await handleEditSelection(
        config,
        cellId,
        cellLines,
        startLine,
        endLine,
        selectedLines,
        contextMessage,
        systemPrompt
      );
    } else {
      result = await handleEditFullCell(
        config,
        cellId,
        cellLines,
        contextMessage,
        systemPrompt
      );
    }

    console.log(`Ephemeral ${modeLabel} request completed.`);
    return result;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error(`Failed to process: ${errorMessage}`, error);
    return false;
  }
}

/**
 * Handle the full prompt submission flow with UI updates
 */
export async function handlePromptSubmit(
  config: QuickGenConfig,
  cell: Cell,
  prompt: string
): Promise<void> {
  if (!prompt.trim()) return;

  const inputContainer = cell.node.querySelector(
    '.sage-ai-prompt-input'
  ) as HTMLInputElement;
  const errorMessage = cell.node.querySelector(
    '.sage-ai-quick-gen-prompt-error-message'
  ) as HTMLElement;
  const submitButton = cell.node.querySelector(
    '.sage-ai-quick-gen-submit'
  ) as HTMLButtonElement;
  const undoButton = cell.node.querySelector(
    '.sage-ai-quick-gen-undo'
  ) as HTMLButtonElement;
  const loader = cell.node.querySelector('.sage-ai-blob-loader') as HTMLElement;

  // Get cell tracking ID and save to history
  const metadata: any = cell.model.sharedModel.getMetadata() || {};
  const trackingId = metadata.cell_tracker?.trackingId;
  const originalContent = cell.model.sharedModel.getSource();

  if (trackingId) {
    config.historyManager.saveToHistory(trackingId, originalContent);
  }

  // Show loading state
  if (loader) loader.style.display = 'block';
  if (submitButton) submitButton.disabled = true;
  if (inputContainer) inputContainer.disabled = true;
  if (undoButton) undoButton.disabled = true;

  const result = await onPromptSubmit(config, cell, prompt);

  // Hide loading state
  if (loader) loader.style.display = 'none';
  if (submitButton) submitButton.disabled = false;
  if (inputContainer) inputContainer.disabled = false;

  if (result === true) {
    if (inputContainer) inputContainer.value = '';
    errorMessage?.classList.add(
      'sage-ai-quick-gen-prompt-error-message-hidden'
    );

    // Show diff if content changed
    const newContent = cell.model.sharedModel.getSource();
    if (originalContent !== newContent) {
      showDiffView(cell, originalContent, newContent);
    }

    updateUndoButtonState(cell, config.historyManager);
  } else if (result === false) {
    errorMessage?.classList.remove(
      'sage-ai-quick-gen-prompt-error-message-hidden'
    );
    if (undoButton) undoButton.disabled = true;
  }
}
