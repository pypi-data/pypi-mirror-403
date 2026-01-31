"""
Image management commands for Conserver CLI.
"""

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from conserver.console import console, print_error, print_success, print_warning
from conserver.docker_ops import DockerOps
from conserver.exceptions import ConserverError, ImageError
from conserver.image_registry import ImageRegistry

# Create images subcommand app
app = typer.Typer(help="Container image management commands")

# Default registry
DEFAULT_REGISTRY = "public.ecr.aws/r4g1k2s3/vcon-dev/vcon-server"


@app.command("list")
def list_images(
    remote: bool = typer.Option(
        False, "--remote", "-r", help="List available tags from remote registry"
    ),
    limit: int = typer.Option(20, "--limit", help="Maximum number of tags to show"),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
) -> None:
    """List available vcon-server images."""
    try:
        image_registry = ImageRegistry(registry)

        if remote:
            console.print(f"[bold]Fetching tags from {registry}...[/bold]\n")
            tags = image_registry.list_tags(limit=limit)

            if not tags:
                print_warning("No tags found in registry")
                return

            table = Table(title="Available Tags")
            table.add_column("Tag", style="cyan")
            table.add_column("Type", style="dim")

            for tag in tags:
                if tag.is_version_tag:
                    tag_type = "version"
                elif tag.is_branch_tag:
                    tag_type = "branch"
                else:
                    tag_type = "other"
                table.add_row(tag.tag, tag_type)

            console.print(table)
            console.print(f"\n[dim]Showing {len(tags)} of available tags[/dim]")

        else:
            # List local images
            images = image_registry.get_local_images()

            if not images:
                print_warning("No local images found")
                console.print(
                    "[dim]Use 'conserver images pull <tag>' to download an image[/dim]"
                )
                return

            table = Table(title="Local Images")
            table.add_column("Tag", style="cyan")
            table.add_column("Image ID", style="dim")
            table.add_column("Created", style="dim")
            table.add_column("Size", style="green")

            for image in images:
                table.add_row(
                    image.tag,
                    image.image_id[:12],
                    image.created,
                    image.size,
                )

            console.print(table)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("pull")
