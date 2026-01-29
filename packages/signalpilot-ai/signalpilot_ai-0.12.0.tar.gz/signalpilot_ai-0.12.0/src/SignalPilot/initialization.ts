/**
 * SignalPilot Initialization Module
 *
 * Handles core service initialization including:
 * - Caching services (settings and StateDB)
 * - Database state
 * - JWT authentication
 * - Snippets loading
 * - Workspace context fetching
 */

import {
  startTimer,
  endTimer,
  trackSubscription
} from '../utils/performanceDebug';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IThemeManager } from '@jupyterlab/apputils';
import { INotebookTracker } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';
import { ListModel } from '@jupyterlab/extensionmanager';

import { CachingService, SETTING_KEYS } from '../utils/caching';
import { StateDBCachingService } from '../utils/backendCaching';
import { useServicesStore } from '../stores/servicesStore';
import { setWorkspaceContext } from '../stores/appStore';
import { useAppStore } from '../stores/appStore';
import { useSnippetStore } from '../stores/snippetStore';
import { ConfigService } from '../Config/ConfigService';
import { ToolService } from '../LLM/ToolService';
import { NotebookContextManager } from '../Notebook/NotebookContextManager';
import { ActionHistory } from '@/ChatBox/services/ActionHistory';
import { NotebookTools } from '../Notebook/NotebookTools';
import { CellTrackingService } from '../Services/CellTrackingService';
import { TrackingIDUtility } from '../utils/TrackingIDUtility';
import { ContextCellHighlighter } from '../Jupyter';
import { TabCompletionService } from '../Services/TabCompletionService';
import { CompletionManager } from '../Services/CompletionManager';
import { DatabaseMetadataCache } from '../stores/databaseMetadataCacheStore';
import { ContextCacheService } from '@/ChatBox/Context/ContextCacheService';
import { KernelExecutionListener } from '@/ChatBox/Context/KernelExecutionListener';
import { CloudUploadService } from '../Services/CloudUploadService';
import { JWTAuthModalService } from '../Services/JWTAuthModalService';
import { PlanStateDisplay } from '@/ChatBox/StateDisplay/PlanStateDisplay';
import { LLMStateDisplay } from '@/ChatBox/StateDisplay/LLMStateDisplay';
import { WaitingUserReplyBoxManager } from '../Notebook/WaitingUserReplyBoxManager';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { NotebookDiffTools } from '../Notebook/NotebookDiffTools';
import { KernelUtils } from '../utils/kernelUtils';

export interface InitializationContext {
  app: JupyterFrontEnd;
  notebooks: INotebookTracker;
  themeManager: IThemeManager;
  db: IStateDB;
  documentManager: IDocumentManager;
  settingRegistry: ISettingRegistry | null;
  replayId: string | null;
}

export interface CoreServices {
  toolService: ToolService;
  notebookContextManager: NotebookContextManager;
  actionHistory: ActionHistory;
  notebookTools: NotebookTools;
  planStateDisplay: PlanStateDisplay;
  llmStateDisplay: LLMStateDisplay;
  waitingUserReplyBoxManager: WaitingUserReplyBoxManager;
  cellTrackingService: CellTrackingService;
  trackingIDUtility: TrackingIDUtility;
  contextCellHighlighter: ContextCellHighlighter;
  diffManager: NotebookDiffManager;
}

/**
 * Initialize all caching services
 */
export async function initializeCaching(
  settingRegistry: ISettingRegistry | null
): Promise<void> {
  startTimer('initializeCaching');
  // Initialize the caching service with settings registry
  CachingService.initialize(settingRegistry);

  // Initialize the state database caching service for chat histories
  StateDBCachingService.initialize();

  // Move old chat histories to StateDB
  const moveToChatHistory = async () => {
    const oldHistories = await CachingService.getSetting(
      SETTING_KEYS.CHAT_HISTORIES,
      {}
    );
    if (oldHistories && Object.keys(oldHistories).length > 0) {
      console.log('MOVING ALL SETTINGS TO THE STATE DB');
      await StateDBCachingService.setValue(
        SETTING_KEYS.CHAT_HISTORIES,
        oldHistories
      );
      console.log('SUCCESSFULLY MOVED ALL SETTINGS TO THE STATE DB');
      await CachingService.setSetting(SETTING_KEYS.CHAT_HISTORIES, {});
    }
  };

  void moveToChatHistory();
  endTimer('initializeCaching');
}

