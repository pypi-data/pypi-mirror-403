/**
 * Centralized file cache service that manages scanned files data
 * Used by both FileExplorerWidget and DataLoaderService to ensure consistency
 */
import { ISignal, Signal } from '@lumino/signaling';
import { IFileEntry } from '@/ChatBox/Context/DataLoaderService';
import { IScannedDirectory } from '../utils/handler';
import { useContextCacheStore } from '../stores/contextCacheStore';

export interface ICacheState {
  files: IFileEntry[];
  scannedDirectories: IScannedDirectory[];
  workDir: string | null;
  totalFileCount: number;
  lastUpdated: Date | null;
  isLoading: boolean;
}

/**
 * Centralized file cache service
 */
export class FileCacheService {
  private static _instance: FileCacheService | null = null;
  private _cacheState: ICacheState;

  private constructor() {
    this._cacheState = {
      files: [],
      scannedDirectories: [],
      workDir: null,
      totalFileCount: 0,
      lastUpdated: null,
      isLoading: true
    };
  }

  private _cacheUpdated = new Signal<this, ICacheState>(this);

  /**
   * Get the signal that fires when cache is updated
   */
  public get cacheUpdated(): ISignal<this, ICacheState> {
    return this._cacheUpdated;
  }

  /**
   * Get the singleton instance
   */
  public static getInstance(): FileCacheService {
    if (!FileCacheService._instance) {
      FileCacheService._instance = new FileCacheService();
    }
    return FileCacheService._instance;
  }

  /**
   * Get the current cache state
   */
  public getCacheState(): ICacheState {
    return { ...this._cacheState };
  }

  /**
   * Get cached files
   */
  public getFiles(): IFileEntry[] {
    return [...this._cacheState.files];
  }

  /**
   * Get cached scanned directories
   */
  public getScannedDirectories(): IScannedDirectory[] {
    return [...this._cacheState.scannedDirectories];
  }

  /**
   * Get cached work directory
   */
  public getWorkDir(): string | null {
    return this._cacheState.workDir;
  }

  /**
   * Get total file count
   */
  public getTotalFileCount(): number {
    return this._cacheState.totalFileCount;
  }

  /**
   * Check if cache has been initialized
   */
  public isInitialized(): boolean {
    return this._cacheState.lastUpdated !== null;
  }

  /**
   * Check if cache is currently loading
   */
  public isLoading(): boolean {
    return this._cacheState.isLoading;
  }

  /**
   * Update the cache with new file scan data
   * Called by FileExplorerWidget during polling
   */
  public updateCache(data: {
    files: IFileEntry[];
    scannedDirectories: IScannedDirectory[];
    totalFileCount: number;
    workDir?: string | null;
  }): void {
    const oldState = { ...this._cacheState };

    // Build new state without updating lastUpdated yet
    const newState: ICacheState = {
      files: [...data.files],
      scannedDirectories: [...data.scannedDirectories],
      workDir:
        data.workDir !== undefined ? data.workDir : this._cacheState.workDir,
      totalFileCount: data.totalFileCount,
      lastUpdated: this._cacheState.lastUpdated, // Keep old timestamp initially
      isLoading: false
    };

    // Only update lastUpdated and emit signal if there are actual changes
    if (this.hasStateChanged(oldState, newState)) {
      newState.lastUpdated = new Date(); // Update timestamp only on real changes
      this._cacheState = newState;
      this._cacheUpdated.emit(this._cacheState);

      // Invalidate the context cache so mention dropdown picks up new files
      useContextCacheStore.getState().invalidateCache();

      console.log(
        '[FileCacheService] Cache updated with',
        data.files.length,
        'files, context cache invalidated'
      );
    } else {
      // Still update state to clear isLoading if needed
      this._cacheState = newState;
    }
  }

  /**
   * Set loading state
   */
  public setLoading(isLoading: boolean): void {
    if (this._cacheState.isLoading !== isLoading) {
      this._cacheState.isLoading = isLoading;
      this._cacheUpdated.emit(this._cacheState);
    }
  }

  /**
   * Update work directory
   */
  public updateWorkDir(workDir: string | null): void {
    if (this._cacheState.workDir !== workDir) {
      this._cacheState.workDir = workDir;
      this._cacheUpdated.emit(this._cacheState);
    }
  }

  /**
   * Clear the cache
   */
  public clearCache(): void {
    this._cacheState = {
      files: [],
      scannedDirectories: [],
      workDir: this._cacheState.workDir, // Keep workDir
      totalFileCount: 0,
      lastUpdated: null,
      isLoading: true
    };
    this._cacheUpdated.emit(this._cacheState);
    console.log('[FileCacheService] Cache cleared');
  }

  /**
   * Check if state has changed (excludes lastUpdated since it changes every call)
   */
  private hasStateChanged(
    oldState: ICacheState,
    newState: ICacheState
  ): boolean {
    // Check basic structural changes
    if (
      oldState.files.length !== newState.files.length ||
      oldState.scannedDirectories.length !==
        newState.scannedDirectories.length ||
      oldState.totalFileCount !== newState.totalFileCount ||
      oldState.workDir !== newState.workDir ||
      oldState.isLoading !== newState.isLoading
    ) {
      return true;
    }

    // Check if any file's schema loading state changed
    const oldLoadingSet = new Set(
      oldState.files
        .filter(f => f.schema?.loading === true)
        .map(f => f.absolute_path)
    );
    const newLoadingSet = new Set(
      newState.files
        .filter(f => f.schema?.loading === true)
        .map(f => f.absolute_path)
    );

    // If loading sets differ, state has changed
    if (oldLoadingSet.size !== newLoadingSet.size) {
      console.log(
        '[FileCacheService] Schema loading count changed:',
        oldLoadingSet.size,
        '->',
        newLoadingSet.size
      );
      return true;
    }
    for (const path of oldLoadingSet) {
      if (!newLoadingSet.has(path)) {
        console.log(
          '[FileCacheService] Schema completed for:',
          path
        );
        return true;
      }
    }

    return false;
  }
}
