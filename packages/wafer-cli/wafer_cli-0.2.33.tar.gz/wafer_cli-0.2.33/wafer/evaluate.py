"""Remote kernel evaluation for Wafer CLI.

Runs evaluate.py on a remote GPU target with the same interface as local execution.
"""

import json
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

from wafer_core.utils.kernel_utils.targets.config import (
    BaremetalTarget,
    DigitalOceanTarget,
    LocalTarget,
    ModalTarget,
    RunPodTarget,
    VMTarget,
    WorkspaceTarget,
)

# Map AMD compute capability to ROCm architecture
# Used to set PYTORCH_ROCM_ARCH for faster compilation (compile only for target arch)
AMD_CC_TO_ARCH = {
    "9.4": "gfx942",  # MI300X
    "9.0a": "gfx90a",  # MI200 series
    "9.08": "gfx908",  # MI100
    "9.06": "gfx906",  # MI50/60
    "10.30": "gfx1030",  # RDNA2
    "11.0": "gfx1100",  # RDNA3
}


def _get_rocm_arch(compute_capability: str) -> str | None:
    """Get ROCm architecture string from compute capability.

    Returns gfx* string for PYTORCH_ROCM_ARCH, or None if not found.
    """
    # Already a gfx string
    if compute_capability.startswith("gfx"):
        return compute_capability
    # Map from numeric CC
    return AMD_CC_TO_ARCH.get(compute_capability)


def _build_docker_run_command(
    image: str,
    command: str,
    *,
    working_dir: str | None = None,
    env: dict[str, str] | None = None,
    gpus: str = "all",
    volumes: dict[str, str] | None = None,
    cap_add: list[str] | None = None,
) -> str:
    """Build a docker run command string for NVIDIA GPUs.

    Pure function: string in, string out. No side effects.

    Args:
        image: Docker image name (e.g., "nvcr.io/nvidia/cutlass:4.3-devel")
        command: Command to run inside container
        working_dir: Container working directory (optional)
        env: Environment variables as dict (optional)
        gpus: GPU access string ("all", "device=0", "device=0,1", etc.)
        volumes: Host:container volume mappings (optional)
        cap_add: Linux capabilities to add (e.g., ["SYS_ADMIN"] for NCU profiling)

    Returns:
        Complete docker run command string
    """
    parts = ["docker", "run", "--rm"]

    # Add capabilities (needed for NCU profiling)
    if cap_add:
        for cap in cap_add:
            parts.extend(["--cap-add", cap])

    # GPU access - use single quotes for the device spec to avoid shell escaping issues
    if gpus:
        parts.extend(["--gpus", f"'{gpus}'"])

    # Volume mounts
    if volumes:
        for host_path, container_path in volumes.items():
            parts.extend(["-v", f"{host_path}:{container_path}"])

    # Working directory
    if working_dir:
        parts.extend(["-w", working_dir])

    # Environment variables
    if env:
        for key, value in env.items():
            parts.extend(["-e", f"{key}={shlex.quote(value)}"])

    # Image and command
    parts.append(image)
    parts.append(f"bash -c {shlex.quote(command)}")

    return " ".join(parts)


def _build_docker_run_command_amd(
    image: str,
    command: str,
    *,
    working_dir: str | None = None,
    env: dict[str, str] | None = None,
    volumes: dict[str, str] | None = None,
) -> str:
    """Build a docker run command string for AMD GPUs (ROCm).

    Uses device passthrough instead of NVIDIA's --gpus flag.

    Args:
        image: Docker image name (e.g., "rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0")
        command: Command to run inside container
        working_dir: Container working directory (optional)
        env: Environment variables as dict (optional)
        volumes: Host:container volume mappings (optional)

    Returns:
        Complete docker run command string
    """
    parts = ["docker", "run", "--rm"]

    # AMD GPU access via device passthrough
    parts.extend(["--device=/dev/kfd", "--device=/dev/dri", "--group-add", "video"])

    # Volume mounts
    if volumes:
        for host_path, container_path in volumes.items():
            parts.extend(["-v", f"{host_path}:{container_path}"])

    # Working directory
    if working_dir:
        parts.extend(["-w", working_dir])

    # Environment variables
    if env:
        for key, value in env.items():
            parts.extend(["-e", f"{key}={shlex.quote(value)}"])

    # Image and command
    parts.append(image)
    parts.append(f"bash -c {shlex.quote(command)}")

    return " ".join(parts)


@dataclass(frozen=True)
class EvaluateArgs:
    """Arguments for evaluate command.

    Mirrors evaluate.py's CLI args.
    """

    implementation: Path
    reference: Path
    test_cases: Path
    target_name: str
    benchmark: bool = False
    profile: bool = False
    defensive: bool = False
    sync_artifacts: bool = True
    gpu_id: int | None = None


@dataclass(frozen=True)
class KernelBenchEvaluateArgs:
    """Arguments for KernelBench format evaluate command.

    KernelBench format uses Model/ModelNew classes instead of functions.
    No test_cases file - reference defines get_inputs()/get_init_inputs().
    """

    implementation: Path  # Must define ModelNew class
    reference: Path  # Must define Model, get_inputs, get_init_inputs
    target_name: str
    benchmark: bool = False
    profile: bool = False
    inputs: Path | None = None  # Custom inputs file to override get_inputs()
    seed: int = 42  # Random seed for reproducibility
    defensive: bool = False
    backend: str | None = None  # Kernel backend for static validation
    sync_artifacts: bool = True
    gpu_id: int | None = None
    stages: str = "compile,correctness"  # Stages to run: compile, correctness, benchmark, defense
    prepare_only: bool = False  # Sync files and generate script but don't run


@dataclass(frozen=True)
class EvaluateResult:
    """Result from remote evaluation."""

    success: bool
    all_correct: bool | None  # None when correctness wasn't checked (compile-only, prepare-only)
    correctness_score: float
    geomean_speedup: float
    passed_tests: int
    total_tests: int
    error_message: str | None = None
    artifact_path: Path | None = None


def _check_python_file_has(path: Path, *names: str) -> list[str]:
    """Check if a Python file exports the given names.

    Uses AST parsing to find:
    - Function definitions: def name(...)
    - Class definitions: class name(...)
    - Assignments: name = ...
    - Imports: from module import name / from module import x as name

    Returns:
        List of names that are missing
    """
    import ast

    content = path.read_text()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # If we can't parse, let the runtime fail with a better error
        return []

    defined_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            defined_names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined_names.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                # Use asname if present, otherwise use the original name
                defined_names.add(alias.asname or alias.name)

    return [name for name in names if name not in defined_names]


def _validate_files(args: EvaluateArgs) -> str | None:
    """Validate that all input files exist, have correct format, and expected signatures.

    Returns:
        Error message if validation fails, None if all valid
    """
    if not args.implementation.exists():
        return f"Implementation file not found: {args.implementation}"
    if not args.reference.exists():
        return f"Reference file not found: {args.reference}"
    if not args.test_cases.exists():
        return f"Test cases file not found: {args.test_cases}"

    # Validate test_cases is valid JSON
    try:
        json.loads(args.test_cases.read_text())
    except json.JSONDecodeError:
        if args.test_cases.suffix == ".py":
            return (
                f"--test-cases must be a JSON file, not a Python file: {args.test_cases}\n"
                "Hint: For KernelBench problems, use 'wafer evaluate kernelbench' instead:\n"
                f"  wafer evaluate kernelbench --impl <impl.py> --reference {args.test_cases}"
            )
        return f"--test-cases must be valid JSON: {args.test_cases}"

    # Validate implementation has custom_kernel
    impl_missing = _check_python_file_has(args.implementation, "custom_kernel")
    if impl_missing:
        # Check if it looks like KernelBench format (has ModelNew)
        has_model_new = not _check_python_file_has(args.implementation, "ModelNew")
        if has_model_new:
            return (
                f"Implementation file missing 'custom_kernel' function: {args.implementation}\n"
                "Hint: This looks like KernelBench format. Use 'wafer evaluate kernelbench' instead:\n"
                f"  wafer evaluate kernelbench --impl {args.implementation} --reference <reference.py>"
            )
        return (
            f"Implementation file missing 'custom_kernel' function: {args.implementation}\n"
            "  Required: 'def custom_kernel(inputs)' function"
        )

    # Validate reference has ref_kernel and generate_input
    ref_missing = _check_python_file_has(args.reference, "ref_kernel", "generate_input")
    if ref_missing:
        # Check if it looks like KernelBench format (has Model and get_inputs)
        has_kernelbench = not _check_python_file_has(args.reference, "Model", "get_inputs")
        if has_kernelbench:
            return (
                f"Reference file missing required functions: {', '.join(ref_missing)}\n"
                "Hint: This looks like KernelBench format. Use 'wafer evaluate kernelbench' instead:\n"
                f"  wafer evaluate kernelbench --impl <impl.py> --reference {args.reference}"
            )
        return (
            f"Reference file missing required functions: {', '.join(ref_missing)}\n"
            f"  File: {args.reference}\n"
            "  Required: 'ref_kernel' and 'generate_input' functions"
        )

    return None


def _select_gpu_id(
    target: BaremetalTarget | VMTarget | ModalTarget, gpu_id_override: int | None
) -> int:
    """Select GPU ID to use.

    Args:
        target: Target config
        gpu_id_override: Optional explicit GPU ID

    Returns:
        GPU ID to use
    """
    if gpu_id_override is not None:
        return gpu_id_override

    # Use first GPU from target's list
    if isinstance(target, BaremetalTarget | VMTarget):
        return target.gpu_ids[0]

    # Modal doesn't have explicit GPU IDs
    return 0


def _build_docker_pip_install_cmd(target: BaremetalTarget | VMTarget) -> str:
    """Build pip install command for Docker container.

    Installs uv first, then uses uv to install packages (Modal-like approach).
    Uses --system flag to install to container's system Python (not any venv).

    Handles base CUDA images that may not have pip pre-installed.

    Args:
        target: Target config with pip_packages, torch_package, torch_index_url

    Returns:
        Shell command string to install dependencies
    """
    commands = []

    # Some base images (like nvidia/cuda) don't have pip or git, install them first
    # Use apt for Debian/Ubuntu-based images, with noninteractive to avoid prompts
    commands.append(
        "(which pip > /dev/null 2>&1 && which git > /dev/null 2>&1) || "
        "(apt-get update && "
        "DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-pip git > /dev/null)"
    )

    # Install uv (fast, reliable) - use pip3 for compatibility
    # Use --break-system-packages for Python 3.12+ with PEP 668 externally managed environments
    commands.append("pip3 install --break-system-packages uv")

    # Install torch with custom index if specified (like Modal's two-phase install)
    # Use --system --break-system-packages to install to container's Python
    # (needed for Python 3.12+ with PEP 668 externally managed environments)
    if target.torch_package:
        if target.torch_index_url:
            commands.append(
                f"uv pip install --system --break-system-packages --index-url {target.torch_index_url} "
                f"--extra-index-url https://pypi.org/simple {target.torch_package}"
            )
        else:
            commands.append(
                f"uv pip install --system --break-system-packages {target.torch_package}"
            )

    # Install other packages
    if target.pip_packages:
        packages_str = " ".join(target.pip_packages)
        commands.append(f"uv pip install --system --break-system-packages {packages_str}")

    return " && ".join(commands)


