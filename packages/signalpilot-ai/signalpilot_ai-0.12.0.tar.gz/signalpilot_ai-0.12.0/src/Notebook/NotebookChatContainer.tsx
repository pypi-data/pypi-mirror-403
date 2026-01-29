import * as React from 'react';
import { ReactWidget } from '@jupyterlab/ui-components';
import { ToolService } from '../LLM/ToolService';
import { NotebookContextManager } from './NotebookContextManager';
import {
  subscribeToNotebookChange,
  useNotebookEventsStore
} from '../stores/notebookEventsStore';
import { useServicesStore } from '../stores/servicesStore';
import { useAppStore } from '../stores/appStore';
import { ActionHistory } from '@/ChatBox/services/ActionHistory';
import { ChatBox } from '@/ChatBox';
import { useChatboxStore } from '../stores/chatboxStore';
import { useChatHistoryStore } from '../stores/chatHistoryStore';

/**
 * React component for the chat container
 * Now uses the pure React ChatBox component
 */
function ChatContainerContent({
  onReady
}: {
  onReady?: () => void;
}): JSX.Element {
  // Get notebook ID directly from store for immediate updates
  const notebookId = useNotebookEventsStore(state => state.currentNotebookId);

  // Debug logging
  console.log('[ChatContainerContent] Rendering with notebookId:', notebookId);

  return (
    <div className="sage-ai-chat-container-inner h-100">
      <ChatBox onReady={onReady} className="h-100" />
    </div>
  );
}

/**
 * Container widget that holds the chat interface
 *
 * This is the new implementation using pure React ChatBox component
 * instead of the legacy ChatBoxWidget.
 */
export class NotebookChatContainer extends ReactWidget {
  private toolService: ToolService;
  private contextManager: NotebookContextManager | null;
  private actionHistory: ActionHistory;
  private currentNotebookId: string | null = null;
  private _isReady: boolean = false;

  constructor(
    toolService: ToolService,
    contextManager: NotebookContextManager | null | undefined,
    actionHistory: ActionHistory
  ) {
    super();

    this.id = 'sage-ai-chat-container';
    this.title.label = 'SignalPilot AI Chat';
    this.title.closable = true;
    this.addClass('sage-ai-chat-container');
    this.toolService = toolService;
    this.contextManager = contextManager || null;
    this.actionHistory = actionHistory;

    // Set the minimum width of the widget's node
    this.node.style.minWidth = '320px';

    // Initialize the chatbox store with services
    this.initializeStoreServices();

    // Subscribe to notebook changes from store
    subscribeToNotebookChange(async ({ newNotebookId, fromLauncher }) => {
      if (
        newNotebookId &&
        (fromLauncher || newNotebookId !== this.currentNotebookId)
      ) {
        await this.switchToNotebook(newNotebookId, fromLauncher);
      }
    });
  }

  /**
   * Legacy compatibility: get chatWidget property
   * Returns a compatibility object for code that expects chatWidget
   */
  public get chatWidget(): any {
    // Return a compatibility shim that redirects to store actions
    return {
      isFullyReady: () => this.isFullyReady(),
      setInputValue: (value: string) => {
        const {
          useChatInputStore
        } = require('../stores/chatInput/chatInputStore');
        useChatInputStore.getState().setInputValue(value);
      },
      sendMessage: async () => {
        // Trigger send through store
        console.log('[NotebookChatContainer] sendMessage called via shim');
      },
      cancelMessage: () => {
        // Cancel message through store
        console.log('[NotebookChatContainer] cancelMessage called via shim');
        useChatboxStore.getState().cancelMessage();
      },
      startWelcomeMessagePreload: () => {
        useChatboxStore.getState().setWelcomeMessagePreloaded(true);
      },
      showWelcomeMessage: () => {
        useChatboxStore.getState().setHasShownWelcomeMessage(true);
      },
      reinitializeForNotebook: async (notebookId: string) => {
        await this.switchToNotebook(notebookId, true);
      },
      setNotebookId: async (notebookId: string) => {
        await this.switchToNotebook(notebookId, false);
      },
      updateNotebookPath: (path: string) => {
        useChatboxStore.getState().updateNotebookPath(path);
      },
      onCellAddedToContext: (path: string) => this.onCellAddedToContext(path),
      onCellRemovedFromContext: (path: string) =>
        this.onCellRemovedFromContext(path),
      updateTokenProgress: () => {
        // Token progress is handled by ChatInputContainer's internal state
        // This triggers a recalculation via the store
        const services = useChatboxStore.getState().services;
        if (services.messageComponent) {
          const messages = services.messageComponent.getMessageHistory();
          // The actual token calculation happens in ChatInputContainer
          // This is a no-op here since token progress is managed reactively
          console.log(
            '[NotebookChatContainer] updateTokenProgress called, messages:',
            messages.length
          );
        }
      },
      // Expose messageComponent for legacy code that accesses chatWidget.messageComponent
      get messageComponent() {
        return useChatboxStore.getState().services.messageComponent;
      },
      // threadManager is null - its functionality is handled by ChatHistoryManager directly
      threadManager: null,
      // Expose chatHistoryManager for legacy code that accesses it
      get chatHistoryManager() {
        return useChatboxStore.getState().services.chatHistoryManager;
      },
      // Expose llmStateDisplay for legacy code that accesses it
      get llmStateDisplay() {
        return useServicesStore.getState().llmStateDisplay;
      },
      // Expose conversationService for legacy code that accesses it
      get conversationService() {
        return useChatboxStore.getState().services.conversationService;
      },
      isDisposed: this.isDisposed
    };
  }

