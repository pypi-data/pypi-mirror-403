"""Module management for dd-dm."""

from pathlib import Path

from dd_dm.core.config import ConfigManager
from dd_dm.core.exceptions import ModuleAlreadyExistsError, ModuleNotFoundDDDMError
from dd_dm.models.config import Config
from dd_dm.models.module import Module, ModuleDiff, ModuleSource


class ModuleManager:
    """Manages constitution modules."""

    MODULES_DIR = "modules"

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize module manager.

        Args:
            config_manager: Configuration manager instance.
        """
        self.config_manager = config_manager
        self.cache_modules_dir = config_manager.cache_dir / self.MODULES_DIR
        self.local_modules_dir = config_manager.local_dir

    def list_available_modules(self) -> list[Module]:
        """List all available modules (remote and local).

        Returns:
            List of available modules.
        """
        modules: list[Module] = []

        # Load remote modules from cache
        if self.cache_modules_dir.exists():
            for path in self.cache_modules_dir.glob("*.md"):
                module = self._load_module_from_file(path, ModuleSource.REMOTE)
                if module:
                    modules.append(module)

        # Load local modules
        if self.local_modules_dir.exists():
            for path in self.local_modules_dir.glob("*.md"):
                module = self._load_module_from_file(path, ModuleSource.LOCAL)
                if module:
                    modules.append(module)

        return sorted(modules, key=lambda m: m.name)

    def list_enabled_modules(self, config: Config) -> list[str]:
        """List enabled module names.

        Args:
            config: Current configuration.

        Returns:
            List of enabled module names.
        """
        return config.modules.enabled.copy()

    def get_module(self, name: str) -> Module:
        """Get a module by name.

        Args:
            name: Module name.

        Returns:
            The requested module.

        Raises:
            ModuleNotFoundError: If module is not found.
        """
        # Check remote modules first
        remote_path = self.cache_modules_dir / f"{name}.md"
        if remote_path.exists():
            module = self._load_module_from_file(remote_path, ModuleSource.REMOTE)
            if module:
                return module

        # Check local modules
        local_path = self.local_modules_dir / f"{name}.md"
        if local_path.exists():
            module = self._load_module_from_file(local_path, ModuleSource.LOCAL)
            if module:
                return module

        raise ModuleNotFoundDDDMError(name)

    def is_module_enabled(self, name: str, config: Config) -> bool:
        """Check if a module is enabled.

        Args:
            name: Module name.
            config: Current configuration.

        Returns:
            True if module is enabled.
        """
        return name in config.modules.enabled

    def add_module(
        self,
        name: str,
        config: Config,
        force: bool = False,
    ) -> ModuleDiff:
        """Add a module to the enabled list.

        Args:
            name: Module name to add.
            config: Current configuration.
            force: Force add even if already enabled.

        Returns:
            ModuleDiff describing the change.

        Raises:
            ModuleNotFoundError: If module doesn't exist.
            ModuleAlreadyExistsError: If module is enabled and force is False.
        """
        # Verify module exists
        module = self.get_module(name)

        old_content = None
        if self.is_module_enabled(name, config):
            if not force:
                raise ModuleAlreadyExistsError(name)
            old_content = module.content

        if name not in config.modules.enabled:
            config.modules.enabled.append(name)

        return ModuleDiff(
            module_name=name,
            old_content=old_content,
            new_content=module.content,
        )

    def remove_module(self, name: str, config: Config) -> ModuleDiff:
        """Remove a module from the enabled list.

        Args:
            name: Module name to remove.
            config: Current configuration.

        Returns:
            ModuleDiff describing the change.

        Raises:
            ModuleNotFoundError: If module is not enabled.
        """
        if name not in config.modules.enabled:
            raise ModuleNotFoundDDDMError(name)

        module = self.get_module(name)
        config.modules.enabled.remove(name)

        return ModuleDiff(
            module_name=name,
            old_content=module.content,
            new_content=None,
        )

    def create_local_module(
        self,
        name: str,
        content: str | None = None,
    ) -> Module:
        """Create a new local module.

        Args:
            name: Module name.
            content: Optional initial content.

        Returns:
            The created module.
        """
        self.local_modules_dir.mkdir(parents=True, exist_ok=True)

        if content is None:
            content = f"""# {name.replace("_", " ").title()}

## Overview

Describe the purpose of this module here.

## Guidelines

Add your guidelines here.
"""

        module_path = self.local_modules_dir / f"{name}.md"
        module_path.write_text(content)

        return Module(
            name=name,
            content=content,
            source=ModuleSource.LOCAL,
        )

    def delete_local_module(self, name: str) -> bool:
        """Delete a local module file.

        Args:
            name: Module name.

        Returns:
            True if deleted, False if not found.
        """
        module_path = self.local_modules_dir / f"{name}.md"
        if module_path.exists():
            module_path.unlink()
            return True
        return False

    def _load_module_from_file(
        self,
        path: Path,
        source: ModuleSource,
    ) -> Module | None:
        """Load a module from a file.

        Args:
            path: Path to the module file.
            source: Source type of the module.

        Returns:
            Loaded module or None if invalid.
        """
        if not path.exists():
            return None

        try:
            content = path.read_text()
            name = path.stem  # filename without extension
            return Module(
                name=name,
                content=content,
                source=source,
            )
        except (OSError, UnicodeDecodeError):
            return None

    def get_module_diff(self, name: str, new_content: str) -> ModuleDiff:
        """Get diff between current and new module content.

        Args:
            name: Module name.
            new_content: New content to compare.

        Returns:
            ModuleDiff describing changes.
        """
        try:
            module = self.get_module(name)
            old_content = module.content
        except ModuleNotFoundError:
            old_content = None

        return ModuleDiff(
            module_name=name,
            old_content=old_content,
            new_content=new_content,
        )