def _get_wafer_root() -> Path:
    """Get wafer monorepo root directory.

    Walks up from this file to find the wafer repo root (contains apps/, packages/).
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "apps").is_dir() and (parent / "packages").is_dir():
            return parent
    raise RuntimeError(f"Could not find wafer root from {__file__}")


async def run_evaluate_docker(
    args: EvaluateArgs,
    target: BaremetalTarget | VMTarget,
) -> EvaluateResult:
    """Run evaluation in Docker container on SSH-based target.

    Uses async SSH client for true non-blocking I/O.
    Uploads wafer-core and runs evaluate.py directly with PYTHONPATH.
    No package installation needed - avoids rollouts dependency.

    Args:
        args: Evaluate arguments
        target: SSH target config with docker_image set

    Returns:
        Evaluation result
    """
    from datetime import datetime

    from wafer_core.async_ssh import AsyncSSHClient

    CONTAINER_WORKSPACE = "/workspace"
    REMOTE_WORKSPACE_BASE = "~/.wafer/workspaces"

    if not target.docker_image:
        raise ValueError("docker_image must be set for Docker execution")

    # Select GPU
    gpu_id = _select_gpu_id(target, args.gpu_id)

    print(f"Connecting to {target.ssh_target}...")

    async with AsyncSSHClient(target.ssh_target, target.ssh_key) as client:
        print(f"Using Docker image: {target.docker_image}")
        print(f"Using GPU {gpu_id}...")

        # Read local files
        impl_code = args.implementation.read_text()
        ref_code = args.reference.read_text()
        test_cases_data = json.loads(args.test_cases.read_text())

        # Create workspace for evaluation files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = f"wafer_eval_{timestamp}"
        eval_workspace = f"{REMOTE_WORKSPACE_BASE}/eval_{timestamp}"
        await client.exec(f"mkdir -p {eval_workspace}")
        eval_workspace_expanded = await client.expand_path(eval_workspace)
        run_path = f"{eval_workspace_expanded}/{run_dir}"

        print("Uploading evaluation files...")

        # Create run directory
        mkdir_result = await client.exec(f"mkdir -p {run_path}")
        if mkdir_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to create run directory: {mkdir_result.stderr}",
            )

        # Write implementation
        impl_path = f"{run_path}/implementation.py"
        write_result = await client.exec(
            f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write implementation: {write_result.stderr}",
            )

        # Write reference
        ref_path = f"{run_path}/reference.py"
        write_result = await client.exec(f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF")
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write reference: {write_result.stderr}",
            )

        # Also write as reference_kernel.py (evaluate.py imports generate_input from this)
        ref_kernel_path = f"{run_path}/reference_kernel.py"
        write_result = await client.exec(
            f"cat > '{ref_kernel_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write reference_kernel: {write_result.stderr}",
            )

        # Write test cases
        test_cases_path = f"{run_path}/test_cases.json"
        test_cases_json = json.dumps(test_cases_data, indent=2)
        write_result = await client.exec(
            f"cat > '{test_cases_path}' << 'TESTS_EOF'\n{test_cases_json}\nTESTS_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write test cases: {write_result.stderr}",
            )

        print("Running evaluation in Docker container...")

        # Paths inside container (workspace mounted at /workspace)
        container_run_path = f"{CONTAINER_WORKSPACE}/{run_dir}"
        container_impl_path = f"{container_run_path}/implementation.py"
        container_ref_path = f"{container_run_path}/reference.py"
        container_test_cases_path = f"{container_run_path}/test_cases.json"

        # Build pip install command for torch and other deps, plus wafer-core
        pip_install_cmd = _build_docker_pip_install_cmd(target)
        install_cmd = (
            f"{pip_install_cmd} && uv pip install --system --break-system-packages wafer-core"
        )

        # Build evaluate command using installed wafer-core module
        python_cmd_parts = [
            "python3 -m wafer_core.utils.kernel_utils.evaluate",
            f"--implementation {container_impl_path}",
            f"--reference {container_ref_path}",
            f"--test-cases {container_test_cases_path}",
            f"--run-dir {container_run_path}",
        ]

        if args.benchmark:
            python_cmd_parts.append("--benchmark")
        if args.profile:
            python_cmd_parts.append("--profile")
        if args.defensive:
            python_cmd_parts.append("--defensive")

        eval_cmd = " ".join(python_cmd_parts)

        # Full command: install deps + wafer-core, then run evaluate
        full_cmd = f"{install_cmd} && cd {container_run_path} && {eval_cmd}"

        # Build Docker run command
        # Add SYS_ADMIN capability when profiling (needed for NCU GPU performance counters)
        docker_cmd = _build_docker_run_command(
            image=target.docker_image,
            command=full_cmd,
            working_dir=container_run_path,
            env={"CUDA_VISIBLE_DEVICES": str(gpu_id), "PYTHONUNBUFFERED": "1"},
            gpus="all",
            volumes={eval_workspace_expanded: CONTAINER_WORKSPACE},
            cap_add=["SYS_ADMIN"] if args.profile else None,
        )

        print(f"Docker command: {docker_cmd[:100]}...")

        # Run Docker command and stream output
        log_lines = []
        async for line in client.exec_stream(docker_cmd):
            print(line, flush=True)
            log_lines.append(line)

        # Read results
        results_path = f"{run_path}/results.json"
        cat_result = await client.exec(f"cat {results_path}")

        if cat_result.exit_code != 0:
            log_tail = "\n".join(log_lines[-50:])
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Evaluation failed. Log tail:\n{log_tail}",
            )

        # Parse results
        try:
            results_data = json.loads(cat_result.stdout)
        except json.JSONDecodeError as e:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to parse results: {e}",
            )

        # Extract backend results
        backends = results_data.get("backends", [])
        if not backends:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message="No backend results found",
            )

        backend = backends[0]
        correctness_tests = backend.get("correctness_tests", [])
        passed = sum(1 for t in correctness_tests if t.get("is_correct", False))
        total = len(correctness_tests)

        # Sync artifacts if requested
        artifact_path = None
        if args.sync_artifacts:
            local_artifact_dir = Path.cwd() / "wafer_artifacts" / run_dir
            local_artifact_dir.mkdir(parents=True, exist_ok=True)

            try:
                # Download results.json
                download_result = await client.download_files(
                    remote_path=f"{run_path}/results.json",
                    local_path=str(local_artifact_dir / "results.json"),
                )
                if download_result.success:
                    artifact_path = local_artifact_dir
                    print(f"Artifacts saved to: {artifact_path}")
                else:
                    print(f"Warning: Failed to sync results.json: {download_result.error_message}")

                # Download NCU profiles if they exist (from --profile flag)
                # NCU profiles are stored in artifact/ncu/ subdirectory
                ncu_check = await client.exec(f"test -d {run_path}/artifact/ncu")
                if ncu_check.exit_code == 0:
                    local_ncu_dir = local_artifact_dir / "ncu"
                    local_ncu_dir.mkdir(parents=True, exist_ok=True)
                    ncu_result = await client.download_files(
                        remote_path=f"{run_path}/artifact/ncu",
                        local_path=str(local_ncu_dir),
                        recursive=True,
                    )
                    if ncu_result.success:
                        print(f"NCU profiles synced: {ncu_result.files_copied} files")
                    else:
                        print(f"Warning: Failed to sync NCU profiles: {ncu_result.error_message}")
            except Exception as e:
                print(f"Warning: Failed to sync artifacts: {e}")

        return EvaluateResult(
            success=True,
            all_correct=backend.get("all_correct", False),
            correctness_score=backend.get("correctness_score", 0.0),
            geomean_speedup=backend.get("geomean_speedup", 0.0),
            passed_tests=passed,
            total_tests=total,
            artifact_path=artifact_path,
        )


async def run_evaluate_local(
    args: EvaluateArgs,
    target: LocalTarget,
) -> EvaluateResult:
    """Run evaluation locally on the current machine.

    For LocalTarget - no SSH needed, runs directly.

    Args:
        args: Evaluate arguments
        target: Local target config

    Returns:
        Evaluation result
    """
    import os
    import subprocess
    import tempfile
    from datetime import datetime

    # Select GPU
    gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]

    print(f"Running local evaluation on GPU {gpu_id}...")

    # Create temp directory for eval files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with tempfile.TemporaryDirectory(prefix=f"wafer_eval_{timestamp}_") as run_path:
        run_path = Path(run_path)

        # Write implementation
        impl_path = run_path / "implementation.py"
        impl_path.write_text(args.implementation.read_text())

        # Write reference
        ref_path = run_path / "reference.py"
        ref_path.write_text(args.reference.read_text())

        # Write custom inputs if provided
        inputs_path = None
        if args.inputs:
            inputs_path = run_path / "custom_inputs.py"
            inputs_path.write_text(args.inputs.read_text())

        # Write eval script
        eval_script_path = run_path / "kernelbench_eval.py"
        eval_script_path.write_text(KERNELBENCH_EVAL_SCRIPT)

        # Write defense module if defensive mode is enabled
        defense_module_path = None
        if args.defensive:
            defense_src = (
                Path(__file__).parent.parent.parent.parent
                / "packages"
                / "wafer-core"
                / "wafer_core"
                / "utils"
                / "kernel_utils"
                / "defense.py"
            )
            if defense_src.exists():
                defense_module_path = run_path / "defense.py"
                defense_module_path.write_text(defense_src.read_text())
            else:
                print(f"Warning: defense.py not found at {defense_src}")

        # Output file
        output_path = run_path / "results.json"

        # Build eval command
        cmd_parts = [
            "python3",
            str(eval_script_path),
            "--impl",
            str(impl_path),
            "--reference",
            str(ref_path),
            "--output",
            str(output_path),
            "--seed",
            str(args.seed),
        ]

        if args.benchmark:
            cmd_parts.append("--benchmark")
        if args.profile:
            cmd_parts.append("--profile")
        if inputs_path:
            cmd_parts.extend(["--inputs", str(inputs_path)])
        if args.defensive and defense_module_path:
            cmd_parts.extend(["--defensive", "--defense-module", str(defense_module_path)])

        # Set environment for GPU selection
        env = os.environ.copy()
        if target.vendor == "nvidia":
            env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        else:  # AMD
            env["HIP_VISIBLE_DEVICES"] = str(gpu_id)
            env["ROCM_PATH"] = "/opt/rocm"

        print(f"Running: {' '.join(cmd_parts[:4])} ...")

        # Run evaluation
        try:
            result = subprocess.run(
                cmd_parts,
                cwd=str(run_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=args.timeout or 600,
            )
        except subprocess.TimeoutExpired:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message="Evaluation timed out",
            )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            # Truncate long errors
            if len(error_msg) > 1000:
                error_msg = error_msg[:500] + "\n...\n" + error_msg[-500:]
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Evaluation failed:\n{error_msg}",
            )

        # Parse results
        if not output_path.exists():
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message="No results.json produced",
            )

        try:
            results = json.loads(output_path.read_text())
        except json.JSONDecodeError as e:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to parse results: {e}",
            )

        # Extract results
        return EvaluateResult(
            success=True,
            all_correct=results.get("all_correct", False),
            correctness_score=results.get("correctness_score", 0.0),
            geomean_speedup=results.get("geomean_speedup", 0.0),
            passed_tests=results.get("passed_tests", 0),
            total_tests=results.get("total_tests", 0),
            benchmark_results=results.get("benchmark", {}),
        )


async def run_evaluate_ssh(
    args: EvaluateArgs,
    target: BaremetalTarget | VMTarget,
) -> EvaluateResult:
    """Run evaluation on SSH-based target (Baremetal or VM).

    Routes to Docker or venv execution based on target.docker_image.

    If docker_image is set:
    - Uses Docker container with GPU passthrough
    - Installs deps via uv inside container (Modal-like)

    If docker_image is not set:
    - Uses the existing venv-based deployment infrastructure

    Args:
        args: Evaluate arguments
        target: SSH target config

    Returns:
        Evaluation result
    """
    # Route to Docker execution if docker_image is set
    if target.docker_image:
        return await run_evaluate_docker(args, target)

    # Otherwise, use venv-based execution (existing path)
    from datetime import datetime

    from wafer_core.remote_jobs import (
        LogStreamConfig,
        start_tmux_session,
        stream_log_until_complete,
    )
    from wafer_core.utils.kernel_utils.deployment import (
        DeploymentConfig,
        setup_deployment,
    )

    # Select GPU
    gpu_id = _select_gpu_id(target, args.gpu_id)

    # Create deployment config
    config = DeploymentConfig(
        ssh_target=target.ssh_target,
        ssh_key=target.ssh_key,
        gpu_id=gpu_id,
    )

    print(f"Connecting to {target.ssh_target}...")

    # Setup deployment (expensive - deploys monorepo + creates venv)
    state, err = await setup_deployment(config)
    if err:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Deployment setup failed: {err}",
        )

    assert state is not None

    print(f"Using GPU {gpu_id}...")

    # Read local files
    impl_code = args.implementation.read_text()
    ref_code = args.reference.read_text()
    test_cases_data = json.loads(args.test_cases.read_text())

    # Create a unique run directory within the deployed workspace
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = f"wafer_eval_{timestamp}"

    # workspace_path is the project path (e.g., .../research/async-wevin/benchmarks/gpumode)
    workspace = state.workspace_path
    run_path = f"{workspace}/{run_dir}"

    # Get SSH client from deployment state
    client = state.ssh_client

    print("Uploading files...")

    # Create run directory
    mkdir_result = client.exec(f"mkdir -p {run_path}")
    if mkdir_result.exit_code != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to create run directory: {mkdir_result.stderr}",
        )

    # Write implementation (must define custom_kernel function)
    impl_path = f"{run_path}/implementation.py"
    write_result = client.exec(f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF")
    if write_result.exit_code != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to write implementation: {write_result.stderr}",
        )

    # Write reference (must define ref_kernel function)
    ref_path = f"{run_path}/reference.py"
    write_result = client.exec(f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF")
    if write_result.exit_code != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to write reference: {write_result.stderr}",
        )

    # Also write as reference_kernel.py (evaluate.py imports generate_input from this)
    ref_kernel_path = f"{run_path}/reference_kernel.py"
    write_result = client.exec(f"cat > '{ref_kernel_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF")
    if write_result.exit_code != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to write reference_kernel: {write_result.stderr}",
        )

    # Write test cases
    test_cases_path = f"{run_path}/test_cases.json"
    test_cases_json = json.dumps(test_cases_data, indent=2)
    write_result = client.exec(
        f"cat > '{test_cases_path}' << 'TESTS_EOF'\n{test_cases_json}\nTESTS_EOF"
    )
    if write_result.exit_code != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to write test cases: {write_result.stderr}",
        )

    print("Running evaluation...")

    # Build evaluate command
    # The deployment deploys to research/async-wevin/benchmarks/gpumode
    # evaluate.py is at research/async-wevin/wafer_utils/kernel_utils/evaluate.py
    # So we need to go up 2 levels from workspace to find async-wevin root
    # workspace = .../research/async-wevin/benchmarks/gpumode
    # async_wevin_root = .../research/async-wevin
    async_wevin_root = "/".join(workspace.rstrip("/").split("/")[:-2])
    evaluate_script = f"{async_wevin_root}/wafer_utils/kernel_utils/evaluate.py"

    env_state = state.env_state

    eval_cmd_parts = [
        f"cd {run_path} &&",
        f"PATH={env_state.venv_bin}:$PATH",
        f"{env_state.venv_python} {evaluate_script}",
        f"--implementation {impl_path}",
        f"--reference {ref_path}",
        f"--test-cases {test_cases_path}",
        f"--run-dir {run_path}",
    ]

    if args.benchmark:
        eval_cmd_parts.append("--benchmark")
    if args.profile:
        eval_cmd_parts.append("--profile")
    if args.defensive:
        eval_cmd_parts.append("--defensive")

    eval_cmd = " ".join(eval_cmd_parts)

    # Run via tmux for streaming output
    session_name = f"wafer_eval_{datetime.now().strftime('%H%M%S')}"
    log_file = f"{run_path}/evaluate.log"

    _, err = start_tmux_session(
        client=client,
        session_name=session_name,
        command=eval_cmd,
        workspace=run_path,
        log_file=log_file,
        env_vars={
            "CUDA_VISIBLE_DEVICES": str(gpu_id),
            "PYTHONUNBUFFERED": "1",
        },
    )

    if err:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to start evaluation: {err}",
        )

    # Stream logs until completion
    stream_config = LogStreamConfig(
        session_name=session_name,
        log_file=log_file,
        timeout_sec=600,  # 10 minutes max
        poll_interval_sec=2.0,
    )

    _ = stream_log_until_complete(client=client, config=stream_config)

    # Read results
    results_path = f"{run_path}/results.json"
    cat_result = client.exec(f"cat {results_path}")

    if cat_result.exit_code != 0:
        # Try to get error from log
        log_result = client.exec(f"tail -50 {log_file}")
        log_tail = log_result.stdout if log_result.exit_code == 0 else ""
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Evaluation failed. Log tail:\n{log_tail}",
        )

    # Parse results
    try:
        results_data = json.loads(cat_result.stdout)
    except json.JSONDecodeError as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to parse results: {e}",
        )

    # Extract backend results
    # Results format: {"backends": [{"backend_name": ..., "correctness_score": ..., ...}]}
    backends = results_data.get("backends", [])
    if not backends:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message="No backend results found",
        )

    backend = backends[0]
    correctness_tests = backend.get("correctness_tests", [])
    passed = sum(1 for t in correctness_tests if t.get("is_correct", False))
    total = len(correctness_tests)

    # Sync artifacts if requested
    artifact_path = None
    if args.sync_artifacts:
        local_artifact_dir = Path.cwd() / "wafer_artifacts" / run_dir
        local_artifact_dir.mkdir(parents=True, exist_ok=True)

        # Download results and logs
        try:
            client.download_files(
                remote_path=f"{run_path}/results.json",
                local_path=str(local_artifact_dir / "results.json"),
            )
            client.download_files(
                remote_path=log_file,
                local_path=str(local_artifact_dir / "evaluate.log"),
            )
            artifact_path = local_artifact_dir
            print(f"Artifacts saved to: {artifact_path}")
        except Exception as e:
            print(f"Warning: Failed to sync artifacts: {e}")

    return EvaluateResult(
        success=True,
        all_correct=backend.get("all_correct", False),
        correctness_score=backend.get("correctness_score", 0.0),
        geomean_speedup=backend.get("geomean_speedup", 0.0),
        passed_tests=passed,
        total_tests=total,
        artifact_path=artifact_path,
    )


def _build_modal_sandbox_script(
    target: ModalTarget,
    impl_code_b64: str,
    ref_code_b64: str,
    test_cases_b64: str,
    run_benchmarks: bool,
    run_defensive: bool,
    defense_code_b64: str | None = None,
) -> str:
    """Build Python script to create sandbox and run evaluation.

    This runs in a subprocess to isolate Modal's asyncio from trio.
    """
    gpu_type = target.gpu_type

    # Determine PyTorch index and CUDA arch based on GPU type
    if gpu_type in ("B200", "GB200"):
        torch_index = "https://download.pytorch.org/whl/cu130"
        cuda_arch_list = "10.0"  # Blackwell (sm_100)
    elif gpu_type == "H100":
        torch_index = "https://download.pytorch.org/whl/cu130"
        cuda_arch_list = "9.0"  # Hopper (sm_90)
    else:
        torch_index = "https://download.pytorch.org/whl/cu124"
        cuda_arch_list = "8.0"  # Default to Ampere (sm_80)

    return f'''
import asyncio
import base64
import json
import sys
import modal

async def run_eval():
    app = modal.App.lookup("wafer-evaluate", create_if_missing=True)

    # Build image with PyTorch and dependencies
    image = (
        modal.Image.from_registry(
            "nvidia/cuda:12.9.0-devel-ubuntu22.04",
            add_python="3.12",
        )
        .apt_install("git", "build-essential", "cmake", "ripgrep")
        .pip_install(
            "torch",
            index_url="{torch_index}",
            extra_index_url="https://pypi.org/simple",
        )
        .pip_install(
            "numpy",
            "triton",
            "ninja",
        )
        .env({{
            "CUDA_HOME": "/usr/local/cuda",
            # C++ compiler needs explicit include path for cuda_runtime.h
            "CPLUS_INCLUDE_PATH": "/usr/local/cuda/include",
            # Linker needs lib path
            "LIBRARY_PATH": "/usr/local/cuda/lib64",
            # Force PyTorch to compile for correct GPU architecture
            "TORCH_CUDA_ARCH_LIST": "{cuda_arch_list}",
        }})
    )

    # Create sandbox
    sandbox = modal.Sandbox.create(
        app=app,
        image=image,
        gpu="{gpu_type}",
        timeout={target.timeout_seconds},
    )

    try:
        # Decode files
        impl_code = base64.b64decode("{impl_code_b64}").decode()
        ref_code = base64.b64decode("{ref_code_b64}").decode()
        test_cases = base64.b64decode("{test_cases_b64}").decode()

        # Write files to sandbox
        sandbox.exec("mkdir", "-p", "/workspace").wait()

        # Write implementation
        proc = sandbox.exec("python", "-c", f"""
import base64
with open('/workspace/kernel.py', 'w') as f:
    f.write(base64.b64decode('{impl_code_b64}').decode())
with open('/workspace/reference.py', 'w') as f:
    f.write(base64.b64decode('{ref_code_b64}').decode())
with open('/workspace/reference_kernel.py', 'w') as f:
    f.write(base64.b64decode('{ref_code_b64}').decode())
with open('/workspace/test_cases.json', 'w') as f:
    f.write(base64.b64decode('{test_cases_b64}').decode())
print('Files written')
""")
        proc.wait()
        if proc.returncode != 0:
            print(json.dumps({{"error": f"Failed to write files: {{proc.stderr.read()}}"}}))
            return

        # Write defense module if defensive mode is enabled
        # NOTE: Check for actual base64 content, not just truthy string (None becomes "None")
        if {run_defensive} and "{defense_code_b64}" and "{defense_code_b64}" != "None":
            proc = sandbox.exec("python", "-c", f"""
import base64
with open('/workspace/defense.py', 'w') as f:
    f.write(base64.b64decode('{defense_code_b64}').decode())
print('Defense module written')
""")
            proc.wait()
            if proc.returncode != 0:
                print(json.dumps({{"error": f"Failed to write defense module: {{proc.stderr.read()}}"}}))
                return

        # Build inline evaluation script
        eval_script = """
import json
import sys
import os
import importlib.util

os.chdir('/workspace')
sys.path.insert(0, '/workspace')

# Load test cases
with open('test_cases.json') as f:
    test_cases = json.load(f)

# Load kernels
def load_fn(path, name):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, name)

custom_kernel = load_fn('kernel.py', 'custom_kernel')
ref_kernel = load_fn('reference.py', 'ref_kernel')
generate_input = load_fn('reference.py', 'generate_input')

import torch

# Load defense module if available and defensive mode is enabled
run_defensive = {run_defensive}
defense = None
if run_defensive:
    try:
        defense = load_fn('defense.py', 'run_all_defenses')
        time_with_defenses = load_fn('defense.py', 'time_execution_with_defenses')
        print('[Defense] Defense module loaded')

        # Wrap kernels for defense API compatibility
        # Defense API calls kernel(*args), but functional format expects kernel(inputs_tuple)
        # These wrappers repack the unpacked args back into a tuple
        def _wrap_for_defense(kernel):
            return lambda *args: kernel(args)
        custom_kernel_for_defense = _wrap_for_defense(custom_kernel)
        ref_kernel_for_defense = _wrap_for_defense(ref_kernel)
    except Exception as e:
        print(f'[Defense] Warning: Could not load defense module: {{e}}')
        defense = None

