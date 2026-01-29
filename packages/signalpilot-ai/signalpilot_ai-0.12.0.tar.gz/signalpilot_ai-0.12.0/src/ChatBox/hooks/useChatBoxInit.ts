/**
 * useChatBoxInit Hook
 *
 * Handles ChatBox initialization logic, including:
 * - Creating core services (ChatHistoryManager, ChatMessages, ConversationService, etc.)
 * - Loading chat history for the current notebook
 * - Setting up notebook change listeners
 */

import { useCallback, useEffect, useRef } from 'react';
import { useChatboxStore } from '@/stores/chatboxStore';
import { useChatHistoryStore } from '@/stores/chatHistoryStore';
import { useChatUIStore } from '@/stores/chatUIStore';
import { useChatMessagesStore } from '@/stores/chatMessages';
import { useNotebookEventsStore } from '@/stores/notebookEventsStore';
import { useAppStore } from '@/stores/appStore';
import { LAUNCHER_NOTEBOOK_ID } from '@/stores/chatModeStore';
import {
  getToolService,
  getActionHistory,
  getNotebookTools,
  getContentManager,
  getLlmStateDisplay,
  getNotebookDiffManager,
  useServicesStore
} from '@/stores/servicesStore';
import { ChatHistoryManager } from '@/ChatBox/services/ChatHistoryManager';
import { ChatMessages } from '@/ChatBox/services/ChatMessagesService';
import { ChatUIHelper } from '@/ChatBox/services/ChatUIHelper';
import { ConversationService } from '@/LLM';
import { ServiceFactory, ServiceProvider } from '@/Services/ServiceFactory';
import { ConfigService } from '@/Config/ConfigService';
import { startTimer, endTimer } from '@/utils/performanceDebug';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface UseChatBoxInitOptions {
  /** Initial notebook ID to load */
  initialNotebookId?: string;
  /** Callback when initialization completes */
  onReady?: () => void;
  /** Callback when initialization fails */
  onError?: (error: Error) => void;
}

export interface UseChatBoxInitReturn {
  /** Whether the ChatBox is ready */
  isReady: boolean;
  /** Whether initialization is in progress */
  isInitializing: boolean;
  /** Current notebook ID */
  notebookId: string | null;
  /** Reinitialize for a new notebook */
  reinitialize: (notebookId: string) => Promise<void>;
  /** Clear all state */
  reset: () => void;
}

// ═══════════════════════════════════════════════════════════════
// HOOK
// ═══════════════════════════════════════════════════════════════

