"""List command for dd-dm."""

from pathlib import Path
from typing import Annotated

import typer

from dd_dm.core.config import ConfigManager
from dd_dm.core.module_manager import ModuleManager
from dd_dm.utils.console import print_error, print_info, print_module_list


def list_command(
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path"),
    ] = None,
) -> None:
    """List available modules and their status."""
    project_root = project_path or Path.cwd()
    config_manager = ConfigManager(project_root)

    try:
        config_manager.ensure_initialized()
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)

    config = config_manager.load()
    module_manager = ModuleManager(config_manager)

    modules = module_manager.list_available_modules()
    if not modules:
        print_info("No modules available.")
        raise typer.Exit(0)

    module_data = [
        (m.name, m.source.value, module_manager.is_module_enabled(m.name, config))
        for m in modules
    ]
    print_module_list(module_data, show_numbers=False)
