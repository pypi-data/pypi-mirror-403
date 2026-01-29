"""Git operations wrapper using subprocess."""

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from dd_dm.core.exceptions import GitError


@dataclass
class GitResult:
    """Result of a git operation."""

    success: bool
    stdout: str
    stderr: str
    return_code: int


class GitOperations:
    """Wrapper for git operations using subprocess."""

    def __init__(self, repo_path: Path) -> None:
        """Initialize git operations for a repository.

        Args:
            repo_path: Path to the git repository.
        """
        self.repo_path = repo_path

    def _run(
        self,
        *args: str,
        check: bool = True,
        capture_output: bool = True,
    ) -> GitResult:
        """Execute a git command.

        Args:
            *args: Git command arguments.
            check: Whether to raise on non-zero exit.
            capture_output: Whether to capture stdout/stderr.

        Returns:
            GitResult with command output.

        Raises:
            GitError: If command fails and check is True.
        """
        cmd: Sequence[str] = ["git", *args]
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            git_result = GitResult(
                success=result.returncode == 0,
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                return_code=result.returncode,
            )
            if check and not git_result.success:
                raise GitError(
                    f"Git command failed: git {' '.join(args)}\n{git_result.stderr}"
                )
            return git_result
        except FileNotFoundError:
            raise GitError("Git is not installed or not in PATH") from None

    def clone(
        self,
        url: str,
        target_dir: Path | None = None,
        branch: str = "main",
    ) -> GitResult:
        """Clone a repository.

        Args:
            url: Repository URL to clone.
            target_dir: Target directory for clone.
            branch: Branch to checkout.

        Returns:
            GitResult from the clone operation.
        """
        args = ["clone", "--branch", branch, "--single-branch", url]
        if target_dir:
            args.append(str(target_dir))
        return self._run(*args)

    def pull(self, force: bool = False) -> GitResult:
        """Pull changes from remote.

        Args:
            force: If True, reset to remote HEAD.

        Returns:
            GitResult from the pull operation.
        """
        if force:
            self._run("fetch", "--all")
            return self._run("reset", "--hard", "origin/HEAD")
        return self._run("pull")

    def push(self, force: bool = False) -> GitResult:
        """Push changes to remote.

        Args:
            force: If True, force push.

        Returns:
            GitResult from the push operation.
        """
        args = ["push"]
        if force:
            args.append("--force")
        return self._run(*args)

    def fetch(self) -> GitResult:
        """Fetch from remote.

        Returns:
            GitResult from the fetch operation.
        """
        return self._run("fetch")

    def status(self, porcelain: bool = True) -> GitResult:
        """Get repository status.

        Args:
            porcelain: Use porcelain format for easier parsing.

        Returns:
            GitResult with status output.
        """
        args = ["status"]
        if porcelain:
            args.append("--porcelain")
        return self._run(*args)

    def diff(self, cached: bool = False, name_only: bool = False) -> GitResult:
        """Get diff of changes.

        Args:
            cached: Show staged changes.
            name_only: Only show file names.

        Returns:
            GitResult with diff output.
        """
        args = ["diff"]
        if cached:
            args.append("--cached")
        if name_only:
            args.append("--name-only")
        return self._run(*args)

    def add(self, *paths: str) -> GitResult:
        """Stage files for commit.

        Args:
            *paths: Paths to stage.

        Returns:
            GitResult from the add operation.
        """
        return self._run("add", *paths)

    def commit(self, message: str) -> GitResult:
        """Create a commit.

        Args:
            message: Commit message.

        Returns:
            GitResult from the commit operation.
        """
        return self._run("commit", "-m", message)

    def is_dirty(self) -> bool:
        """Check if working directory has uncommitted changes.

        Returns:
            True if there are uncommitted changes.
        """
        result = self.status()
        return bool(result.stdout)

    def has_remote_changes(self) -> bool:
        """Check if remote has changes not pulled locally.

        Returns:
            True if remote has unpulled changes.
        """
        self.fetch()
        result = self._run("rev-list", "HEAD...origin/HEAD", "--count", check=False)
        if not result.success:
            return False
        try:
            return int(result.stdout) > 0
        except ValueError:
            return False

    def get_current_branch(self) -> str:
        """Get the current branch name.

        Returns:
            Current branch name.
        """
        result = self._run("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout

    def is_git_repo(self) -> bool:
        """Check if the path is a git repository.

        Returns:
            True if the path is inside a git repository.
        """
        result = self._run("rev-parse", "--git-dir", check=False)
        return result.success
