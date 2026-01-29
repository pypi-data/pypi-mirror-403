/**
 * ChatboxStore
 *
 * Central orchestration store for the ChatBox component.
 * This store manages:
 * - Initialization and ready state
 * - Notebook tracking and lifecycle
 * - Message processing state
 * - Welcome message state
 * - Service references for orchestration
 *
 * This store replaces the class-level state from ChatBoxWidget
 * and provides a pure React/Zustand approach.
 */

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Service references stored for orchestration
 * These are set during initialization and used by actions
 */
export interface IChatboxServices {
  conversationService: any | null;
  chatHistoryManager: any | null;
  threadManager: any | null;
  chatService: any | null;
  messageComponent: any | null;
  uiHelper: any | null;
  // Widget reference for UI operations
  chatWidget: any | null;
  // Chat container widget reference for launcher operations
  chatContainer: any | null;
}

/**
 * Chatbox state
 */
export interface IChatboxState {
  // Initialization state
  isReady: boolean;
  isFullyInitialized: boolean;
  isInitializing: boolean;

  // Notebook tracking
  currentNotebookId: string | null;
  currentNotebookPath: string | null;
  lastNotebookId: string | null;

  // Processing state
  isProcessingMessage: boolean;
  isCancelled: boolean;

  // Welcome message state
  hasShownWelcomeMessage: boolean;
  welcomeMessagePreloaded: boolean;
  isWelcomeMessageHidden: boolean;

  // Context row version - incremented when cell context changes to trigger re-render
  contextRowVersion: number;

  // Service references (for orchestration)
  services: IChatboxServices;
}

/**
 * Chatbox actions
 */
export interface IChatboxActions {
  // Initialization
  initialize: (notebookId?: string) => Promise<void>;
  setReady: () => void;
  setServices: (services: Partial<IChatboxServices>) => void;

  // Notebook management
  updateNotebookId: (newId: string) => void;
  updateNotebookPath: (newPath: string) => void;
  setNotebookId: (notebookId: string | null) => Promise<void>;
  reinitializeForNotebook: (notebookId: string) => Promise<void>;
  setLastNotebookId: (id: string | null) => void;

  // Processing state
  setIsProcessingMessage: (value: boolean) => void;
  setCancelled: (value: boolean) => void;

  // Welcome message
  setHasShownWelcomeMessage: (value: boolean) => void;
  setWelcomeMessagePreloaded: (value: boolean) => void;
  setWelcomeMessageHidden: (value: boolean) => void;

  // Chat operations
  createNewChat: () => void;
  continueMessage: () => void;
  sendPromptMessage: (
    prompt: string,
    mode?: 'agent' | 'ask' | 'fast' | 'welcome'
  ) => Promise<void>;
  cancelMessage: () => void;
  undoLastAction: () => void;

  // Service access helpers
  getConversationService: () => any | null;
  getChatHistoryManager: () => any | null;
  getMessageComponent: () => any | null;

  // Context operations
  onCellAddedToContext: (path: string) => void;
  onCellRemovedFromContext: (path: string) => void;

  // Widget UI operations
  showHistoryWidget: () => void;
  showWelcomeMessage: () => Promise<void>;
  startWelcomeMessagePreload: () => Promise<void>;
  getStateDisplayContainer: () => HTMLElement | null;
  updateDynamicBottomPositions: () => void;

  // Launcher operations
  attachToLauncher: (launcherBody: HTMLElement) => boolean;
  detachFromLauncher: () => void;
  isAttachedToLauncher: () => boolean;

  // Cleanup
  reset: () => void;
  dispose: () => void;
}

type IChatboxStore = IChatboxState & IChatboxActions;

// ═══════════════════════════════════════════════════════════════
// INITIAL STATE
// ═══════════════════════════════════════════════════════════════

const initialServices: IChatboxServices = {
  conversationService: null,
  chatHistoryManager: null,
  threadManager: null,
  chatService: null,
  messageComponent: null,
  uiHelper: null,
  chatWidget: null,
  chatContainer: null
};

