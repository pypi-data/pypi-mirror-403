/**
 * Jupyter-specific utilities
 *
 * This module contains code that directly interacts with JupyterLab's
 * notebook DOM structure. These utilities are intentionally kept as
 * imperative DOM manipulation code because JupyterLab cells are not
 * React-controlled.
 */

// Re-export everything from ContextHighlighter module
export * from './ContextHighlighter';

// Re-export WelcomeCTA mounting utilities
export * from './WelcomeCTA';

// Re-export DemoOverlays utilities
export * from './DemoOverlays';
