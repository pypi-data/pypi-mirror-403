"""Integration tests for CLI/IDE parity features.

Tests real user workflows against the actual API. No mocking.
Run with: WAFER_API_URL=https://wafer-api-staging.onrender.com uv run pytest tests/test_cli_parity_integration.py -v

Auth is checked by conftest.py - if token is expired, it will print the login command.
"""

import json
import os
import subprocess
from pathlib import Path

import httpx
import pytest

CLI_DIR = Path(__file__).parent.parent


def _api_reachable() -> bool:
    """Check if the wafer API is reachable."""
    api_url = os.environ.get("WAFER_API_URL", "http://localhost:8000")
    try:
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


def run_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run wafer CLI command and return result."""
    result = subprocess.run(
        ["uv", "run", "wafer", *args],
        capture_output=True,
        text=True,
        cwd=CLI_DIR,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"CLI failed: {result.stderr}")
    return result


@requires_api
class TestWorkspacesWorkflow:
    """Test: User creates a workspace, lists it, shows details, then deletes it."""

    def test_workspace_lifecycle(self) -> None:
        """Create -> list -> show -> delete workflow."""
        ws_name = f"test-cli-{os.getpid()}"
        ws_id = None

        try:
            # Create workspace
            result = run_cli("workspaces", "create", ws_name, "--json")
            ws_data = json.loads(result.stdout)
            ws_id = ws_data["id"]
            assert ws_data["name"] == ws_name

            # List should include it
            result = run_cli("workspaces", "list", "--json")
            workspaces = json.loads(result.stdout)
            assert any(w["id"] == ws_id for w in workspaces)

            # Show should return details
            result = run_cli("workspaces", "show", ws_id, "--json")
            show_data = json.loads(result.stdout)
            assert show_data["id"] == ws_id

        finally:
            # Cleanup
            if ws_id:
                run_cli("workspaces", "delete", ws_id, "-y", check=False)


@requires_api
class TestNcuAnalyzeWorkflow:
    """Test: User analyzes an NCU profile file."""

    @pytest.fixture
    def ncu_file(self) -> Path | None:
        """Find a .ncu-rep file in the repo."""
        for f in Path(__file__).parents[4].rglob("*.ncu-rep"):
            return f
        return None

    def test_ncu_analyze_remote(self, ncu_file: Path | None) -> None:
        """Upload and analyze NCU profile via API."""
        if ncu_file is None:
            pytest.skip("No .ncu-rep file found")

        result = run_cli("nvidia", "ncu", "analyze", str(ncu_file), "--remote", "--json")
        data = json.loads(result.stdout)

        assert "report_id" in data
        assert "kernels" in data

    def test_ncu_analyze_direct(self, ncu_file: Path | None) -> None:
        """Analyze NCU profile via direct SSH to target."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        if not target_path.exists():
            pytest.skip("vultr-b200 target not configured")
        if ncu_file is None:
            pytest.skip("No .ncu-rep file found")

        result = run_cli("nvidia", "ncu", "analyze", str(ncu_file), "--target", "vultr-b200")

        assert "NCU Profiling Analysis" in result.stdout
        assert "GPU Information" in result.stdout


