"""NSYS Analyze - Parse and analyze .nsys-rep profile files.

This module provides the implementation for the `wafer nvidia nsys analyze` command.
Supports local analysis (when nsys is installed), remote analysis via API,
direct SSH analysis via targets, and workspace execution.

Local analysis uses `nsys stats` and `nsys export` commands which work on any machine
with nsys installed (no GPU required for analysis, only for profiling).
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Known NSYS installation paths by platform
# NOTE: On macOS, NVIDIA only provides the GUI viewer (nsys-ui), NOT the CLI tool.
# The nsys CLI is only available on Linux. macOS users must use remote analysis.
NSYS_PATHS = {
    "linux": [
        "/usr/bin/nsys",
        "/usr/local/bin/nsys",
        "/usr/local/cuda/bin/nsys",
        "/opt/nvidia/nsight-systems/bin/nsys",
        "/opt/nvidia/nsight-systems-cli/bin/nsys",
    ],
    # macOS: nsys CLI not available - only GUI viewer exists
    # Set to empty list to always fall back to remote analysis
    "darwin": [],
    "windows": [
        r"C:\Program Files\NVIDIA Corporation\Nsight Systems\bin\nsys.exe",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin\nsys.exe",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\nsys.exe",
    ],
}


@dataclass(frozen=True)
class NSYSCheckResult:
    """Result of checking NSYS installation."""

    installed: bool
    path: str | None = None
    version: str | None = None
    install_command: str | None = None


@dataclass(frozen=True)
class KernelInfo:
    """Information about a CUDA kernel from NSYS profile."""

    name: str
    duration_ns: int
    duration_ms: float
    instances: int
    avg_duration_ns: float
    min_duration_ns: int
    max_duration_ns: int
    grid_size: str | None = None
    block_size: str | None = None
    registers_per_thread: int | None = None
    shared_memory_bytes: int | None = None
    memory_throughput_gb_s: float | None = None


@dataclass(frozen=True)
class MemoryTransfer:
    """Information about a memory transfer from NSYS profile."""

    operation: str  # HtoD, DtoH, DtoD, etc.
    duration_ns: int
    size_bytes: int
    throughput_gb_s: float
    instances: int


@dataclass(frozen=True)
class NSYSAnalysisResult:
    """Complete NSYS analysis result."""

    success: bool
    report_id: str | None = None
    gpu: str = "Unknown"
    duration_ms: float = 0.0
    kernel_count: int = 0
    memory_transfer_count: int = 0
    kernels: list[dict] | None = None
    memory_transfers: list[dict] | None = None
    timeline: list[dict] | None = None
    diagnostics: list[dict] | None = None
    error: str | None = None


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    return "linux"


def _find_nsys() -> str | None:
    """Find nsys executable on the system.

    Searches in order:
    1. PATH environment variable
    2. Common installation paths for the current platform
    """
    # First check PATH
    nsys = shutil.which("nsys")
    if nsys:
        return nsys

    # Then check known installation paths
    plat = _get_platform()
    for path in NSYS_PATHS.get(plat, []):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def _get_nsys_version(nsys_path: str) -> str | None:
    """Get NSYS version string."""
    try:
        result = subprocess.run(
            [nsys_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse version from output like "NVIDIA Nsight Systems version 2024.6.1.90-246160830v0"
            for line in result.stdout.split("\n"):
                if "version" in line.lower():
                    parts = line.split("version")
                    if len(parts) >= 2:
                        return parts[1].strip().split()[0]
            return result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _get_install_command() -> str:
    """Get platform-appropriate install command for NSYS."""
    plat = _get_platform()

    if plat == "darwin":
        # macOS only has GUI viewer, no CLI - user must use remote analysis
        return "NSYS CLI not available on macOS. Use --remote flag or --target for remote analysis."

    if plat == "linux":
        if shutil.which("apt-get") or shutil.which("apt"):
            return "sudo apt install nsight-systems"
        elif shutil.which("dnf"):
            return "sudo dnf install nsight-systems"
        elif shutil.which("yum"):
            return "sudo yum install nsight-systems"
        elif shutil.which("pacman"):
            return "sudo pacman -S nsight-systems"

    if shutil.which("conda"):
        return "conda install -c nvidia nsight-systems"

    return "Download from https://developer.nvidia.com/nsight-systems"


def is_macos() -> bool:
    """Check if running on macOS."""
    return _get_platform() == "darwin"


def check_nsys_installation() -> NSYSCheckResult:
    """Check if NSYS is installed and return details.

    Returns:
        NSYSCheckResult with installation status and details
    """
    nsys_path = _find_nsys()

    if nsys_path is None:
        return NSYSCheckResult(
            installed=False,
            install_command=_get_install_command(),
        )

    version = _get_nsys_version(nsys_path)

    return NSYSCheckResult(
        installed=True,
        path=nsys_path,
        version=version,
    )


def _run_nsys_stats(
    nsys_path: str,
    filepath: Path,
    report_name: str,
    timeout: int = 120,
) -> tuple[bool, str]:
    """Run nsys stats command to extract report data.

    Args:
        nsys_path: Path to nsys executable
        filepath: Path to .nsys-rep file
        report_name: Report type (e.g., gpukernsum, gpumemtimesum, cudaapisum)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, output_or_error)
    """
    try:
        result = subprocess.run(
            [
                nsys_path,
                "stats",
                "--report", report_name,
                "--format", "csv",
                "--force-export", "true",
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, error_msg

        return True, result.stdout

    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except OSError as e:
        return False, f"Failed to execute nsys: {e}"


def _run_nsys_export(
    nsys_path: str,
    filepath: Path,
    output_format: str = "sqlite",
    timeout: int = 180,
) -> tuple[bool, str]:
    """Run nsys export command to export trace data.

    Args:
        nsys_path: Path to nsys executable
        filepath: Path to .nsys-rep file
        output_format: Export format (sqlite, json)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, output_path_or_error)
    """
    # Determine output path
    output_path = filepath.with_suffix(f".{output_format}")

    try:
        result = subprocess.run(
            [
                nsys_path,
                "export",
                "--type", output_format,
                "--force-overwrite", "true",
                "--output", str(output_path),
                str(filepath),
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, error_msg

        return True, str(output_path)

    except subprocess.TimeoutExpired:
        return False, f"Export timed out after {timeout}s"
    except OSError as e:
        return False, f"Failed to execute nsys: {e}"


def _parse_csv_kernels(csv_output: str) -> list[dict]:
    """Parse GPU kernel summary from nsys stats CSV output."""
    kernels = []

    lines = csv_output.strip().split("\n")
    if len(lines) < 2:
        return kernels

    # Find header line - look for a line with known CSV header columns
    # The nsys output includes informational lines before the actual CSV
    # Header line should contain "Time" and "Name" columns
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Skip comment lines and non-CSV lines
        if line.startswith("#"):
            continue
        # Check if this looks like a CSV header with expected columns
        if ("time" in line_lower and "name" in line_lower) or \
           ("time (%)" in line_lower) or \
           ("total time" in line_lower and "instances" in line_lower):
            header_idx = i
            break

    if header_idx < 0 or header_idx >= len(lines) - 1:
        return kernels

    headers = [h.strip().strip('"') for h in lines[header_idx].split(",")]

    # Map header names to indices
    def find_col(names: list[str]) -> int | None:
        for name in names:
            name_lower = name.lower()
            for i, h in enumerate(headers):
                if name_lower in h.lower():
                    return i
        return None

    name_col = find_col(["Name", "Kernel Name", "KernelName"])
    time_col = find_col(["Time (%)", "Time Percent", "Time%"])
    total_time_col = find_col(["Total Time", "TotalTime", "Duration"])
    instances_col = find_col(["Instances", "Count", "Calls"])
    avg_col = find_col(["Avg", "Average", "AvgTime"])
    min_col = find_col(["Min", "Minimum", "MinTime"])
    max_col = find_col(["Max", "Maximum", "MaxTime"])

    # Parse data rows
    for line in lines[header_idx + 1:]:
        if not line.strip() or line.startswith("#"):
            continue

        # Handle CSV with quoted fields
        parts = []
        in_quote = False
        current = ""
        for char in line:
            if char == '"':
                in_quote = not in_quote
            elif char == "," and not in_quote:
                parts.append(current.strip().strip('"'))
                current = ""
            else:
                current += char
        parts.append(current.strip().strip('"'))

        if len(parts) <= (name_col or 0):
            continue

        kernel = {
            "name": parts[name_col] if name_col is not None else "Unknown",
            "time_percent": 0.0,
            "total_time_ns": 0,
            "duration_ms": 0.0,
            "instances": 0,
            "avg_time_ns": 0,
            "min_time_ns": 0,
            "max_time_ns": 0,
        }

        try:
            if time_col is not None and time_col < len(parts):
                kernel["time_percent"] = float(parts[time_col].replace("%", "").strip() or 0)

            if total_time_col is not None and total_time_col < len(parts):
                # Time may be in ns, us, or ms - parse accordingly
                time_str = parts[total_time_col].strip()
                kernel["total_time_ns"] = _parse_time_to_ns(time_str)
                kernel["duration_ms"] = kernel["total_time_ns"] / 1_000_000

            if instances_col is not None and instances_col < len(parts):
                kernel["instances"] = int(float(parts[instances_col].strip() or 0))

            if avg_col is not None and avg_col < len(parts):
                kernel["avg_time_ns"] = _parse_time_to_ns(parts[avg_col].strip())

            if min_col is not None and min_col < len(parts):
                kernel["min_time_ns"] = _parse_time_to_ns(parts[min_col].strip())

            if max_col is not None and max_col < len(parts):
                kernel["max_time_ns"] = _parse_time_to_ns(parts[max_col].strip())

        except (ValueError, IndexError):
            pass

        if kernel["name"] and kernel["name"] != "Unknown":
            kernels.append(kernel)

    return kernels


def _parse_time_to_ns(time_str: str) -> int:
    """Parse time string to nanoseconds."""
    if not time_str:
        return 0

    time_str = time_str.strip().lower()

    try:
        if "ms" in time_str:
            return int(float(time_str.replace("ms", "").strip()) * 1_000_000)
        elif "us" in time_str or "µs" in time_str:
            return int(float(time_str.replace("us", "").replace("µs", "").strip()) * 1_000)
        elif "ns" in time_str:
            return int(float(time_str.replace("ns", "").strip()))
        elif "s" in time_str:
            return int(float(time_str.replace("s", "").strip()) * 1_000_000_000)
        else:
            # Assume nanoseconds
            return int(float(time_str))
    except ValueError:
        return 0


def _parse_csv_memory(csv_output: str) -> list[dict]:
    """Parse memory transfer summary from nsys stats CSV output."""
    transfers = []

    lines = csv_output.strip().split("\n")
    if len(lines) < 2:
        return transfers

    # Find header line - look for a line with known CSV header columns
    # The nsys output includes informational lines before the actual CSV
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Skip comment lines
        if line.startswith("#"):
            continue
        # Check if this looks like a CSV header with expected columns
        if ("time" in line_lower and ("operation" in line_lower or "total" in line_lower)) or \
           ("time (%)" in line_lower) or \
           ("count" in line_lower and "total" in line_lower):
            header_idx = i
            break

    if header_idx < 0 or header_idx >= len(lines) - 1:
        return transfers

    headers = [h.strip().strip('"') for h in lines[header_idx].split(",")]

    # Map header names
    def find_col(names: list[str]) -> int | None:
        for name in names:
            name_lower = name.lower()
            for i, h in enumerate(headers):
                if name_lower in h.lower():
                    return i
        return None

    op_col = find_col(["Operation", "Name", "MemOp"])
    time_col = find_col(["Total Time", "TotalTime", "Duration"])
    size_col = find_col(["Total", "Size", "Bytes"])
    count_col = find_col(["Count", "Instances", "Calls"])
    throughput_col = find_col(["Throughput", "Bandwidth"])

    for line in lines[header_idx + 1:]:
        if not line.strip() or line.startswith("#"):
            continue

        parts = [p.strip().strip('"') for p in line.split(",")]

        if len(parts) <= (op_col or 0):
            continue

        transfer = {
            "operation": parts[op_col] if op_col is not None else "Unknown",
            "total_time_ns": 0,
            "duration_ms": 0.0,
            "size_bytes": 0,
            "instances": 0,
            "throughput_gb_s": 0.0,
        }

        try:
            if time_col is not None and time_col < len(parts):
                transfer["total_time_ns"] = _parse_time_to_ns(parts[time_col])
                transfer["duration_ms"] = transfer["total_time_ns"] / 1_000_000

            if size_col is not None and size_col < len(parts):
                size_str = parts[size_col].strip().upper()
                if "GB" in size_str:
                    transfer["size_bytes"] = int(float(size_str.replace("GB", "").strip()) * 1e9)
                elif "MB" in size_str:
                    transfer["size_bytes"] = int(float(size_str.replace("MB", "").strip()) * 1e6)
                elif "KB" in size_str:
                    transfer["size_bytes"] = int(float(size_str.replace("KB", "").strip()) * 1e3)
                else:
                    transfer["size_bytes"] = int(float(size_str.replace("B", "").strip() or 0))

            if count_col is not None and count_col < len(parts):
                transfer["instances"] = int(float(parts[count_col].strip() or 0))

            if throughput_col is not None and throughput_col < len(parts):
                tp_str = parts[throughput_col].strip().upper()
                if "GB" in tp_str:
                    transfer["throughput_gb_s"] = float(tp_str.replace("GB/S", "").strip())
                elif "MB" in tp_str:
                    transfer["throughput_gb_s"] = float(tp_str.replace("MB/S", "").strip()) / 1000
                else:
                    transfer["throughput_gb_s"] = float(tp_str.replace("/S", "").strip() or 0) / 1e9

        except (ValueError, IndexError):
            pass

        if transfer["operation"] and transfer["operation"] != "Unknown":
            transfers.append(transfer)

    return transfers


def _analyze_local(
    filepath: Path,
    nsys_path: str,
    output_dir: Path | None = None,
    json_output: bool = False,
) -> str:
    """Analyze NSYS profile locally using installed nsys CLI.

    Uses `nsys stats` commands to extract kernel and memory statistics.
    This works on any machine with nsys installed - no GPU required for analysis.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File must exist: {filepath}")
    if filepath.suffix != ".nsys-rep":
        raise ValueError(f"File must be .nsys-rep: {filepath}")

    print(f"Analyzing {filepath.name} locally...", file=sys.stderr)

    # Get GPU kernel summary
    # Note: Report names changed in nsys 2024.x: gpukernsum -> cuda_gpu_kern_sum
    print("Extracting kernel statistics...", file=sys.stderr)
    success, kernel_output = _run_nsys_stats(nsys_path, filepath, "cuda_gpu_kern_sum")

    # Try legacy report name if new one fails
    if not success:
        success, kernel_output = _run_nsys_stats(nsys_path, filepath, "gpukernsum")

    kernels = []
    if success:
        kernels = _parse_csv_kernels(kernel_output)
    else:
        print(f"Warning: Could not extract kernel stats: {kernel_output}", file=sys.stderr)

    # Get memory transfer summary
    # Note: Report names changed in nsys 2024.x: gpumemtimesum -> cuda_gpu_mem_time_sum
    print("Extracting memory statistics...", file=sys.stderr)
    success, mem_output = _run_nsys_stats(nsys_path, filepath, "cuda_gpu_mem_time_sum")

    # Try legacy report names if new one fails
    if not success:
        success, mem_output = _run_nsys_stats(nsys_path, filepath, "gpumemtimesum")

    memory_transfers = []
    if success:
        memory_transfers = _parse_csv_memory(mem_output)
    else:
        # Try alternative report name (for very old nsys versions)
        success, mem_output = _run_nsys_stats(nsys_path, filepath, "cudamemcpysum")
        if success:
            memory_transfers = _parse_csv_memory(mem_output)

    # Get CUDA API summary for additional context
    # Note: Report names changed in nsys 2024.x: cudaapisum -> cuda_api_sum
    print("Extracting CUDA API statistics...", file=sys.stderr)
    success, api_output = _run_nsys_stats(nsys_path, filepath, "cuda_api_sum")

    # Try legacy report name if new one fails
    if not success:
        success, api_output = _run_nsys_stats(nsys_path, filepath, "cudaapisum")

    # Build summary
    total_kernel_time_ms = sum(k.get("duration_ms", 0) for k in kernels)
    total_mem_time_ms = sum(m.get("duration_ms", 0) for m in memory_transfers)

    # Try to get GPU info from report
    gpu_name = "Unknown"

    # Build result
    result = {
        "success": True,
        "summary": {
            "gpu": gpu_name,
            "duration_ms": total_kernel_time_ms + total_mem_time_ms,
            "kernel_count": len(kernels),
            "memory_transfers": len(memory_transfers),
            "total_kernel_time_ms": total_kernel_time_ms,
            "total_memory_time_ms": total_mem_time_ms,
        },
        "kernels": kernels,
        "memory_transfers": memory_transfers,
    }

    # Save to output directory if specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        output_filename = f"nsys_analysis_{filepath.stem}_{timestamp}"

        if json_output:
            json_path = output_dir / f"{output_filename}.json"
            json_path.write_text(json.dumps(result, indent=2))
            print(f"Saved JSON: {json_path}", file=sys.stderr)
        else:
            txt_path = output_dir / f"{output_filename}.txt"
            txt_path.write_text(_generate_text_output(filepath.name, result))
            print(f"Saved analysis: {txt_path}", file=sys.stderr)

    print("Analysis complete.", file=sys.stderr)

    if json_output:
        return json.dumps(result, indent=2)
    else:
        return _generate_text_output(filepath.name, result)


