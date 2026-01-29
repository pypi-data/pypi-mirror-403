// Bridge for external code to interact with chat UI
import { useChatStore } from './chat';

export interface ISendMessageOptions {
  hidden?: boolean;
  cellContext?: string;
  mode?: 'agent' | 'ask' | 'fast';
}

export interface IUIBridgeHandlers {
  sendMessage: (text: string, options?: ISendMessageOptions) => Promise<void>;
  focusInput: () => void;
  getInputValue: () => string;
  setInputValue: (text: string) => void;
  clearInput: () => void;
  scrollToBottom: () => void;
  cancelMessage: () => void;
  createNewChat: () => Promise<void>;
  showHistoryWidget: () => void;
  showNewChatDisplay: () => void;
  addSystemMessage: (message: string) => void;
  addErrorMessage: (message: string) => void;
}

export type IPartialUIBridgeHandlers = Partial<IUIBridgeHandlers>;

class UIBridge {
  private handlers: IPartialUIBridgeHandlers = {};
  private pendingMessages: Array<{
    text: string;
    options?: ISendMessageOptions;
    resolve: () => void;
    reject: (error: Error) => void;
  }> = [];
  private isReady = false;

  get ready(): boolean {
    return this.isReady;
  }

  registerHandlers(handlers: IPartialUIBridgeHandlers): () => void {
    this.handlers = { ...this.handlers, ...handlers };
    this.isReady = true;
    this.processPendingMessages();

    return () => {
      Object.keys(handlers).forEach(key => {
        if (
          this.handlers[key as keyof IUIBridgeHandlers] ===
          handlers[key as keyof IUIBridgeHandlers]
        ) {
          delete this.handlers[key as keyof IUIBridgeHandlers];
        }
      });
      this.isReady = Object.keys(this.handlers).length > 0;
    };
  }

  async sendMessage(
    text: string,
    options?: ISendMessageOptions
  ): Promise<void> {
    if (this.handlers.sendMessage)
      return this.handlers.sendMessage(text, options);

    return new Promise((resolve, reject) => {
      this.pendingMessages.push({ text, options, resolve, reject });
      setTimeout(() => {
        const idx = this.pendingMessages.findIndex(
          m => m.text === text && m.resolve === resolve
        );
        if (idx !== -1) {
          this.pendingMessages.splice(idx, 1);
          reject(new Error('Timeout waiting for handlers'));
        }
      }, 10000);
    });
  }

  focusInput() {
    this.handlers.focusInput?.();
  }

  getInputValue(): string {
    return this.handlers.getInputValue?.() || '';
  }

  setInputValue(text: string) {
    this.handlers.setInputValue?.(text);
  }

  clearInput() {
    this.handlers.clearInput?.();
  }

  scrollToBottom() {
    this.handlers.scrollToBottom?.();
  }

  cancelMessage() {
    if (this.handlers.cancelMessage) {
      this.handlers.cancelMessage();
    } else {
      useChatStore.getState().setProcessing(false);
      useChatStore.getState().endStreaming();
    }
  }

  async createNewChat(): Promise<void> {
    if (this.handlers.createNewChat) return this.handlers.createNewChat();
    useChatStore.getState().createThread();
  }

  showHistoryWidget() {
    this.handlers.showHistoryWidget?.() ||
      useChatStore.getState().setShowNewChatDisplay(false);
  }

  showNewChatDisplay() {
    this.handlers.showNewChatDisplay?.() ||
      useChatStore.getState().setShowNewChatDisplay(true);
  }

  addSystemMessage(message: string) {
    if (this.handlers.addSystemMessage) {
      this.handlers.addSystemMessage(message);
    } else {
      useChatStore.getState().addMessage({ role: 'system', content: message });
    }
  }

  addErrorMessage(message: string) {
    if (this.handlers.addErrorMessage) {
      this.handlers.addErrorMessage(message);
    } else {
      useChatStore.getState().setError(message);
      useChatStore
        .getState()
        .addMessage({ role: 'assistant', content: `❌ ${message}` });
    }
  }

  private async processPendingMessages(): Promise<void> {
    if (!this.handlers.sendMessage || this.pendingMessages.length === 0) return;
    const msgs = [...this.pendingMessages];
    this.pendingMessages = [];
    for (const { text, options, resolve, reject } of msgs) {
      try {
        await this.handlers.sendMessage(text, options);
        resolve();
      } catch (e) {
        reject(e instanceof Error ? e : new Error(String(e)));
      }
    }
  }
}

export const uiBridge = new UIBridge();

export function useUIBridgeHandlers(handlers: IPartialUIBridgeHandlers): void {
  const { useEffect } = require('react');
  useEffect(() => uiBridge.registerHandlers(handlers), [handlers]);
}
