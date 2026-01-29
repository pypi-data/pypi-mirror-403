"""Update command for dd-dm."""

from pathlib import Path
from typing import Annotated

import typer

from dd_dm import __version__
from dd_dm.core.config import ConfigManager
from dd_dm.core.constitution import ConstitutionManager
from dd_dm.core.module_manager import ModuleManager
from dd_dm.utils.console import print_error, print_info, print_success


def update_command(
    check: Annotated[
        bool,
        typer.Option("--check", "-c", help="Only check for updates, don't install"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Force regenerate templates from bundled version"
        ),
    ] = False,
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path"),
    ] = None,
) -> None:
    """Update dd-dm to the latest version or refresh templates.

    Use --force to regenerate cached templates from the bundled version.
    This is useful after upgrading dd-dm to get the latest templates.

    To update the tool itself, run:

        uv tool upgrade dd-dm
        # or
        pipx upgrade dd-dm
    """
    if force:
        project_root = project_path or Path.cwd()
        config_manager = ConfigManager(project_root)

        try:
            config_manager.ensure_initialized()
        except Exception as e:
            print_error(str(e))
            raise typer.Exit(1)

        # Import here to avoid circular imports
        from dd_dm.commands.init import _copy_bundled_templates

        # Refresh templates from bundled version
        _copy_bundled_templates(config_manager.cache_dir)
        print_success("Refreshed cached templates from bundled version")

        # Regenerate constitution
        config = config_manager.load()
        module_manager = ModuleManager(config_manager)
        constitution_manager = ConstitutionManager(config_manager, module_manager)
        constitution_manager.copy_template_files()
        constitution_manager.write(config)
        print_success("Regenerated CONSTITUTION.md")

        raise typer.Exit(0)

    # Default behavior: show version info and update instructions
    print_info(f"Current version: {__version__}")
    print_info("")
    print_info("To update the tool:")
    print_info("  uv tool upgrade dd-dm")
    print_info("  pipx upgrade dd-dm")
    print_info("  pip install --upgrade dd-dm")
    print_info("")
    print_info("To refresh templates after upgrading:")
    print_info("  dd-dm update --force")

    raise typer.Exit(0)
