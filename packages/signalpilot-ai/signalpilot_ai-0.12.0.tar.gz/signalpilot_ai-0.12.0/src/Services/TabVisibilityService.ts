/**
 * TabVisibilityService
 *
 * Manages tab visibility state to prevent API calls from stale/hidden tabs.
 * This helps reduce 404 errors when users have multiple tabs open and
 * sessions change or expire.
 */

type VisibilityCallback = (isVisible: boolean) => void;

class TabVisibilityServiceClass {
  private _isVisible: boolean = true;
  private _callbacks: Set<VisibilityCallback> = new Set();
  private _initialized: boolean = false;

  /**
   * Initialize the service - should be called once at app startup
   */
  public initialize(): void {
    if (this._initialized) {
      return;
    }

    this._isVisible = !document.hidden;
    this._initialized = true;

    document.addEventListener('visibilitychange', this._handleVisibilityChange);

    console.log(
      '[TabVisibilityService] Initialized, tab is currently:',
      this._isVisible ? 'visible' : 'hidden'
    );
  }

  /**
   * Clean up event listeners
   */
  public dispose(): void {
    document.removeEventListener(
      'visibilitychange',
      this._handleVisibilityChange
    );
    this._callbacks.clear();
    this._initialized = false;
  }

  /**
   * Check if the tab is currently visible
   */
  public get isVisible(): boolean {
    return this._isVisible;
  }

  /**
   * Check if polling should be active (tab is visible)
   */
  public shouldPoll(): boolean {
    return this._isVisible;
  }

  /**
   * Subscribe to visibility changes
   * @param callback Function to call when visibility changes
   * @returns Unsubscribe function
   */
  public subscribe(callback: VisibilityCallback): () => void {
    this._callbacks.add(callback);
    return () => {
      this._callbacks.delete(callback);
    };
  }

  /**
   * Execute a callback only if the tab is visible
   * @param callback Function to execute if visible
   */
  public executeIfVisible<T>(callback: () => T): T | undefined {
    if (this._isVisible) {
      return callback();
    }
    return undefined;
  }

  /**
   * Execute an async callback only if the tab is visible
   * @param callback Async function to execute if visible
   */
  public async executeIfVisibleAsync<T>(
    callback: () => Promise<T>
  ): Promise<T | undefined> {
    if (this._isVisible) {
      return callback();
    }
    return undefined;
  }

  private _handleVisibilityChange = (): void => {
    const wasVisible = this._isVisible;
    this._isVisible = !document.hidden;

    if (wasVisible !== this._isVisible) {
      console.log(
        '[TabVisibilityService] Tab visibility changed:',
        this._isVisible ? 'visible' : 'hidden'
      );

      // Notify all subscribers
      this._callbacks.forEach(callback => {
        try {
          callback(this._isVisible);
        } catch (error) {
          console.error(
            '[TabVisibilityService] Error in visibility callback:',
            error
          );
        }
      });
    }
  };
}

// Export singleton instance
export const TabVisibilityService = new TabVisibilityServiceClass();
