"""Create command for dd-dm."""

from pathlib import Path
from typing import Annotated

import typer

from dd_dm.core.config import ConfigManager
from dd_dm.core.constitution import ConstitutionManager
from dd_dm.core.module_manager import ModuleManager
from dd_dm.utils.console import print_error, print_info, print_success
from dd_dm.utils.paths import safe_filename


def create_command(
    name: Annotated[
        str,
        typer.Argument(help="Name for the new module"),
    ],
    add_to_constitution: Annotated[
        bool,
        typer.Option("--add", "-a", help="Add to constitution immediately"),
    ] = False,
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path"),
    ] = None,
) -> None:
    """Create a new custom local module.

    Local modules are stored in .dd-dm/local/ and are project-specific.
    They are NOT pushed to the templates repository.
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

    # Sanitize module name
    module_name = safe_filename(name)
    if not module_name:
        print_error("Invalid module name. Use alphanumeric characters and underscores.")
        raise typer.Exit(1)

    # Check if module already exists
    module_path = config_manager.local_dir / f"{module_name}.md"
    if module_path.exists():
        print_error(f"Local module '{module_name}' already exists.")
        print_info(f"File: {module_path}")
        raise typer.Exit(1)

    try:
        # Create the module
        module_manager.create_local_module(module_name)
        print_success(f"Created local module: {module_path}")

        # Update local config
        if module_name not in config.local.custom_modules:
            config.local.custom_modules.append(module_name)
            config_manager.save(config)

        # Add to constitution if requested
        if add_to_constitution:
            module_manager.add_module(module_name, config)
            config_manager.save(config)
            constitution_manager.write(config)
            print_success(f"Added '{module_name}' to constitution")
        else:
            print_info("")
            print_info("To add this module to your constitution:")
            print_info(f"  dd-dm add {module_name}")

        print_info("")
        print_info(f"Edit your module at: {module_path}")

    except Exception as e:
        print_error(f"Failed to create module: {e}")
        raise typer.Exit(1)
