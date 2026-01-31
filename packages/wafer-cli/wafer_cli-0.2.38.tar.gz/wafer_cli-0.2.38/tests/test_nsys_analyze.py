"""Unit tests for NSYS analyze functionality.

Tests the nsys_analyze module including:
- Installation detection
- Local analysis parsing
- Target/workspace support
- API fallback logic
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from wafer.nsys_analyze import (
    _find_nsys,
    _get_install_command,
    _get_platform,
    _parse_csv_kernels,
    _parse_csv_memory,
    _parse_target,
    _parse_time_to_ns,
    analyze_nsys_profile,
    check_nsys_installation,
)


class TestGetPlatform:
    """Tests for platform detection."""

    def test_darwin_on_mac(self) -> None:
        """Should return 'darwin' on macOS."""
        with patch("platform.system", return_value="Darwin"):
            assert _get_platform() == "darwin"

    def test_windows_on_windows(self) -> None:
        """Should return 'windows' on Windows."""
        with patch("platform.system", return_value="Windows"):
            assert _get_platform() == "windows"

    def test_linux_on_linux(self) -> None:
        """Should return 'linux' on Linux."""
        with patch("platform.system", return_value="Linux"):
            assert _get_platform() == "linux"

    def test_linux_on_unknown(self) -> None:
        """Should default to 'linux' on unknown systems."""
        with patch("platform.system", return_value="FreeBSD"):
            assert _get_platform() == "linux"


class TestFindNsys:
    """Tests for NSYS executable detection."""

    def test_finds_nsys_in_path(self) -> None:
        """Should find nsys in PATH."""
        with patch("shutil.which", return_value="/usr/bin/nsys"):
            result = _find_nsys()
            assert result == "/usr/bin/nsys"

    def test_finds_nsys_in_common_paths_linux(self) -> None:
        """Should find nsys in common Linux paths."""
        with patch("wafer.nsys_analyze._get_platform", return_value="linux"):
            with patch("shutil.which", return_value=None):
                with patch("os.path.isfile", side_effect=lambda p: p == "/usr/local/cuda/bin/nsys"):
                    with patch("os.access", return_value=True):
                        result = _find_nsys()
                        assert result == "/usr/local/cuda/bin/nsys"

    def test_returns_none_when_not_found(self) -> None:
        """Should return None when nsys not found."""
        with patch("shutil.which", return_value=None):
            with patch("os.path.isfile", return_value=False):
                result = _find_nsys()
                assert result is None


class TestGetInstallCommand:
    """Tests for install command generation."""

    def test_macos_shows_cli_not_available(self) -> None:
        """Should inform users that NSYS CLI is not available on macOS."""
        with patch("platform.system", return_value="Darwin"):
            cmd = _get_install_command()
            # macOS only has GUI viewer, no CLI - message should explain this
            assert "not available" in cmd.lower() or "--remote" in cmd

    def test_linux_apt_uses_apt(self) -> None:
        """Should recommend apt on Debian-based Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch("shutil.which", side_effect=lambda c: c == "apt-get"):
                cmd = _get_install_command()
                assert "apt" in cmd

    def test_falls_back_to_download(self) -> None:
        """Should provide download URL as fallback."""
        with patch("platform.system", return_value="Linux"):
            with patch("shutil.which", return_value=None):
                cmd = _get_install_command()
                assert "developer.nvidia.com" in cmd


class TestCheckNsysInstallation:
    """Tests for NSYS installation check."""

    def test_returns_installed_when_found(self) -> None:
        """Should return installed=True when nsys found."""
        with patch("wafer.nsys_analyze._find_nsys", return_value="/usr/bin/nsys"):
            with patch("wafer.nsys_analyze._get_nsys_version", return_value="2024.6.1"):
                result = check_nsys_installation()
                assert result.installed is True
                assert result.path == "/usr/bin/nsys"
                assert result.version == "2024.6.1"

    def test_returns_not_installed_when_not_found(self) -> None:
        """Should return installed=False when nsys not found."""
        with patch("wafer.nsys_analyze._find_nsys", return_value=None):
            result = check_nsys_installation()
            assert result.installed is False
            assert result.install_command is not None


class TestParseTimeToNs:
    """Tests for time string parsing."""

    def test_parses_ms(self) -> None:
        """Should parse milliseconds."""
        assert _parse_time_to_ns("1.5ms") == 1_500_000

    def test_parses_us(self) -> None:
        """Should parse microseconds."""
        assert _parse_time_to_ns("500us") == 500_000

    def test_parses_ns(self) -> None:
        """Should parse nanoseconds."""
        assert _parse_time_to_ns("1000ns") == 1000

    def test_parses_seconds(self) -> None:
        """Should parse seconds."""
        assert _parse_time_to_ns("2s") == 2_000_000_000

    def test_handles_empty_string(self) -> None:
        """Should return 0 for empty string."""
        assert _parse_time_to_ns("") == 0

    def test_assumes_ns_without_unit(self) -> None:
        """Should assume nanoseconds when no unit specified."""
        assert _parse_time_to_ns("1000") == 1000


