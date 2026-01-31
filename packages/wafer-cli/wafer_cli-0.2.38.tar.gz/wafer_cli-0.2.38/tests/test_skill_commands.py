"""Unit tests for wafer skill commands.

Tests skill installation, uninstallation, and status for Claude Code, Codex CLI, and Cursor.

Run with: PYTHONPATH=apps/wafer-cli uv run pytest apps/wafer-cli/tests/test_skill_commands.py -v
"""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from wafer.cli import app

runner = CliRunner()


@pytest.fixture
def mock_home(tmp_path: Path, monkeypatch) -> Path:
    """Create a temporary home directory for testing."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    # Set HOME environment variable
    monkeypatch.setenv("HOME", str(home_dir))
    return home_dir


@pytest.fixture
def skill_source(tmp_path: Path) -> Path:
    """Create a test skill source directory matching the expected structure."""
    # Create the structure: wafer/skills/wafer-guide/
    skill_dir = tmp_path / "wafer" / "skills" / "wafer-guide"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(
        "---\n"
        "name: wafer-guide\n"
        "description: Test skill\n"
        "---\n"
        "# Test Skill\n"
        "Test content\n"
    )
    return skill_dir


@pytest.fixture
def mock_cli_file_path(skill_source: Path, tmp_path: Path):
    """Create a mock __file__ path that points to the skill source."""
    # Create a fake cli.py path that when resolved gives us access to skill_source
    fake_cli_dir = tmp_path / "fake_wafer"
    fake_cli_file = fake_cli_dir / "cli.py"
    fake_cli_file.parent.mkdir(parents=True)
    
    # Create the skills directory structure
    (fake_cli_dir / "skills" / "wafer-guide").mkdir(parents=True)
    # Copy skill file
    shutil.copytree(skill_source, fake_cli_dir / "skills" / "wafer-guide", dirs_exist_ok=True)
    
    return fake_cli_file


class TestSkillInstall:
    """Test wafer skill install command."""

    def test_install_cursor_only(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should install skill for Cursor only."""
        cursor_skill_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        
        # Patch Path(__file__) to return our mock cli file
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "install", "-t", "cursor"])
        
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert "Cursor" in result.stdout
        assert cursor_skill_path.exists()
        assert cursor_skill_path.is_symlink()
        assert cursor_skill_path.resolve() == skill_source.resolve()

    def test_install_all_targets(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should install skill for all targets."""
        claude_path = mock_home / ".claude" / "skills" / "wafer-guide"
        codex_path = mock_home / ".codex" / "skills" / "wafer-guide"
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "install"])
        
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert claude_path.exists()
        assert codex_path.exists()
        assert cursor_path.exists()
        assert all(p.is_symlink() for p in [claude_path, codex_path, cursor_path])
        assert all(p.resolve() == skill_source.resolve() for p in [claude_path, codex_path, cursor_path])

    def test_install_already_exists_no_force(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should skip installation if skill already exists without --force."""
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        cursor_path.parent.mkdir(parents=True)
        cursor_path.mkdir()  # Create existing directory
        
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "install", "-t", "cursor"])
        
        assert result.exit_code == 0
        assert "Already installed" in result.stdout
        assert "Use --force" in result.stdout

    def test_install_with_force_overwrites(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should overwrite existing skill with --force."""
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        cursor_path.parent.mkdir(parents=True)
        cursor_path.mkdir()
        (cursor_path / "old_file.txt").write_text("old content")
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "install", "-t", "cursor", "--force"])
        
        assert result.exit_code == 0
        assert cursor_path.exists()
        assert cursor_path.is_symlink()
        assert cursor_path.resolve() == skill_source.resolve()
        assert not (cursor_path / "old_file.txt").exists()

    def test_install_invalid_target(self) -> None:
        """Should fail with invalid target."""
        result = runner.invoke(app, ["skill", "install", "-t", "invalid"])
        
        assert result.exit_code != 0
        assert "Unknown target" in result.output

    def test_install_missing_skill_source(self, mock_home: Path, tmp_path: Path) -> None:
        """Should fail if skill source doesn't exist."""
        # Create a cli.py path but don't create the skills directory
        fake_cli_file = tmp_path / "fake_wafer" / "cli.py"
        fake_cli_file.parent.mkdir(parents=True)
        
        with patch("wafer.cli.__file__", str(fake_cli_file)):
            result = runner.invoke(app, ["skill", "install", "-t", "cursor"])
        
        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "Error" in result.output


class TestSkillUninstall:
    """Test wafer skill uninstall command."""

    def test_uninstall_cursor(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should uninstall skill from Cursor."""
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        cursor_path.parent.mkdir(parents=True)
        cursor_path.symlink_to(skill_source)
        
        result = runner.invoke(app, ["skill", "uninstall", "-t", "cursor"])
        
        assert result.exit_code == 0
        assert "Uninstalled" in result.stdout
        assert not cursor_path.exists()

    def test_uninstall_not_installed(self, mock_home: Path) -> None:
        """Should handle uninstalling when skill is not installed."""
        result = runner.invoke(app, ["skill", "uninstall", "-t", "cursor"])
        
        assert result.exit_code == 0
        assert "Not installed" in result.stdout

    def test_uninstall_all_targets(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should uninstall from all targets."""
        claude_path = mock_home / ".claude" / "skills" / "wafer-guide"
        codex_path = mock_home / ".codex" / "skills" / "wafer-guide"
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        
        for path in [claude_path, codex_path, cursor_path]:
            path.parent.mkdir(parents=True)
            path.symlink_to(skill_source)
        
        result = runner.invoke(app, ["skill", "uninstall"])
        
        assert result.exit_code == 0
        assert not claude_path.exists()
        assert not codex_path.exists()
        assert not cursor_path.exists()


class TestSkillStatus:
    """Test wafer skill status command."""

    def test_status_not_installed(self, mock_home: Path, mock_cli_file_path: Path) -> None:
        """Should show status when skill is not installed."""
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "status"])
        
        assert result.exit_code == 0
        assert "Not installed" in result.stdout
        assert "Claude Code" in result.stdout
        assert "Codex CLI" in result.stdout
        assert "Cursor" in result.stdout

    def test_status_installed(
        self, mock_home: Path, mock_cli_file_path: Path
    ) -> None:
        """Should show status when skill is installed."""
        cursor_path = mock_home / ".cursor" / "skills" / "wafer-guide"
        skill_source = mock_cli_file_path.parent / "skills" / "wafer-guide"
        cursor_path.parent.mkdir(parents=True)
        cursor_path.symlink_to(skill_source)
        
        with patch("wafer.cli.__file__", str(mock_cli_file_path)):
            result = runner.invoke(app, ["skill", "status"])
        
        assert result.exit_code == 0
        assert "Installed" in result.stdout
        assert "Cursor" in result.stdout
