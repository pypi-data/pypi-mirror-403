/**
 * ServicesStore
 *
 * Centralized Zustand store for all service references.
 * Replaces the service getter pattern from AppStateService.
 *
 * Services are initialized during app startup and remain stable.
 * This store provides:
 * - Typed service references
 * - Safe getters that throw if service not initialized
 * - Non-React access via getServicesState()
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { INotebookTracker } from '@jupyterlab/notebook';
import { Contents, ServiceManager } from '@jupyterlab/services';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { ListModel } from '@jupyterlab/extensionmanager';

import { ToolService } from '../LLM/ToolService';
import { IChatService } from '../LLM/IChatService';
import { IConfig } from '../Config/ConfigService';
import { NotebookTools } from '../Notebook/NotebookTools';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { PlanStateDisplay } from '@/ChatBox/StateDisplay/PlanStateDisplay';
import { LLMStateDisplay } from '@/ChatBox/StateDisplay/LLMStateDisplay';
import { WaitingUserReplyBoxManager } from '../Notebook/WaitingUserReplyBoxManager';
import { ActionHistory } from '@/ChatBox/services/ActionHistory';
import { CellTrackingService } from '../Services/CellTrackingService';
import { TrackingIDUtility } from '../utils/TrackingIDUtility';
import { ContextCellHighlighter } from '../Jupyter';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IServicesState {
  // Core JupyterLab services
  notebookTracker: INotebookTracker | null;
  contentManager: Contents.IManager | null;
  documentManager: IDocumentManager | null;
  serviceManager: ServiceManager.IManager | null;
  settingsRegistry: ISettingRegistry | null;
  extensions: ListModel | null;

  // LLM services
  toolService: ToolService | null;
  chatService: IChatService | null;
  config: IConfig | null;

  // Notebook services
  notebookTools: NotebookTools | null;
  notebookContextManager: NotebookContextManager | null;
  notebookDiffManager: NotebookDiffManager | null;

  // State displays
  planStateDisplay: PlanStateDisplay | null;
  llmStateDisplay: LLMStateDisplay | null;

  // Managers
  waitingUserReplyBoxManager: WaitingUserReplyBoxManager | null;

  // Additional services
  actionHistory: ActionHistory | null;
  cellTrackingService: CellTrackingService | null;
  trackingIDUtility: TrackingIDUtility | null;
  contextCellHighlighter: ContextCellHighlighter | null;

  // Widget references
  fileExplorerWidget: any | null;
  databaseManagerWidget: any | null;
  diffNavigationWidget: any | null;

  // All widgets container (for bulk access)
  widgets: {
    tracker?: any;
    settingsContainer?: any;
    snippetCreationWidget?: any;
    diffNavigationWidget?: any;
    databaseManagerWidget?: any;
    fileExplorerWidget?: any;
    mcpManagerWidget?: any;
  } | null;

  // Initialization flag
  isInitialized: boolean;
}

export interface IServicesActions {
  // Batch setters for initialization phases
  initializeCoreServices: (services: {
    toolService: ToolService;
    notebookTracker: INotebookTracker;
    notebookTools: NotebookTools;
    notebookContextManager: NotebookContextManager;
    contentManager: Contents.IManager;
    documentManager: IDocumentManager;
    settingsRegistry?: ISettingRegistry | null;
  }) => void;

  initializeManagers: (managers: {
    planStateDisplay: PlanStateDisplay;
    llmStateDisplay: LLMStateDisplay;
    waitingUserReplyBoxManager: WaitingUserReplyBoxManager;
    notebookDiffManager?: NotebookDiffManager;
  }) => void;

  initializeAdditionalServices: (services: {
    actionHistory: ActionHistory;
    cellTrackingService: CellTrackingService;
    trackingIDUtility: TrackingIDUtility;
    contextCellHighlighter: ContextCellHighlighter;
  }) => void;

  // Individual setters
  setServiceManager: (serviceManager: ServiceManager.IManager) => void;
  setExtensions: (extensions: ListModel) => void;
  setChatService: (chatService: IChatService) => void;
  setConfig: (config: IConfig) => void;

  // Widget setters
  setFileExplorerWidget: (widget: any) => void;
  setDatabaseManagerWidget: (widget: any) => void;
  setDiffNavigationWidget: (widget: any) => void;
  setWidgets: (widgets: IServicesState['widgets']) => void;

  // Mark as fully initialized
  markInitialized: () => void;
}

type IServicesStore = IServicesState & IServicesActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialState: IServicesState = {
  // Core JupyterLab services
  notebookTracker: null,
  contentManager: null,
  documentManager: null,
  serviceManager: null,
  settingsRegistry: null,
  extensions: null,

  // LLM services
  toolService: null,
  chatService: null,
  config: null,

  // Notebook services
  notebookTools: null,
  notebookContextManager: null,
  notebookDiffManager: null,

  // State displays
  planStateDisplay: null,
  llmStateDisplay: null,

  // Managers
  waitingUserReplyBoxManager: null,

  // Additional services
  actionHistory: null,
  cellTrackingService: null,
  trackingIDUtility: null,
  contextCellHighlighter: null,

  // Widget references
  fileExplorerWidget: null,
  databaseManagerWidget: null,
  diffNavigationWidget: null,

  // All widgets container
  widgets: null,

  // Initialization flag
  isInitialized: false
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useServicesStore = create<IServicesStore>()(
  subscribeWithSelector(set => ({
    ...initialState,

    // ─────────────────────────────────────────────────────────────
    // Batch Setters
    // ─────────────────────────────────────────────────────────────

    initializeCoreServices: services => {
      set({
        toolService: services.toolService,
        notebookTracker: services.notebookTracker,
        notebookTools: services.notebookTools,
        notebookContextManager: services.notebookContextManager,
        contentManager: services.contentManager,
        documentManager: services.documentManager,
        settingsRegistry: services.settingsRegistry || null
      });
      console.log('[ServicesStore] Core services initialized');
    },

    initializeManagers: managers => {
      set({
        planStateDisplay: managers.planStateDisplay,
        llmStateDisplay: managers.llmStateDisplay,
        waitingUserReplyBoxManager: managers.waitingUserReplyBoxManager,
        notebookDiffManager: managers.notebookDiffManager || null
      });
      console.log('[ServicesStore] Managers initialized');
    },

    initializeAdditionalServices: services => {
      set({
        actionHistory: services.actionHistory,
        cellTrackingService: services.cellTrackingService,
        trackingIDUtility: services.trackingIDUtility,
        contextCellHighlighter: services.contextCellHighlighter
      });
      console.log('[ServicesStore] Additional services initialized');
    },

    // ─────────────────────────────────────────────────────────────
    // Individual Setters
    // ─────────────────────────────────────────────────────────────

    setServiceManager: serviceManager => {
      set({ serviceManager });
    },

    setExtensions: extensions => {
      set({ extensions });
    },

    setChatService: chatService => {
      set({ chatService });
    },

    setConfig: config => {
      set({ config });
    },

    // ─────────────────────────────────────────────────────────────
    // Widget Setters
    // ─────────────────────────────────────────────────────────────

    setFileExplorerWidget: widget => {
      set({ fileExplorerWidget: widget });
    },

    setDatabaseManagerWidget: widget => {
      set({ databaseManagerWidget: widget });
    },

    setDiffNavigationWidget: widget => {
      set({ diffNavigationWidget: widget });
      console.log('[ServicesStore] DiffNavigationWidget set');
    },

    setWidgets: widgets => {
      set({ widgets });
      console.log('[ServicesStore] All widgets set');
    },

    markInitialized: () => {
      set({ isInitialized: true });
      console.log('[ServicesStore] Fully initialized');
    }
  }))
  // NOTE: No devtools middleware - services are set once and don't need debugging
);

// ═══════════════════════════════════════════════════════════════
// TYPED GETTERS (throw if not initialized)
// ═══════════════════════════════════════════════════════════════

/**
 * Get service state for non-React code.
 * Use this in TypeScript services, not in React components.
 */
