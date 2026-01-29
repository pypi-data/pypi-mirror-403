"""Unit tests for git operations."""

from pathlib import Path

import pytest

from dd_dm.core.exceptions import GitError
from dd_dm.core.git_ops import GitOperations, GitResult


class TestGitResult:
    """Tests for GitResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful result properties."""
        result = GitResult(
            success=True,
            stdout="output",
            stderr="",
            return_code=0,
        )
        assert result.success is True
        assert result.stdout == "output"
        assert result.return_code == 0

    def test_failure_result(self) -> None:
        """Test failure result properties."""
        result = GitResult(
            success=False,
            stdout="",
            stderr="error message",
            return_code=1,
        )
        assert result.success is False
        assert result.stderr == "error message"
        assert result.return_code == 1


class TestGitOperations:
    """Tests for GitOperations class."""

    def test_init(self, temp_project: Path) -> None:
        """Test GitOperations initialization."""
        git = GitOperations(temp_project)
        assert git.repo_path == temp_project

    def test_is_git_repo_false(self, temp_project: Path) -> None:
        """Test is_git_repo returns False for non-repo."""
        git = GitOperations(temp_project)
        assert not git.is_git_repo()

    def test_is_git_repo_true(self, temp_git_repo: Path) -> None:
        """Test is_git_repo returns True for repo."""
        git = GitOperations(temp_git_repo)
        assert git.is_git_repo()

    def test_status_empty_repo(self, temp_git_repo: Path) -> None:
        """Test status on empty repo."""
        git = GitOperations(temp_git_repo)
        result = git.status()
        assert result.success
        # Empty repo, no files
        assert result.stdout == ""

    def test_status_with_untracked_file(self, temp_git_repo: Path) -> None:
        """Test status with untracked file."""
        git = GitOperations(temp_git_repo)
        (temp_git_repo / "test.txt").write_text("hello")

        result = git.status()
        assert result.success
        assert "test.txt" in result.stdout

    def test_is_dirty_false(self, temp_git_repo: Path) -> None:
        """Test is_dirty returns False for clean repo."""
        git = GitOperations(temp_git_repo)
        assert not git.is_dirty()

    def test_is_dirty_true(self, temp_git_repo: Path) -> None:
        """Test is_dirty returns True with changes."""
        git = GitOperations(temp_git_repo)
        (temp_git_repo / "test.txt").write_text("hello")
        assert git.is_dirty()

    def test_add_file(self, temp_git_repo: Path) -> None:
        """Test staging a file."""
        git = GitOperations(temp_git_repo)
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("hello")

        result = git.add("test.txt")
        assert result.success

        # Verify file is staged
        diff_result = git.diff(cached=True, name_only=True)
        assert "test.txt" in diff_result.stdout

    def test_commit(self, temp_git_repo: Path) -> None:
        """Test creating a commit."""
        git = GitOperations(temp_git_repo)
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("hello")

        git.add("test.txt")
        result = git.commit("test: initial commit")

        assert result.success
        assert not git.is_dirty()

    def test_get_current_branch(self, temp_git_repo: Path) -> None:
        """Test getting current branch name."""
        git = GitOperations(temp_git_repo)
        # Create initial commit to have a branch
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("hello")
        git.add("test.txt")
        git.commit("initial commit")

        branch = git.get_current_branch()
        # Could be 'main' or 'master' depending on git config
        assert branch in ("main", "master")

    def test_run_raises_on_failure(self, temp_git_repo: Path) -> None:
        """Test _run raises GitError on failure when check=True."""
        git = GitOperations(temp_git_repo)
        with pytest.raises(GitError, match="Git command failed"):
            git._run("invalid-command-that-does-not-exist")

    def test_diff_empty(self, temp_git_repo: Path) -> None:
        """Test diff on clean repo."""
        git = GitOperations(temp_git_repo)
        result = git.diff()
        assert result.success
        assert result.stdout == ""

    def test_diff_with_changes(self, temp_git_repo: Path) -> None:
        """Test diff with changes."""
        git = GitOperations(temp_git_repo)
        test_file = temp_git_repo / "test.txt"
        test_file.write_text("hello")
        git.add("test.txt")
        git.commit("initial")

        test_file.write_text("hello world")
        result = git.diff()

        assert result.success
        assert "hello world" in result.stdout