def _analyze_remote_direct(
    filepath: Path,
    target_name: str,
    json_output: bool = False,
) -> str:
    """Analyze NSYS profile remotely via direct SSH to target.

    Uploads the .nsys-rep file and runs nsys analysis on the target machine.
    """
    import tempfile

    from .gpu_run import push_directory, run_command_capture
    from .targets import load_target

    # Load target
    try:
        target = load_target(target_name)
    except FileNotFoundError as e:
        raise RuntimeError(f"Target not found: {target_name}. Create with: wafer targets add {target_name}") from e

    # Create temp directory with just the .nsys-rep file
    workspace_name = f"nsys_analyze_{filepath.stem}"

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a directory with the workspace name
        tmp_path = Path(tmpdir) / workspace_name
        tmp_path.mkdir()
        shutil.copy(filepath, tmp_path / filepath.name)

        # Push the file
        print(f"Uploading {filepath.name} to {target_name}...", file=sys.stderr)
        push_directory(tmp_path, target)

    # Run nsys stats commands on remote
    # First try to find nsys on the remote system
    nsys_paths = [
        "/usr/bin/nsys",
        "/usr/local/cuda/bin/nsys",
        "/opt/nvidia/nsight-systems/bin/nsys",
    ]

    nsys_cmd = "nsys"  # Default to PATH
    for path in nsys_paths:
        check_cmd = f"test -x {path} && echo found"
        exit_code, output = run_command_capture(check_cmd, workspace_name, target)
        if exit_code == 0 and "found" in output:
            nsys_cmd = path
            break

    # Run analysis commands
    # Try new report name first, fall back to legacy if it fails
    print("Running NSYS analysis...", file=sys.stderr)
    analysis_cmd = f"{nsys_cmd} stats --report cuda_gpu_kern_sum --format csv --force-export true {filepath.name}"
    exit_code, kernel_output = run_command_capture(analysis_cmd, workspace_name, target)

    # Try legacy report name if new one fails
    if exit_code != 0 or "could not be found" in kernel_output.lower():
        analysis_cmd = f"{nsys_cmd} stats --report gpukernsum --format csv --force-export true {filepath.name}"
        exit_code, kernel_output = run_command_capture(analysis_cmd, workspace_name, target)

    if exit_code != 0:
        raise RuntimeError(f"NSYS kernel stats failed: {kernel_output}")

    # Get memory stats - try new name first, fall back to legacy
    mem_cmd = f"{nsys_cmd} stats --report cuda_gpu_mem_time_sum --format csv --force-export true {filepath.name}"
    exit_code, mem_output = run_command_capture(mem_cmd, workspace_name, target)

    # Try legacy report name if new one fails
    if exit_code != 0 or "could not be found" in mem_output.lower():
        mem_cmd = f"{nsys_cmd} stats --report gpumemtimesum --format csv --force-export true {filepath.name}"
        exit_code, mem_output = run_command_capture(mem_cmd, workspace_name, target)

    # Parse outputs (memory stats may fail if no memory transfers)
    kernels = _parse_csv_kernels(kernel_output) if kernel_output else []
    memory_transfers = _parse_csv_memory(mem_output) if exit_code == 0 and mem_output else []

    # Build result
    total_kernel_time_ms = sum(k.get("duration_ms", 0) for k in kernels)
    total_mem_time_ms = sum(m.get("duration_ms", 0) for m in memory_transfers)

    result = {
        "success": True,
        "summary": {
            "gpu": "Unknown",  # Would need additional parsing to get GPU name
            "duration_ms": total_kernel_time_ms + total_mem_time_ms,
            "kernel_count": len(kernels),
            "memory_transfers": len(memory_transfers),
        },
        "kernels": kernels,
        "memory_transfers": memory_transfers,
    }

    if json_output:
        return json.dumps(result, indent=2)
    else:
        return _generate_text_output(filepath.name, result)


