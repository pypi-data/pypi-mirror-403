"""Remove command for dd-dm."""

from pathlib import Path
from typing import Annotated

import typer

from dd_dm.core.config import ConfigManager
from dd_dm.core.constitution import ConstitutionManager
from dd_dm.core.exceptions import ModuleNotFoundDDDMError
from dd_dm.core.module_manager import ModuleManager
from dd_dm.utils.console import (
    confirm,
    print_error,
    print_info,
    print_module_list,
    print_success,
)


def remove_command(
    module_name: Annotated[
        str | None,
        typer.Argument(help="Name or number of the module to remove"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Skip confirmation"),
    ] = False,
    list_modules: Annotated[
        bool,
        typer.Option("--list", "-l", help="List enabled modules"),
    ] = False,
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path"),
    ] = None,
) -> None:
    """Remove a module from the constitution.

    You can specify the module by name or by its number from the list.
    This removes the module section from CONSTITUTION.md. The module file
    itself is not deleted and can be re-added later.
    """
    project_root = project_path or Path.cwd()
    config_manager = ConfigManager(project_root)

    try:
        config_manager.ensure_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = config_manager.load()
    module_manager = ModuleManager(config_manager)
    constitution_manager = ConstitutionManager(config_manager, module_manager)

    # Get enabled modules (needed for both listing and number resolution)
    enabled_names = list(config.modules.enabled)
    enabled_modules = []
    for name in enabled_names:
        try:
            module = module_manager.get_module(name)
            enabled_modules.append((name, module.source.value, True))
        except ModuleNotFoundDDDMError:
            # Module file may have been deleted, still show it
            enabled_modules.append((name, "unknown", True))

    # List modules if requested or no module specified
    if list_modules or module_name is None:
        if not enabled_modules:
            print_info("No modules are currently enabled.")
            raise typer.Exit(0)

        print_module_list(enabled_modules, title="Enabled Modules")

        if module_name is None:
            raise typer.Exit(0)

    # Resolve module_name if it's a number
    if module_name is not None and module_name.isdigit():
        module_num = int(module_name)
        if module_num < 1 or module_num > len(enabled_modules):
            print_error(f"Invalid module number: {module_num}")
            print_info(f"Please choose a number between 1 and {len(enabled_modules)}.")
            raise typer.Exit(1)
        module_name = enabled_modules[module_num - 1][0]

    # Check if module is enabled
    if not module_manager.is_module_enabled(module_name, config):
        print_error(f"Module '{module_name}' is not enabled.")
        print_info(f"Enabled modules: {', '.join(enabled_names) or 'none'}")
        raise typer.Exit(1)

    # Confirm deletion
    if not force:
        if not confirm(f"Remove module '{module_name}' from constitution?"):
            print_info("Aborted.")
            raise typer.Exit(0)

    try:
        # Remove the module
        module_manager.remove_module(module_name, config)
        config_manager.save(config)

        # Regenerate constitution
        constitution_manager.write(config)

        print_success(f"Removed module '{module_name}' from constitution")

    except ModuleNotFoundDDDMError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to remove module: {e}")
        raise typer.Exit(1)
