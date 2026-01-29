/**
 * Jupyter-specific utilities - Context Highlighter Module
 *
 * This module contains code that directly interacts with JupyterLab's
 * notebook DOM structure. These utilities are intentionally kept as
 * imperative DOM manipulation code because JupyterLab cells are not
 * React-controlled.
 *
 * Module structure:
 * - ContextCellHighlighter.ts: Main coordinator class (~180 lines)
 * - cellContextUI.ts: UI elements for buttons and highlighting (~280 lines)
 * - quickGeneration.ts: AI inline editing logic (~400 lines)
 * - cellHistory.ts: Undo/history management (~100 lines)
 * - icons.ts: SVG icons and keyboard shortcuts (~60 lines)
 * - types.ts: TypeScript interfaces (~30 lines)
 */

// Main class
export { ContextCellHighlighter } from './ContextCellHighlighter';

// UI utilities
export {
  highlightCell,
  createCellPlaceholder,
  setupPlaceholderListener,
  addContextButtonsToCell,
  addContextButtonsToAllCells
} from './cellContextUI';
export type { CellContextUIConfig } from './cellContextUI';

// Quick generation / inline edit
export {
  onPromptSubmit,
  handlePromptSubmit,
  calculateEndLine,
  showDiffView
} from './quickGeneration';
export type { QuickGenConfig } from './quickGeneration';

// Cell history management
export { CellHistoryManager, updateUndoButtonState } from './cellHistory';

// Icons and utilities
export {
  UNDO_ICON,
  SUBMIT_ICON,
  CANCEL_ICON,
  ADD_ICON,
  getKeyboardShortcutLabel
} from './icons';

// Types
export type {
  IEditOperation,
  IEditSelectionResponse,
  CellHistoryMap,
  HighlightedCellsMap
} from './types';
