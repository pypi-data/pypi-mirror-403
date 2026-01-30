"""Tests for CLI interface."""

from pathlib import Path

from typer.testing import CliRunner

from mdstruct.cli import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent / "fixtures"
INPUTS_DIR = FIXTURES_DIR / "inputs"


class TestCLISplit:
    """Test split command."""

    def test_split_basic(self, actual_path, monkeypatch):
        """Test basic split command."""
        monkeypatch.chdir(actual_path)

        # Copy input file to actual_path
        input_file = actual_path / "test.md"
        input_file.write_text((INPUTS_DIR / "simple.md").read_text())

        result = runner.invoke(app, ["split", "test.md"])

        assert result.exit_code == 0
        assert "Split complete" in result.stdout
        assert (actual_path / "test").is_dir()

    def test_split_without_extension(self, actual_path, monkeypatch):
        """Test split command infers .md extension."""
        monkeypatch.chdir(actual_path)

        input_file = actual_path / "test.md"
        input_file.write_text((INPUTS_DIR / "simple.md").read_text())

        result = runner.invoke(app, ["split", "test"])

        assert result.exit_code == 0
        assert (actual_path / "test").is_dir()

    def test_split_with_level(self, actual_path, monkeypatch):
        """Test split command with custom level."""
        monkeypatch.chdir(actual_path)

        input_file = actual_path / "test.md"
        input_file.write_text((INPUTS_DIR / "nested.md").read_text())

        result = runner.invoke(app, ["split", "test", "-l", "3"])

        assert result.exit_code == 0
        # Should have deeper nesting
        assert any((actual_path / "test").rglob("*/*/*.md"))

    def test_split_nonexistent_file(self, actual_path, monkeypatch):
        """Test split command with nonexistent file."""
        monkeypatch.chdir(actual_path)

        result = runner.invoke(app, ["split", "nonexistent.md"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestCLIJoin:
    """Test join command."""

    def test_join_basic(self, actual_path, monkeypatch):
        """Test basic join command."""
        monkeypatch.chdir(actual_path)

        # First split
        input_file = actual_path / "test.md"
        input_file.write_text((INPUTS_DIR / "simple.md").read_text())
        runner.invoke(app, ["split", "test.md"])

        # Original file was moved to /tmp by split command, so it's already gone

        # Then join
        result = runner.invoke(app, ["join", "test"])

        assert result.exit_code == 0
        assert "Join complete" in result.stdout
        assert (actual_path / "test.md").exists()

    def test_join_with_trailing_slash(self, actual_path, monkeypatch):
        """Test join command handles trailing slash."""
        monkeypatch.chdir(actual_path)

        # Create split structure
        input_file = actual_path / "test.md"
        input_file.write_text((INPUTS_DIR / "simple.md").read_text())
        runner.invoke(app, ["split", "test", "--force"])

        result = runner.invoke(app, ["join", "test/", "--force"])

        assert result.exit_code == 0
        assert (actual_path / "test.md").exists()

    def test_join_nonexistent_dir(self, actual_path, monkeypatch):
        """Test join command with nonexistent directory."""
        monkeypatch.chdir(actual_path)

        result = runner.invoke(app, ["join", "nonexistent"])

        assert result.exit_code == 1
        assert "Error" in result.stdout


class TestCLIVersion:
    """Test version command."""

    def test_version_flag(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert "mdstruct version" in result.stdout

    def test_version_short_flag(self):
        """Test -v flag."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert "mdstruct version" in result.stdout