results = []
all_correct = True
total_time_ms = 0.0
ref_total_time_ms = 0.0

for tc in test_cases:
    name = tc.pop('name', 'test')
    try:
        inputs = generate_input(**tc)

        # Correctness check - pass inputs as single arg (wafer-core convention)
        with torch.no_grad():
            ref_out = ref_kernel(inputs)
            impl_out = custom_kernel(inputs)

        if isinstance(ref_out, torch.Tensor):
            correct = torch.allclose(ref_out, impl_out, rtol=1e-3, atol=1e-3)
        else:
            correct = ref_out == impl_out

        if not correct:
            all_correct = False

        # Benchmark if requested
        impl_time_ms = 0.0
        ref_time_ms = 0.0
        if {run_benchmarks}:
            if run_defensive and defense is not None:
                # Use full defense suite with wrapped kernels
                # inputs_list unpacks the tuple so defense can infer dtype/device from tensors
                inputs_list = list(inputs) if hasattr(inputs, '__iter__') and not isinstance(inputs, torch.Tensor) else [inputs]

                # Run defense checks
                all_passed, defense_results, _ = defense(custom_kernel_for_defense, *inputs_list)
                if not all_passed:
                    failed = [name for name, passed, _ in defense_results if not passed]
                    raise ValueError(f"Defense checks failed: {{failed}}")

                # Time with defensive timing (using wrapped kernels)
                impl_times, _ = time_with_defenses(
                    custom_kernel_for_defense,
                    inputs_list,
                    num_warmup=3,
                    num_trials=10,
                    verbose=False,
                    run_defenses=False,
                )
                impl_time_ms = sum(impl_times) / len(impl_times)

                ref_times, _ = time_with_defenses(
                    ref_kernel_for_defense,
                    inputs_list,
                    num_warmup=3,
                    num_trials=10,
                    verbose=False,
                    run_defenses=False,
                )
                ref_time_ms = sum(ref_times) / len(ref_times)
            else:
                # Standard timing without full defenses
                # Warmup
                for _ in range(3):
                    custom_kernel(inputs)
                torch.cuda.synchronize()

                start = torch.cuda.Event(enable_timing=True)
                end = torch.cuda.Event(enable_timing=True)
                start.record()
                for _ in range(10):
                    custom_kernel(inputs)
                end.record()
                torch.cuda.synchronize()
                impl_time_ms = start.elapsed_time(end) / 10

                # Reference timing
                for _ in range(3):
                    ref_kernel(inputs)
                torch.cuda.synchronize()
                start.record()
                for _ in range(10):
                    ref_kernel(inputs)
                end.record()
                torch.cuda.synchronize()
                ref_time_ms = start.elapsed_time(end) / 10

            total_time_ms += impl_time_ms
            ref_total_time_ms += ref_time_ms

        results.append({{
            'name': name,
            'correct': correct,
            'impl_time_ms': impl_time_ms,
            'ref_time_ms': ref_time_ms,
        }})

    except Exception as e:
        results.append({{'name': name, 'correct': False, 'error': str(e)}})
        all_correct = False

# Calculate speedup
speedup = 0.0
if total_time_ms > 0 and ref_total_time_ms > 0:
    speedup = ref_total_time_ms / total_time_ms

passed = sum(1 for r in results if r.get('correct', False))
total = len(results)

