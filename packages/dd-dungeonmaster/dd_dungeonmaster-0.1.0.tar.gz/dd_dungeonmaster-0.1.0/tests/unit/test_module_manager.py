"""Unit tests for module manager."""

from pathlib import Path

import pytest

from dd_dm.core.config import ConfigManager
from dd_dm.core.exceptions import ModuleAlreadyExistsError, ModuleNotFoundDDDMError
from dd_dm.core.module_manager import ModuleManager
from dd_dm.models.config import Config, ModulesConfig
from dd_dm.models.module import ModuleSource


@pytest.fixture
def config_manager(temp_project: Path) -> ConfigManager:
    """Create a ConfigManager for testing."""
    manager = ConfigManager(temp_project)
    manager.init_directories()
    return manager


@pytest.fixture
def module_manager(config_manager: ConfigManager) -> ModuleManager:
    """Create a ModuleManager for testing."""
    return ModuleManager(config_manager)


@pytest.fixture
def sample_config() -> Config:
    """Create a sample configuration."""
    return Config(
        modules=ModulesConfig(enabled=[]),
    )


class TestModuleManager:
    """Tests for ModuleManager class."""

    def test_init(self, config_manager: ConfigManager) -> None:
        """Test ModuleManager initialization."""
        manager = ModuleManager(config_manager)
        assert manager.config_manager == config_manager

    def test_list_available_modules_empty(self, module_manager: ModuleManager) -> None:
        """Test listing modules when none exist."""
        modules = module_manager.list_available_modules()
        assert modules == []

    def test_list_available_modules_with_remote(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test listing modules includes remote modules."""
        # Create a remote module
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "TEST_MODULE.md").write_text("# Test Module\n\nContent here.")

        modules = module_manager.list_available_modules()
        assert len(modules) == 1
        assert modules[0].name == "TEST_MODULE"
        assert modules[0].source == ModuleSource.REMOTE

    def test_list_available_modules_with_local(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test listing modules includes local modules."""
        # Create a local module
        (config_manager.local_dir / "LOCAL_MODULE.md").write_text("# Local\n\nContent.")

        modules = module_manager.list_available_modules()
        assert len(modules) == 1
        assert modules[0].name == "LOCAL_MODULE"
        assert modules[0].source == ModuleSource.LOCAL

    def test_get_module_not_found(self, module_manager: ModuleManager) -> None:
        """Test get_module raises for non-existent module."""
        with pytest.raises(ModuleNotFoundDDDMError):
            module_manager.get_module("NON_EXISTENT")

    def test_get_module_remote(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test get_module returns remote module."""
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "TEST.md").write_text("# Test\n\nContent.")

        module = module_manager.get_module("TEST")
        assert module.name == "TEST"
        assert module.source == ModuleSource.REMOTE
        assert "Content" in module.content

    def test_get_module_local(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test get_module returns local module."""
        (config_manager.local_dir / "LOCAL.md").write_text("# Local\n\nLocal content.")

        module = module_manager.get_module("LOCAL")
        assert module.name == "LOCAL"
        assert module.source == ModuleSource.LOCAL

    def test_is_module_enabled_false(
        self,
        module_manager: ModuleManager,
        sample_config: Config,
    ) -> None:
        """Test is_module_enabled returns False for disabled module."""
        assert not module_manager.is_module_enabled("TEST", sample_config)

    def test_is_module_enabled_true(
        self,
        module_manager: ModuleManager,
        sample_config: Config,
    ) -> None:
        """Test is_module_enabled returns True for enabled module."""
        sample_config.modules.enabled.append("TEST")
        assert module_manager.is_module_enabled("TEST", sample_config)

    def test_add_module(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
        sample_config: Config,
    ) -> None:
        """Test adding a module."""
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "NEW_MODULE.md").write_text("# New\n\nContent.")

        diff = module_manager.add_module("NEW_MODULE", sample_config)

        assert "NEW_MODULE" in sample_config.modules.enabled
        assert diff.is_addition

    def test_add_module_already_exists(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
        sample_config: Config,
    ) -> None:
        """Test adding existing module raises without force."""
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "EXISTING.md").write_text("# Existing")

        sample_config.modules.enabled.append("EXISTING")

        with pytest.raises(ModuleAlreadyExistsError):
            module_manager.add_module("EXISTING", sample_config, force=False)

    def test_add_module_force(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
        sample_config: Config,
    ) -> None:
        """Test adding existing module with force succeeds."""
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "EXISTING.md").write_text("# Existing")

        sample_config.modules.enabled.append("EXISTING")

        diff = module_manager.add_module("EXISTING", sample_config, force=True)
        assert not diff.is_addition  # It's a modification/no-change

    def test_remove_module(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
        sample_config: Config,
    ) -> None:
        """Test removing a module."""
        modules_dir = config_manager.cache_dir / "modules"
        modules_dir.mkdir(parents=True, exist_ok=True)
        (modules_dir / "TO_REMOVE.md").write_text("# Remove")

        sample_config.modules.enabled.append("TO_REMOVE")

        diff = module_manager.remove_module("TO_REMOVE", sample_config)

        assert "TO_REMOVE" not in sample_config.modules.enabled
        assert diff.is_removal

    def test_remove_module_not_enabled(
        self,
        module_manager: ModuleManager,
        sample_config: Config,
    ) -> None:
        """Test removing non-enabled module raises."""
        with pytest.raises(ModuleNotFoundDDDMError):
            module_manager.remove_module("NOT_ENABLED", sample_config)

    def test_create_local_module(self, module_manager: ModuleManager) -> None:
        """Test creating a local module."""
        module = module_manager.create_local_module("MY_MODULE")

        assert module.name == "MY_MODULE"
        assert module.source == ModuleSource.LOCAL
        assert (module_manager.config_manager.local_dir / "MY_MODULE.md").exists()

    def test_create_local_module_with_content(
        self, module_manager: ModuleManager
    ) -> None:
        """Test creating a local module with custom content."""
        content = "# Custom\n\nMy custom content."
        module = module_manager.create_local_module("CUSTOM", content=content)

        assert module.content == content

    def test_delete_local_module(
        self,
        module_manager: ModuleManager,
        config_manager: ConfigManager,
    ) -> None:
        """Test deleting a local module."""
        # Create module first
        module_manager.create_local_module("TO_DELETE")
        assert (config_manager.local_dir / "TO_DELETE.md").exists()

        # Delete it
        result = module_manager.delete_local_module("TO_DELETE")
        assert result is True
        assert not (config_manager.local_dir / "TO_DELETE.md").exists()

    def test_delete_local_module_not_found(self, module_manager: ModuleManager) -> None:
        """Test deleting non-existent module returns False."""
        result = module_manager.delete_local_module("NOT_EXISTS")
        assert result is False
