"""NSYS Profile - Execute NSYS profiling on local, remote, or workspace targets.

This module provides the implementation for the `wafer nvidia nsys profile` command.
Supports local profiling (when nsys is installed), workspace execution, and direct SSH.

Profiling requires an NVIDIA GPU. Analysis can be done locally or remotely.
"""

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .nsys_analyze import (
    NSYSAnalysisResult,
    _find_nsys,
    _get_install_command,
    _parse_target,
    is_macos,
)


@dataclass(frozen=True)
class NSYSProfileResult:
    """Result of NSYS profiling execution."""

    success: bool
    output_path: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class NSYSProfileOptions:
    """Options for NSYS profiling."""

    command: str
    output: str = "profile"
    trace: list[str] | None = None  # cuda, nvtx, osrt, cudnn, cublas
    duration: int | None = None  # Max duration in seconds
    extra_args: str | None = None
    working_dir: str | None = None


def _build_nsys_command(
    nsys_path: str,
    options: NSYSProfileOptions,
) -> list[str]:
    """Build nsys profile command from options.

    Args:
        nsys_path: Path to nsys executable
        options: Profiling options

    Returns:
        Command as list of arguments
    """
    cmd = [nsys_path, "profile"]

    # Output file (without extension - nsys adds .nsys-rep)
    output_name = options.output
    if output_name.endswith(".nsys-rep"):
        output_name = output_name[:-9]
    cmd.extend(["-o", output_name])

    # Trace options
    if options.trace:
        cmd.extend(["-t", ",".join(options.trace)])
    else:
        cmd.extend(["-t", "cuda"])  # Default to CUDA tracing

    # Duration limit
    if options.duration:
        cmd.extend(["--duration", str(options.duration)])

    # Force overwrite
    cmd.append("--force-overwrite=true")

    # Extra args
    if options.extra_args:
        cmd.extend(shlex.split(options.extra_args))

    # Command to profile
    cmd.extend(shlex.split(options.command))

    return cmd


def profile_local(
    options: NSYSProfileOptions,
    verbose: bool = False,
) -> NSYSProfileResult:
    """Execute NSYS profiling locally.

    Args:
        options: Profiling options
        verbose: If True, print progress messages

    Returns:
        NSYSProfileResult with success status and output path

    Raises:
        FileNotFoundError: If nsys not installed
        RuntimeError: If profiling fails
    """
    # Find nsys
    nsys_path = _find_nsys()
    if nsys_path is None:
        if is_macos():
            raise FileNotFoundError(
                "NSYS CLI is not available on macOS. "
                "Use --target to profile on a remote GPU server or workspace."
            )
        raise FileNotFoundError(
            f"NSYS not installed. Install with: {_get_install_command()}"
        )

    # Build command
    cmd = _build_nsys_command(nsys_path, options)

    if verbose:
        print(f"[nsys] Running: {' '.join(cmd)}", file=sys.stderr)

    # Execute
    try:
        cwd = options.working_dir or os.getcwd()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=options.duration + 60 if options.duration else 660,
        )

        # Check for output file
        output_name = options.output
        if not output_name.endswith(".nsys-rep"):
            output_name = f"{output_name}.nsys-rep"

        output_path = Path(cwd) / output_name

        if result.returncode != 0:
            return NSYSProfileResult(
                success=False,
                stdout=result.stdout,
                stderr=result.stderr,
                error=f"nsys profile failed with exit code {result.returncode}",
            )

        if not output_path.exists():
            return NSYSProfileResult(
                success=False,
                stdout=result.stdout,
                stderr=result.stderr,
                error=f"Output file not created: {output_path}",
            )

        return NSYSProfileResult(
            success=True,
            output_path=str(output_path),
            stdout=result.stdout,
            stderr=result.stderr,
        )

    except subprocess.TimeoutExpired:
        return NSYSProfileResult(
            success=False,
            error=f"Profiling timed out after {options.duration or 600} seconds",
        )
    except OSError as e:
        return NSYSProfileResult(
            success=False,
            error=f"Failed to execute nsys: {e}",
        )


