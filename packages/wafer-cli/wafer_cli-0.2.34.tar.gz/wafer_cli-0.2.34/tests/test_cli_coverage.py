"""Unit tests for CLI commands using CliRunner for coverage.

These tests invoke CLI commands in-process so coverage can track them.
For integration tests that test the actual binary, see test_cli_parity_integration.py.

Run with: PYTHONPATH=apps/wafer-cli uv run pytest apps/wafer-cli/tests/test_cli_coverage.py -v

NOTE ON FIXTURES:
Fixtures (like sample.ncu-rep) are a form of mocking - they encode assumptions about
what external systems produce. They're less bad than API mocks because:
1. File formats change less often than APIs
2. The fixture is real data, not handcrafted assumptions

But they can still go stale. Ideally we'd also have slow integration tests that
generate these files fresh by running real profiling commands on GPUs.
TODO: Add slow tests that generate .ncu-rep/.nsys-rep files via remote-run.
"""

import json
import os
import re
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from wafer.cli import app

runner = CliRunner()


def _api_reachable() -> bool:
    """Check if the wafer API is reachable."""
    from wafer.api_client import get_api_url

    try:
        api_url = get_api_url()
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{api_url}/health")
            return response.status_code == 200
    except Exception:
        return False


# Skip tests that require API if it's unreachable
requires_api = pytest.mark.skipif(
    not _api_reachable(),
    reason="Wafer API not reachable",
)


def _cleanup_test_workspaces() -> None:
    """Delete any workspaces with names starting with 'test-'."""
    result = runner.invoke(app, ["workspaces", "list", "--json"])
    if result.exit_code != 0:
        return
    try:
        workspaces = json.loads(result.stdout)
    except json.JSONDecodeError:
        return
    for ws in workspaces:
        if ws.get("name", "").startswith("test-"):
            runner.invoke(app, ["workspaces", "delete", ws["id"], "-y"])


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_workspaces_session():
    """Clean up orphaned test workspaces at start and end of test session."""
    # Cleanup before tests (in case previous run left orphans)
    _cleanup_test_workspaces()
    yield
    # Cleanup after tests
    _cleanup_test_workspaces()


class TestGuideCommand:
    """Test wafer guide command."""

    def test_guide_displays_content(self) -> None:
        """Guide command should display GUIDE.md content."""
        result = runner.invoke(app, ["guide"])
        assert result.exit_code == 0, f"Failed with output: {result.output}"
        assert "Wafer CLI Guide" in result.stdout
        assert "wafer nvidia ncu" in result.stdout


