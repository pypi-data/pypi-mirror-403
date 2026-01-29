"""Shared test fixtures for dd-dm tests."""

from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def temp_project() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_git_repo(temp_project: Path) -> Path:
    """Create a temporary git repository for testing."""
    import subprocess

    subprocess.run(["git", "init"], cwd=temp_project, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    return temp_project
