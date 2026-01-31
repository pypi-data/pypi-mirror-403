"""ROCprof-Compute - CLI wrapper for rocprof-compute tool.

This module provides the CLI wrapper for the `wafer rocprof-compute` command.
It supports multiple subcommands:
- check: Check rocprof-compute installation
- profile: Run profiling on a command
- analyze: Analyze existing workload data
- gui: Launch GUI viewer for analyzing results
- list-metrics: List available metrics for architecture

This follows the design in Wafer-391: ROCprofiler Tools Architecture.
Architecture follows similar patterns from the codebase.
"""

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path


def print_usage() -> None:
    """Print CLI usage information."""
    print("Usage: wafer rocprof-compute <subcommand> [options]", file=sys.stderr)
    print("", file=sys.stderr)
    print("Subcommands:", file=sys.stderr)
    print("  check                Check rocprof-compute installation status", file=sys.stderr)
    print("  profile COMMAND      Profile a command", file=sys.stderr)
    print("  analyze PATH         Analyze existing workload", file=sys.stderr)
    print("  gui <folder>         Launch GUI viewer for profiling results", file=sys.stderr)
    print("  list-metrics ARCH    List metrics for architecture", file=sys.stderr)
    print("", file=sys.stderr)
    print("Profile Options:", file=sys.stderr)
    print("  --name NAME          Workload name (required)", file=sys.stderr)
    print("  --path DIR           Workload base path", file=sys.stderr)
    print("  --kernel K1,K2       Kernel name filter", file=sys.stderr)
    print("  --dispatch D1,D2     Dispatch ID filter", file=sys.stderr)
    print("  --block B1,B2        Hardware block filter", file=sys.stderr)
    print("  --no-roof            Skip roofline data", file=sys.stderr)
    print("  --roof-only          Profile roofline only (fastest)", file=sys.stderr)
    print("  --hip-trace          Enable HIP trace", file=sys.stderr)
    print("", file=sys.stderr)
    print("Analyze Options:", file=sys.stderr)
    print("  --list-stats         List all detected kernels and dispatches", file=sys.stderr)
    print("", file=sys.stderr)
    print("GUI Options:", file=sys.stderr)
    print("  --port PORT          Port for GUI server (default: 8050)", file=sys.stderr)
    print("  --json               Output result as JSON", file=sys.stderr)
    print("  --external           Use external rocprof-compute binary (default: bundled)", file=sys.stderr)
    print("", file=sys.stderr)
    print("Examples:", file=sys.stderr)
    print("  wafer rocprof-compute check", file=sys.stderr)
    print("  wafer rocprof-compute profile --name vcopy -- './vcopy -n 1048576'", file=sys.stderr)
    print("  wafer rocprof-compute profile --name vcopy --roof-only -- './vcopy -n 1048576'", file=sys.stderr)
    print("  wafer rocprof-compute analyze ./workloads/vcopy", file=sys.stderr)
    print("  wafer rocprof-compute analyze ./workloads/vcopy --list-stats", file=sys.stderr)
    print("  wafer rocprof-compute gui ./workloads/vcopy", file=sys.stderr)
    print("  wafer rocprof-compute list-metrics gfx90a", file=sys.stderr)


def check_command(json_output: bool = False) -> str:
    """CLI wrapper for checking rocprof-compute installation.

    Args:
        json_output: If True, return JSON; otherwise print human-readable

    Returns:
        Status message or JSON string
    """
    from dataclasses import asdict

    from wafer_core.lib.rocprofiler.compute import (
        check_installation as core_check,  # pragma: no cover
    )

    result = core_check()

    if json_output:
        result_dict = asdict(result) if hasattr(result, "__dataclass_fields__") else result
        return json.dumps(result_dict, indent=2)
    else:
        if result.installed:
            print("✓ rocprof-compute is installed", file=sys.stderr)
            if result.path:
                print(f"  Path: {result.path}", file=sys.stderr)
            if result.version:
                print(f"  Version: {result.version}", file=sys.stderr)
            return "rocprof-compute is installed"
        else:
            print("✗ rocprof-compute is not installed", file=sys.stderr)
            print("", file=sys.stderr)
            print("rocprof-compute is required to use this feature.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Installation options:", file=sys.stderr)
            print("  1. Install ROCm toolkit (includes rocprof-compute):", file=sys.stderr)
            print("     sudo apt-get install rocm-dev", file=sys.stderr)
            print("", file=sys.stderr)
            print("  2. Install rocprofiler-compute package:", file=sys.stderr)
            print("     sudo apt-get install rocprofiler-compute", file=sys.stderr)
            print("", file=sys.stderr)
            print("  3. Add ROCm to PATH if already installed:", file=sys.stderr)
            print("     export PATH=/opt/rocm/bin:$PATH", file=sys.stderr)
            print("", file=sys.stderr)
            if result.install_command:
                print(f"Suggested command: {result.install_command}", file=sys.stderr)
            return "rocprof-compute is not installed"


