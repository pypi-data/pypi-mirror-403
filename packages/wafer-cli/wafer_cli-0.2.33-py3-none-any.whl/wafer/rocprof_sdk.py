"""ROCprof-SDK - CLI wrapper for rocprofv3 profiling tool.

This module provides the CLI wrapper for the `wafer rocprof-sdk` command.
It supports multiple subcommands:
- check: Check rocprofv3 installation
- profile: Run profiling on a command
- analyze: Analyze profiling output files

This follows the design in Wafer-391: ROCprofiler Tools Architecture.
Architecture pattern matches rocprof_compute.py.
"""

import json
import shlex
import sys
from dataclasses import asdict
from pathlib import Path


def print_usage() -> None:
    """Print CLI usage information."""
    print("Usage: wafer rocprof-sdk <subcommand> [options]", file=sys.stderr)
    print("", file=sys.stderr)
    print("Subcommands:", file=sys.stderr)
    print("  check              Check rocprofv3 installation status", file=sys.stderr)
    print("  list-counters      List available hardware counters for your GPU", file=sys.stderr)
    print("  profile COMMAND    Profile a command with rocprofv3", file=sys.stderr)
    print("  analyze FILE       Analyze profiling output file", file=sys.stderr)
    print("", file=sys.stderr)
    print("Profile Options:", file=sys.stderr)
    print(
        "  --output-dir DIR   Output directory for results (default: current directory)",
        file=sys.stderr,
    )
    print(
        "  --format FORMAT    Output format: csv, json, rocpd, pftrace, otf2 (default: csv)",
        file=sys.stderr,
    )
    print(
        "  --counters C1,C2   Hardware counters to collect (comma-separated)",
        file=sys.stderr,
    )
    print("  --json             Output result as JSON", file=sys.stderr)
    print("", file=sys.stderr)
    print("Analyze Options:", file=sys.stderr)
    print("  --json             Output result as JSON", file=sys.stderr)
    print("", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  wafer rocprof-sdk check", file=sys.stderr)
    print("  wafer rocprof-sdk list-counters", file=sys.stderr)
    print("  wafer rocprof-sdk profile './my_app --arg'", file=sys.stderr)
    print(
        "  wafer rocprof-sdk profile './kernel' --format csv --output-dir ./results",
        file=sys.stderr,
    )
    print(
        "  wafer rocprof-sdk profile './kernel' --counters SQ_WAVES,L2_CACHE_HITS",
        file=sys.stderr,
    )
    print("  wafer rocprof-sdk analyze stats_kernel.csv", file=sys.stderr)
    print("  wafer rocprof-sdk analyze results.json --json", file=sys.stderr)


def check_command(json_output: bool = False) -> str:
    """CLI wrapper for checking rocprofv3 installation.

    Args:
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Status message or JSON string
    """
    from wafer_core.lib.rocprofiler.sdk import check_installation  # pragma: no cover

    result = check_installation()

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.installed:
            print("✓ rocprofv3 is installed", file=sys.stderr)
            if result.path:
                print(f"  Path: {result.path}", file=sys.stderr)
            if result.version:
                print(f"  Version: {result.version}", file=sys.stderr)
            return "rocprofv3 is installed"
        else:
            print("✗ rocprofv3 is not installed", file=sys.stderr)
            if result.install_command:
                print(f"  {result.install_command}", file=sys.stderr)
            return "rocprofv3 is not installed"


def list_counters_command() -> str:
    """CLI wrapper for listing available hardware counters.

    Returns:
        Counter list output

    Raises:
        RuntimeError: If listing fails
    """
    from wafer_core.lib.rocprofiler.sdk import list_counters  # pragma: no cover

    success, output, error = list_counters()

    if success:
        # Print the output directly to stdout
        print(output)
        return output
    else:
        print("✗ Failed to list counters", file=sys.stderr)
        print(f"  {error}", file=sys.stderr)
        raise RuntimeError(error)


def profile_command(
    command: str,
    output_dir: str | None = None,
    output_format: str = "csv",
    counters: list[str] | None = None,
    kernel_include: str | None = None,
    kernel_exclude: str | None = None,
    trace_hip_runtime: bool = False,
    trace_hip_compiler: bool = False,
    trace_hsa: bool = False,
    trace_marker: bool = False,
    trace_memory_copy: bool = False,
    json_output: bool = False,
) -> str:
    """Run rocprofv3 profiling.

    Args:
        command: Shell command to profile
        output_dir: Output directory for results
        output_format: Output format (csv, json, rocpd, pftrace)
        counters: List of hardware counters to collect
        kernel_include: Include only kernels matching this regex
        kernel_exclude: Exclude kernels matching this regex
        trace_hip_runtime: Enable HIP runtime API tracing
        trace_hip_compiler: Enable HIP compiler code tracing
        trace_hsa: Enable HSA API tracing
        trace_marker: Enable ROCTx marker tracing
        trace_memory_copy: Enable memory copy tracing
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Success message or JSON string

    Raises:
        RuntimeError: If profiling fails
    """
    from wafer_core.lib.rocprofiler.sdk import run_profile  # pragma: no cover

    # Parse command string into list
    cmd_list = shlex.split(command)

    result = run_profile(
        command=cmd_list,
        output_dir=Path(output_dir) if output_dir else None,
        output_format=output_format,
        counters=counters,
        kernel_include_regex=kernel_include,
        kernel_exclude_regex=kernel_exclude,
        trace_hip_runtime=trace_hip_runtime,
        trace_hip_compiler=trace_hip_compiler,
        trace_hsa=trace_hsa,
        trace_marker=trace_marker,
        trace_memory_copy=trace_memory_copy,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Profiling completed successfully", file=sys.stderr)
            if result.output_files:
                print("  Output files:", file=sys.stderr)
                for f in result.output_files:
                    print(f"    - {f}", file=sys.stderr)
            if result.stdout:
                print("", file=sys.stderr)
                print("Output:", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
            return "Profiling completed"
        else:
            print("✗ Profiling failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            if result.stderr:
                print("  stderr:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            raise RuntimeError(result.error or "Profiling failed")


def analyze_command(
    file_path: str,
    json_output: bool = False,
) -> str:
    """Analyze rocprofiler output file.

    Args:
        file_path: Path to output file (CSV, JSON, or rocpd database)
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Analysis summary or JSON string

    Raises:
        RuntimeError: If analysis fails
    """
    from wafer_core.lib.rocprofiler.sdk import analyze_file  # pragma: no cover

    result = analyze_file(Path(file_path))

    if json_output:
        result_dict = asdict(result)
        # Convert KernelMetrics objects to dicts
        if result.kernels:
            result_dict["kernels"] = [asdict(k) for k in result.kernels]
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Analysis completed", file=sys.stderr)
            print(f"  Format: {result.file_format}", file=sys.stderr)

            if result.summary:
                print(
                    f"  Kernels: {result.summary.get('total_kernels', 0)}",
                    file=sys.stderr,
                )
                total_ms = result.summary.get("total_duration_ms", 0)
                print(f"  Total Duration: {total_ms:.3f} ms", file=sys.stderr)
                avg_ms = result.summary.get("avg_duration_ms", 0)
                print(f"  Avg Duration: {avg_ms:.3f} ms", file=sys.stderr)

            print("", file=sys.stderr)

            # Print kernel table
            if result.kernels:
                print("Kernel Summary:", file=sys.stderr)
                print(
                    f"{'Name':<40} {'Duration (ms)':>13} {'Grid':>12} {'Block':>12} {'SGPRs':>7} {'VGPRs':>7} {'LDS (B)':>9}",
                    file=sys.stderr,
                )
                print("-" * 110, file=sys.stderr)

                for k in result.kernels[:20]:  # Limit to first 20
                    duration_ms = (k.duration_ns or 0) / 1_000_000
                    grid = k.grid_size or "-"
                    block = k.block_size or "-"
                    sgprs = str(k.sgprs) if k.sgprs is not None else "-"
                    vgprs = str(k.vgprs) if k.vgprs is not None else "-"
                    lds = str(k.lds_per_workgroup) if k.lds_per_workgroup is not None else "-"
                    # Truncate long kernel names
                    name = k.name[:37] + "..." if len(k.name) > 40 else k.name
                    print(
                        f"{name:<40} {duration_ms:>13.3f} {grid:>12} {block:>12} {sgprs:>7} {vgprs:>7} {lds:>9}",
                        file=sys.stderr,
                    )

                if len(result.kernels) > 20:
                    print(
                        f"... and {len(result.kernels) - 20} more kernels",
                        file=sys.stderr,
                    )

            return "Analysis completed"
        else:
            print("✗ Analysis failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            raise RuntimeError(result.error or "Analysis failed")
