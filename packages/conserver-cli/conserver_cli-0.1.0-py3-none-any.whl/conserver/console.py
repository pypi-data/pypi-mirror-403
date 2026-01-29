"""
Rich console output utilities for Conserver CLI.
"""

from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Global console instance
console = Console()
error_console = Console(stderr=True)


def print_error(message: str, hint: Optional[str] = None) -> None:
    """Print an error message with optional hint."""
    error_console.print(f"[bold red]Error:[/bold red] {message}")
    if hint:
        error_console.print(f"[dim]Hint:[/dim] {hint}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]Info:[/bold blue] {message}")


def print_status_table(
    title: str,
    rows: list[dict[str, Any]],
    columns: Optional[list[tuple[str, str]]] = None,
) -> None:
    """
    Print a status table.

    Args:
        title: Table title
        rows: List of row dictionaries
        columns: Optional list of (key, header) tuples. If None, uses row keys.
    """
    if not rows:
        console.print("[dim]No data to display[/dim]")
        return

    table = Table(title=title, show_header=True, header_style="bold")

    # Determine columns
    if columns is None:
        columns = [(k, k.replace("_", " ").title()) for k in rows[0].keys()]

    for key, header in columns:
        table.add_column(header)

    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key, "")
            # Apply status coloring
            if key == "status":
                value = format_status(str(value))
            elif key == "health":
                value = format_health(str(value))
            else:
                value = str(value)
            values.append(value)
        table.add_row(*values)

    console.print(table)


def format_status(status: str) -> str:
    """Format container status with color."""
    status_lower = status.lower()
    if "running" in status_lower:
        return f"[green]{status}[/green]"
    elif "exited" in status_lower or "stopped" in status_lower:
        return f"[red]{status}[/red]"
    elif "starting" in status_lower or "restarting" in status_lower:
        return f"[yellow]{status}[/yellow]"
    elif "paused" in status_lower:
        return f"[blue]{status}[/blue]"
    return status


def format_health(health: str) -> str:
    """Format health status with color."""
    health_lower = health.lower()
    if health_lower == "healthy":
        return "[green]healthy[/green]"
    elif health_lower == "unhealthy":
        return "[red]unhealthy[/red]"
    elif health_lower == "starting":
        return "[yellow]starting[/yellow]"
    elif health_lower in ("none", "-", "n/a"):
        return "[dim]-[/dim]"
    return health


def print_service_panel(
    service: str,
    status: str,
    health: str,
    details: Optional[dict[str, str]] = None,
) -> None:
    """Print a panel for a single service."""
    content = Text()
    content.append(f"Status: ", style="bold")
    content.append(format_status(status))
    content.append("\n")
    content.append("Health: ", style="bold")
    content.append(format_health(health))

    if details:
        for key, value in details.items():
            content.append(f"\n{key}: ", style="bold")
            content.append(str(value))

    panel = Panel(content, title=f"[bold]{service}[/bold]", border_style="blue")
    console.print(panel)


def print_config_value(key: str, value: Any, masked: bool = False) -> None:
    """Print a configuration key-value pair."""
    if masked and value:
        display_value = "****" + str(value)[-4:] if len(str(value)) > 4 else "****"
    else:
        display_value = str(value) if value else "[dim]<not set>[/dim]"

    console.print(f"[bold]{key}:[/bold] {display_value}")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for confirmation."""
    suffix = " [Y/n]" if default else " [y/N]"
    response = console.input(f"{message}{suffix} ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes")
