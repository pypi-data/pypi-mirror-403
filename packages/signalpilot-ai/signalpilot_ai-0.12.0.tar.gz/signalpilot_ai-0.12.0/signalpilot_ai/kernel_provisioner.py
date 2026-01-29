"""
SignalPilot Kernel Provisioner

Custom kernel provisioner that injects database environment variables
at kernel launch time, eliminating the need for runtime code execution
to set up database connections.

This provisioner reads database configurations from db.toml and sets
environment variables in the format: {DB_NAME}_{FIELD}

For example, a database named "Production DB" would have:
- PRODUCTION_DB_HOST
- PRODUCTION_DB_PORT
- PRODUCTION_DB_DATABASE
- PRODUCTION_DB_USERNAME
- PRODUCTION_DB_PASSWORD
- PRODUCTION_DB_TYPE
- PRODUCTION_DB_CONNECTION_JSON
"""

import json
import logging
import os
from typing import Any, Dict

from jupyter_client.provisioning import LocalProvisioner

from .signalpilot_home import get_signalpilot_home

logger = logging.getLogger(__name__)


def _get_env_var_prefix(db_name: str) -> str:
    """
    Convert a database name to an environment variable prefix.
    Example: "SignalPilot production DB" -> "SIGNALPILOT_PRODUCTION_DB"
    """
    return db_name.upper().replace(' ', '_').replace('-', '_').replace('.', '_')


def _sanitize_env_var_name(name: str) -> str:
    """Sanitize a string to be a valid environment variable name."""
    import re
    # Replace any non-alphanumeric characters (except underscore) with underscore
    sanitized = re.sub(r'[^A-Z0-9_]', '_', name.upper())
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip('_')


def build_database_env_vars() -> Dict[str, str]:
    """
    Build environment variables dictionary from all database configurations.

    Returns a dictionary of environment variable name -> value pairs.
    """
    env_vars = {}

    try:
        home = get_signalpilot_home()
        db_configs = home.get_database_configs()

        logger.info(f"[SignalPilotProvisioner] Building env vars for {len(db_configs)} database configs")

        for config in db_configs:
            db_name = config.get('name', '')
            db_type = config.get('type', '')

            if not db_name:
                logger.warning("[SignalPilotProvisioner] Skipping database config without name")
                continue

            prefix = _get_env_var_prefix(db_name)

            # Set common fields
            if 'host' in config:
                env_vars[f'{prefix}_HOST'] = str(config['host'])
            if 'port' in config:
                env_vars[f'{prefix}_PORT'] = str(config['port'])
            if 'database' in config:
                env_vars[f'{prefix}_DATABASE'] = str(config['database'])
            if 'username' in config:
                env_vars[f'{prefix}_USERNAME'] = str(config['username'])
            if 'password' in config:
                env_vars[f'{prefix}_PASSWORD'] = str(config['password'])

            env_vars[f'{prefix}_TYPE'] = db_type

            # Snowflake-specific fields
            if db_type == 'snowflake':
                if 'connectionUrl' in config:
                    env_vars[f'{prefix}_CONNECTION_URL'] = str(config['connectionUrl'])

                    # Extract account from connection URL
                    connection_url = config['connectionUrl']
                    import re
                    account_match = re.match(r'https?://([^./]+)', connection_url)
                    if account_match:
                        env_vars[f'{prefix}_ACCOUNT'] = account_match.group(1)

                if 'warehouse' in config and config['warehouse']:
                    env_vars[f'{prefix}_WAREHOUSE'] = str(config['warehouse'])
                if 'role' in config and config['role']:
                    env_vars[f'{prefix}_ROLE'] = str(config['role'])

            # Databricks-specific fields
            if db_type == 'databricks':
                # Use whichever value is available: connectionUrl or host
                databricks_host = config.get('connectionUrl') or config.get('host') or ''
                if databricks_host:
                    # Set both HOST and CONNECTION_URL to the same value for Databricks
                    env_vars[f'{prefix}_HOST'] = str(databricks_host)
                    env_vars[f'{prefix}_CONNECTION_URL'] = str(databricks_host)
                if 'authType' in config:
                    env_vars[f'{prefix}_AUTH_TYPE'] = str(config['authType'])
                if 'accessToken' in config and config['accessToken']:
                    env_vars[f'{prefix}_ACCESS_TOKEN'] = str(config['accessToken'])
                if 'clientId' in config and config['clientId']:
                    env_vars[f'{prefix}_CLIENT_ID'] = str(config['clientId'])
                if 'clientSecret' in config and config['clientSecret']:
                    env_vars[f'{prefix}_CLIENT_SECRET'] = str(config['clientSecret'])
                if 'oauthTokenUrl' in config and config['oauthTokenUrl']:
                    env_vars[f'{prefix}_OAUTH_TOKEN_URL'] = str(config['oauthTokenUrl'])
                if 'warehouseId' in config and config['warehouseId']:
                    env_vars[f'{prefix}_WAREHOUSE_ID'] = str(config['warehouseId'])
                if 'warehouseHttpPath' in config and config['warehouseHttpPath']:
                    env_vars[f'{prefix}_WAREHOUSE_HTTP_PATH'] = str(config['warehouseHttpPath'])
                if 'catalog' in config and config['catalog']:
                    env_vars[f'{prefix}_CATALOG'] = str(config['catalog'])
                if 'schema' in config and config['schema']:
                    env_vars[f'{prefix}_SCHEMA'] = str(config['schema'])

            # Build connection JSON with all available fields
            connection_json = {
                'name': db_name,
                'type': db_type,
            }

            # Add all config fields to connection JSON
            for key in ['host', 'port', 'database', 'username', 'password',
                       'connectionUrl', 'warehouse', 'role', 'authType',
                       'accessToken', 'clientId', 'clientSecret', 'oauthTokenUrl',
                       'warehouseId', 'warehouseHttpPath', 'catalog', 'schema']:
                if key in config and config[key]:
                    connection_json[key] = config[key]

            env_vars[f'{prefix}_CONNECTION_JSON'] = json.dumps(connection_json)

            logger.debug(f"[SignalPilotProvisioner] Set env vars for database: {db_name}")

        logger.info(f"[SignalPilotProvisioner] Built {len(env_vars)} environment variables")

    except Exception as e:
        logger.error(f"[SignalPilotProvisioner] Error building database env vars: {e}")

    return env_vars


