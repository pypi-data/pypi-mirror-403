"""
Restart command for Conserver CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from conserver.console import console, print_error, print_success
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError


def restart(
    services: Optional[str] = typer.Option(
        None, "--services", help="Specific services to restart (comma-separated)"
    ),
    timeout: int = typer.Option(30, "--timeout", help="Timeout for graceful shutdown"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Restart vcon-server containers."""
    try:
        docker = DockerOps(server_path)

        service_list = services.split(",") if services else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            if service_list:
                progress.add_task(
                    f"Restarting services: {', '.join(service_list)}...", total=None
                )
            else:
                progress.add_task("Restarting all services...", total=None)

            success = docker.restart(
                services=service_list,
                timeout=timeout,
            )

        if success:
            print_success("Services restarted successfully")

            # Show current status
            containers = docker.get_status()
            if containers:
                console.print("\n[bold]Current status:[/bold]")
                for c in containers:
                    status_color = "green" if "running" in c.status.lower() else "red"
                    console.print(f"  {c.service}: [{status_color}]{c.status}[/{status_color}]")
        else:
            print_error("Failed to restart services")
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
