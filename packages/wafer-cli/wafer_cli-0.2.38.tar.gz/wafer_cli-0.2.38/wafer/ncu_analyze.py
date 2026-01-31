"""NCU Analyze - Parse and analyze .ncu-rep profile files.

This module provides the implementation for the `wafer nvidia ncu analyze` command.
It reuses the parsing logic from services/ncu-tool/ncu_tool.py.

TODO(Wafer-326): Migrate this to wafer-core architecture.
The NCU parsing logic should be consolidated into wafer_core/tools/ncu_parser.py,
similar to how compiler_explorer_tool.py was migrated to wafer_core/tools/compiler.py.
This will:
1. Eliminate duplicate code between this file and extension's ncu_tool.py
2. Enable automatic telemetry via @with_telemetry decorator
3. Allow both CLI and extension to use the same implementation
See wafer_core/tools/compiler.py for the migration pattern.
"""

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

# Known NCU installation paths by platform
NCU_PATHS = {
    "linux": [
        "/usr/local/cuda/bin/ncu",
        "/opt/nvidia/nsight-compute/ncu",
        "/usr/bin/ncu",
        "/usr/local/bin/ncu",
    ],
    "darwin": [
        "/Applications/NVIDIA Nsight Compute.app/Contents/MacOS/ncu",
        "/usr/local/cuda/bin/ncu",
    ],
    "windows": [
        r"C:\Program Files\NVIDIA Corporation\Nsight Compute\ncu.exe",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin\ncu.exe",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\ncu.exe",
    ],
}


# GPU SM counts for common NVIDIA GPUs (used for underfill detection)
GPU_SM_COUNTS = {
    "B200": 148,
    "H100": 132,
    "H200": 132,
    "A100": 108,
    "A10": 72,
    "L4": 58,
    "L40": 142,
    "V100": 80,
    "RTX 4090": 128,
    "RTX 3090": 82,
}


def _get_sm_count_for_gpu(gpu_name: str) -> int:
    """Get SM count for a GPU name. Returns 148 (B200) as default."""
    if not gpu_name:
        return 148
    gpu_upper = gpu_name.upper()
    for gpu_key, sm_count in GPU_SM_COUNTS.items():
        if gpu_key.upper() in gpu_upper:
            return sm_count
    return 148  # Default to B200


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    return "linux"


def _find_ncu() -> str | None:
    """Find NCU executable on the system."""
    ncu = shutil.which("ncu")
    if ncu:
        return ncu

    plat = _get_platform()
    for path in NCU_PATHS.get(plat, []):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def _get_install_command() -> str:
    """Get platform-appropriate install command."""
    plat = _get_platform()

    if plat == "linux":
        if shutil.which("apt-get") or shutil.which("apt"):
            return "sudo apt install nvidia-cuda-toolkit"
        elif shutil.which("dnf"):
            return "sudo dnf install cuda-nsight-compute"
        elif shutil.which("yum"):
            return "sudo yum install cuda-nsight-compute"
        elif shutil.which("pacman"):
            return "sudo pacman -S cuda-tools"

    if shutil.which("conda"):
        return "conda install -c nvidia nsight-compute"

    return "Download from https://developer.nvidia.com/nsight-compute"


def _parse_gpu_from_session(session_output: str) -> str:
    """Parse GPU name from NCU session output."""
    assert isinstance(session_output, str)
    
    for line in session_output.split("\n"):
        if "display_name" in line:
            parts = line.split()
            if len(parts) >= 2:
                return " ".join(parts[1:])
    return "Unknown"


def _create_kernel_entry(kernel_name: str) -> dict:
    """Create a new kernel metrics dict with default values."""
    assert kernel_name, "kernel_name must not be empty"
    
    return {
        "name": kernel_name,
        "duration_us": 0,
        "duration_ms": 0,
        "memory_throughput_pct": 0,
        "compute_throughput_pct": 0,
        "achieved_occupancy_pct": 0,
        "theoretical_occupancy_pct": 0,
        "registers_per_thread": 0,
        "block_size": 0,
        "grid_size": 0,
        "waves_per_sm": 0,
        "estimated_speedup_pct": 0,
        "recommendations": [],
    }


