"""Configuration management for dd-dm."""

import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from dd_dm.core.exceptions import ConfigError, NotInitializedError
from dd_dm.models.config import Config, LocalConfig, ModulesConfig


class ConfigManager:
    """Manages dd-dm configuration for a project."""

    CONFIG_DIR = ".dd-dm"
    CONFIG_FILE = "config.toml"
    CACHE_DIR = "cache"
    LOCAL_DIR = "local"

    def __init__(self, project_root: Path | None = None) -> None:
        """Initialize config manager.

        Args:
            project_root: Root directory of the project. Defaults to cwd.
        """
        self.project_root = project_root or Path.cwd()
        self.config_dir = self.project_root / self.CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self.cache_dir = self.config_dir / self.CACHE_DIR
        self.local_dir = self.config_dir / self.LOCAL_DIR

    def is_initialized(self) -> bool:
        """Check if dd-dm is initialized in the project."""
        return self.config_path.exists()

    def ensure_initialized(self) -> None:
        """Ensure dd-dm is initialized, raise error if not."""
        if not self.is_initialized():
            raise NotInitializedError(str(self.project_root))

    def init_directories(self) -> None:
        """Create the dd-dm directory structure."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "modules").mkdir(parents=True, exist_ok=True)

    def load(self) -> Config:
        """Load configuration from file.

        Returns:
            Parsed configuration.

        Raises:
            NotInitializedError: If dd-dm is not initialized.
            ConfigError: If configuration is invalid.
        """
        self.ensure_initialized()

        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
            return self._parse_config(data)
        except tomllib.TOMLDecodeError as e:
            raise ConfigError(f"Invalid configuration file: {e}") from e

    def save(self, config: Config) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = self._serialize_config(config)
        with open(self.config_path, "wb") as f:
            tomli_w.dump(data, f)

    def _parse_config(self, data: dict[str, Any]) -> Config:
        """Parse configuration dictionary into Config object."""
        modules_data = data.get("modules", {})
        modules = ModulesConfig(
            enabled=modules_data.get("enabled", []),
        )

        local_data = data.get("local", {})
        local = LocalConfig(
            custom_modules=local_data.get("custom_modules", []),
        )

        return Config(modules=modules, local=local)

    def _serialize_config(self, config: Config) -> dict[str, Any]:
        """Serialize Config object to dictionary for TOML."""
        data: dict[str, Any] = {
            "modules": {
                "enabled": config.modules.enabled,
            },
            "local": {
                "custom_modules": config.local.custom_modules,
            },
        }

        return data