def profile_workspace(
    workspace_id: str,
    options: NSYSProfileOptions,
    verbose: bool = False,
    sync_artifacts: bool = True,
) -> NSYSProfileResult:
    """Execute NSYS profiling on a workspace.

    Args:
        workspace_id: Workspace ID to profile on
        options: Profiling options
        verbose: If True, print progress messages
        sync_artifacts: If True, sync output file back to local

    Returns:
        NSYSProfileResult with success status and output path
    """
    from .workspaces import exec_command_capture, get_workspace_info

    # Get workspace info to verify it exists
    try:
        workspace_info = get_workspace_info(workspace_id)
        if not workspace_info:
            return NSYSProfileResult(
                success=False,
                error=f"Workspace not found: {workspace_id}",
            )
    except Exception as e:
        return NSYSProfileResult(
            success=False,
            error=f"Failed to get workspace info: {e}",
        )

    if verbose:
        print(f"[nsys] Profiling on workspace: {workspace_id}", file=sys.stderr)

    # Build nsys command for remote execution
    # On workspace, nsys is expected to be in PATH
    nsys_cmd = "nsys profile"

    # Output file
    output_name = options.output
    if not output_name.endswith(".nsys-rep"):
        output_name_base = output_name
    else:
        output_name_base = output_name[:-9]

    nsys_cmd += f" -o {output_name_base}"

    # Trace options
    if options.trace:
        nsys_cmd += f" -t {','.join(options.trace)}"
    else:
        nsys_cmd += " -t cuda"

    # Duration
    if options.duration:
        nsys_cmd += f" --duration {options.duration}"

    # Force overwrite
    nsys_cmd += " --force-overwrite=true"

    # Extra args
    if options.extra_args:
        nsys_cmd += f" {options.extra_args}"

    # Command to profile
    nsys_cmd += f" {options.command}"

    if verbose:
        print(f"[nsys] Running: {nsys_cmd}", file=sys.stderr)

    # Execute on workspace
    exit_code, output = exec_command_capture(workspace_id, nsys_cmd)

    if exit_code != 0:
        return NSYSProfileResult(
            success=False,
            stdout=output,
            error=f"nsys profile failed on workspace with exit code {exit_code}",
        )

    # Check if output file was created
    output_file = f"{output_name_base}.nsys-rep"
    check_cmd = f"test -f {output_file} && echo 'exists' || echo 'not found'"
    check_code, check_output = exec_command_capture(workspace_id, check_cmd)

    if "not found" in check_output:
        return NSYSProfileResult(
            success=False,
            stdout=output,
            error=f"Output file not created on workspace: {output_file}",
        )

    if verbose:
        print(f"[nsys] Profile created: {output_file}", file=sys.stderr)

    # Optionally sync back to local
    local_path = None
    if sync_artifacts:
        if verbose:
            print(f"[nsys] Syncing {output_file} to local...", file=sys.stderr)

        try:
            from .workspaces import sync_workspace_file

            local_path = sync_workspace_file(workspace_id, output_file, Path.cwd())
            if verbose:
                print(f"[nsys] Synced to: {local_path}", file=sys.stderr)
        except Exception as e:
            if verbose:
                print(f"[nsys] Warning: Failed to sync: {e}", file=sys.stderr)
            # Not a failure - file exists on workspace
            local_path = None

    return NSYSProfileResult(
        success=True,
        output_path=str(local_path) if local_path else f"workspace:{workspace_id}:{output_file}",
        stdout=output,
    )


def profile_remote_ssh(
    target: str,
    options: NSYSProfileOptions,
    verbose: bool = False,
) -> NSYSProfileResult:
    """Execute NSYS profiling on a remote target via SSH.

    Args:
        target: Target name from ~/.wafer/targets/
        options: Profiling options
        verbose: If True, print progress messages

    Returns:
        NSYSProfileResult with success status and output path
    """
    import trio

    from .targets import load_target
    from .targets_ops import TargetExecError, exec_on_target_sync, get_target_ssh_info

    # Load target
    try:
        target_config = load_target(target)
    except FileNotFoundError as e:
        return NSYSProfileResult(
            success=False,
            error=f"Target not found: {e}",
        )
    except ValueError as e:
        return NSYSProfileResult(
            success=False,
            error=f"Invalid target config: {e}",
        )

    if verbose:
        print(f"[nsys] Connecting to target: {target}", file=sys.stderr)

    # Get SSH info
    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        return NSYSProfileResult(
            success=False,
            error=f"Failed to connect to target: {e}",
        )

    if verbose:
        print(
            f"[nsys] Connected: {ssh_info.user}@{ssh_info.host}:{ssh_info.port}",
            file=sys.stderr,
        )

    # Build nsys command
    output_name = options.output
    if not output_name.endswith(".nsys-rep"):
        output_name_base = output_name
    else:
        output_name_base = output_name[:-9]

    nsys_cmd = f"nsys profile -o {output_name_base}"

    if options.trace:
        nsys_cmd += f" -t {','.join(options.trace)}"
    else:
        nsys_cmd += " -t cuda"

    if options.duration:
        nsys_cmd += f" --duration {options.duration}"

    nsys_cmd += " --force-overwrite=true"

    if options.extra_args:
        nsys_cmd += f" {options.extra_args}"

    nsys_cmd += f" {options.command}"

    if verbose:
        print(f"[nsys] Running: {nsys_cmd}", file=sys.stderr)

    # Execute
    try:
        timeout = options.duration + 60 if options.duration else 660
        exit_code = exec_on_target_sync(ssh_info, nsys_cmd, timeout)

        if exit_code != 0:
            return NSYSProfileResult(
                success=False,
                error=f"nsys profile failed on target with exit code {exit_code}",
            )

        output_file = f"{output_name_base}.nsys-rep"
        return NSYSProfileResult(
            success=True,
            output_path=f"ssh:{target}:{output_file}",
        )

    except TargetExecError as e:
        return NSYSProfileResult(
            success=False,
            error=f"Execution failed: {e}",
        )