def check_installation() -> dict:
    """Legacy function for backward compatibility."""
    from dataclasses import asdict

    from wafer_core.lib.rocprofiler.compute import (
        check_installation as core_check,  # pragma: no cover
    )

    result = core_check()
    if hasattr(result, "__dataclass_fields__"):
        return asdict(result)
    elif hasattr(result, "__dict__"):
        return result.__dict__
    return result


def gui_command(
    folder_path: str,
    port: int = 8050,
    json_output: bool = False,
    use_bundled: bool = True,
) -> str:
    """Launch rocprof-compute analyze GUI.

    By default, uses the bundled GUI viewer (GPU-agnostic, works on any platform).
    Can optionally use external rocprof-compute binary if installed.

    Args:
        folder_path: Path to folder containing ROCprofiler results
        port: Port number for the GUI server (default: 8050)
        json_output: If True, return JSON with status; otherwise launch the GUI
        use_bundled: If True, use bundled GUI viewer (default: True)
                     If False, use external rocprof-compute binary

    Returns:
        Success message or JSON output

    Raises:
        FileNotFoundError: If folder doesn't exist
        RuntimeError: If launch fails
    """
    from dataclasses import asdict

    if use_bundled:
        # Use bundled GUI viewer (no rocprof-compute needed)
        from wafer_core.lib.rocprofiler.compute import launch_gui_server  # pragma: no cover

        # For JSON mode, run in background to return immediately
        # For interactive mode, run in foreground (blocking)
        launch_result = launch_gui_server(folder_path, port, background=json_output)

        if not launch_result.success:
            raise RuntimeError(launch_result.error or "Failed to launch bundled GUI")

        result_dict = asdict(launch_result)
        result_dict["command"] = "bundled-gui-viewer"

        if json_output:
            return json.dumps(result_dict, indent=2)
        else:
            print("Launching bundled rocprof-compute GUI viewer...", file=sys.stderr)
            print(f"Folder: {launch_result.folder}", file=sys.stderr)
            print(f"Port: {launch_result.port}", file=sys.stderr)
            print(f"URL: {launch_result.url}", file=sys.stderr)
            print("", file=sys.stderr)
            print(f"Open {launch_result.url} in your browser", file=sys.stderr)
            print("Press Ctrl+C to stop the server", file=sys.stderr)

            # The launch_gui_server with background=False is blocking, so we never reach here
            # unless there's an error
            return "GUI server stopped."
    else:
        # Legacy: use external rocprof-compute binary
        from wafer_core.lib.rocprofiler.compute import launch_gui as core_launch  # pragma: no cover

        launch_result = core_launch(folder_path, port)

        if not launch_result.success:
            raise RuntimeError(launch_result.error or "Failed to launch GUI")

        result_dict = asdict(launch_result)
        result_dict["command"] = " ".join(launch_result.command or [])

        if json_output:
            return json.dumps(result_dict, indent=2)
        else:
            print("Launching external rocprof-compute GUI...", file=sys.stderr)
            print(f"Folder: {launch_result.folder}", file=sys.stderr)
            print(f"Port: {launch_result.port}", file=sys.stderr)
            print(f"URL: {launch_result.url}", file=sys.stderr)
            print(f"Command: {result_dict['command']}", file=sys.stderr)
            print("", file=sys.stderr)

            try:
                subprocess.run(launch_result.command, check=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"rocprof-compute failed with exit code {e.returncode}")
            except KeyboardInterrupt:
                print("\nGUI server stopped.", file=sys.stderr)

            return "GUI server stopped."


def launch_gui(
    folder_path: str,
    port: int = 8050,
    json_output: bool = False,
    use_bundled: bool = True,
) -> str:
    """Legacy function for backward compatibility. Use gui_command() instead."""
    return gui_command(folder_path, port, json_output, use_bundled)


