"""Add command for dd-dm."""

from pathlib import Path
from typing import Annotated

import typer

from dd_dm.core.config import ConfigManager
from dd_dm.core.constitution import ConstitutionManager
from dd_dm.core.exceptions import ModuleAlreadyExistsError, ModuleNotFoundDDDMError
from dd_dm.core.module_manager import ModuleManager
from dd_dm.utils.console import (
    confirm,
    print_diff,
    print_error,
    print_info,
    print_module_list,
    print_success,
)


def add_command(
    module_name: Annotated[
        str | None,
        typer.Argument(help="Name or number of the module to add"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force override if module already exists"),
    ] = False,
    list_modules: Annotated[
        bool,
        typer.Option("--list", "-l", help="List available modules"),
    ] = False,
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path"),
    ] = None,
) -> None:
    """Add a module to the constitution.

    You can specify the module by name or by its number from the list.
    If the module is already enabled and the content differs, you'll be asked
    to confirm the override. Use --force to skip confirmation.
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

    # Get available modules (needed for both listing and number resolution)
    modules = module_manager.list_available_modules()

    # List modules if requested or no module specified
    if list_modules or module_name is None:
        if not modules:
            print_info("No modules available.")
            raise typer.Exit(0)

        module_data = [
            (m.name, m.source.value, module_manager.is_module_enabled(m.name, config))
            for m in modules
        ]
        print_module_list(module_data)

        if module_name is None:
            raise typer.Exit(0)

    # Resolve module_name if it's a number
    if module_name is not None and module_name.isdigit():
        module_num = int(module_name)
        if module_num < 1 or module_num > len(modules):
            print_error(f"Invalid module number: {module_num}")
            print_info(f"Please choose a number between 1 and {len(modules)}.")
            raise typer.Exit(1)
        module_name = modules[module_num - 1].name

    try:
        # Check if module exists
        module = module_manager.get_module(module_name)

        # Check if already enabled with different content
        if module_manager.is_module_enabled(module_name, config) and not force:
            print_info(f"Module '{module_name}' is already enabled.")
            print_info("Use --force to override with the latest version.")

            # Show diff
            diff = module_manager.get_module_diff(module_name, module.content)
            if diff.has_changes:
                print_diff(diff.old_content, diff.new_content, module_name)
                if not confirm("Do you want to override?"):
                    print_info("Aborted.")
                    raise typer.Exit(0)
            else:
                print_info("Content is identical. No changes needed.")
                raise typer.Exit(0)

        # Add the module
        diff = module_manager.add_module(module_name, config, force=force)
        config_manager.save(config)

        # Regenerate constitution
        constitution_manager.write(config)

        if diff.is_addition:
            print_success(f"Added module '{module_name}' to constitution")
        else:
            print_success(f"Updated module '{module_name}' in constitution")

    except ModuleNotFoundDDDMError as e:
        print_error(str(e))
        print_info("Use 'dd-dm add --list' to see available modules.")
        raise typer.Exit(1)
    except ModuleAlreadyExistsError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to add module: {e}")
        raise typer.Exit(1)