def _parse_metric_line(kernel: dict, metric_line: str, parts: list[str], current_section: str | None) -> None:
    """Parse a metric line and update the kernel dict in place."""
    assert kernel is not None
    assert parts, "parts must not be empty"
    
    # Duration (in us)
    if metric_line.startswith("Duration") and "us" in metric_line:
        try:
            value = float(parts[-1].replace(",", ""))
            kernel["duration_us"] = value
            kernel["duration_ms"] = value / 1000
        except (ValueError, IndexError):
            pass
    # Memory Throughput (%)
    elif "Memory Throughput" in metric_line and "%" in metric_line:
        try:
            kernel["memory_throughput_pct"] = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            pass
    # Compute (SM) Throughput (%)
    elif "Compute (SM) Throughput" in metric_line or "Compute Throughput" in metric_line:
        try:
            kernel["compute_throughput_pct"] = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            pass
    # Achieved Occupancy (%)
    elif "Achieved Occupancy" in metric_line and "%" in metric_line:
        try:
            kernel["achieved_occupancy_pct"] = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            pass
    # Registers Per Thread
    elif "Registers Per Thread" in metric_line:
        try:
            kernel["registers_per_thread"] = int(float(parts[-1].replace(",", "")))
        except (ValueError, IndexError):
            pass
    # Block Size (only from Launch Statistics section)
    elif metric_line.startswith("Block Size") and current_section == "Launch Statistics":
        try:
            kernel["block_size"] = int(float(parts[-1].replace(",", "")))
        except (ValueError, IndexError):
            pass
    # Grid Size (only from Launch Statistics section)
    elif metric_line.startswith("Grid Size") and current_section == "Launch Statistics":
        try:
            kernel["grid_size"] = int(float(parts[-1].replace(",", "")))
        except (ValueError, IndexError):
            pass
    # Waves Per SM (key metric for underfill detection)
    elif "Waves Per SM" in metric_line:
        try:
            kernel["waves_per_sm"] = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            pass
    # Theoretical Occupancy (%)
    elif "Theoretical Occupancy" in metric_line and "%" in metric_line:
        try:
            kernel["theoretical_occupancy_pct"] = float(parts[-1].replace(",", ""))
        except (ValueError, IndexError):
            pass


def _extract_speedup(kernel: dict, stripped: str) -> None:
    """Extract estimated speedup from recommendation line."""
    import re
    assert kernel is not None
    
    for pattern in [r"Est\. Speedup:\s*([\d.]+)%", r"Est\. Local Speedup:\s*([\d.]+)%"]:
        match = re.search(pattern, stripped)
        if match:
            try:
                speedup = float(match.group(1))
                if speedup > kernel["estimated_speedup_pct"]:
                    kernel["estimated_speedup_pct"] = speedup
            except ValueError:
                pass


def _parse_ncu_output(session_output: str, details_output: str) -> dict:
    """Parse NCU session and details output into structured data."""
    import re
    
    assert isinstance(session_output, str)
    assert isinstance(details_output, str)

    summary: dict = {
        "gpu": _parse_gpu_from_session(session_output) if session_output else "Unknown",
        "kernels": [],
        "recommendations": [],
    }

    if not details_output:
        return summary
        
    lines = details_output.split("\n")
    current_kernel: dict | None = None
    current_section: str | None = None
    in_recommendation = False
    recommendation_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect kernel header
        if line.startswith("  ") and not line.startswith("    ") and "Context" in line and "Device" in line:
            match = re.match(r"^  (.+?)\s+\(\d+,\s*\d+,\s*\d+\)x\(\d+,\s*\d+,\s*\d+\)", line)
            if match:
                current_kernel = _create_kernel_entry(match.group(1).strip())
                summary["kernels"].append(current_kernel)

        # Detect section headers
        if stripped.startswith("Section:"):
            current_section = stripped.replace("Section:", "").strip()

        # Parse metrics from table rows
        if current_kernel and "          " in line:
            parts = line.split()
            if len(parts) >= 2:
                _parse_metric_line(current_kernel, stripped, parts, current_section)

        # Parse recommendations (OPT and INF markers)
        if stripped.startswith("OPT") or stripped.startswith("INF"):
            in_recommendation = True
            recommendation_lines = [stripped]
            if current_kernel:
                _extract_speedup(current_kernel, stripped)
        elif in_recommendation:
            if line.startswith("          ") and stripped:
                recommendation_lines.append(stripped)
            elif stripped.startswith("Section:") or stripped.startswith("---") or (stripped and not line.startswith(" ")):
                if recommendation_lines:
                    full_rec = " ".join(recommendation_lines)
                    if full_rec not in summary["recommendations"]:
                        summary["recommendations"].append(full_rec)
                    if current_kernel and full_rec not in current_kernel["recommendations"]:
                        current_kernel["recommendations"].append(full_rec)
                in_recommendation = False
                recommendation_lines = []

    # Capture last recommendation if any
    if recommendation_lines:
        full_rec = " ".join(recommendation_lines)
        if full_rec not in summary["recommendations"]:
            summary["recommendations"].append(full_rec)
        if current_kernel and full_rec not in current_kernel["recommendations"]:
            current_kernel["recommendations"].append(full_rec)

    return summary


