/**
 * Cell Context UI
 *
 * Handles the UI elements for cell context management:
 * - Add/Remove context buttons
 * - Cell highlighting
 * - Cell ID labels
 * - Quick generation button and input UI
 * - Empty cell placeholder
 */

import { NotebookPanel } from '@jupyterlab/notebook';
import { Cell } from '@jupyterlab/cells';
import { NotebookContextManager } from '../../Notebook/NotebookContextManager';
import { NotebookTools } from '../../Notebook/NotebookTools';
import { getChatService } from '../../stores/servicesStore';
import {
  ADD_ICON,
  CANCEL_ICON,
  getKeyboardShortcutLabel,
  SUBMIT_ICON,
  UNDO_ICON
} from './icons';
import { CellHistoryManager, updateUndoButtonState } from './cellHistory';
import { handlePromptSubmit, QuickGenConfig } from './quickGeneration';

/**
 * Configuration for cell context UI
 */
export interface CellContextUIConfig {
  notebookContextManager: NotebookContextManager;
  notebookTools: NotebookTools;
  historyManager: CellHistoryManager;
  chatContainerRef: any;
  cellsWithKeydownListener: WeakSet<HTMLElement>;
  getAbortController: () => AbortController | null;
  setAbortController: (controller: AbortController | null) => void;
  quickGenConfig: QuickGenConfig;
}

/**
 * Highlight a cell to indicate it's in context
 */
export function highlightCell(cell: Cell, isInContext: boolean): void {
  // Remove existing highlighting
  cell.node.classList.remove('sage-ai-in-context-cell');
  const existingIndicator = cell.node.querySelector(
    '.sage-ai-context-indicator'
  );
  if (existingIndicator) {
    existingIndicator.remove();
  }

  const existingBadge = cell.node.querySelector('.sage-ai-context-badge');
  if (existingBadge) {
    existingBadge.remove();
  }

  if (isInContext) {
    cell.node.classList.add('sage-ai-in-context-cell');

    const indicator = document.createElement('div');
    indicator.className = 'sage-ai-context-indicator';
    cell.node.appendChild(indicator);

    const badge = document.createElement('div');
    badge.className = 'sage-ai-context-badge';
    badge.textContent = 'In Context';
    cell.node.appendChild(badge);
  }
}

/**
 * Create placeholder for empty cells
 */
export function createCellPlaceholder(cell: Cell): void {
  const existing = cell.node.querySelector('.sage-ai-placeholder-quick-gen');
  if (existing) return;

  const placeholder = document.createElement('span');
  placeholder.className = 'sage-ai-placeholder-quick-gen';

  if (cell.model.sharedModel.source) {
    placeholder.classList.add('sage-ai-placeholder-quick-gen-hidden');
  }

  const { modifier, key } = getKeyboardShortcutLabel();

  const quickGenButton = document.createElement('a');
  quickGenButton.className = 'sage-ai-placeholder-quick-gen-button';
  quickGenButton.textContent = `Inline Edit (${modifier} ${key})`;

  placeholder.textContent = 'Start coding or use ';
  placeholder.append(quickGenButton);

  quickGenButton.addEventListener('click', ev => {
    ev.stopPropagation();
    const generateButton = cell.node.querySelector(
      '.sage-ai-quick-generation'
    ) as HTMLElement;
    const isOpen = cell.node.querySelector(
      '.sage-ai-quick-gen-prompt-container'
    );

    if (generateButton && !isOpen) {
      generateButton.click();
    }
  });

  placeholder.addEventListener('click', () => {
    const editor = cell.node.querySelector('.cm-content') as HTMLElement;
    editor?.focus();
  });

  cell.node.append(placeholder);
}

/**
 * Setup listener for cell content changes to toggle placeholder
 */
export function setupPlaceholderListener(cell: Cell): void {
  cell.model.contentChanged.connect(ev => {
    const sageEditButton = cell.node.querySelector('.sage-ai-quick-generation');
    const hasContent = ev.sharedModel.source;
    const placeholder = cell.node.querySelector(
      '.sage-ai-placeholder-quick-gen'
    ) as HTMLElement;
    const isPlaceholderHidden = placeholder?.classList.contains(
      'sage-ai-placeholder-quick-gen-hidden'
    );

    if (!hasContent && isPlaceholderHidden) {
      placeholder?.classList.remove('sage-ai-placeholder-quick-gen-hidden');
      sageEditButton?.classList.add('sage-ai-quick-generation-hidden');
      return;
    }

    if (hasContent) {
      placeholder?.classList.add('sage-ai-placeholder-quick-gen-hidden');
      sageEditButton?.classList.remove('sage-ai-quick-generation-hidden');
    }
  });
}

