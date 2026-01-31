"""
Start command for Conserver CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from conserver.console import console, print_error, print_success
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError
from conserver.health import HealthChecker


def start(
    build: bool = typer.Option(False, "--build", "-b", help="Build images before starting"),
    detach: bool = typer.Option(True, "--detach/--no-detach", help="Run in detached mode"),
    services: Optional[str] = typer.Option(
        None, "--services", help="Specific services to start (comma-separated)"
    ),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Wait for services to be healthy"),
    timeout: int = typer.Option(60, "--timeout", help="Health check timeout in seconds"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Start the vcon-server containers."""
    try:
        docker = DockerOps(server_path)

        service_list = services.split(",") if services else None

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # Ensure network exists
            progress.add_task("Ensuring Docker network exists...", total=None)
            created = docker.ensure_network()
            if created:
                console.print("[green]Created Docker network 'conserver'[/green]")

            # Start containers
            if build:
                progress.add_task("Building images...", total=None)

            task = progress.add_task("Starting containers...", total=None)

            success = docker.start(
                services=service_list,
                build=build,
                detach=detach,
            )

            if not success:
                print_error("Failed to start containers")
                raise typer.Exit(1)

        if detach:
            print_success("Containers started successfully")

            # Wait for health if requested
            if wait:
                console.print("\n[dim]Waiting for services to be healthy...[/dim]")
                health_checker = HealthChecker(docker)

                import time

                start_time = time.time()
                healthy = False

                while time.time() - start_time < timeout:
                    health = health_checker.check_all(timeout=5.0)
                    if health.is_healthy:
                        healthy = True
                        break
                    time.sleep(2)

                if healthy:
                    console.print("[green]All services are healthy[/green]")

                    # Show status
                    containers = docker.get_status()
                    if containers:
                        console.print("\n[bold]Services:[/bold]")
                        for c in containers:
                            status_color = "green" if "running" in c.status.lower() else "red"
                            console.print(
                                f"  {c.service}: [{status_color}]{c.status}[/{status_color}]"
                            )
                else:
                    console.print(
                        "[yellow]Warning: Some services may not be fully healthy yet[/yellow]"
                    )

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
