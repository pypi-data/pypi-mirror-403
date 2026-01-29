"""
Database Configuration Service
Manages database configurations stored in db.toml in the connect/ cache directory
"""

import logging
from typing import Any, Dict, List, Optional

from .signalpilot_home import get_signalpilot_home

logger = logging.getLogger(__name__)


class DatabaseConfigService:
    """
    Service for managing database configurations in TOML format.
    Configurations stored at <cache_dir>/connect/db.toml
    (e.g., ~/Library/Caches/SignalPilotAI/connect/db.toml on macOS)
    """

    _instance = None

    # Supported database types
    SUPPORTED_TYPES = ["snowflake", "postgres", "mysql", "databricks"]

    def __init__(self):
        self._home_manager = get_signalpilot_home()

    @classmethod
    def get_instance(cls) -> 'DatabaseConfigService':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = DatabaseConfigService()
        return cls._instance

    def get_all_configs(self) -> List[Dict[str, Any]]:
        """Get all database configurations."""
        return self._home_manager.get_database_configs()

    def get_config(self, db_type: str, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific database configuration."""
        return self._home_manager.get_database_config(db_type, name)

    def get_configs_by_type(self, db_type: str) -> List[Dict[str, Any]]:
        """Get all configurations for a specific database type."""
        configs = self.get_all_configs()
        return [c for c in configs if c.get("type") == db_type]

    def add_config(self, db_type: str, config: Dict[str, Any]) -> bool:
        """Add a new database configuration."""
        if db_type not in self.SUPPORTED_TYPES:
            logger.error(f"Unsupported database type: {db_type}")
            return False

        if "name" not in config:
            logger.error("Database config must have a 'name' field")
            return False

        return self._home_manager.add_database_config(db_type, config)

    def update_config(self, db_type: str, name: str,
                      updates: Dict[str, Any]) -> bool:
        """Update an existing database configuration."""
        return self._home_manager.update_database_config(db_type, name, updates)

    def remove_config(self, db_type: str, name: str) -> bool:
        """Remove a database configuration."""
        return self._home_manager.remove_database_config(db_type, name)

    def set_defaults(self, defaults: Dict[str, Any]) -> bool:
        """Set global defaults for database configurations."""
        return self._home_manager.set_database_defaults(defaults)

    def get_defaults(self) -> Dict[str, Any]:
        """Get global defaults."""
        return self._home_manager.get_database_defaults()

    def sync_all_configs(self, configs: List[Dict[str, Any]]) -> bool:
        """
        Replace all database configurations with the provided list.
        This is used to sync configurations from the frontend StateDB to db.toml.

        Args:
            configs: List of database configuration dictionaries.
                     Each config must have 'name' and 'type' fields.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Group configs by type
            configs_by_type = {}
            for config in configs:
                db_type = config.get('type', '').lower()

                # Map frontend type names to backend type names
                type_mapping = {
                    'postgresql': 'postgres',
                    'postgres': 'postgres',
                    'mysql': 'mysql',
                    'snowflake': 'snowflake',
                    'databricks': 'databricks',
                }

                db_type = type_mapping.get(db_type, db_type)

                if db_type not in self.SUPPORTED_TYPES:
                    logger.warning(f"[DatabaseConfigService] Skipping unsupported type: {db_type}")
                    continue

                if db_type not in configs_by_type:
                    configs_by_type[db_type] = []

                # Extract relevant fields for db.toml
                toml_config = self._convert_frontend_config_to_toml(config, db_type)
                if toml_config:
                    configs_by_type[db_type].append(toml_config)

            # Build the full TOML structure
            full_config = self._home_manager.read_db_config()
            defaults = full_config.get("defaults", {})

            # Create new config with defaults preserved
            new_config = {"defaults": defaults}

            # Add each type's configs
            for db_type in self.SUPPORTED_TYPES:
                if db_type in configs_by_type and configs_by_type[db_type]:
                    new_config[db_type] = configs_by_type[db_type]

            # Write the new config
            success = self._home_manager.write_db_config(new_config)

            if success:
                logger.info(f"[DatabaseConfigService] Synced {len(configs)} configurations to db.toml")
                # Also print to ensure it shows in server console
                print(f"[DatabaseConfigService] *** WROTE db.toml with {len(configs)} configs ***")
                print(f"[DatabaseConfigService] Configs written: {[c.get('name') for c in configs]}")
                # Log file path and modification time
                import os
                from datetime import datetime
                db_path = self._home_manager.db_config_path
                if db_path.exists():
                    mtime = os.path.getmtime(db_path)
                    mtime_str = datetime.fromtimestamp(mtime).isoformat()
                    print(f"[DatabaseConfigService] db.toml path: {db_path}")
                    print(f"[DatabaseConfigService] db.toml modified at: {mtime_str}")
            else:
                logger.error("[DatabaseConfigService] Failed to write db.toml")
                print("[DatabaseConfigService] *** FAILED to write db.toml ***")

            return success

        except Exception as e:
            logger.error(f"[DatabaseConfigService] Error syncing configs: {e}")
            return False

    def get_all_configs_frontend_format(self) -> List[Dict[str, Any]]:
        """
        Get all database configurations in the format expected by the frontend.
        Converts flat TOML configs to nested frontend format with 'credentials' object.
        """
        toml_configs = self.get_all_configs()
        frontend_configs = []

        for config in toml_configs:
            frontend_config = self._convert_toml_config_to_frontend(config)
            if frontend_config:
                frontend_configs.append(frontend_config)

        return frontend_configs

    def _convert_toml_config_to_frontend(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a TOML database config to the frontend format.
        """
        try:
            import json
            import uuid
            from datetime import datetime

            db_name = config.get('name', '')
            db_type = config.get('type', '')

            if not db_name:
                return None

            # Map backend type names to frontend type names
            type_mapping = {
                'postgres': 'postgresql',
                'postgresql': 'postgresql',
                'mysql': 'mysql',
                'snowflake': 'snowflake',
                'databricks': 'databricks',
            }
            frontend_type = type_mapping.get(db_type, db_type)

            # Generate a deterministic ID based on name and type
            config_id = config.get('id') or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{db_name}-{db_type}"))
            now = datetime.now().isoformat()

            # Build credentials object
            credentials = {
                'id': config_id,
                'name': db_name,
                'description': config.get('description', ''),
                'type': frontend_type,
                'host': config.get('host', ''),
                'port': config.get('port', 0),
                'database': config.get('database', ''),
                'username': config.get('username', ''),
                'password': config.get('password', ''),
                'createdAt': config.get('createdAt', now),
                'updatedAt': config.get('updatedAt', now),
            }

            # Add type-specific fields
            conn_url = config.get('connection_url') or config.get('connectionUrl', '')
            if conn_url:
                credentials['connectionUrl'] = conn_url

            if db_type == 'snowflake':
                if config.get('warehouse'):
                    credentials['warehouse'] = config['warehouse']
                if config.get('role'):
                    credentials['role'] = config['role']

            if db_type == 'databricks':
                credentials['authType'] = config.get('auth_type') or config.get('authType', 'pat')
                if config.get('access_token') or config.get('accessToken'):
                    credentials['accessToken'] = config.get('access_token') or config.get('accessToken')
                if config.get('client_id') or config.get('clientId'):
                    credentials['clientId'] = config.get('client_id') or config.get('clientId')
                if config.get('client_secret') or config.get('clientSecret'):
                    credentials['clientSecret'] = config.get('client_secret') or config.get('clientSecret')
                if config.get('http_path') or config.get('warehouseHttpPath'):
                    credentials['warehouseHttpPath'] = config.get('http_path') or config.get('warehouseHttpPath')
                if config.get('catalog'):
                    credentials['catalog'] = config['catalog']
                if config.get('schema'):
                    credentials['schema'] = config['schema']

            # Parse database_schema from JSON string if needed
            db_schema = config.get('database_schema')
            if db_schema and isinstance(db_schema, str):
                try:
                    db_schema = json.loads(db_schema)
                except (json.JSONDecodeError, ValueError):
                    db_schema = None

            # Build frontend config
            frontend_config = {
                'id': config_id,
                'name': db_name,
                'type': frontend_type,
                'connectionType': 'credentials',
                'credentials': credentials,
                'schema_last_updated': config.get('schema_last_updated'),
                'database_schema': db_schema,
                'createdAt': config.get('createdAt', now),
                'updatedAt': config.get('updatedAt', now),
            }

            return frontend_config

        except Exception as e:
            logger.error(f"[DatabaseConfigService] Error converting TOML config to frontend: {e}")
            return None

    def _convert_frontend_config_to_toml(self, config: Dict[str, Any], db_type: str) -> Optional[Dict[str, Any]]:
        """
        Convert a frontend database configuration to the TOML format.

        Frontend configs may have nested 'credentials' or 'urlConnection' objects.
        This flattens them for TOML storage.
        """
        try:
            import json

            toml_config = {"name": config.get("name", "")}

            if not toml_config["name"]:
                logger.warning("[DatabaseConfigService] Config missing name, skipping")
                return None

            # Preserve metadata fields
            if config.get('id'):
                toml_config['id'] = config['id']
            if config.get('createdAt'):
                toml_config['createdAt'] = config['createdAt']
            if config.get('updatedAt'):
                toml_config['updatedAt'] = config['updatedAt']
            if config.get('schema_last_updated'):
                toml_config['schema_last_updated'] = config['schema_last_updated']
            if config.get('database_schema'):
                # Serialize as JSON string for TOML storage (skip if already a string)
                schema = config['database_schema']
                if isinstance(schema, str):
                    toml_config['database_schema'] = schema
                else:
                    toml_config['database_schema'] = json.dumps(schema)

            # Check if it has credentials object (from frontend)
            creds = config.get("credentials")
            if creds:
                # Extract fields from credentials
                for field in ['host', 'port', 'database', 'username', 'password',
                              'connectionUrl', 'warehouse', 'role', 'authType',
                              'accessToken', 'clientId', 'clientSecret',
                              'warehouseHttpPath', 'catalog', 'schema']:
                    if field in creds and creds[field]:
                        # Convert camelCase to snake_case for some fields
                        toml_field = field
                        if field == 'connectionUrl':
                            toml_field = 'connection_url'
                        elif field == 'authType':
                            toml_field = 'auth_type'
                        elif field == 'accessToken':
                            toml_field = 'access_token'
                        elif field == 'clientId':
                            toml_field = 'client_id'
                        elif field == 'clientSecret':
                            toml_field = 'client_secret'
                        elif field == 'warehouseHttpPath':
                            toml_field = 'http_path'
                        toml_config[toml_field] = creds[field]

            # Check if it has urlConnection (connection URL mode)
            url_conn = config.get("urlConnection")
            if url_conn and url_conn.get("connectionUrl"):
                toml_config["connection_url"] = url_conn["connectionUrl"]

            # Also copy top-level fields that might be present
            for field in ['host', 'port', 'database', 'username', 'password',
                          'connectionUrl', 'connection_url', 'warehouse', 'role',
                          'auth_type', 'access_token', 'client_id', 'client_secret',
                          'http_path', 'catalog', 'schema']:
                if field in config and config[field] and field not in toml_config:
                    toml_config[field] = config[field]

            return toml_config

        except Exception as e:
            logger.error(f"[DatabaseConfigService] Error converting config: {e}")
            return None

    # ==================== Type-specific helpers ====================

    def add_snowflake_config(self, name: str, account: str,
                             database: str = None,
                             warehouse: str = None,
                             role: str = None,
                             username: str = None,
                             password: str = None,
                             **extra) -> bool:
        """Add a Snowflake database configuration."""
        config = {
            "name": name,
            "account": account,
        }
        if database:
            config["database"] = database
        if warehouse:
            config["warehouse"] = warehouse
        if role:
            config["role"] = role
        if username:
            config["username"] = username
        if password:
            config["password"] = password
        config.update(extra)

        return self.add_config("snowflake", config)

    def add_postgres_config(self, name: str, host: str, port: int,
                            database: str, username: str, password: str,
                            **extra) -> bool:
        """Add a PostgreSQL database configuration."""
        config = {
            "name": name,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password,
        }
        config.update(extra)

        return self.add_config("postgres", config)

    def add_mysql_config(self, name: str, host: str, port: int,
                         database: str, username: str, password: str,
                         **extra) -> bool:
        """Add a MySQL database configuration."""
        config = {
            "name": name,
            "host": host,
            "port": port,
            "database": database,
            "username": username,
            "password": password,
        }
        config.update(extra)

        return self.add_config("mysql", config)

    def add_databricks_config(self, name: str, host: str,
                              http_path: str, catalog: str,
                              auth_type: str = "pat",
                              access_token: str = None,
                              client_id: str = None,
                              client_secret: str = None,
                              **extra) -> bool:
        """Add a Databricks database configuration."""
        config = {
            "name": name,
            "host": host,
            "http_path": http_path,
            "catalog": catalog,
            "auth_type": auth_type,
        }
        if access_token:
            config["access_token"] = access_token
        if client_id:
            config["client_id"] = client_id
        if client_secret:
            config["client_secret"] = client_secret
        config.update(extra)

        return self.add_config("databricks", config)


def get_database_config_service() -> DatabaseConfigService:
    """Get the singleton instance."""
    return DatabaseConfigService.get_instance()