def _classify_underfill(
    waves_per_sm: float, grid_size: int, num_sms: int
) -> tuple[str | None, str | None]:
    """Classify underfill type and severity based on metrics.
    
    Returns:
        (underfill_type, severity) where:
        - underfill_type: "launch" | "resource" | None
        - severity: "severe" | "moderate" | None
    """
    assert waves_per_sm >= 0, f"waves_per_sm must be non-negative, got {waves_per_sm}"
    assert grid_size >= 0, f"grid_size must be non-negative, got {grid_size}"
    assert num_sms > 0, f"num_sms must be positive, got {num_sms}"
    
    is_grid_small = grid_size > 0 and grid_size < num_sms
    
    if waves_per_sm > 0 and waves_per_sm < 1.0:
        return ("launch" if is_grid_small else "resource", "severe")
    if waves_per_sm > 0 and waves_per_sm < 2.0:
        return ("launch" if is_grid_small else "resource", "moderate")
    if is_grid_small:
        return ("launch", "severe")
    return (None, None)


def _classify_occupancy(
    achieved_occ: float, theoretical_occ: float
) -> tuple[bool, str | None]:
    """Classify occupancy issue.
    
    Returns:
        (is_low_occupancy, analysis_type) where:
        - is_low_occupancy: True if achieved < 50%
        - analysis_type: "runtime_issue" | "resource_limited" | None
    """
    assert achieved_occ >= 0, f"achieved_occ must be non-negative, got {achieved_occ}"
    assert theoretical_occ >= 0, f"theoretical_occ must be non-negative, got {theoretical_occ}"
    
    if achieved_occ <= 0 or achieved_occ >= 50:
        return (False, None)
    
    if theoretical_occ <= 0:
        return (True, None)
    
    occ_gap = theoretical_occ - achieved_occ
    if theoretical_occ >= 50 and occ_gap > 20:
        return (True, "runtime_issue")
    if theoretical_occ < 50:
        return (True, "resource_limited")
    return (True, None)


def _classify_throughput(
    memory_tp: float, compute_tp: float, achieved_occ: float
) -> tuple[bool, bool, bool]:
    """Classify throughput observations.
    
    Returns:
        (has_high_memory, has_high_compute, has_both_low)
    """
    assert memory_tp >= 0, f"memory_tp must be non-negative, got {memory_tp}"
    assert compute_tp >= 0, f"compute_tp must be non-negative, got {compute_tp}"
    assert achieved_occ >= 0, f"achieved_occ must be non-negative, got {achieved_occ}"
    
    has_high_memory = memory_tp > 60
    has_high_compute = compute_tp > 60
    has_both_low = memory_tp < 30 and compute_tp < 30 and achieved_occ >= 50
    return (has_high_memory, has_high_compute, has_both_low)