  /**
   * Render the React component
   */
  render(): JSX.Element {
    return (
      <ChatContainerContent
        onReady={() => {
          this._isReady = true;
          console.log('[NotebookChatContainer] ChatBox is ready');
        }}
      />
    );
  }

  /**
   * Check if the chat is fully ready
   */
  public isFullyReady(): boolean {
    return this._isReady && useChatboxStore.getState().isReady;
  }

  public updateNotebookId(oldNotebookId: string, newNotebookId: string): void {
    this.contextManager?.updateNotebookId(oldNotebookId, newNotebookId);

    // Update through stores
    useChatboxStore.getState().updateNotebookId(newNotebookId);

    this.toolService.updateNotebookId(oldNotebookId, newNotebookId);
    this.currentNotebookId = newNotebookId;
  }

  /**
   * Switch to a different notebook
   */
  public async switchToNotebook(
    notebookId: string,
    fromLauncher?: boolean
  ): Promise<void> {
    console.log('[NotebookChatContainer] Switching to notebook:', notebookId);
    console.log('[NotebookChatContainer] From launcher:', fromLauncher);

    if (!fromLauncher && this.currentNotebookId === notebookId) {
      return;
    }

    const previousNotebookId = this.currentNotebookId;
    this.currentNotebookId = notebookId;

    // Update the tool service
    this.toolService.setCurrentNotebookId(notebookId);

    // Update context manager
    if (this.contextManager) {
      this.contextManager.getContext(notebookId);
    }

    // Update stores
    if (fromLauncher || !previousNotebookId) {
      console.log('[NotebookChatContainer] Full re-initialization');
      if (useAppStore.getState().isDemoMode) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      await useChatboxStore.getState().reinitializeForNotebook(notebookId);
    } else {
      await useChatboxStore.getState().setNotebookId(notebookId);
    }

    // Load threads for this notebook
    await useChatHistoryStore.getState().loadThreads(notebookId);

    // Force re-render
    this.update();
  }

  /**
   * Handle a cell added to context
   */
  public onCellAddedToContext(notebookId: string): void {
    if (!this.currentNotebookId || this.currentNotebookId !== notebookId) {
      console.warn(
        `Cannot add cell from ${notebookId} to context when current notebook is ${this.currentNotebookId}`
      );
      return;
    }
    useChatboxStore.getState().onCellAddedToContext(notebookId);
  }

  /**
   * Handle a cell removed from context
   */
  public onCellRemovedFromContext(notebookId: string): void {
    if (!this.currentNotebookId || this.currentNotebookId !== notebookId) {
      console.warn(
        `Cannot remove cell from ${notebookId} context when current notebook is ${this.currentNotebookId}`
      );
      return;
    }
    useChatboxStore.getState().onCellRemovedFromContext(notebookId);
  }

  /**
   * Initialize the chatbox store with service references
   */
  private initializeStoreServices(): void {
    // Get services from servicesStore
    const servicesState = useServicesStore.getState();

    useChatboxStore.getState().setServices({
      conversationService: null, // Will be wired later
      chatHistoryManager: null, // Will be wired later
      threadManager: null, // Will be set when available
      chatService: servicesState.chatService || null,
      messageComponent: null, // Will be set when ChatBox mounts
      uiHelper: null
    });
  }
}
