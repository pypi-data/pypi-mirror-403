#!/usr/bin/env python3
"""Release script for dd-dungeonmaster.

Usage:
    python scripts/release.py 0.2.0
"""

import re
import subprocess
import sys
from pathlib import Path


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command and return the result."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # noqa: S602
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/release.py <version>")
        print("Example: python scripts/release.py 0.2.0")
        sys.exit(1)

    version = sys.argv[1]

    # Validate version format
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        print(f"Error: Invalid version format '{version}'. Expected x.y.z")
        sys.exit(1)

    # Check we're on main branch
    print("Checking branch...")
    result = run("git branch --show-current")
    branch = result.stdout.strip()
    if branch != "main":
        print(f"Error: Must be on main branch (currently on '{branch}')")
        sys.exit(1)

    # Check working directory is clean
    print("Checking working directory...")
    result = run("git status --porcelain")
    if result.stdout.strip():
        print("Error: Working directory is not clean. Commit or stash changes first.")
        sys.exit(1)

    # Pull latest
    print("Pulling latest...")
    run("git pull")

    # Update version in pyproject.toml
    print(f"Updating version to {version}...")
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    new_content = re.sub(
        r'^version = "[^"]+"',
        f'version = "{version}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if content == new_content:
        print("Error: Failed to update version in pyproject.toml")
        sys.exit(1)
    pyproject_path.write_text(new_content)

    # Commit
    print("Committing...")
    run("git add pyproject.toml")
    run(f'git commit -m "chore: bump version to {version}"')

    # Push
    print("Pushing...")
    run("git push")

    # Create release
    print(f"Creating release v{version}...")
    run(f'gh release create v{version} --title "v{version}" --generate-notes')

    print(f"\nRelease v{version} created successfully!")
    print("Watch the publish workflow: gh run watch")
    print("Verify on PyPI: https://pypi.org/project/dd-dungeonmaster/")


if __name__ == "__main__":
    main()