def _format_underfill_diagnosis(
    underfill_type: str,
    underfill_severity: str,
    waves_per_sm: float,
    grid_size: int,
    num_sms: int,
    achieved_occ: float,
    theoretical_occ: float,
    compute_tp: float,
    memory_tp: float,
    estimated_speedup: float,
) -> list[str]:
    """Format diagnosis lines for underfill issues. Returns early from _generate_diagnosis."""
    assert underfill_type in ("launch", "resource")
    assert underfill_severity in ("severe", "moderate")
    
    severity_label = "UNDERFILL" if underfill_severity == "severe" else "LIMITED CONCURRENCY"
    blocks_per_sm = grid_size / num_sms if grid_size > 0 else 0
    
    lines = [f"**Primary Issue: {severity_label}**"]
    
    if waves_per_sm > 0:
        lines.append(f"- Waves per SM: {waves_per_sm:.2f} (often benefits from >2 to hide latency)")
    if grid_size > 0:
        lines.append(f"- Grid: {grid_size} blocks for {num_sms} SMs ({blocks_per_sm:.2f} blocks/SM)")
    lines.append("- ⚠️ Compute/memory throughput % not reliable for global bottleneck; underfill dominates")
    lines.append("")
    
    if underfill_type == "launch":
        lines.extend([
            "**Type: LAUNCH-LIMITED** (grid smaller than SM count)",
            "",
            "**What WON'T help:**",
            "- Reducing registers/shared memory (can't create more blocks than launched)",
            "",
            "**What MAY help:**",
            "- Increase batch size or problem dimensions",
            "- Split work into more blocks (e.g., tile over batch/head/rows; sequence tiling only if algorithm permits)",
            "- Use persistent CTAs / work queue: launch ~k×SM blocks that pull tasks",
            "- If inherently sequential, focus on per-block latency optimization",
        ])
    else:
        lines.extend([
            "**Type: RESOURCE-LIMITED** (grid is adequate, but few blocks fit per SM)",
            "",
            "**What MAY help:**",
            "- Reduce registers per thread (__launch_bounds__, fewer local vars)",
            "- Reduce shared memory per block (smaller tiles, multi-stage)",
            "- Reduce block size to fit more blocks per SM",
            "- Check 'Block Limit' in NCU Occupancy section for the limiter",
            "",
            "**Note:** If kernel is very short, waves/SM may be less indicative.",
            "Confirm with Occupancy 'Block Limit' and duration metrics.",
        ])
    
    lines.extend(["", "**Raw metrics (interpret with caution due to underfill):**"])
    lines.append(f"- Achieved Occupancy: {achieved_occ:.1f}%")
    if theoretical_occ > 0:
        lines.append(f"- Theoretical Occupancy: {theoretical_occ:.1f}%")
    lines.append(f"- Compute Throughput: {compute_tp:.1f}%")
    lines.append(f"- Memory Throughput: {memory_tp:.1f}%")
    if estimated_speedup > 0:
        lines.append(f"- NCU Est. Speedup potential: {estimated_speedup:.1f}%")
    lines.append("")
    return lines


def _format_occupancy_diagnosis(
    achieved_occ: float,
    theoretical_occ: float,
    occupancy_analysis: str | None,
) -> list[str]:
    """Format diagnosis lines for low occupancy issues."""
    assert achieved_occ >= 0
    
    lines = ["**Observation: Low Achieved Occupancy**", f"- Achieved: {achieved_occ:.1f}%"]
    
    if theoretical_occ > 0:
        lines.append(f"- Theoretical: {theoretical_occ:.1f}%")
        
        if occupancy_analysis == "runtime_issue":
            lines.extend([
                "",
                "**Analysis: Large gap between theoretical and achieved**",
                "- Theoretical is high, so this is NOT a resource limit (regs/shmem)",
                "- Likely causes: load imbalance, barriers, short kernel duration, tail effects",
                "- Check if work is evenly distributed across blocks",
            ])
        elif occupancy_analysis == "resource_limited":
            lines.extend([
                "",
                "**Analysis: Theoretical occupancy is also low**",
                "- This IS a resource limit (registers, shared memory, or block size)",
                "- Check 'Block Limit' in NCU Occupancy section for the specific limiter",
            ])
    
    lines.extend([
        "",
        "**General suggestions:**",
        "- If register-limited: try __launch_bounds__, reduce local arrays",
        "- If shared-mem-limited: reduce tile sizes or use multi-stage",
        "- If runtime-limited: check barriers, load balance, kernel duration",
        "",
    ])
    return lines


