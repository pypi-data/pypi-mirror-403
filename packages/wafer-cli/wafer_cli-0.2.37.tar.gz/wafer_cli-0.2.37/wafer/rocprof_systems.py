"""ROCprof-Systems - CLI wrapper for rocprof-sys tools.

This module provides the CLI wrapper for the `wafer rocprof-systems` command.
It supports multiple subcommands for different rocprof-sys tools:
- check: Check rocprof-sys installation
- run: Run system profiling with rocprof-sys-run
- analyze: Analyze profiling output files

This follows the design in Wafer-391: ROCprofiler Tools Architecture.
Architecture pattern matches rocprof_sdk.py.
"""

import json
import shlex
import sys
from dataclasses import asdict
from pathlib import Path


def print_usage() -> None:
    """Print CLI usage information."""
    print(
        "Usage: wafer rocprof-systems <subcommand> [options]",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print("Subcommands:", file=sys.stderr)
    print("  check              Check rocprof-sys installation status", file=sys.stderr)
    print(
        "  run COMMAND        Profile a command with rocprof-sys-run", file=sys.stderr
    )
    print(
        "  analyze FILE       Analyze profiling output file (JSON/text)", file=sys.stderr
    )
    print("", file=sys.stderr)
    print("Run Options:", file=sys.stderr)
    print(
        "  --output-dir DIR   Output directory for results (default: current directory)",
        file=sys.stderr,
    )
    print(
        "  --trace            Generate detailed trace (Perfetto output)", file=sys.stderr
    )
    print(
        "  --profile          Generate call-stack-based profile", file=sys.stderr
    )
    print("  --flat-profile     Generate flat profile", file=sys.stderr)
    print("  --sample           Enable sampling profiling", file=sys.stderr)
    print(
        "  --host             Enable host metrics (CPU freq, memory)", file=sys.stderr
    )
    print(
        "  --device           Enable device metrics (GPU temp, memory)", file=sys.stderr
    )
    print(
        "  --wait SECONDS     Wait time before collecting data", file=sys.stderr
    )
    print(
        "  --duration SECONDS Duration of data collection", file=sys.stderr
    )
    print(
        "  --cpus CPU_IDS     Comma-separated CPU IDs to sample (e.g., 0,1,2)", file=sys.stderr
    )
    print(
        "  --gpus GPU_IDS     Comma-separated GPU IDs to sample (e.g., 0)", file=sys.stderr
    )
    print(
        "  --use-rocm         Enable ROCm backend (default: true)", file=sys.stderr
    )
    print(
        "  --use-sampling     Enable sampling backend", file=sys.stderr
    )
    print(
        "  --use-kokkosp      Enable Kokkos profiling backend", file=sys.stderr
    )
    print(
        "  --use-mpip         Enable MPI profiling backend", file=sys.stderr
    )
    print(
        "  --use-rocpd        Enable rocpd database output", file=sys.stderr
    )
    print("  --json             Output result as JSON", file=sys.stderr)
    print("", file=sys.stderr)
    print("Analyze Options:", file=sys.stderr)
    print("  --json             Output result as JSON", file=sys.stderr)
    print("", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  wafer rocprof-systems check", file=sys.stderr)
    print("  wafer rocprof-systems run './my_app --arg' --trace", file=sys.stderr)
    print(
        "  wafer rocprof-systems run './kernel' --trace --profile --output-dir ./results",
        file=sys.stderr,
    )
    print(
        "  wafer rocprof-systems run './app' --host --device --duration 10",
        file=sys.stderr,
    )
    print(
        "  wafer rocprof-systems analyze wall_clock-12345.json", file=sys.stderr
    )
    print("  wafer rocprof-systems analyze wall-clock.txt --json", file=sys.stderr)


def check_command(json_output: bool = False) -> str:
    """CLI wrapper for checking rocprof-sys installation.

    Args:
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Status message or JSON string
    """
    from wafer_core.lib.rocprofiler.systems import check_installation  # pragma: no cover

    result = check_installation()

    if json_output:
        return json.dumps(asdict(result), indent=2)
    else:
        if result.installed:
            print("✓ rocprof-sys tools are installed", file=sys.stderr)
            for tool, path in result.paths.items():
                print(f"  {tool}: {path}", file=sys.stderr)
                if tool in result.versions:
                    print(f"    Version: {result.versions[tool]}", file=sys.stderr)
            return "rocprof-sys tools are installed"
        else:
            print("✗ rocprof-sys tools are not installed", file=sys.stderr)
            if result.install_command:
                print(f"  {result.install_command}", file=sys.stderr)
            return "rocprof-sys tools are not installed"


def run_command(
    command: str,
    output_dir: str | None = None,
    trace: bool = False,
    profile: bool = False,
    flat_profile: bool = False,
    sample: bool = False,
    host: bool = False,
    device: bool = False,
    wait: float | None = None,
    duration: float | None = None,
    use_rocm: bool = True,
    use_sampling: bool = False,
    use_kokkosp: bool = False,
    use_mpip: bool = False,
    use_rocpd: bool = False,
    json_output: bool = False,
) -> str:
    """Run rocprof-sys-run system profiling.

    Args:
        command: Shell command to profile
        output_dir: Output directory for results
        trace: Generate detailed trace (Perfetto)
        profile: Generate call-stack-based profile
        flat_profile: Generate flat profile
        sample: Enable sampling profiling
        host: Enable host metrics
        device: Enable device metrics
        wait: Wait time before collecting data (seconds)
        duration: Duration of data collection (seconds)
        use_rocm: Enable ROCm backend
        use_sampling: Enable sampling backend
        use_kokkosp: Enable Kokkos profiling backend
        use_mpip: Enable MPI profiling backend
        use_rocpd: Enable rocpd database output
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Success message or JSON string

    Raises:
        RuntimeError: If profiling fails
    """
    from wafer_core.lib.rocprofiler.systems import run_systems_profile  # pragma: no cover

    # Parse command string into list
    cmd_list = shlex.split(command)

    result = run_systems_profile(
        command=cmd_list,
        output_dir=Path(output_dir) if output_dir else None,
        trace=trace,
        profile=profile,
        flat_profile=flat_profile,
        sample=sample,
        host=host,
        device=device,
        wait=wait,
        duration=duration,
        use_rocm=use_rocm,
        use_sampling=use_sampling,
        use_kokkosp=use_kokkosp,
        use_mpip=use_mpip,
        use_rocpd=use_rocpd,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ System profiling completed successfully", file=sys.stderr)
            if result.output_files:
                print("  Output files:", file=sys.stderr)
                for f in result.output_files:
                    print(f"    - {f}", file=sys.stderr)

                # Provide hints for next steps
                perfetto_files = [f for f in result.output_files if "perfetto" in f]
                if perfetto_files:
                    print(
                        "",
                        file=sys.stderr,
                    )
                    print(
                        "  Tip: Open Perfetto traces at https://ui.perfetto.dev",
                        file=sys.stderr,
                    )

            if result.stdout:
                print("", file=sys.stderr)
                print("Output:", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
            return "System profiling completed"
        else:
            print("✗ System profiling failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            if result.stderr:
                print("  stderr:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            raise RuntimeError(result.error or "System profiling failed")


def analyze_command(
    file_path: str,
    json_output: bool = False,
) -> str:
    """Analyze rocprof-sys output file.

    Args:
        file_path: Path to output file (JSON or text)
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Analysis summary or JSON string

    Raises:
        RuntimeError: If analysis fails
    """
    from wafer_core.lib.rocprofiler.systems.run.analyzer import analyze_file  # pragma: no cover

    result = analyze_file(Path(file_path))

    if json_output:
        result_dict = asdict(result)
        # Convert SystemMetrics objects to dicts
        if result.functions:
            result_dict["functions"] = [asdict(f) for f in result.functions]
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Analysis completed", file=sys.stderr)
            print(f"  Format: {result.file_format}", file=sys.stderr)

            if result.summary:
                print(
                    f"  Functions: {result.summary.get('total_functions', 0)}",
                    file=sys.stderr,
                )
                if "total_time_ms" in result.summary:
                    total_ms = result.summary.get("total_time_ms", 0)
                    print(f"  Total Time: {total_ms:.3f} ms", file=sys.stderr)
                if "total_calls" in result.summary:
                    calls = result.summary.get("total_calls", 0)
                    print(f"  Total Calls: {calls}", file=sys.stderr)

            if result.metadata:
                print("", file=sys.stderr)
                print("Metadata:", file=sys.stderr)
                if result.metadata.get("pid"):
                    print(f"  PID: {result.metadata['pid']}", file=sys.stderr)
                if result.metadata.get("user"):
                    print(f"  User: {result.metadata['user']}", file=sys.stderr)
                if result.metadata.get("working_directory"):
                    print(f"  Working Directory: {result.metadata['working_directory']}", file=sys.stderr)
                if result.metadata.get("cpu_model"):
                    print(f"  CPU: {result.metadata['cpu_model']}", file=sys.stderr)
                if result.metadata.get("rocm_version"):
                    print(f"  ROCm Version: {result.metadata['rocm_version']}", file=sys.stderr)
                if result.metadata.get("launch_date") and result.metadata.get("launch_time"):
                    print(f"  Launch: {result.metadata['launch_date']} {result.metadata['launch_time']}", file=sys.stderr)

            print("", file=sys.stderr)

            # Print function table
            if result.functions:
                print("Function Summary:", file=sys.stderr)
                print(
                    f"{'Name':<50} {'Calls':>10} {'Total (ms)':>15} {'Mean (ms)':>15}",
                    file=sys.stderr,
                )
                print("-" * 92, file=sys.stderr)

                for f in result.functions[:20]:  # Limit to first 20
                    calls = f.call_count or 0
                    total_ms = (f.total_time_ns or 0) / 1_000_000
                    mean_ms = (f.mean_time_ns or 0) / 1_000_000
                    # Truncate long function names
                    name = f.function_name[:47] + "..." if len(f.function_name) > 50 else f.function_name
                    print(
                        f"{name:<50} {calls:>10} {total_ms:>15.3f} {mean_ms:>15.3f}",
                        file=sys.stderr,
                    )

                if len(result.functions) > 20:
                    print(
                        f"... and {len(result.functions) - 20} more functions",
                        file=sys.stderr,
                    )

            return "Analysis completed"
        else:
            print("✗ Analysis failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            raise RuntimeError(result.error or "Analysis failed")


def sample_command(
    command: str,
    output_dir: str | None = None,
    frequency: int | None = None,
    trace: bool = False,
    profile: bool = False,
    flat_profile: bool = False,
    host: bool = False,
    device: bool = False,
    wait: float | None = None,
    duration: float | None = None,
    cpus: str | None = None,
    gpus: str | None = None,
    json_output: bool = False,
) -> str:
    """Run sampling profiling with rocprof-sys-sample.

    Args:
        command: Shell command to profile
        output_dir: Output directory for results
        frequency: Sampling frequency in Hz
        trace: Generate detailed trace
        profile: Generate call-stack-based profile
        flat_profile: Generate flat profile
        host: Enable host metrics
        device: Enable device metrics
        wait: Wait time before collecting data (seconds)
        duration: Duration of data collection (seconds)
        cpus: Comma-separated CPU IDs to sample (e.g., "0,1,2")
        gpus: Comma-separated GPU IDs to sample (e.g., "0")
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Success message or JSON string

    Raises:
        RuntimeError: If sampling fails
    """
    from wafer_core.lib.rocprofiler.systems import run_sampling  # pragma: no cover

    # Parse command string into list
    cmd_list = shlex.split(command)

    # Parse CPU/GPU lists
    cpu_list = [int(x.strip()) for x in cpus.split(",")] if cpus else None
    gpu_list = [int(x.strip()) for x in gpus.split(",")] if gpus else None

    result = run_sampling(
        command=cmd_list,
        output_dir=Path(output_dir) if output_dir else None,
        freq=frequency,
        trace=trace,
        profile=profile,
        flat_profile=flat_profile,
        host=host,
        device=device,
        wait=wait,
        duration=duration,
        cpus=cpu_list,
        gpus=gpu_list,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Sampling completed successfully", file=sys.stderr)
            if result.output_files:
                print("  Output files:", file=sys.stderr)
                for f in result.output_files:
                    print(f"    - {f}", file=sys.stderr)
            return "Sampling completed"
        else:
            print("✗ Sampling failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            if result.stderr:
                print("  stderr:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            raise RuntimeError(result.error or "Sampling failed")


def instrument_command(
    command: str,
    output_dir: str | None = None,
    simulate: bool = False,
    function_include: list[str] | None = None,
    function_exclude: list[str] | None = None,
    json_output: bool = False,
) -> str:
    """Run binary instrumentation with rocprof-sys-instrument.

    Args:
        command: Shell command to instrument
        output_dir: Output directory for results
        simulate: Simulate instrumentation without creating binary
        function_include: Function patterns to include
        function_exclude: Function patterns to exclude
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Success message or JSON string

    Raises:
        RuntimeError: If instrumentation fails
    """
    from wafer_core.lib.rocprofiler.systems import run_instrumentation  # pragma: no cover

    # Parse command string into list
    cmd_list = shlex.split(command)

    result = run_instrumentation(
        command=cmd_list,
        output=Path(output_dir) if output_dir else None,
        simulate=simulate,
        function_include=function_include,
        function_exclude=function_exclude,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Instrumentation completed successfully", file=sys.stderr)
            if result.output_files:
                print("  Output files:", file=sys.stderr)
                for f in result.output_files:
                    print(f"    - {f}", file=sys.stderr)
            return "Instrumentation completed"
        else:
            print("✗ Instrumentation failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            if result.stderr:
                print("  stderr:", file=sys.stderr)
                print(result.stderr, file=sys.stderr)
            raise RuntimeError(result.error or "Instrumentation failed")


def query_command(
    components: bool = False,
    hw_counters: bool = False,
    all_metrics: bool = False,
    filter_pattern: str | None = None,
    json_output: bool = False,
) -> str:
    """Query available profiling metrics and components.

    Args:
        components: Query available components
        hw_counters: Query hardware counters
        all_metrics: Query all available metrics
        filter_pattern: Filter pattern for results
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Query results or JSON string

    Raises:
        RuntimeError: If query fails
    """
    from wafer_core.lib.rocprofiler.systems import query_available_metrics  # pragma: no cover

    result = query_available_metrics(
        components=components,
        hw_counters=hw_counters,
        all_metrics=all_metrics,
        filter_pattern=filter_pattern,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Query completed", file=sys.stderr)
            if result.output:
                print("", file=sys.stderr)
                print(result.output)
            return "Query completed"
        else:
            print("✗ Query failed", file=sys.stderr)
            if result.error:
                print(f"  Error: {result.error}", file=sys.stderr)
            raise RuntimeError(result.error or "Query failed")
