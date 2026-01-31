"""TraceLens CLI wrapper.

Provides human-readable CLI interface for TraceLens operations.
This follows the same pattern as rocprof_sdk.py and other CLI wrappers.
"""

import json
import sys
from dataclasses import asdict


def print_usage() -> None:
    """Print CLI usage information."""
    print("Usage: wafer tracelens <subcommand> [options]", file=sys.stderr)
    print("", file=sys.stderr)
    print("Subcommands:", file=sys.stderr)
    print("  check              Check TraceLens installation status", file=sys.stderr)
    print("  report TRACE       Generate performance report from trace file", file=sys.stderr)
    print("  compare A B        Compare two performance reports", file=sys.stderr)
    print("  collective DIR     Generate multi-rank collective report", file=sys.stderr)
    print("", file=sys.stderr)
    print("Report Options:", file=sys.stderr)
    print("  --output PATH      Output file path", file=sys.stderr)
    print("  --format FORMAT    Trace format: auto, pytorch, rocprof, jax", file=sys.stderr)
    print("  --short-kernel     Include short kernel analysis", file=sys.stderr)
    print("  --kernel-details   Include detailed kernel breakdown", file=sys.stderr)
    print("  --json             Output result as JSON", file=sys.stderr)
    print("", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  wafer tracelens check", file=sys.stderr)
    print("  wafer tracelens report trace.json", file=sys.stderr)
    print("  wafer tracelens report trace.json --format pytorch --kernel-details", file=sys.stderr)
    print("  wafer tracelens compare baseline.xlsx candidate.xlsx", file=sys.stderr)
    print("  wafer tracelens collective ./traces --world-size 8", file=sys.stderr)


def check_command(json_output: bool = False) -> str:
    """CLI wrapper for checking TraceLens installation.
    
    Args:
        json_output: If True, return JSON; otherwise print human-readable
        
    Returns:
        Status message or JSON string
    """
    from wafer_core.lib.tracelens import check_installation

    result = check_installation()

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.installed:
            print("✓ TraceLens is installed", file=sys.stderr)
            if result.version:
                print(f"  Version: {result.version}", file=sys.stderr)
            if result.commands_available:
                print("  Available commands:", file=sys.stderr)
                for cmd in result.commands_available:
                    print(f"    - {cmd}", file=sys.stderr)
            return "TraceLens is installed"
        else:
            print("✗ TraceLens is not installed", file=sys.stderr)
            if result.install_command:
                print(f"  Install: {result.install_command}", file=sys.stderr)
            return "TraceLens is not installed"


def report_command(
    trace_path: str,
    output_path: str | None = None,
    trace_format: str = "auto",
    short_kernel: bool = False,
    kernel_details: bool = False,
    json_output: bool = False,
) -> str:
    """CLI wrapper for generating performance report.
    
    Args:
        trace_path: Path to trace file
        output_path: Optional output path for Excel report
        trace_format: Trace format (auto, pytorch, rocprof, jax)
        short_kernel: Include short kernel analysis
        kernel_details: Include detailed kernel breakdown
        json_output: If True, return JSON; otherwise print human-readable
        
    Returns:
        Success message or JSON string
        
    Raises:
        RuntimeError: If report generation fails
    """
    from wafer_core.lib.tracelens import generate_perf_report
    from wafer_core.lib.tracelens.types import TraceFormat

    format_map = {
        "auto": TraceFormat.AUTO,
        "pytorch": TraceFormat.PYTORCH,
        "rocprof": TraceFormat.ROCPROF,
        "jax": TraceFormat.JAX,
    }

    result = generate_perf_report(
        trace_path=trace_path,
        output_path=output_path,
        trace_format=format_map.get(trace_format, TraceFormat.AUTO),
        short_kernel_study=short_kernel,
        kernel_details=kernel_details,
    )

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.success:
            print("✓ Report generated successfully", file=sys.stderr)
            print(f"  Output: {result.output_path}", file=sys.stderr)
            print(f"  Format: {result.trace_format}", file=sys.stderr)
            return "Report generated"
        else:
            print("✗ Report generation failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            if result.stderr:
                print("  stderr:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            raise RuntimeError(result.error or "Report generation failed")


def compare_command(
    baseline_path: str,
    candidate_path: str,
    output_path: str | None = None,
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
    json_output: bool = False,
) -> str:
    """CLI wrapper for comparing two performance reports.
    
    Args:
        baseline_path: Path to baseline Excel report
        candidate_path: Path to candidate Excel report
        output_path: Optional output path for comparison file
        baseline_name: Display name for baseline
        candidate_name: Display name for candidate
        json_output: If True, return JSON; otherwise print human-readable
        
    Returns:
        Success message or JSON string
        
    Raises:
        RuntimeError: If comparison fails
    """
    from wafer_core.lib.tracelens import compare_reports

    result = compare_reports(
        baseline_path=baseline_path,
        candidate_path=candidate_path,
        output_path=output_path,
        baseline_name=baseline_name,
        candidate_name=candidate_name,
    )

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.success:
            print("✓ Comparison complete", file=sys.stderr)
            print(f"  Output: {result.output_path}", file=sys.stderr)
            return "Comparison complete"
        else:
            print("✗ Comparison failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            raise RuntimeError(result.error or "Comparison failed")


def collective_command(
    trace_dir: str,
    world_size: int,
    output_path: str | None = None,
    json_output: bool = False,
) -> str:
    """CLI wrapper for generating multi-rank collective report.
    
    Args:
        trace_dir: Directory containing trace files for all ranks
        world_size: Number of ranks (GPUs)
        output_path: Optional output path for report
        json_output: If True, return JSON; otherwise print human-readable
        
    Returns:
        Success message or JSON string
        
    Raises:
        RuntimeError: If report generation fails
    """
    from wafer_core.lib.tracelens import generate_collective_report

    result = generate_collective_report(
        trace_dir=trace_dir,
        world_size=world_size,
        output_path=output_path,
    )

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.success:
            print("✓ Collective report generated", file=sys.stderr)
            print(f"  World size: {result.world_size}", file=sys.stderr)
            if result.output_path:
                print(f"  Output: {result.output_path}", file=sys.stderr)
            return "Collective report generated"
        else:
            print("✗ Collective report failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            raise RuntimeError(result.error or "Collective report failed")
