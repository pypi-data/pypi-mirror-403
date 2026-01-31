"""
Configuration commands for Conserver CLI.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer
import yaml

from conserver.config_manager import ConfigManager
from conserver.console import (
    confirm,
    console,
    print_config_value,
    print_error,
    print_success,
    print_warning,
)
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError

# Create config subcommand app
app = typer.Typer(help="Configuration management commands")


class ConfigFileType(str, Enum):
    ENV = "env"
    CONFIG = "config"
    COMPOSE = "compose"


class OutputFormat(str, Enum):
    YAML = "yaml"
    JSON = "json"
    TABLE = "table"


@app.command("show")
def show(
    file: ConfigFileType = typer.Option(
        ConfigFileType.CONFIG, "--file", help="Which config file to show"
    ),
    secrets: bool = typer.Option(False, "--secrets", help="Show sensitive values unmasked"),
    output_format: OutputFormat = typer.Option(
        OutputFormat.YAML, "--format", help="Output format (for config/compose)"
    ),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Show current configuration."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)

        config_file = config_manager.get_config_file(file.value)

        if not config_file.exists:
            print_error(f"File not found: {config_file.path}")
            console.print(
                "[dim]Hint: Run 'conserver config init' to create from example[/dim]"
            )
            raise typer.Exit(1)

        console.print(f"[bold]File:[/bold] {config_file.path}\n")

        if file == ConfigFileType.ENV:
            _show_env(config_manager, secrets)
        else:
            _show_yaml(config_file.content, output_format, config_manager, secrets)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


def _show_env(config_manager: ConfigManager, show_secrets: bool) -> None:
    """Show environment variables."""
    env = config_manager.load_env()

    if not env:
        console.print("[dim]No environment variables set[/dim]")
        return

    for key, value in sorted(env.items()):
        masked = config_manager.is_key_sensitive(key) and not show_secrets
        print_config_value(key, value, masked=masked)


def _show_yaml(
    content: dict[str, Any],
    format: OutputFormat,
    config_manager: ConfigManager,
    show_secrets: bool,
) -> None:
    """Show YAML content."""
    if not show_secrets:
        content = _mask_sensitive_values(content, config_manager)

    if format == OutputFormat.JSON:
        console.print(json.dumps(content, indent=2))
    elif format == OutputFormat.YAML:
        console.print(yaml.dump(content, default_flow_style=False, sort_keys=False))
    else:
        # Table format - just show YAML for now
        console.print(yaml.dump(content, default_flow_style=False, sort_keys=False))


def _mask_sensitive_values(data: Any, config_manager: ConfigManager) -> Any:
    """Recursively mask sensitive values in a dictionary."""
    if isinstance(data, dict):
        return {
            k: (
                config_manager.mask_value(v)
                if config_manager.is_key_sensitive(k)
                else _mask_sensitive_values(v, config_manager)
            )
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [_mask_sensitive_values(item, config_manager) for item in data]
    return data


@app.command("edit")
def edit(
    file: ConfigFileType = typer.Option(
        ConfigFileType.CONFIG, "--file", help="Which config file to edit"
    ),
    editor: Optional[str] = typer.Option(None, "--editor", help="Editor to use"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Edit configuration file in your editor."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)

        config_file = config_manager.get_config_file(file.value)

        if not config_file.exists:
            print_error(f"File not found: {config_file.path}")
            console.print(
                "[dim]Hint: Run 'conserver config init' to create from example[/dim]"
            )
            raise typer.Exit(1)

        console.print(f"Opening {config_file.path}...")
        success = config_manager.edit_file(file.value, editor)

        if success:
            print_success("File edited")
        else:
            print_error("Editor exited with error")
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("set")
def set_value(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Value to set"),
    file: ConfigFileType = typer.Option(
        ConfigFileType.ENV,
        "--file",
        help="Which config file to modify (env or config)",
    ),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Set a configuration value."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)

        if file == ConfigFileType.COMPOSE:
            print_error("Cannot modify docker-compose.yml with set command")
            console.print("[dim]Use 'conserver config edit --file compose' instead[/dim]")
            raise typer.Exit(1)

        if file == ConfigFileType.ENV:
            config_manager.set_env_value(key, value)
            print_success(f"Set {key} in .env")
        else:
            # Parse value as YAML to handle types
            try:
                parsed_value = yaml.safe_load(value)
            except yaml.YAMLError:
                parsed_value = value

            config_manager.set_config_value(key, parsed_value)
            print_success(f"Set {key} in config.yml")

        console.print("[dim]Restart services for changes to take effect[/dim]")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("validate")
def validate(
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix simple validation issues"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Validate configuration files."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)

        console.print("[bold]Validating configuration files...[/bold]\n")

        errors = config_manager.validate()

        if not errors:
            print_success("All configuration files are valid")
            return

        # Group errors by severity
        error_errors = [e for e in errors if e.severity == "error"]
        warning_errors = [e for e in errors if e.severity == "warning"]

        if warning_errors:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for err in warning_errors:
                print_warning(f"{err.field}: {err.message}")
            console.print()

        if error_errors:
            console.print("[bold red]Errors:[/bold red]")
            for err in error_errors:
                print_error(f"{err.field}: {err.message}")

            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("init")
def init(
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing configuration files"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Initialize configuration files from examples."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)

        if overwrite and not force:
            if not confirm(
                "[yellow]This will overwrite existing configuration files. Continue?[/yellow]",
                default=False,
            ):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        console.print("[bold]Initializing configuration files...[/bold]\n")

        results = config_manager.init_from_examples(overwrite=overwrite)

        for name, created in results.items():
            if created:
                print_success(f"Created {name} configuration")
            else:
                console.print(f"[dim]Skipped {name} (already exists or no example)[/dim]")

        console.print("\n[dim]Edit configuration files with 'conserver config edit'[/dim]")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
