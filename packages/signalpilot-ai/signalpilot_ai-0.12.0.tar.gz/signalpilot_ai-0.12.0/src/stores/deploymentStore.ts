// src/stores/deploymentStore.ts
// PURPOSE: Manage deployment state for notebooks
// Replaces DeploymentStateService.ts RxJS implementation

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Track update count for debugging
let deploymentUpdateCount = 0;

// Custom serializer for devtools to handle Maps
const devtoolsSerialize = {
  replacer: (_key: string, value: any) => {
    if (value instanceof Map) {
      return `[Map: ${value.size} entries]`;
    }
    return value;
  }
};

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface IDeploymentData {
  slug: string;
  deployedUrl: string;
  filename: string;
  deployedAt: string;
  s3_key: string;
  fileSize: number;
}

export interface IBackendFileData {
  id: string;
  slug: string;
  filename: string;
  file_size: number | null;
  workspace_notebook_path: string | null;
  is_active: boolean;
  user_email: string;
  created_at: string;
}

export interface IDeploymentChange {
  type: 'added' | 'removed' | 'updated' | 'cleared';
  notebookPath: string | null;
  deployment: IDeploymentData | null;
}

interface IDeploymentState {
  deployments: Map<string, IDeploymentData>;
  lastChange: IDeploymentChange | null;
}

interface IDeploymentActions {
  // Deployment management
  saveDeployment: (
    notebookPath: string,
    deploymentData: IDeploymentData
  ) => void;
  removeDeployment: (notebookPath: string) => void;
  clearAllDeployments: () => void;
  loadDeploymentFromBackend: (
    workspaceNotebookPath: string,
    backendFiles: IBackendFileData[],
    appUrl: string
  ) => IDeploymentData | null;
  syncWithBackend: (backendFiles: IBackendFileData[]) => void;

  // Getters
  getDeployment: (notebookPath: string) => IDeploymentData | undefined;
  getAllDeployments: () => Map<string, IDeploymentData>;
  isDeployed: (notebookPath: string) => boolean;
  getDeploymentCount: () => number;
}

