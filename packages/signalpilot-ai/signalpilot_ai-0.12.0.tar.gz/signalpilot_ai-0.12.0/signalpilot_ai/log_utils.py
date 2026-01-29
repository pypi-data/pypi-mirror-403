"""
Logging utilities for SignalPilot AI.
Provides controlled print function that respects SIGNALPILOT_DEBUG environment variable.
"""

import builtins
import os

# Debug mode controlled by environment variable
# Set SIGNALPILOT_DEBUG=1 to enable verbose logging (disabled by default)
_DEBUG = os.environ.get('SIGNALPILOT_DEBUG', '0').lower() not in ('0', 'false', 'no')

# Store the original print function
_original_print = builtins.print


def print(*args, **kwargs) -> None:
    """Conditionally print messages based on debug mode.

    Only prints when SIGNALPILOT_DEBUG environment variable is not set to 0/false/no.
    Error messages (containing 'ERROR') are always printed regardless of debug mode.
    """
    message = ' '.join(str(arg) for arg in args)
    # Always print errors, otherwise only print in debug mode
    if 'ERROR' in message or _DEBUG:
        _original_print(*args, **kwargs)


def is_debug_enabled() -> bool:
    """Check if debug mode is enabled."""
    return _DEBUG