print(json.dumps({{
    'success': True,
    'all_correct': all_correct,
    'passed': passed,
    'total': total,
    'speedup': speedup,
    'results': results,
}}))
"""

        # Run evaluation
        proc = sandbox.exec(
            "python", "-c", eval_script,
            timeout={target.timeout_seconds},
        )
        proc.wait()

        stdout = proc.stdout.read()
        stderr = proc.stderr.read()

        if proc.returncode != 0:
            print(json.dumps({{"error": f"Eval failed: {{stderr or stdout}}"}}))
            return

        # Forward the result JSON
        # Find the last JSON line in output
        for line in reversed(stdout.strip().split("\\n")):
            if line.startswith("{{"):
                print(line, flush=True)
                return

        print(json.dumps({{"error": f"No result JSON in output: {{stdout[:500]}}"}}))

    finally:
        sandbox.terminate()

asyncio.run(run_eval())
'''


async def run_evaluate_modal(
    args: EvaluateArgs,
    target: ModalTarget,
) -> EvaluateResult:
    """Run evaluation on Modal sandbox.

    Creates a Modal sandbox, uploads files, runs evaluate, and parses results.
    Uses subprocess to isolate Modal's asyncio from trio.

    Args:
        args: Evaluate arguments
        target: Modal target config

    Returns:
        Evaluation result
    """
    import base64
    import subprocess
    import sys

    import trio

    print(f"Creating Modal sandbox ({target.gpu_type})...")

    # Encode files as base64
    impl_code_b64 = base64.b64encode(args.implementation.read_bytes()).decode()
    ref_code_b64 = base64.b64encode(args.reference.read_bytes()).decode()
    test_cases_b64 = base64.b64encode(args.test_cases.read_bytes()).decode()

    # Encode defense module if defensive mode is enabled
    defense_code_b64 = None
    if args.defensive:
        defense_path = (
            Path(__file__).parent.parent.parent.parent
            / "packages"
            / "wafer-core"
            / "wafer_core"
            / "utils"
            / "kernel_utils"
            / "defense.py"
        )
        if defense_path.exists():
            defense_code_b64 = base64.b64encode(defense_path.read_bytes()).decode()
        else:
            print(f"Warning: defense.py not found at {defense_path}, falling back to basic defense")

    # Build the script that creates sandbox and runs eval
    script = _build_modal_sandbox_script(
        target=target,
        impl_code_b64=impl_code_b64,
        ref_code_b64=ref_code_b64,
        test_cases_b64=test_cases_b64,
        run_benchmarks=args.benchmark,
        run_defensive=args.defensive,
        defense_code_b64=defense_code_b64,
    )

    def _run_subprocess() -> tuple[str, str, int]:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=target.timeout_seconds + 60,  # Extra buffer for sandbox creation
        )
        return result.stdout, result.stderr, result.returncode

    try:
        stdout, stderr, returncode = await trio.to_thread.run_sync(_run_subprocess)
    except subprocess.TimeoutExpired:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Modal evaluation timed out after {target.timeout_seconds}s",
        )
    except Exception as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to run Modal sandbox: {e}",
        )

    if returncode != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Modal sandbox failed (exit {returncode}): {stderr or stdout}",
        )

    # Parse result JSON from stdout
    result_json = None
    for line in reversed(stdout.strip().split("\n")):
        if line.startswith("{"):
            try:
                result_json = json.loads(line)
                break
            except json.JSONDecodeError:
                continue

    if result_json is None:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"No valid JSON result in output: {stdout[:500]}",
        )

    if "error" in result_json:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=result_json["error"],
        )

    passed = result_json.get("passed", 0)
    total = result_json.get("total", 0)
    correctness = passed / total if total > 0 else 0.0

    return EvaluateResult(
        success=True,
        all_correct=result_json.get("all_correct", False),
        correctness_score=correctness,
        geomean_speedup=result_json.get("speedup", 0.0),
        passed_tests=passed,
        total_tests=total,
    )


def _build_workspace_eval_script(
    impl_code: str,
    ref_code: str,
    test_cases_json: str,
    run_benchmarks: bool,
    run_defensive: bool = False,
    defense_code: str | None = None,
) -> str:
    """Build inline evaluation script for workspace exec.

    Similar to Modal inline eval, but runs via workspace exec.
    """
    import base64

    impl_b64 = base64.b64encode(impl_code.encode()).decode()
    ref_b64 = base64.b64encode(ref_code.encode()).decode()
    tests_b64 = base64.b64encode(test_cases_json.encode()).decode()
    defense_b64 = base64.b64encode(defense_code.encode()).decode() if defense_code else ""

    return f'''
import base64
import json
import sys
import os
import importlib.util

# Decode files
impl_code = base64.b64decode("{impl_b64}").decode()
ref_code = base64.b64decode("{ref_b64}").decode()
test_cases = json.loads(base64.b64decode("{tests_b64}").decode())

# Write to temp files
with open("/tmp/kernel.py", "w") as f:
    f.write(impl_code)
with open("/tmp/reference.py", "w") as f:
    f.write(ref_code)

# Write defense module if available
run_defensive = {run_defensive}
defense_b64 = "{defense_b64}"
# NOTE: Check defense_b64 is not empty and not the string "None" (from None formatting)
if run_defensive and defense_b64 and defense_b64 != "None":
    defense_code = base64.b64decode(defense_b64).decode()
    with open("/tmp/defense.py", "w") as f:
        f.write(defense_code)

# Load kernels
def load_fn(path, name):
    spec = importlib.util.spec_from_file_location("mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, name)

custom_kernel = load_fn("/tmp/kernel.py", "custom_kernel")
ref_kernel = load_fn("/tmp/reference.py", "ref_kernel")
generate_input = load_fn("/tmp/reference.py", "generate_input")

import torch

# Load defense module if available
defense = None
if run_defensive and defense_b64 and defense_b64 != "None":
    try:
        defense = load_fn("/tmp/defense.py", "run_all_defenses")
        time_with_defenses = load_fn("/tmp/defense.py", "time_execution_with_defenses")
        print("[Defense] Defense module loaded")

        # Wrap kernels for defense API compatibility
        # Defense API calls kernel(*args), but functional format expects kernel(inputs_tuple)
        def _wrap_for_defense(kernel):
            return lambda *args: kernel(args)
        custom_kernel_for_defense = _wrap_for_defense(custom_kernel)
        ref_kernel_for_defense = _wrap_for_defense(ref_kernel)
    except Exception as e:
        print(f"[Defense] Warning: Could not load defense module: {{e}}")
        defense = None

results = []
all_correct = True
total_time_ms = 0.0
ref_total_time_ms = 0.0

for tc in test_cases:
    name = tc.pop("name", "test")
    try:
        inputs = generate_input(**tc)

        # Correctness check - pass inputs as single arg (wafer-core convention)
        with torch.no_grad():
            ref_out = ref_kernel(inputs)
            impl_out = custom_kernel(inputs)

        if isinstance(ref_out, torch.Tensor):
            correct = torch.allclose(ref_out, impl_out, rtol=1e-3, atol=1e-3)
        else:
            correct = ref_out == impl_out

        if not correct:
            all_correct = False

        # Benchmark if requested
        impl_time_ms = 0.0
        ref_time_ms = 0.0
        if {run_benchmarks}:
            if run_defensive and defense is not None:
                # Use full defense suite with wrapped kernels
                inputs_list = list(inputs) if hasattr(inputs, '__iter__') and not isinstance(inputs, torch.Tensor) else [inputs]

                # Run defense checks
                all_passed, defense_results, _ = defense(custom_kernel_for_defense, *inputs_list)
                if not all_passed:
                    failed = [name for name, passed, _ in defense_results if not passed]
                    raise ValueError(f"Defense checks failed: {{failed}}")

                # Time with defensive timing (using wrapped kernels)
                impl_times, _ = time_with_defenses(
                    custom_kernel_for_defense,
                    inputs_list,
                    num_warmup=3,
                    num_trials=10,
                    verbose=False,
                    run_defenses=False,
                )
                impl_time_ms = sum(impl_times) / len(impl_times)

                ref_times, _ = time_with_defenses(
                    ref_kernel_for_defense,
                    inputs_list,
                    num_warmup=3,
                    num_trials=10,
                    verbose=False,
                    run_defenses=False,
                )
                ref_time_ms = sum(ref_times) / len(ref_times)
            else:
                # Standard timing
                for _ in range(3):
                    custom_kernel(inputs)
                torch.cuda.synchronize()

                start = torch.cuda.Event(enable_timing=True)
                end = torch.cuda.Event(enable_timing=True)
                start.record()
                for _ in range(10):
                    custom_kernel(inputs)
                end.record()
                torch.cuda.synchronize()
                impl_time_ms = start.elapsed_time(end) / 10

                for _ in range(3):
                    ref_kernel(inputs)
                torch.cuda.synchronize()
                start.record()
                for _ in range(10):
                    ref_kernel(inputs)
                end.record()
                torch.cuda.synchronize()
                ref_time_ms = start.elapsed_time(end) / 10

            total_time_ms += impl_time_ms
            ref_total_time_ms += ref_time_ms

        results.append({{
            "name": name,
            "correct": correct,
            "impl_time_ms": impl_time_ms,
            "ref_time_ms": ref_time_ms,
        }})

    except Exception as e:
        results.append({{"name": name, "correct": False, "error": str(e)}})
        all_correct = False

# Calculate speedup
speedup = 0.0
if total_time_ms > 0 and ref_total_time_ms > 0:
    speedup = ref_total_time_ms / total_time_ms

passed = sum(1 for r in results if r.get("correct", False))
total = len(results)

print(json.dumps({{
    "success": True,
    "all_correct": all_correct,
    "passed": passed,
    "total": total,
    "speedup": speedup,
    "results": results,
}}))
'''


async def run_evaluate_workspace(
    args: EvaluateArgs,
    target: WorkspaceTarget,
) -> EvaluateResult:
    """Run evaluation on wafer-api managed workspace.

    Uses inline evaluation (no file sync needed) via workspace exec.
    The eval script is passed as a Python command with base64-encoded files.

    Args:
        args: Evaluate arguments
        target: Workspace target config

    Returns:
        Evaluation result
    """
    import trio

    from .workspaces import exec_command

    print(f"Using workspace: {target.workspace_id}")

    # Read files
    impl_code = args.implementation.read_text()
    ref_code = args.reference.read_text()
    test_cases_json = args.test_cases.read_text()

    # Read defense module if defensive mode is enabled
    defense_code = None
    if args.defensive:
        defense_path = (
            Path(__file__).parent.parent.parent.parent
            / "packages"
            / "wafer-core"
            / "wafer_core"
            / "utils"
            / "kernel_utils"
            / "defense.py"
        )
        if defense_path.exists():
            defense_code = defense_path.read_text()
        else:
            print(f"Warning: defense.py not found at {defense_path}, falling back to basic defense")

    # Build inline eval script
    eval_script = _build_workspace_eval_script(
        impl_code=impl_code,
        ref_code=ref_code,
        test_cases_json=test_cases_json,
        run_benchmarks=args.benchmark,
        run_defensive=args.defensive,
        defense_code=defense_code,
    )

    # Execute via workspace exec
    # Use python -c with the script
    eval_cmd = f"python -c {shlex.quote(eval_script)}"

    print("Running evaluation...")

    # Capture stdout by redirecting exec output
    # exec_command prints to stdout, we need to capture it
    import io
    import sys

    captured_output = io.StringIO()
    original_stdout = sys.stdout

    def _exec() -> int:
        # Temporarily redirect stdout to capture output
        sys.stdout = captured_output
        try:
            return exec_command(
                workspace_id=target.workspace_id,
                command=eval_cmd,
                timeout_seconds=target.timeout_seconds,
            )
        finally:
            sys.stdout = original_stdout

    try:
        exit_code = await trio.to_thread.run_sync(_exec)
    except Exception as e:
        sys.stdout = original_stdout
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Execution failed: {e}",
        )

    # Parse output
    output = captured_output.getvalue()
    print(output)  # Show output to user

    # Find JSON result in output
    result_json = None
    for line in reversed(output.strip().split("\n")):
        if line.startswith("{"):
            try:
                result_json = json.loads(line)
                break
            except json.JSONDecodeError:
                continue

    if result_json is None:
        if exit_code == 0:
            return EvaluateResult(
                success=True,
                all_correct=True,
                correctness_score=1.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
            )
        else:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Evaluation failed with exit code {exit_code}",
            )

    if "error" in result_json:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=result_json["error"],
        )

    passed = result_json.get("passed", 0)
    total = result_json.get("total", 0)
    correctness = passed / total if total > 0 else 0.0

    return EvaluateResult(
        success=True,
        all_correct=result_json.get("all_correct", False),
        correctness_score=correctness,
        geomean_speedup=result_json.get("speedup", 0.0),
        passed_tests=passed,
        total_tests=total,
    )


async def run_evaluate_runpod(
    args: EvaluateArgs,
    target: RunPodTarget,
) -> EvaluateResult:
    """Run evaluation on RunPod target.

    Provisions a RunPod pod (or reuses existing), runs evaluation via SSH,
    then cleans up based on keep_alive setting.

    Sets up a Python venv with ROCm torch using uv, then runs evaluation.

    Args:
        args: Evaluate arguments
        target: RunPod target config

    Returns:
        Evaluation result
    """
    from datetime import datetime

    from wafer_core.async_ssh import AsyncSSHClient
    from wafer_core.remote_env import async_setup_python_env
    from wafer_core.targets.runpod import RunPodError, runpod_ssh_context

    REMOTE_WORKSPACE = "/tmp/wafer_eval"
    ROCM_TORCH_INDEX_URL = "https://download.pytorch.org/whl/rocm6.2"
    ROCM_TORCH_VERSION_SUFFIX = "+rocm6.2"

    print(f"Provisioning RunPod ({target.gpu_type_id})...")

    try:
        async with runpod_ssh_context(target) as ssh_info:
            ssh_target = f"{ssh_info.user}@{ssh_info.host}:{ssh_info.port}"
            print(f"Connected to RunPod: {ssh_target}")

            async with AsyncSSHClient(ssh_target, target.ssh_key) as client:
                # Ensure rsync is installed (needed for file uploads)
                print("Checking rsync...")
                result = await client.exec("which rsync || echo 'NOT_FOUND'")
                if "NOT_FOUND" in result.stdout:
                    print("Installing rsync...")
                    await client.exec("apt-get update && apt-get install -y rsync")

                # Setup Python environment with ROCm torch
                # Match wafer-core dependencies needed for evaluate.py
                print("Setting up Python environment with ROCm torch...")
                requirements = [
                    f"torch==2.5.1{ROCM_TORCH_VERSION_SUFFIX}",
                    "numpy",
                    "ninja",
                    "setuptools",
                    # wafer_core dependencies
                    "trio",
                    "httpx",
                    "pydantic",
                    "anyio",
                    "pyyaml",
                ]

                try:
                    env_state = await async_setup_python_env(
                        client=client,
                        workspace=REMOTE_WORKSPACE,
                        requirements=requirements,
                        python_version=">=3.10",
                        venv_path=".venv",
                        index_url=ROCM_TORCH_INDEX_URL,
                    )
                    python_exe = env_state.venv_python
                    print(f"Using Python: {python_exe}")
                except Exception as e:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to setup Python environment: {e}",
                    )

                # Upload wafer-core to remote
                try:
                    wafer_root = _get_wafer_root()
                    wafer_core_path = wafer_root / "packages" / "wafer-core"
                    print(f"Uploading wafer-core from {wafer_core_path}...")

                    wafer_core_remote = f"{REMOTE_WORKSPACE}/wafer-core"
                    await client.exec(f"mkdir -p {wafer_core_remote}")
                    wafer_core_workspace = await client.expand_path(wafer_core_remote)

                    upload_result = await client.upload_files(
                        str(wafer_core_path), wafer_core_workspace, recursive=True
                    )

                    # Wide event logging for upload result
                    upload_event = {
                        "event": "wafer_core_upload",
                        "target": target.name,
                        "target_type": "runpod",
                        "ssh_host": f"{client.user}@{client.host}:{client.port}",
                        "local_path": str(wafer_core_path),
                        "remote_path": wafer_core_workspace,
                        "success": upload_result.success,
                        "files_copied": upload_result.files_copied,
                        "duration_seconds": upload_result.duration_seconds,
                        "error_message": upload_result.error_message,
                    }
                    if upload_result.debug_info:
                        upload_event["debug_info"] = upload_result.debug_info
                    logger.info(json.dumps(upload_event))

                    # Fail fast if upload failed
                    if not upload_result.success:
                        print(f"ERROR: Upload failed: {upload_result.error_message}")
                        if upload_result.debug_info:
                            print(f"Debug info: {json.dumps(upload_result.debug_info, indent=2)}")
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to upload wafer-core: {upload_result.error_message}",
                        )

                    print(f"Uploaded {upload_result.files_copied} files")
                except Exception as e:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to upload wafer-core: {e}",
                    )

                # Select GPU (RunPod pods typically have GPU 0)
                gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]
                print(f"Using GPU {gpu_id}...")

                # Read local files
                impl_code = args.implementation.read_text()
                ref_code = args.reference.read_text()
                test_cases_data = json.loads(args.test_cases.read_text())

                # Create a unique run directory (uuid for concurrent eval isolation)
                import uuid

                unique_id = uuid.uuid4().hex[:8]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_dir = f"wafer_eval_{timestamp}_{unique_id}"
                run_path = f"{REMOTE_WORKSPACE}/{run_dir}"

                print("Uploading evaluation files...")

                # Create run directory
                mkdir_result = await client.exec(f"mkdir -p {run_path}")
                if mkdir_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to create run directory: {mkdir_result.stderr}",
                    )

                # Write implementation
                impl_path = f"{run_path}/implementation.py"
                write_result = await client.exec(
                    f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write implementation: {write_result.stderr}",
                    )

                # Write reference
                ref_path = f"{run_path}/reference.py"
                write_result = await client.exec(
                    f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write reference: {write_result.stderr}",
                    )

                # Also write as reference_kernel.py (evaluate.py imports generate_input from this)
                ref_kernel_path = f"{run_path}/reference_kernel.py"
                write_result = await client.exec(
                    f"cat > '{ref_kernel_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write reference_kernel: {write_result.stderr}",
                    )

                # Write test cases as JSON
                test_cases_path = f"{run_path}/test_cases.json"
                test_cases_json = json.dumps(test_cases_data)
                write_result = await client.exec(
                    f"cat > '{test_cases_path}' << 'TEST_EOF'\n{test_cases_json}\nTEST_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write test cases: {write_result.stderr}",
                    )

                print("Running evaluation...")

                # Build evaluation command
                # RunPod ROCm images use HIP_VISIBLE_DEVICES for AMD GPUs
                # Add venv bin to PATH so ninja (from pip) is found by torch.utils.cpp_extension
                venv_bin = env_state.venv_bin
                env_vars = f"PATH={venv_bin}:$PATH HIP_VISIBLE_DEVICES={gpu_id} ROCM_PATH=/opt/rocm"

                # Run from run_path so reference_kernel.py is importable
                # Use installed wafer-core module
                eval_cmd = (
                    f"cd {run_path} && "
                    f"{env_vars} {python_exe} -m wafer_core.utils.kernel_utils.evaluate "
                    f"--implementation {impl_path} "
                    f"--reference {ref_path} "
                    f"--test-cases {test_cases_path} "
                    f"--run-dir {run_path}"
                )

                if args.benchmark:
                    eval_cmd += " --benchmark"
                if args.defensive:
                    eval_cmd += " --defensive"

                # Run with timeout
                import trio

                with trio.move_on_after(target.eval_timeout) as cancel_scope:
                    result = await client.exec(eval_cmd)

                if cancel_scope.cancelled_caught:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Evaluation timed out after {target.eval_timeout}s",
                    )

                # Parse output
                stdout = result.stdout
                stderr = result.stderr

                if result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Evaluation failed:\nstdout: {stdout}\nstderr: {stderr}",
                    )

                # Find JSON result in output
                result_json = None
                for line in reversed(stdout.strip().split("\n")):
                    if line.startswith("{"):
                        try:
                            result_json = json.loads(line)
                            break
                        except json.JSONDecodeError:
                            continue

                if result_json is None:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"No JSON result in output:\n{stdout}",
                    )

                if "error" in result_json:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=result_json["error"],
                    )

                passed = result_json.get("passed", 0)
                total = result_json.get("total", 0)
                correctness = passed / total if total > 0 else 0.0

                return EvaluateResult(
                    success=True,
                    all_correct=result_json.get("all_correct", False),
                    correctness_score=correctness,
                    geomean_speedup=result_json.get("speedup", 0.0),
                    passed_tests=passed,
                    total_tests=total,
                )

    except RunPodError as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"RunPod error: {e}",
        )


async def run_evaluate_digitalocean(
    args: EvaluateArgs,
    target: DigitalOceanTarget,
) -> EvaluateResult:
    """Run evaluation on DigitalOcean target.

    Provisions a DigitalOcean droplet (or reuses existing), bootstraps Python
    environment with uv, runs evaluation via SSH, then cleans up based on
    keep_alive setting.

    Args:
        args: Evaluate arguments
        target: DigitalOcean target config

    Returns:
        Evaluation result
    """
    from datetime import datetime

    import trio_asyncio
    from wafer_core.async_ssh import AsyncSSHClient
    from wafer_core.remote_env import async_setup_python_env
    from wafer_core.targets.digitalocean import DigitalOceanError, digitalocean_ssh_context

    REMOTE_WORKSPACE = "/tmp/wafer_eval"
    ROCM_TORCH_INDEX_URL = "https://download.pytorch.org/whl/rocm6.2"
    ROCM_TORCH_VERSION_SUFFIX = "+rocm6.2"

    print(f"Provisioning DigitalOcean droplet ({target.size_slug})...")

    try:
        async with digitalocean_ssh_context(target) as ssh_info:
            ssh_target = f"{ssh_info.user}@{ssh_info.host}:{ssh_info.port}"
            print(f"Connected to DigitalOcean: {ssh_target}")

            # Need trio_asyncio for AsyncSSHClient
            async with trio_asyncio.open_loop():
                async with AsyncSSHClient(ssh_target, target.ssh_key) as client:
                    # Ensure rsync and ninja are installed
                    # ninja is needed for torch.utils.cpp_extension (HIP kernel compilation)
                    print("Checking system dependencies...")
                    result = await client.exec("which rsync && which ninja || echo 'MISSING'")
                    if "MISSING" in result.stdout:
                        print("Installing rsync and ninja...")
                        await client.exec("apt-get update && apt-get install -y rsync ninja-build")

                    # Setup Python environment with ROCm torch
                    # Match wafer-core dependencies needed for evaluate.py
                    print("Setting up Python environment with ROCm torch...")
                    requirements = [
                        f"torch==2.5.1{ROCM_TORCH_VERSION_SUFFIX}",
                        "numpy",
                        "ninja",
                        "setuptools",
                        # wafer_core dependencies
                        "trio",
                        "httpx",
                        "pydantic",
                        "anyio",
                        "pyyaml",
                    ]

                    try:
                        env_state = await async_setup_python_env(
                            client=client,
                            workspace=REMOTE_WORKSPACE,
                            requirements=requirements,
                            python_version="3.10",
                            venv_path=".venv",
                            index_url=ROCM_TORCH_INDEX_URL,
                        )
                        python_exe = env_state.venv_python
                        print(f"Using Python: {python_exe}")
                    except Exception as e:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to setup Python environment: {e}",
                        )

                    # Upload wafer-core to remote
                    try:
                        wafer_root = _get_wafer_root()
                        wafer_core_path = wafer_root / "packages" / "wafer-core"
                        print(f"Uploading wafer-core from {wafer_core_path}...")

                        wafer_core_remote = f"{REMOTE_WORKSPACE}/wafer-core"
                        await client.exec(f"mkdir -p {wafer_core_remote}")
                        wafer_core_workspace = await client.expand_path(wafer_core_remote)

                        # Use SFTP instead of rsync to avoid SSH subprocess timeout issues
                        # (DigitalOcean may rate-limit new SSH connections)
                        upload_result = await client.upload_files(
                            str(wafer_core_path),
                            wafer_core_workspace,
                            recursive=True,
                            use_sftp=True,
                        )

                        # Wide event logging for upload result
                        upload_event = {
                            "event": "wafer_core_upload",
                            "target": target.name,
                            "target_type": "digitalocean",
                            "ssh_host": f"{client.user}@{client.host}:{client.port}",
                            "local_path": str(wafer_core_path),
                            "remote_path": wafer_core_workspace,
                            "success": upload_result.success,
                            "files_copied": upload_result.files_copied,
                            "duration_seconds": upload_result.duration_seconds,
                            "error_message": upload_result.error_message,
                        }
                        if upload_result.debug_info:
                            upload_event["debug_info"] = upload_result.debug_info
                        logger.info(json.dumps(upload_event))

                        # Fail fast if upload failed
                        if not upload_result.success:
                            print(f"ERROR: Upload failed: {upload_result.error_message}")
                            if upload_result.debug_info:
                                print(
                                    f"Debug info: {json.dumps(upload_result.debug_info, indent=2)}"
                                )
                            return EvaluateResult(
                                success=False,
                                all_correct=False,
                                correctness_score=0.0,
                                geomean_speedup=0.0,
                                passed_tests=0,
                                total_tests=0,
                                error_message=f"Failed to upload wafer-core: {upload_result.error_message}",
                            )

                        print(f"Uploaded {upload_result.files_copied} files")
                    except Exception as e:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to upload wafer-core: {e}",
                        )

                    # Select GPU (DigitalOcean droplets typically have GPU 0)
                    gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]
                    print(f"Using GPU {gpu_id}...")

                    # Read local files
                    impl_code = args.implementation.read_text()
                    ref_code = args.reference.read_text()
                    test_cases_data = json.loads(args.test_cases.read_text())

                    # Create a unique run directory (uuid for concurrent eval isolation)
                    import uuid

                    unique_id = uuid.uuid4().hex[:8]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_dir = f"wafer_eval_{timestamp}_{unique_id}"
                    run_path = f"{REMOTE_WORKSPACE}/{run_dir}"

                    print("Uploading evaluation files...")

                    # Create run directory
                    mkdir_result = await client.exec(f"mkdir -p {run_path}")
                    if mkdir_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to create run directory: {mkdir_result.stderr}",
                        )

                    # Write implementation
                    impl_path = f"{run_path}/implementation.py"
                    write_result = await client.exec(
                        f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write implementation: {write_result.stderr}",
                        )

                    # Write reference
                    ref_path = f"{run_path}/reference.py"
                    write_result = await client.exec(
                        f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write reference: {write_result.stderr}",
                        )

                    # Also write as reference_kernel.py (evaluate.py imports generate_input from this)
                    ref_kernel_path = f"{run_path}/reference_kernel.py"
                    write_result = await client.exec(
                        f"cat > '{ref_kernel_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write reference_kernel: {write_result.stderr}",
                        )

                    # Write test cases as JSON
                    test_cases_path = f"{run_path}/test_cases.json"
                    test_cases_json = json.dumps(test_cases_data)
                    write_result = await client.exec(
                        f"cat > '{test_cases_path}' << 'TEST_EOF'\n{test_cases_json}\nTEST_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write test cases: {write_result.stderr}",
                        )

                    print("Running evaluation...")

                    # Build evaluation command
                    # DigitalOcean AMD uses HIP_VISIBLE_DEVICES for AMD GPUs
                    # Add venv bin to PATH so ninja (from pip) is found by torch.utils.cpp_extension
                    venv_bin = env_state.venv_bin
                    env_vars = (
                        f"PATH={venv_bin}:$PATH HIP_VISIBLE_DEVICES={gpu_id} ROCM_PATH=/opt/rocm"
                    )

                    # Run from run_path so reference_kernel.py is importable
                    # Use installed wafer-core module
                    eval_cmd = (
                        f"cd {run_path} && "
                        f"{env_vars} {python_exe} -m wafer_core.utils.kernel_utils.evaluate "
                        f"--implementation {impl_path} "
                        f"--reference {ref_path} "
                        f"--test-cases {test_cases_path} "
                        f"--run-dir {run_path}"
                    )

                    if args.benchmark:
                        eval_cmd += " --benchmark"
                    if args.defensive:
                        eval_cmd += " --defensive"

                    # Run with timeout
                    import trio

                    with trio.move_on_after(target.eval_timeout) as cancel_scope:
                        result = await client.exec(eval_cmd)

                    if cancel_scope.cancelled_caught:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Evaluation timed out after {target.eval_timeout}s",
                        )

                    # Show output to user
                    stdout = result.stdout
                    stderr = result.stderr
                    if stdout:
                        print(stdout)

                    if result.exit_code != 0:
                        # Include both stdout and stderr for debugging
                        error_parts = [f"Evaluation failed (exit code {result.exit_code}):"]
                        if stdout:
                            error_parts.append(f"stdout: {stdout}")
                        if stderr:
                            error_parts.append(f"stderr: {stderr}")
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message="\n".join(error_parts),
                        )

                    # Read results from results.json (like SSH path)
                    results_path = f"{run_path}/results.json"
                    cat_result = await client.exec(f"cat {results_path}")

                    if cat_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to read results: {cat_result.stderr}",
                        )

                    try:
                        results_data = json.loads(cat_result.stdout)
                    except json.JSONDecodeError as e:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Invalid JSON in results: {e}",
                        )

                    # Extract backend results (same format as SSH path)
                    backends = results_data.get("backends", [])
                    if not backends:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message="No backend results found",
                        )

                    backend = backends[0]
                    correctness_tests = backend.get("correctness_tests", [])
                    passed = sum(1 for t in correctness_tests if t.get("is_correct", False))
                    total = len(correctness_tests)

                    return EvaluateResult(
                        success=True,
                        all_correct=backend.get("all_correct", False),
                        correctness_score=backend.get("correctness_score", 0.0),
                        geomean_speedup=backend.get("geomean_speedup", 0.0),
                        passed_tests=passed,
                        total_tests=total,
                    )

    except DigitalOceanError as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"DigitalOcean error: {e}",
        )


async def run_evaluate(args: EvaluateArgs) -> EvaluateResult:
    """Run evaluation on configured target.

    Args:
        args: Evaluate arguments

    Returns:
        Evaluation result
    """
    from .targets import get_default_target, load_target

    # Validate input files
    err = _validate_files(args)
    if err:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=err,
        )

    # Load target
    target_name = args.target_name
    if not target_name:
        target_name = get_default_target()
        if not target_name:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=(
                    "No target specified and no default set.\n"
                    "Set up a target first:\n"
                    "  wafer config targets init ssh --name my-gpu --host user@host:22\n"
                    "  wafer config targets init runpod --gpu MI300X\n"
                    "Then use: --target my-gpu (or set default: wafer config targets default my-gpu)"
                ),
            )

    try:
        target = load_target(target_name)
    except FileNotFoundError:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Target not found: {target_name}. Run: wafer config targets list",
        )

    print(f"Using target: {target_name}")

    # Dispatch to appropriate executor
    if isinstance(target, LocalTarget):
        return await run_evaluate_local(args, target)
    elif isinstance(target, BaremetalTarget | VMTarget):
        return await run_evaluate_ssh(args, target)
    elif isinstance(target, ModalTarget):
        return await run_evaluate_modal(args, target)
    elif isinstance(target, WorkspaceTarget):
        return await run_evaluate_workspace(args, target)
    elif isinstance(target, RunPodTarget):
        return await run_evaluate_runpod(args, target)
    elif isinstance(target, DigitalOceanTarget):
        return await run_evaluate_digitalocean(args, target)
    else:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Unknown target type: {type(target)}",
        )


# =============================================================================
# KernelBench Format Evaluation
# =============================================================================

# Inline evaluation script for KernelBench format
# This runs inside the Docker container on the remote GPU
KERNELBENCH_EVAL_SCRIPT = """
import gc
import json
import os
import sys
import time
import torch
import torch.nn as nn
from pathlib import Path

