import { PartialJSONValue } from '@lumino/coreutils';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

/**
 * Backend Cache Service - Replaces StateDBCachingService with HTTP-based caching
 * This service provides the same API as StateDBCachingService but stores data
 * in the robust backend cache system instead of JupyterLab's StateDB.
 */
export class BackendCacheService {
  private static readonly NAMESPACE = 'signalpilot-ai';
  private static serverSettings: ServerConnection.ISettings;

  /**
   * Initialize the backend cache service
   */
  public static initialize(serverSettings?: ServerConnection.ISettings): void {
    BackendCacheService.serverSettings =
      serverSettings || ServerConnection.makeSettings();
  }

  /**
   * Get a value from the backend cache
   * @param key The setting key
   * @param defaultValue The default value if setting doesn't exist
   * @returns The setting value or default
   */
  public static async getValue<T>(key: string, defaultValue: T): Promise<T> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          const response =
            await BackendCacheService.makeRequest('chat-histories');
          return (response.chat_histories || defaultValue) as T;
        } else {
          // Individual chat history
          const response = await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`
          );
          return (response.history || defaultValue) as T;
        }
      } else {
        // Handle app values
        const response = await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`
        );
        return (
          response.value !== undefined && response.value !== null
            ? response.value
            : defaultValue
        ) as T;
      }
    } catch (error) {
      console.warn(
        `[BackendCacheService] Failed to get value '${key}':`,
        error
      );
      return defaultValue;
    }
  }

  /**
   * Set a value in the backend cache
   * @param key The setting key
   * @param value The value to set
   */
  public static async setValue(
    key: string,
    value: PartialJSONValue
  ): Promise<void> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          await BackendCacheService.makeRequest('chat-histories', 'POST', {
            chat_histories: value
          });
        } else {
          // Individual chat history
          await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`,
            'POST',
            {
              history: value
            }
          );
        }
      } else {
        // Handle app values
        await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`,
          'POST',
          {
            value: value
          }
        );
      }
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to set value '${key}':`,
        error
      );
      throw error;
    }
  }

  /**
   * Remove a value from the backend cache
   * @param key The setting key to remove
   */
  public static async removeValue(key: string): Promise<void> {
    try {
      if (BackendCacheService.isChatHistoryKey(key)) {
        // Handle chat history keys
        if (key === 'chatHistories') {
          await BackendCacheService.makeRequest('chat-histories', 'DELETE');
        } else {
          // Individual chat history
          await BackendCacheService.makeRequest(
            `chat-histories/${encodeURIComponent(key)}`,
            'DELETE'
          );
        }
      } else {
        // Handle app values
        await BackendCacheService.makeRequest(
          `app-values/${encodeURIComponent(key)}`,
          'DELETE'
        );
      }
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to remove value '${key}':`,
        error
      );
      throw error;
    }
  }

  /**
   * Get an object value (for complex data like arrays, objects)
   */
  public static async getObjectValue<T>(
    key: string,
    defaultValue: T
  ): Promise<T> {
    return BackendCacheService.getValue(key, defaultValue);
  }

  /**
   * Set an object value (for complex data like arrays, objects)
   */
  public static async setObjectValue<T>(key: string, value: T): Promise<void> {
    return BackendCacheService.setValue(key, value as PartialJSONValue);
  }

  /**
   * Check if the backend cache service is available
   */
  public static async isAvailable(): Promise<boolean> {
    try {
      const response = await BackendCacheService.makeRequest('info');
      return response.available === true;
    } catch (error) {
      console.warn(
        '[BackendCacheService] Service availability check failed:',
        error
      );
      return false;
    }
  }

  /**
   * List all keys in the namespace (for debugging purposes)
   */
  public static async listKeys(): Promise<string[]> {
    try {
      const [chatResponse, appResponse] = await Promise.all([
        BackendCacheService.makeRequest('chat-histories'),
        BackendCacheService.makeRequest('app-values')
      ]);

      const chatKeys = Object.keys(chatResponse.chat_histories || {});
      const appKeys = Object.keys(appResponse.app_values || {});

      return [...chatKeys, ...appKeys];
    } catch (error) {
      console.error('[BackendCacheService] Failed to list keys:', error);
      return [];
    }
  }

  /**
   * Get cache service information
   */
  public static async getCacheInfo(): Promise<any> {
    try {
      return await BackendCacheService.makeRequest('info');
    } catch (error) {
      console.error('[BackendCacheService] Failed to get cache info:', error);
      return {
        available: false,
        error: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Get the server settings, creating default ones if not initialized
   */
  private static getServerSettings(): ServerConnection.ISettings {
    if (!BackendCacheService.serverSettings) {
      BackendCacheService.serverSettings = ServerConnection.makeSettings();
    }
    return BackendCacheService.serverSettings;
  }

  /**
   * Make a request to the backend cache API
   */
  private static async makeRequest(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const settings = BackendCacheService.getServerSettings();
    const url = URLExt.join(
      settings.baseUrl,
      'signalpilot-ai',
      'cache',
      endpoint
    );

    const requestInit: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json'
      }
    };

    if (body !== undefined) {
      requestInit.body = JSON.stringify(body);
    }

    try {
      const response = await ServerConnection.makeRequest(
        url,
        requestInit,
        settings
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error(
          `Backend cache request failed: ${response.status} ${errorText}`
        );
        throw new Error(`Cache request failed: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Backend cache service error for ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Determine if a key should be stored as chat history or app value
   */
  private static isChatHistoryKey(key: string): boolean {
    const chatKeys = [
      'chatHistories',
      'chat-history-notebook-',
      'chat-thread-',
      'chat-message-'
    ];
    return chatKeys.some(prefix => key.includes(prefix));
  }

  // ==================== User Rules API (markdown files) ====================

  /**
   * Make a request to the user rules API
   */
  private static async makeRulesRequest(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const settings = BackendCacheService.getServerSettings();
    const url = URLExt.join(settings.baseUrl, 'signalpilot-ai', endpoint);

    const requestInit: RequestInit = {
      method,
      headers: { 'Content-Type': 'application/json' }
    };

    if (body !== undefined) {
      requestInit.body = JSON.stringify(body);
    }

    const response = await ServerConnection.makeRequest(
      url,
      requestInit,
      settings
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Rules request failed: ${response.status} ${errorText}`);
    }

    return response.json();
  }

  /**
   * Get all user rules (snippets stored as markdown files)
   */
  public static async getRules(): Promise<any[]> {
    try {
      const response = await BackendCacheService.makeRulesRequest('rules');
      return response.rules || [];
    } catch (error) {
      console.error('[BackendCacheService] Failed to get rules:', error);
      return [];
    }
  }

  /**
   * Get a specific rule by ID
   */
  public static async getRule(ruleId: string): Promise<any | null> {
    try {
      const response = await BackendCacheService.makeRulesRequest(
        `rules/${encodeURIComponent(ruleId)}`
      );
      return response;
    } catch (error) {
      console.error('[BackendCacheService] Failed to get rule:', error);
      return null;
    }
  }

  /**
   * Create a new rule
   */
  public static async createRule(rule: {
    title: string;
    content: string;
    description?: string;
    id?: string;
  }): Promise<any | null> {
    try {
      const response = await BackendCacheService.makeRulesRequest(
        'rules',
        'POST',
        rule
      );
      return response.rule || null;
    } catch (error) {
      console.error('[BackendCacheService] Failed to create rule:', error);
      return null;
    }
  }

  /**
   * Update an existing rule
   */
  public static async updateRule(
    ruleId: string,
    updates: {
      title?: string;
      content?: string;
      description?: string;
    }
  ): Promise<any | null> {
    try {
      const response = await BackendCacheService.makeRulesRequest(
        `rules/${encodeURIComponent(ruleId)}`,
        'POST',
        updates
      );
      return response.rule || null;
    } catch (error) {
      console.error('[BackendCacheService] Failed to update rule:', error);
      return null;
    }
  }

  /**
   * Delete a rule
   */
  public static async deleteRule(ruleId: string): Promise<boolean> {
    try {
      await BackendCacheService.makeRulesRequest(
        `rules/${encodeURIComponent(ruleId)}`,
        'DELETE'
      );
      return true;
    } catch (error) {
      console.error('[BackendCacheService] Failed to delete rule:', error);
      return false;
    }
  }

  /**
   * Get user rules service info
   */
  public static async getRulesInfo(): Promise<any> {
    try {
      return await BackendCacheService.makeRulesRequest('rules-info');
    } catch (error) {
      console.error('[BackendCacheService] Failed to get rules info:', error);
      return { available: false };
    }
  }

  // ==================== Checkpoint API (file-per-checkpoint storage) ====================

  /**
   * Get a single checkpoint
   */
  public static async getCheckpoint(
    notebookId: string,
    checkpointId: string
  ): Promise<any | null> {
    try {
      const response = await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}/${encodeURIComponent(checkpointId)}`
      );
      return response.checkpoint || null;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to get checkpoint ${checkpointId}:`,
        error
      );
      return null;
    }
  }

  /**
   * Save a single checkpoint
   */
  public static async setCheckpoint(
    notebookId: string,
    checkpointId: string,
    checkpointData: any
  ): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}/${encodeURIComponent(checkpointId)}`,
        'POST',
        { checkpoint: checkpointData }
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to save checkpoint ${checkpointId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Delete a single checkpoint
   */
  public static async deleteCheckpoint(
    notebookId: string,
    checkpointId: string
  ): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}/${encodeURIComponent(checkpointId)}`,
        'DELETE'
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to delete checkpoint ${checkpointId}:`,
        error
      );
      return false;
    }
  }

  /**
   * List all checkpoints for a notebook
   */
  public static async listCheckpoints(notebookId: string): Promise<any[]> {
    try {
      const response = await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}`
      );
      return response.checkpoints || [];
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to list checkpoints for ${notebookId}:`,
        error
      );
      return [];
    }
  }

  /**
   * Clear all checkpoints for a notebook
   */
  public static async clearCheckpointsForNotebook(
    notebookId: string
  ): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}`,
        'DELETE'
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to clear checkpoints for ${notebookId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Clear all checkpoints after a specific checkpoint
   */
  public static async clearCheckpointsAfter(
    notebookId: string,
    checkpointId: string
  ): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `checkpoints/${encodeURIComponent(notebookId)}/clear-after`,
        'POST',
        { checkpoint_id: checkpointId }
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to clear checkpoints after ${checkpointId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Migrate checkpoints from old format to new file-based format
   */
  public static async migrateCheckpoints(): Promise<{
    success: boolean;
    migratedNotebooks?: number;
    migratedCheckpoints?: number;
    message?: string;
  }> {
    try {
      const response = await BackendCacheService.makeRequest(
        'checkpoints/migrate',
        'POST'
      );
      return {
        success: response.success || false,
        migratedNotebooks: response.migrated_notebooks || 0,
        migratedCheckpoints: response.migrated_checkpoints || 0,
        message: response.message
      };
    } catch (error) {
      console.error('[BackendCacheService] Failed to migrate checkpoints:', error);
      return { success: false, message: String(error) };
    }
  }

  /**
   * Get checkpoint cache statistics
   */
  public static async getCheckpointStats(): Promise<any> {
    try {
      return await BackendCacheService.makeRequest('checkpoints/stats');
    } catch (error) {
      console.error('[BackendCacheService] Failed to get checkpoint stats:', error);
      return { available: false, error: String(error) };
    }
  }

  // ==================== Cell State API (file-per-notebook storage) ====================

  /**
   * Get cell state for a notebook
   */
  public static async getCellState(notebookId: string): Promise<any | null> {
    try {
      const response = await BackendCacheService.makeRequest(
        `cell-states/${encodeURIComponent(notebookId)}`
      );
      return response.cell_state || null;
    } catch (error) {
      // 404 is expected when no cell state exists yet
      if (String(error).includes('404')) {
        return null;
      }
      console.error(
        `[BackendCacheService] Failed to get cell state for ${notebookId}:`,
        error
      );
      return null;
    }
  }

  /**
   * Save cell state for a notebook
   */
  public static async setCellState(
    notebookId: string,
    cellStateData: any
  ): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `cell-states/${encodeURIComponent(notebookId)}`,
        'POST',
        { cell_state: cellStateData }
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to save cell state for ${notebookId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Delete cell state for a notebook
   */
  public static async deleteCellState(notebookId: string): Promise<boolean> {
    try {
      await BackendCacheService.makeRequest(
        `cell-states/${encodeURIComponent(notebookId)}`,
        'DELETE'
      );
      return true;
    } catch (error) {
      console.error(
        `[BackendCacheService] Failed to delete cell state for ${notebookId}:`,
        error
      );
      return false;
    }
  }

  /**
   * Migrate cell states from old format to new file-based format
   */
  public static async migrateCellStates(): Promise<{
    success: boolean;
    migrated?: number;
    errors?: number;
    message?: string;
  }> {
    try {
      const response = await BackendCacheService.makeRequest(
        'cell-states/migrate',
        'POST'
      );
      return {
        success: response.success || false,
        migrated: response.migrated || 0,
        errors: response.errors || 0,
        message: response.message
      };
    } catch (error) {
      console.error('[BackendCacheService] Failed to migrate cell states:', error);
      return { success: false, message: String(error) };
    }
  }

  /**
   * Get cell state cache statistics
   */
  public static async getCellStateStats(): Promise<any> {
    try {
      return await BackendCacheService.makeRequest('cell-states/stats');
    } catch (error) {
      console.error('[BackendCacheService] Failed to get cell state stats:', error);
      return { available: false, error: String(error) };
    }
  }
}

// State DB key constants for chat-related data (kept for compatibility)
export const STATE_DB_KEYS = {
  // Chat settings
  CHAT_HISTORIES: 'chatHistories',
  // Checkpoint data
  NOTEBOOK_CHECKPOINTS: 'notebookCheckpoints',
  // Error logging
  ERROR_LOGS: 'errorLogs',
  // Snippets
  SNIPPETS: 'snippets',
  // Inserted snippets
  INSERTED_SNIPPETS: 'insertedSnippets',
  // Authentication
  JWT_TOKEN: 'jupyter_auth_jwt',
  // Welcome tour
  WELCOME_TOUR_COMPLETED: 'welcomeTourCompleted',
  // Demo mode
  IS_DEMO_MODE: 'isDemoMode'
} as const;

// Alias for backward compatibility
export const StateDBCachingService = BackendCacheService;