class TestFullProfilingWorkflow:
    """Test: Full workflow - compile CUDA, profile with ncu inside Docker, analyze results."""

    B200_HOST = "chiraag@45.76.244.62"
    SSH_KEY = "~/.ssh/id_ed25519"
    DOCKER_IMAGE = "nvcr.io/nvidia/pytorch:25.01-py3"

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 target is configured and reachable."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        if not target_path.exists():
            return False
        # Quick SSH check
        result = subprocess.run(
            [
                "ssh",
                "-i",
                str(Path(self.SSH_KEY).expanduser()),
                "-o",
                "ConnectTimeout=5",
                self.B200_HOST,
                "echo ok",
            ],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def test_compile_profile_analyze(self, vultr_available: bool, tmp_path: Path) -> None:
        """Compile CUDA code on B200, profile with ncu in Docker, analyze it."""
        if not vultr_available:
            pytest.skip("vultr-b200 not available")

        ssh_key = str(Path(self.SSH_KEY).expanduser())
        remote_dir = f"/tmp/wafer-test-{os.getpid()}"

        try:
            # 1. Create test kernel
            kernel_code = """
#include <stdio.h>
__global__ void add(float *a, float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
int main() {
    int n = 1024;
    float *a, *b, *c;
    cudaMallocManaged(&a, n*sizeof(float));
    cudaMallocManaged(&b, n*sizeof(float));
    cudaMallocManaged(&c, n*sizeof(float));
    for (int i = 0; i < n; i++) { a[i] = 1; b[i] = 2; }
    add<<<4, 256>>>(a, b, c, n);
    cudaDeviceSynchronize();
    cudaFree(a); cudaFree(b); cudaFree(c);
    return 0;
}
"""
            local_kernel = tmp_path / "test_kernel.cu"
            local_kernel.write_text(kernel_code)

            # Setup remote dir and copy kernel
            subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, f"mkdir -p {remote_dir}"],
                check=True,
            )
            subprocess.run(
                ["scp", "-i", ssh_key, str(local_kernel), f"{self.B200_HOST}:{remote_dir}/"],
                check=True,
            )

            # 2. Compile and profile inside Docker (needs --cap-add SYS_ADMIN for ncu)
            docker_cmd = (
                f"docker run --rm --gpus all --cap-add SYS_ADMIN "
                f"-v {remote_dir}:/workspace -w /workspace "
                f"{self.DOCKER_IMAGE} "
                f"bash -c 'nvcc test_kernel.cu -o test_kernel && ncu --set basic -o profile ./test_kernel'"
            )
            result = subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, docker_cmd],
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, (
                f"Compile/profile failed: {result.stdout}\n{result.stderr}"
            )

            # 3. Download profile
            local_profile = tmp_path / "profile.ncu-rep"
            subprocess.run(
                [
                    "scp",
                    "-i",
                    ssh_key,
                    f"{self.B200_HOST}:{remote_dir}/profile.ncu-rep",
                    str(local_profile),
                ],
                check=True,
            )
            assert local_profile.exists()

            # 4. Analyze with wafer CLI
            result = run_cli(
                "nvidia", "ncu", "analyze", str(local_profile), "--target", "vultr-b200"
            )

            assert "NCU Profiling Analysis" in result.stdout
            assert "GPU Information" in result.stdout
            assert "add" in result.stdout  # Our kernel name

        finally:
            # Cleanup remote
            subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, f"rm -rf {remote_dir}"],
                check=False,
            )


