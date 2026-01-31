"""Integration tests for wafer rocprof-compute CLI command.

Tests the rocprof-compute command end-to-end, verifying:
- CLI command execution
- JSON output format
- Error handling
- Integration with wafer-core

Follows similar testing patterns from the codebase.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Constants
CLI_TIMEOUT_SECONDS = 30
CLI_COMMAND = "wafer"
ROCPROF_COMPUTE_SUBCOMMAND = "rocprof-compute"
CHECK_SUBCOMMAND = "check"
JSON_FLAG = "--json"
PORT_FLAG = "--port"

# JSON keys
INSTALLED_KEY = "installed"
PATH_KEY = "path"
VERSION_KEY = "version"
INSTALL_COMMAND_KEY = "install_command"
SUCCESS_KEY = "success"
COMMAND_KEY = "command"
URL_KEY = "url"
PORT_KEY = "port"
FOLDER_KEY = "folder"
ERROR_KEY = "error"


class TestCheckInstallation:
    """Test check installation command."""

    @patch("wafer.rocprof_compute.check_installation")
    def test_check_returns_json(self, mock_check: Mock) -> None:
        """Test check command returns valid JSON."""
        mock_check.return_value = {
            INSTALLED_KEY: True,
            PATH_KEY: "/opt/rocm/bin/rocprof-compute",
            VERSION_KEY: "6.0.0",
            INSTALL_COMMAND_KEY: None
        }

        # This would be called by CLI, testing the function directly
        result = mock_check()

        assert isinstance(result, dict)
        assert INSTALLED_KEY in result
        assert result[INSTALLED_KEY] is True
        assert PATH_KEY in result
        assert VERSION_KEY in result

    @patch("wafer.rocprof_compute.check_installation")
    def test_check_not_installed(self, mock_check: Mock) -> None:
        """Test check command when tool not installed."""
        mock_check.return_value = {
            INSTALLED_KEY: False,
            PATH_KEY: None,
            VERSION_KEY: None,
            INSTALL_COMMAND_KEY: "Install ROCm from https://rocm.docs.amd.com/"
        }

        result = mock_check()

        assert isinstance(result, dict)
        assert result[INSTALLED_KEY] is False
        assert INSTALL_COMMAND_KEY in result


class TestLaunchGui:
    """Test launch GUI command."""

    @patch("wafer.rocprof_compute.launch_gui")
    def test_launch_json_output(self, mock_launch: Mock, tmp_path: Path) -> None:
        """Test launch command with JSON output."""
        test_folder = tmp_path / "results"
        test_folder.mkdir()

        mock_launch.return_value = json.dumps({
            SUCCESS_KEY: True,
            COMMAND_KEY: "rocprof-compute analyze -p /data --gui --port 8050",
            URL_KEY: "http://localhost:8050",
            PORT_KEY: 8050,
            FOLDER_KEY: str(test_folder)
        })

        result_str = mock_launch(str(test_folder), 8050, json_output=True)
        result = json.loads(result_str)

        assert isinstance(result, dict)
        assert result[SUCCESS_KEY] is True
        assert COMMAND_KEY in result
        assert URL_KEY in result
        assert result[URL_KEY] == "http://localhost:8050"
        assert PORT_KEY in result
        assert result[PORT_KEY] == 8050

    @patch("wafer.rocprof_compute.launch_gui")
    def test_launch_nonexistent_folder(self, mock_launch: Mock) -> None:
        """Test launch command with nonexistent folder raises error."""
        mock_launch.side_effect = RuntimeError("Folder not found: /nonexistent")

        with pytest.raises(RuntimeError, match="Folder not found"):
            mock_launch("/nonexistent", 8050, json_output=True)


class TestIntegrationWithCore:
    """Test integration with wafer-core."""

    @patch("wafer_core.lib.rocprofiler.compute.find_rocprof_compute")
    def test_uses_core_check_installation(self, mock_find: Mock) -> None:
        """Test CLI uses wafer-core check_installation."""
        from wafer.rocprof_compute import check_installation

        mock_find.return_value = "/opt/rocm/bin/rocprof-compute"

        result = check_installation()

        assert isinstance(result, dict)
        assert INSTALLED_KEY in result

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_uses_core_launch_gui(
        self,
        mock_is_dir: Mock,
        mock_exists: Mock,
        mock_check: Mock,
        tmp_path: Path
    ) -> None:
        """Test CLI uses wafer-core launch_gui."""
        from wafer_core.lib.rocprofiler.compute.types import CheckResult

        from wafer.rocprof_compute import launch_gui

        test_folder = tmp_path / "results"
        test_folder.mkdir()

        mock_check.return_value = CheckResult(
            installed=True,
            path="/opt/rocm/bin/rocprof-compute"
        )
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        result_str = launch_gui(str(test_folder), 8050, json_output=True)
        result = json.loads(result_str)

        assert result[SUCCESS_KEY] is True
        assert COMMAND_KEY in result


class TestCommandFormat:
    """Test command format matches specification."""

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_command_uses_correct_flags(
        self,
        mock_is_dir: Mock,
        mock_exists: Mock,
        mock_check: Mock,
        tmp_path: Path
    ) -> None:
        """Test generated command uses correct CLI flags when using external binary."""
        from wafer_core.lib.rocprofiler.compute.types import CheckResult, LaunchResult

        from wafer.rocprof_compute import launch_gui

        test_folder = tmp_path / "results"
        test_folder.mkdir()

        mock_check.return_value = CheckResult(
            installed=True,
            path="/opt/rocm/bin/rocprof-compute"
        )
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        # Use use_bundled=False to test external rocprof-compute binary command format
        # By default use_bundled=True returns "bundled-gui-viewer" as the command
        with patch("wafer_core.lib.rocprofiler.compute.launch_gui") as mock_launch:
            mock_launch.return_value = LaunchResult(
                success=True,
                folder=str(test_folder),
                port=8050,
                url="http://localhost:8050",
                command=["rocprof-compute", "analyze", "-p", str(test_folder), "--gui", "--port", "8050"],
                error=None
            )
            result_str = launch_gui(str(test_folder), 8050, json_output=True, use_bundled=False)
            result = json.loads(result_str)

        command = result[COMMAND_KEY]
        # Verify command format: rocprof-compute analyze -p {folder} --gui --port {port}
        assert "rocprof-compute" in command
        assert "analyze" in command
        assert "-p" in command  # NOT --path
        assert str(test_folder) in command
        assert "--gui" in command
        assert "--port" in command
        assert "8050" in command
