/**
 * SignalPilot Notebook Management Module
 *
 * Handles notebook switching, file change detection, and notebook-related events
 */

import { JupyterFrontEnd } from '@jupyterlab/application';
import { INotebookTracker } from '@jupyterlab/notebook';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { v4 as uuidv4 } from 'uuid';

import { useAppStore, hasCompletedWelcomeTour } from '../stores/appStore';
import { useNotebookEventsStore } from '../stores/notebookEventsStore';
import { NotebookTools } from '../Notebook/NotebookTools';
import { NotebookDiffManager } from '../Notebook/NotebookDiffManager';
import { NotebookDiffTools } from '../Notebook/NotebookDiffTools';
import { CellTrackingService } from '../Services/CellTrackingService';
import { TrackingIDUtility } from '../utils/TrackingIDUtility';
import { ContextCellHighlighter } from '../Jupyter';
import { ContextCacheService } from '@/ChatBox/Context/ContextCacheService';
import { DatabaseMetadataCache } from '../stores/databaseMetadataCacheStore';
import { KernelUtils } from '../utils/kernelUtils';
import {
  attachChatboxToLauncher,
  detachChatboxFromLauncher
} from '../Commands/commands';
import { runWelcomeDemo } from '../demo';
import { JupyterAuthService } from '../Services/JupyterAuthService';
import { usePlanStateStore } from '../stores/planStateStore';
import {
  useChatboxStore,
  getChatboxState,
  showWelcomeMessage,
  isChatboxReady,
  isMessagingReady
} from '../stores/chatboxStore';
import {
  useChatModeStore,
  LAUNCHER_NOTEBOOK_ID
} from '../stores/chatModeStore';
import { useChatMessagesStore } from '../stores/chatMessages';
import { useChatUIStore } from '../stores/chatUIStore';
import { useLLMStateStore } from '../stores/llmStateStore';
import { useWaitingReplyStore } from '../stores/waitingReplyStore';
import { startTimer, endTimer } from '../utils/performanceDebug';

// Track the current notebook switch operation for cancellation
let currentNotebookSwitchAbortController: AbortController | null = null;
let currentNotebookSwitchPromise: Promise<void> | null = null;

/**
 * Unified notebook switch handler - handles all notebook switching logic
 * including diff manager updates, kernel setup, database environments,
 * thread management, and context loading.
 *
 * This is the SINGLE source of truth for notebook switching behavior.
 * Used by:
 * - notebooks.currentChanged.connect (switching between notebooks)
 * - File change detection (switching from launcher to notebook)
 *
 * When called multiple times concurrently, only the last call will execute.
 * Previous in-flight operations will be cancelled.
 */