/**
 * Create the quick generation input UI
 */
function createQuickGenUI(
  cell: Cell,
  config: CellContextUIConfig,
  generateButton: HTMLElement,
  buttonsContainer: HTMLElement
): void {
  const isBoxOpened = cell.node.querySelector(
    '.sage-ai-quick-gen-prompt-container'
  );
  if (isBoxOpened) return;

  generateButton.classList.add('sage-ai-quick-generation-hidden');

  // Create container elements
  const quickGenContainer = document.createElement('div');
  quickGenContainer.className = 'sage-ai-quick-gen-prompt-container';

  const loader = document.createElement('div');
  loader.className = 'sage-ai-blob-loader';
  loader.style.display = 'none';

  const inputContainer = document.createElement('div');
  inputContainer.className = 'sage-ai-quick-gen-prompt-input-container';

  const promptInput = document.createElement('input');
  promptInput.className = 'sage-ai-prompt-input';
  promptInput.placeholder = 'Edit selected lines or the whole cell';

  const errorMessage = document.createElement('span');
  errorMessage.className =
    'sage-ai-quick-gen-prompt-error-message sage-ai-quick-gen-prompt-error-message-hidden';
  errorMessage.textContent = 'An unexpected error occurred, please try again.';

  inputContainer.append(promptInput, errorMessage);

  // Cancel button
  const cancelButton = document.createElement('span');
  cancelButton.className = 'sage-ai-quick-gen-cancel';
  cancelButton.innerHTML = CANCEL_ICON;

  const cellInputAreaEditor = cell.node.querySelector(
    '.jp-InputArea-editor'
  ) as HTMLElement;
  const cellInputArea = cell.node.querySelector('.jp-InputArea');

  cancelButton.addEventListener('click', () => {
    const chatService = getChatService();
    const abortController = config.getAbortController();

    if (abortController && !abortController.signal.aborted) {
      chatService.cancelRequest();
      config.setAbortController(null);
      return;
    }

    container.remove();
    cellInputArea?.appendChild(cellInputAreaEditor);
    buttonsContainer.classList.remove('sage-ai-buttons-hidden');
    cell.node.classList.remove('sage-ai-quick-gen-active');

    if (cell.model.sharedModel.source) {
      generateButton.classList.remove('sage-ai-quick-generation-hidden');
    }
  });

  // Undo button
  const undoButton = document.createElement('button');
  undoButton.className = 'sage-ai-quick-gen-undo';
  undoButton.disabled = true;
  undoButton.innerHTML = UNDO_ICON;
  undoButton.title = 'Undo AI changes';
  undoButton.addEventListener('click', () => {
    if (config.historyManager.handleUndo(cell)) {
      updateUndoButtonState(cell, config.historyManager);
    }
  });

  // Submit button
  const submitButton = document.createElement('button');
  submitButton.className = 'sage-ai-quick-gen-submit';
  submitButton.style.cursor = 'pointer';
  submitButton.innerHTML = SUBMIT_ICON;
  submitButton.addEventListener('click', () => {
    void handlePromptSubmit(config.quickGenConfig, cell, promptInput.value);
  });

  quickGenContainer.append(
    inputContainer,
    loader,
    undoButton,
    submitButton,
    cancelButton
  );

  const container = document.createElement('div');
  container.className = 'sage-ai-quick-gen-container';

  if (!cellInputAreaEditor) {
    throw new Error("Couldn't find the cell input area editor element");
  }

  container.append(quickGenContainer, cellInputAreaEditor);

  if (!cellInputArea) {
    throw new Error("Couldn't find the cell input area element");
  }

  cellInputArea.appendChild(container);
  cell.node.classList.add('sage-ai-quick-gen-active');
  promptInput.focus();

  // Submit on Enter
  promptInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handlePromptSubmit(config.quickGenConfig, cell, promptInput.value);
    }
  });
}

/**
 * Add context buttons to a single cell
 */
