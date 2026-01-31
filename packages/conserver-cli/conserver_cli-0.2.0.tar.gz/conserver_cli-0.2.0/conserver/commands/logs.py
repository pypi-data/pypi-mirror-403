"""
Logs command for Conserver CLI.
"""

import re
import sys
from pathlib import Path
from typing import Optional

import typer

from conserver.console import console, print_error
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError


def logs(
    services: Optional[str] = typer.Argument(
        None, help="Services to show logs for (comma-separated, or 'all')"
    ),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
    tail: Optional[int] = typer.Option(100, "--tail", help="Number of lines from end"),
    since: Optional[str] = typer.Option(
        None, "--since", help="Show logs since timestamp (e.g., 2h, 30m, 2024-01-01)"
    ),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Show timestamps"),
    grep_pattern: Optional[str] = typer.Option(None, "--grep", help="Filter logs by pattern"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """View container logs."""
    try:
        docker = DockerOps(server_path)

        # Parse services
        service_list: Optional[list[str]] = None
        if services and services.lower() != "all":
            service_list = [s.strip() for s in services.split(",")]

        # Check if any containers are running
        if not docker.is_running():
            print_error("No containers are running")
            console.print("[dim]Start containers with: conserver start[/dim]")
            raise typer.Exit(1)

        # Compile grep pattern if provided
        compiled_pattern: Optional[re.Pattern[str]] = None
        if grep_pattern:
            try:
                compiled_pattern = re.compile(grep_pattern, re.IGNORECASE)
            except re.error as e:
                print_error(f"Invalid grep pattern: {e}")
                raise typer.Exit(1)

        # Get logs process
        process = docker.get_logs(
            services=service_list,
            follow=follow,
            tail=tail,
            since=since,
            timestamps=timestamps,
        )

        try:
            # Stream logs
            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break

                    # Apply grep filter
                    if compiled_pattern:
                        if not compiled_pattern.search(line):
                            continue
                        # Highlight matches
                        line = compiled_pattern.sub(
                            lambda m: f"[bold yellow]{m.group()}[/bold yellow]", line
                        )

                    # Color-code by service if multiple services
                    line = _colorize_log_line(line)
                    console.print(line, end="", markup=True, highlight=False)

        except KeyboardInterrupt:
            console.print("\n[dim]Stopped following logs[/dim]")
        finally:
            process.terminate()
            process.wait()

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


def _colorize_log_line(line: str) -> str:
    """Add color coding to log lines based on service name."""
    # Service colors
    colors = {
        "conserver": "cyan",
        "api": "green",
        "redis": "red",
        "postgres": "blue",
        "elasticsearch": "yellow",
    }

    # Try to detect service name in log line
    # Common format: "service-name-1  | log message"
    for service, color in colors.items():
        if line.lower().startswith(service) or f"| {service}" in line.lower():
            # Color the service prefix
            parts = line.split("|", 1)
            if len(parts) == 2:
                return f"[{color}]{parts[0]}[/{color}]|{parts[1]}"

    return line
