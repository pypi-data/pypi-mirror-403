import { IChatMessage, ICheckpoint } from '../types';
import { IMentionContext } from '@/ChatBox/Context/ChatContextLoaders';
import {
  ICachedCellState,
  NotebookCellStateService
} from './NotebookCellStateService';
import { IActionHistoryEntry } from '@/ChatBox/services/ActionHistory';
import { StateDBCachingService } from '../utils/backendCaching';
import { renderContextTagsAsPlainText } from '../utils/contextTagUtils';

/**
 * Serializable version of ICheckpoint for storage
 */
interface ISerializableCheckpoint {
  id: string;
  timestamp: number;
  userMessage: string;
  userMessageId?: string;
  messageHistory: IChatMessage[];
  notebookState: ICachedCellState[];
  contexts: Record<string, any>; // Serialized Map
  notebookId: string;
  actionHistory: any[];
  nextCheckpointId?: string;
}

/**
 * Service for managing checkpoints in the chat conversation
 * Checkpoints capture the state at user message points for potential restoration
 */
export class CheckpointManager {
  private static instance: CheckpointManager;
  private checkpoints: Map<string, ICheckpoint[]> = new Map(); // notebookId -> checkpoints
  private currentNotebookId: string | null = null;
  private currentCheckpoint: ICheckpoint | null = null;

  private constructor() {
    console.log('[CheckpointManager] Initialized with cached data');
    void this.initialize();
  }

  public static getInstance(): CheckpointManager {
    if (!CheckpointManager.instance) {
      CheckpointManager.instance = new CheckpointManager();
    }
    return CheckpointManager.instance;
  }

  /**
   * Set the current notebook ID and load its checkpoints
   */
  public setCurrentNotebookId(notebookId: string): void {
    this.currentNotebookId = notebookId;
    console.log('[CheckpointManager] Set current notebook ID:', notebookId);

    // Load checkpoints for this notebook if not already loaded
    if (!this.checkpoints.has(notebookId)) {
      void this.loadCheckpointsForNotebook(notebookId);
    }
  }