def _format_throughput_diagnosis(
    has_high_memory: bool,
    has_high_compute: bool,
    has_both_low: bool,
    memory_tp: float,
    compute_tp: float,
) -> list[str]:
    """Format diagnosis lines for throughput observations."""
    lines: list[str] = []
    
    if has_high_memory or has_high_compute:
        lines.append("**Throughput observations:**")
        if has_high_memory:
            lines.append(f"- Memory throughput relatively high ({memory_tp:.1f}%)")
            lines.append("  - May benefit from: better caching, shared memory tiling, coalesced access")
        if has_high_compute:
            lines.append(f"- Compute throughput relatively high ({compute_tp:.1f}%)")
            lines.append("  - May benefit from: reduced instruction count, better ILP")
            lines.append("  - Check which pipeline is saturated (FP32/FP16/INT/SFU/TensorCore) if available")
        lines.append("")
    elif has_both_low:
        lines.extend([
            "**Observation: Both % of peak are low**",
            "- Likely: latency-bound, sync-bound, dependency stalls, or non-peak pipelines",
            "- This can happen with: integer-heavy, SFU-heavy, or control-flow-heavy kernels",
            "- Check instruction mix / pipeline utilization metrics if available",
            "- Check NCU stall reasons (smsp__warp_issue_stalled_*) for more detail",
            "",
        ])
    
    return lines


def _generate_diagnosis(kernel: dict, num_sms: int = 148) -> list[str]:
    """Generate actionable diagnosis based on kernel metrics.
    
    Uses a prioritized decision order:
    1. Underfill check (waves_per_sm < 2 OR grid_size < num_sms) - overrides other diagnoses
    2. Occupancy limiters (theoretical vs achieved gap analysis)
    3. General observations (avoid strong "bound" labels without stall data)
    """
    assert isinstance(kernel, dict), "kernel must be a dict"
    assert num_sms > 0, f"num_sms must be positive, got {num_sms}"
    
    # Extract metrics (single assignments)
    grid_size = kernel.get('grid_size', 0)
    achieved_occ = kernel.get('achieved_occupancy_pct', 0)
    theoretical_occ = kernel.get('theoretical_occupancy_pct', 0)
    compute_tp = kernel.get('compute_throughput_pct', 0)
    memory_tp = kernel.get('memory_throughput_pct', 0)
    estimated_speedup = kernel.get('estimated_speedup_pct', 0)
    waves_per_sm = kernel.get('waves_per_sm', 0)
    
    # Skip if we don't have enough data
    if grid_size == 0 and achieved_occ == 0 and waves_per_sm == 0:
        return []
    
    # Compute all classifications upfront (single assignments)
    underfill_type, underfill_severity = _classify_underfill(waves_per_sm, grid_size, num_sms)
    is_low_occupancy, occupancy_analysis = _classify_occupancy(achieved_occ, theoretical_occ)
    has_high_memory, has_high_compute, has_both_low = _classify_throughput(memory_tp, compute_tp, achieved_occ)
    
    # Derived flags (single assignments)
    has_underfill = underfill_type is not None
    has_throughput_obs = has_high_memory or has_high_compute or has_both_low
    
    # Build output
    lines = ["#### 🔍 Diagnosis", ""]
    
    # PRIORITY 1: Underfill (overrides other diagnoses)
    if has_underfill:
        lines.extend(_format_underfill_diagnosis(
            underfill_type, underfill_severity, waves_per_sm, grid_size, num_sms,
            achieved_occ, theoretical_occ, compute_tp, memory_tp, estimated_speedup,
        ))
        return lines
    
    # PRIORITY 2: Low occupancy (when NOT caused by underfill)
    if is_low_occupancy:
        lines.extend(_format_occupancy_diagnosis(achieved_occ, theoretical_occ, occupancy_analysis))
    
    # PRIORITY 3: Throughput observations
    lines.extend(_format_throughput_diagnosis(has_high_memory, has_high_compute, has_both_low, memory_tp, compute_tp))
    
    # Show NCU's own recommendations if present
    if estimated_speedup > 0:
        lines.extend([f"**NCU estimated speedup potential: {estimated_speedup:.1f}%**",
                      "- See NCU recommendations below for specific suggestions", ""])
    
    # No major issues detected
    if not (has_underfill or is_low_occupancy or has_throughput_obs):
        lines.extend(["**Status: No obvious bottleneck detected**",
                      f"- Occupancy: {achieved_occ:.1f}%, Compute: {compute_tp:.1f}%, Memory: {memory_tp:.1f}%",
                      "- Consider profiling with --set full for stall breakdown",
                      "- Or the kernel may already be well-optimized for its workload", ""])
    
    return lines


