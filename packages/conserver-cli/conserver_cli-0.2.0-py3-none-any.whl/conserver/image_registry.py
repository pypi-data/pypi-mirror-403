"""
Image registry operations for Conserver CLI.

Handles listing, pulling, and managing vcon-server images from ECR.
"""

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx

from conserver.console import console
from conserver.exceptions import ImageError


@dataclass
class ImageTag:
    """Information about an image tag."""

    tag: str
    digest: Optional[str] = None
    pushed_at: Optional[datetime] = None
    size_bytes: Optional[int] = None

    @property
    def size_mb(self) -> Optional[float]:
        """Get size in MB."""
        if self.size_bytes:
            return self.size_bytes / (1024 * 1024)
        return None

    @property
    def is_version_tag(self) -> bool:
        """Check if this is a semver version tag."""
        return bool(re.match(r"^v?\d+\.\d+\.\d+", self.tag))

    @property
    def is_branch_tag(self) -> bool:
        """Check if this is a branch tag (main, dev, etc)."""
        return self.tag in ("main", "latest", "dev", "develop", "staging")


@dataclass
class LocalImage:
    """Information about a locally pulled image."""

    repository: str
    tag: str
    image_id: str
    created: str
    size: str

    @property
    def full_name(self) -> str:
        """Get full image name with tag."""
        return f"{self.repository}:{self.tag}"


