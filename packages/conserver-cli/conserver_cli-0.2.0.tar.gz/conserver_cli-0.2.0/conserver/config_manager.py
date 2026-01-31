"""
Configuration management for Conserver CLI.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import dotenv_values

from conserver.console import console
from conserver.exceptions import (
    ConfigFileNotFoundError,
    ConfigurationError,
    ConfigValidationError,
)


@dataclass
class ValidationError:
    """Configuration validation error."""

    field: str
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ConfigFile:
    """Configuration file information."""

    path: Path
    file_type: str  # env, yaml, compose
    exists: bool = False
    content: Optional[dict[str, Any]] = None


# Sensitive keys that should be masked in output
SENSITIVE_KEYS = {
    "CONSERVER_API_TOKEN",
    "GROQ_API_KEY",
    "DEEPGRAM_KEY",
    "OPENAI_API_KEY",
    "DD_API_KEY",
    "aws_secret_access_key",
    "api_key",
    "password",
    "secret",
}


class ConfigManager:
    """Configuration manager for vcon-server."""

    def __init__(self, server_path: Path) -> None:
        """
        Initialize configuration manager.

        Args:
            server_path: Path to vcon-server installation
        """
        self.server_path = server_path
        self._config_files: dict[str, ConfigFile] = {}

    @property
    def env_file(self) -> Path:
        return self.server_path / ".env"

    @property
    def env_example_file(self) -> Path:
        return self.server_path / ".env.example"

    @property
    def config_file(self) -> Path:
        return self.server_path / "config.yml"

    @property
    def config_example_file(self) -> Path:
        return self.server_path / "example_config.yml"

    @property
    def compose_file(self) -> Path:
        return self.server_path / "docker-compose.yml"

    @property
    def compose_example_file(self) -> Path:
        return self.server_path / "example_docker-compose.yml"

    def get_config_file(self, file_type: str) -> ConfigFile:
        """
        Get configuration file info.

        Args:
            file_type: One of 'env', 'config', 'compose'

        Returns:
            ConfigFile instance
        """
        path_map = {
            "env": self.env_file,
            "config": self.config_file,
            "compose": self.compose_file,
        }

        if file_type not in path_map:
            raise ConfigurationError(f"Unknown config file type: {file_type}")

        path = path_map[file_type]
        exists = path.exists()
        content = None

        if exists:
            if file_type == "env":
                content = dict(dotenv_values(path))
            elif file_type in ("config", "compose"):
                with open(path) as f:
                    content = yaml.safe_load(f)

        return ConfigFile(
            path=path,
            file_type=file_type,
            exists=exists,
            content=content,
        )

    def load_env(self) -> dict[str, Optional[str]]:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            return {}
        return dict(dotenv_values(self.env_file))

    def load_config(self) -> dict[str, Any]:
        """Load config.yml file."""
        if not self.config_file.exists():
            raise ConfigFileNotFoundError(f"Config file not found: {self.config_file}")

        with open(self.config_file) as f:
            return yaml.safe_load(f) or {}

    def load_compose(self) -> dict[str, Any]:
        """Load docker-compose.yml file."""
        if not self.compose_file.exists():
            raise ConfigFileNotFoundError(f"Compose file not found: {self.compose_file}")

        with open(self.compose_file) as f:
            return yaml.safe_load(f) or {}

    def save_env(self, values: dict[str, Optional[str]]) -> None:
        """
        Save environment variables to .env file.

        Args:
            values: Dictionary of key-value pairs
        """
        lines = []
        for key, value in sorted(values.items()):
            if value is None:
                lines.append(f"{key}=")
            elif " " in str(value) or '"' in str(value):
                # Quote values with spaces or quotes
                escaped = str(value).replace('"', '\\"')
                lines.append(f'{key}="{escaped}"')
            else:
                lines.append(f"{key}={value}")

        with open(self.env_file, "w") as f:
            f.write("\n".join(lines) + "\n")

    def save_config(self, config: dict[str, Any]) -> None:
        """
        Save config.yml file.

        Args:
            config: Configuration dictionary
        """
        with open(self.config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_env_value(self, key: str) -> Optional[str]:
        """Get a single environment variable value."""
        env = self.load_env()
        return env.get(key)

    def set_env_value(self, key: str, value: str) -> None:
        """Set a single environment variable value."""
        env = self.load_env()
        env[key] = value
        self.save_env(env)

    def get_config_value(self, key_path: str) -> Any:
        """
        Get a configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path like 'links.transcribe.options.model_size'

        Returns:
            The value at the path
        """
        config = self.load_config()
        keys = key_path.split(".")
        value = config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def set_config_value(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value by dot-separated path.

        Args:
            key_path: Dot-separated path like 'links.transcribe.options.model_size'
            value: Value to set
        """
        config = self.load_config()
        keys = key_path.split(".")

        # Navigate to parent
        current = config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value
        current[keys[-1]] = value
        self.save_config(config)

    def init_from_examples(self, overwrite: bool = False) -> dict[str, bool]:
        """
        Initialize configuration files from examples.

        Args:
            overwrite: Whether to overwrite existing files

        Returns:
            Dictionary of file -> created status
        """
        results = {}
        mappings = [
            (self.env_example_file, self.env_file, "env"),
            (self.config_example_file, self.config_file, "config"),
            (self.compose_example_file, self.compose_file, "compose"),
        ]

        for example, target, name in mappings:
            if not example.exists():
                results[name] = False
                continue

            if target.exists() and not overwrite:
                results[name] = False
                continue

            shutil.copy(example, target)
            results[name] = True

        return results

    def validate(self) -> list[ValidationError]:
        """
        Validate all configuration files.

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        # Validate env file
        errors.extend(self._validate_env())

        # Validate config.yml
        errors.extend(self._validate_config())

        # Validate docker-compose.yml
        errors.extend(self._validate_compose())

        return errors

    def _validate_env(self) -> list[ValidationError]:
        """Validate .env file."""
        errors = []

        if not self.env_file.exists():
            errors.append(
                ValidationError(
                    field=".env",
                    message="File not found. Run 'conserver config init' to create from example.",
                    severity="warning",
                )
            )
            return errors

        env = self.load_env()

        # Check required variables
        required = ["REDIS_URL"]
        for key in required:
            if not env.get(key):
                errors.append(
                    ValidationError(
                        field=f".env:{key}",
                        message=f"Required variable '{key}' is not set",
                    )
                )

        # Check REDIS_URL format
        redis_url = env.get("REDIS_URL", "")
        if redis_url and not redis_url.startswith("redis://"):
            errors.append(
                ValidationError(
                    field=".env:REDIS_URL",
                    message="REDIS_URL should start with 'redis://'",
                )
            )

        return errors

    def _validate_config(self) -> list[ValidationError]:
        """Validate config.yml file."""
        errors = []

        if not self.config_file.exists():
            errors.append(
                ValidationError(
                    field="config.yml",
                    message="File not found. Run 'conserver config init' to create from example.",
                    severity="warning",
                )
            )
            return errors

        try:
            config = self.load_config()
        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    field="config.yml",
                    message=f"YAML syntax error: {e}",
                )
            )
            return errors

        # Validate chains reference valid links
        links = config.get("links", {})
        chains = config.get("chains", {})
        storages = config.get("storages", {})

        for chain_name, chain_config in chains.items():
            if not isinstance(chain_config, dict):
                continue

            # Check links references
            for link_name in chain_config.get("links", []):
                if link_name not in links:
                    errors.append(
                        ValidationError(
                            field=f"chains.{chain_name}.links",
                            message=f"Link '{link_name}' is not defined in links section",
                        )
                    )

            # Check storage references
            for storage_name in chain_config.get("storages", []):
                if storage_name not in storages:
                    errors.append(
                        ValidationError(
                            field=f"chains.{chain_name}.storages",
                            message=f"Storage '{storage_name}' is not defined in storages section",
                        )
                    )

        return errors

    def _validate_compose(self) -> list[ValidationError]:
        """Validate docker-compose.yml file."""
        errors = []

        if not self.compose_file.exists():
            errors.append(
                ValidationError(
                    field="docker-compose.yml",
                    message="File not found. Run 'conserver config init' to create from example.",
                    severity="warning",
                )
            )
            return errors

        try:
            compose = self.load_compose()
        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    field="docker-compose.yml",
                    message=f"YAML syntax error: {e}",
                )
            )
            return errors

        # Check for required services
        services = compose.get("services", {})
        required_services = ["redis"]

        for service in required_services:
            if service not in services:
                errors.append(
                    ValidationError(
                        field="docker-compose.yml:services",
                        message=f"Required service '{service}' is not defined",
                    )
                )

        # Check network configuration
        networks = compose.get("networks", {})
        if "conserver" not in networks:
            errors.append(
                ValidationError(
                    field="docker-compose.yml:networks",
                    message="Network 'conserver' is not defined",
                    severity="warning",
                )
            )

        return errors

    def edit_file(self, file_type: str, editor: Optional[str] = None) -> bool:
        """
        Open configuration file in editor.

        Args:
            file_type: One of 'env', 'config', 'compose'
            editor: Editor to use (default: $EDITOR or nano)

        Returns:
            True if successful
        """
        config_file = self.get_config_file(file_type)

        if not config_file.exists:
            raise ConfigFileNotFoundError(f"File not found: {config_file.path}")

        editor = editor or os.environ.get("EDITOR", "nano")

        try:
            subprocess.run([editor, str(config_file.path)], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            raise ConfigurationError(f"Editor not found: {editor}")

    def is_key_sensitive(self, key: str) -> bool:
        """Check if a configuration key is sensitive."""
        key_lower = key.lower()
        for sensitive in SENSITIVE_KEYS:
            if sensitive.lower() in key_lower:
                return True
        return False

    def mask_value(self, value: Any) -> str:
        """Mask a sensitive value."""
        if not value:
            return "<not set>"
        str_value = str(value)
        if len(str_value) <= 4:
            return "****"
        return "****" + str_value[-4:]

    def backup_configs(self, backup_dir: Optional[Path] = None) -> Path:
        """
        Backup configuration files.

        Args:
            backup_dir: Directory for backups (default: server_path/.backups)

        Returns:
            Path to backup directory
        """
        import datetime

        if backup_dir is None:
            backup_dir = self.server_path / ".backups"

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)

        files_to_backup = [
            self.env_file,
            self.config_file,
            self.compose_file,
        ]

        for file_path in files_to_backup:
            if file_path.exists():
                shutil.copy(file_path, backup_path / file_path.name)

        return backup_path
