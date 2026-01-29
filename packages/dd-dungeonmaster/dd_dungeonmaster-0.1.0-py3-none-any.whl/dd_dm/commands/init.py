"""Init command for dd-dm."""

import shutil
from importlib import resources
from pathlib import Path
from typing import Annotated

import typer

from dd_dm.core.config import ConfigManager
from dd_dm.core.constitution import ConstitutionManager
from dd_dm.core.module_manager import ModuleManager
from dd_dm.models.config import Config
from dd_dm.utils.console import print_error, print_info, print_success


def init_command(
    project_path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Project path (default: cwd)"),
    ] = None,
) -> None:
    """Initialize dd-dm in the current project.

    This sets up the .dd-dm directory structure and copies bundled templates
    containing CONSTITUTION.md, CLAUDE.md, AGENTS.md, and default modules.
    """
    project_root = project_path or Path.cwd()
    config_manager = ConfigManager(project_root)

    # Check if already initialized
    if config_manager.is_initialized():
        print_error(f"dd-dm is already initialized in {project_root}")
        raise typer.Exit(1)

    print_info("Initializing dd-dm...")

    try:
        # Create directory structure
        config_manager.init_directories()
        print_success("Created .dd-dm directory structure")

        # Copy bundled templates to cache
        _copy_bundled_templates(config_manager.cache_dir)
        print_success("Copied bundled templates")

        # Create config
        config = Config()
        config_manager.save(config)
        print_success("Created configuration file")

        # Copy template files to project root
        module_manager = ModuleManager(config_manager)
        constitution_manager = ConstitutionManager(config_manager, module_manager)
        constitution_manager.copy_template_files()
        print_success("Copied template files to project root")

        # Write initial constitution
        constitution_manager.write(config)
        print_success("Generated CONSTITUTION.md")

        print_success(f"dd-dm initialized successfully in {project_root}")
        print_info("")
        print_info("Next steps:")
        print_info("  dd-dm add <module-name>  - Add a module to your constitution")
        print_info("  dd-dm create <name>      - Create a custom local module")
        print_info("  dd-dm update --force     - Refresh templates to latest version")

    except Exception as e:
        # Clean up on failure
        if config_manager.config_dir.exists():
            shutil.rmtree(config_manager.config_dir)
        print_error(f"Initialization failed: {e}")
        raise typer.Exit(1)


def _copy_bundled_templates(dest: Path) -> None:
    """Copy bundled templates to the destination directory.

    Args:
        dest: Destination directory for templates.
    """
    templates_package = resources.files("dd_dm.templates")

    # Copy top-level template files
    for item in templates_package.iterdir():
        if item.is_file():
            dest_file = dest / item.name
            dest_file.write_bytes(item.read_bytes())
        elif item.name == "modules":
            # Copy modules directory
            modules_dest = dest / "modules"
            modules_dest.mkdir(parents=True, exist_ok=True)
            for module_file in item.iterdir():
                if module_file.is_file():
                    (modules_dest / module_file.name).write_bytes(
                        module_file.read_bytes()
                    )