# Use a unique per-run PyTorch extension cache directory to ensure fresh compilation.
# This prevents stale cached extensions from being loaded when the pod is reused.
# Without this, if a kernel is modified but uses the same extension name,
# PyTorch would load the old cached .so instead of recompiling.
# We use a UUID-based directory instead of clearing the cache to avoid race conditions
# with other processes that might be using the cache.
import uuid
unique_cache_dir = f"/tmp/torch_extensions_{uuid.uuid4().hex[:8]}"
os.environ["TORCH_EXTENSIONS_DIR"] = unique_cache_dir
print(f"[KernelBench] Using unique extension cache: {unique_cache_dir}")

# Clear any stale GPU memory from previous runs at startup
# NOTE: empty_cache only frees memory from THIS process's PyTorch allocator.
# It won't free memory from dead/zombie processes - rocm-smi --showpids can show
# PIDs that no longer exist but still hold GPU memory. Those require a GPU reset
# (rocm-smi --gpureset) to fully clear. TODO: detect and warn about orphaned memory.
if torch.cuda.is_available():
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()


def _calculate_timing_stats(times: list[float]) -> dict:
    '''Calculate median and IQR from timing samples.

    Returns dict with median, iqr_low (25th percentile), iqr_high (75th percentile),
    mean, min, max, and std.
    '''
    import statistics

    if not times:
        return {"median": 0, "iqr_low": 0, "iqr_high": 0, "mean": 0, "min": 0, "max": 0, "std": 0}

    sorted_times = sorted(times)
    n = len(sorted_times)

    # Median
    median = statistics.median(sorted_times)

    # Quartiles (25th and 75th percentile)
    # For small samples, use simple interpolation
    q1_idx = (n - 1) * 0.25
    q3_idx = (n - 1) * 0.75

    q1_low = int(q1_idx)
    q1_frac = q1_idx - q1_low
    iqr_low = sorted_times[q1_low] * (1 - q1_frac) + sorted_times[min(q1_low + 1, n - 1)] * q1_frac

    q3_low = int(q3_idx)
    q3_frac = q3_idx - q3_low
    iqr_high = sorted_times[q3_low] * (1 - q3_frac) + sorted_times[min(q3_low + 1, n - 1)] * q3_frac

    return {
        "median": median,
        "iqr_low": iqr_low,
        "iqr_high": iqr_high,
        "mean": statistics.mean(sorted_times),
        "min": min(sorted_times),
        "max": max(sorted_times),
        "std": statistics.stdev(sorted_times) if n > 1 else 0,
    }


def run_profiling(model, inputs, name, output_dir):
    '''Run torch.profiler and return summary stats.'''
    from torch.profiler import profile, ProfilerActivity

    # Determine activities based on backend
    activities = [ProfilerActivity.CPU]
    if torch.cuda.is_available():
        activities.append(ProfilerActivity.CUDA)

    # Warmup
    for _ in range(3):
        with torch.no_grad():
            _ = model(*inputs)
    torch.cuda.synchronize()

    # Profile
    with profile(
        activities=activities,
        record_shapes=True,
        with_stack=False,
        profile_memory=True,
    ) as prof:
        with torch.no_grad():
            _ = model(*inputs)
        torch.cuda.synchronize()

    # Get key averages
    key_averages = prof.key_averages()

    # Find the main kernel (longest GPU time)
    # Use cuda_time_total for compatibility with both CUDA and ROCm
    def get_gpu_time(e):
        # Try different attributes for GPU time
        if hasattr(e, 'cuda_time_total'):
            return e.cuda_time_total
        if hasattr(e, 'device_time_total'):
            return e.device_time_total
        if hasattr(e, 'self_cuda_time_total'):
            return e.self_cuda_time_total
        return 0

    gpu_events = [e for e in key_averages if get_gpu_time(e) > 0]
    gpu_events.sort(key=lambda e: get_gpu_time(e), reverse=True)

    stats = {
        "name": name,
        "total_gpu_time_ms": sum(get_gpu_time(e) for e in gpu_events) / 1000,
        "total_cpu_time_ms": sum(e.cpu_time_total for e in key_averages) / 1000,
        "num_gpu_kernels": len(gpu_events),
        "top_kernels": [],
    }

    # Top 5 kernels by GPU time
    for e in gpu_events[:5]:
        stats["top_kernels"].append({
            "name": e.key,
            "gpu_time_ms": get_gpu_time(e) / 1000,
            "cpu_time_ms": e.cpu_time_total / 1000,
            "calls": e.count,
        })

    # Save trace for visualization
    trace_path = Path(output_dir) / f"{name}_trace.json"
    prof.export_chrome_trace(str(trace_path))
    stats["trace_file"] = str(trace_path)

    return stats


def validate_custom_inputs(original_inputs, custom_inputs):
    '''Validate that custom inputs match the expected signature.

    Returns (is_valid, error_message).
    '''
    if len(original_inputs) != len(custom_inputs):
        return False, f"get_inputs() must return {len(original_inputs)} tensors, got {len(custom_inputs)}"

    for i, (orig, cust) in enumerate(zip(original_inputs, custom_inputs)):
        if not isinstance(cust, torch.Tensor):
            if not isinstance(orig, torch.Tensor):
                continue  # Both non-tensor, ok
            return False, f"Input {i}: expected Tensor, got {type(cust).__name__}"

        if not isinstance(orig, torch.Tensor):
            return False, f"Input {i}: expected {type(orig).__name__}, got Tensor"

        if orig.dtype != cust.dtype:
            return False, f"Input {i}: dtype mismatch - expected {orig.dtype}, got {cust.dtype}"

        if orig.dim() != cust.dim():
            return False, f"Input {i}: dimension mismatch - expected {orig.dim()}D, got {cust.dim()}D"

    return True, None


def analyze_diff(ref_output, new_output, rtol=1e-3, atol=1e-3, max_samples=5):
    '''Analyze differences between reference and implementation outputs.

    Returns a dict with detailed diff information.
    '''
    diff = (ref_output - new_output).abs()
    threshold = atol + rtol * ref_output.abs()
    wrong_mask = diff > threshold

    total_elements = ref_output.numel()
    wrong_count = wrong_mask.sum().item()

    # Basic stats
    max_diff = diff.max().item()
    max_diff_idx = tuple(torch.unravel_index(diff.argmax(), diff.shape))
    max_diff_idx = tuple(int(i) for i in max_diff_idx)  # Convert to Python ints

    # Relative error (avoid div by zero)
    ref_abs = ref_output.abs()
    nonzero_mask = ref_abs > 1e-8
    if nonzero_mask.any():
        rel_error = diff[nonzero_mask] / ref_abs[nonzero_mask]
        max_rel_error = rel_error.max().item()
        mean_rel_error = rel_error.mean().item()
    else:
        max_rel_error = float('inf') if max_diff > 0 else 0.0
        mean_rel_error = max_rel_error

    # Error histogram (buckets: <1e-6, 1e-6 to 1e-4, 1e-4 to 1e-2, 1e-2 to 1, >1)
    histogram = {
        '<1e-6': int((diff < 1e-6).sum().item()),
        '1e-6 to 1e-4': int(((diff >= 1e-6) & (diff < 1e-4)).sum().item()),
        '1e-4 to 1e-2': int(((diff >= 1e-4) & (diff < 1e-2)).sum().item()),
        '1e-2 to 1': int(((diff >= 1e-2) & (diff < 1)).sum().item()),
        '>1': int((diff >= 1).sum().item()),
    }

    result = {
        'max_diff': max_diff,
        'max_diff_idx': max_diff_idx,
        'mean_diff': diff.mean().item(),
        'max_rel_error': max_rel_error,
        'mean_rel_error': mean_rel_error,
        'total_elements': total_elements,
        'wrong_count': int(wrong_count),
        'wrong_pct': 100.0 * wrong_count / total_elements,
        'histogram': histogram,
        'samples': [],
    }

    # Get indices of wrong elements
    if wrong_count > 0:
        wrong_indices = torch.nonzero(wrong_mask, as_tuple=False)

        # Take first N samples
        num_samples = min(max_samples, len(wrong_indices))
        for i in range(num_samples):
            idx = tuple(wrong_indices[i].tolist())
            ref_val = ref_output[idx].item()
            new_val = new_output[idx].item()
            diff_val = diff[idx].item()
            result['samples'].append({
                'index': idx,
                'ref': ref_val,
                'impl': new_val,
                'diff': diff_val,
            })

        # Try to detect pattern
        if wrong_count >= total_elements * 0.99:
            result['pattern'] = 'all_wrong'
        elif wrong_count < total_elements * 0.01:
            # Check if failures are at boundaries
            shape = ref_output.shape
            boundary_count = 0
            for idx in wrong_indices[:min(100, len(wrong_indices))]:
                idx_list = idx.tolist()
                is_boundary = any(i == 0 or i == s - 1 for i, s in zip(idx_list, shape))
                if is_boundary:
                    boundary_count += 1
            if boundary_count > len(wrong_indices[:100]) * 0.8:
                result['pattern'] = 'boundary_issue'
            else:
                result['pattern'] = 'scattered'
        else:
            result['pattern'] = 'partial'

    return result


def print_diff_analysis(analysis):
    '''Print a human-readable diff analysis.'''
    print(f"[KernelBench] Diff analysis:")

    # Max diff with location
    idx_str = ','.join(str(i) for i in analysis['max_diff_idx'])
    print(f"   Max diff: {analysis['max_diff']:.6f} at index [{idx_str}]")
    print(f"   Mean diff: {analysis['mean_diff']:.6f}")

    # Relative errors
    print(f"   Max relative error: {analysis['max_rel_error']:.2%}, Mean: {analysis['mean_rel_error']:.2%}")

    # Wrong count
    print(f"   Wrong elements: {analysis['wrong_count']:,} / {analysis['total_elements']:,} ({analysis['wrong_pct']:.2f}%)")

    # Histogram
    hist = analysis['histogram']
    print(f"   Error distribution: <1e-6: {hist['<1e-6']:,} | 1e-6~1e-4: {hist['1e-6 to 1e-4']:,} | 1e-4~1e-2: {hist['1e-4 to 1e-2']:,} | 1e-2~1: {hist['1e-2 to 1']:,} | >1: {hist['>1']:,}")

    if 'pattern' in analysis:
        pattern_desc = {
            'all_wrong': 'ALL elements wrong - likely algorithmic error or wrong weights',
            'boundary_issue': 'Mostly BOUNDARY elements wrong - check edge handling',
            'scattered': 'SCATTERED failures - numerical precision issue?',
            'partial': 'PARTIAL failures - check specific conditions',
        }
        print(f"   Pattern: {pattern_desc.get(analysis['pattern'], analysis['pattern'])}")

    if analysis['samples']:
        print(f"   Sample failures:")
        for s in analysis['samples']:
            idx_str = ','.join(str(i) for i in s['index'])
            print(f"      [{idx_str}]: ref={s['ref']:.6f} impl={s['impl']:.6f} (diff={s['diff']:.6f})")