def profile_command(
    command: str,
    name: str,
    path: str | None = None,
    kernel: str | None = None,
    dispatch: str | None = None,
    block: str | None = None,
    no_roof: bool = False,
    roof_only: bool = False,
    hip_trace: bool = False,
    verbose: int = 0,
    json_output: bool = False,
) -> str:
    """Run rocprof-compute profiling.

    Args:
        command: Shell command to profile
        name: Workload name
        path: Base path for workload directory
        kernel: Comma-separated kernel name filters
        dispatch: Comma-separated dispatch ID filters
        block: Comma-separated hardware block filters
        no_roof: Skip roofline data collection
        roof_only: Profile roofline data only (fastest)
        hip_trace: Enable HIP trace
        verbose: Verbosity level (0-3)
        json_output: Return JSON output

    Returns:
        Success message or JSON string

    Raises:
        RuntimeError: If profiling fails
    """
    import shlex

    from wafer_core.lib.rocprofiler.compute import run_profile  # pragma: no cover

    # Parse command string
    cmd_list = shlex.split(command)

    # Parse filter lists
    kernel_list = kernel.split(",") if kernel else None
    dispatch_list = [int(d) for d in dispatch.split(",")] if dispatch else None
    block_list = block.split(",") if block else None

    result = run_profile(
        target_command=cmd_list,
        workload_name=name,
        workload_path=Path(path) if path else None,
        kernel_filter=kernel_list,
        dispatch_filter=dispatch_list,
        block_filter=block_list,
        no_roof=no_roof,
        roof_only=roof_only,
        hip_trace=hip_trace,
        verbose=verbose,
    )

    if json_output:
        result_dict = asdict(result)
        return json.dumps(result_dict, indent=2)
    else:
        if result.success:
            print("✓ Profiling completed", file=sys.stderr)
            if result.workload_path:
                print(f"  Workload: {result.workload_path}", file=sys.stderr)
            if result.output_files:
                print(f"  Generated {len(result.output_files)} files", file=sys.stderr)
            return f"Results in: {result.workload_path}"
        else:
            print("✗ Profiling failed", file=sys.stderr)
            print("", file=sys.stderr)

            # Show stderr output (contains actual error details)
            # Note: rocprof-compute may write errors to stdout instead of stderr
            error_output = result.stderr or result.stdout
            if error_output and error_output.strip():
                print("rocprof-compute output:", file=sys.stderr)
                print("─" * 60, file=sys.stderr)
                print(error_output.strip(), file=sys.stderr)
                print("─" * 60, file=sys.stderr)
                print("", file=sys.stderr)

            # Show command that was run
            if result.command:
                print(f"Command: {' '.join(result.command)}", file=sys.stderr)
                print("", file=sys.stderr)

            # Show high-level error
            if result.error:
                print(f"Error: {result.error}", file=sys.stderr)

            # Create helpful error message
            # Check both stderr and stdout since rocprof-compute may use either
            combined_output = (result.stderr or "") + (result.stdout or "")
            error_msg = "Profiling failed"
            if "error while loading shared libraries" in combined_output.lower():
                error_msg += "\n\nThis looks like a missing dependency. Check the output above for the specific library."
            elif "not found" in combined_output.lower() or "no such file" in combined_output.lower():
                error_msg += "\n\nThe command or a required file was not found. Check the paths above."
            elif "distribution does not meet version requirements" in combined_output.lower():
                error_msg += "\n\nThis looks like a Python dependency version mismatch. Check the output above for the specific package."
            elif result.error and "exit code" in result.error.lower():
                error_msg += "\n\nThe profiling tool exited with an error. See output above for details."

            raise RuntimeError(error_msg)