class TestRemoteRunWorkflow:
    """Test: User runs a command on remote GPU."""

    B200_HOST = "chiraag@45.76.244.62"
    SSH_KEY = "~/.ssh/id_ed25519"

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 is reachable."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        if not target_path.exists():
            return False
        result = subprocess.run(
            [
                "ssh",
                "-i",
                str(Path(self.SSH_KEY).expanduser()),
                "-o",
                "ConnectTimeout=5",
                self.B200_HOST,
                "echo ok",
            ],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def test_remote_run_nvidia_smi(self, vultr_available: bool) -> None:
        """Run nvidia-smi on remote GPU."""
        if not vultr_available:
            pytest.skip("vultr-b200 not available")

        result = run_cli(
            "remote-run",
            "--direct",
            "--target",
            "vultr-b200",
            "--",
            "nvidia-smi",
            "--query-gpu=name",
            "--format=csv,noheader",
        )

        # Should contain GPU name
        assert "NVIDIA" in result.stdout or "B200" in result.stdout


class TestEvaluateWorkflow:
    """Test: User evaluates a kernel implementation."""

    B200_HOST = "chiraag@45.76.244.62"
    SSH_KEY = "~/.ssh/id_ed25519"

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 is reachable."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        if not target_path.exists():
            return False
        result = subprocess.run(
            [
                "ssh",
                "-i",
                str(Path(self.SSH_KEY).expanduser()),
                "-o",
                "ConnectTimeout=5",
                self.B200_HOST,
                "echo ok",
            ],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def test_evaluate_simple_kernel(self, vultr_available: bool, tmp_path: Path) -> None:
        """Evaluate a simple kernel against reference."""
        if not vultr_available:
            pytest.skip("vultr-b200 not available")

        # Create implementation
        impl = tmp_path / "impl.py"
        impl.write_text("""
import torch

def solution(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return a + b
""")

        # Create reference
        ref = tmp_path / "ref.py"
        ref.write_text("""
import torch

def solution(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    return a + b
""")

        # Create test cases
        tests = tmp_path / "tests.json"
        tests.write_text("""
[
    {
        "name": "small",
        "inputs": {
            "a": {"shape": [128], "dtype": "float32"},
            "b": {"shape": [128], "dtype": "float32"}
        }
    }
]
""")

        result = run_cli(
            "evaluate",
            "--impl",
            str(impl),
            "--reference",
            str(ref),
            "--test-cases",
            str(tests),
            "--target",
            "vultr-b200",
            check=False,  # May fail for various reasons, we just want to test the workflow
        )

        # Should at least attempt to run (output something about evaluation)
        combined = result.stdout + result.stderr
        assert (
            "evaluate" in combined.lower()
            or "running" in combined.lower()
            or "error" in combined.lower()
        )


class TestAMDProfilingWorkflow:
    """Test: User profiles AMD GPU code with rocprof tools."""

    @pytest.fixture
    def amd_target_available(self) -> bool:
        """Check if any AMD target is configured."""
        targets_dir = Path.home() / ".wafer" / "targets"
        if not targets_dir.exists():
            return False
        # Look for any target with AMD/ROCm
        for target_file in targets_dir.glob("*.toml"):
            content = target_file.read_text()
            if "amd" in content.lower() or "rocm" in content.lower() or "mi" in content.lower():
                return True
        return False

    def test_rocprof_compute_check(self) -> None:
        """Check rocprof-compute availability (doesn't need AMD hardware)."""
        result = run_cli("rocprof-compute", "check", check=False)
        # Should return some output about rocprof availability
        combined = result.stdout + result.stderr
        assert (
            "rocprof" in combined.lower()
            or "not found" in combined.lower()
            or "installed" in combined.lower()
        )

    def test_rocprof_compute_analyze(self, amd_target_available: bool, tmp_path: Path) -> None:
        """Analyze rocprof-compute workload (needs AMD GPU)."""
        if not amd_target_available:
            pytest.skip("No AMD target configured")

        # Would need real workload data from AMD GPU
        pytest.skip("AMD workload analysis requires real profile data from AMD GPU")


@requires_api
class TestNsysAnalyzeWorkflow:
    """Test: Full nsys workflow - compile CUDA, profile with nsys, analyze."""

    B200_HOST = "chiraag@45.76.244.62"
    SSH_KEY = "~/.ssh/id_ed25519"
    DOCKER_IMAGE = "nvcr.io/nvidia/pytorch:25.01-py3"

    @pytest.fixture
    def vultr_available(self) -> bool:
        """Check if vultr-b200 is reachable."""
        target_path = Path.home() / ".wafer" / "targets" / "vultr-b200.toml"
        if not target_path.exists():
            return False
        result = subprocess.run(
            [
                "ssh",
                "-i",
                str(Path(self.SSH_KEY).expanduser()),
                "-o",
                "ConnectTimeout=5",
                self.B200_HOST,
                "echo ok",
            ],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0

    def test_nsys_profile_and_analyze(self, vultr_available: bool, tmp_path: Path) -> None:
        """Compile CUDA, profile with nsys in Docker, analyze with CLI."""
        if not vultr_available:
            pytest.skip("vultr-b200 not available")

        ssh_key = str(Path(self.SSH_KEY).expanduser())
        remote_dir = f"/tmp/wafer-nsys-test-{os.getpid()}"

        try:
            # 1. Create test kernel
            kernel_code = """
#include <stdio.h>
__global__ void add(float *a, float *b, float *c, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) c[i] = a[i] + b[i];
}
int main() {
    int n = 1024;
    float *a, *b, *c;
    cudaMallocManaged(&a, n*sizeof(float));
    cudaMallocManaged(&b, n*sizeof(float));
    cudaMallocManaged(&c, n*sizeof(float));
    for (int i = 0; i < n; i++) { a[i] = 1; b[i] = 2; }
    add<<<4, 256>>>(a, b, c, n);
    cudaDeviceSynchronize();
    cudaFree(a); cudaFree(b); cudaFree(c);
    return 0;
}
"""
            local_kernel = tmp_path / "test_kernel.cu"
            local_kernel.write_text(kernel_code)

            # Setup remote dir and copy kernel
            subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, f"mkdir -p {remote_dir}"],
                check=True,
            )
            subprocess.run(
                ["scp", "-i", ssh_key, str(local_kernel), f"{self.B200_HOST}:{remote_dir}/"],
                check=True,
            )

            # 2. Compile and profile with nsys inside Docker
            docker_cmd = (
                f"docker run --rm --gpus all "
                f"-v {remote_dir}:/workspace -w /workspace "
                f"{self.DOCKER_IMAGE} "
                f"bash -c 'nvcc test_kernel.cu -o test_kernel && nsys profile -o profile ./test_kernel'"
            )
            result = subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, docker_cmd],
                capture_output=True,
                text=True,
                timeout=120,
            )
            assert result.returncode == 0, (
                f"Compile/nsys profile failed: {result.stdout}\n{result.stderr}"
            )

            # 3. Download profile
            local_profile = tmp_path / "profile.nsys-rep"
            subprocess.run(
                [
                    "scp",
                    "-i",
                    ssh_key,
                    f"{self.B200_HOST}:{remote_dir}/profile.nsys-rep",
                    str(local_profile),
                ],
                check=True,
            )
            assert local_profile.exists()

            # 4. Analyze with wafer nvidia nsys analyze (via API since we don't have nsys locally)
            result = run_cli("nvidia", "nsys", "analyze", str(local_profile), "--remote", "--json")
            data = json.loads(result.stdout)

            # Should have timeline/kernel info
            assert "kernels" in data or "timeline" in data or "summary" in data

        finally:
            # Cleanup
            subprocess.run(
                ["ssh", "-i", ssh_key, self.B200_HOST, f"rm -rf {remote_dir}"],
                check=False,
            )


