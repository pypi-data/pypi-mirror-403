// src/stores/databaseStore.ts
// PURPOSE: Manage database configuration state
// Replaces DatabaseStateService.ts RxJS implementation

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';
import { v4 as uuidv4 } from 'uuid';
import { DatabaseEncoder } from '../utils/databaseEncoder';
import {
  DatabaseTools,
  DatabaseType as DBToolsType
} from '../BackendTools/DatabaseTools';
import { StateDBCachingService } from '../utils/backendCaching';
import { requestAPI } from '../utils/handler';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/**
 * Supported database types
 */
export enum DatabaseType {
  MySQL = 'mysql',
  PostgreSQL = 'postgresql',
  Snowflake = 'snowflake',
  Databricks = 'databricks'
}

/**
 * Base database credentials interface
 */
export interface IDatabaseCredentials {
  id: string;
  name: string;
  description: string;
  type: DatabaseType;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * MySQL specific database credentials
 */
export interface IMySQLCredentials extends IDatabaseCredentials {
  type: DatabaseType.MySQL;
}

/**
 * PostgreSQL specific database credentials
 */
export interface IPostgreSQLCredentials extends IDatabaseCredentials {
  type: DatabaseType.PostgreSQL;
}

/**
 * Snowflake specific database credentials
 */
export interface ISnowflakeCredentials extends IDatabaseCredentials {
  type: DatabaseType.Snowflake;
  connectionUrl: string;
  warehouse?: string;
  role?: string;
}

/**
 * Databricks authentication type
 */
export type DatabricksAuthType = 'pat' | 'service_principal';

/**
 * Databricks specific database credentials
 */
export interface IDatabricksCredentials extends IDatabaseCredentials {
  type: DatabaseType.Databricks;
  connectionUrl: string;
  authType: DatabricksAuthType;
  accessToken?: string;
  clientId?: string;
  clientSecret?: string;
  oauthTokenUrl?: string;
  warehouseId?: string;
  warehouseHttpPath?: string;
  catalog: string;
  schema?: string;
}

// Database schema type definitions

export interface IDatabaseColumn {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default: string | null;
  character_maximum_length: number | null;
  numeric_precision: number | null;
  numeric_scale: number | null;
}

export interface IForeignKey {
  column_name: string;
  foreign_table_schema: string;
  foreign_table_name: string;
  foreign_column_name: string;
}

export interface IIndex {
  indexname: string;
  indexdef: string;
}

export interface ITableSchema {
  schema: string;
  table_name: string;
  full_name: string;
  columns: IDatabaseColumn[];
  primary_keys: string[];
  foreign_keys: IForeignKey[];
  indices: IIndex[];
}

export interface IMySQLPostgreSQLSchema {
  table_schemas: {
    [tableName: string]: ITableSchema;
  };
}

// Snowflake schema types
export interface IColumnBase {
  name: string;
  type: string;
  ordinal: number;
  nullable: boolean;

  [extra: string]: unknown;
}

export interface INumberColumn extends IColumnBase {
  type: 'NUMBER';
  precision: number;
  scale: number;
}

export interface ITextColumn extends IColumnBase {
  type: 'TEXT';
  max_length: number;
  description?: string;
}

export interface IDateColumn extends IColumnBase {
  type: 'DATE';
}

export type Column =
  | INumberColumn
  | ITextColumn
  | IDateColumn
  | (IColumnBase & {
      type: Exclude<string, 'NUMBER' | 'TEXT' | 'DATE'>;
    });

export interface ITableEntry {
  schema: string;
  table: string;
  type: string;
  columns: Column[];
}

export interface ISchemaEntry {
  schema: string;
  tables: ITableEntry[];
  error: string | null;
}

export interface IDatabaseDefinition {
  database: string;
  schemas: ISchemaEntry[];
}

export interface ISnowflakeSchemaData {
  databases: IDatabaseDefinition[];
}

export interface IDatabaseUrlConnection {
  id: string;
  name: string;
  description: string;
  type: DatabaseType;
  connectionUrl: string;
  createdAt: string;
  updatedAt: string;
}

export interface IDatabaseConfig {
  id: string;
  name: string;
  type: DatabaseType;
  connectionType: 'credentials' | 'url';
  credentials?:
    | IMySQLCredentials
    | IPostgreSQLCredentials
    | ISnowflakeCredentials
    | IDatabricksCredentials;
  urlConnection?: IDatabaseUrlConnection;
  schema_last_updated?: string | null;
  database_schema?: IMySQLPostgreSQLSchema | ISnowflakeSchemaData | null;
  createdAt: string;
  updatedAt: string;
}

// Event types for change tracking
export interface IDatabaseConfigChange {
  type: 'added' | 'removed' | 'updated' | 'active_changed';
  configId: string | null;
  config: IDatabaseConfig | null;
  oldConfigId?: string | null;
}

// ═══════════════════════════════════════════════════════════════
// STATE INTERFACE
// ═══════════════════════════════════════════════════════════════

interface IDatabaseState {
  configurations: IDatabaseConfig[];
  activeConfigId: string | null;
  activeConfig: IDatabaseConfig | null;
  isInitialized: boolean;
  lastChange: IDatabaseConfigChange | null;
}

interface IDatabaseActions {
  // Initialization
  initialize: () => void;
  initializeWithStateDB: () => Promise<void>;

