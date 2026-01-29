"""Integration tests for CLI commands."""

from pathlib import Path

from typer.testing import CliRunner

from dd_dm.cli import app

runner = CliRunner()


class TestInitCommand:
    """Tests for init command."""

    def test_init_success(self, temp_project: Path) -> None:
        """Test successful initialization."""
        result = runner.invoke(app, ["init", "--path", str(temp_project)])

        assert result.exit_code == 0
        assert "initialized successfully" in result.output

        # Verify files were created
        assert (temp_project / ".dd-dm").exists()
        assert (temp_project / ".dd-dm" / "config.toml").exists()
        assert (temp_project / "CONSTITUTION.md").exists()
        assert (temp_project / "CLAUDE.md").exists()
        assert (temp_project / "AGENTS.md").exists()

    def test_init_already_initialized(self, temp_project: Path) -> None:
        """Test init fails if already initialized."""
        # First init
        runner.invoke(app, ["init", "--path", str(temp_project)])

        # Second init should fail
        result = runner.invoke(app, ["init", "--path", str(temp_project)])

        assert result.exit_code != 0
        assert "already initialized" in result.output


class TestAddCommand:
    """Tests for add command."""

    def test_add_not_initialized(self, temp_project: Path) -> None:
        """Test add fails when not initialized."""
        result = runner.invoke(
            app, ["add", "GIT_CONVENTIONAL_COMMITS", "--path", str(temp_project)]
        )
        assert result.exit_code != 0
        assert "not initialized" in result.output

    def test_add_list_modules(self, temp_project: Path) -> None:
        """Test listing available modules."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(app, ["add", "--list", "--path", str(temp_project)])

        assert result.exit_code == 0
        assert "GIT_CONVENTIONAL_COMMITS" in result.output

    def test_add_module(self, temp_project: Path) -> None:
        """Test adding a module."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(
            app, ["add", "GIT_CONVENTIONAL_COMMITS", "--path", str(temp_project)]
        )

        assert result.exit_code == 0
        assert "Added module" in result.output

        # Verify module is in constitution
        constitution = (temp_project / "CONSTITUTION.md").read_text()
        assert "Conventional Commits" in constitution

    def test_add_module_not_found(self, temp_project: Path) -> None:
        """Test adding non-existent module fails."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(
            app, ["add", "NON_EXISTENT", "--path", str(temp_project)]
        )

        assert result.exit_code != 0
        assert "not found" in result.output


class TestRemoveCommand:
    """Tests for remove command."""

    def test_remove_not_initialized(self, temp_project: Path) -> None:
        """Test remove fails when not initialized."""
        result = runner.invoke(
            app, ["remove", "GIT_CONVENTIONAL_COMMITS", "--path", str(temp_project)]
        )
        assert result.exit_code != 0
        assert "not initialized" in result.output

    def test_remove_not_enabled(self, temp_project: Path) -> None:
        """Test remove fails for module that's not enabled."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(
            app,
            [
                "remove",
                "GIT_CONVENTIONAL_COMMITS",
                "--force",
                "--path",
                str(temp_project),
            ],
        )

        assert result.exit_code != 0
        assert "not enabled" in result.output

    def test_remove_module(self, temp_project: Path) -> None:
        """Test removing a module."""
        runner.invoke(app, ["init", "--path", str(temp_project)])
        runner.invoke(
            app, ["add", "GIT_CONVENTIONAL_COMMITS", "--path", str(temp_project)]
        )

        result = runner.invoke(
            app,
            [
                "remove",
                "GIT_CONVENTIONAL_COMMITS",
                "--force",
                "--path",
                str(temp_project),
            ],
        )

        assert result.exit_code == 0
        assert "Removed module" in result.output

        # Verify module is not in constitution
        constitution = (temp_project / "CONSTITUTION.md").read_text()
        assert "Conventional Commits" not in constitution


class TestCreateCommand:
    """Tests for create command."""

    def test_create_not_initialized(self, temp_project: Path) -> None:
        """Test create fails when not initialized."""
        result = runner.invoke(
            app, ["create", "MY_MODULE", "--path", str(temp_project)]
        )
        assert result.exit_code != 0
        assert "not initialized" in result.output

    def test_create_module(self, temp_project: Path) -> None:
        """Test creating a local module."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(
            app, ["create", "MY_CUSTOM_MODULE", "--path", str(temp_project)]
        )

        assert result.exit_code == 0
        assert "Created local module" in result.output

        # Verify module file exists
        assert (temp_project / ".dd-dm" / "local" / "MY_CUSTOM_MODULE.md").exists()

    def test_create_and_add(self, temp_project: Path) -> None:
        """Test creating and immediately adding a module."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(
            app, ["create", "MY_MODULE", "--add", "--path", str(temp_project)]
        )

        assert result.exit_code == 0
        assert "Created local module" in result.output
        assert "Added" in result.output

        # Verify module is in constitution
        constitution = (temp_project / "CONSTITUTION.md").read_text()
        assert "MY_MODULE" in constitution


class TestUpdateCommand:
    """Tests for update command."""

    def test_update_shows_info(self) -> None:
        """Test update command shows version info."""
        result = runner.invoke(app, ["update"])

        assert result.exit_code == 0
        assert "Current version" in result.output

    def test_update_force_refreshes_templates(self, temp_project: Path) -> None:
        """Test update --force refreshes templates."""
        runner.invoke(app, ["init", "--path", str(temp_project)])

        result = runner.invoke(app, ["update", "--force", "--path", str(temp_project)])

        assert result.exit_code == 0
        assert "Refreshed cached templates" in result.output
        assert "Regenerated" in result.output
