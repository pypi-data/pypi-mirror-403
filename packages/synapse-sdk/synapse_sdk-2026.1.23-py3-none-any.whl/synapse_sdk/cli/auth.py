"""CLI authentication utilities."""

from __future__ import annotations

from dataclasses import dataclass

import questionary
import typer
from rich.console import Console

from synapse_sdk.utils.auth import (
    CONFIG_FILE,
    DEFAULT_HOST,
    ENV_SYNAPSE_ACCESS_TOKEN,
    ENV_SYNAPSE_HOST,
    load_credentials,
)


@dataclass
class AuthConfig:
    """Authentication configuration."""

    host: str
    access_token: str


def load_credentials_file() -> dict[str, str]:
    """Load credentials from ~/.synapse/config.json file.

    Returns:
        Dict with SYNAPSE_HOST and SYNAPSE_ACCESS_TOKEN if found.
    """
    creds = load_credentials()
    credentials: dict[str, str] = {}
    if creds.host:
        credentials[ENV_SYNAPSE_HOST] = creds.host
    if creds.token:
        credentials[ENV_SYNAPSE_ACCESS_TOKEN] = creds.token
    return credentials


def get_auth_config(
    *,
    host: str | None = None,
    token: str | None = None,
    console: Console | None = None,
    interactive: bool = True,
) -> AuthConfig:
    """Get authentication configuration.

    Priority order:
    1. CLI options (--host, --token)
    2. Environment variables (SYNAPSE_HOST, SYNAPSE_ACCESS_TOKEN)
    3. Config file (~/.synapse/config.json)
    4. Interactive prompt (if interactive=True)

    Args:
        host: Host override from CLI.
        token: Token override from CLI.
        console: Rich console for output.
        interactive: Whether to prompt for missing values.

    Returns:
        AuthConfig with host and access_token.

    Raises:
        typer.Exit: If authentication cannot be resolved.
    """
    # Load from env/credentials file
    creds = load_credentials()

    # Resolve host (CLI > loaded > default)
    resolved_host = host or creds.host or DEFAULT_HOST

    # Resolve token (CLI > loaded)
    resolved_token = token or creds.token

    if not resolved_token and interactive:
        resolved_token = questionary.text(
            'Enter your Synapse access token:',
            validate=lambda x: len(x) > 0 or 'Token cannot be empty',
        ).ask()

        if not resolved_token:
            raise typer.Exit(1)

    if not resolved_token:
        raise typer.BadParameter(
            f'Not authenticated. Run `synapse login` or set {ENV_SYNAPSE_ACCESS_TOKEN} environment variable.'
        )

    return AuthConfig(host=resolved_host, access_token=resolved_token)


__all__ = [
    'AuthConfig',
    'get_auth_config',
    'load_credentials_file',
    'ENV_SYNAPSE_HOST',
    'ENV_SYNAPSE_ACCESS_TOKEN',
    'DEFAULT_HOST',
    'CONFIG_FILE',
]
