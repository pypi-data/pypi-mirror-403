"""
Status command for Conserver CLI.
"""

import json
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.live import Live
from rich.table import Table

from conserver.console import console, format_health, format_status, print_error
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError
from conserver.health import HealthChecker


class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"


def status(
    output_format: OutputFormat = typer.Option(
        OutputFormat.TABLE, "--format", help="Output format"
    ),
    all_containers: bool = typer.Option(
        False, "--all", "-a", help="Show all containers including stopped"
    ),
    health: bool = typer.Option(False, "--health", "-H", help="Include detailed health info"),
    watch: bool = typer.Option(False, "--watch", "-w", help="Continuously watch status"),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Show status of vcon-server containers."""
    try:
        docker = DockerOps(server_path)

        if watch:
            _watch_status(docker, all_containers, health)
        else:
            _show_status(docker, output_format, all_containers, health)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


def _show_status(
    docker: DockerOps,
    format: OutputFormat,
    all_containers: bool,
    include_health: bool,
) -> None:
    """Show status once."""
    containers = docker.get_status(all_containers)

    if not containers:
        console.print("[dim]No containers found[/dim]")
        return

    if format == OutputFormat.TABLE:
        _print_table(containers, include_health, docker)
    elif format == OutputFormat.JSON:
        _print_json(containers, include_health, docker)
    elif format == OutputFormat.YAML:
        _print_yaml(containers, include_health, docker)


def _print_table(containers: list, include_health: bool, docker: DockerOps) -> None:
    """Print status as a table."""
    table = Table(title="vcon-server Status", show_header=True, header_style="bold")

    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Health")
    table.add_column("Ports")

    for c in containers:
        table.add_row(
            c.service,
            format_status(c.status),
            format_health(c.health),
            str(c.ports) if c.ports else "-",
        )

    console.print(table)

    # Additional health info
    if include_health:
        console.print()
        health_checker = HealthChecker(docker)
        health = health_checker.check_all()

        if health.version:
            console.print(f"[bold]Version:[/bold] {health.version}")

        # Queue depths
        queue_depth = health_checker.get_queue_depth()
        dlq_depth = health_checker.get_dlq_depth()

        if queue_depth is not None:
            console.print(f"[bold]Queue depth:[/bold] {queue_depth}")
        if dlq_depth is not None:
            color = "red" if dlq_depth > 0 else "green"
            console.print(f"[bold]DLQ depth:[/bold] [{color}]{dlq_depth}[/{color}]")


def _print_json(containers: list, include_health: bool, docker: DockerOps) -> None:
    """Print status as JSON."""
    data = {
        "containers": [
            {
                "service": c.service,
                "name": c.name,
                "status": c.status,
                "health": c.health,
                "ports": c.ports,
                "image": c.image,
            }
            for c in containers
        ]
    }

    if include_health:
        health_checker = HealthChecker(docker)
        health = health_checker.check_all()
        data["health"] = {
            "overall": health.status.value,
            "version": health.version,
            "services": [
                {
                    "service": r.service,
                    "status": r.status.value,
                    "message": r.message,
                    "latency_ms": r.latency_ms,
                }
                for r in health.services
            ],
        }
        data["queues"] = {
            "default": health_checker.get_queue_depth(),
            "dlq": health_checker.get_dlq_depth(),
        }

    console.print(json.dumps(data, indent=2))


def _print_yaml(containers: list, include_health: bool, docker: DockerOps) -> None:
    """Print status as YAML."""
    data = {
        "containers": [
            {
                "service": c.service,
                "name": c.name,
                "status": c.status,
                "health": c.health,
                "ports": c.ports,
                "image": c.image,
            }
            for c in containers
        ]
    }

    if include_health:
        health_checker = HealthChecker(docker)
        health = health_checker.check_all()
        data["health"] = {
            "overall": health.status.value,
            "version": health.version,
            "services": [
                {
                    "service": r.service,
                    "status": r.status.value,
                    "message": r.message,
                    "latency_ms": r.latency_ms,
                }
                for r in health.services
            ],
        }

    console.print(yaml.dump(data, default_flow_style=False))


def _watch_status(docker: DockerOps, all_containers: bool, include_health: bool) -> None:
    """Watch status continuously."""

    def generate_table() -> Table:
        table = Table(title="vcon-server Status (Press Ctrl+C to exit)", show_header=True)

        table.add_column("Service")
        table.add_column("Status")
        table.add_column("Health")
        table.add_column("Ports")

        containers = docker.get_status(all_containers)

        for c in containers:
            table.add_row(
                c.service,
                format_status(c.status),
                format_health(c.health),
                str(c.ports) if c.ports else "-",
            )

        return table

    try:
        with Live(generate_table(), refresh_per_second=0.5, console=console) as live:
            while True:
                time.sleep(2)
                live.update(generate_table())
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped watching[/dim]")