def _analyze_workspace(
    filepath: Path,
    workspace_id: str,
    json_output: bool = False,
) -> str:
    """Analyze NSYS profile on a Wafer workspace.

    Uses workspace exec to run nsys analysis on the workspace.
    """
    from .workspaces import exec_command_capture

    # First, check if file exists on workspace or needs upload
    # For now, assume file is already on workspace (via sync)
    filename = filepath.name

    print(f"Running NSYS analysis on workspace {workspace_id}...", file=sys.stderr)

    # Try to find nsys on the workspace
    nsys_cmd = "nsys"
    for path in ["/usr/bin/nsys", "/usr/local/cuda/bin/nsys", "/opt/nvidia/nsight-systems/bin/nsys"]:
        check_cmd = f"test -x {path} && echo found"
        exit_code, output = exec_command_capture(workspace_id, check_cmd)
        if exit_code == 0 and "found" in output:
            nsys_cmd = path
            break

    # Run kernel stats - try new report name first, fall back to legacy
    print("Extracting kernel statistics...", file=sys.stderr)
    kernel_cmd = f"{nsys_cmd} stats --report cuda_gpu_kern_sum --format csv --force-export true {filename}"
    exit_code, kernel_output = exec_command_capture(workspace_id, kernel_cmd)

    # Try legacy report name if new one fails
    if exit_code != 0 or "could not be found" in kernel_output.lower():
        kernel_cmd = f"{nsys_cmd} stats --report gpukernsum --format csv --force-export true {filename}"
        exit_code, kernel_output = exec_command_capture(workspace_id, kernel_cmd)

    if exit_code != 0:
        raise RuntimeError(f"NSYS kernel stats failed on workspace: {kernel_output}")

    # Run memory stats - try new report name first, fall back to legacy
    print("Extracting memory statistics...", file=sys.stderr)
    mem_cmd = f"{nsys_cmd} stats --report cuda_gpu_mem_time_sum --format csv --force-export true {filename}"
    exit_code, mem_output = exec_command_capture(workspace_id, mem_cmd)

    # Try legacy report name if new one fails
    if exit_code != 0 or "could not be found" in mem_output.lower():
        mem_cmd = f"{nsys_cmd} stats --report gpumemtimesum --format csv --force-export true {filename}"
        exit_code, mem_output = exec_command_capture(workspace_id, mem_cmd)

    # Parse outputs
    kernels = _parse_csv_kernels(kernel_output) if kernel_output else []
    memory_transfers = _parse_csv_memory(mem_output) if exit_code == 0 and mem_output else []

    # Build result
    total_kernel_time_ms = sum(k.get("duration_ms", 0) for k in kernels)
    total_mem_time_ms = sum(m.get("duration_ms", 0) for m in memory_transfers)

    result = {
        "success": True,
        "summary": {
            "gpu": "Unknown",
            "duration_ms": total_kernel_time_ms + total_mem_time_ms,
            "kernel_count": len(kernels),
            "memory_transfers": len(memory_transfers),
        },
        "kernels": kernels,
        "memory_transfers": memory_transfers,
    }

    if json_output:
        return json.dumps(result, indent=2)
    else:
        return _generate_text_output(filepath.name, result)