export function getServicesState(): IServicesState {
  return useServicesStore.getState();
}

// Core JupyterLab services
export function getToolService(): ToolService {
  const service = useServicesStore.getState().toolService;
  if (!service) {
    throw new Error('[ServicesStore] ToolService not initialized');
  }
  return service;
}

export function getNotebookTracker(): INotebookTracker {
  const service = useServicesStore.getState().notebookTracker;
  if (!service) {
    throw new Error('[ServicesStore] NotebookTracker not initialized');
  }
  return service;
}

export function getNotebookTools(): NotebookTools {
  const service = useServicesStore.getState().notebookTools;
  if (!service) {
    throw new Error('[ServicesStore] NotebookTools not initialized');
  }
  return service;
}

export function getNotebookContextManager(): NotebookContextManager {
  const service = useServicesStore.getState().notebookContextManager;
  if (!service) {
    throw new Error('[ServicesStore] NotebookContextManager not initialized');
  }
  return service;
}

export function getContentManager(): Contents.IManager {
  const service = useServicesStore.getState().contentManager;
  if (!service) {
    throw new Error('[ServicesStore] ContentManager not initialized');
  }
  return service;
}

export function getDocumentManager(): IDocumentManager {
  const service = useServicesStore.getState().documentManager;
  if (!service) {
    throw new Error('[ServicesStore] DocumentManager not initialized');
  }
  return service;
}