def main():
    # Parse args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--impl", required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--inputs", help="Custom inputs file to override get_inputs()/get_init_inputs()")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--profile", action="store_true")
    parser.add_argument("--defensive", action="store_true", help="Run full defense checks against reward hacking")
    parser.add_argument("--defense-module", help="Path to defense.py module")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--num-correct-trials", type=int, default=3)
    parser.add_argument("--num-perf-trials", type=int, default=10)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stages", default="compile,correctness",
                        help="Comma-separated stages: compile, correctness, benchmark, defense")
    args = parser.parse_args()

    # Parse stages
    stages = set(args.stages.split(","))
    run_compile = "compile" in stages
    run_correctness = "correctness" in stages
    run_benchmark = "benchmark" in stages or args.benchmark
    run_defense = "defense" in stages or args.defensive
    print(f"[KernelBench] Stages: {args.stages}")

    # Load defense module if defensive mode is enabled
    defense_module = None
    if args.defensive and args.defense_module:
        try:
            import importlib.util
            defense_spec = importlib.util.spec_from_file_location("defense", args.defense_module)
            defense_module = importlib.util.module_from_spec(defense_spec)
            defense_spec.loader.exec_module(defense_module)
            print("[KernelBench] Defense module loaded")
        except Exception as e:
            print(f"[KernelBench] Warning: Could not load defense module: {e}")

    # Create output directory for profiles
    output_dir = Path(args.output).parent
    profile_dir = output_dir / "profiles"
    if args.profile:
        profile_dir.mkdir(exist_ok=True)

    results = {
        "compiled": False,
        "correct": False,
        "speedup": None,
        "runtime_ms": None,
        "reference_runtime_ms": None,
        "error": None,
    }

    try:
        # Load reference module
        import importlib.util
        ref_spec = importlib.util.spec_from_file_location("reference", args.reference)
        ref_module = importlib.util.module_from_spec(ref_spec)
        ref_spec.loader.exec_module(ref_module)

        Model = ref_module.Model
        get_inputs = ref_module.get_inputs
        get_init_inputs = ref_module.get_init_inputs

        # Load custom inputs if provided
        if args.inputs:
            inputs_spec = importlib.util.spec_from_file_location("custom_inputs", args.inputs)
            inputs_module = importlib.util.module_from_spec(inputs_spec)
            inputs_spec.loader.exec_module(inputs_module)

            # Validate custom inputs match expected signature
            original_inputs = get_inputs()
            custom_get_inputs = inputs_module.get_inputs
            custom_inputs = custom_get_inputs()

            is_valid, error_msg = validate_custom_inputs(original_inputs, custom_inputs)
            if not is_valid:
                print(f"[KernelBench] Custom inputs validation failed: {error_msg}")
                results["error"] = f"Custom inputs validation failed: {error_msg}"
                raise ValueError(error_msg)

            # Override get_inputs (and optionally get_init_inputs)
            get_inputs = custom_get_inputs
            if hasattr(inputs_module, 'get_init_inputs'):
                get_init_inputs = inputs_module.get_init_inputs

            # Show what changed
            orig_shapes = [tuple(t.shape) if hasattr(t, 'shape') else type(t).__name__ for t in original_inputs]
            cust_shapes = [tuple(t.shape) if hasattr(t, 'shape') else type(t).__name__ for t in custom_inputs]
            print(f"[KernelBench] Using custom inputs: {orig_shapes} -> {cust_shapes}")

        # Load implementation module
        impl_spec = importlib.util.spec_from_file_location("implementation", args.impl)
        impl_module = importlib.util.module_from_spec(impl_spec)
        impl_spec.loader.exec_module(impl_module)

        ModelNew = impl_module.ModelNew
        results["compiled"] = True
        print("[KernelBench] Modules loaded successfully")

        # Instantiate models with synchronized seeds for reproducible weights
        # (matches upstream KernelBench behavior in src/eval.py)
        seed = args.seed
        init_inputs = get_init_inputs()
        with torch.no_grad():
            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
            ref_model = Model(*init_inputs).cuda().eval()

            torch.manual_seed(seed)
            torch.cuda.manual_seed(seed)
            new_model = ModelNew(*init_inputs).cuda().eval()
        print(f"[KernelBench] Models instantiated (seed={seed})")

        # Run correctness trials (if stage enabled)
        all_correct = True
        if not run_correctness:
            print("[KernelBench] Skipping correctness (not in stages)")
            results["correct"] = None  # Unknown - not checked
        else:
            for trial in range(args.num_correct_trials):
                inputs = get_inputs()
                inputs = [x.cuda() if isinstance(x, torch.Tensor) else x for x in inputs]

                with torch.no_grad():
                    ref_output = ref_model(*inputs)
                    new_output = new_model(*inputs)

                # Compare outputs
                if isinstance(ref_output, torch.Tensor):
                    if not torch.allclose(ref_output, new_output, rtol=1e-3, atol=1e-3):
                        all_correct = False
                        analysis = analyze_diff(ref_output, new_output)
                        results["error"] = f"Correctness failed on trial {trial+1}: max diff = {analysis['max_diff']}"
                        results["diff_analysis"] = analysis
                        print_diff_analysis(analysis)

                        # Save tensors for debugging
                        debug_dir = output_dir / "debug"
                        debug_dir.mkdir(exist_ok=True)
                        torch.save(ref_output.cpu(), debug_dir / "ref_output.pt")
                        torch.save(new_output.cpu(), debug_dir / "impl_output.pt")
                        torch.save(inputs[0].cpu() if inputs else None, debug_dir / "input.pt")
                        print(f"[KernelBench] Debug tensors saved to: {debug_dir}/")
                        break
                else:
                    # Handle tuple/list outputs
                    for i, (r, n) in enumerate(zip(ref_output, new_output)):
                        if isinstance(r, torch.Tensor):
                            if not torch.allclose(r, n, rtol=1e-3, atol=1e-3):
                                all_correct = False
                                analysis = analyze_diff(r, n)
                                results["error"] = f"Correctness failed on trial {trial+1}, output {i}: max diff = {analysis['max_diff']}"
                                results["diff_analysis"] = analysis
                                print_diff_analysis(analysis)

                                # Save tensors for debugging
                                debug_dir = output_dir / "debug"
                                debug_dir.mkdir(exist_ok=True)
                                torch.save(r.cpu(), debug_dir / f"ref_output_{i}.pt")
                                torch.save(n.cpu(), debug_dir / f"impl_output_{i}.pt")
                                print(f"[KernelBench] Debug tensors saved to: {debug_dir}/")
                                break
                    if not all_correct:
                        break

            results["correct"] = all_correct
            print(f"[KernelBench] Correctness: {all_correct}")

        # Run benchmark if stage enabled (and correctness passed or skipped)
        should_benchmark = run_benchmark and (all_correct or not run_correctness)
        if should_benchmark:
            print("[KernelBench] Running benchmarks...")
            inputs = get_inputs()
            inputs = [x.cuda() if isinstance(x, torch.Tensor) else x for x in inputs]

            if run_defense and defense_module is not None:
                # Use full defense suite
                print("[KernelBench] Running defense checks on implementation...")
                run_all_defenses = defense_module.run_all_defenses
                time_with_defenses = defense_module.time_execution_with_defenses

                # Run defense checks on implementation
                all_passed, defense_results, _ = run_all_defenses(
                    lambda *x: new_model(*x),
                    *inputs,
                )
                results["defense_results"] = {
                    name: {"passed": passed, "message": msg}
                    for name, passed, msg in defense_results
                }
                if not all_passed:
                    failed = [name for name, passed, _ in defense_results if not passed]
                    results["error"] = f"Defense checks failed: {failed}"
                    print(f"[KernelBench] Defense checks FAILED: {failed}")
                    for name, passed, msg in defense_results:
                        status = "PASS" if passed else "FAIL"
                        print(f"   [{status}] {name}: {msg}")
                else:
                    print("[KernelBench] All defense checks passed")

                    # Time with defensive timing
                    impl_times, _ = time_with_defenses(
                        lambda: new_model(*inputs),
                        [],
                        num_warmup=5,
                        num_trials=args.num_perf_trials,
                        verbose=False,
                        run_defenses=False,  # Already ran above
                    )
                    # Calculate stats for new model
                    new_stats = _calculate_timing_stats(impl_times)
                    results["runtime_ms"] = new_stats["median"]
                    results["runtime_stats"] = new_stats

                    # Reference timing
                    ref_times, _ = time_with_defenses(
                        lambda: ref_model(*inputs),
                        [],
                        num_warmup=5,
                        num_trials=args.num_perf_trials,
                        verbose=False,
                        run_defenses=False,
                    )
                    ref_stats = _calculate_timing_stats(ref_times)
                    results["reference_runtime_ms"] = ref_stats["median"]
                    results["reference_runtime_stats"] = ref_stats
                    results["speedup"] = ref_stats["median"] / new_stats["median"] if new_stats["median"] > 0 else 0
                    print(f"[KernelBench] New: {new_stats['median']:.3f}ms (IQR: {new_stats['iqr_low']:.3f}-{new_stats['iqr_high']:.3f}), Ref: {ref_stats['median']:.3f}ms (IQR: {ref_stats['iqr_low']:.3f}-{ref_stats['iqr_high']:.3f}), Speedup: {results['speedup']:.2f}x")
            else:
                # Standard timing without full defenses
                # Warmup BOTH models before benchmarking either
                # This ensures consistent GPU state and avoids MIOpen cache effects
                # that cause variance when warming up models sequentially
                for _ in range(5):
                    with torch.no_grad():
                        _ = new_model(*inputs)
                        _ = ref_model(*inputs)
                torch.cuda.synchronize()

                # Benchmark new model
                start = torch.cuda.Event(enable_timing=True)
                end = torch.cuda.Event(enable_timing=True)

                new_times = []
                for _ in range(args.num_perf_trials):
                    start.record()
                    with torch.no_grad():
                        _ = new_model(*inputs)
                    end.record()
                    torch.cuda.synchronize()
                    new_times.append(start.elapsed_time(end))

                new_stats = _calculate_timing_stats(new_times)
                results["runtime_ms"] = new_stats["median"]
                results["runtime_stats"] = new_stats

                # Benchmark reference model
                ref_times = []
                for _ in range(args.num_perf_trials):
                    start.record()
                    with torch.no_grad():
                        _ = ref_model(*inputs)
                    end.record()
                    torch.cuda.synchronize()
                    ref_times.append(start.elapsed_time(end))

                ref_stats = _calculate_timing_stats(ref_times)
                results["reference_runtime_ms"] = ref_stats["median"]
                results["reference_runtime_stats"] = ref_stats
                results["speedup"] = ref_stats["median"] / new_stats["median"] if new_stats["median"] > 0 else 0
                print(f"[KernelBench] New: {new_stats['median']:.3f}ms (IQR: {new_stats['iqr_low']:.3f}-{new_stats['iqr_high']:.3f}), Ref: {ref_stats['median']:.3f}ms (IQR: {ref_stats['iqr_low']:.3f}-{ref_stats['iqr_high']:.3f}), Speedup: {results['speedup']:.2f}x")

        # Run profiling if requested and correctness passed
        if args.profile and all_correct:
            print("[KernelBench] Running profiler...")
            inputs = get_inputs()
            inputs = [x.cuda() if isinstance(x, torch.Tensor) else x for x in inputs]

            try:
                # Profile implementation
                impl_stats = run_profiling(new_model, inputs, "implementation", str(profile_dir))
                results["profile_impl"] = impl_stats
                print(f"[KernelBench] Implementation profile:")
                print(f"   Total GPU time: {impl_stats['total_gpu_time_ms']:.3f}ms")
                print(f"   Kernels launched: {impl_stats['num_gpu_kernels']}")
                if impl_stats['top_kernels']:
                    print(f"   Top kernel: {impl_stats['top_kernels'][0]['name'][:60]}...")
                    print(f"              {impl_stats['top_kernels'][0]['gpu_time_ms']:.3f}ms")

                # Profile reference
                ref_stats = run_profiling(ref_model, inputs, "reference", str(profile_dir))
                results["profile_ref"] = ref_stats
                print(f"[KernelBench] Reference profile:")
                print(f"   Total GPU time: {ref_stats['total_gpu_time_ms']:.3f}ms")
                print(f"   Kernels launched: {ref_stats['num_gpu_kernels']}")
                if ref_stats['top_kernels']:
                    print(f"   Top kernel: {ref_stats['top_kernels'][0]['name'][:60]}...")
                    print(f"              {ref_stats['top_kernels'][0]['gpu_time_ms']:.3f}ms")

                print(f"[KernelBench] Profile traces saved to: {profile_dir}/")

            except Exception as prof_err:
                print(f"[KernelBench] Profiling failed: {prof_err}")
                results["profile_error"] = str(prof_err)

    except Exception as e:
        import traceback
        results["error"] = f"{type(e).__name__}: {e}\\n{traceback.format_exc()}"
        print(f"[KernelBench] Error: {results['error']}")

    # Write results
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[KernelBench] Results written to {args.output}")

    # Cleanup GPU memory
    try:
        del ref_model, new_model
    except NameError:
        pass
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

if __name__ == "__main__":
    main()
"""


def _validate_kernelbench_files(args: KernelBenchEvaluateArgs) -> str | None:
    """Validate that KernelBench input files exist and have expected signatures.

    Returns:
        Error message if validation fails, None if all valid
    """
    if not args.implementation.exists():
        return f"Implementation file not found: {args.implementation}"
    if not args.reference.exists():
        return f"Reference file not found: {args.reference}"

    # Validate implementation has ModelNew class
    impl_missing = _check_python_file_has(args.implementation, "ModelNew")
    if impl_missing:
        # Check if it looks like functional format (has custom_kernel)
        has_custom_kernel = not _check_python_file_has(args.implementation, "custom_kernel")
        if has_custom_kernel:
            return (
                f"Implementation file missing 'ModelNew' class: {args.implementation}\n"
                "Hint: This looks like functional format. Use 'wafer evaluate' instead:\n"
                f"  wafer evaluate --impl {args.implementation} --reference <ref.py> --test-cases <tests.json>"
            )
        return (
            f"Implementation file missing 'ModelNew' class: {args.implementation}\n"
            "  KernelBench format requires a 'class ModelNew(nn.Module)' definition"
        )

    # Validate reference has Model, get_inputs, get_init_inputs
    ref_missing = _check_python_file_has(args.reference, "Model", "get_inputs", "get_init_inputs")
    if ref_missing:
        # Check if it looks like functional format (has ref_kernel and generate_input)
        has_functional = not _check_python_file_has(args.reference, "ref_kernel", "generate_input")
        if has_functional:
            return (
                f"Reference file missing required definitions: {', '.join(ref_missing)}\n"
                "Hint: This looks like functional format. Use 'wafer evaluate' instead:\n"
                f"  wafer evaluate --impl <impl.py> --reference {args.reference} --test-cases <tests.json>"
            )
        return (
            f"Reference file missing required definitions: {', '.join(ref_missing)}\n"
            f"  File: {args.reference}\n"
            "  KernelBench format requires: 'class Model', 'get_inputs()', 'get_init_inputs()'"
        )

    # Static kernel validation if backend specified
    if args.backend:
        from wafer_core.utils.kernel_utils.static_checker import validate_kernel_static

        code = args.implementation.read_text()
        valid, errors, warnings = validate_kernel_static(code, backend=args.backend)

        # Print warnings (don't fail)
        for warning in warnings:
            logger.warning(f"Static check warning: {warning}")

        # Fail on errors
        if not valid:
            error_list = "\n  - ".join(errors)
            return (
                f"Static kernel validation failed for backend '{args.backend}':\n"
                f"  - {error_list}\n\n"
                f"The implementation must use {args.backend.upper()} kernel primitives.\n"
                "See KernelBench documentation for valid kernel patterns."
            )

    return None


def _build_modal_kernelbench_script(
    target: ModalTarget,
    impl_code_b64: str,
    ref_code_b64: str,
    eval_script_b64: str,
    run_benchmarks: bool,
    run_defensive: bool,
    defense_code_b64: str | None,
    seed: int,
    inputs_code_b64: str | None = None,
) -> str:
    """Build Python script to create Modal sandbox and run KernelBench evaluation.

    This runs in a subprocess to isolate Modal's asyncio from trio.
    """
    gpu_type = target.gpu_type

    # Determine PyTorch index and CUDA arch based on GPU type
    if gpu_type in ("B200", "GB200"):
        torch_index = "https://download.pytorch.org/whl/cu130"
        cuda_arch_list = "10.0"  # Blackwell (sm_100)
    elif gpu_type == "H100":
        # H100 uses CUDA 13.0 (matches modal_app.py)
        torch_index = "https://download.pytorch.org/whl/cu130"
        cuda_arch_list = "9.0"  # Hopper (sm_90)
    else:
        torch_index = "https://download.pytorch.org/whl/cu124"
        cuda_arch_list = "8.0"  # Default to Ampere (sm_80)

    # Install CUTLASS headers (for cute/tensor.hpp and cutlass/util/*.h) from GitHub
    # The nvidia-cutlass-dsl pip package doesn't include the C++ headers needed for nvcc
    # IMPORTANT: symlink to /usr/local/cuda/include because nvcc searches there by default
    cutlass_install = """
        .run_commands([
            # Clone CUTLASS headers from GitHub (shallow clone, full include tree)
            # Use simple shallow clone - sparse-checkout can be buggy in some environments
            "git clone --depth 1 https://github.com/NVIDIA/cutlass.git /opt/cutlass",
            # Verify the util headers exist (for debugging)
            "ls -la /opt/cutlass/include/cutlass/util/ | head -5",
            # Symlink headers to CUDA include path (nvcc searches here by default)
            "ln -sf /opt/cutlass/include/cute /usr/local/cuda/include/cute",
            "ln -sf /opt/cutlass/include/cutlass /usr/local/cuda/include/cutlass",
        ])
        .pip_install(
            "nvidia-cutlass-dsl",
            index_url="https://pypi.nvidia.com",
            extra_index_url="https://pypi.org/simple",
        )
    """

    inputs_write = ""
    if inputs_code_b64:
        inputs_write = f'''
        # Write custom inputs
        proc = sandbox.exec("python", "-c", f"""
import base64
with open('/workspace/custom_inputs.py', 'w') as f:
    f.write(base64.b64decode('{inputs_code_b64}').decode())
print('Custom inputs written')
""")
        proc.wait()
'''

    defense_write = ""
    if run_defensive and defense_code_b64:
        defense_write = f'''
        # Write defense module
        proc = sandbox.exec("python", "-c", f"""
import base64
with open('/workspace/defense.py', 'w') as f:
    f.write(base64.b64decode('{defense_code_b64}').decode())
print('Defense module written')
""")
        proc.wait()
'''

    # Build eval command
    eval_cmd_parts = [
        "python /workspace/kernelbench_eval.py",
        "--impl /workspace/implementation.py",
        "--reference /workspace/reference.py",
        "--output /workspace/results.json",
        f"--seed {seed}",
    ]
    if run_benchmarks:
        eval_cmd_parts.append("--benchmark")
    if run_defensive and defense_code_b64:
        eval_cmd_parts.append("--defensive")
        eval_cmd_parts.append("--defense-module /workspace/defense.py")
    if inputs_code_b64:
        eval_cmd_parts.append("--inputs /workspace/custom_inputs.py")

    eval_cmd = " ".join(eval_cmd_parts)

    return f'''
import asyncio
import base64
import json
import sys
import modal

async def run_eval():
    app = modal.App.lookup("wafer-evaluate", create_if_missing=True)

    # Build image with PyTorch, CUTLASS DSL and dependencies
    image = (
        modal.Image.from_registry(
            "nvidia/cuda:12.9.0-devel-ubuntu22.04",
            add_python="3.12",
        )
        .apt_install("git", "build-essential", "cmake", "ninja-build", "ripgrep")
        .pip_install(
            "torch",
            index_url="{torch_index}",
            extra_index_url="https://pypi.org/simple",
        )
        .pip_install(
            "numpy",
            "triton",
            "ninja",
        )
        {cutlass_install}
        .env({{
            "CUDA_HOME": "/usr/local/cuda",
            # C++ compiler needs explicit include path for cuda_runtime.h
            "CPLUS_INCLUDE_PATH": "/usr/local/cuda/include",
            # Linker needs lib path
            "LIBRARY_PATH": "/usr/local/cuda/lib64",
            # Force PyTorch to compile for correct GPU architecture
            "TORCH_CUDA_ARCH_LIST": "{cuda_arch_list}",
        }})
    )

    # Create sandbox
    sandbox = modal.Sandbox.create(
        app=app,
        image=image,
        gpu="{gpu_type}",
        timeout={target.timeout_seconds},
    )

    try:
        # Create workspace directory
        sandbox.exec("mkdir", "-p", "/workspace").wait()

        # Write files to sandbox
        proc = sandbox.exec("python", "-c", f"""
import base64
with open('/workspace/implementation.py', 'w') as f:
    f.write(base64.b64decode('{impl_code_b64}').decode())
with open('/workspace/reference.py', 'w') as f:
    f.write(base64.b64decode('{ref_code_b64}').decode())
with open('/workspace/kernelbench_eval.py', 'w') as f:
    f.write(base64.b64decode('{eval_script_b64}').decode())
