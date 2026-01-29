"""
Main CLI entry point for Conserver.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from conserver import __app_name__, __version__
from conserver.commands import config as config_cmd
from conserver.commands.logs import logs
from conserver.commands.restart import restart
from conserver.commands.start import start
from conserver.commands.status import status
from conserver.commands.stop import stop
from conserver.commands.upgrade import upgrade
from conserver.console import console, print_error
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError
from conserver.health import HealthChecker, HealthStatus

# Create the main app
app = typer.Typer(
    name=__app_name__,
    help="CLI tool to manage vcon-server Docker containers",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Add config subcommand
app.add_typer(config_cmd.app, name="config")

# Add commands
app.command()(start)
app.command()(stop)
app.command()(status)
app.command()(restart)
app.command()(upgrade)
app.command()(logs)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"{__app_name__} version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """
    Conserver CLI - Manage vcon-server Docker containers.

    Use 'conserver <command> --help' for more information on a command.
    """
    pass


@app.command()
def health(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed health info"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Check health of all services."""
    try:
        docker = DockerOps(server_path)
        health_checker = HealthChecker(docker)

        console.print("[bold]Checking service health...[/bold]\n")

        health_result = health_checker.check_all()

        # Display results
        for service in health_result.services:
            if service.status == HealthStatus.HEALTHY:
                status_icon = "[green]OK[/green]"
            elif service.status == HealthStatus.DEGRADED:
                status_icon = "[yellow]WARN[/yellow]"
            else:
                status_icon = "[red]FAIL[/red]"

            latency = f" ({service.latency_ms:.0f}ms)" if service.latency_ms else ""
            console.print(f"  {service.service}: {status_icon} - {service.message}{latency}")

        console.print()

        # Overall status
        if health_result.is_healthy:
            console.print(
                Panel("[green]All services healthy[/green]", title="Status", border_style="green")
            )
        elif health_result.status == HealthStatus.DEGRADED:
            console.print(
                Panel(
                    f"[yellow]{health_result.healthy_count}/{health_result.total_count} services healthy[/yellow]",
                    title="Status",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel("[red]Services unhealthy[/red]", title="Status", border_style="red")
            )

        # Additional info
        if verbose:
            console.print()
            if health_result.version:
                console.print(f"[bold]Version:[/bold] {health_result.version}")

            queue_depth = health_checker.get_queue_depth()
            dlq_depth = health_checker.get_dlq_depth()

            if queue_depth is not None:
                console.print(f"[bold]Queue depth:[/bold] {queue_depth}")
            if dlq_depth is not None:
                color = "red" if dlq_depth > 0 else "green"
                console.print(f"[bold]DLQ depth:[/bold] [{color}]{dlq_depth}[/{color}]")

        # Exit with error if not healthy
        if not health_result.is_healthy:
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command()
def init(
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing configuration files"
    ),
) -> None:
    """Initialize vcon-server configuration (alias for 'config init')."""
    # Delegate to config init
    from conserver.commands.config import init as config_init

    config_init(overwrite=overwrite, force=False, server_path=server_path)


if __name__ == "__main__":
    app()
