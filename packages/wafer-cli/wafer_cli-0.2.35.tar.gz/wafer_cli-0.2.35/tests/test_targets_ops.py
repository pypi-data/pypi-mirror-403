"""Unit tests for targets_ops module.

Run with: uv run pytest apps/wafer-cli/tests/test_targets_ops.py -v
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wafer.targets_ops import (
    TargetExecError,
    TargetSSHInfo,
    _expand_remote_glob,
    _has_glob_chars,
    _scp_glob_download,
    _scp_single_file,
    scp_transfer,
)


@pytest.fixture
def ssh_info() -> TargetSSHInfo:
    """Create a test SSH info object."""
    return TargetSSHInfo(
        host="test.example.com",
        port=22,
        user="testuser",
        key_path=Path("/path/to/key"),
    )


class TestHasGlobChars:
    """Tests for _has_glob_chars function."""

    def test_no_glob_chars(self) -> None:
        assert not _has_glob_chars("/tmp/file.json")
        assert not _has_glob_chars("/path/to/dir/")
        assert not _has_glob_chars("simple_name.txt")

    def test_asterisk(self) -> None:
        assert _has_glob_chars("/tmp/*.json")
        assert _has_glob_chars("*.txt")
        assert _has_glob_chars("/path/*/file.txt")

    def test_question_mark(self) -> None:
        assert _has_glob_chars("/tmp/file?.json")
        assert _has_glob_chars("test?.txt")

    def test_brackets(self) -> None:
        assert _has_glob_chars("/tmp/file[0-9].json")
        assert _has_glob_chars("[abc].txt")


class TestExpandRemoteGlob:
    """Tests for _expand_remote_glob function."""

    def test_expands_matching_files(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/tmp/file1.json\n/tmp/file2.json\n/tmp/file3.json"

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result) as mock_run:
            result = _expand_remote_glob(ssh_info, "/tmp/*.json")

            assert result == ["/tmp/file1.json", "/tmp/file2.json", "/tmp/file3.json"]
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ls -1d /tmp/*.json 2>/dev/null" in args[-1]

    def test_no_matches_returns_empty(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result):
            result = _expand_remote_glob(ssh_info, "/tmp/*.nonexistent")

            assert result == []

    def test_empty_stdout_returns_empty(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "   "

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result):
            result = _expand_remote_glob(ssh_info, "/tmp/*.json")

            assert result == []


class TestScpSingleFile:
    """Tests for _scp_single_file function."""

    def test_downloads_file_successfully(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result) as mock_run:
            _scp_single_file(ssh_info, "/tmp/file.json", "./local/", recursive=False)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "scp" in args
            assert "-r" not in args
            assert f"{ssh_info.user}@{ssh_info.host}:/tmp/file.json" in args
            assert "./local/" in args

    def test_downloads_with_recursive(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result) as mock_run:
            _scp_single_file(ssh_info, "/tmp/dir/", "./local/", recursive=True)

            args = mock_run.call_args[0][0]
            assert "-r" in args

    def test_raises_on_failure(self, ssh_info: TargetSSHInfo) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result):
            with pytest.raises(TargetExecError, match="scp failed"):
                _scp_single_file(ssh_info, "/tmp/file.json", "./local/", recursive=False)


class TestScpGlobDownload:
    """Tests for _scp_glob_download function."""

    def test_downloads_all_matching_files(self, ssh_info: TargetSSHInfo) -> None:
        expand_result = MagicMock()
        expand_result.returncode = 0
        expand_result.stdout = "/tmp/a.json\n/tmp/b.json"

        scp_result = MagicMock()
        scp_result.returncode = 0

        with patch("wafer.targets_ops.subprocess.run") as mock_run:
            # First call is expand, subsequent are scp
            mock_run.side_effect = [expand_result, scp_result, scp_result]

            _scp_glob_download(ssh_info, "/tmp/*.json", "./results/", recursive=False)

            assert mock_run.call_count == 3

    def test_no_matches_logs_warning(
        self, ssh_info: TargetSSHInfo, caplog: pytest.LogCaptureFixture
    ) -> None:
        expand_result = MagicMock()
        expand_result.returncode = 1
        expand_result.stdout = ""

        with patch("wafer.targets_ops.subprocess.run", return_value=expand_result):
            import logging

            with caplog.at_level(logging.WARNING):
                _scp_glob_download(ssh_info, "/tmp/*.nonexistent", "./results/", recursive=False)

            assert "No files matched pattern" in caplog.text


class TestScpTransfer:
    """Tests for scp_transfer function."""

    def test_glob_download_uses_glob_handler(self, ssh_info: TargetSSHInfo) -> None:
        """Glob patterns in download should trigger glob handler."""
        with patch("wafer.targets_ops._scp_glob_download") as mock_glob:
            scp_transfer(ssh_info, "/tmp/*.json", "./results/", is_download=True)

            mock_glob.assert_called_once_with(ssh_info, "/tmp/*.json", "./results/", False)

    def test_non_glob_download_uses_regular_scp(self, ssh_info: TargetSSHInfo) -> None:
        """Non-glob downloads should use regular scp."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result) as mock_run:
            scp_transfer(ssh_info, "/tmp/file.json", "./local.json", is_download=True)

            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "scp" in args

    def test_upload_ignores_glob_chars(self, ssh_info: TargetSSHInfo) -> None:
        """Glob chars in upload source should not trigger glob handler (shell expands)."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("wafer.targets_ops.subprocess.run", return_value=mock_result) as mock_run:
            # Upload with glob in local path - shell would expand this, we pass through
            scp_transfer(ssh_info, "./*.json", "/tmp/", is_download=False)

            mock_run.assert_called_once()

    def test_recursive_flag_passed_to_glob_handler(self, ssh_info: TargetSSHInfo) -> None:
        """Recursive flag should be passed to glob download handler."""
        with patch("wafer.targets_ops._scp_glob_download") as mock_glob:
            scp_transfer(
                ssh_info, "/tmp/*/results/", "./results/", is_download=True, recursive=True
            )

            mock_glob.assert_called_once()
            # Check recursive=True was passed
            assert mock_glob.call_args[0][3] is True
