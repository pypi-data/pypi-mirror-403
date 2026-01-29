"""
Docker operations for Conserver CLI.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import docker
from docker.errors import DockerException, NotFound

from conserver.console import console
from conserver.exceptions import (
    ContainerError,
    DockerComposeNotFoundError,
    DockerNotRunningError,
    NetworkError,
    ServerNotFoundError,
    TimeoutError,
)


@dataclass
class ContainerInfo:
    """Container information."""

    name: str
    service: str
    status: str
    health: str
    ports: str
    image: str
    created: str


@dataclass
class ComposeProject:
    """Docker Compose project information."""

    path: Path
    compose_file: str = "docker-compose.yml"
    env_file: str = ".env"

    @property
    def compose_path(self) -> Path:
        return self.path / self.compose_file

    @property
    def env_path(self) -> Path:
        return self.path / self.env_file

    def exists(self) -> bool:
        return self.compose_path.exists()


class DockerOps:
    """Docker operations handler."""

    NETWORK_NAME = "conserver"
    DEFAULT_SERVICES = ["conserver", "api", "redis"]

    def __init__(self, server_path: Optional[Path] = None) -> None:
        """
        Initialize Docker operations.

        Args:
            server_path: Path to vcon-server installation
        """
        self._client: Optional[docker.DockerClient] = None
        self._server_path = server_path
        self._project: Optional[ComposeProject] = None

    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client, initializing if needed."""
        if self._client is None:
            try:
                self._client = docker.from_env()
                # Test connection
                self._client.ping()
            except DockerException as e:
                raise DockerNotRunningError(str(e))
        return self._client

    @property
    def server_path(self) -> Path:
        """Get server path, resolving if needed."""
        if self._server_path is None:
            self._server_path = self._resolve_server_path()
        return self._server_path

    @property
    def project(self) -> ComposeProject:
        """Get Compose project info."""
        if self._project is None:
            self._project = ComposeProject(path=self.server_path)
            if not self._project.exists():
                raise ServerNotFoundError(
                    f"docker-compose.yml not found at {self._project.compose_path}"
                )
        return self._project

    def _resolve_server_path(self) -> Path:
        """Resolve vcon-server path from environment or config."""
        # Check environment variable
        env_path = os.environ.get("VCON_SERVER_PATH")
        if env_path:
            path = Path(env_path).expanduser().resolve()
            if path.exists():
                return path

        # Check common relative locations
        cwd = Path.cwd()
        candidates = [
            cwd / "vcon-server",
            cwd.parent / "vcon-server",
            Path.home() / "vcon-server",
        ]

        for candidate in candidates:
            if (candidate / "docker-compose.yml").exists():
                return candidate
            if (candidate / "example_docker-compose.yml").exists():
                return candidate

        raise ServerNotFoundError()

    def _run_compose(
        self,
        command: list[str],
        capture_output: bool = False,
        timeout: Optional[int] = None,
    ) -> subprocess.CompletedProcess[str]:
        """
        Run a docker compose command.

        Args:
            command: Command arguments (without 'docker compose')
            capture_output: Whether to capture output
            timeout: Command timeout in seconds

        Returns:
            Completed process result
        """
        # Check if docker compose is available
        try:
            subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DockerComposeNotFoundError()

        full_command = ["docker", "compose", "-f", str(self.project.compose_path)]

        # Add env file if exists
        if self.project.env_path.exists():
            full_command.extend(["--env-file", str(self.project.env_path)])

        full_command.extend(command)

        try:
            result = subprocess.run(
                full_command,
                capture_output=capture_output,
                text=True,
                cwd=self.project.path,
                timeout=timeout,
            )
            return result
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timed out after {timeout} seconds")

    def ensure_network(self) -> bool:
        """
        Ensure the conserver network exists.

        Returns:
            True if network was created, False if it already existed
        """
        try:
            self.client.networks.get(self.NETWORK_NAME)
            return False
        except NotFound:
            console.print(f"[yellow]Creating network '{self.NETWORK_NAME}'...[/yellow]")
            self.client.networks.create(self.NETWORK_NAME, driver="bridge")
            return True

    def remove_network(self, force: bool = False) -> bool:
        """
        Remove the conserver network.

        Args:
            force: Force removal even if containers are connected

        Returns:
            True if network was removed
        """
        try:
            network = self.client.networks.get(self.NETWORK_NAME)
            if force:
                # Disconnect all containers first
                for container in network.containers:
                    network.disconnect(container, force=True)
            network.remove()
            return True
        except NotFound:
            return False
        except Exception as e:
            raise NetworkError(str(e))

    def start(
        self,
        services: Optional[list[str]] = None,
        build: bool = False,
        detach: bool = True,
    ) -> bool:
        """
        Start containers.

        Args:
            services: Specific services to start (None for all)
            build: Build images before starting
            detach: Run in detached mode

        Returns:
            True if successful
        """
        self.ensure_network()

        command = ["up"]
        if detach:
            command.append("-d")
        if build:
            command.append("--build")
        if services:
            command.extend(services)

        result = self._run_compose(command)
        return result.returncode == 0

    def stop(
        self,
        services: Optional[list[str]] = None,
        timeout: int = 30,
    ) -> bool:
        """
        Stop containers.

        Args:
            services: Specific services to stop (None for all)
            timeout: Timeout for graceful shutdown

        Returns:
            True if successful
        """
        command = ["stop", "-t", str(timeout)]
        if services:
            command.extend(services)

        result = self._run_compose(command)
        return result.returncode == 0

    def down(
        self,
        remove_volumes: bool = False,
        remove_orphans: bool = True,
        timeout: int = 30,
    ) -> bool:
        """
        Stop and remove containers.

        Args:
            remove_volumes: Remove named volumes
            remove_orphans: Remove orphan containers
            timeout: Timeout for graceful shutdown

        Returns:
            True if successful
        """
        command = ["down", "-t", str(timeout)]
        if remove_volumes:
            command.append("-v")
        if remove_orphans:
            command.append("--remove-orphans")

        result = self._run_compose(command)
        return result.returncode == 0

    def restart(
        self,
        services: Optional[list[str]] = None,
        timeout: int = 30,
    ) -> bool:
        """
        Restart containers.

        Args:
            services: Specific services to restart (None for all)
            timeout: Timeout for graceful shutdown

        Returns:
            True if successful
        """
        command = ["restart", "-t", str(timeout)]
        if services:
            command.extend(services)

        result = self._run_compose(command)
        return result.returncode == 0

    def pull(self, services: Optional[list[str]] = None) -> bool:
        """
        Pull latest images.

        Args:
            services: Specific services to pull (None for all)

        Returns:
            True if successful
        """
        command = ["pull"]
        if services:
            command.extend(services)

        result = self._run_compose(command)
        return result.returncode == 0

    def build(
        self,
        services: Optional[list[str]] = None,
        no_cache: bool = False,
    ) -> bool:
        """
        Build images.

        Args:
            services: Specific services to build (None for all)
            no_cache: Build without cache

        Returns:
            True if successful
        """
        command = ["build"]
        if no_cache:
            command.append("--no-cache")
        if services:
            command.extend(services)

        result = self._run_compose(command)
        return result.returncode == 0

    def get_status(self, all_containers: bool = False) -> list[ContainerInfo]:
        """
        Get status of containers.

        Args:
            all_containers: Include stopped containers

        Returns:
            List of container info
        """
        command = ["ps", "--format", "json"]
        if all_containers:
            command.append("-a")

        result = self._run_compose(command, capture_output=True)

        if result.returncode != 0:
            return []

        containers = []
        # Parse JSON output (one JSON object per line)
        import json

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                containers.append(
                    ContainerInfo(
                        name=data.get("Name", ""),
                        service=data.get("Service", ""),
                        status=data.get("State", data.get("Status", "")),
                        health=data.get("Health", "-"),
                        ports=data.get("Ports", data.get("Publishers", "")),
                        image=data.get("Image", ""),
                        created=data.get("CreatedAt", ""),
                    )
                )
            except json.JSONDecodeError:
                continue

        return containers

    def get_logs(
        self,
        services: Optional[list[str]] = None,
        follow: bool = False,
        tail: Optional[int] = None,
        since: Optional[str] = None,
        timestamps: bool = False,
    ) -> subprocess.Popen[str]:
        """
        Get container logs as a streaming process.

        Args:
            services: Specific services (None for all)
            follow: Follow log output
            tail: Number of lines from end
            since: Show logs since timestamp
            timestamps: Show timestamps

        Returns:
            Popen process streaming logs
        """
        command = ["docker", "compose", "-f", str(self.project.compose_path)]

        if self.project.env_path.exists():
            command.extend(["--env-file", str(self.project.env_path)])

        command.append("logs")

        if follow:
            command.append("-f")
        if tail:
            command.extend(["--tail", str(tail)])
        if since:
            command.extend(["--since", since])
        if timestamps:
            command.append("-t")
        if services:
            command.extend(services)

        return subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.project.path,
        )

    def exec_command(
        self,
        service: str,
        command: list[str],
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute a command in a running container.

        Args:
            service: Service name
            command: Command to execute
            capture_output: Whether to capture output

        Returns:
            Completed process result
        """
        full_command = ["exec", "-T", service] + command
        return self._run_compose(full_command, capture_output=capture_output)

    def is_running(self, service: Optional[str] = None) -> bool:
        """
        Check if containers are running.

        Args:
            service: Specific service to check (None for any)

        Returns:
            True if running
        """
        containers = self.get_status()

        if not containers:
            return False

        if service:
            return any(
                c.service == service and "running" in c.status.lower() for c in containers
            )

        return any("running" in c.status.lower() for c in containers)

    def get_service_url(self, service: str = "api", port: int = 8000) -> str:
        """
        Get URL for a service.

        Args:
            service: Service name
            port: Internal port

        Returns:
            URL string
        """
        containers = self.get_status()
        for container in containers:
            if container.service == service:
                # Try to extract mapped port from ports string
                # Format might be "0.0.0.0:8000->8000/tcp"
                if container.ports:
                    for port_mapping in str(container.ports).split(","):
                        if f"->{port}" in port_mapping:
                            # Extract host port
                            host_port = port_mapping.split(":")[1].split("->")[0]
                            return f"http://localhost:{host_port}"

        # Default
        return f"http://localhost:{port}"