/**
 * Initialize demo mode and database state service
 */
export async function initializeDemoMode(
  replayId: string | null
): Promise<void> {
  startTimer('initializeDemoMode');
  // Load demo mode from cache on startup
  await useAppStore.getState().loadDemoMode();

  // If replay is present, set demo mode to true
  if (replayId) {
    console.log('[Replay] Setting demo mode to true');
    await useAppStore.getState().setDemoMode(true);
  }

  // Initialize the database state service with StateDB (async, non-blocking)
  console.log('[Plugin] Initializing database state service...');
  void import('../stores/databaseStore').then(({ DatabaseStateService }) => {
    DatabaseStateService.initializeWithStateDB().catch(error => {
      console.warn(
        '[Plugin] Database state service initialization failed:',
        error
      );
    });
  });
  endTimer('initializeDemoMode');
}

/**
 * Initialize JWT authentication
 */
export async function initializeAuthentication(): Promise<void> {
  startTimer('initializeAuthentication');
  console.log('[Plugin] Initializing JWT authentication on startup...');
  try {
    const jwtInitialized = await JWTAuthModalService.initializeJWTOnStartup();
    if (jwtInitialized) {
      console.log(
        '[Plugin] JWT authentication initialized successfully on startup'
      );

      // Load user profile if authenticated
      try {
        const { JupyterAuthService } =
          await import('../Services/JupyterAuthService');
        const isAuthenticated = await JupyterAuthService.isAuthenticated();

        if (isAuthenticated) {
          const userProfile = await JupyterAuthService.getUserProfile();
          useAppStore.getState().setUserProfile(userProfile);
          console.log('[Plugin] User profile loaded and stored in useAppStore');
        }
      } catch (profileError) {
        console.warn('[Plugin] Failed to load user profile:', profileError);
      }
    } else {
      console.log('[Plugin] No JWT token found during startup initialization');
    }
  } catch (error) {
    console.error('[Plugin] Failed to initialize JWT on startup:', error);
  }
  endTimer('initializeAuthentication');
}

/**
 * Load snippets and inserted snippets from StateDB
 */
export async function loadSnippets(): Promise<void> {
  // Load both snippets and inserted snippets from StateDB via snippet store
  useSnippetStore
    .getState()
    .loadFromStateDB()
    .catch(error => {
      console.warn('[Plugin] Failed to load snippets from StateDB:', error);
    });
}

/**
 * Initialize AppState with registry and extensions
 */
export function initializeAppState(
  app: JupyterFrontEnd,
  settingRegistry: ISettingRegistry | null
): void {
  // Store settings registry in servicesStore
  // Note: This is stored here and will be passed to initializeCoreServices later
  // For now, we'll store it in a module-level variable
  const serviceManager = app.serviceManager;

  // Store service manager in servicesStore
  useServicesStore.getState().setServiceManager(serviceManager);

  const extensions = new ListModel(serviceManager as any);

  // Store extensions in servicesStore for UpdateBanner to use
  useServicesStore.getState().setExtensions(extensions);
}

/**
 * Set dark theme if not already set
 */
export async function initializeTheme(
  themeManager: IThemeManager
): Promise<void> {
  const checkAndSetTheme = async () => {
    const alreadySet = await CachingService.getBooleanSetting(
      SETTING_KEYS.DARK_THEME_APPLIED,
      false
    );
    if (!alreadySet) {
      console.log('Setting theme to JupyterLab Dark (first time)');
      void themeManager.setTheme('JupyterLab Dark');
      await CachingService.setBooleanSetting(
        SETTING_KEYS.DARK_THEME_APPLIED,
        true
      );
    }
  };
  void checkAndSetTheme();
}

/**
 * Load and configure settings from registry
 */
export function loadSettings(
  settingRegistry: ISettingRegistry | null,
  pluginId: string
): void {
  if (settingRegistry) {
    settingRegistry
      .load(pluginId)
      .then(settings => {
        console.log('Loaded settings for signalpilot-ai');
        const defaultService = settings.get('defaultService')
          .composite as string;
        // Store the default service in ConfigService
        if (defaultService) {
          ConfigService.setActiveModelType(defaultService);
        }

        // Watch for setting changes
        settings.changed.connect(() => {
          const newDefaultService = settings.get('defaultService')
            .composite as string;
          ConfigService.setActiveModelType(newDefaultService);
          console.log(`Default service changed to ${newDefaultService}`);
        });
      })
      .catch(error => {
        console.error('Failed to load settings for signalpilot-ai', error);
      });
  }
}