class TestParseCsvKernels:
    """Tests for kernel CSV parsing."""

    def test_parses_kernel_summary(self) -> None:
        """Should parse kernel summary CSV."""
        csv_data = """# NVIDIA Nsight Systems
"Time (%)","Total Time (ns)","Instances","Avg (ns)","Min (ns)","Max (ns)","Name"
80.5,1500000,100,15000,10000,20000,"kernel_gemm"
15.3,285000,50,5700,4000,8000,"kernel_relu"
"""
        kernels = _parse_csv_kernels(csv_data)
        assert len(kernels) == 2
        assert kernels[0]["name"] == "kernel_gemm"
        assert kernels[0]["total_time_ns"] == 1500000
        assert kernels[0]["instances"] == 100
        assert kernels[1]["name"] == "kernel_relu"

    def test_handles_empty_csv(self) -> None:
        """Should return empty list for empty CSV."""
        kernels = _parse_csv_kernels("")
        assert kernels == []

    def test_handles_header_only(self) -> None:
        """Should return empty list for header-only CSV."""
        csv_data = '"Name","Time (ns)","Instances"\n'
        kernels = _parse_csv_kernels(csv_data)
        assert kernels == []

    def test_handles_comment_lines(self) -> None:
        """Should skip comment lines."""
        csv_data = """# Comment line
# Another comment
"Time (%)","Total Time (ns)","Instances","Name"
50.0,1000000,10,"test_kernel"
"""
        kernels = _parse_csv_kernels(csv_data)
        assert len(kernels) == 1


class TestParseCsvMemory:
    """Tests for memory transfer CSV parsing."""

    def test_parses_memory_summary(self) -> None:
        """Should parse memory transfer summary CSV."""
        csv_data = """# NVIDIA Nsight Systems
"Operation","Total Time (ns)","Count","Total (MB)","Avg (ns)"
"[CUDA memcpy HtoD]",500000,10,100.5,50000
"[CUDA memcpy DtoH]",300000,5,50.2,60000
"""
        transfers = _parse_csv_memory(csv_data)
        assert len(transfers) == 2
        assert transfers[0]["operation"] == "[CUDA memcpy HtoD]"
        assert transfers[0]["total_time_ns"] == 500000
        assert transfers[0]["instances"] == 10


class TestParseTarget:
    """Tests for target string parsing."""

    def test_parses_workspace_prefix(self) -> None:
        """Should parse workspace:id prefix."""
        target_type, target_id = _parse_target("workspace:abc123")
        assert target_type == "workspace"
        assert target_id == "abc123"

    def test_parses_regular_target(self) -> None:
        """Should treat non-prefixed as target name."""
        target_type, target_id = _parse_target("vultr-b200")
        assert target_type == "target"
        assert target_id == "vultr-b200"


class TestAnalyzeNsysProfile:
    """Integration tests for analyze_nsys_profile function."""

    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            analyze_nsys_profile(tmp_path / "nonexistent.nsys-rep")

    def test_raises_value_error_for_wrong_extension(self, tmp_path: Path) -> None:
        """Should raise ValueError for non-.nsys-rep file."""
        wrong_file = tmp_path / "test.txt"
        wrong_file.write_text("test")
        with pytest.raises(ValueError, match="Expected .nsys-rep file"):
            analyze_nsys_profile(wrong_file)

    def test_uses_remote_when_nsys_not_installed(self, tmp_path: Path) -> None:
        """Should use remote API when nsys not installed locally."""
        test_file = tmp_path / "test.nsys-rep"
        test_file.write_bytes(b"fake nsys data")

        with patch("wafer.nsys_analyze._find_nsys", return_value=None):
            with patch("wafer.nsys_analyze._analyze_remote_api") as mock_remote:
                mock_remote.return_value = '{"success": true}'
                analyze_nsys_profile(test_file)
                mock_remote.assert_called_once()

    def test_uses_local_when_nsys_installed(self, tmp_path: Path) -> None:
        """Should use local analysis when nsys is installed."""
        test_file = tmp_path / "test.nsys-rep"
        test_file.write_bytes(b"fake nsys data")

        with patch("wafer.nsys_analyze._find_nsys", return_value="/usr/bin/nsys"):
            with patch("wafer.nsys_analyze._analyze_local") as mock_local:
                mock_local.return_value = '{"success": true}'
                analyze_nsys_profile(test_file)
                mock_local.assert_called_once()

    def test_respects_remote_flag(self, tmp_path: Path) -> None:
        """Should use remote when --remote flag is set."""
        test_file = tmp_path / "test.nsys-rep"
        test_file.write_bytes(b"fake nsys data")

        with patch("wafer.nsys_analyze._find_nsys", return_value="/usr/bin/nsys"):
            with patch("wafer.nsys_analyze._analyze_remote_api") as mock_remote:
                mock_remote.return_value = '{"success": true}'
                analyze_nsys_profile(test_file, remote=True)
                mock_remote.assert_called_once()

    def test_uses_workspace_when_specified(self, tmp_path: Path) -> None:
        """Should use workspace execution when workspace: target specified."""
        test_file = tmp_path / "test.nsys-rep"
        test_file.write_bytes(b"fake nsys data")

        with patch("wafer.nsys_analyze._analyze_workspace") as mock_workspace:
            mock_workspace.return_value = '{"success": true}'
            analyze_nsys_profile(test_file, target="workspace:abc123")
            mock_workspace.assert_called_once_with(test_file, "abc123", False)

    def test_uses_target_when_specified(self, tmp_path: Path) -> None:
        """Should use direct SSH when target name specified."""
        test_file = tmp_path / "test.nsys-rep"
        test_file.write_bytes(b"fake nsys data")

        with patch("wafer.nsys_analyze._analyze_remote_direct") as mock_direct:
            mock_direct.return_value = '{"success": true}'
            analyze_nsys_profile(test_file, target="vultr-b200")
            mock_direct.assert_called_once_with(test_file, "vultr-b200", False)
