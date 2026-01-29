try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'signalpilot_ai' outside a proper installation.")
    __version__ = "dev"
from .handlers import setup_handlers
from .mcp_server_manager import autostart_mcp_servers

import json
import subprocess
from pathlib import Path


def _get_database_env_vars():
    """
    Build environment variables dictionary from database configurations.
    This is called at server startup and when refreshing kernel env vars.
    """
    from .signalpilot_home import get_signalpilot_home

    env_vars = {}

    def get_config_value(config, *keys):
        """Get a value from config, trying multiple key names (camelCase and snake_case)."""
        for key in keys:
            if key in config and config[key]:
                return config[key]
        return None

    try:
        home = get_signalpilot_home()
        db_configs = home.get_database_configs()

        for config in db_configs:
            db_name = config.get('name', '')
            db_type = config.get('type', '')

            if not db_name:
                continue

            # Convert name to env var prefix: "My DB" -> "MY_DB"
            prefix = db_name.upper().replace(' ', '_').replace('-', '_').replace('.', '_')

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

            # Build CONNECTION_URL for all database types except Snowflake
            # Snowflake uses account/user/password separately, not a single URL
            if db_type in ('postgres', 'postgresql'):
                # Check if a connection URL is already provided
                existing_url = get_config_value(config, 'connectionUrl', 'connection_url')
                if existing_url:
                    env_vars[f'{prefix}_CONNECTION_URL'] = existing_url
                else:
                    # Build PostgreSQL connection URL from individual fields
                    username = config.get('username', '')
                    password = config.get('password', '')
                    host = config.get('host', '')
                    port = config.get('port', 5432)
                    database = config.get('database', '')
                    env_vars[f'{prefix}_CONNECTION_URL'] = f"postgresql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == 'mysql':
                # Check if a connection URL is already provided
                existing_url = get_config_value(config, 'connectionUrl', 'connection_url')
                if existing_url:
                    env_vars[f'{prefix}_CONNECTION_URL'] = existing_url
                else:
                    # Build MySQL connection URL from individual fields
                    username = config.get('username', '')
                    password = config.get('password', '')
                    host = config.get('host', '')
                    port = config.get('port', 3306)
                    database = config.get('database', '')
                    env_vars[f'{prefix}_CONNECTION_URL'] = f"mysql://{username}:{password}@{host}:{port}/{database}"
            elif db_type == 'databricks':
                # For Databricks, set HOST to the server hostname (from connectionUrl)
                # This is used with the databricks-sql-connector, not SQLAlchemy
                server_hostname = get_config_value(config, 'connectionUrl', 'connection_url')
                if server_hostname:
                    env_vars[f'{prefix}_HOST'] = server_hostname

            # Snowflake-specific
            if db_type == 'snowflake':
                warehouse = get_config_value(config, 'warehouse')
                if warehouse:
                    env_vars[f'{prefix}_WAREHOUSE'] = str(warehouse)
                role = get_config_value(config, 'role')
                if role:
                    env_vars[f'{prefix}_ROLE'] = str(role)

            # Databricks-specific (check both camelCase and snake_case)
            if db_type == 'databricks':
                databricks_fields = [
                    ('authType', 'auth_type', 'AUTH_TYPE'),
                    ('accessToken', 'access_token', 'ACCESS_TOKEN'),
                    ('clientId', 'client_id', 'CLIENT_ID'),
                    ('clientSecret', 'client_secret', 'CLIENT_SECRET'),
                    ('oauthTokenUrl', 'oauth_token_url', 'OAUTH_TOKEN_URL'),
                    ('warehouseId', 'warehouse_id', 'WAREHOUSE_ID'),
                    ('warehouseHttpPath', 'http_path', 'WAREHOUSE_HTTP_PATH'),
                    ('catalog', 'catalog', 'CATALOG'),
                    ('schema', 'schema', 'SCHEMA'),
                ]
                for camel, snake, env_suffix in databricks_fields:
                    value = get_config_value(config, camel, snake)
                    if value:
                        env_vars[f'{prefix}_{env_suffix}'] = str(value)

            # Connection JSON
            env_vars[f'{prefix}_CONNECTION_JSON'] = json.dumps(config)

    except Exception:
        pass

    return env_vars