/**
 * Fetch and cache workspace context
 */
export async function fetchWorkspaceContext(): Promise<void> {
  try {
    const { requestAPI } = await import('../utils/handler');
    const workspaceData = await requestAPI<any>('read-all-files');
    setWorkspaceContext(workspaceData);
    console.log('[Plugin] Workspace context cached at startup');
  } catch (error) {
    console.warn('[Plugin] Failed to fetch workspace context:', error);
  }
}

/**
 * Initialize all core services and components
 */
export function initializeCoreServices(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  documentManager: IDocumentManager,
  settingsRegistry?: ISettingRegistry | null
): CoreServices {
  startTimer('initializeCoreServices');
  const contentManager = app.serviceManager.contents;

  // Create shared instances
  const planStateDisplay = new PlanStateDisplay();
  const llmStateDisplay = new LLMStateDisplay();
  const waitingUserReplyBoxManager = new WaitingUserReplyBoxManager();
  const toolService = new ToolService();
  const notebookTools = new NotebookTools(
    notebooks,
    waitingUserReplyBoxManager
  );
  const notebookContextManager = new NotebookContextManager(toolService);
  const actionHistory = new ActionHistory();

  // Configure tool service
  toolService.setNotebookTracker(notebooks, waitingUserReplyBoxManager);
  toolService.setContentManager(contentManager);
  toolService.setContextManager(notebookContextManager);

  // Initialize the servicesStore with core services
  useServicesStore.getState().initializeCoreServices({
    toolService,
    notebookTracker: notebooks,
    notebookTools,
    notebookContextManager,
    contentManager,
    documentManager,
    settingsRegistry: settingsRegistry ?? null
  });

  // Initialize managers in servicesStore
  useServicesStore.getState().initializeManagers({
    planStateDisplay,
    llmStateDisplay,
    waitingUserReplyBoxManager
  });

  // Initialize additional services
  const cellTrackingService = new CellTrackingService(notebookTools, notebooks);
  const trackingIDUtility = new TrackingIDUtility(notebooks);
  const contextCellHighlighter = new ContextCellHighlighter(
    notebooks,
    notebookContextManager,
    notebookTools
  );

  useServicesStore.getState().initializeAdditionalServices({
    actionHistory,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter
  });

  // Initialize NotebookDiffManager
  const diffManager = new NotebookDiffManager(notebookTools, actionHistory);
  useServicesStore.getState().initializeManagers({
    planStateDisplay,
    llmStateDisplay,
    waitingUserReplyBoxManager,
    notebookDiffManager: diffManager
  });

  // Initialize diff2html theme detection
  NotebookDiffTools.initializeThemeDetection();

  endTimer('initializeCoreServices');

  return {
    toolService,
    notebookContextManager,
    actionHistory,
    notebookTools,
    planStateDisplay,
    llmStateDisplay,
    waitingUserReplyBoxManager,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter,
    diffManager
  };
}

/**
 * Initialize async services (tab completion, cloud upload, database cache, etc.)
 */
export async function initializeAsyncServices(
  notebooks: INotebookTracker
): Promise<void> {
  startTimer('initializeAsyncServices');
  // Initialize tab completion service (async, non-blocking)
  const tabCompletionService = TabCompletionService.getInstance();
  tabCompletionService.initialize().catch(error => {
    console.warn(
      '[Plugin] Tab completion service initialization failed:',
      error
    );
  });

  // Initialize cloud upload services (async, non-blocking)
  const cloudUploadService = CloudUploadService.getInstance();
  Promise.all([cloudUploadService.initialize()]).catch(error => {
    console.warn(
      '[Plugin] Cloud upload services initialization failed:',
      error
    );
  });

  // Initialize completion manager
  const completionManager = CompletionManager.getInstance();
  completionManager.initialize(notebooks);

  // Initialize database metadata cache (async, non-blocking)
  const databaseCache = DatabaseMetadataCache.getInstance();
  databaseCache.initializeOnStartup().catch(error => {
    console.warn('[Plugin] Database cache initialization failed:', error);
  });

  // Initialize context cache service and kernel execution listener
  // Note: Core services (toolService, contentManager) are already initialized
  // by initializeCoreServices() before this function is called
  const contextCacheService = ContextCacheService.getInstance();
  const kernelExecutionListener = KernelExecutionListener.getInstance();

  // Initialize context services directly (no setTimeout needed)
  // Core services are guaranteed to be available at this point
  (async () => {
    startTimer('initializeAsyncServices.contextInit');
    try {
      await contextCacheService.initialize();
      console.log('[Plugin] Context cache service initialized');

      // Initialize kernel execution listener after context cache service
      await kernelExecutionListener.initialize(notebooks);
      console.log('[Plugin] Kernel execution listener initialized');

      // Start initial context loading (non-blocking)
      console.log('[Plugin] Starting initial context loading...');
      contextCacheService.loadAllContexts().catch(error => {
        console.warn('[Plugin] Initial context loading failed:', error);
      });

      // Subscribe to notebook changes for context refreshing
      trackSubscription('Plugin.contextCacheNotebookSubscription');
      contextCacheService.subscribeToNotebookChanges();
    } catch (error) {
      console.warn(
        '[Plugin] Context cache service initialization failed:',
        error
      );
    }
    endTimer('initializeAsyncServices.contextInit');
  })();

  endTimer('initializeAsyncServices');
}