  // Configuration CRUD
  createMySQLConfig: (
    name: string,
    description: string,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => IDatabaseConfig;

  createPostgreSQLConfig: (
    name: string,
    description: string,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => IDatabaseConfig;

  createSnowflakeConfig: (
    name: string,
    description: string,
    connectionUrl: string,
    username: string,
    password: string,
    database?: string,
    warehouse?: string,
    role?: string
  ) => IDatabaseConfig;

  createDatabricksConfig: (
    name: string,
    description: string,
    connectionUrl: string,
    authType: DatabricksAuthType,
    catalog: string,
    accessToken?: string,
    clientId?: string,
    clientSecret?: string,
    warehouseHttpPath?: string,
    dbSchema?: string
  ) => IDatabaseConfig;

  createUrlConfig: (
    name: string,
    description: string,
    type: DatabaseType,
    connectionUrl: string
  ) => IDatabaseConfig;

  // Getters
  getConfigurations: () => IDatabaseConfig[];
  getConfiguration: (configId: string) => IDatabaseConfig | null;
  getConfigurationsByType: (type: DatabaseType) => IDatabaseConfig[];
  getConfigurationsByConnectionType: (
    connectionType: 'credentials' | 'url'
  ) => IDatabaseConfig[];
  getActiveConfiguration: () => IDatabaseConfig | null;

  // Updates
  updateConfiguration: (
    configId: string,
    updates: Partial<IDatabaseConfig>
  ) => boolean;
  removeConfiguration: (configId: string) => boolean;
  setActiveConfiguration: (configId: string | null) => boolean;

  // Schema management
  fetchAndUpdateSchema: (
    configId: string
  ) => Promise<{ success: boolean; error?: string; schema?: any }>;
  getSchemaInfo: (
    configId: string
  ) => { lastUpdated: string | null; schema: any | null } | null;
  isSchemaFresh: (configId: string, maxAgeHours?: number) => boolean;

  // Backend persistence (db.toml is the single source of truth)
  saveConfigurationsToStateDB: () => Promise<void>;
  loadConfigurationsFromStateDB: () => Promise<void>;
  migrateFromStateDB: () => Promise<void>;

  // Create and persist shortcuts
  createAndPersistMySQLConfig: (
    name: string,
    description: string,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => Promise<IDatabaseConfig>;

  createAndPersistPostgreSQLConfig: (
    name: string,
    description: string,
    host: string,
    port: number,
    database: string,
    username: string,
    password: string
  ) => Promise<IDatabaseConfig>;

  createAndPersistSnowflakeConfig: (
    name: string,
    description: string,
    connectionUrl: string,
    username: string,
    password: string,
    database?: string,
    warehouse?: string,
    role?: string
  ) => Promise<IDatabaseConfig>;

  createAndPersistDatabricksConfig: (
    name: string,
    description: string,
    connectionUrl: string,
    authType: DatabricksAuthType,
    catalog: string,
    accessToken?: string,
    clientId?: string,
    clientSecret?: string,
    warehouseHttpPath?: string,
    dbSchema?: string
  ) => Promise<IDatabaseConfig>;

  removeConfigurationAndPersist: (configId: string) => Promise<boolean>;
  updateConfigurationAndPersist: (
    configId: string,
    updates: Partial<IDatabaseConfig>
  ) => Promise<boolean>;

  updateConfigurationFromFormDataAndPersist: (
    configId: string,
    name: string,
    description: string,
    type: DatabaseType,
    connectionMethod: 'credentials' | 'url',
    host?: string,
    port?: number,
    database?: string,
    username?: string,
    password?: string,
    connectionUrl?: string,
    warehouse?: string,
    account?: string,
    role?: string,
    databricksAuthType?: DatabricksAuthType,
    databricksAccessToken?: string,
    databricksClientId?: string,
    databricksClientSecret?: string,
    databricksWarehouseHttpPath?: string,
    databricksCatalog?: string,
    databricksSchema?: string
  ) => Promise<boolean>;
}

type IDatabaseStore = IDatabaseState & IDatabaseActions;

// ═══════════════════════════════════════════════════════════════
// STORE
// ═══════════════════════════════════════════════════════════════

export const useDatabaseStore = create<IDatabaseStore>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // ─────────────────────────────────────────────────────────────
      // Initial State
      // ─────────────────────────────────────────────────────────────
      configurations: [],
      activeConfigId: null,
      activeConfig: null,
      isInitialized: false,
      lastChange: null,

      // ─────────────────────────────────────────────────────────────
      // Initialization
      // ─────────────────────────────────────────────────────────────
      initialize: () => {
        set({ isInitialized: true });
      },

      initializeWithStateDB: async () => {
        try {
          get().initialize();
          await get().loadConfigurationsFromStateDB();
          console.log('[DatabaseStore] Service initialized with StateDB data');
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to initialize with StateDB:',
            error
          );
          get().initialize();
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Configuration Creation
      // ─────────────────────────────────────────────────────────────
      createMySQLConfig: (
        name,
        description,
        host,
        port,
        database,
        username,
        password
      ) => {
        const id = uuidv4();
        const now = new Date().toISOString();

        const credentials: IMySQLCredentials = {
          id,
          name,
          description,
          type: DatabaseType.MySQL,
          host,
          port,
          database,
          username,
          password,
          createdAt: now,
          updatedAt: now
        };

        const config: IDatabaseConfig = {
          id,
          name,
          type: DatabaseType.MySQL,
          connectionType: 'credentials',
          credentials,
          urlConnection: undefined,
          schema_last_updated: null,
          database_schema: null,
          createdAt: now,
          updatedAt: now
        };

        set(state => ({
          configurations: [...state.configurations, config],
          lastChange: { type: 'added', configId: id, config }
        }));

        return config;
      },

      createPostgreSQLConfig: (
        name,
        description,
        host,
        port,
        database,
        username,
        password
      ) => {
        const id = uuidv4();
        const now = new Date().toISOString();

        const credentials: IPostgreSQLCredentials = {
          id,
          name,
          description,
          type: DatabaseType.PostgreSQL,
          host,
          port,
          database,
          username,
          password,
          createdAt: now,
          updatedAt: now
        };

        const config: IDatabaseConfig = {
          id,
          name,
          type: DatabaseType.PostgreSQL,
          connectionType: 'credentials',
          credentials,
          urlConnection: undefined,
          schema_last_updated: null,
          database_schema: null,
          createdAt: now,
          updatedAt: now
        };

        set(state => ({
          configurations: [...state.configurations, config],
          lastChange: { type: 'added', configId: id, config }
        }));

        return config;
      },

      createSnowflakeConfig: (
        name,
        description,
        connectionUrl,
        username,
        password,
        database,
        warehouse,
        role
      ) => {
        const id = uuidv4();
        const now = new Date().toISOString();

        const credentials: ISnowflakeCredentials = {
          id,
          name,
          description,
          type: DatabaseType.Snowflake,
          host: '',
          port: 443,
          database: database || '',
          username,
          password,
          connectionUrl,
          warehouse,
          role,
          createdAt: now,
          updatedAt: now
        };

        const config: IDatabaseConfig = {
          id,
          name,
          type: DatabaseType.Snowflake,
          connectionType: 'credentials',
          credentials,
          urlConnection: undefined,
          schema_last_updated: null,
          database_schema: null,
          createdAt: now,
          updatedAt: now
        };

        set(state => ({
          configurations: [...state.configurations, config],
          lastChange: { type: 'added', configId: id, config }
        }));

        return config;
      },

      createDatabricksConfig: (
        name,
        description,
        connectionUrl,
        authType,
        catalog,
        accessToken,
        clientId,
        clientSecret,
        warehouseHttpPath,
        dbSchema
      ) => {
        const id = uuidv4();
        const now = new Date().toISOString();

        const credentials: IDatabricksCredentials = {
          id,
          name,
          description,
          type: DatabaseType.Databricks,
          host: '',
          port: 443,
          database: catalog || '',
          username: authType === 'pat' ? 'token' : clientId || '',
          password: authType === 'pat' ? accessToken || '' : clientSecret || '',
          connectionUrl,
          authType,
          accessToken: authType === 'pat' ? accessToken : undefined,
          clientId: authType === 'service_principal' ? clientId : undefined,
          clientSecret:
            authType === 'service_principal' ? clientSecret : undefined,
          warehouseHttpPath,
          catalog,
          schema: dbSchema,
          createdAt: now,
          updatedAt: now
        };

        const config: IDatabaseConfig = {
          id,
          name,
          type: DatabaseType.Databricks,
          connectionType: 'credentials',
          credentials,
          urlConnection: undefined,
          schema_last_updated: null,
          database_schema: null,
          createdAt: now,
          updatedAt: now
        };

        set(state => ({
          configurations: [...state.configurations, config],
          lastChange: { type: 'added', configId: id, config }
        }));

        return config;
      },

      createUrlConfig: (name, description, type, connectionUrl) => {
        const id = uuidv4();
        const now = new Date().toISOString();

        const urlConnection: IDatabaseUrlConnection = {
          id,
          name,
          description,
          type,
          connectionUrl,
          createdAt: now,
          updatedAt: now
        };

        const config: IDatabaseConfig = {
          id,
          name,
          type,
          connectionType: 'url',
          credentials: undefined,
          urlConnection,
          schema_last_updated: null,
          database_schema: null,
          createdAt: now,
          updatedAt: now
        };

        set(state => ({
          configurations: [...state.configurations, config],
          lastChange: { type: 'added', configId: id, config }
        }));

        return config;
      },

      // ─────────────────────────────────────────────────────────────
      // Getters
      // ─────────────────────────────────────────────────────────────
      getConfigurations: () => get().configurations,

      getConfiguration: configId => {
        return get().configurations.find(c => c.id === configId) || null;
      },

      getConfigurationsByType: type => {
        return get().configurations.filter(c => c.type === type);
      },

      getConfigurationsByConnectionType: connectionType => {
        return get().configurations.filter(
          c => c.connectionType === connectionType
        );
      },

      getActiveConfiguration: () => get().activeConfig,

      // ─────────────────────────────────────────────────────────────
      // Updates
      // ─────────────────────────────────────────────────────────────
      updateConfiguration: (configId, updates) => {
        const state = get();
        const configIndex = state.configurations.findIndex(
          c => c.id === configId
        );

        if (configIndex === -1) {
          return false;
        }

        const updatedConfig = {
          ...state.configurations[configIndex],
          ...updates,
          updatedAt: new Date().toISOString()
        };

        const updatedConfigurations = [...state.configurations];
        updatedConfigurations[configIndex] = updatedConfig;

        const newState: Partial<IDatabaseState> = {
          configurations: updatedConfigurations,
          lastChange: { type: 'updated', configId, config: updatedConfig }
        };

        // Update active config if it's the same
        if (state.activeConfigId === configId) {
          newState.activeConfig = updatedConfig;
        }

        set(newState);
        return true;
      },

      removeConfiguration: configId => {
        const state = get();
        const configIndex = state.configurations.findIndex(
          c => c.id === configId
        );

        if (configIndex === -1) {
          return false;
        }

        const configToRemove = state.configurations[configIndex];
        const updatedConfigurations = state.configurations.filter(
          c => c.id !== configId
        );

        const newState: Partial<IDatabaseState> = {
          configurations: updatedConfigurations,
          lastChange: { type: 'removed', configId, config: configToRemove }
        };

        // Clear active config if it was the removed one
        if (state.activeConfigId === configId) {
          newState.activeConfigId = null;
          newState.activeConfig = null;
        }

        set(newState);
        return true;
      },

      setActiveConfiguration: configId => {
        const state = get();
        const oldConfigId = state.activeConfigId;

        if (configId === null) {
          set({
            activeConfigId: null,
            activeConfig: null,
            lastChange: {
              type: 'active_changed',
              configId: null,
              config: null,
              oldConfigId
            }
          });
          return true;
        }

        const config = get().getConfiguration(configId);
        if (!config) {
          return false;
        }

        set({
          activeConfigId: configId,
          activeConfig: config,
          lastChange: {
            type: 'active_changed',
            configId,
            config,
            oldConfigId
          }
        });

        return true;
      },

      // ─────────────────────────────────────────────────────────────
      // Schema Management
      // ─────────────────────────────────────────────────────────────
      fetchAndUpdateSchema: async configId => {
        try {
          const config = get().getConfiguration(configId);
          if (!config) {
            return {
              success: false,
              error: 'Database configuration not found'
            };
          }

          let databaseUrl: string | undefined;
          let dbType: DBToolsType;
          let snowflakeConfig: any;
          let databricksConfig: any;

          if (config.connectionType === 'url' && config.urlConnection) {
            databaseUrl = config.urlConnection.connectionUrl;
            dbType = config.type as unknown as DBToolsType;
          } else if (
            config.connectionType === 'credentials' &&
            config.credentials
          ) {
            const creds = config.credentials;
            dbType = config.type as unknown as DBToolsType;

            switch (config.type) {
              case DatabaseType.PostgreSQL:
                databaseUrl = `postgresql://${creds.username}:${creds.password}@${creds.host}:${creds.port}/${creds.database}`;
                break;
              case DatabaseType.MySQL:
                databaseUrl = `mysql://${creds.username}:${creds.password}@${creds.host}:${creds.port}/${creds.database}`;
                break;
              case DatabaseType.Snowflake:
                const sfCreds = creds as ISnowflakeCredentials;
                snowflakeConfig = {
                  type: 'snowflake',
                  connectionUrl: sfCreds.connectionUrl,
                  username: sfCreds.username,
                  password: sfCreds.password,
                  warehouse: sfCreds.warehouse || undefined,
                  database: sfCreds.database || undefined,
                  role: sfCreds.role || undefined
                };
                break;
              case DatabaseType.Databricks:
                const dbCreds = creds as IDatabricksCredentials;
                databricksConfig = {
                  type: 'databricks',
                  connectionUrl: dbCreds.connectionUrl,
                  authType: dbCreds.authType,
                  accessToken: dbCreds.accessToken,
                  clientId: dbCreds.clientId,
                  clientSecret: dbCreds.clientSecret,
                  warehouseHttpPath: dbCreds.warehouseHttpPath,
                  catalog: dbCreds.catalog || undefined,
                  schema: dbCreds.schema || undefined
                };
                break;
              default:
                return {
                  success: false,
                  error: 'Unsupported database type for schema fetching'
                };
            }
          } else {
            return { success: false, error: 'Invalid database configuration' };
          }

          const databaseTools = new DatabaseTools();
          let schemaResult: string;

          if (dbType === DBToolsType.Snowflake && snowflakeConfig) {
            schemaResult = await databaseTools.getDatabaseMetadata(
              undefined,
              DBToolsType.Snowflake,
              snowflakeConfig
            );
          } else if (dbType === DBToolsType.Databricks && databricksConfig) {
            schemaResult = await databaseTools.getDatabaseMetadata(
              undefined,
              DBToolsType.Databricks,
              databricksConfig
            );
          } else {
            schemaResult = await databaseTools.getDatabaseMetadata(
              databaseUrl,
              dbType
            );
          }

          let parsedResult;
          try {
            parsedResult = JSON.parse(schemaResult);
          } catch (parseError) {
            return {
              success: false,
              error: `Failed to parse schema result: ${parseError}`
            };
          }

          if (parsedResult.error) {
            return { success: false, error: parsedResult.error };
          }

          const schemaToStore = parsedResult.schema_info
            ? typeof parsedResult.schema_info === 'string'
              ? JSON.parse(parsedResult.schema_info)
              : parsedResult.schema_info
            : parsedResult;

          const now = new Date().toISOString();
          const updateResult = get().updateConfiguration(configId, {
            schema_last_updated: now,
            database_schema: schemaToStore
          });

          if (!updateResult) {
            return {
              success: false,
              error: 'Failed to update configuration with schema information'
            };
          }

          await get().saveConfigurationsToStateDB();

          return { success: true, schema: schemaToStore };
        } catch (error) {
          console.error('[DatabaseStore] Error fetching schema:', error);
          return {
            success: false,
            error: `Schema fetch failed: ${error instanceof Error ? error.message : String(error)}`
          };
        }
      },

      getSchemaInfo: configId => {
        const config = get().getConfiguration(configId);
        if (!config) {
          return null;
        }

        return {
          lastUpdated: config.schema_last_updated || null,
          schema: config.database_schema || null
        };
      },

      isSchemaFresh: (configId, maxAgeHours = 24) => {
        const schemaInfo = get().getSchemaInfo(configId);
        if (!schemaInfo || !schemaInfo.lastUpdated || !schemaInfo.schema) {
          return false;
        }

        const lastUpdated = new Date(schemaInfo.lastUpdated);
        const now = new Date();
        const ageHours =
          (now.getTime() - lastUpdated.getTime()) / (1000 * 60 * 60);

        return ageHours <= maxAgeHours;
      },

      // ─────────────────────────────────────────────────────────────
      // Backend Persistence (db.toml is the single source of truth)
      // ─────────────────────────────────────────────────────────────

      /**
       * Save all configurations to the backend db.toml file.
       * This is the single source of truth for database configurations.
       */
      saveConfigurationsToStateDB: async () => {
        try {
          const state = get();

          console.log(
            `[DatabaseStore] Saving ${state.configurations.length} configurations to backend`
          );

          const result = await requestAPI<{ success: boolean; message: string }>(
            'db-configs/sync',
            {
              method: 'POST',
              body: JSON.stringify({ configurations: state.configurations })
            }
          );

          console.log('[DatabaseStore] Saved to backend:', result.message);
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to save configurations to backend:',
            error
          );
          throw error;
        }
      },

      /**
       * Load configurations from the backend db.toml file.
       * Also performs one-time migration from StateDB if needed.
       */
      loadConfigurationsFromStateDB: async () => {
        try {
          // First, check if we need to migrate from StateDB
          await get().migrateFromStateDB();

          // Load from backend
          const response = await requestAPI<{
            configurations: IDatabaseConfig[];
            count: number;
          }>('db-configs/sync');

          if (response.configurations.length === 0) {
            console.log('[DatabaseStore] No configurations found in backend');
            return;
          }

          set({ configurations: response.configurations });
          console.log(
            `[DatabaseStore] Loaded ${response.count} configurations from backend`
          );
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to load configurations from backend:',
            error
          );
          throw error;
        }
      },

      /**
       * One-time migration from StateDB to backend.
       * Moves existing configs from StateDB to db.toml, then clears StateDB.
       */
      migrateFromStateDB: async () => {
        try {
          // Check if we have configs in StateDB
          const encodedConfigs = await StateDBCachingService.getObjectValue<
            IDatabaseConfig[]
          >('database_configurations', []);

          if (!encodedConfigs || encodedConfigs.length === 0) {
            // No StateDB configs to migrate
            return;
          }

          console.log(
            `[DatabaseStore] Found ${encodedConfigs.length} configs in StateDB, migrating to backend...`
          );

          // Decode the configs
          const decodedConfigs = encodedConfigs
            .map(config => {
              const decoded = { ...config };

              if (config.credentials) {
                try {
                  decoded.credentials = {
                    ...config.credentials,
                    password: DatabaseEncoder.decode(
                      config.credentials.password
                    ),
                    username: DatabaseEncoder.decode(
                      config.credentials.username
                    )
                  } as any;
                } catch (error) {
                  console.warn(
                    '[DatabaseStore] Migration: Failed to decode credentials for config:',
                    config.id,
                    error
                  );
                  return null;
                }
              }

              if (config.urlConnection) {
                try {
                  decoded.urlConnection = {
                    ...config.urlConnection,
                    connectionUrl: DatabaseEncoder.decode(
                      config.urlConnection.connectionUrl
                    )
                  };
                } catch (error) {
                  console.warn(
                    '[DatabaseStore] Migration: Failed to decode URL connection for config:',
                    config.id,
                    error
                  );
                  return null;
                }
              }

              if (
                decoded.database_schema &&
                typeof decoded.database_schema === 'string'
              ) {
                try {
                  decoded.database_schema = JSON.parse(decoded.database_schema);
                } catch {
                  // Keep as is
                }
              }

              return decoded;
            })
            .filter(config => config !== null) as IDatabaseConfig[];

          if (decodedConfigs.length > 0) {
            // Save to backend
            await requestAPI<{ success: boolean; message: string }>(
              'db-configs/sync',
              {
                method: 'POST',
                body: JSON.stringify({ configurations: decodedConfigs })
              }
            );

            console.log(
              `[DatabaseStore] Migrated ${decodedConfigs.length} configs to backend`
            );
          }

          // Clear StateDB to prevent re-migration
          await StateDBCachingService.setObjectValue(
            'database_configurations',
            []
          );
          console.log('[DatabaseStore] Cleared StateDB after migration');
        } catch (error) {
          console.warn(
            '[DatabaseStore] Migration from StateDB failed (non-fatal):',
            error
          );
          // Don't throw - migration failure shouldn't block normal operation
        }
      },

      // ─────────────────────────────────────────────────────────────
      // Create and Persist Shortcuts
      // ─────────────────────────────────────────────────────────────
      createAndPersistMySQLConfig: async (
        name,
        description,
        host,
        port,
        database,
        username,
        password
      ) => {
        try {
          const config = get().createMySQLConfig(
            name,
            description,
            host,
            port,
            database,
            username,
            password
          );
          await get().saveConfigurationsToStateDB();
          console.log(
            '[DatabaseStore] MySQL configuration created and persisted'
          );
          return config;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to create and persist MySQL config:',
            error
          );
          throw error;
        }
      },

