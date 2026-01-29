"""
Custom exceptions for Conserver CLI.
"""

from typing import Optional


class ConserverError(Exception):
    """Base exception for all CLI errors."""

    exit_code: int = 1
    message: str = "An error occurred"

    def __init__(self, message: Optional[str] = None) -> None:
        self.message = message or self.__class__.message
        super().__init__(self.message)


class DockerNotRunningError(ConserverError):
    """Docker daemon is not running."""

    exit_code: int = 2
    message: str = "Docker daemon is not running. Please start Docker and try again."


class DockerComposeNotFoundError(ConserverError):
    """Docker Compose is not available."""

    exit_code: int = 3
    message: str = "Docker Compose not found. Please install Docker Compose."


class ServerNotFoundError(ConserverError):
    """vcon-server installation not found."""

    exit_code: int = 4
    message: str = "vcon-server installation not found. Use --server-path to specify location."


class ConfigurationError(ConserverError):
    """Configuration file error."""

    exit_code: int = 5
    message: str = "Configuration error"


class ConfigFileNotFoundError(ConfigurationError):
    """Configuration file not found."""

    message: str = "Configuration file not found"


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed."""

    message: str = "Configuration validation failed"


class HealthCheckError(ConserverError):
    """Service health check failed."""

    exit_code: int = 6
    message: str = "Health check failed"


class NetworkError(ConserverError):
    """Docker network error."""

    exit_code: int = 7
    message: str = "Docker network error"


class TimeoutError(ConserverError):
    """Operation timed out."""

    exit_code: int = 8
    message: str = "Operation timed out"


class ContainerError(ConserverError):
    """Container operation error."""

    exit_code: int = 9
    message: str = "Container operation failed"


class ServiceNotRunningError(ConserverError):
    """Service is not running."""

    exit_code: int = 10
    message: str = "Service is not running"
