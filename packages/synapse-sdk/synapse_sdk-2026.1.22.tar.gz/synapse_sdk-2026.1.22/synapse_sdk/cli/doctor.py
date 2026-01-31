"""Synapse doctor - diagnostic command for configuration issues."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console
from rich.table import Table


@dataclass
class DiagnosticResult:
    """Result of a single diagnostic check.

    Attributes:
        name: Name of the check (e.g., 'Config file exists').
        status: Check result - 'ok', 'warning', or 'error'.
        message: Human-readable result message.
        details: Additional details about the result (optional).
        fix: Suggested fix command or action (optional).
    """

    name: str
    status: str  # 'ok', 'warning', 'error'
    message: str
    details: str | None = None
    fix: str | None = None


@dataclass
class DoctorReport:
    """Complete diagnostic report containing all check results.

    Attributes:
        results: List of DiagnosticResult from all checks.
    """

    results: list[DiagnosticResult] = field(default_factory=list)

    def add(self, result: DiagnosticResult) -> None:
        """Add a result to the report."""
        self.results.append(result)

    @property
    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return any(r.status == 'error' for r in self.results)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return any(r.status == 'warning' for r in self.results)


def check_config_file_exists(config_path: Path) -> DiagnosticResult:
    """Check if config file exists."""
    if config_path.exists():
        return DiagnosticResult(
            name='Config file exists',
            status='ok',
            message=f'Found at {config_path}',
        )
    return DiagnosticResult(
        name='Config file exists',
        status='error',
        message=f'Not found at {config_path}',
        fix='Run `synapse login` to create config file',
    )


def check_config_valid_json(config_path: Path) -> DiagnosticResult:
    """Check if config file is valid JSON."""
    if not config_path.exists():
        return DiagnosticResult(
            name='Config valid JSON',
            status='error',
            message='Config file does not exist',
        )

    try:
        content = config_path.read_text()
        json.loads(content)
        return DiagnosticResult(
            name='Config valid JSON',
            status='ok',
            message='Config file is valid JSON',
        )
    except json.JSONDecodeError as e:
        return DiagnosticResult(
            name='Config valid JSON',
            status='error',
            message=f'Invalid JSON: {e}',
            fix='Fix the JSON syntax in config file',
        )
    except OSError as e:
        return DiagnosticResult(
            name='Config valid JSON',
            status='error',
            message=f'Cannot read file: {e}',
        )


def check_cli_auth(config_path: Path) -> DiagnosticResult:
    """Check if CLI authentication is configured (host, access_token)."""
    if not config_path.exists():
        return DiagnosticResult(
            name='CLI authentication',
            status='error',
            message='Config file does not exist',
            fix='Run `synapse login` to authenticate',
        )

    try:
        config = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return DiagnosticResult(
            name='CLI authentication',
            status='error',
            message='Cannot parse config file',
        )

    host = config.get('host')
    token = config.get('access_token')

    missing = []
    if not host:
        missing.append('host')
    if not token:
        missing.append('access_token')

    if missing:
        return DiagnosticResult(
            name='CLI authentication',
            status='error',
            message=f'Missing fields: {", ".join(missing)}',
            details='CLI commands require `host` and `access_token` fields',
            fix='Run `synapse login` to configure authentication',
        )

    return DiagnosticResult(
        name='CLI authentication',
        status='ok',
        message=f'Configured for {host}',
        details=f'Token: {token[:12]}...' if len(token) > 12 else f'Token: {token}',
    )


def check_mcp_config(config_path: Path) -> DiagnosticResult:
    """Check if MCP configuration is complete (default_environment, environments)."""
    if not config_path.exists():
        return DiagnosticResult(
            name='MCP configuration',
            status='warning',
            message='Config file does not exist',
            fix='Run `synapse mcp init` to create MCP config',
        )

    try:
        config = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return DiagnosticResult(
            name='MCP configuration',
            status='error',
            message='Cannot parse config file',
        )

    default_env = config.get('default_environment')
    environments = config.get('environments')

    issues = []
    if not default_env:
        issues.append('missing `default_environment`')
    if not environments:
        issues.append('missing `environments`')
    elif not isinstance(environments, dict):
        issues.append('`environments` must be an object')
    elif default_env and default_env not in environments:
        issues.append(f'default_environment "{default_env}" not found in environments')

    if issues:
        return DiagnosticResult(
            name='MCP configuration',
            status='warning',
            message=f'Issues: {"; ".join(issues)}',
            details='MCP server requires `default_environment` and `environments` fields',
            fix='Run `synapse mcp init` to configure MCP, or add these fields manually',
        )

    # Check if environment has required fields
    env_issues = []
    for env_name, env_config in environments.items():
        if not env_config:
            env_issues.append(f'{env_name}: empty configuration')
            continue
        if not env_config.get('backend_url'):
            env_issues.append(f'{env_name}: missing backend_url')
        if not env_config.get('access_token'):
            env_issues.append(f'{env_name}: missing access_token')

    if env_issues:
        return DiagnosticResult(
            name='MCP configuration',
            status='warning',
            message=f'Environment issues: {"; ".join(env_issues)}',
            fix='Add backend_url and access_token to each environment',
        )

    return DiagnosticResult(
        name='MCP configuration',
        status='ok',
        message=f'Configured with {len(environments)} environment(s)',
        details=f'Default: {default_env}',
    )


def check_agent_config(config_path: Path) -> DiagnosticResult:
    """Check if agent is configured."""
    if not config_path.exists():
        return DiagnosticResult(
            name='Agent configuration',
            status='warning',
            message='Config file does not exist',
        )

    try:
        config = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return DiagnosticResult(
            name='Agent configuration',
            status='warning',
            message='Cannot parse config file',
        )

    agent = config.get('agent')
    if not agent:
        return DiagnosticResult(
            name='Agent configuration',
            status='warning',
            message='No agent configured',
            details='Some commands require an agent (e.g., `synapse plugin run --mode remote`)',
            fix='Run `synapse agent select` to configure an agent',
        )

    agent_id = agent.get('id')
    agent_name = agent.get('name', 'unnamed')
    agent_url = agent.get('url')

    if not agent_id:
        return DiagnosticResult(
            name='Agent configuration',
            status='warning',
            message='Agent missing ID',
            fix='Run `synapse agent select` to reconfigure',
        )

    return DiagnosticResult(
        name='Agent configuration',
        status='ok',
        message=f'Agent "{agent_name}" (ID: {agent_id})',
        details=f'URL: {agent_url}' if agent_url else 'No URL configured',
    )


def check_token_validity(config_path: Path, console: Console) -> DiagnosticResult:
    """Check if the access token is valid by making a test API call."""
    if not config_path.exists():
        return DiagnosticResult(
            name='Token validity',
            status='error',
            message='Config file does not exist',
        )

    try:
        config = json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return DiagnosticResult(
            name='Token validity',
            status='error',
            message='Cannot parse config file',
        )

    host = config.get('host')
    token = config.get('access_token')

    if not host or not token:
        return DiagnosticResult(
            name='Token validity',
            status='error',
            message='Missing host or access_token',
        )

    try:
        from synapse_sdk.clients.backend import BackendClient

        client = BackendClient(base_url=host, access_token=token)
        # Try to list agents - a simple endpoint to validate token
        client.list_agents()
        return DiagnosticResult(
            name='Token validity',
            status='ok',
            message='Token is valid',
            details=f'Successfully authenticated with {host}',
        )
    except Exception as e:
        error_msg = str(e)
        if '401' in error_msg or 'unauthorized' in error_msg.lower():
            return DiagnosticResult(
                name='Token validity',
                status='error',
                message='Token is invalid or expired',
                fix='Run `synapse login` to get a new token',
            )
        elif '403' in error_msg or 'forbidden' in error_msg.lower():
            return DiagnosticResult(
                name='Token validity',
                status='error',
                message='Token lacks required permissions',
                fix='Check your account permissions or get a new token',
            )
        else:
            return DiagnosticResult(
                name='Token validity',
                status='warning',
                message=f'Could not verify token: {error_msg}',
                details='This might be a network issue or server problem',
            )


def check_config_permissions(config_path: Path) -> DiagnosticResult:
    """Check if config file has secure permissions."""
    if not config_path.exists():
        return DiagnosticResult(
            name='Config permissions',
            status='warning',
            message='Config file does not exist',
        )

    try:
        mode = config_path.stat().st_mode
        # Check if file is readable by others (group or world)
        if mode & 0o077:  # Any permission for group or others
            return DiagnosticResult(
                name='Config permissions',
                status='warning',
                message='Config file may be readable by other users',
                details=f'Current permissions: {oct(mode)[-3:]}',
                fix=f'Run `chmod 600 {config_path}` to secure the file',
            )
        return DiagnosticResult(
            name='Config permissions',
            status='ok',
            message='Config file has secure permissions',
            details=f'Permissions: {oct(mode)[-3:]}',
        )
    except OSError as e:
        return DiagnosticResult(
            name='Config permissions',
            status='warning',
            message=f'Could not check permissions: {e}',
        )


def run_diagnostics(config_path: Path, console: Console) -> DoctorReport:
    """Run all diagnostic checks.

    Args:
        config_path: Path to config file.
        console: Rich console for output.

    Returns:
        DoctorReport with all results.
    """
    report = DoctorReport()

    # Basic config checks
    report.add(check_config_file_exists(config_path))
    report.add(check_config_valid_json(config_path))
    report.add(check_config_permissions(config_path))

    # Authentication checks
    report.add(check_cli_auth(config_path))
    report.add(check_mcp_config(config_path))
    report.add(check_agent_config(config_path))

    # Token validation
    report.add(check_token_validity(config_path, console))

    return report


def display_report(report: DoctorReport, console: Console) -> None:
    """Display the doctor report in a formatted table.

    Args:
        report: DoctorReport containing diagnostic results.
        console: Rich console for formatted output.
    """
    table = Table(show_header=True, header_style='bold')
    table.add_column('Check', style='cyan')
    table.add_column('Status')
    table.add_column('Message')

    status_icons = {
        'ok': '[green]\u2713[/green]',  # checkmark
        'warning': '[yellow]![/yellow]',
        'error': '[red]\u2717[/red]',  # X mark
    }

    for result in report.results:
        icon = status_icons.get(result.status, '?')
        table.add_row(
            result.name,
            icon,
            result.message,
        )

    console.print(table)

    # Show details and fixes for non-ok results
    issues = [r for r in report.results if r.status != 'ok']
    if issues:
        console.print()
        for result in issues:
            style = 'yellow' if result.status == 'warning' else 'red'
            console.print(f'[{style}]{result.name}[/{style}]')
            if result.details:
                console.print(f'  [dim]{result.details}[/dim]')
            if result.fix:
                console.print(f'  [bold]Fix:[/bold] {result.fix}')
            console.print()


__all__ = [
    'DiagnosticResult',
    'DoctorReport',
    'run_diagnostics',
    'display_report',
]