export async function handleNotebookSwitch(
  notebook: any,
  contentManager: any,
  diffManager: NotebookDiffManager,
  cellTrackingService: CellTrackingService,
  trackingIDUtility: TrackingIDUtility,
  contextCellHighlighter: ContextCellHighlighter,
  notebookTools: NotebookTools,
  fromLauncher: boolean = false
): Promise<void> {
  if (!notebook) {
    return;
  }

  // Cancel any previous in-flight operation
  if (currentNotebookSwitchAbortController) {
    console.log('[NotebookSwitch] Cancelling previous in-flight operation');
    currentNotebookSwitchAbortController.abort();
  }

  // Create a new AbortController for this operation
  const abortController = new AbortController();
  currentNotebookSwitchAbortController = abortController;

  // Create a promise that will be resolved/rejected based on cancellation
  const executeSwitch = async (): Promise<void> => {
    // Helper function to check if operation was cancelled
    const checkCancelled = () => {
      if (abortController.signal.aborted) {
        throw new Error('Notebook switch operation was cancelled');
      }
    };

    try {
      startTimer('NotebookSwitch.TOTAL');
      console.log('==== UNIFIED NOTEBOOK SWITCH HANDLER ====', notebook);
      if (fromLauncher) {
        console.log('[NotebookSwitch] Triggered from launcher state');
      }

      // Reset UI state stores when switching notebooks
      // This ensures we don't show stale plan/LLM state from previous notebook
      console.log('[NotebookSwitch] Resetting UI state stores');
      usePlanStateStore.getState().reset();
      useLLMStateStore.getState().hide();
      useWaitingReplyStore.getState().hide();
      useChatUIStore.getState().reset();

      checkCancelled();

      // Get notebook file and metadata
      startTimer('NotebookSwitch.getNotebookFile');
      const nbFile = await contentManager.get(notebook.context.path);
      endTimer('NotebookSwitch.getNotebookFile');
      checkCancelled();

      let notebookUniqueId: string | null = null;

      console.log('================== NOTEBOOK FILE =================');
      console.log(nbFile);

      if (nbFile && nbFile.content) {
        // Get notebook metadata
        if (!nbFile.content.metadata || !nbFile.content.nbformat) {
          return;
        }

        const nbMetadata = nbFile.content.metadata || {};

        // Ensure unique_id exists
        if (!nbMetadata.sage_ai || !nbMetadata.sage_ai.unique_id) {
          checkCancelled();
          await notebook.context.save();
          checkCancelled();
          nbMetadata.sage_ai = {
            unique_id: 'nb_' + uuidv4() + '_' + Date.now()
          };

          nbFile.content.metadata = nbMetadata;
          if (nbFile.content.metadata) {
            await contentManager.save(notebook.context.path, nbFile);
            checkCancelled();
          }

          await notebook.context.revert();
          checkCancelled();
          await notebook.context.save();
          checkCancelled();
        }

        notebookUniqueId = nbMetadata.sage_ai.unique_id;
      }

      // Setup path change tracking (only once per notebook)
      let oldPath = notebook.context.path;
      if (!notebook._pathChangeListenerAttached) {
        notebook._pathChangeListenerAttached = true;
        notebook.context.pathChanged.connect(async (_: any, path: string) => {
          if (oldPath !== path) {
            try {
              console.log('RENAMING NOTEBOOK');
              const updatedNbFile = await contentManager.get(path);
              const currentNotebookId =
                updatedNbFile?.content?.metadata?.sage_ai?.unique_id ||
                notebookUniqueId;

              console.log('NB ID:', currentNotebookId);

              if (currentNotebookId) {
                useNotebookEventsStore
                  .getState()
                  .setCurrentNotebook(notebook, notebookUniqueId);
                useNotebookEventsStore
                  .getState()
                  .updateNotebookId(
                    notebookUniqueId || oldPath,
                    currentNotebookId
                  );
                notebookUniqueId = currentNotebookId;
              }
            } catch (error) {
              console.warn(
                'Could not get notebook metadata after path change:',
                error
              );
              useNotebookEventsStore
                .getState()
                .setCurrentNotebook(notebook, notebookUniqueId);
              useNotebookEventsStore.getState().updateNotebookId(oldPath, path);
            }

            oldPath = path;
          }
        });
      }

      checkCancelled();

      // Auto-apply any pending diffs for the old notebook before switching
      // This prevents diffs from being lost when switching notebooks mid-generation
      const oldNotebookIdForDiffs =
        useNotebookEventsStore.getState().currentNotebookId;
      if (oldNotebookIdForDiffs && diffManager.hasPendingDiffs()) {
        console.log(
          '[NotebookSwitch] Auto-applying pending diffs for old notebook:',
          oldNotebookIdForDiffs
        );
        // Approve all pending diffs
        diffManager.approveAllDiffsForNotebook(oldNotebookIdForDiffs);
        // Apply the approved diffs
        await diffManager.applyApprovedDiffs(oldNotebookIdForDiffs);
        // Clear the diffs after applying
        diffManager.clearDiffsForNotebook(oldNotebookIdForDiffs);
      }

      // Remove diff overlays from all cells
      for (const cell of notebook.content.widgets) {
        NotebookDiffTools.removeDiffOverlay(cell);
      }

      // Update diff manager
      diffManager.setNotebookWidget(notebook);

      // Store the old notebook ID before switching
      const oldNotebookId = useNotebookEventsStore.getState().currentNotebookId;

      // Set the current notebook and ID using the unique_id
      startTimer('NotebookSwitch.setCurrentNotebook');
      if (notebookUniqueId) {
        // If we're coming from launcher, use triggerNotebookChange to pass the fromLauncher flag
        // This must be done BEFORE setCurrentNotebook to ensure the subscription gets the flag
        if (fromLauncher) {
          useNotebookEventsStore
            .getState()
            .triggerNotebookChange(oldNotebookId, notebookUniqueId, true);
        }

        useNotebookEventsStore
          .getState()
          .setCurrentNotebook(notebook, notebookUniqueId);
        // Update centralized chat mode store - this is the definitive mode source
        useChatModeStore.getState().switchToNotebook(notebookUniqueId);
        useChatboxStore.getState().cancelMessage();
      } else {
        useNotebookEventsStore.getState().setCurrentNotebook(notebook);
        // Even without a unique ID, we're in notebook context
        useChatModeStore.getState().switchToNotebook(notebook.context.path);
      }
      endTimer('NotebookSwitch.setCurrentNotebook');

      checkCancelled();

      // Initialize tracking metadata for existing cells
      startTimer('NotebookSwitch.initializeCells');
      cellTrackingService.initializeExistingCells();

      // Fix for old notebooks having undeletable first cells
      if (notebook.model && notebook.model.cells.length > 0) {
        notebook.model.cells.get(0).setMetadata('deletable', true);
      }

      // Set the current notebook ID in the centralized store using unique_id
      useNotebookEventsStore
        .getState()
        .setCurrentNotebookId(notebookUniqueId || notebook.context.path);

      diffManager.setNotebookWidget(notebook);
      cellTrackingService.initializeExistingCells();

      // Ensure cell overlays are rendered immediately after tracking initialization
      // This is crucial for new notebooks where cells might not trigger the change event
      contextCellHighlighter.refreshHighlighting(notebook);
      endTimer('NotebookSwitch.initializeCells');

      // Update plan state display
      const planCell = notebookTools.getPlanCell(
        notebookUniqueId || notebook.context.path
      );

      if (planCell) {
        const currentStep =
          (planCell.model.sharedModel.getMetadata()?.custom as any)
            ?.current_step_string || '';
        const nextStep =
          (planCell.model.sharedModel.getMetadata()?.custom as any)
            ?.next_step_string || '';
        const source = planCell.model.sharedModel.getSource() || '';

        void usePlanStateStore
          .getState()
          .updatePlan(currentStep || 'Plan active', nextStep, source, false);
      } else {
        // Explicitly clear plan state when no plan cell exists
        // (defensive - reset() was already called above, but this ensures clarity)
        void usePlanStateStore
          .getState()
          .updatePlan(undefined, undefined, undefined);
      }

      // Setup cell change listeners (only once per notebook)
      if (!notebook._cellChangeListenerAttached) {
        notebook._cellChangeListenerAttached = true;
        notebook?.model?.cells.changed.connect(async () => {
          // Fix tracking IDs first (synchronous)
          trackingIDUtility.fixTrackingIDs(
            notebookUniqueId || notebook.context.path
          );

          // Use requestAnimationFrame to ensure DOM is ready before adding overlays
          // This is especially important for the first cell in a new notebook
          requestAnimationFrame(() => {
            contextCellHighlighter.refreshHighlighting(notebook);
          });

          // Refresh cell contexts when cells change
          setTimeout(() => {
            const contextCacheService = ContextCacheService.getInstance();
            contextCacheService.loadContextCategory('cells').catch(error => {
              console.warn('[Plugin] Cell context refresh failed:', error);
            });
          }, 200);

          const planCell = notebookTools.getPlanCell(
            notebookUniqueId || notebook.context.path
          );

          if (planCell) {
            const currentStep =
              (planCell.model.sharedModel.getMetadata()?.custom as any)
                ?.current_step_string || '';
            const nextStep =
              (planCell.model.sharedModel.getMetadata()?.custom as any)
                ?.next_step_string || '';
            const source = planCell.model.sharedModel.getSource() || '';

            console.log('Updating step floating box', currentStep, nextStep);

            const currentStepState = usePlanStateStore.getState().currentStep;
            // If the current step is equal from the state and the state is loading, set the loading state to true
            const isLoading =
              currentStepState === currentStep &&
              usePlanStateStore.getState().isLoading;

            void usePlanStateStore
              .getState()
              .updatePlan(currentStep, nextStep, source, isLoading);
          } else if (!planCell) {
            void usePlanStateStore
              .getState()
              .updatePlan(undefined, undefined, undefined);
          }

          // Attach metadata change listeners to new cells only
          if (notebook.model?.cells) {
            for (const cell of notebook.model.cells) {
              // Check if listener already attached to avoid duplicates
              if (!(cell as any)._metadataListenerAttached) {
                (cell as any)._metadataListenerAttached = true;
                cell.metadataChanged.connect(() => {
                  // Use requestAnimationFrame to ensure DOM is ready
                  requestAnimationFrame(() => {
                    contextCellHighlighter.refreshHighlighting(notebook);
                  });
                });
              }
            }
          }
        });
      }

      checkCancelled();

      // Set database environment variables for all configured databases
      console.log(
        '[Plugin] Notebook changed, setting up database environments in kernel'
      );
      void KernelUtils.setDatabaseEnvironmentsInKernelWithRetry();

      // Refresh context cache on notebook switch
      setTimeout(() => {
        if (!abortController.signal.aborted) {
          const contextCacheService = ContextCacheService.getInstance();
          contextCacheService.refreshIfStale().catch(error => {
            console.warn(
              '[Plugin] Context refresh on notebook change failed:',
              error
            );
          });
        }
      }, 500);

      // Notify database cache that kernel may be ready
      const databaseCache = DatabaseMetadataCache.getInstance();
      setTimeout(() => {
        if (!abortController.signal.aborted) {
          console.log(
            '[Plugin] Notifying database cache of potential kernel readiness'
          );
          databaseCache.onKernelReady().catch(error => {
            console.warn(
              '[Plugin] Database cache kernel ready notification failed:',
              error
            );
          });
        }
      }, 3000);

      endTimer('NotebookSwitch.TOTAL');
    } catch (error) {
      // If the operation was cancelled, silently ignore the error
      if (abortController.signal.aborted) {
        console.log('[NotebookSwitch] Operation was cancelled');
        return;
      }
      // Otherwise, re-throw the error
      throw error;
    }
  };

  // Execute the switch and store the promise
  currentNotebookSwitchPromise = executeSwitch();

  // Return the promise, but clear the abort controller reference when done
  return currentNotebookSwitchPromise
    .then(() => {
      // Only clear if this is still the current operation
      if (currentNotebookSwitchAbortController === abortController) {
        currentNotebookSwitchAbortController = null;
        currentNotebookSwitchPromise = null;
      }
    })
    .catch(error => {
      // Only clear if this is still the current operation
      if (currentNotebookSwitchAbortController === abortController) {
        currentNotebookSwitchAbortController = null;
        currentNotebookSwitchPromise = null;
      }
      // Re-throw if it's not a cancellation error
      if (!abortController.signal.aborted) {
        throw error;
      }
    });
}