      createAndPersistPostgreSQLConfig: async (
        name,
        description,
        host,
        port,
        database,
        username,
        password
      ) => {
        try {
          const config = get().createPostgreSQLConfig(
            name,
            description,
            host,
            port,
            database,
            username,
            password
          );
          await get().saveConfigurationsToStateDB();
          console.log(
            '[DatabaseStore] PostgreSQL configuration created and persisted'
          );
          return config;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to create and persist PostgreSQL config:',
            error
          );
          throw error;
        }
      },

      createAndPersistSnowflakeConfig: async (
        name,
        description,
        connectionUrl,
        username,
        password,
        database,
        warehouse,
        role
      ) => {
        try {
          const config = get().createSnowflakeConfig(
            name,
            description,
            connectionUrl,
            username,
            password,
            database,
            warehouse,
            role
          );
          await get().saveConfigurationsToStateDB();
          console.log(
            '[DatabaseStore] Snowflake configuration created and persisted'
          );
          return config;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to create and persist Snowflake config:',
            error
          );
          throw error;
        }
      },

      createAndPersistDatabricksConfig: async (
        name,
        description,
        connectionUrl,
        authType,
        catalog,
        accessToken,
        clientId,
        clientSecret,
        warehouseHttpPath,
        dbSchema
      ) => {
        try {
          const config = get().createDatabricksConfig(
            name,
            description,
            connectionUrl,
            authType,
            catalog,
            accessToken,
            clientId,
            clientSecret,
            warehouseHttpPath,
            dbSchema
          );
          await get().saveConfigurationsToStateDB();
          console.log(
            '[DatabaseStore] Databricks configuration created and persisted'
          );
          return config;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to create and persist Databricks config:',
            error
          );
          throw error;
        }
      },

      removeConfigurationAndPersist: async configId => {
        try {
          const removed = get().removeConfiguration(configId);
          if (removed) {
            await get().saveConfigurationsToStateDB();
            console.log('[DatabaseStore] Configuration removed and persisted');
          }
          return removed;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to remove and persist configuration:',
            error
          );
          throw error;
        }
      },

      updateConfigurationAndPersist: async (configId, updates) => {
        try {
          const updated = get().updateConfiguration(configId, updates);
          if (updated) {
            await get().saveConfigurationsToStateDB();
            console.log('[DatabaseStore] Configuration updated and persisted');
          }
          return updated;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to update and persist configuration:',
            error
          );
          throw error;
        }
      },

      updateConfigurationFromFormDataAndPersist: async (
        configId,
        name,
        description,
        type,
        connectionMethod,
        host,
        port,
        database,
        username,
        password,
        connectionUrl,
        warehouse,
        account,
        role,
        databricksAuthType,
        databricksAccessToken,
        databricksClientId,
        databricksClientSecret,
        databricksWarehouseHttpPath,
        databricksCatalog,
        databricksSchema
      ) => {
        try {
          const currentConfig = get().getConfiguration(configId);
          if (!currentConfig) {
            return false;
          }

          const updatedAt = new Date().toISOString();
          let updatedConfig: IDatabaseConfig;

          if (connectionMethod === 'url' && connectionUrl) {
            updatedConfig = {
              ...currentConfig,
              name,
              type,
              connectionType: 'url',
              credentials: undefined,
              urlConnection: {
                id: currentConfig.id,
                name,
                description,
                type,
                connectionUrl,
                createdAt: currentConfig.createdAt,
                updatedAt
              },
              updatedAt
            };
          } else {
            let credentials:
              | IMySQLCredentials
              | IPostgreSQLCredentials
              | ISnowflakeCredentials
              | IDatabricksCredentials;

            if (type === DatabaseType.Snowflake) {
              credentials = {
                id: currentConfig.id,
                name,
                description,
                type: DatabaseType.Snowflake,
                host: '',
                port: 443,
                database: database || '',
                username: username!,
                password: password!,
                connectionUrl: connectionUrl!,
                warehouse: warehouse || undefined,
                role: role || undefined,
                createdAt: currentConfig.createdAt,
                updatedAt
              } as ISnowflakeCredentials;
            } else if (type === DatabaseType.Databricks) {
              const authType = databricksAuthType || 'pat';
              credentials = {
                id: currentConfig.id,
                name,
                description,
                type: DatabaseType.Databricks,
                host: '',
                port: 443,
                database: databricksCatalog || '',
                username:
                  authType === 'pat' ? 'token' : databricksClientId || '',
                password:
                  authType === 'pat'
                    ? databricksAccessToken || ''
                    : databricksClientSecret || '',
                connectionUrl: connectionUrl!,
                authType,
                accessToken:
                  authType === 'pat' ? databricksAccessToken : undefined,
                clientId:
                  authType === 'service_principal'
                    ? databricksClientId
                    : undefined,
                clientSecret:
                  authType === 'service_principal'
                    ? databricksClientSecret
                    : undefined,
                warehouseHttpPath: databricksWarehouseHttpPath,
                catalog: databricksCatalog!,
                schema: databricksSchema,
                createdAt: currentConfig.createdAt,
                updatedAt
              } as IDatabricksCredentials;
            } else {
              const baseCredentials = {
                id: currentConfig.id,
                name,
                description,
                type,
                host: host!,
                port: port!,
                database: database!,
                username: username!,
                password: password!,
                createdAt: currentConfig.createdAt,
                updatedAt
              };

              if (type === DatabaseType.MySQL) {
                credentials = {
                  ...baseCredentials,
                  type: DatabaseType.MySQL
                } as IMySQLCredentials;
              } else {
                credentials = {
                  ...baseCredentials,
                  type: DatabaseType.PostgreSQL
                } as IPostgreSQLCredentials;
              }
            }

            updatedConfig = {
              ...currentConfig,
              name,
              type,
              connectionType: 'credentials',
              credentials,
              urlConnection: undefined,
              updatedAt
            };
          }

          const updated = get().updateConfiguration(configId, updatedConfig);

          if (updated) {
            await get().saveConfigurationsToStateDB();
            console.log(
              '[DatabaseStore] Configuration updated from form data and persisted'
            );
          }

          return updated;
        } catch (error) {
          console.error(
            '[DatabaseStore] Failed to update configuration from form data:',
            error
          );
          throw error;
        }
      }
    })),
    { name: 'DatabaseStore' }
  )
);

