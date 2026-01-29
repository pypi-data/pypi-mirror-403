/**
 * SignalPilot Activation Entry Point
 *
 * IMPORTANT: This activation function is designed to NEVER block the main thread.
 *
 * Architecture:
 * 1. INSTANT PHASE (<10ms) - Synchronous setup, no I/O
 * 2. UI SHELL PHASE (setTimeout 0) - Create empty containers, return fast
 * 3. DEFERRED PHASE (setTimeout 0, scheduled) - Heavy async work
 * 4. BACKGROUND PHASE (requestIdleCallback) - Nice-to-have initializations
 *
 * Key insight: Simply using `void asyncFunc()` does NOT make code non-blocking
 * if the async function does synchronous work before its first internal `await`.
 * We use the DeferredInitScheduler to truly yield to the event loop.
 */

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import {
  ICommandPalette,
  IThemeManager,
  IToolbarWidgetRegistry
} from '@jupyterlab/apputils';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { deferredInit } from '../utils/deferredInit';
import {
  useLoadingStateStore,
  getLoadingState
} from '../stores/loadingStateStore';
import { useAppStore } from '../stores/appStore';
import {
  handleNotebookRestoration,
  handleReplayInitialization,
  handleTakeoverModeReentry
} from './replayHandlers';
import {
  handleNotebookSwitch,
  setupFileChangeDetection,
  setupNotebookTracking
} from './notebookManagement';
import {
  fetchWorkspaceContext,
  initializeAppState,
  initializeAsyncServices,
  initializeAuthentication,
  initializeCaching,
  initializeCoreServices,
  initializeDemoMode,
  initializeTheme,
  loadSettings,
  loadSnippets,
  setupDebugUtilities,
  CoreServices
} from './initialization';
import {
  initializeAllWidgets,
  setupDiffNavigationWidgetTracking,
  WidgetInstances
} from './widgetInitialization';
import {
  initializeJWTAuthenticationModal,
  registerAllCommands,
  setupActiveCellTracking
} from './commandsAndAuth';

/**
 * Main activation function - designed to return in <50ms
 *
 * All heavy work is deferred to background tasks via the DeferredInitScheduler.
 */