print('Files written')
""")
        proc.wait()
        if proc.returncode != 0:
            print(json.dumps({{"success": False, "error": f"Failed to write files: {{proc.stderr.read()}}"}}))
            return
{inputs_write}
{defense_write}
        # Run evaluation
        print(f"Running KernelBench evaluation on {{'{gpu_type}'}}...")
        proc = sandbox.exec("bash", "-c", "{eval_cmd}")

        # Stream output
        for line in proc.stdout:
            print(line, end="")
        for line in proc.stderr:
            print(line, end="", file=sys.stderr)

        proc.wait()

        if proc.returncode != 0:
            print(json.dumps({{"success": False, "error": f"Evaluation failed with exit code {{proc.returncode}}"}}))
            return

        # Read results
        result_proc = sandbox.exec("cat", "/workspace/results.json")
        result_data = result_proc.stdout.read()
        result_proc.wait()

        if result_data:
            results = json.loads(result_data)
            print("EVAL_RESULT_JSON:" + json.dumps(results))
        else:
            print(json.dumps({{"success": False, "error": "No results.json found"}}))

    finally:
        sandbox.terminate()

asyncio.run(run_eval())
'''


async def run_evaluate_kernelbench_modal(
    args: KernelBenchEvaluateArgs,
    target: ModalTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation on Modal sandbox.

    Creates a Modal sandbox, uploads files, runs KernelBench eval, and parses results.
    Uses subprocess to isolate Modal's asyncio from trio.
    """
    import base64
    import subprocess
    import sys

    import trio

    print(f"Creating Modal sandbox ({target.gpu_type}) for KernelBench evaluation...")

    # Encode files as base64
    impl_code_b64 = base64.b64encode(args.implementation.read_bytes()).decode()
    ref_code_b64 = base64.b64encode(args.reference.read_bytes()).decode()
    eval_script_b64 = base64.b64encode(KERNELBENCH_EVAL_SCRIPT.encode()).decode()

    # Encode custom inputs if provided
    inputs_code_b64 = None
    if args.inputs:
        inputs_code_b64 = base64.b64encode(args.inputs.read_bytes()).decode()

    # Encode defense module if defensive mode is enabled
    defense_code_b64 = None
    if args.defensive:
        defense_path = (
            Path(__file__).parent.parent.parent.parent
            / "packages"
            / "wafer-core"
            / "wafer_core"
            / "utils"
            / "kernel_utils"
            / "defense.py"
        )
        if defense_path.exists():
            defense_code_b64 = base64.b64encode(defense_path.read_bytes()).decode()
        else:
            print(f"Warning: defense.py not found at {defense_path}, falling back to basic defense")

    # Build the script
    script = _build_modal_kernelbench_script(
        target=target,
        impl_code_b64=impl_code_b64,
        ref_code_b64=ref_code_b64,
        eval_script_b64=eval_script_b64,
        run_benchmarks=args.benchmark,
        run_defensive=args.defensive,
        defense_code_b64=defense_code_b64,
        seed=args.seed,
        inputs_code_b64=inputs_code_b64,
    )

    def _run_subprocess() -> tuple[str, str, int]:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=target.timeout_seconds + 120,  # Extra buffer for sandbox creation + image build
        )
        return result.stdout, result.stderr, result.returncode

    try:
        stdout, stderr, returncode = await trio.to_thread.run_sync(_run_subprocess)
    except subprocess.TimeoutExpired:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Modal KernelBench evaluation timed out after {target.timeout_seconds}s",
        )
    except Exception as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to run Modal sandbox: {e}",
        )

    # Print output for debugging
    if stdout:
        for line in stdout.split("\n"):
            if not line.startswith("EVAL_RESULT_JSON:"):
                print(line)
    if stderr:
        print(stderr, file=sys.stderr)

    if returncode != 0:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Modal sandbox failed (exit {returncode}): {stderr or stdout}",
        )

    # Parse results from stdout
    result_json = None
    for line in stdout.split("\n"):
        if line.startswith("EVAL_RESULT_JSON:"):
            result_json = line[len("EVAL_RESULT_JSON:") :]
            break

    if not result_json:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message="No results found in Modal output",
        )

    try:
        results = json.loads(result_json)
    except json.JSONDecodeError as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Failed to parse results JSON: {e}",
        )

    # Check for error in results
    if "error" in results and results.get("success") is False:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=results.get("error", "Unknown error"),
        )

    # Extract metrics from results
    return EvaluateResult(
        success=True,
        all_correct=results.get("all_correct", False),
        correctness_score=float(results.get("correctness_score", 0.0)),
        geomean_speedup=float(results.get("geomean_speedup", 0.0)),
        passed_tests=int(results.get("passed_tests", 0)),
        total_tests=int(results.get("total_tests", 0)),
        error_message=results.get("error"),
        test_results=results.get("test_results", []),
        compilation_time_s=results.get("compilation_time_s"),
        profiling_stats=results.get("profiling_stats"),
    )


async def run_evaluate_kernelbench_docker(
    args: KernelBenchEvaluateArgs,
    target: BaremetalTarget | VMTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation in Docker container on SSH-based target.

    Similar to run_evaluate_docker but uses KernelBench eval script instead.
    """
    from datetime import datetime

    from wafer_core.async_ssh import AsyncSSHClient

    CONTAINER_WORKSPACE = "/workspace"
    REMOTE_WORKSPACE_BASE = "~/.wafer/workspaces"

    if not target.docker_image:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message="docker_image must be set for Docker execution",
        )

    # Select GPU
    gpu_id = _select_gpu_id(target, args.gpu_id)

    print(f"Connecting to {target.ssh_target}...")

    async with AsyncSSHClient(target.ssh_target, target.ssh_key) as client:
        # Create workspace
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = f"kernelbench_eval_{timestamp}"
        workspace_path = await client.expand_path(f"{REMOTE_WORKSPACE_BASE}/kernelbench")
        run_path = f"{workspace_path}/{run_dir}"

        await client.exec(f"mkdir -p {run_path}")
        print(f"Created run directory: {run_path}")

        # Read and upload files
        impl_code = args.implementation.read_text()
        ref_code = args.reference.read_text()

        # Write implementation
        impl_path = f"{run_path}/implementation.py"
        write_result = await client.exec(
            f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write implementation: {write_result.stderr}",
            )

        # Write reference
        ref_path = f"{run_path}/reference.py"
        write_result = await client.exec(f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF")
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write reference: {write_result.stderr}",
            )

        # Write custom inputs if provided
        if args.inputs:
            inputs_code = args.inputs.read_text()
            inputs_file_path = f"{run_path}/custom_inputs.py"
            write_result = await client.exec(
                f"cat > '{inputs_file_path}' << 'INPUTS_EOF'\n{inputs_code}\nINPUTS_EOF"
            )
            if write_result.exit_code != 0:
                return EvaluateResult(
                    success=False,
                    all_correct=False,
                    correctness_score=0.0,
                    geomean_speedup=0.0,
                    passed_tests=0,
                    total_tests=0,
                    error_message=f"Failed to write custom inputs: {write_result.stderr}",
                )

        # Write eval script
        eval_script_path = f"{run_path}/kernelbench_eval.py"
        write_result = await client.exec(
            f"cat > '{eval_script_path}' << 'EVAL_EOF'\n{KERNELBENCH_EVAL_SCRIPT}\nEVAL_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write eval script: {write_result.stderr}",
            )

        # Write defense module if defensive mode is enabled
        defense_module_path = None
        if args.defensive:
            defense_path = (
                Path(__file__).parent.parent.parent.parent
                / "packages"
                / "wafer-core"
                / "wafer_core"
                / "utils"
                / "kernel_utils"
                / "defense.py"
            )
            if defense_path.exists():
                defense_code = defense_path.read_text()
                defense_module_path = f"{run_path}/defense.py"
                write_result = await client.exec(
                    f"cat > '{defense_module_path}' << 'DEFENSE_EOF'\n{defense_code}\nDEFENSE_EOF"
                )
                if write_result.exit_code != 0:
                    print(f"Warning: Failed to write defense module: {write_result.stderr}")
                    defense_module_path = None
            else:
                print(f"Warning: defense.py not found at {defense_path}")

        print("Running KernelBench evaluation in Docker container...")

        # Paths inside container
        container_run_path = f"{CONTAINER_WORKSPACE}/{run_dir}"
        container_impl_path = f"{container_run_path}/implementation.py"
        container_ref_path = f"{container_run_path}/reference.py"
        container_inputs_path = f"{container_run_path}/custom_inputs.py" if args.inputs else None
        container_eval_script = f"{container_run_path}/kernelbench_eval.py"
        container_output = f"{container_run_path}/results.json"
        container_defense_path = f"{container_run_path}/defense.py" if defense_module_path else None

        # Build eval command
        python_cmd_parts = [
            f"python3 {container_eval_script}",
            f"--impl {container_impl_path}",
            f"--reference {container_ref_path}",
            f"--output {container_output}",
        ]

        if args.benchmark:
            python_cmd_parts.append("--benchmark")
        if args.profile:
            python_cmd_parts.append("--profile")
        if container_inputs_path:
            python_cmd_parts.append(f"--inputs {container_inputs_path}")
        if args.defensive and container_defense_path:
            python_cmd_parts.append("--defensive")
            python_cmd_parts.append(f"--defense-module {container_defense_path}")
        python_cmd_parts.append(f"--seed {args.seed}")
        python_cmd_parts.append(f"--stages {args.stages}")

        eval_cmd = " ".join(python_cmd_parts)

        # Build pip install for torch dependencies if needed
        pip_install_cmd = _build_docker_pip_install_cmd(target)
        full_cmd = f"{pip_install_cmd} && cd {container_run_path} && {eval_cmd}"

        # Build Docker command
        docker_cmd = _build_docker_run_command(
            image=target.docker_image,
            command=full_cmd,
            working_dir=container_run_path,
            env={"CUDA_VISIBLE_DEVICES": str(gpu_id), "PYTHONUNBUFFERED": "1"},
            gpus="all",
            volumes={workspace_path: CONTAINER_WORKSPACE},
        )

        print(f"Docker command: {docker_cmd[:100]}...")

        # Run and stream output
        log_lines = []
        async for line in client.exec_stream(docker_cmd):
            print(line, flush=True)
            log_lines.append(line)

        # Read results
        results_path = f"{run_path}/results.json"
        cat_result = await client.exec(f"cat {results_path}")

        if cat_result.exit_code != 0:
            log_tail = "\n".join(log_lines[-50:])
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Evaluation failed. Log tail:\n{log_tail}",
            )

        # Parse results
        try:
            results_data = json.loads(cat_result.stdout)
        except json.JSONDecodeError as e:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to parse results: {e}",
            )

        # Convert to EvaluateResult
        # TODO: use compiled field - currently ignored, should affect success/error
        # compiled = results_data.get("compiled", False)
        correct = results_data.get("correct", False)
        speedup = results_data.get("speedup", 0.0) or 0.0
        error = results_data.get("error")

        if error:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=1,
                error_message=error,
            )

        return EvaluateResult(
            success=True,
            all_correct=correct,
            correctness_score=1.0 if correct else 0.0,
            geomean_speedup=speedup,
            passed_tests=1 if correct else 0,
            total_tests=1,
        )


# Default ROCm PyTorch image for DigitalOcean AMD MI300X
DEFAULT_ROCM_DOCKER_IMAGE = "rocm/pytorch:rocm6.2_ubuntu22.04_py3.10_pytorch_release_2.3.0"


async def run_evaluate_kernelbench_digitalocean(
    args: KernelBenchEvaluateArgs,
    target: DigitalOceanTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation in Docker container on DigitalOcean AMD GPU.

    Uses ROCm Docker image with device passthrough for AMD GPUs.
    """
    from datetime import datetime

    import trio_asyncio
    from wafer_core.async_ssh import AsyncSSHClient
    from wafer_core.targets.digitalocean import digitalocean_ssh_context

    CONTAINER_WORKSPACE = "/workspace"
    REMOTE_WORKSPACE_BASE = "~/.wafer/workspaces"

    docker_image = DEFAULT_ROCM_DOCKER_IMAGE

    # Select GPU
    gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]

    print("Provisioning/connecting to DigitalOcean droplet...")

    async with digitalocean_ssh_context(target) as ssh_info:
        ssh_target = f"{ssh_info.user}@{ssh_info.host}:{ssh_info.port}"
        print(f"Connected to {ssh_target}")

        async with trio_asyncio.open_loop():
            async with AsyncSSHClient(ssh_target, target.ssh_key) as client:
                # Ensure Docker is installed
                docker_check = await client.exec("which docker")
                if docker_check.exit_code != 0:
                    print("Docker not found, installing...")
                    install_result = await client.exec(
                        "apt-get update -qq && apt-get install -y -qq docker.io"
                    )
                    if install_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to install Docker: {install_result.stderr}",
                        )

                # Create workspace
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_dir = f"kernelbench_eval_{timestamp}"
                workspace_path = await client.expand_path(f"{REMOTE_WORKSPACE_BASE}/kernelbench")
                run_path = f"{workspace_path}/{run_dir}"

                await client.exec(f"mkdir -p {run_path}")
                print(f"Created run directory: {run_path}")

                # Read and upload files
                impl_code = args.implementation.read_text()
                ref_code = args.reference.read_text()

                # Write implementation
                impl_path = f"{run_path}/implementation.py"
                write_result = await client.exec(
                    f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write implementation: {write_result.stderr}",
                    )

                # Write reference
                ref_path = f"{run_path}/reference.py"
                write_result = await client.exec(
                    f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write reference: {write_result.stderr}",
                    )

                # Write custom inputs if provided
                if args.inputs:
                    inputs_code = args.inputs.read_text()
                    inputs_file_path = f"{run_path}/custom_inputs.py"
                    write_result = await client.exec(
                        f"cat > '{inputs_file_path}' << 'INPUTS_EOF'\n{inputs_code}\nINPUTS_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write custom inputs: {write_result.stderr}",
                        )

                # Write eval script
                eval_script_path = f"{run_path}/kernelbench_eval.py"
                write_result = await client.exec(
                    f"cat > '{eval_script_path}' << 'EVAL_EOF'\n{KERNELBENCH_EVAL_SCRIPT}\nEVAL_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write eval script: {write_result.stderr}",
                    )

                # Write defense module if defensive mode is enabled
                defense_module_path = None
                if args.defensive:
                    defense_path = (
                        Path(__file__).parent.parent.parent.parent
                        / "packages"
                        / "wafer-core"
                        / "wafer_core"
                        / "utils"
                        / "kernel_utils"
                        / "defense.py"
                    )
                    if defense_path.exists():
                        defense_code = defense_path.read_text()
                        defense_module_path = f"{run_path}/defense.py"
                        write_result = await client.exec(
                            f"cat > '{defense_module_path}' << 'DEFENSE_EOF'\n{defense_code}\nDEFENSE_EOF"
                        )
                        if write_result.exit_code != 0:
                            print(f"Warning: Failed to write defense module: {write_result.stderr}")
                            defense_module_path = None
                    else:
                        print(f"Warning: defense.py not found at {defense_path}")

                print("Running KernelBench evaluation in Docker container (AMD/ROCm)...")

                # Paths inside container
                container_run_path = f"{CONTAINER_WORKSPACE}/{run_dir}"
                container_impl_path = f"{container_run_path}/implementation.py"
                container_ref_path = f"{container_run_path}/reference.py"
                container_inputs_path = (
                    f"{container_run_path}/custom_inputs.py" if args.inputs else None
                )
                container_eval_script = f"{container_run_path}/kernelbench_eval.py"
                container_output = f"{container_run_path}/results.json"
                container_defense_path = (
                    f"{container_run_path}/defense.py" if defense_module_path else None
                )

                # Build eval command
                python_cmd_parts = [
                    f"python3 {container_eval_script}",
                    f"--impl {container_impl_path}",
                    f"--reference {container_ref_path}",
                    f"--output {container_output}",
                ]

                if args.benchmark:
                    python_cmd_parts.append("--benchmark")
                if args.profile:
                    python_cmd_parts.append("--profile")
                if container_inputs_path:
                    python_cmd_parts.append(f"--inputs {container_inputs_path}")
                if args.defensive and container_defense_path:
                    python_cmd_parts.append("--defensive")
                    python_cmd_parts.append(f"--defense-module {container_defense_path}")
                python_cmd_parts.append(f"--seed {args.seed}")
                python_cmd_parts.append(f"--stages {args.stages}")

                eval_cmd = " ".join(python_cmd_parts)

                # For AMD, we don't need pip install - the ROCm image has everything
                full_cmd = f"cd {container_run_path} && {eval_cmd}"

                # Build Docker command for AMD
                # PYTORCH_ROCM_ARCH: compile only for target arch (5-7x faster compile)
                rocm_arch = _get_rocm_arch(target.compute_capability)
                env_dict = {
                    "HIP_VISIBLE_DEVICES": str(gpu_id),
                    "PYTHONUNBUFFERED": "1",
                }
                if rocm_arch:
                    env_dict["PYTORCH_ROCM_ARCH"] = rocm_arch

                docker_cmd = _build_docker_run_command_amd(
                    image=docker_image,
                    command=full_cmd,
                    working_dir=container_run_path,
                    env=env_dict,
                    volumes={workspace_path: CONTAINER_WORKSPACE},
                )

                print(f"Docker command: {docker_cmd[:100]}...")

                # Run and stream output
                log_lines = []
                async for line in client.exec_stream(docker_cmd):
                    print(line, flush=True)
                    log_lines.append(line)

                # Read results
                results_path = f"{run_path}/results.json"
                cat_result = await client.exec(f"cat {results_path}")

                if cat_result.exit_code != 0:
                    log_tail = "\n".join(log_lines[-50:])
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Evaluation failed. Log tail:\n{log_tail}",
                    )

                # Parse results
                try:
                    results_data = json.loads(cat_result.stdout)
                except json.JSONDecodeError as e:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to parse results: {e}",
                    )

                # Convert to EvaluateResult
                # TODO: use compiled field - currently ignored, should affect success/error
                # compiled = results_data.get("compiled", False)
                correct = results_data.get("correct", False)
                speedup = results_data.get("speedup", 0.0) or 0.0
                error = results_data.get("error")

                if error:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=1,
                        error_message=error,
                    )

                return EvaluateResult(
                    success=True,
                    all_correct=correct,
                    correctness_score=1.0 if correct else 0.0,
                    geomean_speedup=speedup,
                    passed_tests=1 if correct else 0,
                    total_tests=1,
                )


