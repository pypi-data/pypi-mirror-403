/**
 * Jupyter Diff Module
 *
 * JupyterLab-specific code for diff visualization in notebook cells.
 * This code MUST use DOM APIs because it integrates with JupyterLab's
 * Cell and CodeMirror editor components which are Lumino widgets.
 *
 * For pure React diff components, see src/ChatBox/Diff/
 */

export * from './InlineDiffService';
export * from './CellDiffOverlay';
export * from './DiffClassManager';