const initialState: IChatboxState = {
  isReady: false,
  isFullyInitialized: false,
  isInitializing: false,
  currentNotebookId: null,
  currentNotebookPath: null,
  lastNotebookId: null,
  isProcessingMessage: false,
  isCancelled: false,
  hasShownWelcomeMessage: false,
  welcomeMessagePreloaded: false,
  isWelcomeMessageHidden: false,
  contextRowVersion: 0,
  services: { ...initialServices }
};

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useChatboxStore = create<IChatboxStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      ...initialState,

      // ─────────────────────────────────────────────────────────────
      // Initialization Actions
      // ─────────────────────────────────────────────────────────────

      initialize: async (notebookId?: string) => {
        const { isInitializing, currentNotebookId } = get();

        // Prevent double initialization
        if (isInitializing) {
          console.log('[ChatboxStore] Already initializing, skipping');
          return;
        }

        // Skip if same notebook
        if (notebookId && notebookId === currentNotebookId) {
          console.log('[ChatboxStore] Same notebook, skipping initialization');
          return;
        }

        set({ isInitializing: true }, false, 'initialize:start');

        try {
          if (notebookId) {
            set(
              {
                currentNotebookId: notebookId,
                lastNotebookId: notebookId
              },
              false,
              'initialize:setNotebook'
            );
          }

          set(
            {
              isReady: true,
              isFullyInitialized: true,
              isInitializing: false
            },
            false,
            'initialize:complete'
          );

          console.log('[ChatboxStore] Initialization complete', {
            notebookId
          });
        } catch (error) {
          console.error('[ChatboxStore] Initialization failed:', error);
          set({ isInitializing: false }, false, 'initialize:error');
        }
      },

      setReady: () => {
        set({ isReady: true, isFullyInitialized: true }, false, 'setReady');
        console.log('[ChatboxStore] Marked as ready and fully initialized');
      },

      setServices: (services: Partial<IChatboxServices>) => {
        set(
          state => ({
            services: { ...state.services, ...services }
          }),
          false,
          'setServices'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Notebook Management Actions
      // ─────────────────────────────────────────────────────────────

      updateNotebookId: (newId: string) => {
        set(
          {
            currentNotebookId: newId,
            lastNotebookId: newId
          },
          false,
          'updateNotebookId'
        );

        // Update services if available
        const { services } = get();
        services.threadManager?.updateNotebookId?.(newId);
        services.conversationService?.updateNotebookId?.(newId);
      },

      updateNotebookPath: (newPath: string) => {
        get().updateNotebookId(newPath);
      },

      setNotebookId: async (notebookId: string | null) => {
        const { lastNotebookId, services } = get();

        if (!notebookId) {
          set({ currentNotebookId: null }, false, 'setNotebookId:clear');
          services.threadManager?.setNotebookId?.(null);
          return;
        }

        if (lastNotebookId === notebookId) {
          return;
        }

        set(
          {
            currentNotebookId: notebookId,
            lastNotebookId: notebookId
          },
          false,
          'setNotebookId'
        );

        services.conversationService?.setNotebookId?.(notebookId);

        // Wait for chat history to load
        const chatHistoryManager = services.chatHistoryManager;
        if (chatHistoryManager?.isLoading?.()) {
          while (chatHistoryManager.isLoading()) {
            await new Promise(resolve => setTimeout(resolve, 50));
          }
        }

        services.threadManager?.setNotebookId?.(notebookId);
      },

      reinitializeForNotebook: async (notebookId: string) => {
        console.log(
          `[ChatboxStore] Re-initializing for notebook: ${notebookId}`
        );

        const { isProcessingMessage, services, currentNotebookId } = get();

        // Skip if same notebook
        if (notebookId === currentNotebookId) {
          console.log(
            `[ChatboxStore] Same notebook ${notebookId}, skipping reinitialize`
          );
          return;
        }

        // Cancel any ongoing message
        if (isProcessingMessage) {
          services.chatService?.cancelRequest?.();
          set({ isProcessingMessage: false }, false, 'reinitialize:cancel');
        }

        // CRITICAL: Clear messages and threads BEFORE setting new notebook ID
        // This prevents stale data from being shown during the transition
        const { useChatMessagesStore } = await import('./chatMessages');
        const { useChatHistoryStore } = await import('./chatHistoryStore');
        const { useChatUIStore } = await import('./chatUIStore');

        // Clear old notebook's messages immediately
        console.log(
          `[ChatboxStore] Clearing messages for notebook switch: ${currentNotebookId} -> ${notebookId}`
        );
        useChatMessagesStore.getState().clearMessages();

        // Clear thread list to prevent showing old threads
        useChatHistoryStore.getState().clearForNotebook();

        // Show new chat display during loading
        useChatUIStore.getState().setShowNewChatDisplay(true);

        set(
          {
            lastNotebookId: null,
            currentNotebookId: notebookId
          },
          false,
          'reinitialize:setNotebook'
        );

        services.conversationService?.setNotebookId?.(notebookId);

        // Wait for chat history to reinitialize
        const chatHistoryManager = services.chatHistoryManager;
        if (chatHistoryManager) {
          await chatHistoryManager.reinitializeForNotebook?.(notebookId);
        }

        // Load threads into the Zustand store
        // This will also load the current thread's messages via loadFromThread
        await useChatHistoryStore.getState().loadThreads(notebookId);

        services.threadManager?.setNotebookId?.(notebookId);

        set({ lastNotebookId: notebookId }, false, 'reinitialize:complete');

        console.log(
          `[ChatboxStore] Re-initialization complete for notebook: ${notebookId}`
        );
      },

      setLastNotebookId: (id: string | null) => {
        set({ lastNotebookId: id }, false, 'setLastNotebookId');
      },

      // ─────────────────────────────────────────────────────────────
      // Processing State Actions
      // ─────────────────────────────────────────────────────────────

      setIsProcessingMessage: (value: boolean) => {
        set({ isProcessingMessage: value }, false, 'setIsProcessingMessage');
      },

      setCancelled: (value: boolean) => {
        set({ isCancelled: value }, false, 'setCancelled');
      },

      // ─────────────────────────────────────────────────────────────
      // Welcome Message Actions
      // ─────────────────────────────────────────────────────────────

      setHasShownWelcomeMessage: (value: boolean) => {
        set(
          { hasShownWelcomeMessage: value },
          false,
          'setHasShownWelcomeMessage'
        );
      },

      setWelcomeMessagePreloaded: (value: boolean) => {
        set(
          { welcomeMessagePreloaded: value },
          false,
          'setWelcomeMessagePreloaded'
        );
      },

      setWelcomeMessageHidden: (value: boolean) => {
        set(
          { isWelcomeMessageHidden: value },
          false,
          'setWelcomeMessageHidden'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Chat Operations
      // ─────────────────────────────────────────────────────────────

      createNewChat: async () => {
        const { services, isProcessingMessage } = get();
        console.log('[ChatboxStore] Creating new chat');

        // Cancel any processing message
        if (isProcessingMessage) {
          services.chatService?.cancelRequest?.();
        }

        // Create new thread via ChatHistoryManager
        const chatHistoryManager = services.chatHistoryManager;
        if (chatHistoryManager) {
          const newThread = chatHistoryManager.createNewThread();
          if (newThread) {
            console.log('[ChatboxStore] New thread created:', newThread.id);

            const { useChatHistoryStore } = await import('./chatHistoryStore');
            const { useChatMessagesStore } = await import('./chatMessages');
            const { useChatUIStore } = await import('./chatUIStore');
            const { useLLMStateStore } = await import('./llmStateStore');
            const { usePlanStateStore } = await import('./planStateStore');

            // Sync threads from ChatHistoryManager to Zustand (single source of truth)
            await useChatHistoryStore.getState().syncFromManager();

            // Clear messages in UI
            useChatMessagesStore.getState().clearMessages();

            // Show new chat display
            useChatUIStore.getState().setShowNewChatDisplay(true);

            // Hide state displays
            useLLMStateStore.getState().hide();
            usePlanStateStore.getState().hide();

            // Clear conversation service action history
            services.conversationService?.clearActionHistory?.();
          }
        } else {
          // Fallback: just clear messages
          services.messageComponent?.clearMessages?.();
        }

        set(
          {
            isProcessingMessage: false,
            isCancelled: false
          },
          false,
          'createNewChat'
        );
      },

      continueMessage: () => {
        const { services, isProcessingMessage } = get();
        if (isProcessingMessage) {
          console.log('[ChatboxStore] Already processing, cannot continue');
          return;
        }
        console.log('[ChatboxStore] Continuing message');
        services.conversationService?.continueConversation?.();
      },

      sendPromptMessage: async (
        prompt: string,
        mode: 'agent' | 'ask' | 'fast' | 'welcome' = 'agent'
      ) => {
        const { services, isProcessingMessage, setIsProcessingMessage } = get();
        const { conversationService } = services;

        if (isProcessingMessage) {
          console.log('[ChatboxStore] Already processing, cannot send prompt');
          return;
        }
        if (!prompt || prompt.trim() === '') {
          console.log('[ChatboxStore] Empty prompt, not sending');
          return;
        }
        if (!conversationService) {
          console.error(
            '[ChatboxStore] No conversationService available for sendPromptMessage'
          );
          return;
        }

        console.log('[ChatboxStore] Sending prompt message:', prompt);

        try {
          setIsProcessingMessage(true);

          // Import stores lazily to avoid circular deps
          const { useChatMessagesStore } = require('./chatMessages');
          const { useChatUIStore } = require('./chatUIStore');
          const store = useChatMessagesStore.getState();

          // Hide the new chat display since we're now sending a message
          useChatUIStore.getState().setShowNewChatDisplay(false);

          // Generate message ID
          const id = `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

          // Create the user message for the LLM
          const userMessage = {
            role: 'user' as const,
            content: prompt,
            id
          };

          // Add user message to the UI (skip for welcome mode - hidden prompt)
          if (mode !== 'welcome') {
            store.addUserMessage(prompt);
          }

          // Add to LLM history so it gets sent to the API
          store.addToLlmHistory(userMessage);

          // Process the conversation
          await conversationService.processConversation(
            [userMessage],
            [],
            mode
          );
        } catch (error) {
          console.error('[ChatboxStore] Error sending prompt message:', error);
        } finally {
          setIsProcessingMessage(false);
        }
      },

      cancelMessage: () => {
        const { services, isProcessingMessage } = get();
        if (!isProcessingMessage) {
          return;
        }
        console.log('[ChatboxStore] Cancelling message');
        services.chatService?.cancelRequest?.();
        set(
          { isProcessingMessage: false, isCancelled: true },
          false,
          'cancelMessage'
        );
      },

      undoLastAction: () => {
        const { services } = get();
        console.log('[ChatboxStore] Undoing last action');
        services.conversationService?.undoLastAction?.();
      },

      // ─────────────────────────────────────────────────────────────
      // Service Access Helpers
      // ─────────────────────────────────────────────────────────────

      getConversationService: () => {
        return get().services.conversationService;
      },

      getChatHistoryManager: () => {
        return get().services.chatHistoryManager;
      },

      getMessageComponent: () => {
        return get().services.messageComponent;
      },

      // ─────────────────────────────────────────────────────────────
      // Context Operations
      // ─────────────────────────────────────────────────────────────

      onCellAddedToContext: (path: string) => {
        console.log('[ChatboxStore] Cell added to context:', path);
        // Increment contextRowVersion to trigger re-render in ChatInputContainer
        set(
          state => ({ contextRowVersion: state.contextRowVersion + 1 }),
          false,
          'onCellAddedToContext'
        );
      },

      onCellRemovedFromContext: (path: string) => {
        console.log('[ChatboxStore] Cell removed from context:', path);
        // Increment contextRowVersion to trigger re-render in ChatInputContainer
        set(
          state => ({ contextRowVersion: state.contextRowVersion + 1 }),
          false,
          'onCellRemovedFromContext'
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Widget UI Operations
      // ─────────────────────────────────────────────────────────────

      showHistoryWidget: () => {
        const { services } = get();
        if (services.chatWidget?.showHistoryWidget) {
          services.chatWidget.showHistoryWidget();
        } else {
          console.warn(
            '[ChatboxStore] chatWidget not available for showHistoryWidget'
          );
        }
      },

      showWelcomeMessage: async () => {
        const { hasShownWelcomeMessage, isProcessingMessage, services } = get();
        const { conversationService } = services;

        // Don't show if already shown or if processing a message
        if (hasShownWelcomeMessage || isProcessingMessage) {
          console.log(
            '[ChatboxStore] Welcome message already shown or processing, skipping'
          );
          return;
        }

        // Check if conversationService is available before attempting to send
        if (!conversationService) {
          console.log(
            '[ChatboxStore] No conversationService available for welcome message, skipping'
          );
          return;
        }

        console.log('[ChatboxStore] Sending welcome message to LLM');

        // Show launcher welcome loader via React state (rendered in ChatMessagesPanel)
        // This hides the "New Chat" display and shows the loader while preparing context
        const { useChatUIStore } = require('./chatUIStore');
        useChatUIStore.getState().setShowNewChatDisplay(false);
        useChatUIStore.getState().setShowLauncherWelcomeLoader(true);

        // Ensure workspace context is loaded for welcome mode
        // This provides file/notebook information for the welcome message
        const { getWorkspaceContext } = require('./appStore');
        let workspaceContext = getWorkspaceContext();

        if (!workspaceContext || !workspaceContext.welcome_context) {
          console.log(
            '[ChatboxStore] Workspace context not loaded, waiting for deferred fetch...'
          );

          try {
            // Wait for the already-scheduled workspace-context task instead of starting a new fetch
            // This task is scheduled at 'normal' priority in activateSignalPilot.ts
            const { deferredInit } = require('../utils/deferredInit');
            await deferredInit.waitFor('workspace-context');
            workspaceContext = getWorkspaceContext();
            console.log(
              '[ChatboxStore] Workspace context loaded:',
              !!workspaceContext?.welcome_context
            );
          } catch (error) {
            console.warn(
              '[ChatboxStore] Failed to wait for workspace context:',
              error
            );
          }
        } else {
          console.log('[ChatboxStore] Workspace context already loaded');
        }

        // Note: The loader will be hidden by StreamingUIHandler via useChatUIStore.setShowLauncherWelcomeLoader(false)

        // Mark as shown to prevent duplicate sends
        set(
          { hasShownWelcomeMessage: true },
          false,
          'showWelcomeMessage:markShown'
        );

        // Send "Create Welcome Message" to the LLM - this is the hidden prompt
        // that triggers the AI to generate a welcome message
        // Use 'welcome' mode which has limited tools (no bash_code_execution, etc.)
        await get().sendPromptMessage('Create Welcome Message', 'welcome');
      },

      startWelcomeMessagePreload: async () => {
        const { services } = get();
        if (services.chatWidget?.startWelcomeMessagePreload) {
          await services.chatWidget.startWelcomeMessagePreload();
        } else {
          console.warn(
            '[ChatboxStore] chatWidget not available for startWelcomeMessagePreload'
          );
        }
      },

      getStateDisplayContainer: () => {
        const { services } = get();
        if (services.chatWidget?.getStateDisplayContainer) {
          return services.chatWidget.getStateDisplayContainer();
        }
        console.warn(
          '[ChatboxStore] chatWidget not available for getStateDisplayContainer'
        );
        return null;
      },

      updateDynamicBottomPositions: () => {
        const { services } = get();
        if (services.chatWidget?.updateDynamicBottomPositions) {
          services.chatWidget.updateDynamicBottomPositions();
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Launcher Operations
      // ─────────────────────────────────────────────────────────────

      attachToLauncher: (launcherBody: HTMLElement) => {
        const { services } = get();
        const chatContainer = services.chatContainer;

        if (!chatContainer) {
          console.warn(
            '[ChatboxStore] Cannot attach to launcher - chatContainer not available'
          );
          return false;
        }

        try {
          // Create wrapper div for launcher
          const wrapper = document.createElement('div');
          wrapper.className = 'sage-chatbox-launcher-wrapper';

          // Move the chatContainer's node to the wrapper (DOM-level move, not Lumino detach)
          // This keeps the widget "attached" in Lumino's sense but physically moves its DOM node
          wrapper.appendChild(chatContainer.node);

          // Insert wrapper as the first child of launcher body (not append)
          // This ensures the chatbox appears at the top of the launcher
          if (launcherBody.firstChild) {
            launcherBody.insertBefore(wrapper, launcherBody.firstChild);
          } else {
            launcherBody.appendChild(wrapper);
          }

          // Remove the lm-mod-hidden class that may have been set by the sidebar
          // This class is set by Lumino when a widget is hidden in the shell
          chatContainer.node.classList.remove('lm-mod-hidden');

          // Reset inline styles that were set by the shell's layout manager
          // These absolute positioning styles don't work in the launcher context
          chatContainer.node.style.position = 'relative';
          chatContainer.node.style.top = '';
          chatContainer.node.style.left = '';
          chatContainer.node.style.width = '100%';
          chatContainer.node.style.height = '100%';
          chatContainer.node.style.contain = '';

          // Force React to re-render in the new location
          if (chatContainer.update) {
            chatContainer.update();
          }

          console.log('[ChatboxStore] Chatbox attached to launcher');
          return true;
        } catch (error) {
          console.error('[ChatboxStore] Error attaching to launcher:', error);
          return false;
        }
      },

      detachFromLauncher: () => {
        const { services } = get();
        const chatContainer = services.chatContainer;

        if (!chatContainer) {
          console.warn(
            '[ChatboxStore] Cannot detach from launcher - chatContainer not available'
          );
          return;
        }

        try {
          // Find and remove the launcher wrapper
          const launcherBody = document.querySelector('.jp-Launcher-content');
          const wrapper = launcherBody?.querySelector(
            '.sage-chatbox-launcher-wrapper'
          );

          if (wrapper) {
            // Remove the chatContainer's node from the wrapper first
            if (chatContainer.node.parentNode === wrapper) {
              wrapper.removeChild(chatContainer.node);
            }

            // Remove wrapper from launcher
            wrapper.remove();

            console.log('[ChatboxStore] Chatbox detached from launcher');
          }
        } catch (error) {
          console.error('[ChatboxStore] Error detaching from launcher:', error);
        }
      },

      isAttachedToLauncher: () => {
        const launcherBody = document.querySelector('.jp-Launcher-content');
        const wrapper = launcherBody?.querySelector(
          '.sage-chatbox-launcher-wrapper'
        );
        return !!wrapper;
      },

      // ─────────────────────────────────────────────────────────────
      // Cleanup Actions
      // ─────────────────────────────────────────────────────────────

      reset: () => {
        set({ ...initialState }, false, 'reset');
      },

      dispose: () => {
        console.log('[ChatboxStore] Disposing');
        set({ ...initialState }, false, 'dispose');
      }
    })),
    {
      name: 'ChatboxStore',
      // Prevent DevTools from serializing large service objects
      serialize: {
        replacer: (_key: string, value: unknown) => {
          // Skip service objects that contain class instances
          if (
            value &&
            typeof value === 'object' &&
            'conversationService' in value
          ) {
            return '[Services - not serialized]';
          }
          return value;
        }
      }
    }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectIsReady = (state: IChatboxStore) => state.isReady;
export const selectIsFullyInitialized = (state: IChatboxStore) =>
  state.isFullyInitialized;
export const selectIsInitializing = (state: IChatboxStore) =>
  state.isInitializing;
export const selectCurrentNotebookId = (state: IChatboxStore) =>
  state.currentNotebookId;
export const selectIsProcessingMessage = (state: IChatboxStore) =>
  state.isProcessingMessage;
export const selectHasShownWelcomeMessage = (state: IChatboxStore) =>
  state.hasShownWelcomeMessage;
export const selectServices = (state: IChatboxStore) => state.services;

// ═══════════════════════════════════════════════════════════════
// NON-REACT API (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the store's current state (for use outside React)
 */
export const getChatboxState = () => useChatboxStore.getState();

/**
 * Subscribe to store changes (for use outside React)
 */
export const subscribeToChatbox = (
  callback: (state: IChatboxState) => void
) => {
  return useChatboxStore.subscribe(callback);
};

/**
 * Subscribe to notebook ID changes
 */
export const subscribeToNotebookId = (
  callback: (notebookId: string | null) => void
) => {
  return useChatboxStore.subscribe(state => state.currentNotebookId, callback);
};

/**
 * Subscribe to processing state changes
 */
export const subscribeToProcessing = (
  callback: (isProcessing: boolean) => void
) => {
  return useChatboxStore.subscribe(
    state => state.isProcessingMessage,
    callback
  );
};

/**
 * Subscribe to ready state changes
 */
export const subscribeToReady = (callback: (isReady: boolean) => void) => {
  return useChatboxStore.subscribe(state => state.isReady, callback);
};

// ═══════════════════════════════════════════════════════════════
// SERVICE ACCESS HELPERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the conversation service from the store
 */
export const getConversationService = () => {
  return useChatboxStore.getState().services.conversationService;
};

/**
 * Get the chat history manager from the store
 */
export const getChatHistoryManager = () => {
  return useChatboxStore.getState().services.chatHistoryManager;
};

/**
 * Get the message component from the store
 */
export const getMessageComponent = () => {
  return useChatboxStore.getState().services.messageComponent;
};

/**
 * Check if the chatbox UI is fully initialized (for UI operations like launcher attachment)
 */
export const isChatboxReady = () => {
  return useChatboxStore.getState().isFullyInitialized;
};

/**
 * Check if the chatbox is ready to send messages (conversationService available)
 * Use this for operations that need to send messages to the LLM
 */
export const isMessagingReady = () => {
  const state = useChatboxStore.getState();
  return state.isFullyInitialized && !!state.services.conversationService;
};

// ═══════════════════════════════════════════════════════════════
// WIDGET UI HELPERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Show the chat history widget UI
 */
export const showHistoryWidget = () => {
  useChatboxStore.getState().showHistoryWidget();
};

/**
 * Show the welcome message
 */
export const showWelcomeMessage = async () => {
  await useChatboxStore.getState().showWelcomeMessage();
};

/**
 * Start preloading the welcome message
 */
export const startWelcomeMessagePreload = async () => {
  await useChatboxStore.getState().startWelcomeMessagePreload();
};

/**
 * Get the state display container element
 */
export const getStateDisplayContainer = () => {
  return useChatboxStore.getState().getStateDisplayContainer();
};

/**
 * Update dynamic bottom positions
 */
export const updateDynamicBottomPositions = () => {
  useChatboxStore.getState().updateDynamicBottomPositions();
};

// ═══════════════════════════════════════════════════════════════
// LAUNCHER HELPERS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Attach the chatbox to the launcher
 */
export const attachChatboxToLauncher = (launcherBody: HTMLElement) => {
  return useChatboxStore.getState().attachToLauncher(launcherBody);
};

/**
 * Detach the chatbox from the launcher
 */
export const detachChatboxFromLauncher = () => {
  useChatboxStore.getState().detachFromLauncher();
};

/**
 * Check if the chatbox is attached to the launcher
 */
export const isChatboxAttachedToLauncher = () => {
  return useChatboxStore.getState().isAttachedToLauncher();
};