// ═══════════════════════════════════════════════════════════════
// SELECTORS
// ═══════════════════════════════════════════════════════════════

export const selectConfigurations = (state: IDatabaseStore) =>
  state.configurations;
export const selectActiveConfig = (state: IDatabaseStore) => state.activeConfig;
export const selectActiveConfigId = (state: IDatabaseStore) =>
  state.activeConfigId;
export const selectIsInitialized = (state: IDatabaseStore) =>
  state.isInitialized;
export const selectLastChange = (state: IDatabaseStore) => state.lastChange;

// ═══════════════════════════════════════════════════════════════
// NON-REACT SUBSCRIPTIONS (for TypeScript services)
// ═══════════════════════════════════════════════════════════════

/**
 * Subscribe to all database configuration changes.
 */
export function subscribeToDatabaseChanges(
  callback: (state: IDatabaseState) => void
): () => void {
  return useDatabaseStore.subscribe(callback);
}

/**
 * Subscribe to configuration change events.
 */
export function subscribeToConfigChanges(
  callback: (change: IDatabaseConfigChange | null) => void
): () => void {
  return useDatabaseStore.subscribe(state => state.lastChange, callback);
}

/**
 * Subscribe to active configuration changes.
 */
export function subscribeToActiveConfigChanges(
  callback: (config: IDatabaseConfig | null) => void
): () => void {
  return useDatabaseStore.subscribe(state => state.activeConfig, callback);
}