def profile_and_analyze(
    options: NSYSProfileOptions,
    target: str | None = None,
    json_output: bool = False,
    verbose: bool = False,
) -> tuple[NSYSProfileResult, NSYSAnalysisResult | None]:
    """Profile and optionally analyze in one operation.

    Args:
        options: Profiling options
        target: Optional target (workspace:id or target name)
        json_output: If True, analysis returns JSON
        verbose: If True, print progress messages

    Returns:
        Tuple of (profile_result, analysis_result or None)
    """
    from .nsys_analyze import analyze_nsys_profile

    # Profile
    if target:
        target_type, target_id = _parse_target(target)
        if target_type == "workspace":
            profile_result = profile_workspace(
                target_id, options, verbose=verbose, sync_artifacts=True
            )
        else:
            profile_result = profile_remote_ssh(target_id, options, verbose=verbose)
    else:
        profile_result = profile_local(options, verbose=verbose)

    if not profile_result.success:
        return profile_result, None

    # Analyze
    if profile_result.output_path:
        # Check if it's a local path we can analyze
        output_path = profile_result.output_path
        if output_path.startswith("workspace:") or output_path.startswith("ssh:"):
            # Remote file - need to analyze on remote
            if verbose:
                print(
                    f"[nsys] Analyzing remote file: {output_path}", file=sys.stderr
                )
            # For workspace, we can use workspace analysis
            if target and target.startswith("workspace:"):
                parts = output_path.split(":")
                ws_id = parts[1]
                filepath = parts[2]
                try:
                    analysis_output = analyze_nsys_profile(
                        Path(filepath),
                        json_output=json_output,
                        target=f"workspace:{ws_id}",
                    )
                    # Parse the output if needed
                    if json_output:
                        analysis_data = json.loads(analysis_output)
                        analysis_result = NSYSAnalysisResult(
                            success=True,
                            kernels=analysis_data.get("kernels"),
                            memory_transfers=analysis_data.get("memory_transfers"),
                        )
                    else:
                        analysis_result = NSYSAnalysisResult(
                            success=True,
                        )
                    return profile_result, analysis_result
                except Exception as e:
                    return profile_result, NSYSAnalysisResult(
                        success=False,
                        error=f"Analysis failed: {e}",
                    )
            else:
                # For SSH targets, we'd need to implement analysis there
                return profile_result, NSYSAnalysisResult(
                    success=False,
                    error="Remote analysis for SSH targets not yet implemented. Download the file and analyze locally.",
                )
        else:
            # Local file
            try:
                analysis_output = analyze_nsys_profile(
                    Path(output_path),
                    json_output=json_output,
                )
                if json_output:
                    analysis_data = json.loads(analysis_output)
                    analysis_result = NSYSAnalysisResult(
                        success=True,
                        kernels=analysis_data.get("kernels"),
                        memory_transfers=analysis_data.get("memory_transfers"),
                    )
                else:
                    analysis_result = NSYSAnalysisResult(success=True)
                    # Print the analysis
                    print(analysis_output)
                return profile_result, analysis_result
            except Exception as e:
                return profile_result, NSYSAnalysisResult(
                    success=False,
                    error=f"Analysis failed: {e}",
                )

    return profile_result, None
