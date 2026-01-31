"""Tests for the paxx CLI."""

import os

from typer.testing import CliRunner

from paxx.cli.main import app

runner = CliRunner()


def test_version_flag():
    """Test that the --version flag outputs the version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip()  # outputs version number


def test_version_flag_short():
    """Test that the -v flag outputs the version."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert result.stdout.strip()  # outputs version number


def test_help():
    """Test that --help shows help text."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "paxx" in result.stdout


class TestBootstrap:
    """Tests for the bootstrap command."""

    def test_bootstrap_new_project(self, temp_dir):
        """Test bootstrapping a new project in a fresh directory."""
        result = runner.invoke(app, ["bootstrap", "myproject", "-o", str(temp_dir)])
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert (temp_dir / "myproject" / "main.py").exists()
        assert (temp_dir / "myproject" / "settings.py").exists()

    def test_bootstrap_existing_empty_dir_with_force(self, temp_dir):
        """Test bootstrapping into an existing empty directory with --force."""
        project_dir = temp_dir / "emptyproject"
        project_dir.mkdir()

        result = runner.invoke(
            app, ["bootstrap", "emptyproject", "-o", str(temp_dir), "--force"]
        )
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert (project_dir / "main.py").exists()

    def test_bootstrap_existing_empty_dir_confirm_yes(self, temp_dir):
        """Test bootstrapping into existing empty dir with user confirmation."""
        project_dir = temp_dir / "emptyproject"
        project_dir.mkdir()

        result = runner.invoke(
            app, ["bootstrap", "emptyproject", "-o", str(temp_dir)], input="y\n"
        )
        assert result.exit_code == 0
        assert "already exists but is empty" in result.stdout
        assert "Project created successfully" in result.stdout

    def test_bootstrap_existing_empty_dir_confirm_no(self, temp_dir):
        """Test declining bootstrap into existing empty directory."""
        project_dir = temp_dir / "emptyproject"
        project_dir.mkdir()

        result = runner.invoke(
            app, ["bootstrap", "emptyproject", "-o", str(temp_dir)], input="n\n"
        )
        assert result.exit_code == 0
        assert "Aborted" in result.stdout
        assert not (project_dir / "main.py").exists()

    def test_bootstrap_existing_nonempty_dir_with_force(self, temp_dir):
        """Test bootstrapping into existing non-empty directory with --force."""
        project_dir = temp_dir / "nonemptyproject"
        project_dir.mkdir()
        (project_dir / "existing_file.txt").write_text("existing content")

        result = runner.invoke(
            app, ["bootstrap", "nonemptyproject", "-o", str(temp_dir), "--force"]
        )
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert (project_dir / "main.py").exists()
        # Existing file should still be there
        assert (project_dir / "existing_file.txt").exists()

    def test_bootstrap_existing_nonempty_dir_confirm_yes(self, temp_dir):
        """Test bootstrapping into non-empty dir with user confirmation."""
        project_dir = temp_dir / "nonemptyproject"
        project_dir.mkdir()
        (project_dir / "somefile.txt").write_text("content")

        result = runner.invoke(
            app, ["bootstrap", "nonemptyproject", "-o", str(temp_dir)], input="y\n"
        )
        assert result.exit_code == 0
        # Normalize whitespace since Rich may wrap long lines
        normalized_output = " ".join(result.stdout.split())
        assert "already exists and contains" in normalized_output
        assert "will be overwritten" in normalized_output
        assert "Project created successfully" in normalized_output

    def test_bootstrap_existing_nonempty_dir_confirm_no(self, temp_dir):
        """Test declining bootstrap into non-empty directory."""
        project_dir = temp_dir / "nonemptyproject"
        project_dir.mkdir()
        (project_dir / "somefile.txt").write_text("content")

        result = runner.invoke(
            app, ["bootstrap", "nonemptyproject", "-o", str(temp_dir)], input="n\n"
        )
        assert result.exit_code == 0
        assert "Aborted" in result.stdout
        assert not (project_dir / "main.py").exists()

    def test_bootstrap_dot_in_existing_dir(self, temp_dir):
        """Test bootstrapping with '.' into an existing directory."""
        project_dir = temp_dir / "mydotproject"
        project_dir.mkdir()

        result = runner.invoke(
            app, ["bootstrap", ".", "-o", str(project_dir), "--force"]
        )
        assert result.exit_code == 0
        assert "Project created successfully" in result.stdout
        assert (project_dir / "main.py").exists()
        # Check that project name was derived from directory
        assert "mydotproject" in result.stdout

    def test_bootstrap_dot_nonexistent_dir_fails(self, temp_dir):
        """Test that '.' fails for non-existent directory."""
        nonexistent = temp_dir / "doesnotexist"

        result = runner.invoke(app, ["bootstrap", ".", "-o", str(nonexistent)])
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_bootstrap_dot_in_current_dir(self, temp_dir):
        """Test bootstrapping with '.' in current directory."""
        project_dir = temp_dir / "currentdirproject"
        project_dir.mkdir()

        # Change to the project directory and bootstrap with "."
        original_cwd = os.getcwd()
        try:
            os.chdir(project_dir)
            result = runner.invoke(app, ["bootstrap", ".", "--force"])
            assert result.exit_code == 0
            assert "Project created successfully" in result.stdout
            assert (project_dir / "main.py").exists()
        finally:
            os.chdir(original_cwd)

    def test_bootstrap_dir_with_only_hidden_files_is_empty(self, temp_dir):
        """Test that directory with only hidden files is considered empty."""
        project_dir = temp_dir / "hiddenonly"
        project_dir.mkdir()
        (project_dir / ".git").mkdir()
        (project_dir / ".gitignore").write_text("*.pyc")

        result = runner.invoke(
            app, ["bootstrap", "hiddenonly", "-o", str(temp_dir), "--force"]
        )
        assert result.exit_code == 0
        # Should be treated as empty (only hidden items)
        assert "already exists but is empty" in result.stdout

    def test_bootstrap_invalid_name_from_dot(self, temp_dir):
        """Test that invalid project name derived from '.' fails."""
        # Create directory with invalid name (starts with number)
        project_dir = temp_dir / "123invalid"
        project_dir.mkdir()

        result = runner.invoke(
            app, ["bootstrap", ".", "-o", str(project_dir), "--force"]
        )
        assert result.exit_code == 1
        assert "must start with a letter" in result.stdout
