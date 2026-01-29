"""Unit tests for configuration management."""

from pathlib import Path

import pytest

from dd_dm.core.config import ConfigManager
from dd_dm.core.exceptions import ConfigError, NotInitializedError
from dd_dm.models.config import Config, LocalConfig, ModulesConfig


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_init_with_default_path(self, temp_project: Path) -> None:
        """Test initialization with default project root."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            manager = ConfigManager()
            # Resolve both paths to handle macOS symlinks (/var -> /private/var)
            assert manager.project_root.resolve() == temp_project.resolve()
        finally:
            os.chdir(original_cwd)

    def test_init_with_custom_path(self, temp_project: Path) -> None:
        """Test initialization with custom project root."""
        manager = ConfigManager(temp_project)
        assert manager.project_root == temp_project
        assert manager.config_dir == temp_project / ".dd-dm"
        assert manager.config_path == temp_project / ".dd-dm" / "config.toml"

    def test_is_initialized_false(self, temp_project: Path) -> None:
        """Test is_initialized returns False when not initialized."""
        manager = ConfigManager(temp_project)
        assert not manager.is_initialized()

    def test_is_initialized_true(self, temp_project: Path) -> None:
        """Test is_initialized returns True when initialized."""
        manager = ConfigManager(temp_project)
        manager.config_dir.mkdir(parents=True)
        manager.config_path.write_text("[modules]\nenabled = []")
        assert manager.is_initialized()

    def test_ensure_initialized_raises(self, temp_project: Path) -> None:
        """Test ensure_initialized raises when not initialized."""
        manager = ConfigManager(temp_project)
        with pytest.raises(NotInitializedError):
            manager.ensure_initialized()

    def test_init_directories(self, temp_project: Path) -> None:
        """Test init_directories creates required directories."""
        manager = ConfigManager(temp_project)
        manager.init_directories()

        assert manager.config_dir.exists()
        assert manager.cache_dir.exists()
        assert manager.local_dir.exists()
        assert (manager.cache_dir / "modules").exists()

    def test_save_and_load_config(self, temp_project: Path) -> None:
        """Test saving and loading configuration."""
        manager = ConfigManager(temp_project)
        manager.init_directories()

        config = Config(
            modules=ModulesConfig(enabled=["module1", "module2"]),
            local=LocalConfig(custom_modules=["custom1"]),
        )

        manager.save(config)
        loaded = manager.load()

        assert loaded.modules.enabled == config.modules.enabled
        assert loaded.local.custom_modules == config.local.custom_modules

    def test_load_minimal_config(self, temp_project: Path) -> None:
        """Test loading a minimal configuration."""
        manager = ConfigManager(temp_project)
        manager.config_dir.mkdir(parents=True)
        manager.config_path.write_text("[modules]\nenabled = []")

        config = manager.load()

        assert config.modules.enabled == []
        assert config.local.custom_modules == []

    def test_load_invalid_toml_raises(self, temp_project: Path) -> None:
        """Test load raises on invalid TOML."""
        manager = ConfigManager(temp_project)
        manager.config_dir.mkdir(parents=True)
        manager.config_path.write_text("this is not valid toml [[[")

        with pytest.raises(ConfigError, match="Invalid configuration file"):
            manager.load()
