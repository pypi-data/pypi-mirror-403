/**
 * ChatBoxReactWrapper
 *
 * A Lumino Widget wrapper for the pure React ChatBox component.
 * This allows the ChatBox to be used within JupyterLab's widget system
 * while keeping all logic in pure React.
 *
 * Usage:
 * ```typescript
 * const chatWrapper = new ChatBoxReactWrapper(tracker, app);
 * app.shell.add(chatWrapper, 'right');
 * ```
 */

import { ReactWidget } from '@jupyterlab/ui-components';
import { INotebookTracker } from '@jupyterlab/notebook';
import { JupyterFrontEnd } from '@jupyterlab/application';
import * as React from 'react';
import { ChatBox, ChatBoxProps } from './index';
import { JupyterLabProvider } from '@/contexts/JupyterLabContext';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface ChatBoxReactWrapperOptions {
  /** Notebook tracker for accessing notebooks */
  tracker?: INotebookTracker;
  /** JupyterLab application instance */
  app?: JupyterFrontEnd;
  /** Initial notebook ID */
  initialNotebookId?: string;
  /** Callback when ready */
  onReady?: () => void;
}

// ═══════════════════════════════════════════════════════════════
// WRAPPER COMPONENT
// ═══════════════════════════════════════════════════════════════

/**
 * Internal React component that renders ChatBox with JupyterLab context
 */
interface ChatBoxWithContextProps extends ChatBoxProps {
  tracker?: INotebookTracker;
  app?: JupyterFrontEnd;
}

function ChatBoxWithContext({
  tracker,
  app,
  ...chatBoxProps
}: ChatBoxWithContextProps): JSX.Element {
  return (
    <JupyterLabProvider tracker={tracker} app={app}>
      <ChatBox {...chatBoxProps} />
    </JupyterLabProvider>
  );
}

// ═══════════════════════════════════════════════════════════════
// LUMINO WIDGET WRAPPER
// ═══════════════════════════════════════════════════════════════

/**
 * ChatBoxReactWrapper - Lumino Widget wrapper for React ChatBox
 *
 * This class wraps the pure React ChatBox component in a Lumino Widget
 * so it can be used within JupyterLab's widget system.
 */
export class ChatBoxReactWrapper extends ReactWidget {
  private _tracker: INotebookTracker | undefined;
  private _app: JupyterFrontEnd | undefined;
  private _initialNotebookId: string | undefined;
  private _onReady: (() => void) | undefined;

  constructor(options: ChatBoxReactWrapperOptions = {}) {
    super();

    this._tracker = options.tracker;
    this._app = options.app;
    this._initialNotebookId = options.initialNotebookId;
    this._onReady = options.onReady;

    // Set up widget properties
    this.id = 'sage-ai-chatbox-react-wrapper';
    this.title.label = 'Chat';
    this.title.caption = 'SignalPilot AI Chat';
    this.title.closable = true;

    // Add CSS class for styling
    this.addClass('sage-ai-chatbox-wrapper');
  }

  /**
   * Set the notebook tracker
   */
  setTracker(tracker: INotebookTracker): void {
    this._tracker = tracker;
    this.update();
  }

  /**
   * Set the JupyterLab app
   */
  setApp(app: JupyterFrontEnd): void {
    this._app = app;
    this.update();
  }

  /**
   * Set the initial notebook ID
   */
  setNotebookId(notebookId: string): void {
    this._initialNotebookId = notebookId;
    this.update();
  }

  /**
   * Render the React component
   */
  protected render(): JSX.Element {
    return (
      <ChatBoxWithContext
        tracker={this._tracker}
        app={this._app}
        initialNotebookId={this._initialNotebookId}
        onReady={this._onReady}
      />
    );
  }
}

// ═══════════════════════════════════════════════════════════════
// FACTORY FUNCTION
// ═══════════════════════════════════════════════════════════════

/**
 * Create a new ChatBoxReactWrapper instance
 */
export function createChatBoxWrapper(
  options: ChatBoxReactWrapperOptions = {}
): ChatBoxReactWrapper {
  return new ChatBoxReactWrapper(options);
}

export default ChatBoxReactWrapper;