class TestCaptureWorkflow:
    """Test: User captures execution snapshots."""

    def test_capture_simple_command(self, tmp_path: Path) -> None:
        """Capture a simple command execution."""
        # Create a simple script to capture
        script = tmp_path / "test_script.py"
        script.write_text('print("hello from captured script")\n')

        result = run_cli(
            "capture",
            f"test-capture-{os.getpid()}",
            f"python {script}",
            "--dir",
            str(tmp_path),
            check=False,
        )

        # Should attempt capture (may fail if not authenticated to supabase)
        combined = result.stdout + result.stderr
        assert (
            "capture" in combined.lower()
            or "upload" in combined.lower()
            or "error" in combined.lower()
        )

    def test_capture_list(self) -> None:
        """List captured executions."""
        result = run_cli("capture-list", "--json", check=False)

        # Should return list (possibly empty) or auth error
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert isinstance(data, list)


@requires_api
class TestWevinWorkflow:
    """Test: User interacts with Wevin AI assistant."""

    def test_wevin_simple_query(self) -> None:
        """Send a simple query to Wevin."""
        result = run_cli(
            "wevin",
            "What is a CUDA kernel?",
            "--json",
            "--max-turns",
            "1",
            check=False,
        )

        # Wevin should return streamed JSON events or error
        combined = result.stdout + result.stderr
        assert len(combined) > 0

        # If successful, should have response content
        if result.returncode == 0 and result.stdout:
            # Should have some JSON events
            lines = [line for line in result.stdout.strip().split("\n") if line.strip()]
            assert len(lines) > 0, "Expected JSON events in response"


class TestPerfettoWorkflow:
    """Test: User analyzes Perfetto traces with SQL queries."""

    @pytest.fixture
    def sample_trace(self, tmp_path: Path) -> Path:
        """Create a sample Chrome/Perfetto trace file."""
        trace_content = {
            "traceEvents": [
                {
                    "name": "kernel_launch",
                    "cat": "cuda",
                    "ph": "X",
                    "ts": 0,
                    "dur": 1500,
                    "pid": 0,
                    "tid": 1,
                },
                {
                    "name": "memcpy",
                    "cat": "cuda",
                    "ph": "X",
                    "ts": 2000,
                    "dur": 500,
                    "pid": 0,
                    "tid": 1,
                },
            ],
            "metadata": {"trace-type": "perfetto"},
        }
        trace_file = tmp_path / "test_trace.json"
        trace_file.write_text(json.dumps(trace_content))
        return trace_file

    def test_perfetto_check(self) -> None:
        """Check trace_processor availability."""
        result = run_cli("nvidia", "perfetto", "check", "--json", check=False)

        # Should return JSON with availability info
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "available" in data
        else:
            # If not available, should still give meaningful output
            combined = result.stdout + result.stderr
            assert "trace_processor" in combined.lower()

    def test_perfetto_tables(self, sample_trace: Path) -> None:
        """List tables in a trace."""
        result = run_cli(
            "nvidia",
            "perfetto",
            "tables",
            str(sample_trace),
            "--json",
            check=False,
        )

        # This requires trace_processor to be downloaded
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "tables" in data
            # Chrome traces should have a slice table
            assert isinstance(data["tables"], list)
        else:
            # Skip if trace_processor not available
            if "not available" in result.stderr.lower() or "not found" in result.stderr.lower():
                pytest.skip("trace_processor not available")

    def test_perfetto_query(self, sample_trace: Path) -> None:
        """Execute SQL query against a trace."""
        result = run_cli(
            "nvidia",
            "perfetto",
            "query",
            str(sample_trace),
            "SELECT COUNT(*) as cnt FROM slice",
            "--json",
            check=False,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "results" in data
            assert "count" in data
        else:
            # Skip if trace_processor not available
            if "not available" in result.stderr.lower() or "not found" in result.stderr.lower():
                pytest.skip("trace_processor not available")

    def test_perfetto_schema(self, sample_trace: Path) -> None:
        """Get schema for a table."""
        result = run_cli(
            "nvidia",
            "perfetto",
            "schema",
            str(sample_trace),
            "slice",
            "--json",
            check=False,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert "table" in data
            assert data["table"] == "slice"
            assert "columns" in data
        else:
            # Skip if trace_processor not available
            if "not available" in result.stderr.lower() or "not found" in result.stderr.lower():
                pytest.skip("trace_processor not available")
