"""
Stop command for Conserver CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from conserver.console import confirm, console, print_error, print_success
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError


def stop(
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove containers after stopping"),
    volumes: bool = typer.Option(
        False, "--volumes", "-v", help="Remove volumes when removing containers"
    ),
    timeout: int = typer.Option(30, "--timeout", help="Timeout for graceful shutdown"),
    services: Optional[str] = typer.Option(
        None, "--services", help="Specific services to stop (comma-separated)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Stop the vcon-server containers."""
    try:
        docker = DockerOps(server_path)

        # Check if anything is running
        if not docker.is_running():
            console.print("[dim]No containers are running[/dim]")
            return

        service_list = services.split(",") if services else None

        # Confirm if removing volumes
        if volumes and not force:
            if not confirm(
                "[yellow]This will remove all data volumes. Are you sure?[/yellow]",
                default=False,
            ):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            if remove:
                progress.add_task("Stopping and removing containers...", total=None)
                success = docker.down(
                    remove_volumes=volumes,
                    timeout=timeout,
                )
            else:
                progress.add_task("Stopping containers...", total=None)
                success = docker.stop(
                    services=service_list,
                    timeout=timeout,
                )

        if success:
            if remove:
                print_success("Containers stopped and removed")
                if volumes:
                    console.print("[dim]Volumes have been removed[/dim]")
            else:
                print_success("Containers stopped")
        else:
            print_error("Failed to stop containers")
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