class ImageRegistry:
    """Handle vcon-server image registry operations."""

    # Default ECR registry for vcon-server
    DEFAULT_REGISTRY = "public.ecr.aws/r4g1k2s3/vcon-dev/vcon-server"

    def __init__(self, registry: Optional[str] = None) -> None:
        """
        Initialize image registry handler.

        Args:
            registry: Custom registry URL (defaults to ECR)
        """
        self.registry = registry or self.DEFAULT_REGISTRY
        self._parse_registry()

    def _parse_registry(self) -> None:
        """Parse registry URL into components."""
        # Handle different registry formats
        # public.ecr.aws/r4g1k2s3/vcon-dev/vcon-server
        # ghcr.io/vcon-dev/vcon-server
        # docker.io/library/image

        self.registry_host = self.registry.split("/")[0]
        self.repository_path = "/".join(self.registry.split("/")[1:])

        # Determine registry type
        if "ecr.aws" in self.registry_host:
            self.registry_type = "ecr"
        elif "ghcr.io" in self.registry_host:
            self.registry_type = "ghcr"
        elif "docker.io" in self.registry_host:
            self.registry_type = "dockerhub"
        else:
            self.registry_type = "unknown"

    def list_tags(self, limit: int = 50) -> list[ImageTag]:
        """
        List available image tags from the registry.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List of ImageTag objects
        """
        if self.registry_type == "ecr":
            return self._list_ecr_tags(limit)
        elif self.registry_type == "ghcr":
            return self._list_ghcr_tags(limit)
        else:
            # Fallback: use docker CLI to inspect
            return self._list_tags_via_docker(limit)

    def _list_ecr_tags(self, limit: int) -> list[ImageTag]:
        """List tags from AWS ECR Public."""
        # ECR Public has a public API
        # https://public.ecr.aws/v2/<repository>/tags/list
        try:
            # First get auth token for public ECR
            # Note: ECR public requires trailing slash and follows redirects
            auth_url = "https://public.ecr.aws/token/"
            params = {
                "service": "public.ecr.aws",
                "scope": f"repository:{self.repository_path}:pull",
            }

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                # Get token
                auth_response = client.get(auth_url, params=params)
                if auth_response.status_code != 200:
                    console.print(
                        f"[yellow]Warning: Could not authenticate with ECR (status {auth_response.status_code})[/yellow]"
                    )
                    return self._list_tags_via_docker(limit)

                token = auth_response.json().get("token", "")

                # List tags
                tags_url = f"https://public.ecr.aws/v2/{self.repository_path}/tags/list"
                headers = {"Authorization": f"Bearer {token}"}

                response = client.get(tags_url, headers=headers)
                if response.status_code != 200:
                    console.print(
                        f"[yellow]Warning: Could not list tags from ECR[/yellow]"
                    )
                    return self._list_tags_via_docker(limit)

                data = response.json()
                tags = data.get("tags", [])

                # Sort tags: versions first (descending), then branches
                def sort_key(tag: str) -> tuple[int, str]:
                    if re.match(r"^v?\d+\.\d+\.\d+", tag):
                        # Version tags - extract version for sorting
                        version = tag.lstrip("v")
                        parts = version.split(".")
                        try:
                            return (0, f"{int(parts[0]):05d}.{int(parts[1]):05d}.{int(parts[2].split('-')[0]):05d}")
                        except (ValueError, IndexError):
                            return (0, version)
                    elif tag in ("main", "latest"):
                        return (1, tag)
                    else:
                        return (2, tag)

                tags = sorted(tags, key=sort_key, reverse=True)[:limit]

                return [ImageTag(tag=tag) for tag in tags]

        except Exception as e:
            console.print(f"[yellow]Warning: ECR API error: {e}[/yellow]")
            return self._list_tags_via_docker(limit)

    def _list_ghcr_tags(self, limit: int) -> list[ImageTag]:
        """List tags from GitHub Container Registry."""
        try:
            # GHCR uses the standard OCI distribution API
            with httpx.Client(timeout=30.0) as client:
                # Get token
                auth_url = f"https://ghcr.io/token?scope=repository:{self.repository_path}:pull"
                auth_response = client.get(auth_url)
                if auth_response.status_code != 200:
                    return self._list_tags_via_docker(limit)

                token = auth_response.json().get("token", "")

                # List tags
                tags_url = f"https://ghcr.io/v2/{self.repository_path}/tags/list"
                headers = {"Authorization": f"Bearer {token}"}

                response = client.get(tags_url, headers=headers)
                if response.status_code != 200:
                    return self._list_tags_via_docker(limit)

                data = response.json()
                tags = data.get("tags", [])[:limit]

                return [ImageTag(tag=tag) for tag in tags]

        except Exception:
            return self._list_tags_via_docker(limit)

    def _list_tags_via_docker(self, limit: int) -> list[ImageTag]:
        """Fallback: list tags using docker CLI (requires image to be pulled)."""
        # This only shows locally available tags
        try:
            result = subprocess.run(
                [
                    "docker",
                    "images",
                    "--format",
                    "{{.Tag}}",
                    self.registry,
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
                return [ImageTag(tag=tag) for tag in tags[:limit]]
        except Exception:
            pass

        return []

    def get_local_images(self) -> list[LocalImage]:
        """Get locally pulled images for this registry."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "images",
                    "--format",
                    "{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}",
                    "--filter",
                    f"reference={self.registry}*",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return []

            images = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 5:
                    images.append(
                        LocalImage(
                            repository=parts[0],
                            tag=parts[1],
                            image_id=parts[2],
                            created=parts[3],
                            size=parts[4],
                        )
                    )

            return images

        except Exception:
            return []

    def get_current_tag(self) -> Optional[str]:
        """Get the currently used tag (if any image is pulled)."""
        images = self.get_local_images()
        if images:
            # Return the most recently created one
            return images[0].tag
        return None

    def pull_image(self, tag: str = "main") -> bool:
        """
        Pull an image with the specified tag.

        Args:
            tag: Image tag to pull

        Returns:
            True if successful
        """
        image_name = f"{self.registry}:{tag}"
        console.print(f"[bold]Pulling {image_name}...[/bold]")

        try:
            result = subprocess.run(
                ["docker", "pull", image_name],
                capture_output=False,  # Show progress
            )
            return result.returncode == 0
        except Exception as e:
            raise ImageError(f"Failed to pull image: {e}")

    def tag_image(self, source_tag: str, target_tag: str) -> bool:
        """
        Tag an image locally.

        Args:
            source_tag: Source tag
            target_tag: Target tag

        Returns:
            True if successful
        """
        source = f"{self.registry}:{source_tag}"
        target = f"{self.registry}:{target_tag}"

        try:
            result = subprocess.run(
                ["docker", "tag", source, target],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False

    def remove_image(self, tag: str, force: bool = False) -> bool:
        """
        Remove a local image.

        Args:
            tag: Image tag to remove
            force: Force removal

        Returns:
            True if successful
        """
        image_name = f"{self.registry}:{tag}"

        try:
            command = ["docker", "rmi"]
            if force:
                command.append("-f")
            command.append(image_name)

            result = subprocess.run(command, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def image_exists_locally(self, tag: str) -> bool:
        """Check if an image with the given tag exists locally."""
        images = self.get_local_images()
        return any(img.tag == tag for img in images)

    def get_image_digest(self, tag: str) -> Optional[str]:
        """Get the digest of a local image."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{.Id}}",
                    f"{self.registry}:{tag}",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    def compare_versions(self, tag1: str, tag2: str) -> int:
        """
        Compare two version tags.

        Args:
            tag1: First tag
            tag2: Second tag

        Returns:
            -1 if tag1 < tag2, 0 if equal, 1 if tag1 > tag2
        """
        def parse_version(tag: str) -> tuple[int, ...]:
            """Parse version tag into tuple of integers."""
            version = tag.lstrip("v")
            # Handle pre-release suffixes
            version = version.split("-")[0]
            parts = version.split(".")
            try:
                return tuple(int(p) for p in parts)
            except ValueError:
                return (0, 0, 0)

        v1 = parse_version(tag1)
        v2 = parse_version(tag2)

        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
        return 0