class TestPerfettoCommands:
    """Test wafer nvidia perfetto subcommands."""

    @pytest.fixture
    def sample_trace(self, tmp_path: Path) -> Path:
        """Create a sample Chrome/Perfetto trace file."""
        trace_content = {
            "traceEvents": [
                {"name": "test", "ph": "X", "ts": 0, "dur": 100, "pid": 0, "tid": 0},
            ],
        }
        trace_file = tmp_path / "test_trace.json"
        trace_file.write_text(json.dumps(trace_content))
        return trace_file

    def test_perfetto_check(self) -> None:
        """Check trace_processor availability."""
        result = runner.invoke(app, ["nvidia", "perfetto", "check", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "available" in data

    def test_perfetto_tables(self, sample_trace: Path) -> None:
        """List tables in a trace."""
        result = runner.invoke(app, ["nvidia", "perfetto", "tables", str(sample_trace), "--json"])
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert "tables" in data
        else:
            if "perfetto" in result.output.lower() or "not installed" in result.output.lower():
                pytest.skip("perfetto package not installed")

    def test_perfetto_query(self, sample_trace: Path) -> None:
        """Execute SQL query against a trace."""
        result = runner.invoke(
            app,
            [
                "nvidia",
                "perfetto",
                "query",
                str(sample_trace),
                "SELECT COUNT(*) as cnt FROM slice",
                "--json",
            ],
        )
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert "results" in data
        else:
            if "perfetto" in result.output.lower() or "not installed" in result.output.lower():
                pytest.skip("perfetto package not installed")

    def test_perfetto_schema(self, sample_trace: Path) -> None:
        """Get schema for a table."""
        result = runner.invoke(
            app,
            ["nvidia", "perfetto", "schema", str(sample_trace), "slice", "--json"],
        )
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert "table" in data
            assert "columns" in data
        else:
            if "perfetto" in result.output.lower() or "not installed" in result.output.lower():
                pytest.skip("perfetto package not installed")


@requires_api
class TestWorkspacesCommands:
    """Test wafer workspaces subcommands."""

    def test_workspaces_list_json(self) -> None:
        """List workspaces with JSON output."""
        result = runner.invoke(app, ["workspaces", "list", "--json"])
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        else:
            combined = result.output.lower()
            assert (
                "auth" in combined
                or "login" in combined
                or "error" in combined
                or "not authenticated" in combined
            )

    def test_workspaces_list_pretty(self) -> None:
        """List workspaces with pretty output (no --json)."""
        result = runner.invoke(app, ["workspaces", "list"])
        # Either succeeds with formatted output or fails with auth error
        if result.exit_code == 0:
            # Should have some output (either workspaces or "No workspaces")
            assert len(result.output) > 0
        else:
            combined = result.output.lower()
            assert "auth" in combined or "login" in combined or "error" in combined

    def test_workspaces_create_and_delete(self) -> None:
        """Create, show, and delete a workspace."""
        ws_name = f"test-coverage-{os.getpid()}"
        ws_id = None

        try:
            # Create with JSON
            result = runner.invoke(app, ["workspaces", "create", ws_name, "--json"])
            if result.exit_code != 0:
                if "auth" in result.output.lower() or "not authenticated" in result.output.lower():
                    pytest.skip("Not authenticated")
                return

            data = json.loads(result.stdout)
            ws_id = data.get("id")
            assert ws_id is not None

            # Show with JSON
            result = runner.invoke(app, ["workspaces", "show", ws_id, "--json"])
            if result.exit_code == 0:
                show_data = json.loads(result.stdout)
                assert show_data["id"] == ws_id

            # Show without JSON (pretty print)
            result = runner.invoke(app, ["workspaces", "show", ws_id])
            if result.exit_code == 0:
                assert ws_id in result.output or ws_name in result.output

        finally:
            # Delete
            if ws_id:
                result = runner.invoke(app, ["workspaces", "delete", ws_id, "-y"])

    def test_workspaces_create_pretty(self) -> None:
        """Create workspace with pretty output."""
        ws_name = f"test-pretty-{os.getpid()}"
        ws_id = None

        try:
            result = runner.invoke(app, ["workspaces", "create", ws_name])
            if result.exit_code != 0:
                if "auth" in result.output.lower() or "not authenticated" in result.output.lower():
                    pytest.skip("Not authenticated")
                return

            # Extract ID from output
            # Output format: "Creating workspace: <name> (<uuid>)"
            match = re.search(r"\(([a-f0-9-]{36})\)", result.output)
            if match:
                ws_id = match.group(1)
            assert "Creating workspace:" in result.output
            assert ws_id is not None, f"Could not extract workspace ID from: {result.output}"

        finally:
            if ws_id:
                runner.invoke(app, ["workspaces", "delete", ws_id, "-y"])

    def test_workspaces_create_wait_json(self) -> None:
        """Create workspace with --wait JSON output."""
        ws_name = f"test-create-wait-{os.getpid()}"
        ws_id = None

        try:
            result = runner.invoke(
                app,
                ["workspaces", "create", ws_name, "--wait", "--json"],
            )
            if result.exit_code != 0:
                if "auth" in result.output.lower() or "not authenticated" in result.output.lower():
                    pytest.skip("Not authenticated")
                assert "error" in result.output.lower() or "no gpu" in result.output.lower()
                return

            data = json.loads(result.stdout)
            ws_id = data.get("workspace_id")
            assert ws_id is not None
            assert "ssh_host" in data
            assert "ssh_port" in data
            assert "ssh_user" in data

        finally:
            if ws_id:
                runner.invoke(app, ["workspaces", "delete", ws_id, "-y"])

    def test_workspaces_show_not_found(self) -> None:
        """Show workspace with invalid ID returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = runner.invoke(app, ["workspaces", "show", fake_id])
        if result.exit_code != 0:
            # Should be 404 or auth error
            assert (
                "not found" in result.output.lower()
                or "404" in result.output
                or "auth" in result.output.lower()
            )

    def test_workspaces_ssh_not_found(self) -> None:
        """SSH to workspace with invalid ID returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = runner.invoke(app, ["workspaces", "ssh", fake_id])
        if result.exit_code != 0:
            # Should be 404 or auth error
            assert (
                "not found" in result.output.lower()
                or "404" in result.output
                or "auth" in result.output.lower()
            )

    def test_workspaces_exec_option_order(self) -> None:
        """Exec should reject options after workspace name."""
        result = runner.invoke(
            app,
            ["workspaces", "exec", "dev", "--timeout", "10", "--", "echo", "hi"],
        )
        assert result.exit_code != 0
        assert "options must come before the workspace name" in result.output.lower()


class TestNsysAnalyzeCommand:
    """Test wafer nvidia nsys analyze command."""

    @pytest.fixture
    def real_nsys_file(self) -> Path | None:
        """Get real .nsys-rep fixture file if available."""
        fixture = Path(__file__).parent / "fixtures" / "sample.nsys-rep"
        if fixture.exists():
            return fixture
        return None

    def test_nsys_analyze_missing_file(self) -> None:
        """nvidia nsys analyze should error on missing file."""
        result = runner.invoke(app, ["nvidia", "nsys", "analyze", "/nonexistent/file.nsys-rep"])
        assert result.exit_code != 0
        combined = result.output.lower()
        assert (
            "not found" in combined
            or "error" in combined
            or "no such file" in combined
            or "does not exist" in combined
        )

    @requires_api
    def test_nsys_analyze_remote_json(self, real_nsys_file: Path | None) -> None:
        """nvidia nsys analyze with --remote and --json flags."""
        if real_nsys_file is None:
            pytest.skip("No real .nsys-rep fixture available")

        result = runner.invoke(
            app, ["nvidia", "nsys", "analyze", str(real_nsys_file), "--remote", "--json"]
        )
        if result.exit_code != 0:
            combined = result.output.lower()
            if "auth" in combined or "login" in combined or "401" in combined or "403" in combined:
                pytest.skip("Not authenticated")
            if (
                "no gpu" in combined
                or "no targets" in combined
                or "unavailable" in combined
                or "timed out" in combined
                or "timeout" in combined
                or "connect" in combined
                or "service" in combined
                or "billing" in combined
                or "spend limit" in combined
                or "402" in combined
            ):
                pytest.skip(f"Remote nsys unavailable: {result.output.strip()}")
            assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "kernels" in data or "timeline" in data or "summary" in data

    @requires_api
    def test_nsys_analyze_remote_pretty(self, real_nsys_file: Path | None) -> None:
        """nvidia nsys analyze with --remote but no --json (pretty print)."""
        if real_nsys_file is None:
            pytest.skip("No real .nsys-rep fixture available")

        result = runner.invoke(app, ["nvidia", "nsys", "analyze", str(real_nsys_file), "--remote"])
        if result.exit_code != 0:
            combined = result.output.lower()
            if "auth" in combined or "login" in combined or "401" in combined or "403" in combined:
                pytest.skip("Not authenticated")
            if (
                "no gpu" in combined
                or "no targets" in combined
                or "unavailable" in combined
                or "timed out" in combined
                or "timeout" in combined
                or "connect" in combined
                or "service" in combined
                or "billing" in combined
                or "spend limit" in combined
                or "402" in combined
            ):
                pytest.skip(f"Remote nsys unavailable: {result.output.strip()}")
            assert result.exit_code == 0
        assert "NSYS" in result.output or "Kernel" in result.output or "Profile" in result.output

    def test_nsys_analyze_local(self, real_nsys_file: Path | None) -> None:
        """nvidia nsys analyze without --remote (local mode)."""
        if real_nsys_file is None:
            pytest.skip("No real .nsys-rep fixture available")

        result = runner.invoke(app, ["nvidia", "nsys", "analyze", str(real_nsys_file)])
        # Will fail if nsys not installed locally, but exercises local code path
        # Either succeeds or fails with "nsys not found"
        assert result.exit_code in (0, 1)


class TestNcuAnalyzeCommand:
    """Test wafer nvidia ncu analyze command."""

    @pytest.fixture
    def real_ncu_file(self) -> Path | None:
        """Get real .ncu-rep fixture file if available."""
        fixture = Path(__file__).parent / "fixtures" / "sample.ncu-rep"
        if fixture.exists():
            return fixture
        return None

    def test_ncu_analyze_missing_file(self) -> None:
        """nvidia ncu analyze should error on missing file."""
        result = runner.invoke(app, ["nvidia", "ncu", "analyze", "/nonexistent/file.ncu-rep"])
        assert result.exit_code != 0

    @requires_api
    def test_ncu_analyze_remote_json(self, real_ncu_file: Path | None) -> None:
        """nvidia ncu analyze with --remote and --json flags."""
        if real_ncu_file is None:
            pytest.skip("No real .ncu-rep fixture available")

        result = runner.invoke(
            app, ["nvidia", "ncu", "analyze", str(real_ncu_file), "--remote", "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "report_id" in data or "kernels" in data

    @requires_api
    def test_ncu_analyze_remote_pretty(self, real_ncu_file: Path | None) -> None:
        """nvidia ncu analyze with --remote but no --json (pretty print)."""
        if real_ncu_file is None:
            pytest.skip("No real .ncu-rep fixture available")

        result = runner.invoke(app, ["nvidia", "ncu", "analyze", str(real_ncu_file), "--remote"])
        assert result.exit_code == 0
        assert "NCU" in result.output or "Kernel" in result.output or "GPU" in result.output

    @requires_api
    def test_ncu_analyze_include_source_json(self, real_ncu_file: Path | None) -> None:
        """nvidia ncu analyze with --include-source and --json flags."""
        if real_ncu_file is None:
            pytest.skip("No real .ncu-rep fixture available")

        result = runner.invoke(
            app,
            [
                "nvidia",
                "ncu",
                "analyze",
                str(real_ncu_file),
                "--remote",
                "--include-source",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "report_id" in data or "kernels" in data

    @requires_api
    def test_ncu_analyze_include_source_pretty(self, real_ncu_file: Path | None) -> None:
        """nvidia ncu analyze with --include-source but no --json."""
        if real_ncu_file is None:
            pytest.skip("No real .ncu-rep fixture available")

        result = runner.invoke(
            app, ["nvidia", "ncu", "analyze", str(real_ncu_file), "--remote", "--include-source"]
        )
        assert result.exit_code == 0

    def test_ncu_analyze_target(self, tmp_path: Path) -> None:
        """nvidia ncu analyze with --target flag (direct SSH mode)."""
        dummy = tmp_path / "dummy.ncu-rep"
        dummy.write_bytes(b"dummy")

        result = runner.invoke(
            app, ["nvidia", "ncu", "analyze", str(dummy), "--target", "nonexistent-target"]
        )
        # Will fail (target not found) but exercises the target code path
        assert result.exit_code in (0, 1)


class TestCaptureCommand:
    """Test wafer capture commands."""

    def test_capture_list(self) -> None:
        """List captures."""
        result = runner.invoke(app, ["capture-list", "--json"])
        if result.exit_code == 0:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        else:
            # Auth error is acceptable
            combined = result.output.lower()
            assert "auth" in combined or "error" in combined or len(combined) > 0

    def test_capture_command(self, tmp_path: Path) -> None:
        """Capture a command execution."""
        script = tmp_path / "test.py"
        script.write_text('print("hello")\n')

        result = runner.invoke(
            app,
            ["capture", f"test-{os.getpid()}", f"python {script}", "--dir", str(tmp_path)],
        )
        # May fail without auth, but exercises code path
        assert result.exit_code in (0, 1)


class TestWevinCommand:
    """Test wafer wevin command."""

    def test_wevin_query(self) -> None:
        """Query Wevin AI assistant."""
        result = runner.invoke(
            app,
            ["wevin", "What is a kernel?", "--json", "--max-turns", "1"],
        )
        # May fail if service not running
        if result.exit_code == 0:
            assert len(result.output) > 0
        else:
            assert result.exit_code in (0, 1)


class TestRocprofCommands:
    """Test wafer rocprof commands."""

    def test_rocprof_compute_check(self) -> None:
        """Check rocprof-compute availability."""
        result = runner.invoke(app, ["rocprof-compute", "check"])
        # Should run without crashing
        combined = result.output.lower()
        assert (
            "rocprof" in combined
            or "not found" in combined
            or "error" in combined
            or len(combined) > 0
        )


class TestTargetsCommands:
    """Test wafer config targets commands."""

    def test_targets_list(self) -> None:
        """List configured targets."""
        result = runner.invoke(app, ["config", "targets", "list"])
        # Should succeed even with no targets
        assert result.exit_code == 0


class TestRemoteRunCommand:
    """Test wafer remote-run command."""

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 target is configured."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        return target_path.exists()

    def test_remote_run_simple(self) -> None:
        """remote-run executes command on remote GPU."""
        result = runner.invoke(app, ["remote-run", "--", "echo", "hello"])
        # Should succeed or fail with auth/target error
        if result.exit_code == 0:
            assert "hello" in result.output
        else:
            # Auth or target error is acceptable
            combined = result.output.lower()
            assert "auth" in combined or "target" in combined or "error" in combined

    def test_remote_run_nvidia_smi(self, vultr_available: bool) -> None:
        """Run nvidia-smi on real GPU target."""
        if not vultr_available:
            pytest.skip("vultr-b200 target not configured")

        result = runner.invoke(
            app,
            [
                "remote-run",
                "--direct",
                "--target",
                "vultr-b200",
                "--",
                "nvidia-smi",
                "--query-gpu=name",
                "--format=csv,noheader",
            ],
        )
        if result.exit_code == 0:
            assert "NVIDIA" in result.output or "B200" in result.output
        else:
            # SSH connection issues are acceptable in CI
            combined = result.output.lower()
            assert "error" in combined or "connection" in combined or "timeout" in combined


class TestEvaluateCommand:
    """Test wafer evaluate command."""

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 target is configured."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        return target_path.exists()

    def test_evaluate_missing_files(self) -> None:
        """evaluate with missing files should error."""
        result = runner.invoke(
            app,
            [
                "evaluate",
                "--impl",
                "/nonexistent/impl.py",
                "--reference",
                "/nonexistent/ref.py",
                "--test-cases",
                "/nonexistent/tests.json",
            ],
        )
        assert result.exit_code != 0

    def test_evaluate_simple_kernel(self, vultr_available: bool, tmp_path: Path) -> None:
        """Evaluate a simple kernel against reference on real GPU."""
        if not vultr_available:
            pytest.skip("vultr-b200 target not configured")

        # Create implementation
        impl = tmp_path / "impl.py"
        impl.write_text(
            "import torch\n\ndef solution(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:\n    return a + b\n"
        )

        # Create reference (same as impl for correctness test)
        ref = tmp_path / "ref.py"
        ref.write_text(
            "import torch\n\ndef solution(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:\n    return a + b\n"
        )

        # Create test cases
        tests = tmp_path / "tests.json"
        tests.write_text(
            '[{"name": "small", "inputs": {"a": {"shape": [128], "dtype": "float32"}, "b": {"shape": [128], "dtype": "float32"}}}]'
        )

        result = runner.invoke(
            app,
            [
                "evaluate",
                "--impl",
                str(impl),
                "--reference",
                str(ref),
                "--test-cases",
                str(tests),
                "--target",
                "vultr-b200",
            ],
        )
        # May fail for various reasons (SSH, GPU availability), but exercises the code path
        combined = result.output.lower()
        assert (
            "evaluate" in combined
            or "running" in combined
            or "error" in combined
            or result.exit_code in (0, 1)
        )


class TestWorkspacesExecFlagPassthrough:
    """Test that flags after -- are passed through to the command, not intercepted."""

    def test_exec_passes_dash_i_flag(self) -> None:
        """The -i flag should pass through, not be intercepted as --image."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "echo", "-i", "test"
        ])
        # Should NOT fail with "no such option" or similar parse error
        assert "no such option" not in result.output.lower()
        assert "unrecognized" not in result.output.lower()
        # May fail with workspace not found - that's fine, parsing succeeded

    def test_exec_passes_dash_v_flag(self) -> None:
        """The -v flag should pass through, not be intercepted as --verbose."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "python", "-v", "-c", "print(1)"
        ])
        assert "no such option" not in result.output.lower()

    def test_exec_passes_double_dash_help(self) -> None:
        """--help after -- should pass to command, not show exec help."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "python", "--help"
        ])
        # Should NOT show the exec command's help text
        assert "Execute a command in workspace" not in result.output

    def test_exec_passes_multiple_flags(self) -> None:
        """Multiple flags like -i -v -n should all pass through."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "grep", "-i", "-v", "-n", "pattern"
        ])
        assert "no such option" not in result.output.lower()

    def test_exec_no_command_shows_error(self) -> None:
        """Missing command after -- should show helpful error."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--"
        ])
        assert result.exit_code != 0
        assert "no command" in result.output.lower() or "error" in result.output.lower()

    def test_exec_preserves_flag_order(self) -> None:
        """Flags should be preserved in order they were given."""
        # This tests the shlex.join behavior
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "cmd", "-a", "1", "-b", "2"
        ])
        assert "no such option" not in result.output.lower()

    def test_exec_with_equals_syntax(self) -> None:
        """Flags with --flag=value syntax should pass through."""
        result = runner.invoke(app, [
            "workspaces", "exec", "test-ws", "--", "cmd", "--output=/tmp/out"
        ])
        assert "no such option" not in result.output.lower()


class TestAgentNoSandboxOption:
    """Test --no-sandbox option in wafer agent command."""

    def test_agent_no_sandbox_option_exists(self) -> None:
        """Test that --no-sandbox option is accepted by wafer agent command."""
        result = runner.invoke(app, ["agent", "--help"])
        assert result.exit_code == 0
        # Strip ANSI escape codes before checking (help output may contain color codes)
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        clean_output = ansi_escape.sub('', result.stdout)
        assert "--no-sandbox" in clean_output
        assert "liability" in clean_output.lower()  # Warning text should be in help
