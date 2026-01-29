import { getToolService } from '../stores/servicesStore';
import { getDatabaseUrl, getClaudeSettings } from '../stores/settingsStore';
import { KernelPreviewUtils } from './kernelPreview';
import { DatabaseStateService, IDatabaseConfig } from '../stores/databaseStore';

/**
 * Utility functions for kernel operations
 *
 * Database environment variable injection uses a two-tier approach:
 *
 * 1. PRIMARY: SignalPilotProvisioner (server-side)
 *    - Injects env vars at kernel launch time, before any code runs
 *    - Reads from db.toml configuration
 *    - See: signalpilot_ai/kernel_provisioner.py
 *
 * 2. FALLBACK: Runtime injection (this file)
 *    - Updates running kernels when database configs change
 *    - Used when user adds/modifies databases while kernel is running
 *    - Requires code execution in kernel
 */
export class KernelUtils {
  // Guard to prevent multiple simultaneous retry attempts
  private static isRetrying = false;

  /**
   * Update database environment variables in a running kernel.
   *
   * NOTE: For new kernels, environment variables are set by SignalPilotProvisioner
   * at launch time. This method is only needed to update RUNNING kernels when
   * database configurations change (e.g., user adds a new database).
   */
  static setDatabaseEnvironmentsInKernel(): void {
    try {
      const toolService = getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.log(
          '[KernelUtils] No running kernel to update. New kernels will get env vars from provisioner.'
        );
        return;
      }

      // Get all database configurations from DatabaseStateService
      const databaseConfigs = DatabaseStateService.getConfigurations();

      console.log(
        `[KernelUtils] Updating running kernel with ${databaseConfigs.length} database configurations`
      );

      if (databaseConfigs.length === 0) {
        console.log('[KernelUtils] No database configurations to set');
        return;
      }

      // Build environment variables update code
      const envVarsCode = this.buildEnvVarsCode(databaseConfigs);

      kernel.requestExecute({ code: envVarsCode, silent: true });
      console.log(
        '[KernelUtils] Sent database environment update to running kernel'
      );
    } catch (error) {
      console.error(
        '[KernelUtils] Error updating database environments in kernel:',
        error
      );
    }
  }

  /**
   * Build Python code to set environment variables for all database configurations.
   */
  private static buildEnvVarsCode(databaseConfigs: IDatabaseConfig[]): string {
    let code = `
import os
import json

# Update database environment variables (runtime update)
`;

    databaseConfigs.forEach((config: IDatabaseConfig) => {
      const dbName = config.name.toUpperCase().replace(/[^A-Z0-9]/g, '_');

      if (config.connectionType === 'credentials' && config.credentials) {
        const creds = config.credentials;

        code += `
# Database: ${config.name} (${config.type})
os.environ['${dbName}_HOST'] = '${this.escapeString(creds.host)}'
os.environ['${dbName}_PORT'] = '${creds.port}'
os.environ['${dbName}_DATABASE'] = '${this.escapeString(creds.database)}'
os.environ['${dbName}_USERNAME'] = '${this.escapeString(creds.username)}'
os.environ['${dbName}_PASSWORD'] = '${this.escapeString(creds.password)}'
os.environ['${dbName}_TYPE'] = '${creds.type}'
`;

        // Add Snowflake-specific variables
        if (config.type === 'snowflake' && 'connectionUrl' in creds) {
          const connectionUrl = (creds as any).connectionUrl;
          code += `os.environ['${dbName}_CONNECTION_URL'] = '${this.escapeString(connectionUrl)}'\n`;

          const accountMatch = connectionUrl.match(/https?:\/\/([^./]+)/);
          if (accountMatch && accountMatch[1]) {
            code += `os.environ['${dbName}_ACCOUNT'] = '${this.escapeString(accountMatch[1])}'\n`;
          }

          if ((creds as any).warehouse) {
            code += `os.environ['${dbName}_WAREHOUSE'] = '${this.escapeString((creds as any).warehouse)}'\n`;
          }
          if ((creds as any).role) {
            code += `os.environ['${dbName}_ROLE'] = '${this.escapeString((creds as any).role)}'\n`;
          }
        }

        // Add Databricks-specific variables
        if (config.type === 'databricks') {
          // Use whichever value is available: connectionUrl or host
          const databricksHost = (creds as any).connectionUrl || creds.host || '';
          // Set both HOST and CONNECTION_URL to the same value for Databricks
          if (databricksHost) {
            code += `os.environ['${dbName}_HOST'] = '${this.escapeString(databricksHost)}'\n`;
            code += `os.environ['${dbName}_CONNECTION_URL'] = '${this.escapeString(databricksHost)}'\n`;
          }

          const databricksFields = [
            'authType',
            'accessToken',
            'clientId',
            'clientSecret',
            'oauthTokenUrl',
            'warehouseId',
            'warehouseHttpPath',
            'catalog',
            'schema'
          ];

          databricksFields.forEach(field => {
            if ((creds as any)[field]) {
              const envName = field
                .replace(/([A-Z])/g, '_$1')
                .toUpperCase()
                .replace(/^_/, '');
              code += `os.environ['${dbName}_${envName}'] = '${this.escapeString((creds as any)[field])}'\n`;
            }
          });
        }

        // Set JSON connection details
        const connectionJson = this.buildConnectionJson(config, creds);
        code += `os.environ['${dbName}_CONNECTION_JSON'] = '''${JSON.stringify(connectionJson).replace(/'/g, "\\'")}'''\n`;
      } else if (config.connectionType === 'url' && config.urlConnection) {
        const urlConn = config.urlConnection;
        code += `
# Database: ${config.name} (${config.type} - URL)
os.environ['${dbName}_CONNECTION_URL'] = '${this.escapeString(urlConn.connectionUrl)}'
os.environ['${dbName}_TYPE'] = '${urlConn.type}'
os.environ['${dbName}_CONNECTION_JSON'] = '''${JSON.stringify({ id: config.id, name: config.name, type: config.type, connectionUrl: urlConn.connectionUrl }).replace(/'/g, "\\'")}'''
`;
      }
    });

    return code;
  }

  /**
   * Escape a string for use in Python code.
   */
  private static escapeString(str: string): string {
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }

  /**
   * Build connection JSON object for a database config.
   */
  private static buildConnectionJson(
    config: IDatabaseConfig,
    creds: any
  ): Record<string, any> {
    const json: Record<string, any> = {
      id: config.id,
      name: config.name,
      type: config.type,
      host: creds.host,
      port: creds.port,
      database: creds.database,
      username: creds.username,
      password: creds.password
    };

    // Add optional fields if present
    const optionalFields = [
      'connectionUrl',
      'warehouse',
      'role',
      'authType',
      'accessToken',
      'clientId',
      'clientSecret',
      'oauthTokenUrl',
      'warehouseId',
      'warehouseHttpPath',
      'catalog',
      'schema'
    ];

    optionalFields.forEach(field => {
      if (creds[field]) {
        json[field] = creds[field];
      }
    });

    return json;
  }

  /**
   * Update database environments with retry mechanism for running kernels.
   *
   * NOTE: For new kernels, environment variables are set by SignalPilotProvisioner
   * at launch time. This method is for updating RUNNING kernels when database
   * configurations change.
   *
   * @param maxRetries Maximum number of retry attempts
   * @param delay Delay between retries in ms
   */
  static async setDatabaseEnvironmentsInKernelWithRetry(
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<void> {
    if (this.isRetrying) {
      console.log(
        '[KernelUtils] Already updating database environments, skipping duplicate attempt'
      );
      return;
    }

    this.isRetrying = true;

    try {
      for (let i = 0; i < maxRetries; i++) {
        try {
          const toolService = getToolService();
          const kernel = toolService?.getCurrentNotebook()?.kernel;

          if (kernel) {
            console.log(
              `[KernelUtils] Kernel available, updating database environments`
            );
            this.setDatabaseEnvironmentsInKernel();
            return;
          } else {
            console.log(
              `[KernelUtils] No kernel yet, attempt ${i + 1}/${maxRetries}. New kernels will get env vars from provisioner.`
            );
            if (i < maxRetries - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }
          }
        } catch (error) {
          console.error(`[KernelUtils] Error on attempt ${i + 1}:`, error);
          if (i < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }

      console.log(
        '[KernelUtils] No running kernel to update. New kernels will get env vars from provisioner at launch.'
      );
    } finally {
      this.isRetrying = false;
    }
  }

  /**
   * @deprecated Use setDatabaseEnvironmentsInKernel() instead
   * Set DB_URL environment variable in the current kernel
   * @param databaseUrl The database URL to set, or null to use from AppState
   */
  static setDbUrlInKernel(databaseUrl?: string | null): void {
    try {
      // Get database URL from parameter or settings store
      const dbUrl = databaseUrl ?? getDatabaseUrl();

      console.log(
        '[KernelUtils] Attempting to set DB_URL in kernel:',
        dbUrl ? 'configured' : 'not configured'
      );
      console.log('[KernelUtils] Database URL value:', dbUrl);

      const toolService = getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.warn('[KernelUtils] No kernel available to set DB_URL');
        return;
      }

      if (dbUrl && dbUrl.trim() !== '') {
        const code = `
import os
os.environ['DB_URL'] = '${dbUrl.replace(/'/g, "\\'")}'
print(f"[KernelUtils] DB_URL environment variable set: {os.environ.get('DB_URL', 'Not set')}")
        `;

        console.log(
          '[KernelUtils] Setting DB_URL environment variable in kernel. URL:',
          dbUrl.length > 50 ? dbUrl.substring(0, 50) + '...' : dbUrl
        );
        kernel.requestExecute({ code, silent: true });
      } else {
        // Remove DB_URL if empty
        const code = `
import os
if 'DB_URL' in os.environ:
    del os.environ['DB_URL']
    print("[KernelUtils] DB_URL environment variable removed")
else:
    print("[KernelUtils] DB_URL environment variable was not set")
        `;

        console.log(
          '[KernelUtils] Removing DB_URL environment variable from kernel'
        );
        kernel.requestExecute({ code, silent: true });
      }
    } catch (error) {
      console.error('[KernelUtils] Error setting DB_URL in kernel:', error);
    }
  }

  /**
   * Check current DB_URL in kernel
   */
  static checkDbUrlInKernel(): void {
    try {
      const toolService = getToolService();
      const kernel = toolService?.getCurrentNotebook()?.kernel;

      if (!kernel) {
        console.warn('[KernelUtils] No kernel available to check DB_URL');
        return;
      }

      const code = `
import os
db_url = os.environ.get('DB_URL')
print(f"[KernelUtils Check] Current DB_URL: {db_url}")
if db_url:
    print(f"[KernelUtils Check] DB_URL length: {len(db_url)}")
    print(f"[KernelUtils Check] DB_URL starts with: {db_url[:50]}...")
else:
    print("[KernelUtils Check] DB_URL is not set")
      `;

      console.log('[KernelUtils] Checking current DB_URL in kernel');
      kernel.requestExecute({ code, silent: true });
    } catch (error) {
      console.error('[KernelUtils] Error checking DB_URL in kernel:', error);
    }
  }

  /**
   * Debug settings store database URL
   */
  static debugAppStateDatabaseUrl(): void {
    try {
      const settings = getClaudeSettings();
      console.log('[KernelUtils] Settings:', settings);
      console.log(
        '[KernelUtils] Database URL from settings:',
        settings.databaseUrl
      );
      console.log(
        '[KernelUtils] Database URL type:',
        typeof settings.databaseUrl
      );
      console.log(
        '[KernelUtils] Database URL length:',
        settings.databaseUrl?.length
      );
    } catch (error) {
      console.error('[KernelUtils] Error debugging settings:', error);
    }
  }

  /**
   * @deprecated Use setDatabaseEnvironmentsInKernelWithRetry() instead
   * Set DB_URL with retry mechanism for when kernel is not ready
   * @param databaseUrl The database URL to set
   * @param maxRetries Maximum number of retry attempts
   * @param delay Delay between retries in ms
   */
  static async setDbUrlInKernelWithRetry(
    databaseUrl?: string | null,
    maxRetries: number = 3,
    delay: number = 1000
  ): Promise<void> {
    if (this.isRetrying) {
      console.log(
        '[KernelUtils] Already retrying DB_URL setup, skipping duplicate attempt'
      );
      return;
    }

    this.isRetrying = true;
    console.log('[KernelUtils] Starting DB_URL retry process...');
    this.debugAppStateDatabaseUrl();

    try {
      for (let i = 0; i < maxRetries; i++) {
        try {
          const toolService = getToolService();
          const kernel = toolService?.getCurrentNotebook()?.kernel;

          if (kernel) {
            console.log(
              `[KernelUtils] Kernel available on attempt ${i + 1}, setting DB_URL`
            );
            this.setDbUrlInKernel(databaseUrl);
            console.log(
              '[KernelUtils] DB_URL retry process completed successfully'
            );
            return;
          } else {
            console.log(
              `[KernelUtils] Kernel not ready, attempt ${i + 1}/${maxRetries}, waiting ${delay}ms...`
            );
            if (i < maxRetries - 1) {
              await new Promise(resolve => setTimeout(resolve, delay));
            }
          }
        } catch (error) {
          console.error(`[KernelUtils] Error on attempt ${i + 1}:`, error);
          if (i < maxRetries - 1) {
            await new Promise(resolve => setTimeout(resolve, delay));
          }
        }
      }

      console.warn(
        '[KernelUtils] Failed to set DB_URL after all retry attempts'
      );
    } finally {
      this.isRetrying = false;
    }
  }

  /**
   * Gets a preview of all variables, dicts, and objects in the current kernel
   */
  static async getKernelPreview(): Promise<string | null> {
    return KernelPreviewUtils.getKernelPreview();
  }
}