export async function activateSignalPilot(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  palette: ICommandPalette,
  themeManager: IThemeManager,
  db: IStateDB,
  documentManager: IDocumentManager,
  settingRegistry: ISettingRegistry | null,
  toolbarRegistry: IToolbarWidgetRegistry | null,
  plugin: JupyterFrontEndPlugin<void>,
  replayId: string | null = null,
  replayIdFromUrl: boolean = false
) {
  // ═══════════════════════════════════════════════════════════════
  // INSTANT PHASE - Must complete in <10ms, no I/O
  // ═══════════════════════════════════════════════════════════════

  // Record activation start time for metrics
  useLoadingStateStore.getState().recordActivateStart();

  console.log('[SignalPilot] Activation started (non-blocking mode)');

  // Store replay ID if present (sync operation)
  if (replayId) {
    console.log(
      `[Replay] Replay ID passed to activateSignalPilot (from ${replayIdFromUrl ? 'URL' : 'localStorage'}):`,
      replayId
    );
  }

  // Initialize AppState synchronously (no I/O)
  initializeAppState(app, settingRegistry);

  // Get content manager reference (sync)
  const contentManager = app.serviceManager.contents;

  // ═══════════════════════════════════════════════════════════════
  // UI SHELL PHASE - Create core services and UI containers
  // This should complete quickly and allow the UI to render
  // ═══════════════════════════════════════════════════════════════

  // Initialize core services synchronously (no I/O, just object creation)
  const coreServices = initializeCoreServices(
    app,
    notebooks,
    documentManager,
    settingRegistry
  );

  const {
    toolService,
    notebookContextManager,
    actionHistory,
    notebookTools,
    cellTrackingService,
    trackingIDUtility,
    contextCellHighlighter,
    diffManager
  } = coreServices;

  // Advance loading state
  useLoadingStateStore.getState().advanceToShellReady();

  // ═══════════════════════════════════════════════════════════════
  // CRITICAL DEFERRED TASKS - Run after UI shell, high priority
  // ═══════════════════════════════════════════════════════════════

  // Schedule widget initialization (critical - users need to see the chat)
  void deferredInit.schedule(
    'widget-initialization',
    async () => {
      const widgets = await initializeAllWidgets(
        app,
        notebooks,
        toolService,
        notebookContextManager,
        diffManager,
        actionHistory,
        contextCellHighlighter,
        contentManager
      );

      // Set up widget tracking after widgets are created
      setupDiffNavigationWidgetTracking(notebooks);

      // Store widget references for later use
      storeWidgetReferences(widgets);

      useLoadingStateStore.getState().setFeatureReady('chatContainer');
      useLoadingStateStore.getState().setFeatureReady('settingsWidget');
    },
    'critical'
  );

  // Schedule command registration (critical - users need commands to work)
  void deferredInit.schedule(
    'command-registration',
    async () => {
      // Register all commands
      registerAllCommands(
        app,
        palette,
        documentManager,
        null as any, // tracker will be set by widget initialization
        notebooks,
        notebookContextManager
      );

      // Set up active cell tracking
      setupActiveCellTracking(notebooks, notebookContextManager);
    },
    'critical'
  );

  // ═══════════════════════════════════════════════════════════════
  // HIGH PRIORITY DEFERRED TASKS
  // ═══════════════════════════════════════════════════════════════

  // Schedule caching initialization
  void deferredInit.schedule(
    'caching-init',
    async () => {
      await initializeCaching(settingRegistry);
      useLoadingStateStore.getState().setFeatureReady('configuration');
    },
    'high'
  );

  // Schedule demo mode initialization
  void deferredInit.schedule(
    'demo-mode-init',
    async () => {
      // Store replay ID in localStorage if present
      if (replayId) {
        const { storeReplayId } = await import('../utils/replayIdManager');
        storeReplayId(replayId);
      }
      await initializeDemoMode(replayId);
    },
    'high'
  );

  // Schedule authentication initialization
  void deferredInit.schedule(
    'authentication-init',
    async () => {
      await initializeAuthentication();
      useLoadingStateStore.getState().setFeatureReady('authentication');
    },
    'high'
  );

  // Schedule settings loading
  void deferredInit.schedule(
    'settings-load',
    () => {
      loadSettings(settingRegistry, plugin.id);
    },
    'high'
  );

  // Schedule theme initialization
  void deferredInit.schedule(
    'theme-init',
    async () => {
      await initializeTheme(themeManager);
    },
    'high'
  );

  // ═══════════════════════════════════════════════════════════════
  // NORMAL PRIORITY DEFERRED TASKS
  // ═══════════════════════════════════════════════════════════════

  // Schedule notebook management setup
  void deferredInit.schedule(
    'notebook-management',
    async () => {
      // Set up file change detection
      setupFileChangeDetection(
        app,
        notebooks,
        documentManager,
        contentManager,
        diffManager,
        cellTrackingService,
        trackingIDUtility,
        contextCellHighlighter,
        notebookTools
      );

      // Initialize the tracking ID utility
      trackingIDUtility.fixTrackingIDs();

      // Set up notebook tracking
      setupNotebookTracking(
        notebooks,
        contentManager,
        diffManager,
        cellTrackingService,
        trackingIDUtility,
        contextCellHighlighter,
        notebookTools,
        app
      );

      // Handle current notebook if one is already open
      if (notebooks.currentWidget) {
        await handleNotebookSwitch(
          notebooks.currentWidget,
          contentManager,
          diffManager,
          cellTrackingService,
          trackingIDUtility,
          contextCellHighlighter,
          notebookTools
        );

        // Auto-render the welcome CTA on notebook switch
        // setTimeout(() => {
        //   app.commands.execute('sage-ai:add-cta-div').catch(error => {
        //     console.warn(
        //       '[Plugin] Failed to auto-render welcome CTA on notebook switch:',
        //       error
        //     );
        //   });
        // }, 300);
      }

      useLoadingStateStore.getState().setFeatureReady('notebookContext');
    },
    'normal'
  );

  // Schedule snippets loading
  void deferredInit.schedule(
    'snippets-load',
    async () => {
      await loadSnippets();
      useLoadingStateStore.getState().setFeatureReady('snippetContext');
    },
    'normal'
  );

  // Schedule async services initialization
  void deferredInit.schedule(
    'async-services',
    async () => {
      await initializeAsyncServices(notebooks);
      useLoadingStateStore.getState().setFeatureReady('databaseContext');
    },
    'normal'
  );

  // Schedule JWT modal initialization
  void deferredInit.schedule(
    'jwt-modal-init',
    async () => {
      // Wait for widgets to be ready first
      await deferredInit.waitFor('widget-initialization');

      // Get settings container from stored references
      const { useServicesStore } = await import('../stores/servicesStore');
      const settingsContainer =
        useServicesStore.getState().widgets?.settingsContainer;

      if (settingsContainer) {
        await initializeJWTAuthenticationModal(app, settingsContainer);
      }
    },
    'normal'
  );

  // ═══════════════════════════════════════════════════════════════
  // NORMAL PRIORITY - Workspace context (needed for welcome message)
  // ═══════════════════════════════════════════════════════════════

  // Schedule workspace context fetch - needed early for welcome message
  void deferredInit.schedule(
    'workspace-context',
    async () => {
      await fetchWorkspaceContext();
    },
    'normal'
  );

  // ═══════════════════════════════════════════════════════════════
  // IDLE PRIORITY TASKS - Nice-to-have, run when browser is idle
  // ═══════════════════════════════════════════════════════════════

  // Schedule debug utilities setup
  void deferredInit.schedule(
    'debug-utilities',
    () => {
      setupDebugUtilities(notebooks);
    },
    'idle'
  );

  // Schedule replay/special modes handling
  void deferredInit.schedule(
    'replay-handling',
    async () => {
      // Wait for critical initialization to complete
      await deferredInit.waitFor('authentication-init');
      await deferredInit.waitFor('widget-initialization');

      // Handle replay if replay ID was passed AND it came from the URL
      if (replayId && replayIdFromUrl) {
        console.log(
          '[Replay] Starting replay initialization for ID (from URL):',
          replayId
        );
        void handleReplayInitialization(replayId, app);
      } else if (replayId && !replayIdFromUrl) {
        console.log(
          '[Replay] ReplayId found in cache but not triggering replay (already played)'
        );
      }

      // Check for stored notebook path to restore
      const { getStoredLastNotebookPath } =
        await import('../utils/replayIdManager');
      const storedNotebookPath = getStoredLastNotebookPath();

      if (storedNotebookPath) {
        console.log(
          '[Notebook Restore] Found stored notebook path, restoring:',
          storedNotebookPath
        );
        void handleNotebookRestoration(storedNotebookPath);
      } else if (useAppStore.getState().isTakeoverMode) {
        console.log('[Takeover] Takeover mode detected, handling re-entry...');
        void handleTakeoverModeReentry();
      }
    },
    'idle'
  );

  // Schedule initialization complete signal
  void deferredInit.schedule(
    'signal-init-complete',
    async () => {
      // Wait for all critical and high priority tasks
      await deferredInit.waitForPriority('high');

      // Signal that core initialization is complete
      useLoadingStateStore.getState().advanceToCoreReady();
      console.log('[SignalPilot] Core initialization complete');

      // Signal that SignalPilot is fully initialized
      const { signalSignalpilotInitialized } = await import('../plugin');
      signalSignalpilotInitialized();

      // Mark all features ready and advance to fully ready state
      useLoadingStateStore.getState().advanceToFullyReady();
      console.log(
        '[SignalPilot] All components loaded, initialization complete'
      );
    },
    'normal'
  );

  // ═══════════════════════════════════════════════════════════════
  // RETURN IMMEDIATELY - Don't block JupyterLab
  // ═══════════════════════════════════════════════════════════════

  console.log('[SignalPilot] Activation returned (background tasks scheduled)');

  // Log scheduler status for debugging
  const status = deferredInit.getStatus();
  console.log(
    `[SignalPilot] Scheduler status: ${status.pendingCount} tasks pending`
  );

  return;
}

/**
 * Store widget references for later access
 */
function storeWidgetReferences(widgets: WidgetInstances): void {
  // Store widgets in servicesStore for access by other parts of the app
  import('../stores/servicesStore')
    .then(({ useServicesStore }) => {
      useServicesStore.getState().setWidgets?.(widgets);
    })
    .catch(error => {
      console.warn('[SignalPilot] Failed to store widget references:', error);
    });
}