/**
 * Subscribe to configurations array changes.
 */
export function subscribeToConfigurationsChanges(
  callback: (configurations: IDatabaseConfig[]) => void
): () => void {
  return useDatabaseStore.subscribe(state => state.configurations, callback);
}

// ═══════════════════════════════════════════════════════════════
// CONVENIENCE ACCESSORS (for non-React code)
// ═══════════════════════════════════════════════════════════════

/**
 * Get the current database state directly.
 */
export function getDatabaseState() {
  return useDatabaseStore.getState();
}

/**
 * Compatibility wrapper that mirrors the old DatabaseStateService API.
 * Use this for easier migration of existing code.
 */
export const DatabaseStateService = {
  getState: () => useDatabaseStore.getState(),
  setState: (partial: Partial<IDatabaseState>) =>
    useDatabaseStore.setState(partial),
  changes: {
    subscribe: (callback: (state: IDatabaseState) => void) => {
      const unsubscribe = useDatabaseStore.subscribe(callback);
      return { unsubscribe };
    }
  },
  initialize: () => useDatabaseStore.getState().initialize(),
  initializeWithStateDB: () =>
    useDatabaseStore.getState().initializeWithStateDB(),
  createMySQLConfig: (
    ...args: Parameters<IDatabaseActions['createMySQLConfig']>
  ) => useDatabaseStore.getState().createMySQLConfig(...args),
  createPostgreSQLConfig: (
    ...args: Parameters<IDatabaseActions['createPostgreSQLConfig']>
  ) => useDatabaseStore.getState().createPostgreSQLConfig(...args),
  createSnowflakeConfig: (
    ...args: Parameters<IDatabaseActions['createSnowflakeConfig']>
  ) => useDatabaseStore.getState().createSnowflakeConfig(...args),
  createDatabricksConfig: (
    ...args: Parameters<IDatabaseActions['createDatabricksConfig']>
  ) => useDatabaseStore.getState().createDatabricksConfig(...args),
  createUrlConfig: (...args: Parameters<IDatabaseActions['createUrlConfig']>) =>
    useDatabaseStore.getState().createUrlConfig(...args),
  getConfigurations: () => useDatabaseStore.getState().getConfigurations(),
  getConfiguration: (configId: string) =>
    useDatabaseStore.getState().getConfiguration(configId),
  getConfigurationsByType: (type: DatabaseType) =>
    useDatabaseStore.getState().getConfigurationsByType(type),
  getConfigurationsByConnectionType: (connectionType: 'credentials' | 'url') =>
    useDatabaseStore
      .getState()
      .getConfigurationsByConnectionType(connectionType),
  getActiveConfiguration: () =>
    useDatabaseStore.getState().getActiveConfiguration(),
  updateConfiguration: (
    ...args: Parameters<IDatabaseActions['updateConfiguration']>
  ) => useDatabaseStore.getState().updateConfiguration(...args),
  removeConfiguration: (configId: string) =>
    useDatabaseStore.getState().removeConfiguration(configId),
  setActiveConfiguration: (configId: string | null) =>
    useDatabaseStore.getState().setActiveConfiguration(configId),
  fetchAndUpdateSchema: (configId: string) =>
    useDatabaseStore.getState().fetchAndUpdateSchema(configId),
  getSchemaInfo: (configId: string) =>
    useDatabaseStore.getState().getSchemaInfo(configId),
  isSchemaFresh: (configId: string, maxAgeHours?: number) =>
    useDatabaseStore.getState().isSchemaFresh(configId, maxAgeHours),
  saveConfigurationsToStateDB: () =>
    useDatabaseStore.getState().saveConfigurationsToStateDB(),
  loadConfigurationsFromStateDB: () =>
    useDatabaseStore.getState().loadConfigurationsFromStateDB(),
  createAndPersistMySQLConfig: (
    ...args: Parameters<IDatabaseActions['createAndPersistMySQLConfig']>
  ) => useDatabaseStore.getState().createAndPersistMySQLConfig(...args),
  createAndPersistPostgreSQLConfig: (
    ...args: Parameters<IDatabaseActions['createAndPersistPostgreSQLConfig']>
  ) => useDatabaseStore.getState().createAndPersistPostgreSQLConfig(...args),
  createAndPersistSnowflakeConfig: (
    ...args: Parameters<IDatabaseActions['createAndPersistSnowflakeConfig']>
  ) => useDatabaseStore.getState().createAndPersistSnowflakeConfig(...args),
  createAndPersistDatabricksConfig: (
    ...args: Parameters<IDatabaseActions['createAndPersistDatabricksConfig']>
  ) => useDatabaseStore.getState().createAndPersistDatabricksConfig(...args),
  removeConfigurationAndPersist: (configId: string) =>
    useDatabaseStore.getState().removeConfigurationAndPersist(configId),
  updateConfigurationAndPersist: (
    ...args: Parameters<IDatabaseActions['updateConfigurationAndPersist']>
  ) => useDatabaseStore.getState().updateConfigurationAndPersist(...args),
  updateConfigurationFromFormDataAndPersist: (
    ...args: Parameters<
      IDatabaseActions['updateConfigurationFromFormDataAndPersist']
    >
  ) =>
    useDatabaseStore
      .getState()
      .updateConfigurationFromFormDataAndPersist(...args),
  // Event observables (compatibility layer)
  onConfigurationAdded: () => ({
    subscribe: (callback: (config: IDatabaseConfig) => void) => {
      const unsubscribe = useDatabaseStore.subscribe(
        state => state.lastChange,
        change => {
          if (change?.type === 'added' && change.config) {
            callback(change.config);
          }
        }
      );
      return { unsubscribe };
    }
  }),
  onConfigurationRemoved: () => ({
    subscribe: (
      callback: (data: { configId: string; config: IDatabaseConfig }) => void
    ) => {
      const unsubscribe = useDatabaseStore.subscribe(
        state => state.lastChange,
        change => {
          if (change?.type === 'removed' && change.configId && change.config) {
            callback({ configId: change.configId, config: change.config });
          }
        }
      );
      return { unsubscribe };
    }
  }),
  onConfigurationUpdated: () => ({
    subscribe: (callback: (config: IDatabaseConfig) => void) => {
      const unsubscribe = useDatabaseStore.subscribe(
        state => state.lastChange,
        change => {
          if (change?.type === 'updated' && change.config) {
            callback(change.config);
          }
        }
      );
      return { unsubscribe };
    }
  }),
  onActiveConfigurationChanged: () => ({
    subscribe: (
      callback: (data: {
        oldConfigId: string | null;
        newConfigId: string | null;
      }) => void
    ) => {
      const unsubscribe = useDatabaseStore.subscribe(
        state => state.lastChange,
        change => {
          if (change?.type === 'active_changed') {
            callback({
              oldConfigId: change.oldConfigId || null,
              newConfigId: change.configId
            });
          }
        }
      );
      return { unsubscribe };
    }
  })
};
