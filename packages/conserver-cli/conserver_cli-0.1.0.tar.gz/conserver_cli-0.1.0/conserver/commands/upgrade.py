"""
Upgrade command for Conserver CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from conserver.config_manager import ConfigManager
from conserver.console import confirm, console, print_error, print_info, print_success
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError
from conserver.health import HealthChecker


def upgrade(
    pull: bool = typer.Option(True, "--pull/--no-pull", help="Pull new images before upgrading"),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Backup configs before upgrading"
    ),
    build: bool = typer.Option(False, "--build", "-b", help="Rebuild images after pulling"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show what would be done without executing"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompts"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Upgrade vcon-server to the latest version."""
    try:
        docker = DockerOps(server_path)
        config_manager = ConfigManager(docker.server_path)
        health_checker = HealthChecker(docker)

        # Get current version
        current_version = None
        if docker.is_running():
            health = health_checker.check_all()
            current_version = health.version

        if current_version:
            console.print(f"[bold]Current version:[/bold] {current_version}")
        else:
            console.print("[dim]Current version: unknown (services not running)[/dim]")

        if dry_run:
            console.print("\n[bold yellow]Dry run mode - no changes will be made[/bold yellow]\n")
            console.print("Steps that would be performed:")
            console.print("  1. Backup configuration files")
            console.print("  2. Pull latest Docker images")
            if build:
                console.print("  3. Rebuild Docker images")
            console.print(f"  {'4' if build else '3'}. Stop current containers")
            console.print(f"  {'5' if build else '4'}. Start containers with new images")
            console.print(f"  {'6' if build else '5'}. Verify health")
            return

        # Confirm upgrade
        if not force:
            if not confirm("Proceed with upgrade?", default=True):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            # Backup configs
            if backup:
                task = progress.add_task("Backing up configuration files...", total=None)
                backup_path = config_manager.backup_configs()
                progress.remove_task(task)
                print_info(f"Configuration backed up to: {backup_path}")

            # Pull images
            if pull:
                task = progress.add_task("Pulling latest images...", total=None)
                if not docker.pull():
                    print_error("Failed to pull images")
                    raise typer.Exit(1)
                progress.remove_task(task)
                print_success("Images pulled successfully")

            # Build if requested
            if build:
                task = progress.add_task("Building images...", total=None)
                if not docker.build():
                    print_error("Failed to build images")
                    raise typer.Exit(1)
                progress.remove_task(task)
                print_success("Images built successfully")

            # Stop containers
            if docker.is_running():
                task = progress.add_task("Stopping containers...", total=None)
                if not docker.stop():
                    print_error("Failed to stop containers")
                    raise typer.Exit(1)
                progress.remove_task(task)

            # Start containers
            task = progress.add_task("Starting containers with new images...", total=None)
            if not docker.start(detach=True):
                print_error("Failed to start containers")
                raise typer.Exit(1)
            progress.remove_task(task)

        # Wait for health
        console.print("\n[dim]Waiting for services to be healthy...[/dim]")

        import time

        start_time = time.time()
        timeout = 60
        healthy = False

        while time.time() - start_time < timeout:
            health = health_checker.check_all()
            if health.is_healthy:
                healthy = True
                break
            time.sleep(2)

        if healthy:
            new_version = health.version
            print_success("Upgrade completed successfully")
            if new_version:
                console.print(f"[bold]New version:[/bold] {new_version}")
        else:
            console.print("[yellow]Warning: Services may not be fully healthy yet[/yellow]")
            console.print("Check status with: conserver status --health")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