def _generate_text_output(filename: str, summary: dict) -> str:
    """Generate human-readable markdown text from summary."""
    timestamp = datetime.now().isoformat()
    gpu_name = summary.get('gpu', 'Unknown')
    num_sms = _get_sm_count_for_gpu(gpu_name)

    lines = [
        "# NCU Profiling Analysis",
        f"Source: {filename}",
        f"Generated: {timestamp}",
        "",
        "## GPU Information",
        f"- Device: {gpu_name}",
        "",
        "## Kernel Summary",
        "",
    ]

    for kernel in summary.get("kernels", []):
        lines.extend([
            f"### {kernel['name']}",
            f"- Duration: {kernel.get('duration_us', 0):.2f} us ({kernel.get('duration_ms', 0):.3f} ms)",
            f"- Achieved Occupancy: {kernel.get('achieved_occupancy_pct', 0):.1f}%",
            f"- Compute (SM) Throughput: {kernel.get('compute_throughput_pct', 0):.1f}%",
            f"- Memory Throughput: {kernel.get('memory_throughput_pct', 0):.1f}%",
            f"- Registers/Thread: {kernel.get('registers_per_thread', 0)}",
            f"- Block Size: {kernel.get('block_size', 0)}",
            f"- Grid Size: {kernel.get('grid_size', 0)}",
            "",
        ])
        
        # Add actionable diagnosis
        diagnosis = _generate_diagnosis(kernel, num_sms=num_sms)
        if diagnosis:
            lines.extend(diagnosis)

    if summary.get("recommendations"):
        lines.extend([
            "## NCU Recommendations",
            "",
        ])
        for i, rec in enumerate(summary["recommendations"], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    return "\n".join(lines)


def _analyze_local(
    filepath: Path,
    ncu_path: str,
    output_dir: Path | None = None,
    json_output: bool = False,
) -> str:
    """Analyze NCU profile locally using installed NCU."""
    # Run NCU to get session and details
    try:
        session_result = subprocess.run(
            [ncu_path, "--import", str(filepath), "--page", "session"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        details_result = subprocess.run(
            [ncu_path, "--import", str(filepath), "--page", "details"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("NCU command timed out (120s limit)") from e

    # Parse the outputs
    summary = _parse_ncu_output(session_result.stdout, details_result.stdout)

    # Save to output directory if specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        txt_filename = f"ncu_analysis_{filepath.stem}_{timestamp}.txt"
        txt_path = output_dir / txt_filename
        txt_path.write_text(_generate_text_output(filepath.name, summary))

    if json_output:
        return json.dumps(summary, indent=2)
    else:
        return _generate_text_output(filepath.name, summary)


def _analyze_remote_direct(
    filepath: Path,
    target_name: str,
    json_output: bool = False,
) -> str:
    """Analyze NCU profile remotely via direct SSH to target.

    Uploads the .ncu-rep file and runs NCU analysis on the target machine.
    """
    import sys
    import tempfile

    from .gpu_run import push_directory, run_command_capture
    from .targets import load_target

    # Load target
    try:
        target = load_target(target_name)
    except FileNotFoundError as e:
        raise RuntimeError(f"Target not found: {target_name}") from e

    # Create temp directory with just the .ncu-rep file
    # Use a unique name based on the file
    workspace_name = f"ncu_analyze_{filepath.stem}"

    with tempfile.TemporaryDirectory() as tmpdir:
        import shutil

        # Create a directory with the workspace name
        tmp_path = Path(tmpdir) / workspace_name
        tmp_path.mkdir()
        shutil.copy(filepath, tmp_path / filepath.name)

        # Push the file
        print(f"Uploading {filepath.name} to {target_name}...", file=sys.stderr)
        push_directory(tmp_path, target)

    # Run NCU commands - workspace_name is used (not full path)
    ncu_cmd = f"/usr/local/cuda/bin/ncu --import {filepath.name} --page session && echo '---NCU_SEPARATOR---' && /usr/local/cuda/bin/ncu --import {filepath.name} --page details"

    print("Running NCU analysis...", file=sys.stderr)
    exit_code, output = run_command_capture(ncu_cmd, workspace_name, target)

    if exit_code != 0:
        raise RuntimeError(f"NCU command failed with exit code {exit_code}")

    # Split session and details output
    if "---NCU_SEPARATOR---" in output:
        parts = output.split("---NCU_SEPARATOR---")
        session_output = parts[0].strip()
        details_output = parts[1].strip() if len(parts) > 1 else ""
    else:
        session_output = ""
        details_output = output

    # Parse the outputs
    summary = _parse_ncu_output(session_output, details_output)

    if json_output:
        return json.dumps(summary, indent=2)
    else:
        return _generate_text_output(filepath.name, summary)


def _analyze_remote_api(
    filepath: Path,
    json_output: bool = False,
    include_source: bool = False,
) -> str:
    """Analyze NCU profile remotely via wafer-api.

    Uploads the .ncu-rep file and runs NCU analysis on a remote GPU machine.

    Args:
        filepath: Path to .ncu-rep file
        json_output: Return JSON instead of formatted text
        include_source: If True, fetch source correlation (SASS) for each kernel
    """
    import sys

    import httpx

    from .api_client import get_api_url
    from .auth import get_auth_headers

    api_url = get_api_url()
    headers = get_auth_headers()

    # Use the dedicated NCU analyze endpoint (binary upload)
    print(f"Uploading {filepath.name} for analysis...", file=sys.stderr)

    try:
        with httpx.Client(timeout=300.0, headers=headers) as client:
            # Upload via binary endpoint for efficiency
            file_content = filepath.read_bytes()
            response = client.post(
                f"{api_url}/v1/ncu/reports/binary",
                content=file_content,
                headers={
                    **headers,
                    "Content-Type": "application/octet-stream",
                    "X-Filename": filepath.name,
                },
            )
            response.raise_for_status()
            upload_result = response.json()
            # API returns camelCase "reportId", normalize to snake_case
            report_id = upload_result.get("report_id") or upload_result.get("reportId")

            if not report_id:
                raise RuntimeError("No report_id returned from upload")

            print(f"Report ID: {report_id}", file=sys.stderr)

            # Get kernel list
            print("Fetching kernel data...", file=sys.stderr)
            kernels_response = client.get(f"{api_url}/v1/ncu/reports/{report_id}/kernels")
            kernels_response.raise_for_status()
            kernels_data = kernels_response.json()
            # API may return {"kernels": [...]} or just [...]
            kernels = (
                kernels_data.get("kernels", kernels_data)
                if isinstance(kernels_data, dict)
                else kernels_data
            )

            result: dict = {
                "report_id": report_id,
                "gpu": upload_result.get("gpu", "Unknown"),
                "kernels": kernels,
            }

            # Fetch source correlation if requested
            if include_source:
                print("Fetching source correlation (SASS)...", file=sys.stderr)
                source_data = []
                for kernel in kernels:
                    kernel_id = kernel.get("id") or kernel.get("kernel_id")
                    if not kernel_id:
                        continue

                    try:
                        source_response = client.get(
                            f"{api_url}/v1/ncu/reports/{report_id}/kernels/{kernel_id}/source",
                            params={"view": "sass"},
                            timeout=180.0,  # Source extraction can be slow
                        )
                        source_response.raise_for_status()
                        source_info = source_response.json()
                        source_data.append({
                            "kernel_id": kernel_id,
                            "kernel_name": kernel.get("name", "Unknown"),
                            "source": source_info,
                        })
                    except httpx.HTTPStatusError as e:
                        print(
                            f"Warning: Failed to get source for kernel {kernel_id}: {e}",
                            file=sys.stderr,
                        )

                result["source_correlation"] = source_data

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps(result, indent=2)
    else:
        return _generate_ncu_api_text_output(filepath.name, result)


def _generate_ncu_api_text_output(filename: str, result: dict) -> str:
    """Generate human-readable text from NCU API result."""
    timestamp = datetime.now().isoformat()
    gpu_name = result.get('gpu', 'Unknown')
    num_sms = _get_sm_count_for_gpu(gpu_name)

    lines = [
        "# NCU Profiling Analysis",
        f"Source: {filename}",
        f"Generated: {timestamp}",
        f"Report ID: {result.get('report_id', 'N/A')}",
        "",
        "## GPU Information",
        f"- Device: {gpu_name}",
        "",
        "## Kernel Summary",
        "",
    ]

    for kernel in result.get("kernels", []):
        name = kernel.get("name", kernel.get("function_name", "Unknown"))
        lines.extend([
            f"### {name}",
            f"- Duration: {kernel.get('duration_us', 0):.2f} us",
            f"- Achieved Occupancy: {kernel.get('achieved_occupancy_pct', kernel.get('occupancy', 0)):.1f}%",
            f"- Compute Throughput: {kernel.get('compute_throughput_pct', kernel.get('sm_throughput', 0)):.1f}%",
            f"- Memory Throughput: {kernel.get('memory_throughput_pct', kernel.get('mem_throughput', 0)):.1f}%",
            f"- Grid Size: {kernel.get('grid_size', 0)}",
            f"- Block Size: {kernel.get('block_size', 0)}",
            "",
        ])
        
        # Add actionable diagnosis (normalize field names from API)
        normalized_kernel = {
            'grid_size': kernel.get('grid_size', 0),
            'block_size': kernel.get('block_size', 0),
            'achieved_occupancy_pct': kernel.get('achieved_occupancy_pct', kernel.get('occupancy', 0)),
            'compute_throughput_pct': kernel.get('compute_throughput_pct', kernel.get('sm_throughput', 0)),
            'memory_throughput_pct': kernel.get('memory_throughput_pct', kernel.get('mem_throughput', 0)),
            'registers_per_thread': kernel.get('registers_per_thread', 0),
        }
        diagnosis = _generate_diagnosis(normalized_kernel, num_sms=num_sms)
        if diagnosis:
            lines.extend(diagnosis)

    # Add source correlation summary if present
    source_data = result.get("source_correlation", [])
    if source_data:
        lines.extend([
            "## Source Correlation",
            "",
        ])
        for sc in source_data:
            kernel_name = sc.get("kernel_name", "Unknown")
            source = sc.get("source", {})
            instruction_count = len(source.get("instructions", []))
            region_count = len(source.get("regions", []))
            lines.extend([
                f"### {kernel_name}",
                f"- View: {source.get('view', 'N/A')}",
                f"- Instructions: {instruction_count}",
                f"- Regions: {region_count}",
                "",
            ])

    return "\n".join(lines)


def analyze_ncu_profile(
    filepath: Path,
    output_dir: Path | None = None,
    json_output: bool = False,
    remote: bool | None = None,
    target: str | None = None,
    include_source: bool = False,
) -> str:
    """Analyze an NCU profile file and return results.

    Args:
        filepath: Path to .ncu-rep file
        output_dir: Optional directory to save analysis files
        json_output: If True, return raw JSON; otherwise return formatted text
        remote: If True, force remote analysis via API. If False, force local.
                If None (default), auto-detect: use local if NCU available, else remote.
        target: Target name for direct SSH mode (e.g., "vultr-b200"). If provided,
                uses direct SSH instead of API for remote analysis.
        include_source: If True, fetch source correlation (SASS) for each kernel.
                        Only supported with --remote (requires GPU for extraction).

    Returns:
        Analysis results as string (JSON or markdown)

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If NCU parsing fails
    """
    import sys

    ncu_path = _find_ncu()

    # include_source requires remote API (needs GPU for SASS extraction)
    if include_source and not remote and target is None:
        print("Note: --include-source requires remote analysis. Using --remote.", file=sys.stderr)
        remote = True

    # If target is provided, use direct SSH mode
    if target is not None:
        if include_source:
            print(
                "Warning: --include-source not supported with --target. Ignoring.", file=sys.stderr
            )
        if output_dir:
            print("Warning: --output-dir not supported for remote analysis", file=sys.stderr)
        return _analyze_remote_direct(filepath, target, json_output)

    # Determine whether to use local or remote
    use_remote = remote
    if use_remote is None:
        # Auto-detect: use remote if NCU not available locally
        use_remote = ncu_path is None

    if use_remote:
        # Note: output_dir not supported for remote (would need to download results)
        if output_dir:
            print("Warning: --output-dir not supported for remote analysis", file=sys.stderr)
        return _analyze_remote_api(filepath, json_output, include_source=include_source)
    else:
        if include_source:
            print(
                "Warning: --include-source only supported with --remote. Ignoring.", file=sys.stderr
            )
        if ncu_path is None:
            install_cmd = _get_install_command()
            raise FileNotFoundError(f"NCU not installed. Install with: {install_cmd}")
        return _analyze_local(filepath, ncu_path, output_dir, json_output)