def analyze_command(
    workload_path: str,
    kernel: str | None = None,
    dispatch: str | None = None,
    block: str | None = None,
    output: str | None = None,
    list_stats: bool = False,
    json_output: bool = False,
    gui: bool = False,
    port: int = 8050,
    external: bool = False,
) -> str:
    """Analyze rocprof-compute workload.

    This calls the native rocprof-compute analyze tool to generate comprehensive
    analysis output matching what you get from running rocprof-compute directly.

    For programmatic access to parsed data (without running the native tool),
    use parse_workload() from the Python API instead.

    Args:
        workload_path: Path to workload directory
        kernel: Comma-separated kernel filters
        dispatch: Comma-separated dispatch filters
        block: Comma-separated block filters
        output: Output file path
        list_stats: List all detected kernels and dispatches
        json_output: Return JSON output (uses parse_workload for structured data)
        gui: Launch GUI viewer instead of text analysis
        port: Port for GUI server (default: 8050)
        external: Use external rocprof-compute binary for GUI (default: bundled)

    Returns:
        Analysis output or JSON string

    Raises:
        RuntimeError: If analysis fails
    """
    from wafer_core.lib.rocprofiler.compute import parse_workload, run_analysis  # pragma: no cover

    # If GUI mode, delegate to GUI launch
    if gui:
        return gui_command(workload_path, port, json_output, use_bundled=not external)

    # For JSON output, use parse_workload (fast CSV parsing)
    if json_output:
        result = parse_workload(workload_path)
        result_dict = asdict(result)
        # Convert dataclass lists to dicts
        if result.kernels:
            result_dict["kernels"] = [asdict(k) for k in result.kernels]
        if result.roofline:
            result_dict["roofline"] = [asdict(r) for r in result.roofline]
        return json.dumps(result_dict, indent=2)

    # For text output, call native rocprof-compute analyze for full output
    # Parse filter lists
    kernel_list = kernel.split(",") if kernel else None
    dispatch_list = [int(d) for d in dispatch.split(",")] if dispatch else None
    block_list = block.split(",") if block else None

    result = run_analysis(
        workload_path=workload_path,
        kernel_filter=kernel_list,
        dispatch_filter=dispatch_list,
        block_filter=block_list,
        output_file=output,
        list_stats=list_stats,
    )

    if result.success:
        # Output is already streamed in real-time by run_analysis
        # Just return success message
        return "Analysis completed"
    else:
        print("✗ Analysis failed", file=sys.stderr)
        print("", file=sys.stderr)

        # Show stderr output (contains actual error details)
        # Note: rocprof-compute may write errors to stdout instead of stderr
        error_output = result.stderr or result.stdout
        if error_output and error_output.strip():
            print("rocprof-compute output:", file=sys.stderr)
            print("─" * 60, file=sys.stderr)
            print(error_output.strip(), file=sys.stderr)
            print("─" * 60, file=sys.stderr)
            print("", file=sys.stderr)

        # Show command that was run
        if result.command:
            print(f"Command: {' '.join(result.command)}", file=sys.stderr)
            print("", file=sys.stderr)

        # Show high-level error
        if result.error:
            print(f"Error: {result.error}", file=sys.stderr)

        # Create helpful error message
        # Check both stderr and stdout since rocprof-compute may use either
        combined_output = (result.stderr or "") + (result.stdout or "")
        error_msg = "Analysis failed"
        if "error while loading shared libraries" in combined_output.lower():
            error_msg += "\n\nThis looks like a missing dependency. Check the output above for the specific library."
        elif "not found" in combined_output.lower() or "no such file" in combined_output.lower():
            error_msg += "\n\nThe workload directory or required files were not found. Check the path above."
        elif "distribution does not meet version requirements" in combined_output.lower():
            error_msg += "\n\nThis looks like a Python dependency version mismatch. Check the output above for the specific package."
        elif result.error and "exit code" in result.error.lower():
            error_msg += "\n\nThe analysis tool exited with an error. See output above for details."

        raise RuntimeError(error_msg)


def list_metrics_command(arch: str) -> str:
    """List available metrics for architecture.

    Args:
        arch: Architecture name (e.g., "gfx90a", "gfx942")

    Returns:
        Metrics list output
    """
    import os
    import shutil
    import subprocess

    from wafer_core.lib.rocprofiler.compute import find_rocprof_compute  # pragma: no cover

    rocprof_path = find_rocprof_compute()
    if not rocprof_path:
        raise RuntimeError("rocprof-compute not found. Install ROCm toolkit.")

    # Build command: rocprof-compute profile --list-metrics <arch>
    cmd = [rocprof_path, "profile", "--list-metrics", arch]

    # Preserve terminal formatting
    env = os.environ.copy()
    env['TERM'] = 'xterm-256color'
    env['FORCE_COLOR'] = '1'
    env['COLUMNS'] = str(shutil.get_terminal_size().columns)
    env['LINES'] = str(shutil.get_terminal_size().lines)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode == 0:
        print(result.stdout, end='')
        return result.stdout
    else:
        print(f"✗ Failed to list metrics for {arch}", file=sys.stderr)
        if result.stderr:
            print("Error output:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        raise RuntimeError(f"Failed to list metrics for {arch}")