  /**
   * Create a checkpoint at the current user message
   */
  public createCheckpoint(
    userMessage: string,
    messageHistory: IChatMessage[],
    contexts: Map<string, IMentionContext>,
    threadId: string,
    userMessageId?: string
  ): ICheckpoint {
    if (!this.currentNotebookId) {
      throw new Error('No current notebook ID set');
    }

    const checkpoint: ICheckpoint = {
      id: `checkpoint_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      userMessage: renderContextTagsAsPlainText(userMessage),
      userMessageId,
      messageHistory: [...messageHistory], // Deep copy
      notebookState: this.captureNotebookState(),
      contexts: new Map(contexts), // Deep copy
      notebookId: this.currentNotebookId,
      actionHistory: []
    };

    this.currentCheckpoint = checkpoint;

    // Store checkpoint for this notebook
    if (!this.checkpoints.has(this.currentNotebookId)) {
      this.checkpoints.set(this.currentNotebookId, []);
    }

    const notebookCheckpoints = this.checkpoints.get(this.currentNotebookId)!;
    notebookCheckpoints.push(checkpoint);

    let lastMsgCheckpoint: IChatMessage | null = null;
    for (let i = messageHistory.length - 1; i >= 0; i--) {
      const msg = messageHistory[i];
      if (msg.role === 'user' && msg.id && msg.id !== userMessageId) {
        lastMsgCheckpoint = msg;
        break;
      }
    }

    if (lastMsgCheckpoint) {
      const lastCheckpoint = notebookCheckpoints.find(
        cp => cp.userMessageId === lastMsgCheckpoint?.id
      );

      if (lastCheckpoint) {
        lastCheckpoint.nextCheckpointId = checkpoint.id;
      }
    }

    console.log('[CheckpointManager] Created checkpoint:', checkpoint.id);
    console.log(
      '[CheckpointManager] Total checkpoints for notebook:',
      notebookCheckpoints.length
    );
    console.log(
      '[CheckpointManager] Captured',
      checkpoint.actionHistory.length,
      'actions'
    );

    // Auto-save the new checkpoint individually (file-per-checkpoint)
    void this.saveCheckpoint(checkpoint);

    // If there was a previous checkpoint that we linked to, save it too (for nextCheckpointId update)
    if (lastMsgCheckpoint) {
      const lastCheckpoint = notebookCheckpoints.find(
        cp => cp.userMessageId === lastMsgCheckpoint?.id
      );
      if (lastCheckpoint) {
        void this.saveCheckpoint(lastCheckpoint);
      }
    }

    return checkpoint;
  }

  /**
   * Add a single action to the current checkpoint
   */
  public addActionToCurrentCheckpoint(action: IActionHistoryEntry): void {
    if (!this.currentCheckpoint || !this.currentNotebookId) {
      console.warn(
        '[CheckpointManager] No current checkpoint to add action to'
      );
      return;
    }

    const notebookCheckpoints = this.checkpoints.get(this.currentNotebookId);
    if (!notebookCheckpoints) {
      console.warn(
        '[CheckpointManager] No checkpoints found for current notebook'
      );
      return;
    }

    const checkpoint = notebookCheckpoints.find(
      cp => cp.id === this.currentCheckpoint?.id
    );
    if (!checkpoint) {
      console.warn('[CheckpointManager] Current checkpoint not found');
      return;
    }

    // Add the action to the checkpoint's actionHistory
    checkpoint.actionHistory.push(action);

    console.log(
      '[CheckpointManager] Added action to checkpoint:',
      action.description
    );
    console.log(
      '[CheckpointManager] Total actions in checkpoint:',
      checkpoint.actionHistory.length
    );

    // Auto-save the updated checkpoint individually
    void this.saveCheckpoint(checkpoint);
  }

  /**
   * Get all checkpoints for the current notebook
   */
  public getCheckpoints(): ICheckpoint[] {
    if (!this.currentNotebookId) {
      return [];
    }
    return this.checkpoints.get(this.currentNotebookId) || [];
  }

  /**
   * Find a checkpoint by user message content
   */
  public findCheckpointByUserMessage(userMessage: string): ICheckpoint | null {
    if (!this.currentNotebookId) {
      return null;
    }

    const checkpoints = this.checkpoints.get(this.currentNotebookId) || [];
    return (
      checkpoints.find(checkpoint => checkpoint.userMessage === userMessage) ||
      null
    );
  }

  /**
   * Find a checkpoint by user message ID
   */
  public findCheckpointByUserMessageId(
    userMessageId: string
  ): ICheckpoint | null {
    if (!this.currentNotebookId) {
      return null;
    }

    const checkpoints = this.checkpoints.get(this.currentNotebookId) || [];
    return (
      checkpoints.find(
        checkpoint => checkpoint.userMessageId === userMessageId
      ) || null
    );
  }

  /**
   * Clear all checkpoints for the current notebook
   */
  public clearCheckpoints(): void {
    if (this.currentNotebookId) {
      this.checkpoints.delete(this.currentNotebookId);
      console.log(
        '[CheckpointManager] Cleared checkpoints for notebook:',
        this.currentNotebookId
      );

      // Clear from storage using new API
      void StateDBCachingService.clearCheckpointsForNotebook(this.currentNotebookId);
    }
  }

  /**
   * Clear checkpoints after a specific checkpoint (for restoration)
   */
  public clearCheckpointsAfter(checkpointId: string): void {
    if (!this.currentNotebookId) {
      return;
    }

    const notebookCheckpoints =
      this.checkpoints.get(this.currentNotebookId) || [];
    const checkpointIndex = notebookCheckpoints.findIndex(
      cp => cp.id === checkpointId
    );

    if (checkpointIndex !== -1) {
      // Get the checkpoints to be deleted (those after the target)
      const checkpointsToDelete = notebookCheckpoints.slice(checkpointIndex + 1);

      // Keep only checkpoints up to and including the target checkpoint
      const remainingCheckpoints = notebookCheckpoints.slice(
        0,
        checkpointIndex + 1
      );
      this.checkpoints.set(this.currentNotebookId, remainingCheckpoints);

      console.log(
        '[CheckpointManager] Cleared checkpoints after:',
        checkpointId
      );
      console.log(
        '[CheckpointManager] Remaining checkpoints:',
        remainingCheckpoints.length
      );

      // Delete removed checkpoints from storage using new API
      for (const cp of checkpointsToDelete) {
        void this.deleteCheckpointFromStorage(this.currentNotebookId, cp.id);
      }
    }
  }

  /**
   * Initialize CheckpointManager with cached data
   */
  public async initialize(): Promise<void> {
    await this.loadFromStorage();
    console.log('[CheckpointManager] Initialized with cached data');
  }

  /**
   * Capture the current notebook state
   */
  private captureNotebookState(): ICachedCellState[] {
    if (!this.currentNotebookId) {
      return [];
    }

    try {
      const currentState = NotebookCellStateService.getCurrentNotebookState(
        this.currentNotebookId
      );
      return currentState || [];
    } catch (error) {
      console.error(
        '[CheckpointManager] Error capturing notebook state:',
        error
      );
      return [];
    }
  }

  /**
   * Save a single checkpoint to storage (file-per-checkpoint)
   */
  private async saveCheckpoint(checkpoint: ICheckpoint): Promise<void> {
    try {
      // Convert checkpoint to serializable format
      const serializedCheckpoint: ISerializableCheckpoint = {
        ...checkpoint,
        contexts: checkpoint.contexts
          ? Object.fromEntries(checkpoint.contexts)
          : {}
      };

      await StateDBCachingService.setCheckpoint(
        checkpoint.notebookId,
        checkpoint.id,
        serializedCheckpoint
      );

      console.log(
        `[CheckpointManager] Saved checkpoint ${checkpoint.id} for notebook ${checkpoint.notebookId}`
      );
    } catch (error) {
      console.error(
        '[CheckpointManager] Error saving checkpoint:',
        error
      );
    }
  }

  /**
   * Save all checkpoints for current notebook (for bulk operations like clearAfter)
   * @deprecated Use saveCheckpoint for individual saves
   */
  private async saveToStorage(): Promise<void> {
    // With file-per-checkpoint storage, we save individually
    // This method is kept for backward compatibility during transition
    if (!this.currentNotebookId) {
      return;
    }

    const notebookCheckpoints = this.checkpoints.get(this.currentNotebookId);
    if (!notebookCheckpoints) {
      return;
    }

    // Save each checkpoint individually
    for (const checkpoint of notebookCheckpoints) {
      await this.saveCheckpoint(checkpoint);
    }
  }

  /**
   * Load checkpoints for the current notebook from storage
   */
  private async loadFromStorage(): Promise<void> {
    try {
      // First, try to migrate any old checkpoints
      const migrationResult = await StateDBCachingService.migrateCheckpoints();
      if (migrationResult.success && migrationResult.migratedCheckpoints && migrationResult.migratedCheckpoints > 0) {
        console.log(
          `[CheckpointManager] Migrated ${migrationResult.migratedCheckpoints} checkpoints from old format`
        );
      }

      // Initialize empty map - checkpoints will be loaded on demand per notebook
      this.checkpoints = new Map();

      console.log(
        '[CheckpointManager] Initialized with file-per-checkpoint storage'
      );
    } catch (error) {
      console.error(
        '[CheckpointManager] Error initializing checkpoint storage:',
        error
      );
      this.checkpoints = new Map();
    }
  }

  /**
   * Load checkpoints for a specific notebook from storage
   */
  public async loadCheckpointsForNotebook(notebookId: string): Promise<void> {
    try {
      const storedCheckpoints = await StateDBCachingService.listCheckpoints(notebookId);

      if (storedCheckpoints && storedCheckpoints.length > 0) {
        // Convert stored checkpoints to ICheckpoint format with Maps
        const deserializedCheckpoints: ICheckpoint[] = storedCheckpoints.map(
          (checkpoint: ISerializableCheckpoint) => ({
            ...checkpoint,
            contexts: checkpoint.contexts
              ? new Map<string, any>(Object.entries(checkpoint.contexts))
              : new Map<string, any>()
          })
        );

        this.checkpoints.set(notebookId, deserializedCheckpoints);

        console.log(
          `[CheckpointManager] Loaded ${deserializedCheckpoints.length} checkpoints for notebook ${notebookId}`
        );
      } else {
        this.checkpoints.set(notebookId, []);
        console.log(
          `[CheckpointManager] No checkpoints found for notebook ${notebookId}`
        );
      }
    } catch (error) {
      console.error(
        `[CheckpointManager] Error loading checkpoints for notebook ${notebookId}:`,
        error
      );
      this.checkpoints.set(notebookId, []);
    }
  }

  /**
   * Delete a checkpoint from storage
   */
  private async deleteCheckpointFromStorage(
    notebookId: string,
    checkpointId: string
  ): Promise<void> {
    try {
      await StateDBCachingService.deleteCheckpoint(notebookId, checkpointId);
      console.log(
        `[CheckpointManager] Deleted checkpoint ${checkpointId} from storage`
      );
    } catch (error) {
      console.error(
        `[CheckpointManager] Error deleting checkpoint ${checkpointId}:`,
        error
      );
    }
  }
}
