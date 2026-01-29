"""
Health check utilities for Conserver CLI.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import httpx

from conserver.docker_ops import DockerOps
from conserver.exceptions import HealthCheckError


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"
    UNREACHABLE = "unreachable"


@dataclass
class HealthResult:
    """Health check result for a service."""

    service: str
    status: HealthStatus
    message: str = ""
    latency_ms: Optional[float] = None
    details: Optional[dict[str, Any]] = None

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY


@dataclass
class OverallHealth:
    """Overall health status."""

    status: HealthStatus
    services: list[HealthResult]
    version: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.HEALTHY

    @property
    def healthy_count(self) -> int:
        return sum(1 for s in self.services if s.is_healthy)

    @property
    def total_count(self) -> int:
        return len(self.services)


class HealthChecker:
    """Health checker for vcon-server services."""

    def __init__(self, docker_ops: DockerOps) -> None:
        """
        Initialize health checker.

        Args:
            docker_ops: Docker operations instance
        """
        self.docker = docker_ops
        self._api_url: Optional[str] = None

    @property
    def api_url(self) -> str:
        """Get API URL."""
        if self._api_url is None:
            self._api_url = self.docker.get_service_url("api", 8000)
        return self._api_url

    async def check_api(self, timeout: float = 10.0) -> HealthResult:
        """
        Check API health.

        Args:
            timeout: Request timeout in seconds

        Returns:
            HealthResult for API service
        """
        import time

        start = time.monotonic()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/health",
                    timeout=timeout,
                )
                latency = (time.monotonic() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    return HealthResult(
                        service="api",
                        status=HealthStatus.HEALTHY,
                        message="API responding normally",
                        latency_ms=latency,
                        details=data,
                    )
                else:
                    return HealthResult(
                        service="api",
                        status=HealthStatus.UNHEALTHY,
                        message=f"HTTP {response.status_code}",
                        latency_ms=latency,
                    )

        except httpx.ConnectError:
            return HealthResult(
                service="api",
                status=HealthStatus.UNREACHABLE,
                message="Connection refused",
            )
        except httpx.TimeoutException:
            return HealthResult(
                service="api",
                status=HealthStatus.UNREACHABLE,
                message=f"Timeout after {timeout}s",
            )
        except Exception as e:
            return HealthResult(
                service="api",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    def check_api_sync(self, timeout: float = 10.0) -> HealthResult:
        """
        Check API health synchronously.

        Args:
            timeout: Request timeout in seconds

        Returns:
            HealthResult for API service
        """
        import time

        start = time.monotonic()

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.api_url}/health",
                    timeout=timeout,
                )
                latency = (time.monotonic() - start) * 1000

                if response.status_code == 200:
                    data = response.json()
                    return HealthResult(
                        service="api",
                        status=HealthStatus.HEALTHY,
                        message="API responding normally",
                        latency_ms=latency,
                        details=data,
                    )
                else:
                    return HealthResult(
                        service="api",
                        status=HealthStatus.UNHEALTHY,
                        message=f"HTTP {response.status_code}",
                        latency_ms=latency,
                    )

        except httpx.ConnectError:
            return HealthResult(
                service="api",
                status=HealthStatus.UNREACHABLE,
                message="Connection refused",
            )
        except httpx.TimeoutException:
            return HealthResult(
                service="api",
                status=HealthStatus.UNREACHABLE,
                message=f"Timeout after {timeout}s",
            )
        except Exception as e:
            return HealthResult(
                service="api",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )

    def check_redis(self, timeout: float = 5.0) -> HealthResult:
        """
        Check Redis health via docker exec.

        Args:
            timeout: Command timeout in seconds

        Returns:
            HealthResult for Redis service
        """
        import time

        start = time.monotonic()

        try:
            result = self.docker.exec_command(
                "redis",
                ["redis-cli", "ping"],
            )
            latency = (time.monotonic() - start) * 1000

            if result.returncode == 0 and "PONG" in result.stdout:
                return HealthResult(
                    service="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis responding to PING",
                    latency_ms=latency,
                )
            else:
                return HealthResult(
                    service="redis",
                    status=HealthStatus.UNHEALTHY,
                    message=result.stderr or "No PONG response",
                    latency_ms=latency,
                )

        except Exception as e:
            return HealthResult(
                service="redis",
                status=HealthStatus.UNREACHABLE,
                message=str(e),
            )

    def check_container(self, service: str) -> HealthResult:
        """
        Check container health status.

        Args:
            service: Service name

        Returns:
            HealthResult for the container
        """
        containers = self.docker.get_status()

        for container in containers:
            if container.service == service:
                status_lower = container.status.lower()
                health_lower = container.health.lower()

                if "running" not in status_lower:
                    return HealthResult(
                        service=service,
                        status=HealthStatus.UNHEALTHY,
                        message=f"Container status: {container.status}",
                    )

                if health_lower == "healthy":
                    return HealthResult(
                        service=service,
                        status=HealthStatus.HEALTHY,
                        message="Container healthy",
                    )
                elif health_lower == "unhealthy":
                    return HealthResult(
                        service=service,
                        status=HealthStatus.UNHEALTHY,
                        message="Container health check failing",
                    )
                elif health_lower in ("starting", "none", "-"):
                    return HealthResult(
                        service=service,
                        status=HealthStatus.HEALTHY,
                        message="Container running (no health check)",
                    )
                else:
                    return HealthResult(
                        service=service,
                        status=HealthStatus.DEGRADED,
                        message=f"Health: {container.health}",
                    )

        return HealthResult(
            service=service,
            status=HealthStatus.UNREACHABLE,
            message="Container not found",
        )

    def check_all(self, timeout: float = 10.0) -> OverallHealth:
        """
        Check health of all services.

        Args:
            timeout: Timeout for individual checks

        Returns:
            OverallHealth with all service results
        """
        results: list[HealthResult] = []

        # Check containers first
        for service in ["conserver", "api", "redis"]:
            results.append(self.check_container(service))

        # If API container is running, check API endpoint
        api_container = next((r for r in results if r.service == "api"), None)
        if api_container and api_container.is_healthy:
            api_health = self.check_api_sync(timeout)
            # Replace container check with API check
            results = [r for r in results if r.service != "api"]
            results.append(api_health)

        # If Redis container is running, check Redis
        redis_container = next((r for r in results if r.service == "redis"), None)
        if redis_container and redis_container.is_healthy:
            redis_health = self.check_redis(timeout)
            # Replace container check with Redis check
            results = [r for r in results if r.service != "redis"]
            results.append(redis_health)

        # Determine overall status
        unhealthy = sum(1 for r in results if not r.is_healthy)
        if unhealthy == 0:
            overall_status = HealthStatus.HEALTHY
        elif unhealthy == len(results):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        # Try to get version
        version = self._get_version()

        return OverallHealth(
            status=overall_status,
            services=results,
            version=version,
        )

    def _get_version(self) -> Optional[str]:
        """Get vcon-server version from API."""
        try:
            with httpx.Client() as client:
                response = client.get(f"{self.api_url}/version", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("version")
        except Exception:
            pass
        return None

    def get_queue_depth(self, queue_name: str = "default") -> Optional[int]:
        """
        Get queue depth from Redis.

        Args:
            queue_name: Name of the queue

        Returns:
            Queue depth or None if unavailable
        """
        try:
            result = self.docker.exec_command(
                "redis",
                ["redis-cli", "LLEN", queue_name],
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception:
            pass
        return None

    def get_dlq_depth(self, queue_name: str = "default") -> Optional[int]:
        """
        Get dead letter queue depth from Redis.

        Args:
            queue_name: Name of the ingress list

        Returns:
            DLQ depth or None if unavailable
        """
        return self.get_queue_depth(f"DLQ:{queue_name}")
