/**
 * JupyterLabContext
 *
 * React context for providing JupyterLab services to React components.
 * This allows React components to access JupyterLab functionality
 * without importing from AppStateService.
 *
 * Usage:
 * ```tsx
 * // In plugin.ts or initialization
 * <JupyterLabProvider tracker={notebookTracker} app={app}>
 *   <ChatBox />
 * </JupyterLabProvider>
 *
 * // In a component
 * const { notebookTracker, app } = useJupyterLab();
 * ```
 */

import React, { createContext, ReactNode, useContext, useMemo } from 'react';
import { INotebookTracker } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * JupyterLab services available through context
 */
export interface IJupyterLabContext {
  /** Notebook tracker for accessing notebooks */
  notebookTracker: INotebookTracker | null;
  /** JupyterLab application instance */
  app: JupyterFrontEnd | null;
  /** Whether services are available */
  isReady: boolean;
}

/**
 * Props for the JupyterLabProvider
 */
export interface JupyterLabProviderProps {
  children: ReactNode;
  tracker?: INotebookTracker;
  app?: JupyterFrontEnd;
}

// ═══════════════════════════════════════════════════════════════
// CONTEXT
// ═══════════════════════════════════════════════════════════════

const defaultContext: IJupyterLabContext = {
  notebookTracker: null,
  app: null,
  isReady: false
};

const JupyterLabContext = createContext<IJupyterLabContext>(defaultContext);

// ═══════════════════════════════════════════════════════════════
// PROVIDER
// ═══════════════════════════════════════════════════════════════

/**
 * Provider component for JupyterLab services.
 * Wrap your React tree with this to provide JupyterLab access.
 */
export const JupyterLabProvider: React.FC<JupyterLabProviderProps> = ({
  children,
  tracker,
  app
}) => {
  const value = useMemo<IJupyterLabContext>(
    () => ({
      notebookTracker: tracker || null,
      app: app || null,
      isReady: !!(tracker && app)
    }),
    [tracker, app]
  );

  return (
    <JupyterLabContext.Provider value={value}>
      {children}
    </JupyterLabContext.Provider>
  );
};

// ═══════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════

/**
 * Hook to access JupyterLab services from React components.
 *
 * @throws Error if used outside of JupyterLabProvider
 * @returns JupyterLab context with services
 */
export const useJupyterLab = (): IJupyterLabContext => {
  const context = useContext(JupyterLabContext);

  if (context === undefined) {
    throw new Error('useJupyterLab must be used within a JupyterLabProvider');
  }

  return context;
};

/**
 * Hook to access only the notebook tracker.
 * Returns null if not available.
 */
export const useNotebookTracker = (): INotebookTracker | null => {
  const { notebookTracker } = useJupyterLab();
  return notebookTracker;
};

/**
 * Hook to access only the JupyterLab app.
 * Returns null if not available.
 */
export const useJupyterLabApp = (): JupyterFrontEnd | null => {
  const { app } = useJupyterLab();
  return app;
};

// ═══════════════════════════════════════════════════════════════
// EXPORTS
// ═══════════════════════════════════════════════════════════════

export default JupyterLabContext;
