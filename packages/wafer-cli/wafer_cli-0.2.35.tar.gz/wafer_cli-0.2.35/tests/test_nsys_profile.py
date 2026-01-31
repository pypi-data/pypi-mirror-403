"""Tests for NSYS profile command."""

from unittest.mock import patch

import pytest

from wafer.nsys_profile import (
    NSYSProfileOptions,
    NSYSProfileResult,
    _build_nsys_command,
    profile_and_analyze,
    profile_local,
)


class TestNSYSProfileOptions:
    """Test NSYSProfileOptions dataclass."""

    def test_create_basic_options(self):
        opts = NSYSProfileOptions(command="./my_kernel")
        assert opts.command == "./my_kernel"
        assert opts.output == "profile"
        assert opts.trace is None
        assert opts.duration is None

    def test_create_full_options(self):
        opts = NSYSProfileOptions(
            command="python train.py",
            output="training_profile",
            trace=["cuda", "nvtx"],
            duration=60,
            extra_args="--capture-range=cudaProfilerApi",
        )
        assert opts.command == "python train.py"
        assert opts.output == "training_profile"
        assert opts.trace == ["cuda", "nvtx"]
        assert opts.duration == 60
        assert opts.extra_args == "--capture-range=cudaProfilerApi"


class TestNSYSProfileResult:
    """Test NSYSProfileResult dataclass."""

    def test_success_result(self):
        result = NSYSProfileResult(
            success=True,
            output_path="/tmp/profile.nsys-rep",
            stdout="Profiling completed",
        )
        assert result.success is True
        assert result.output_path == "/tmp/profile.nsys-rep"
        assert result.error is None

    def test_failure_result(self):
        result = NSYSProfileResult(
            success=False,
            error="NSYS not found",
        )
        assert result.success is False
        assert result.error == "NSYS not found"


class TestBuildNsysCommand:
    """Test _build_nsys_command function."""

    def test_basic_command(self):
        opts = NSYSProfileOptions(command="./my_kernel")
        cmd = _build_nsys_command("/usr/bin/nsys", opts)
        
        assert cmd[0] == "/usr/bin/nsys"
        assert "profile" in cmd
        assert "-o" in cmd
        assert "-t" in cmd

    def test_with_trace_options(self):
        opts = NSYSProfileOptions(command="./my_kernel", trace=["cuda", "nvtx"])
        cmd = _build_nsys_command("/usr/bin/nsys", opts)
        
        idx = cmd.index("-t")
        assert "cuda,nvtx" in cmd[idx + 1]

    def test_with_duration(self):
        opts = NSYSProfileOptions(command="./my_kernel", duration=30)
        cmd = _build_nsys_command("/usr/bin/nsys", opts)
        
        assert "--duration" in cmd
        assert "30" in cmd


class TestProfileLocal:
    """Test profile_local function."""

    def test_nsys_not_installed_raises(self):
        """On macOS (or when nsys missing), profile_local raises FileNotFoundError."""
        opts = NSYSProfileOptions(command="./my_kernel")
        
        # On macOS or when nsys is not installed, it raises
        with pytest.raises(FileNotFoundError):
            profile_local(opts)


class TestProfileWorkspace:
    """Test profile_workspace function - these require workspace setup."""
    
    def test_workspace_profile_options(self):
        """Test that workspace profile accepts correct options."""
        opts = NSYSProfileOptions(
            command="./my_kernel",
            output="my_profile",
            trace=["cuda", "nvtx"],
        )
        assert opts.command == "./my_kernel"
        assert opts.trace == ["cuda", "nvtx"]


class TestProfileAndAnalyze:
    """Test profile_and_analyze function."""

    @patch("wafer.nsys_profile.profile_local")
    def test_profile_fails_no_analyze(self, mock_profile):
        mock_profile.return_value = NSYSProfileResult(
            success=False,
            error="Profiling failed",
        )
        
        opts = NSYSProfileOptions(command="./crash_kernel")
        
        profile_result, analysis_result = profile_and_analyze(opts)
        
        assert profile_result.success is False
        assert analysis_result is None


class TestCLIIntegration:
    """Test CLI command integration."""

    def test_profile_command_help(self):
        """Verify profile command exists and has help text."""
        from typer.testing import CliRunner

        from wafer.cli import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["nvidia", "nsys", "profile", "--help"])
        
        assert result.exit_code == 0
        assert "profile" in result.output.lower()
        assert "--output" in result.output or "-o" in result.output

    def test_profile_command_requires_command(self):
        """Verify profile command requires a command argument."""
        from typer.testing import CliRunner

        from wafer.cli import app
        
        runner = CliRunner()
        result = runner.invoke(app, ["nvidia", "nsys", "profile"])
        
        # Should fail without command argument
        assert result.exit_code != 0 or "Missing argument" in result.output
