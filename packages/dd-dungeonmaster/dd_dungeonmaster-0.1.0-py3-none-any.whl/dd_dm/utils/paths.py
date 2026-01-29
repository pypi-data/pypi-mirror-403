"""Path utilities for dd-dm."""

import re
from pathlib import Path


def find_project_root(start_path: Path | None = None) -> Path | None:
    """Find the project root by looking for .dd-dm directory.

    Args:
        start_path: Starting directory. Defaults to cwd.

    Returns:
        Project root path or None if not found.
    """
    current = start_path or Path.cwd()
    current = current.resolve()

    while current != current.parent:
        if (current / ".dd-dm").exists():
            return current
        current = current.parent

    # Check root
    if (current / ".dd-dm").exists():
        return current

    return None


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists.

    Args:
        path: Directory path.

    Returns:
        The path (for chaining).
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Convert a string to a safe filename.

    Args:
        name: Original name.

    Returns:
        Safe filename.
    """
    # Replace spaces with underscores
    safe = name.replace(" ", "_")
    # Remove characters that are not alphanumeric, underscore, or hyphen
    safe = re.sub(r"[^\w\-]", "", safe)
    # Convert to uppercase
    safe = safe.upper()
    return safe
