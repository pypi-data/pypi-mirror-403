"""Authentication utilities for SDK."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient

# Environment variable names
ENV_SYNAPSE_HOST = 'SYNAPSE_HOST'
ENV_SYNAPSE_ACCESS_TOKEN = 'SYNAPSE_ACCESS_TOKEN'

# Default host
DEFAULT_HOST = 'https://api.synapse.sh'

# Config file path
CONFIG_FILE = Path.home() / '.synapse' / 'config.json'


@dataclass
class Credentials:
    """Loaded credentials from environment or config.

    Attributes:
        host: API host URL (None if not found).
        token: Access token (None if not found).
    """

    host: str | None = None
    token: str | None = None


def load_credentials() -> Credentials:
    """Load credentials from environment or config file.

    Priority:
    1. Environment variables (SYNAPSE_HOST, SYNAPSE_ACCESS_TOKEN)
    2. Config file (~/.synapse/config.json)

    Returns:
        Credentials with host and token. Either may be None if not found.
    """
    host = os.environ.get(ENV_SYNAPSE_HOST)
    token = os.environ.get(ENV_SYNAPSE_ACCESS_TOKEN)

    # Fall back to config.json
    if not token and CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
            if not host:
                host = config.get('host')
            if not token:
                token = config.get('access_token')
        except (json.JSONDecodeError, OSError):
            pass

    return Credentials(host=host, token=token)


def create_backend_client() -> BackendClient | None:
    """Create a BackendClient from environment/credentials if available.

    Returns:
        BackendClient if credentials are available, None otherwise.
    """
    creds = load_credentials()
    user_token = os.environ.get('SYNAPSE_PLUGIN_RUN_USER_TOKEN')

    if not creds.token and not user_token:
        return None

    from synapse_sdk.clients.backend import BackendClient

    tenant = os.environ.get('SYNAPSE_PLUGIN_RUN_TENANT')

    if user_token:
        return BackendClient(
            base_url=creds.host or DEFAULT_HOST,
            authorization_token=user_token,
            tenant=tenant,
        )
    else:
        return BackendClient(
            base_url=creds.host or DEFAULT_HOST,
            access_token=creds.token,
        )


__all__ = [
    'ENV_SYNAPSE_HOST',
    'ENV_SYNAPSE_ACCESS_TOKEN',
    'DEFAULT_HOST',
    'CONFIG_FILE',
    'Credentials',
    'load_credentials',
    'create_backend_client',
]