type IDeploymentStore = IDeploymentState & IDeploymentActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDeploymentStore = create<IDeploymentStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      deployments: new Map(),
      lastChange: null,

      // ─────────────────────────────────────────────────────────────
      // Actions
      // ─────────────────────────────────────────────────────────────
      saveDeployment: (notebookPath, deploymentData) => {
        set(state => {
          const isUpdate = state.deployments.has(notebookPath);
          const newDeployments = new Map(state.deployments);
          newDeployments.set(notebookPath, deploymentData);
          console.log(
            `[DeploymentStore] Saved deployment for: ${notebookPath}`
          );
          return {
            deployments: newDeployments,
            lastChange: {
              type: isUpdate ? 'updated' : 'added',
              notebookPath,
              deployment: deploymentData
            }
          };
        });
      },

      removeDeployment: notebookPath => {
        set(state => {
          const newDeployments = new Map(state.deployments);
          newDeployments.delete(notebookPath);
          console.log(
            `[DeploymentStore] Removed deployment for: ${notebookPath}`
          );
          return {
            deployments: newDeployments,
            lastChange: {
              type: 'removed',
              notebookPath,
              deployment: null
            }
          };
        });
      },

      clearAllDeployments: () => {
        set(() => {
          console.log('[DeploymentStore] Cleared all deployments');
          return {
            deployments: new Map(),
            lastChange: {
              type: 'cleared',
              notebookPath: null,
              deployment: null
            }
          };
        });
      },

      loadDeploymentFromBackend: (
        workspaceNotebookPath,
        backendFiles,
        appUrl
      ) => {
        // Filter active files matching the workspace_notebook_path
        const matchingFiles = backendFiles.filter(
          file =>
            file.is_active &&
            file.workspace_notebook_path === workspaceNotebookPath
        );

        if (matchingFiles.length === 0) {
          return null;
        }

        // Get most recent if multiple
        const mostRecent = matchingFiles.sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )[0];

        const deploymentData: IDeploymentData = {
          slug: mostRecent.slug,
          deployedUrl: `${appUrl}/notebooks/${mostRecent.slug}`,
          filename: mostRecent.filename,
          deployedAt: mostRecent.created_at,
          s3_key: mostRecent.slug,
          fileSize: mostRecent.file_size || 0
        };

        // Save to store
        get().saveDeployment(workspaceNotebookPath, deploymentData);
        console.log(
          `[DeploymentStore] Loaded deployment from backend for: ${workspaceNotebookPath}`
        );

        return deploymentData;
      },

      syncWithBackend: backendFiles => {
        const state = get();
        const backendFileMap = new Map<string, IBackendFileData>();
        backendFiles.forEach(file => {
          if (file.slug) {
            backendFileMap.set(file.slug, file);
          }
        });

        // Check if any local deployments are no longer active on backend
        const deploymentsToRemove: string[] = [];
        for (const [notebookPath, deployment] of state.deployments) {
          const backendFile = backendFileMap.get(deployment.slug);
          if (!backendFile || !backendFile.is_active) {
            deploymentsToRemove.push(notebookPath);
          }
        }

        // Remove inactive deployments
        deploymentsToRemove.forEach(notebookPath => {
          get().removeDeployment(notebookPath);
        });

        console.log(
          `[DeploymentStore] Synced with backend, removed ${deploymentsToRemove.length} inactive deployments`
        );
      },

      // ─────────────────────────────────────────────────────────────
      // Getters
      // ─────────────────────────────────────────────────────────────
      getDeployment: notebookPath => get().deployments.get(notebookPath),

      getAllDeployments: () => new Map(get().deployments),

      isDeployed: notebookPath => get().deployments.has(notebookPath),

      getDeploymentCount: () => get().deployments.size
    })),
    { name: 'DeploymentStore', serialize: devtoolsSerialize }
  )
);

// Debug utility
(window as any).getDeploymentStoreUpdateCount = () => deploymentUpdateCount;

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectDeployments = (state: IDeploymentStore) => state.deployments;
export const selectDeploymentCount = (state: IDeploymentStore) =>
  state.deployments.size;
export const selectLastChange = (state: IDeploymentStore) => state.lastChange;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to deployment changes from non-React code.
 * Returns an unsubscribe function.
 */
export function subscribeToDeploymentChanges(
  callback: (change: IDeploymentChange | null) => void
): () => void {
  return useDeploymentStore.subscribe(state => state.lastChange, callback);
}

/**
 * Subscribe to a specific notebook's deployment status.
 * Returns an unsubscribe function.
 */
export function subscribeToNotebookDeployment(
  notebookPath: string,
  callback: (deployment: IDeploymentData | undefined) => void
): () => void {
  return useDeploymentStore.subscribe(
    state => state.deployments.get(notebookPath),
    callback
  );
}

// ═══════════════════════════════════════════════════════════════
// CONVENIENCE ACCESSORS (for non-React code)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the current deployment state directly (for non-React code).
 */
export function getDeploymentState() {
  return useDeploymentStore.getState();
}

/**
 * Get debug information about deployments.
 */
export function getDeploymentDebugInfo(): {
  deploymentCount: number;
  deployments: Array<{
    notebookPath: string;
    slug: string;
    filename: string;
    deployedAt: string;
    deployedUrl: string;
  }>;
} {
  const state = useDeploymentStore.getState();
  return {
    deploymentCount: state.deployments.size,
    deployments: Array.from(state.deployments.entries()).map(
      ([path, data]) => ({
        notebookPath: path,
        slug: data.slug,
        filename: data.filename,
        deployedAt: data.deployedAt,
        deployedUrl: data.deployedUrl
      })
    )
  };
}
