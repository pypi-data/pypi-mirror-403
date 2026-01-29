/**
 * Types for Jupyter cell context and inline editing
 */

/**
 * Edit operation for line-by-line cell modifications
 */
export interface IEditOperation {
  line: number;
  action: 'KEEP' | 'MODIFY' | 'REMOVE' | 'INSERT';
  content: string;
}

/**
 * Response format for edit_selection mode
 */
export interface IEditSelectionResponse {
  operations: IEditOperation[];
}

/**
 * Cell history entry for undo functionality
 */
export type CellHistoryMap = Map<string, string[]>;

/**
 * Highlighted cells tracking per notebook
 */
export type HighlightedCellsMap = Map<string, Set<string>>;