/**
 * Set up debug utilities on window object
 */
export function setupDebugUtilities(notebooks: INotebookTracker): void {
  const databaseCache = DatabaseMetadataCache.getInstance();
  const contextCacheService = ContextCacheService.getInstance();
  const kernelExecutionListener = KernelExecutionListener.getInstance();

  if (!(window as any).debugDBURL) {
    (window as any).debugDBURL = {
      check: () => KernelUtils.checkDbUrlInKernel(),
      debug: () => KernelUtils.debugAppStateDatabaseUrl(),
      set: (url?: string) => KernelUtils.setDbUrlInKernel(url),
      retry: () => KernelUtils.setDbUrlInKernelWithRetry(),
      setAllDatabases: () => KernelUtils.setDatabaseEnvironmentsInKernel(),
      retryAllDatabases: () =>
        KernelUtils.setDatabaseEnvironmentsInKernelWithRetry()
    };
  }

  if (!(window as any).debugDBCache) {
    (window as any).debugDBCache = {
      getStatus: () => databaseCache.getCacheStatus(),
      refresh: () => databaseCache.refreshMetadata(),
      clear: () => databaseCache.clearCache(),
      onKernelReady: () => databaseCache.onKernelReady(),
      onSettingsChanged: () => databaseCache.onSettingsChanged()
    };
  }

  if (!(window as any).debugContextCache) {
    (window as any).debugContextCache = {
      getContexts: () => contextCacheService.getContexts(),
      refresh: () => contextCacheService.forceRefresh()
    };
  }

  if (!(window as any).debugKernelListener) {
    (window as any).debugKernelListener = {
      getDebugInfo: () => kernelExecutionListener.getDebugInfo(),
      triggerRefresh: () => kernelExecutionListener.triggerVariableRefresh(),
      dispose: () => kernelExecutionListener.dispose(),
      reinitialize: () => kernelExecutionListener.initialize(notebooks)
    };
  }

  if (!(window as any).debugLoginSuccess) {
    (window as any).debugLoginSuccess = {
      show: async () => {
        try {
          const { LoginSuccessModalService } =
            await import('../Services/LoginSuccessModalService');
          LoginSuccessModalService.debugShow();
          console.log('✅ Login success modal triggered from debug');
        } catch (error) {
          console.error('❌ Failed to show login success modal:', error);
        }
      },
      getDebugInfo: async () => {
        try {
          const { LoginSuccessModalService } =
            await import('../Services/LoginSuccessModalService');
          const instance = LoginSuccessModalService.getInstance();
          return instance.getDebugInfo();
        } catch (error) {
          console.error('❌ Failed to get debug info:', error);
          return null;
        }
      }
    };
  }

  if (!(window as any).debugJWTAuth) {
    (window as any).debugJWTAuth = {
      show: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.show();
        console.log('✅ JWT auth modal shown from debug');
      },
      hide: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.hide();
        console.log('✅ JWT auth modal hidden from debug');
      },
      forceShow: () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        jwtModalService.forceShow();
        console.log('✅ JWT auth modal force shown from debug');
      },
      checkAndHide: async () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        await jwtModalService.checkAndHideIfAuthenticated();
        console.log('✅ JWT auth modal check and hide completed');
      },
      getDebugInfo: async () => {
        const jwtModalService = JWTAuthModalService.getInstance();
        return await jwtModalService.getDebugInfo();
      }
    };
  }
}