def _analyze_remote_api(
    filepath: Path,
    json_output: bool = False,
) -> str:
    """Analyze NSYS profile remotely via wafer-api.

    Uploads the .nsys-rep file and runs analysis on Modal.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File must exist: {filepath}")
    if filepath.suffix != ".nsys-rep":
        raise ValueError(f"File must be .nsys-rep: {filepath}")

    import httpx

    from .api_client import get_api_url
    from .auth import get_auth_headers

    api_url = get_api_url()
    headers = get_auth_headers()

    if not api_url:
        raise ValueError("API URL must be configured")

    # Use multipart/form-data upload
    print(f"Uploading {filepath.name} for analysis...", file=sys.stderr)

    try:
        with httpx.Client(timeout=300.0, headers=headers) as client:
            with open(filepath, "rb") as f:
                files = {"file": (filepath.name, f, "application/octet-stream")}
                data = {"filename": filepath.name}

                response = client.post(
                    f"{api_url}/v1/nsys/tool/analyze",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if not result.get("success", True):
        raise RuntimeError(f"Analysis failed: {result.get('error', 'Unknown error')}")

    # Validate response structure
    if not isinstance(result, dict):
        raise TypeError("API must return a dictionary")

    if json_output:
        return json.dumps(result, indent=2)
    else:
        return _generate_text_output(filepath.name, result)


def _generate_text_output(filename: str, result: dict) -> str:
    """Generate human-readable markdown text from analysis result."""
    if not filename:
        raise ValueError("filename must be non-empty")
    if not isinstance(result, dict):
        raise TypeError("result must be a dictionary")

    timestamp = datetime.now().isoformat()
    summary = result.get("summary", {})
    kernels = result.get("kernels", [])
    memory_transfers = result.get("memory_transfers", [])

    lines = [
        "# NSYS Profiling Analysis",
        f"Source: {filename}",
        f"Generated: {timestamp}",
        "",
        "## Summary",
        f"- GPU: {summary.get('gpu', 'Unknown')}",
        f"- Total Duration: {summary.get('duration_ms', 0):.2f} ms",
        f"- Kernel Count: {summary.get('kernel_count', 0)}",
        f"- Memory Transfers: {summary.get('memory_transfers', 0)}",
        "",
    ]

    if kernels:
        lines.extend([
            "## GPU Kernels",
            "",
            "| Kernel | Time (ms) | Instances | Avg (ms) |",
            "|--------|-----------|-----------|----------|",
        ])

        # Sort by duration descending
        sorted_kernels = sorted(kernels, key=lambda k: k.get("duration_ms", 0), reverse=True)

        for kernel in sorted_kernels[:20]:  # Top 20 kernels
            name = kernel.get("name", "Unknown")
            # Truncate long kernel names
            if len(name) > 50:
                name = name[:47] + "..."
            duration = kernel.get("duration_ms", 0)
            instances = kernel.get("instances", 0)
            avg = kernel.get("avg_time_ns", 0) / 1_000_000 if kernel.get("avg_time_ns") else 0

            lines.append(f"| {name} | {duration:.3f} | {instances} | {avg:.4f} |")

        if len(kernels) > 20:
            lines.append(f"| ... and {len(kernels) - 20} more kernels | | | |")

        lines.append("")

    if memory_transfers:
        lines.extend([
            "## Memory Transfers",
            "",
            "| Operation | Time (ms) | Size | Instances |",
            "|-----------|-----------|------|-----------|",
        ])

        for transfer in memory_transfers:
            op = transfer.get("operation", "Unknown")
            duration = transfer.get("duration_ms", 0)
            size_bytes = transfer.get("size_bytes", 0)
            size_str = _format_bytes(size_bytes)
            instances = transfer.get("instances", 0)

            lines.append(f"| {op} | {duration:.3f} | {size_str} | {instances} |")

        lines.append("")

    # Add diagnostics if present
    diagnostics = result.get("diagnostics", [])
    if diagnostics:
        lines.extend([
            "## Diagnostics",
            "",
        ])
        for diag in diagnostics:
            level = diag.get("level", "Info")
            text = diag.get("text", "")
            lines.append(f"- [{level}] {text}")
        lines.append("")

    return "\n".join(lines)


def _format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if size_bytes >= 1e9:
        return f"{size_bytes / 1e9:.2f} GB"
    elif size_bytes >= 1e6:
        return f"{size_bytes / 1e6:.2f} MB"
    elif size_bytes >= 1e3:
        return f"{size_bytes / 1e3:.2f} KB"
    else:
        return f"{size_bytes} B"


def _parse_target(target: str) -> tuple[str, str]:
    """Parse target string into type and identifier.

    Supports:
    - "workspace:abc123" -> ("workspace", "abc123")
    - "vultr-b200" -> ("target", "vultr-b200")

    Returns:
        Tuple of (target_type, identifier)
    """
    if target.startswith("workspace:"):
        return "workspace", target[len("workspace:"):]
    else:
        return "target", target


def analyze_nsys_profile(
    filepath: Path,
    json_output: bool = False,
    remote: bool | None = None,
    target: str | None = None,
    output_dir: Path | None = None,
) -> str:
    """Analyze an NSYS profile file and return results.

    Args:
        filepath: Path to .nsys-rep file
        json_output: If True, return raw JSON; otherwise return formatted text
        remote: If True, force remote analysis via API. If False, force local.
                If None (default), auto-detect: use local if nsys available, else remote.
        target: Remote target - either "workspace:id" or target name from ~/.wafer/targets/
        output_dir: Optional directory to save analysis results

    Returns:
        Analysis results as string (JSON or markdown)

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If analysis fails
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    if filepath.suffix != ".nsys-rep":
        raise ValueError(f"Expected .nsys-rep file, got: {filepath.suffix}")

    # If target is specified, use appropriate remote execution
    if target:
        target_type, target_id = _parse_target(target)

        if target_type == "workspace":
            return _analyze_workspace(filepath, target_id, json_output)
        else:
            return _analyze_remote_direct(filepath, target_id, json_output)

    # Check for local nsys installation
    nsys_path = _find_nsys()

    # Determine whether to use local or remote
    use_remote = remote
    if use_remote is None:
        # Auto-detect: use local if nsys available, else remote
        use_remote = nsys_path is None

    if use_remote:
        return _analyze_remote_api(filepath, json_output)
    else:
        if nsys_path is None:
            if is_macos():
                raise FileNotFoundError(
                    "NSYS CLI is not available on macOS (only GUI viewer is provided). "
                    "Use --remote flag for API-based analysis or --target for workspace/SSH analysis."
                )
            install_cmd = _get_install_command()
            raise FileNotFoundError(
                f"NSYS not installed locally. Use --remote flag or install with: {install_cmd}"
            )

        return _analyze_local(filepath, nsys_path, output_dir, json_output)