def pull_image(
    tag: str = typer.Argument("main", help="Image tag to pull (e.g., 'main', 'v1.0.0')"),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
) -> None:
    """Pull a vcon-server image from the registry."""
    try:
        image_registry = ImageRegistry(registry)

        console.print(f"[bold]Pulling image with tag '{tag}'...[/bold]\n")

        if image_registry.pull_image(tag):
            print_success(f"Successfully pulled {registry}:{tag}")
        else:
            print_error(f"Failed to pull {registry}:{tag}")
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("use")
def use_image(
    tag: str = typer.Argument(..., help="Image tag to use (e.g., 'main', 'v1.0.0')"),
    pull: bool = typer.Option(
        True, "--pull/--no-pull", help="Pull the image if not available locally"
    ),
    restart: bool = typer.Option(
        False, "--restart", "-r", help="Restart containers after switching"
    ),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Switch to a specific vcon-server image version."""
    try:
        image_registry = ImageRegistry(registry)

        # Check if image exists locally
        if not image_registry.image_exists_locally(tag):
            if pull:
                console.print(f"[yellow]Image '{tag}' not found locally, pulling...[/yellow]\n")
                if not image_registry.pull_image(tag):
                    print_error(f"Failed to pull {registry}:{tag}")
                    raise typer.Exit(1)
            else:
                print_error(f"Image '{tag}' not found locally. Use --pull to download it.")
                raise typer.Exit(1)

        # Update docker-compose.yml or .env to use the new tag
        docker = DockerOps(server_path)

        # Check if containers are running
        was_running = docker.is_running()

        if was_running and restart:
            console.print("[yellow]Stopping containers...[/yellow]")
            docker.stop()

        # Update the IMAGE_TAG in .env file
        env_path = docker.project.env_path
        if env_path.exists():
            env_content = env_path.read_text()
            lines = env_content.split("\n")
            updated = False

            new_lines = []
            for line in lines:
                if line.startswith("IMAGE_TAG=") or line.startswith("VCON_SERVER_TAG="):
                    new_lines.append(f"VCON_SERVER_TAG={tag}")
                    updated = True
                elif line.startswith("VCON_SERVER_IMAGE="):
                    new_lines.append(f"VCON_SERVER_IMAGE={registry}")
                    updated = True
                else:
                    new_lines.append(line)

            if not updated:
                # Add the variables if they don't exist
                new_lines.append(f"VCON_SERVER_IMAGE={registry}")
                new_lines.append(f"VCON_SERVER_TAG={tag}")

            env_path.write_text("\n".join(new_lines))
            print_success(f"Updated .env to use {registry}:{tag}")
        else:
            # Create .env file with the image settings
            env_path.write_text(
                f"VCON_SERVER_IMAGE={registry}\nVCON_SERVER_TAG={tag}\n"
            )
            print_success(f"Created .env with {registry}:{tag}")

        if was_running and restart:
            console.print("[yellow]Starting containers with new image...[/yellow]")
            docker.start()
            print_success("Containers restarted with new image")
        elif was_running:
            console.print(
                "\n[yellow]Note: Containers are still running with the old image.[/yellow]"
            )
            console.print("[dim]Run 'conserver restart' to apply the change.[/dim]")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("upgrade")
def upgrade_image(
    to_tag: Optional[str] = typer.Argument(
        None, help="Specific version to upgrade to (defaults to latest)"
    ),
    restart: bool = typer.Option(
        True, "--restart/--no-restart", help="Restart containers after upgrade"
    ),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Upgrade to a newer vcon-server image version."""
    try:
        image_registry = ImageRegistry(registry)

        # Get current version
        current_tag = image_registry.get_current_tag()
        if current_tag:
            console.print(f"[bold]Current version:[/bold] {current_tag}")
        else:
            console.print("[dim]No current version detected[/dim]")

        # Determine target version
        if to_tag:
            target_tag = to_tag
        else:
            # Find latest version tag
            console.print("[dim]Fetching available versions...[/dim]")
            tags = image_registry.list_tags(limit=50)
            version_tags = [t for t in tags if t.is_version_tag]

            if version_tags:
                target_tag = version_tags[0].tag  # Already sorted, first is latest
                console.print(f"[bold]Latest version:[/bold] {target_tag}")
            else:
                # Fall back to main
                target_tag = "main"
                console.print("[yellow]No version tags found, using 'main'[/yellow]")

        # Check if upgrade is needed
        if current_tag == target_tag:
            console.print(f"[green]Already at {target_tag}[/green]")
            return

        # Check version comparison for version tags
        if current_tag and image_registry.compare_versions(current_tag, target_tag) >= 0:
            if current_tag != target_tag:
                print_warning(
                    f"Target version {target_tag} is not newer than current {current_tag}"
                )
                console.print("[dim]Use 'conserver images downgrade' to switch to an older version[/dim]")
                return

        console.print(f"\n[bold]Upgrading to {target_tag}...[/bold]")

        # Pull new image
        if not image_registry.pull_image(target_tag):
            print_error(f"Failed to pull {target_tag}")
            raise typer.Exit(1)

        # Use the new image
        docker = DockerOps(server_path)

        # Update .env
        env_path = docker.project.env_path
        env_content = env_path.read_text() if env_path.exists() else ""
        lines = env_content.split("\n") if env_content else []

        new_lines = []
        tag_updated = False
        image_updated = False

        for line in lines:
            if line.startswith("VCON_SERVER_TAG=") or line.startswith("IMAGE_TAG="):
                new_lines.append(f"VCON_SERVER_TAG={target_tag}")
                tag_updated = True
            elif line.startswith("VCON_SERVER_IMAGE="):
                new_lines.append(f"VCON_SERVER_IMAGE={registry}")
                image_updated = True
            else:
                new_lines.append(line)

        if not tag_updated:
            new_lines.append(f"VCON_SERVER_TAG={target_tag}")
        if not image_updated:
            new_lines.append(f"VCON_SERVER_IMAGE={registry}")

        env_path.write_text("\n".join(new_lines))

        if restart and docker.is_running():
            console.print("[yellow]Restarting containers...[/yellow]")
            docker.stop()
            docker.start()

        print_success(f"Upgraded to {target_tag}")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("downgrade")
def downgrade_image(
    to_tag: str = typer.Argument(..., help="Version to downgrade to"),
    restart: bool = typer.Option(
        True, "--restart/--no-restart", help="Restart containers after downgrade"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Skip confirmation prompt"
    ),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
    server_path: Optional[Path] = typer.Option(
        None, "--server-path", help="Path to vcon-server installation"
    ),
) -> None:
    """Downgrade to an older vcon-server image version."""
    try:
        image_registry = ImageRegistry(registry)

        # Get current version
        current_tag = image_registry.get_current_tag()
        if current_tag:
            console.print(f"[bold]Current version:[/bold] {current_tag}")

            # Warn if downgrading
            if image_registry.compare_versions(to_tag, current_tag) >= 0:
                print_warning(f"{to_tag} is not older than {current_tag}")
                console.print("[dim]Use 'conserver images upgrade' to switch to a newer version[/dim]")

        if not force:
            console.print(
                f"\n[yellow]Warning: Downgrading may cause compatibility issues.[/yellow]"
            )
            if not typer.confirm(f"Downgrade to {to_tag}?"):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        console.print(f"\n[bold]Downgrading to {to_tag}...[/bold]")

        # Pull the image
        if not image_registry.image_exists_locally(to_tag):
            if not image_registry.pull_image(to_tag):
                print_error(f"Failed to pull {to_tag}")
                raise typer.Exit(1)

        # Update .env
        docker = DockerOps(server_path)
        env_path = docker.project.env_path
        env_content = env_path.read_text() if env_path.exists() else ""
        lines = env_content.split("\n") if env_content else []

        new_lines = []
        tag_updated = False
        image_updated = False

        for line in lines:
            if line.startswith("VCON_SERVER_TAG=") or line.startswith("IMAGE_TAG="):
                new_lines.append(f"VCON_SERVER_TAG={to_tag}")
                tag_updated = True
            elif line.startswith("VCON_SERVER_IMAGE="):
                new_lines.append(f"VCON_SERVER_IMAGE={registry}")
                image_updated = True
            else:
                new_lines.append(line)

        if not tag_updated:
            new_lines.append(f"VCON_SERVER_TAG={to_tag}")
        if not image_updated:
            new_lines.append(f"VCON_SERVER_IMAGE={registry}")

        env_path.write_text("\n".join(new_lines))

        if restart and docker.is_running():
            console.print("[yellow]Restarting containers...[/yellow]")
            docker.stop()
            docker.start()

        print_success(f"Downgraded to {to_tag}")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("remove")
def remove_image(
    tag: str = typer.Argument(..., help="Image tag to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal"),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
) -> None:
    """Remove a local vcon-server image."""
    try:
        image_registry = ImageRegistry(registry)

        if not image_registry.image_exists_locally(tag):
            print_warning(f"Image '{tag}' not found locally")
            return

        console.print(f"[bold]Removing {registry}:{tag}...[/bold]")

        if image_registry.remove_image(tag, force=force):
            print_success(f"Removed {tag}")
        else:
            print_error(f"Failed to remove {tag}")
            console.print("[dim]The image may be in use by a container[/dim]")
            raise typer.Exit(1)

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("info")
def image_info(
    tag: str = typer.Argument("main", help="Image tag to inspect"),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
) -> None:
    """Show detailed information about an image."""
    try:
        image_registry = ImageRegistry(registry)

        image_name = f"{registry}:{tag}"

        # Check if image exists locally
        if not image_registry.image_exists_locally(tag):
            print_warning(f"Image '{tag}' not found locally")
            console.print(f"[dim]Run 'conserver images pull {tag}' to download it[/dim]")
            return

        # Get image details using docker inspect
        import json
        import subprocess

        result = subprocess.run(
            ["docker", "inspect", image_name],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print_error(f"Failed to inspect image: {result.stderr}")
            raise typer.Exit(1)

        data = json.loads(result.stdout)[0]

        console.print(f"\n[bold]Image:[/bold] {image_name}")
        console.print(f"[bold]ID:[/bold] {data.get('Id', 'N/A')[:19]}")
        console.print(f"[bold]Created:[/bold] {data.get('Created', 'N/A')}")

        # Size
        size_bytes = data.get("Size", 0)
        size_mb = size_bytes / (1024 * 1024)
        console.print(f"[bold]Size:[/bold] {size_mb:.1f} MB")

        # Architecture
        console.print(f"[bold]Architecture:[/bold] {data.get('Architecture', 'N/A')}")
        console.print(f"[bold]OS:[/bold] {data.get('Os', 'N/A')}")

        # Labels
        labels = data.get("Config", {}).get("Labels", {})
        if labels:
            console.print("\n[bold]Labels:[/bold]")
            for key, value in labels.items():
                console.print(f"  {key}: {value}")

        # Digest
        digests = data.get("RepoDigests", [])
        if digests:
            console.print(f"\n[bold]Digest:[/bold] {digests[0]}")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)


@app.command("prune")
def prune_images(
    keep: int = typer.Option(3, "--keep", "-k", help="Number of recent images to keep"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    registry: str = typer.Option(
        DEFAULT_REGISTRY, "--registry", help="Container registry URL"
    ),
) -> None:
    """Remove old local images, keeping only the most recent ones."""
    try:
        image_registry = ImageRegistry(registry)
        images = image_registry.get_local_images()

        if len(images) <= keep:
            console.print(f"[green]Only {len(images)} images found, nothing to prune[/green]")
            return

        # Images to remove (oldest first, skip the most recent 'keep' images)
        to_remove = images[keep:]

        console.print(f"[bold]Found {len(images)} local images[/bold]")
        console.print(f"[yellow]Will remove {len(to_remove)} images, keeping {keep} most recent[/yellow]")

        if not force:
            console.print("\n[bold]Images to remove:[/bold]")
            for img in to_remove:
                console.print(f"  - {img.tag} ({img.size})")

            if not typer.confirm("\nProceed with removal?"):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        removed = 0
        for img in to_remove:
            if image_registry.remove_image(img.tag):
                console.print(f"[green]Removed {img.tag}[/green]")
                removed += 1
            else:
                console.print(f"[yellow]Could not remove {img.tag}[/yellow]")

        print_success(f"Removed {removed} images")

    except ConserverError as e:
        print_error(e.message)
        raise typer.Exit(e.exit_code)
