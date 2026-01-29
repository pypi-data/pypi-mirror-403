/**
 * Context Cell Highlighter
 *
 * Service that manages cell context highlighting and provides UI for:
 * - Adding/removing cells from chat context
 * - Inline editing (Cmd+K quick generation)
 * - Cell content history and undo
 *
 * This is the main coordinator class that uses modular utilities from:
 * - cellHistory.ts: Undo/history management
 * - cellContextUI.ts: UI elements (buttons, highlighting)
 * - quickGeneration.ts: AI inline editing logic
 */

import { INotebookTracker, NotebookPanel } from '@jupyterlab/notebook';
import { NotebookContextManager } from '../../Notebook/NotebookContextManager';
import { NotebookTools } from '../../Notebook/NotebookTools';
import { useNotebookEventsStore } from '../../stores/notebookEventsStore';
import { CellHistoryManager } from './cellHistory';
import {
  addContextButtonsToAllCells,
  CellContextUIConfig,
  highlightCell
} from './cellContextUI';
import { QuickGenConfig } from './quickGeneration';
import { HighlightedCellsMap } from './types';

/**
 * Service that highlights cells that are in context
 * and provides UI to add/remove cells from context and quick generation
 */
export class ContextCellHighlighter {
  private notebookTracker: INotebookTracker;
  private notebookContextManager: NotebookContextManager;
  private notebookTools: NotebookTools;
  private highlightedCells: HighlightedCellsMap = new Map();
  private chatContainerRef: any = null;
  private historyManager: CellHistoryManager;
  private abortController: AbortController | null = null;
  private cellsWithKeydownListener = new WeakSet<HTMLElement>();

  constructor(
    notebookTracker: INotebookTracker,
    notebookContextManager: NotebookContextManager,
    notebookTools: NotebookTools
  ) {
    this.notebookTracker = notebookTracker;
    this.notebookContextManager = notebookContextManager;
    this.notebookTools = notebookTools;
    this.historyManager = new CellHistoryManager();

    // CSS is loaded via style/context-cell-highlighter.css
    this.setupListeners();
  }

  /**
   * Set the chat container reference for updates
   */
  public setChatContainer(container: any): void {
    this.chatContainerRef = container;
  }

  /**
   * Refresh highlighting for a notebook
   */
  public refreshHighlighting(notebook: NotebookPanel): void {
    const notebookPath = this.getNotebookId(notebook);
    this.highlightedCells.delete(notebookPath);
    this.highlightContextCells(notebook);
  }

  /**
   * Add context buttons to all cells in a notebook
   */
  public addContextButtonsToAllCells(notebook: NotebookPanel): void {
    const notebookPath = this.getNotebookId(notebook);
    const { uiConfig } = this.createConfigs();

    addContextButtonsToAllCells(notebook, notebookPath, uiConfig, () =>
      this.refreshHighlighting(this.notebookTracker.currentWidget!)
    );
  }

  /**
   * Set up event listeners for notebook changes
   */
  private setupListeners(): void {
    this.notebookTracker.currentChanged.connect((_, notebook) => {
      if (notebook) {
        this.highlightContextCells(notebook);

        notebook.model?.cells.changed.connect(() => {
          this.refreshHighlighting(notebook);
        });
      }
    });

    // Initial highlight for the current notebook
    if (this.notebookTracker.currentWidget) {
      this.highlightContextCells(this.notebookTracker.currentWidget);
    }
  }

  /**
   * Get the unique notebook ID
   */
  private getNotebookId(notebook: NotebookPanel): string {
    const metadata = notebook.content.model?.sharedModel.getMetadata() as any;

    if (metadata?.sage_ai?.unique_id) {
      return metadata.sage_ai.unique_id;
    }

    const currentNotebookId =
      useNotebookEventsStore.getState().currentNotebookId;
    if (currentNotebookId) {
      return currentNotebookId;
    }

    return notebook.context.path;
  }

  /**
   * Create the configuration objects for UI and quick generation
   */
  private createConfigs(): {
    uiConfig: CellContextUIConfig;
    quickGenConfig: QuickGenConfig;
  } {
    const quickGenConfig: QuickGenConfig = {
      notebookTracker: this.notebookTracker,
      notebookTools: this.notebookTools,
      historyManager: this.historyManager,
      abortController: this.abortController,
      setAbortController: controller => {
        this.abortController = controller;
      }
    };

    const uiConfig: CellContextUIConfig = {
      notebookContextManager: this.notebookContextManager,
      notebookTools: this.notebookTools,
      historyManager: this.historyManager,
      chatContainerRef: this.chatContainerRef,
      cellsWithKeydownListener: this.cellsWithKeydownListener,
      getAbortController: () => this.abortController,
      setAbortController: controller => {
        this.abortController = controller;
      },
      quickGenConfig
    };

    return { uiConfig, quickGenConfig };
  }

  /**
   * Highlight cells that are in context for a specific notebook
   */
  private highlightContextCells(notebook: NotebookPanel): void {
    const notebookPath = this.getNotebookId(notebook);
    if (!notebookPath) return;

    const contextCells =
      this.notebookContextManager.getContextCells(notebookPath);
    const highlightedSet = new Set<string>();
    this.highlightedCells.set(notebookPath, highlightedSet);

    // Highlight context cells
    for (const contextCell of contextCells) {
      const cellId = contextCell.trackingId || contextCell.cellId;
      const cellInfo = this.notebookTools.findCellByAnyId(cellId, notebookPath);

      if (cellInfo) {
        highlightCell(cellInfo.cell, true);
        highlightedSet.add(cellId);
      }
    }

    // Add context buttons to all cells
    this.addContextButtonsToAllCells(notebook);
  }
}