/**
 * Helper function to get active file information
 */
function getActiveFile(
  app: JupyterFrontEnd,
  documentManager: IDocumentManager
) {
  const widget = app.shell.currentWidget;
  if (!widget) {
    return null;
  }

  const context = documentManager.contextForWidget(widget);
  if (!context) {
    return null;
  }

  const path = context.path;
  const name = path.split('/').pop() ?? path;
  const fileTypes = documentManager.registry.getFileTypesForPath(path);
  const fileType = fileTypes.length > 0 ? fileTypes[0].name : 'file';

  return { path, name, fileType, widget, context };
}

/**
 * Sets up file change detection - detects when switching between files/tabs
 * and triggers the unified notebook switch handler when switching to a notebook
 */
export function setupFileChangeDetection(
  app: JupyterFrontEnd,
  notebooks: INotebookTracker,
  documentManager: IDocumentManager,
  contentManager: any,
  diffManager: NotebookDiffManager,
  cellTrackingService: CellTrackingService,
  trackingIDUtility: TrackingIDUtility,
  contextCellHighlighter: ContextCellHighlighter,
  notebookTools: NotebookTools
): void {
  let previousFile: { path: string; fileType: string } | null = null;
  let wasLauncherActive = false;

  const checkAndLogFileChange = async () => {
    const currentFile = getActiveFile(app, documentManager);
    const isLauncher = app.shell.currentWidget?.title.label === 'Launcher';

    console.log('[File Change] Current active file:', currentFile);
    console.log('[File Change] Is launcher active:', isLauncher);

    // Check for launcher state changes
    if (isLauncher !== wasLauncherActive) {
      if (isLauncher) {
        console.log('[File Change] ⚠️ SWITCHED TO LAUNCHER');

        // Capture the old notebook ID before any state changes
        const oldNotebookIdForDiffs =
          useNotebookEventsStore.getState().currentNotebookId;

        // CRITICAL: Cancel any in-progress LLM generation FIRST
        // This must happen before we try to apply diffs, as diffs are created during streaming
        const { isProcessingMessage } = useChatboxStore.getState();
        if (isProcessingMessage) {
          console.log('[File Change] Cancelling in-progress LLM generation');
          useChatboxStore.getState().cancelMessage();
          // Give the streaming a moment to stop and finalize any pending tool calls
          await new Promise(resolve => setTimeout(resolve, 300));
        }

        // Now auto-apply any pending diffs for the old notebook
        // This prevents diffs from being lost when switching mid-generation
        if (oldNotebookIdForDiffs && diffManager.hasPendingDiffs()) {
          console.log(
            '[File Change] Auto-applying pending diffs for old notebook:',
            oldNotebookIdForDiffs
          );
          diffManager.approveAllDiffsForNotebook(oldNotebookIdForDiffs);
          await diffManager.applyApprovedDiffs(oldNotebookIdForDiffs);
          diffManager.clearDiffsForNotebook(oldNotebookIdForDiffs);
        }

        try {
          if (app.commands.isToggled('application:toggle-right-area')) {
            await app.commands.execute('application:toggle-right-area');
          }
        } catch (error) {
          console.warn('Could not toggle right area:', error);
        }
        useAppStore.getState().setLauncherActive(true);
        // Update centralized chat mode store - this is the definitive mode source
        useChatModeStore.getState().switchToLauncher();

        // Clear notebook reference for launcher mode without triggering change events
        // We keep the notebook ID so we can detect same-notebook returns
        // The isLauncherActive flag in appStore is the source of truth for launcher state
        useNotebookEventsStore.getState().clearForLauncher();

        // Reset UI state stores when switching to launcher
        // This ensures we don't show stale plan/LLM state from previous notebook
        usePlanStateStore.getState().reset();
        useLLMStateStore.getState().hide();
        useWaitingReplyStore.getState().hide();

        // Clear chat messages for fresh launcher chat session
        useChatMessagesStore.getState().clearMessages();

        // Reset chat UI state - ensures new chat display can show
        useChatUIStore.getState().reset();

        // Set up the chat history manager with the launcher notebook ID
        const chatHistoryManager =
          getChatboxState().services?.chatHistoryManager;
        if (chatHistoryManager) {
          void chatHistoryManager.setCurrentNotebook(LAUNCHER_NOTEBOOK_ID);
        }

        attachChatboxToLauncher();

        // Check if welcome tour has been completed
        const tourCompleted = await hasCompletedWelcomeTour();
        const isAuthenticated = await JupyterAuthService.isAuthenticated();
        const isDemoMode = useAppStore.getState().isDemoMode;

        if (!tourCompleted && isAuthenticated && !isDemoMode) {
          console.log(
            '[File Change] Welcome tour not completed and user is authenticated - showing tour'
          );
          // Wait a bit for the chatbox to be fully attached
          setTimeout(() => {
            runWelcomeDemo(app);
          }, 1000);
        } else {
          if (tourCompleted) {
            console.log(
              '[File Change] Welcome tour already completed - sending welcome message'
            );
            // For returning users, send welcome message after messaging is ready
            const waitForMessagingAndSendWelcome = () => {
              if (isMessagingReady()) {
                // Add a small delay to ensure the chatbox UI is fully rendered
                setTimeout(() => {
                  // Check if welcome message was already shown
                  const { hasShownWelcomeMessage } = useChatboxStore.getState();
                  if (hasShownWelcomeMessage) {
                    // Welcome already shown - just show the new chat display
                    console.log(
                      '[File Change] Welcome message already shown - showing new chat display'
                    );
                    useChatUIStore.getState().setShowNewChatDisplay(true);
                  } else {
                    // Send welcome message (this will hide new chat display and show the message)
                    void showWelcomeMessage();
                  }
                }, 500);
              } else {
                // Wait for messaging to be ready (conversationService available)
                setTimeout(waitForMessagingAndSendWelcome, 100);
              }
            };
            waitForMessagingAndSendWelcome();
          } else if (!isAuthenticated) {
            console.log(
              '[File Change] User not authenticated - skipping welcome tour'
            );
          } else if (isDemoMode) {
            console.log(
              '[File Change] Demo mode enabled - skipping welcome tour'
            );
          }
        }
      } else {
        console.log('[File Change] ⚠️ SWITCHED AWAY FROM LAUNCHER');
        useAppStore.getState().setLauncherActive(false);

        // Detach chatbox from launcher and restore to sidebar
        detachChatboxFromLauncher(app);

        // If we're switching away from launcher TO a notebook, trigger full notebook initialization
        if (currentFile && currentFile.fileType === 'notebook') {
          console.log(
            '[File Change] 🔄 Triggering full notebook switch from launcher to notebook'
          );
          const notebookWidget = notebooks.currentWidget;
          if (notebookWidget) {
            await handleNotebookSwitch(
              notebookWidget,
              contentManager,
              diffManager,
              cellTrackingService,
              trackingIDUtility,
              contextCellHighlighter,
              notebookTools,
              true
            );
          }
        }
      }
      wasLauncherActive = isLauncher;
    }

    if (!currentFile && previousFile) {
      console.log(
        `[File Change] Switched away from ${previousFile.path} (${previousFile.fileType}) to a non-document widget or closed the file`
      );
      previousFile = null;
      return;
    }

    if (!currentFile) {
      previousFile = null;
      return;
    }

    // Check if we switched to a different file or file type
    if (!previousFile || previousFile.path !== currentFile.path) {
      const fromInfo = previousFile
        ? `from ${previousFile.path} (${previousFile.fileType})`
        : 'from nothing';

      console.log(
        `[File Change] Switched ${fromInfo} to ${currentFile.path} (${currentFile.fileType})`
      );

      // Specifically highlight when switching away from notebooks
      if (
        previousFile?.fileType === 'notebook' &&
        currentFile.fileType !== 'notebook'
      ) {
        console.log(
          `[File Change] ⚠️ SWITCHED AWAY FROM NOTEBOOK to ${currentFile.fileType} file`
        );
      }

      // Specifically highlight when switching to notebooks
      if (
        previousFile &&
        previousFile.fileType !== 'notebook' &&
        currentFile.fileType === 'notebook'
      ) {
        console.log(
          `[File Change] ⚠️ SWITCHED TO NOTEBOOK from ${previousFile.fileType} file`
        );

        // Trigger full notebook initialization when switching TO a notebook
        console.log('[File Change] 🔄 Triggering full notebook switch');
        const notebookWidget = notebooks.currentWidget;
        if (notebookWidget) {
          await handleNotebookSwitch(
            notebookWidget,
            contentManager,
            diffManager,
            cellTrackingService,
            trackingIDUtility,
            contextCellHighlighter,
            notebookTools
          );
        }
      }

      previousFile = {
        path: currentFile.path,
        fileType: currentFile.fileType
      };
    }
  };

  // Initial check
  void checkAndLogFileChange();

  // Listen to shell changes (when user switches tabs/panels)
  if (app.shell.currentChanged) {
    app.shell.currentChanged.connect(() => {
      void checkAndLogFileChange();
    });
  }
}

/**
 * Set up notebook tracking to switch to the active notebook
 */
export function setupNotebookTracking(
  notebooks: INotebookTracker,
  contentManager: any,
  diffManager: NotebookDiffManager,
  cellTrackingService: CellTrackingService,
  trackingIDUtility: TrackingIDUtility,
  contextCellHighlighter: ContextCellHighlighter,
  notebookTools: NotebookTools,
  app: JupyterFrontEnd
): void {
  notebooks.currentChanged.connect(async (_, notebook) => {
    if (notebook) {
      await handleNotebookSwitch(
        notebook,
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
    } else {
      // No notebook is active - check if launcher is active
      const isLauncher = app.shell.currentWidget?.title.label === 'Launcher';
      if (isLauncher) {
        console.log(
          '[Notebook Tracker] Switched to launcher - no notebook active'
        );
        useAppStore.getState().setLauncherActive(true);
      }
    }
  });
}