export function addContextButtonsToCell(
  cell: Cell,
  trackingId: string,
  notebookPath: string,
  isInContext: boolean,
  config: CellContextUIConfig,
  refreshHighlighting: () => void
): void {
  // Remove existing buttons
  const existingButtons = cell.node.querySelector('.sage-ai-context-buttons');
  if (existingButtons) {
    existingButtons.remove();
  }

  const buttonsContainer = document.createElement('div');
  buttonsContainer.className = 'sage-ai-context-buttons';

  if (isInContext) {
    // Remove button
    const removeButton = document.createElement('button');
    removeButton.className = 'sage-ai-remove-button';
    removeButton.textContent = 'Remove from Chat';
    removeButton.addEventListener('click', e => {
      e.stopPropagation();
      e.preventDefault();

      config.notebookContextManager.removeCellFromContext(
        notebookPath,
        trackingId
      );
      highlightCell(cell, false);
      refreshHighlighting();

      if (config.chatContainerRef && !config.chatContainerRef.isDisposed) {
        config.chatContainerRef.onCellRemovedFromContext(
          notebookPath,
          trackingId
        );
      }
    });
    buttonsContainer.appendChild(removeButton);
    cell.node.classList.add('sage-ai-in-context-cell');
  } else {
    // Add button
    const addButton = document.createElement('button');
    addButton.className = 'sage-ai-add-button';
    addButton.innerHTML = `${ADD_ICON} Add to Context`;
    addButton.addEventListener('click', e => {
      e.stopPropagation();
      e.preventDefault();

      const cellContent = cell.model.sharedModel.getSource();
      const cellType = cell.model.type;

      config.notebookContextManager.addCellToContext(
        notebookPath,
        trackingId,
        trackingId,
        cellContent,
        cellType
      );

      refreshHighlighting();

      if (config.chatContainerRef && !config.chatContainerRef.isDisposed) {
        config.chatContainerRef.onCellAddedToContext(notebookPath, trackingId);
      }
    });
    buttonsContainer.appendChild(addButton);
    cell.node.classList.remove('sage-ai-in-context-cell');
  }

  // Quick generation button (if not already open)
  const quickGen = cell.node.querySelector('.sage-ai-quick-gen-container');
  if (!quickGen) {
    const generateButton = document.createElement('button');
    generateButton.className = 'sage-ai-quick-generation';
    const { modifier, key } = getKeyboardShortcutLabel();
    generateButton.append(`Inline Edit (${modifier} ${key})`);
    buttonsContainer.appendChild(generateButton);

    if (!cell.model.sharedModel.source) {
      generateButton.classList.add('sage-ai-quick-generation-hidden');
    }

    generateButton.addEventListener('click', () => {
      createQuickGenUI(cell, config, generateButton, buttonsContainer);
    });
  }

  // Cmd+K keyboard shortcut
  if (!config.cellsWithKeydownListener.has(cell.node)) {
    cell.node.addEventListener('keydown', event => {
      if (
        (event.metaKey || event.ctrlKey) &&
        (event.key === 'k' || event.key === 'K')
      ) {
        if (!cell.node.classList.contains('jp-mod-active')) return;

        event.preventDefault();
        event.stopPropagation();

        const isBoxOpened = cell.node.querySelector(
          '.sage-ai-quick-gen-prompt-container'
        );
        if (isBoxOpened) return;

        const generateButton = cell.node.querySelector(
          '.sage-ai-quick-generation'
        ) as HTMLButtonElement;
        generateButton?.click();
      }
    });
    config.cellsWithKeydownListener.add(cell.node);
  }

  try {
    createCellPlaceholder(cell);
    setupPlaceholderListener(cell);
  } catch (e) {
    console.error(`Couldn't setup placeholder: ${e}`);
  }

  cell.node.appendChild(buttonsContainer);
}

/**
 * Add context buttons to all cells in a notebook
 */
export function addContextButtonsToAllCells(
  notebook: NotebookPanel,
  notebookPath: string,
  config: CellContextUIConfig,
  refreshHighlighting: () => void
): void {
  const cells = notebook.content.widgets;

  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i];
    const metadata: any = cell.model.sharedModel.getMetadata() || {};
    const trackingId = metadata.cell_tracker?.trackingId;

    // Remove existing ID label
    const existingIdLabel = cell.node.querySelector('.sage-ai-cell-id-label');
    if (existingIdLabel) {
      existingIdLabel.remove();
    }

    if (trackingId) {
      // Add cell ID label
      const idLabel = document.createElement('div');
      idLabel.setAttribute('sage-ai-cell-id', trackingId);
      idLabel.className = 'sage-ai-cell-id-label';
      if (trackingId === 'planning_cell') {
        idLabel.className += ' sage-ai-plan-label';
      }
      idLabel.textContent = trackingId;
      cell.node.appendChild(idLabel);

      const isInContext = config.notebookContextManager.isCellInContext(
        notebookPath,
        trackingId
      );

      addContextButtonsToCell(
        cell,
        trackingId,
        notebookPath,
        isInContext,
        config,
        refreshHighlighting
      );
    }
  }
}