async def run_evaluate_kernelbench_runpod(
    args: KernelBenchEvaluateArgs,
    target: RunPodTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation directly on RunPod AMD GPU.

    Runs evaluation script directly on host (no Docker) since RunPod pods
    already have PyTorch/ROCm installed.
    """
    from datetime import datetime

    from wafer_core.async_ssh import AsyncSSHClient
    from wafer_core.targets.runpod import RunPodError, runpod_ssh_context

    REMOTE_WORKSPACE_BASE = "/tmp/wafer_eval"

    # Select GPU
    gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]

    print(f"Provisioning RunPod ({target.gpu_type_id})...")

    try:
        async with runpod_ssh_context(target) as ssh_info:
            ssh_target = f"{ssh_info.user}@{ssh_info.host}:{ssh_info.port}"
            print(f"Connected to RunPod: {ssh_target}")

            async with AsyncSSHClient(ssh_target, target.ssh_key) as client:
                # Create workspace
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                run_dir = f"kernelbench_eval_{timestamp}"
                run_path = f"{REMOTE_WORKSPACE_BASE}/{run_dir}"

                await client.exec(f"mkdir -p {run_path}")
                print(f"Created run directory: {run_path}")

                # Read and upload files
                impl_code = args.implementation.read_text()
                ref_code = args.reference.read_text()

                # Write implementation
                impl_path = f"{run_path}/implementation.py"
                write_result = await client.exec(
                    f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write implementation: {write_result.stderr}",
                    )

                # Write reference
                ref_path = f"{run_path}/reference.py"
                write_result = await client.exec(
                    f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write reference: {write_result.stderr}",
                    )

                # Write custom inputs if provided
                inputs_path = None
                if args.inputs:
                    inputs_code = args.inputs.read_text()
                    inputs_path = f"{run_path}/custom_inputs.py"
                    write_result = await client.exec(
                        f"cat > '{inputs_path}' << 'INPUTS_EOF'\n{inputs_code}\nINPUTS_EOF"
                    )
                    if write_result.exit_code != 0:
                        return EvaluateResult(
                            success=False,
                            all_correct=False,
                            correctness_score=0.0,
                            geomean_speedup=0.0,
                            passed_tests=0,
                            total_tests=0,
                            error_message=f"Failed to write custom inputs: {write_result.stderr}",
                        )

                # Write eval script
                eval_script_path = f"{run_path}/kernelbench_eval.py"
                write_result = await client.exec(
                    f"cat > '{eval_script_path}' << 'EVAL_EOF'\n{KERNELBENCH_EVAL_SCRIPT}\nEVAL_EOF"
                )
                if write_result.exit_code != 0:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to write eval script: {write_result.stderr}",
                    )

                # Write defense module if defensive mode is enabled
                defense_module_path = None
                if args.defensive:
                    defense_path = (
                        Path(__file__).parent.parent.parent.parent
                        / "packages"
                        / "wafer-core"
                        / "wafer_core"
                        / "utils"
                        / "kernel_utils"
                        / "defense.py"
                    )
                    if defense_path.exists():
                        defense_code = defense_path.read_text()
                        defense_module_path = f"{run_path}/defense.py"
                        write_result = await client.exec(
                            f"cat > '{defense_module_path}' << 'DEFENSE_EOF'\n{defense_code}\nDEFENSE_EOF"
                        )
                        if write_result.exit_code != 0:
                            print(f"Warning: Failed to write defense module: {write_result.stderr}")
                            defense_module_path = None
                    else:
                        print(f"Warning: defense.py not found at {defense_path}")

                print("Running KernelBench evaluation (AMD/ROCm)...")

                # Find Python with PyTorch - check common locations on RunPod
                python_exe = "python3"
                for candidate in [
                    "/opt/venv/bin/python3",
                    "/opt/conda/envs/py_3.10/bin/python3",
                    "/opt/conda/bin/python3",
                ]:
                    check = await client.exec(
                        f"{candidate} -c 'import torch' 2>/dev/null && echo OK"
                    )
                    if "OK" in check.stdout:
                        python_exe = candidate
                        print(f"Using Python: {python_exe}")
                        break

                # Build eval command - run directly on host
                output_path = f"{run_path}/results.json"
                python_cmd_parts = [
                    f"{python_exe} {eval_script_path}",
                    f"--impl {impl_path}",
                    f"--reference {ref_path}",
                    f"--output {output_path}",
                ]

                if args.benchmark:
                    python_cmd_parts.append("--benchmark")
                if args.profile:
                    python_cmd_parts.append("--profile")
                if inputs_path:
                    python_cmd_parts.append(f"--inputs {inputs_path}")
                if args.defensive and defense_module_path:
                    python_cmd_parts.append("--defensive")
                    python_cmd_parts.append(f"--defense-module {defense_module_path}")
                python_cmd_parts.append(f"--seed {args.seed}")
                python_cmd_parts.append(f"--stages {args.stages}")

                eval_cmd = " ".join(python_cmd_parts)

                # Set environment for AMD GPU and run
                # PYTORCH_ROCM_ARCH: compile only for target arch (5-7x faster compile)
                rocm_arch = _get_rocm_arch(target.compute_capability)
                arch_env = f"PYTORCH_ROCM_ARCH={rocm_arch}" if rocm_arch else ""
                env_vars = f"HIP_VISIBLE_DEVICES={gpu_id} ROCM_PATH=/opt/rocm PYTHONUNBUFFERED=1 {arch_env}"
                full_cmd = f"cd {run_path} && {env_vars} {eval_cmd}"

                # Handle prepare-only mode
                if args.prepare_only:
                    print(f"\n[wafer] Prepared evaluation at: {run_path}")
                    print(f"[wafer] Target: {target.name} ({client.host}:{client.port})")
                    print("[wafer] To run manually:")
                    print(f"  ssh -p {client.port} root@{client.host} '{full_cmd}'")
                    print("\n[wafer] Or wrap with rocprof:")
                    print(
                        f"  ssh -p {client.port} root@{client.host} 'cd {run_path} && {env_vars} rocprof -i counters.txt {eval_cmd}'"
                    )
                    return EvaluateResult(
                        success=True,
                        all_correct=None,  # Not checked in prepare-only mode
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=None,
                    )

                # Run and stream output
                log_lines = []
                async for line in client.exec_stream(full_cmd):
                    print(line, flush=True)
                    log_lines.append(line)

                # Read results
                cat_result = await client.exec(f"cat {output_path}")

                if cat_result.exit_code != 0:
                    log_tail = "\n".join(log_lines[-50:])
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Evaluation failed. Log tail:\n{log_tail}",
                    )

                # Parse results
                try:
                    results_data = json.loads(cat_result.stdout)
                except json.JSONDecodeError as e:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=0,
                        error_message=f"Failed to parse results: {e}",
                    )

                # Convert to EvaluateResult
                correct = results_data.get("correct", False)
                speedup = results_data.get("speedup", 0.0) or 0.0
                error = results_data.get("error")

                if error:
                    return EvaluateResult(
                        success=False,
                        all_correct=False,
                        correctness_score=0.0,
                        geomean_speedup=0.0,
                        passed_tests=0,
                        total_tests=1,
                        error_message=error,
                    )

                return EvaluateResult(
                    success=True,
                    all_correct=correct,
                    correctness_score=1.0 if correct else 0.0,
                    geomean_speedup=speedup,
                    passed_tests=1 if correct else 0,
                    total_tests=1,
                )

    except RunPodError as e:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"RunPod error: {e}",
        )


async def run_evaluate_kernelbench_baremetal_direct(
    args: KernelBenchEvaluateArgs,
    target: BaremetalTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation directly on NVIDIA target (no Docker).

    For targets that already have PyTorch/CUDA installed (e.g., workspace containers).
    Uses CUDA_VISIBLE_DEVICES for GPU selection.
    """
    # Reuse the AMD function but with CUDA env vars
    # The logic is identical, just the GPU env var is different
    return await _run_evaluate_kernelbench_baremetal_direct_impl(
        args, target, gpu_env_var="CUDA_VISIBLE_DEVICES"
    )


async def run_evaluate_kernelbench_baremetal_amd(
    args: KernelBenchEvaluateArgs,
    target: BaremetalTarget,
) -> EvaluateResult:
    """Run KernelBench format evaluation directly on AMD baremetal target.

    Runs evaluation script directly on host (no Docker) for AMD GPUs
    that have PyTorch/ROCm installed.
    """
    return await _run_evaluate_kernelbench_baremetal_direct_impl(
        args, target, gpu_env_var="HIP_VISIBLE_DEVICES"
    )


async def _run_evaluate_kernelbench_baremetal_direct_impl(
    args: KernelBenchEvaluateArgs,
    target: BaremetalTarget,
    gpu_env_var: str = "HIP_VISIBLE_DEVICES",
) -> EvaluateResult:
    """Internal implementation for direct baremetal evaluation.

    Runs evaluation script directly on host (no Docker).
    """
    from datetime import datetime

    from wafer_core.async_ssh import AsyncSSHClient

    REMOTE_WORKSPACE_BASE = "/tmp/wafer_eval"

    # Select GPU
    gpu_id = args.gpu_id if args.gpu_id is not None else target.gpu_ids[0]

    print(f"Connecting to {target.ssh_target}...")

    async with AsyncSSHClient(target.ssh_target, target.ssh_key) as client:
        # Create workspace
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = f"kernelbench_eval_{timestamp}"
        run_path = f"{REMOTE_WORKSPACE_BASE}/{run_dir}"

        await client.exec(f"mkdir -p {run_path}")
        print(f"Created run directory: {run_path}")

        # Read and upload files
        impl_code = args.implementation.read_text()
        ref_code = args.reference.read_text()

        # Write implementation
        impl_path = f"{run_path}/implementation.py"
        write_result = await client.exec(
            f"cat > '{impl_path}' << 'IMPL_EOF'\n{impl_code}\nIMPL_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write implementation: {write_result.stderr}",
            )

        # Write reference
        ref_path = f"{run_path}/reference.py"
        write_result = await client.exec(f"cat > '{ref_path}' << 'REF_EOF'\n{ref_code}\nREF_EOF")
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write reference: {write_result.stderr}",
            )

        # Write custom inputs if provided
        inputs_path = None
        if args.inputs:
            inputs_code = args.inputs.read_text()
            inputs_path = f"{run_path}/custom_inputs.py"
            write_result = await client.exec(
                f"cat > '{inputs_path}' << 'INPUTS_EOF'\n{inputs_code}\nINPUTS_EOF"
            )
            if write_result.exit_code != 0:
                return EvaluateResult(
                    success=False,
                    all_correct=False,
                    correctness_score=0.0,
                    geomean_speedup=0.0,
                    passed_tests=0,
                    total_tests=0,
                    error_message=f"Failed to write custom inputs: {write_result.stderr}",
                )

        # Write eval script
        eval_script_path = f"{run_path}/kernelbench_eval.py"
        write_result = await client.exec(
            f"cat > '{eval_script_path}' << 'EVAL_EOF'\n{KERNELBENCH_EVAL_SCRIPT}\nEVAL_EOF"
        )
        if write_result.exit_code != 0:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to write eval script: {write_result.stderr}",
            )

        # Write defense module if defensive mode is enabled
        defense_module_path = None
        if args.defensive:
            defense_path = (
                Path(__file__).parent.parent.parent.parent
                / "packages"
                / "wafer-core"
                / "wafer_core"
                / "utils"
                / "kernel_utils"
                / "defense.py"
            )
            if defense_path.exists():
                defense_code = defense_path.read_text()
                defense_module_path = f"{run_path}/defense.py"
                write_result = await client.exec(
                    f"cat > '{defense_module_path}' << 'DEFENSE_EOF'\n{defense_code}\nDEFENSE_EOF"
                )
                if write_result.exit_code != 0:
                    print(f"Warning: Failed to write defense module: {write_result.stderr}")
                    defense_module_path = None
            else:
                print(f"Warning: defense.py not found at {defense_path}")

        print("Running KernelBench evaluation (AMD/ROCm)...")

        # Find Python with PyTorch - check common locations
        python_exe = "python3"
        for candidate in [
            "/opt/conda/envs/py_3.10/bin/python3",
            "/opt/conda/bin/python3",
        ]:
            check = await client.exec(f"{candidate} -c 'import torch' 2>/dev/null && echo OK")
            if "OK" in check.stdout:
                python_exe = candidate
                print(f"Using Python: {python_exe}")
                break

        # Build eval command - run directly on host
        output_path = f"{run_path}/results.json"
        python_cmd_parts = [
            f"{python_exe} {eval_script_path}",
            f"--impl {impl_path}",
            f"--reference {ref_path}",
            f"--output {output_path}",
        ]

        if args.benchmark:
            python_cmd_parts.append("--benchmark")
        if args.profile:
            python_cmd_parts.append("--profile")
        if inputs_path:
            python_cmd_parts.append(f"--inputs {inputs_path}")
        if args.defensive and defense_module_path:
            python_cmd_parts.append("--defensive")
            python_cmd_parts.append(f"--defense-module {defense_module_path}")
        python_cmd_parts.append(f"--seed {args.seed}")
        python_cmd_parts.append(f"--stages {args.stages}")

        eval_cmd = " ".join(python_cmd_parts)

        # Set environment for GPU and run
        if gpu_env_var == "HIP_VISIBLE_DEVICES":
            # AMD: PYTORCH_ROCM_ARCH for faster compile
            rocm_arch = _get_rocm_arch(target.compute_capability)
            arch_env = f"PYTORCH_ROCM_ARCH={rocm_arch}" if rocm_arch else ""
            env_vars = (
                f"HIP_VISIBLE_DEVICES={gpu_id} ROCM_PATH=/opt/rocm PYTHONUNBUFFERED=1 {arch_env}"
            )
        else:
            # NVIDIA: just set CUDA_VISIBLE_DEVICES
            env_vars = f"CUDA_VISIBLE_DEVICES={gpu_id} PYTHONUNBUFFERED=1"
        full_cmd = f"cd {run_path} && {env_vars} {eval_cmd}"

        # Handle prepare-only mode
        if args.prepare_only:
            print(f"\n[wafer] Prepared evaluation at: {run_path}")
            print(f"[wafer] Target: {target.name} ({client.host}:{client.port})")
            print("[wafer] To run manually:")
            print(f"  ssh -p {client.port} root@{client.host} '{full_cmd}'")
            print("\n[wafer] Or wrap with rocprof:")
            print(
                f"  ssh -p {client.port} root@{client.host} 'cd {run_path} && {env_vars} rocprof -i counters.txt {eval_cmd}'"
            )
            return EvaluateResult(
                success=True,
                all_correct=None,  # Not checked in prepare-only mode
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=None,
            )

        # Run and stream output
        log_lines = []
        async for line in client.exec_stream(full_cmd):
            print(line, flush=True)
            log_lines.append(line)

        # Read results
        cat_result = await client.exec(f"cat {output_path}")

        if cat_result.exit_code != 0:
            log_tail = "\n".join(log_lines[-50:])
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Evaluation failed. Log tail:\n{log_tail}",
            )

        # Parse results
        try:
            results_data = json.loads(cat_result.stdout)
        except json.JSONDecodeError as e:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=f"Failed to parse results: {e}",
            )

        # Convert to EvaluateResult
        correct = results_data.get("correct", False)
        speedup = results_data.get("speedup", 0.0) or 0.0
        error = results_data.get("error")

        if error:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=1,
                error_message=error,
            )

        return EvaluateResult(
            success=True,
            all_correct=correct,
            correctness_score=1.0 if correct else 0.0,
            geomean_speedup=speedup,
            passed_tests=1 if correct else 0,
            total_tests=1,
        )


async def run_evaluate_kernelbench(args: KernelBenchEvaluateArgs) -> EvaluateResult:
    """Run KernelBench format evaluation on configured target.

    Args:
        args: KernelBench evaluate arguments

    Returns:
        Evaluation result
    """
    from .targets import get_default_target, load_target

    # Validate input files
    err = _validate_kernelbench_files(args)
    if err:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=err,
        )

    # Load target
    target_name = args.target_name
    if not target_name:
        target_name = get_default_target()
        if not target_name:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=(
                    "No target specified and no default set.\n"
                    "Set up a target first:\n"
                    "  wafer config targets init ssh --name my-gpu --host user@host:22\n"
                    "  wafer config targets init runpod --gpu MI300X\n"
                    "Then use: --target my-gpu (or set default: wafer config targets default my-gpu)"
                ),
            )

    try:
        target = load_target(target_name)
    except FileNotFoundError:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=f"Target not found: {target_name}. Run: wafer config targets list",
        )

    print(f"Using target: {target_name}")

    # Dispatch to appropriate executor
    if isinstance(target, DigitalOceanTarget):
        # DigitalOcean AMD MI300X - uses ROCm Docker with device passthrough
        return await run_evaluate_kernelbench_digitalocean(args, target)
    elif isinstance(target, RunPodTarget):
        # RunPod AMD MI300X - uses ROCm Docker with device passthrough
        return await run_evaluate_kernelbench_runpod(args, target)
    elif isinstance(target, ModalTarget):
        # Modal serverless - runs in Modal sandbox
        return await run_evaluate_kernelbench_modal(args, target)
    elif isinstance(target, BaremetalTarget | VMTarget):
        # Check if this is an AMD target (gfx* compute capability) - run directly
        if target.compute_capability and target.compute_capability.startswith("gfx"):
            return await run_evaluate_kernelbench_baremetal_amd(args, target)
        # Check for direct execution flag (workspace containers that already have everything)
        if getattr(target, "direct", False):
            return await run_evaluate_kernelbench_baremetal_direct(args, target)
        # NVIDIA targets - require docker_image to be set
        if not target.docker_image:
            return EvaluateResult(
                success=False,
                all_correct=False,
                correctness_score=0.0,
                geomean_speedup=0.0,
                passed_tests=0,
                total_tests=0,
                error_message=(
                    f"Target '{target_name}' does not have docker_image set. "
                    "KernelBench format requires Docker execution."
                ),
            )
        return await run_evaluate_kernelbench_docker(args, target)
    else:
        return EvaluateResult(
            success=False,
            all_correct=False,
            correctness_score=0.0,
            geomean_speedup=0.0,
            passed_tests=0,
            total_tests=0,
            error_message=(
                f"Target type '{type(target).__name__}' not yet supported for KernelBench format. "
                "Use a DigitalOcean, RunPod, Baremetal, or VM target."
            ),
        )