export function getServiceManager(): ServiceManager.IManager | null {
  return useServicesStore.getState().serviceManager;
}

export function getSettingsRegistry(): ISettingRegistry | null {
  return useServicesStore.getState().settingsRegistry;
}

export function getExtensions(): ListModel | null {
  return useServicesStore.getState().extensions;
}

// LLM services
export function getChatService(): IChatService {
  const service = useServicesStore.getState().chatService;
  if (!service) {
    throw new Error('[ServicesStore] ChatService not initialized');
  }
  return service;
}

export function getConfig(): IConfig {
  const config = useServicesStore.getState().config;
  if (!config) {
    throw new Error('[ServicesStore] Config not initialized');
  }
  return config;
}

// Notebook services
export function getNotebookDiffManager(): NotebookDiffManager {
  const service = useServicesStore.getState().notebookDiffManager;
  if (!service) {
    throw new Error('[ServicesStore] NotebookDiffManager not initialized');
  }
  return service;
}

// State displays
export function getPlanStateDisplay(): PlanStateDisplay {
  const service = useServicesStore.getState().planStateDisplay;
  if (!service) {
    throw new Error('[ServicesStore] PlanStateDisplay not initialized');
  }
  return service;
}

export function getLlmStateDisplay(): LLMStateDisplay {
  const service = useServicesStore.getState().llmStateDisplay;
  if (!service) {
    throw new Error('[ServicesStore] LLMStateDisplay not initialized');
  }
  return service;
}

// Managers
export function getWaitingUserReplyBoxManager(): WaitingUserReplyBoxManager {
  const service = useServicesStore.getState().waitingUserReplyBoxManager;
  if (!service) {
    throw new Error(
      '[ServicesStore] WaitingUserReplyBoxManager not initialized'
    );
  }
  return service;
}

// Additional services
export function getActionHistory(): ActionHistory {
  const service = useServicesStore.getState().actionHistory;
  if (!service) {
    throw new Error('[ServicesStore] ActionHistory not initialized');
  }
  return service;
}

export function getCellTrackingService(): CellTrackingService {
  const service = useServicesStore.getState().cellTrackingService;
  if (!service) {
    throw new Error('[ServicesStore] CellTrackingService not initialized');
  }
  return service;
}

export function getTrackingIDUtility(): TrackingIDUtility {
  const service = useServicesStore.getState().trackingIDUtility;
  if (!service) {
    throw new Error('[ServicesStore] TrackingIDUtility not initialized');
  }
  return service;
}

export function getContextCellHighlighter(): ContextCellHighlighter {
  const service = useServicesStore.getState().contextCellHighlighter;
  if (!service) {
    throw new Error('[ServicesStore] ContextCellHighlighter not initialized');
  }
  return service;
}

// ═══════════════════════════════════════════════════════════════
// SELECTORS (for React components)
// ═══════════════════════════════════════════════════════════════

export const selectIsInitialized = (state: IServicesStore) =>
  state.isInitialized;
export const selectToolService = (state: IServicesStore) => state.toolService;
export const selectNotebookTools = (state: IServicesStore) =>
  state.notebookTools;
export const selectConfig = (state: IServicesStore) => state.config;

// ═══════════════════════════════════════════════════════════════
// WIDGET GETTERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

export function getFileExplorerWidget(): any | null {
  return useServicesStore.getState().fileExplorerWidget;
}

export function getDatabaseManagerWidget(): any | null {
  return useServicesStore.getState().databaseManagerWidget;
}

export function getDiffNavigationWidget(): any | null {
  return useServicesStore.getState().diffNavigationWidget;
}

export function getDiffNavigationWidgetSafe(): any | null {
  const widget = useServicesStore.getState().diffNavigationWidget;
  if (!widget) {
    console.warn('[ServicesStore] DiffNavigationWidget not available');
  }
  return widget;
}

export function setDiffNavigationWidget(widget: any): void {
  useServicesStore.getState().setDiffNavigationWidget(widget);
}

export function setFileExplorerWidget(widget: any): void {
  useServicesStore.getState().setFileExplorerWidget(widget);
}

export function setDatabaseManagerWidget(widget: any): void {
  useServicesStore.getState().setDatabaseManagerWidget(widget);
}