export function useChatBoxInit(
  options: UseChatBoxInitOptions = {}
): UseChatBoxInitReturn {
  const { initialNotebookId, onReady, onError } = options;

  // Store state
  const {
    isReady,
    isInitializing,
    currentNotebookId,
    initialize,
    reinitializeForNotebook,
    setReady,
    setServices,
    services
  } = useChatboxStore();

  const { loadThreads, clearHistory } = useChatHistoryStore();
  const { reset: resetUI } = useChatUIStore();
  const { clearMessages } = useChatMessagesStore();

  // Use direct state selection for immediate reactivity (no async callback overhead)
  // The store updates synchronously via Zustand, while props may lag behind
  const appStateNotebookId = useNotebookEventsStore(
    state => state.currentNotebookId
  );
  const isLauncherActive = useAppStore(state => state.isLauncherActive);

  // Refs to hold created services (persist across renders)
  const servicesRef = useRef<{
    chatHistoryManager: ChatHistoryManager | null;
    messageComponent: ChatMessages | null;
    uiHelper: ChatUIHelper | null;
    conversationService: ConversationService | null;
  }>({
    chatHistoryManager: null,
    messageComponent: null,
    uiHelper: null,
    conversationService: null
  });

  // Create core services (only once)
  const createServices = useCallback(
    (notebookId: string) => {
      // Skip if already created
      if (servicesRef.current.conversationService) {
        console.log(
          '[useChatBoxInit] Services already created, updating notebookId'
        );
        servicesRef.current.conversationService.updateNotebookId(notebookId);
        return servicesRef.current;
      }

      console.log('[useChatBoxInit] Creating core services...');

      const toolService = getToolService();
      const actionHistory = getActionHistory();
      const notebookTools = getNotebookTools();
      const contentManager = getContentManager();
      const llmStateDisplay = getLlmStateDisplay();
      const diffManager = useServicesStore.getState().notebookDiffManager;

      // Create chatService if it doesn't exist (was previously done in old ChatBoxWidget)
      let chatService = useServicesStore.getState().chatService;
      if (!chatService) {
        console.log('[useChatBoxInit] Creating chatService...');
        chatService = ServiceFactory.createService(ServiceProvider.ANTHROPIC);
        useServicesStore.getState().setChatService(chatService);
      }

      // Log which services are available for debugging
      console.log('[useChatBoxInit] Service availability:', {
        toolService: !!toolService,
        actionHistory: !!actionHistory,
        notebookTools: !!notebookTools,
        chatService: !!chatService,
        contentManager: !!contentManager,
        llmStateDisplay: !!llmStateDisplay,
        diffManager: !!diffManager
      });

      if (
        !toolService ||
        !actionHistory ||
        !notebookTools ||
        !chatService ||
        !contentManager
      ) {
        console.warn(
          '[useChatBoxInit] Missing required services for initialization'
        );
        return null;
      }

      // Create ChatHistoryManager
      const chatHistoryManager = new ChatHistoryManager();

      // Create ChatMessages (messageComponent)
      const messageComponent = new ChatMessages({
        historyManager: chatHistoryManager,
        notebookTools,
        onScrollDownButtonDisplay: () => {
          // Will be wired to actual scroll function later
          console.log('[useChatBoxInit] Scroll down button display requested');
        }
      });

      // Create a placeholder element for DOM-based services
      // These services expect DOM elements but in pure React we create placeholders
      const placeholderElement = document.createElement('div');

      // Create ChatUIHelper
      const uiHelper = new ChatUIHelper(
        placeholderElement, // _chatHistory (not used, for API compat)
        messageComponent,
        llmStateDisplay!
      );

      // Create ConversationService
      const conversationService = new ConversationService(
        chatService,
        toolService,
        contentManager,
        messageComponent,
        placeholderElement, // chatHistory element
        actionHistory,
        uiHelper, // loadingManager
        diffManager || undefined
      );

      // Store in ref
      servicesRef.current = {
        chatHistoryManager,
        messageComponent,
        uiHelper,
        conversationService
      };

      // Update chatbox store with services
      setServices({
        chatHistoryManager,
        messageComponent,
        uiHelper,
        conversationService,
        chatService
      });

      console.log('[useChatBoxInit] Core services created successfully');
      return servicesRef.current;
    },
    [setServices]
  );

  // Initialize function
  const doInitialize = useCallback(
    async (notebookId: string) => {
      startTimer('useChatBoxInit.doInitialize.TOTAL');
      try {
        console.log('[useChatBoxInit] Initializing for notebook:', notebookId);

        // Load config and initialize services (critical for API URLs)
        try {
          startTimer('useChatBoxInit.doInitialize.loadConfig');
          const config = await ConfigService.getConfig();
          useServicesStore.getState().setConfig(config);
          endTimer('useChatBoxInit.doInitialize.loadConfig');
          console.log('[useChatBoxInit] Config loaded');

          // Initialize chat service
          startTimer('useChatBoxInit.doInitialize.initChatService');
          const chatService = useServicesStore.getState().chatService;
          if (chatService) {
            const initialized = await chatService.initialize();
            console.log(
              '[useChatBoxInit] Chat service initialized:',
              initialized
            );
          }
          endTimer('useChatBoxInit.doInitialize.initChatService');

          // Initialize tool service
          startTimer('useChatBoxInit.doInitialize.initToolService');
          const toolService = getToolService();
          if (toolService) {
            await toolService.initialize();
            console.log(
              '[useChatBoxInit] Tool service initialized with',
              toolService.getTools().length,
              'tools'
            );
          }
          endTimer('useChatBoxInit.doInitialize.initToolService');
        } catch (configError) {
          console.error(
            '[useChatBoxInit] Failed to initialize services:',
            configError
          );
        }

        // Create services if not already created
        startTimer('useChatBoxInit.doInitialize.createServices');
        createServices(notebookId);
        endTimer('useChatBoxInit.doInitialize.createServices');

        // Load threads for this notebook
        startTimer('useChatBoxInit.doInitialize.loadThreads');
        await loadThreads(notebookId);
        endTimer('useChatBoxInit.doInitialize.loadThreads');

        // Mark as ready
        setReady();

        // Call onReady callback
        onReady?.();
        endTimer('useChatBoxInit.doInitialize.TOTAL');
      } catch (error) {
        endTimer('useChatBoxInit.doInitialize.TOTAL');
        console.error('[useChatBoxInit] Initialization failed:', error);
        onError?.(error instanceof Error ? error : new Error(String(error)));
      }
    },
    [createServices, loadThreads, setReady, onReady, onError]
  );

  // Initialize on mount or when notebook changes
  useEffect(() => {
    startTimer('useChatBoxInit.useEffect.triggered');
    // Use store value, or LAUNCHER_NOTEBOOK_ID if in launcher mode with no notebook
    const notebookId =
      appStateNotebookId || (isLauncherActive ? LAUNCHER_NOTEBOOK_ID : null);

    // Check if services are already created (key fix for race condition)
    // NotebookChatContainer may have already set currentNotebookId in the store
    // before this hook runs, so we need to check if services exist
    const servicesCreated = !!services.conversationService;

    // Debug logging
    console.log('[useChatBoxInit] useEffect triggered:', {
      notebookId,
      appStateNotebookId,
      isLauncherActive,
      storeNotebookId: currentNotebookId,
      isInitializing,
      servicesCreated,
      willInitialize: !!(
        notebookId &&
        (!servicesCreated || notebookId !== currentNotebookId) &&
        !isInitializing
      )
    });

    // Initialize if:
    // 1. We have a notebook ID (or launcher ID) AND
    // 2. Either services aren't created OR notebook ID changed AND
    // 3. Not already initializing
    if (
      notebookId &&
      (!servicesCreated || notebookId !== currentNotebookId) &&
      !isInitializing
    ) {
      console.log(
        '[useChatBoxInit] Starting initialization for:',
        notebookId === LAUNCHER_NOTEBOOK_ID
          ? 'launcher'
          : `notebook ${notebookId}`
      );

      // Create services FIRST before setting currentNotebookId
      // This ensures chatHistoryManager is available when other components
      // try to load threads after currentNotebookId changes
      startTimer('useChatBoxInit.useEffect.createServices');
      const result = createServices(notebookId);
      endTimer('useChatBoxInit.useEffect.createServices');

      if (!result) {
        endTimer('useChatBoxInit.useEffect.triggered');
        console.error(
          '[useChatBoxInit] Failed to create services - check console for missing dependencies'
        );
        return;
      }

      // Services created successfully, proceed with initialization
      startTimer('useChatBoxInit.useEffect.initialize');
      initialize(notebookId);
      endTimer('useChatBoxInit.useEffect.initialize');
      void doInitialize(notebookId);
    } else if (!notebookId && !isReady) {
      // No notebook and not in launcher mode - just mark as ready for UI
      console.log(
        '[useChatBoxInit] No notebook or launcher - marking as ready'
      );
      setReady();
      onReady?.();
    }
    endTimer('useChatBoxInit.useEffect.triggered');
  }, [
    appStateNotebookId,
    isLauncherActive,
    currentNotebookId,
    isInitializing,
    isReady,
    services.conversationService, // Track service creation state
    createServices,
    initialize,
    doInitialize,
    setReady,
    onReady
  ]);

  // Reinitialize for a new notebook
  const reinitialize = useCallback(
    async (notebookId: string) => {
      await reinitializeForNotebook(notebookId);
      await doInitialize(notebookId);
    },
    [reinitializeForNotebook, doInitialize]
  );

  // Reset all state
  const reset = useCallback(() => {
    clearHistory();
    clearMessages();
    resetUI();
  }, [clearHistory, clearMessages, resetUI]);

  return {
    isReady,
    isInitializing,
    notebookId: currentNotebookId,
    reinitialize,
    reset
  };
}

export default useChatBoxInit;