def _setup_kernel_env_injection(server_app):
    """
    Hook into the kernel provisioner to inject database env vars at kernel start.

    This monkey-patches the LocalProvisioner's pre_launch method which is called
    before every kernel process launch, including restarts.
    """
    log = server_app.log

    try:
        from jupyter_client.provisioning import LocalProvisioner
        import os

        # Check if already patched
        if hasattr(LocalProvisioner, '_signalpilot_patched'):
            log.info("[signalpilot_ai] LocalProvisioner already patched")
            return

        # Store the original method
        original_pre_launch = LocalProvisioner.pre_launch

        async def patched_pre_launch(self, **kwargs):
            """Wrapper that injects database env vars before launching kernel process."""
            # Get database env vars
            db_env_vars = _get_database_env_vars()

            if db_env_vars:
                # Get or create the env dict
                env = kwargs.get('env')
                if env is None:
                    env = os.environ.copy()
                else:
                    env = dict(env)

                # Inject database env vars
                env.update(db_env_vars)
                kwargs['env'] = env

            # Call original method
            return await original_pre_launch(self, **kwargs)

        # Patch at class level
        LocalProvisioner.pre_launch = patched_pre_launch
        LocalProvisioner._signalpilot_patched = True

        log.info("[signalpilot_ai] Kernel env injection hook installed on LocalProvisioner.pre_launch")

    except Exception as e:
        log.warning(f"[signalpilot_ai] Could not install kernel env injection hook: {e}")
        import traceback
        log.warning(traceback.format_exc())
        log.warning("[signalpilot_ai] Database env vars will be set at runtime instead")


def _configure_kernel_env_vars(log):
    """
    Configure kernel specs with database environment variables.

    This directly adds env vars to kernel.json's 'env' field, which is
    simpler and more reliable than using a custom provisioner.
    """
    import shutil
    import os

    try:
        # Get database env vars
        db_env_vars = _get_database_env_vars()

        if not db_env_vars:
            log.info("[signalpilot_ai] No database configurations found, skipping kernel env setup")
            return

        log.info(f"[signalpilot_ai] Found {len(db_env_vars)} database env vars to inject")

        # Get list of kernel specs
        result = subprocess.run(
            ['jupyter', 'kernelspec', 'list', '--json'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log.warning(f"[signalpilot_ai] Could not list kernel specs: {result.stderr}")
            return

        specs = json.loads(result.stdout)

        for name, info in specs.get('kernelspecs', {}).items():
            kernel_json_path = Path(info['resource_dir']) / 'kernel.json'

            if not kernel_json_path.exists():
                continue

            try:
                with open(kernel_json_path, 'r') as f:
                    kernel_json = json.load(f)

                # Get or create env dict
                if 'env' not in kernel_json:
                    kernel_json['env'] = {}

                # Check if env vars are already set (compare a sample key)
                sample_key = list(db_env_vars.keys())[0] if db_env_vars else None
                if sample_key and kernel_json['env'].get(sample_key) == db_env_vars.get(sample_key):
                    log.info(f"[signalpilot_ai] Kernel '{name}' env vars already up to date")
                    continue

                # Add database env vars
                kernel_json['env'].update(db_env_vars)

                # Try to write back
                try:
                    with open(kernel_json_path, 'w') as f:
                        json.dump(kernel_json, f, indent=2)
                    log.info(f"[signalpilot_ai] Updated kernel '{name}' with database env vars")

                except PermissionError:
                    log.warning(
                        f"[signalpilot_ai] No permission to modify kernel '{name}'. "
                        "Database env vars will be set at runtime instead."
                    )

            except Exception as e:
                log.warning(f"[signalpilot_ai] Could not configure kernel '{name}': {e}")

    except Exception as e:
        log.warning(f"[signalpilot_ai] Error configuring kernel env vars: {e}")


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "signalpilot-ai"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "signalpilot_ai"
    }]


def _load_jupyter_server_extension(server_app):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    setup_handlers(server_app.web_app)
    name = "signalpilot_ai"
    server_app.log.info(f"Registered {name} server extension")

    # Hook into kernel manager to inject database env vars at kernel start
    _setup_kernel_env_injection(server_app)