class SignalPilotProvisioner(LocalProvisioner):
    """
    Custom kernel provisioner that injects database environment variables
    at kernel launch time.

    This provisioner extends LocalProvisioner and overrides pre_launch()
    to inject environment variables before the kernel starts.

    Environment variables are read from the SignalPilot db.toml configuration
    file and set in the kernel's environment.

    This solves the race condition with "Restart kernel and run all cells"
    because env vars are set BEFORE the kernel process starts, not via
    code execution after the kernel is ready.
    """

    async def pre_launch(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Prepare for kernel launch by injecting database environment variables.

        This method is called BEFORE the kernel process is started (before Popen),
        which means environment variables are available from the very first line
        of code that runs in the kernel. This eliminates any race conditions.
        """
        # Use print to ensure it shows in server console (logger might be filtered)
        print("[SignalPilotProvisioner] *** PRE_LAUNCH CALLED ***")
        logger.info("[SignalPilotProvisioner] pre_launch called - injecting database env vars")

        # Call parent's pre_launch first
        kwargs = await super().pre_launch(**kwargs)

        try:
            # Get the environment dictionary (create if not exists)
            env = kwargs.get('env')
            if env is None:
                env = os.environ.copy()
            else:
                # Ensure we have a mutable copy
                env = dict(env)

            # Build and inject database environment variables
            db_env_vars = build_database_env_vars()

            if db_env_vars:
                env.update(db_env_vars)
                logger.info(
                    f"[SignalPilotProvisioner] Successfully injected {len(db_env_vars)} "
                    f"database environment variables into kernel environment"
                )
                # Log the database names (not values for security)
                db_names = set()
                for key in db_env_vars.keys():
                    # Extract database name from env var (e.g., "MY_DB_HOST" -> "MY_DB")
                    parts = key.rsplit('_', 1)
                    if len(parts) > 1:
                        db_names.add(parts[0])
                if db_names:
                    logger.info(
                        f"[SignalPilotProvisioner] Databases configured: {', '.join(sorted(db_names))}"
                    )
            else:
                logger.info(
                    "[SignalPilotProvisioner] No database configurations found in db.toml"
                )

            # Update kwargs with the modified environment
            kwargs['env'] = env

        except Exception as e:
            logger.error(f"[SignalPilotProvisioner] Error in pre_launch: {e}", exc_info=True)
            # Don't fail kernel launch if env var injection fails
            # The runtime injection in KernelUtils will serve as fallback

        return kwargs
