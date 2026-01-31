"""Baseline CLI commands.

Discover what kernel PyTorch dispatches to for a given operation.
Helps understand the baseline performance you need to beat.
"""

import asyncio

import typer

from wafer_core.tools.dispatch_baseline.client import (
    lookup_baseline,
    store_baseline,
)
from wafer_core.tools.dispatch_baseline.codegen import (
    parse_op_string,
    update_dtypes,
    update_shapes,
)
from wafer_core.tools.dispatch_baseline.dtypes import KernelTraceConfig
from wafer_core.tools.dispatch_baseline.executor import trace_kernel_local
from wafer_core.tools.dispatch_baseline.roofline import HARDWARE_SPECS, get_hardware_spec

baseline_app = typer.Typer(
    help="""Discover what kernel PyTorch dispatches to for a given operation.

This helps you understand the baseline performance you need to beat when writing
custom kernels. Run a PyTorch op, profile it, and see:
- What kernel PyTorch uses (cuBLAS, cuDNN, Triton, etc.)
- How fast it runs
- What % of peak hardware performance it achieves

Results are stored in a shared database - once traced, everyone benefits.

Examples:
    # Run baseline trace
    wafer baseline run "torch.matmul(A, B)" -s A=4096,4096 -s B=4096,4096 --target b200-dev

    # Show supported hardware
    wafer baseline hardware"""
)


def _parse_shape(shape_str: str) -> tuple[str, tuple[int, ...]]:
    """Parse shape string like 'A=4096,4096' into (name, shape)."""
    if "=" not in shape_str:
        raise typer.BadParameter(f"Invalid shape format: {shape_str}. Expected: name=dim1,dim2,...")

    name, dims_str = shape_str.split("=", 1)
    try:
        dims = tuple(int(d.strip()) for d in dims_str.split(","))
    except ValueError:
        raise typer.BadParameter(f"Invalid dimensions in shape: {dims_str}")

    return name.strip(), dims


def _complete_target_name(incomplete: str) -> list[str]:
    """Autocomplete target names from ~/.wafer/targets/*.toml"""
    from pathlib import Path

    targets_dir = Path.home() / ".wafer" / "targets"
    if not targets_dir.exists():
        return []
    return [f.stem for f in targets_dir.glob("*.toml") if f.stem.startswith(incomplete)]


@baseline_app.command("run")
def baseline_run_cmd(
    op: str = typer.Argument(
        ...,
        help='PyTorch operation to trace, e.g., "torch.matmul(A, B)"',
    ),
    shape: list[str] = typer.Option(
        [],
        "--shape",
        "-s",
        help="Tensor shape as name=dim1,dim2,... (can specify multiple)",
    ),
    dtype: str = typer.Option(
        "float16",
        "--dtype",
        "-d",
        help="Data type for tensors (float16, float32, bfloat16, etc.)",
    ),
    hardware: str = typer.Option(
        None,
        "--hardware",
        help="Hardware name for roofline analysis (auto-detected from target if not specified)",
    ),
    target: str = typer.Option(
        None,
        "--target",
        "-t",
        help="GPU target name (see 'wafer config targets list')",
        autocompletion=_complete_target_name,
    ),
    workspace: str = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Workspace name (see 'wafer workspaces list')",
    ),
    num_warmup: int = typer.Option(
        10,
        "--warmup",
        help="Number of warmup iterations",
    ),
    num_runs: int = typer.Option(
        100,
        "--runs",
        help="Number of profiling runs",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Skip cache and always run fresh trace",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON for programmatic use",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose output including raw profiler data",
    ),
    timeout: int = typer.Option(
        120,
        "--timeout",
        help="Timeout in seconds for profiling (default: 120)",
    ),
) -> None:
    """Discover what kernel PyTorch dispatches to for a given operation.

    This runs the operation on your GPU with profiling and reports:
    - Which kernel(s) PyTorch dispatches to
    - Duration of each kernel
    - Library that provides the kernel (cuBLAS, cuDNN, etc.)
    - Roofline analysis (% of peak compute/memory bandwidth)

    Examples:
        # Run on a target
        wafer baseline run "torch.matmul(A, B)" -s A=4096,4096 -s B=4096,4096 --target b200-dev

        # Run on a workspace
        wafer baseline run "torch.matmul(A, B)" -s A=4096,4096 -s B=4096,4096 --workspace cutlass-b200-eval

        # Run locally (requires local GPU)
        wafer baseline run "torch.matmul(A, B)" -s A=4096,4096 -s B=4096,4096

        # With specific hardware for roofline
        wafer baseline run "torch.matmul(A, B)" -s A=4096,4096 -s B=4096,4096 --target b200-dev --hardware B200
    """
    # Validate mutually exclusive options
    if target and workspace:
        typer.echo("Error: Cannot specify both --target and --workspace", err=True)
        raise typer.Exit(1)

    # Dispatch to appropriate execution mode
    if target:
        asyncio.run(_run_on_target(
            op, shape, dtype, hardware, target, num_warmup, num_runs, no_cache, json_output, verbose, timeout
        ))
    elif workspace:
        asyncio.run(_run_on_workspace(
            op, shape, dtype, hardware, workspace, num_warmup, num_runs, no_cache, json_output, verbose, timeout
        ))
    else:
        _run_locally(op, shape, dtype, hardware, num_warmup, num_runs, no_cache, json_output, verbose, timeout)


def _run_locally(
    op: str,
    shape: list[str],
    dtype: str,
    hardware: str | None,
    num_warmup: int,
    num_runs: int,
    no_cache: bool,
    json_output: bool,
    verbose: bool,
    timeout: int,
) -> None:
    """Run baseline trace on local GPU."""
    import torch

    # Check CUDA availability
    if not torch.cuda.is_available():
        typer.echo("Error: CUDA not available on this machine", err=True)
        typer.echo("Use --target or --workspace to run on a remote GPU.", err=True)
        raise typer.Exit(1)

    # Auto-detect hardware if not specified
    if hardware is None:
        hardware = _detect_local_hardware()
        if hardware:
            if not json_output:
                typer.echo(f"Auto-detected hardware: {hardware}")
        else:
            gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unknown"
            if not json_output:
                typer.echo(f"Warning: No roofline specs for '{gpu_name}'", err=True)
                typer.echo(f"Supported hardware: {', '.join(HARDWARE_SPECS.keys())}", err=True)
                typer.echo("Roofline analysis will be skipped.", err=True)
                typer.echo("")

    # Parse operation
    try:
        op_spec = parse_op_string(op)
    except ValueError as e:
        typer.echo(f"Error parsing operation: {e}", err=True)
        raise typer.Exit(1)

    # Parse shapes
    shapes: dict[str, tuple[int, ...]] = {}
    for shape_str in shape:
        try:
            name, dims = _parse_shape(shape_str)
            shapes[name] = dims
        except typer.BadParameter as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    # Update op_spec with shapes and dtype
    if shapes:
        op_spec = update_shapes(op_spec, shapes)
    op_spec = update_dtypes(op_spec, dtype)

    # Validate hardware
    hw_spec = get_hardware_spec(hardware)
    if hw_spec is None:
        typer.echo(f"Warning: Unknown hardware '{hardware}', roofline analysis will be skipped", err=True)
        typer.echo(f"Supported hardware: {', '.join(HARDWARE_SPECS.keys())}", err=True)

    # Get current environment for cache lookup
    pytorch_version = torch.__version__
    props = torch.cuda.get_device_properties(0)
    
    # Detect runtime version and architecture (CUDA vs ROCm)
    if hasattr(torch.version, 'hip') and torch.version.hip:
        runtime_version = torch.version.hip
        gpu_arch = getattr(props, 'gcnArchName', f"gfx{props.major}{props.minor}")
    else:
        runtime_version = torch.version.cuda or "unknown"
        gpu_arch = f"sm_{props.major}{props.minor}"

    # Check cache first (unless --no-cache)
    from_cache = False
    if not no_cache:
        cached = lookup_baseline(op_spec, hardware, pytorch_version, runtime_version, gpu_arch)
        if cached is not None:
            from_cache = True
            # Re-compute roofline with current hardware specs (in case they've been updated)
            config = KernelTraceConfig(op_spec=op_spec, hardware=hardware, num_warmup=0, num_runs=0)
            from wafer_core.tools.dispatch_baseline.executor import _add_roofline_analysis
            result = _add_roofline_analysis(cached, config)
            if not json_output:
                typer.echo(f"Using cached result (key: {pytorch_version}/{runtime_version}/{gpu_arch})")
                typer.echo("")

    if not from_cache:
        # Create config
        config = KernelTraceConfig(
            op_spec=op_spec,
            hardware=hardware,
            num_warmup=num_warmup,
            num_runs=num_runs,
            timeout_seconds=timeout,
        )

        # Run trace
        if not json_output:
            typer.echo(f"Profiling: {op_spec}")
            typer.echo(f"Hardware: {hardware}")
            typer.echo("")

        exec_result = trace_kernel_local(config)
        result = exec_result.result

        # Cache the result
        if not result.error:
            store_baseline(
                result,
                exec_result.pytorch_version,
                exec_result.runtime_version,
                exec_result.gpu_arch,
            )

    # Output results
    _output_result(result, json_output, verbose, from_cache)


def _detect_local_hardware() -> str:
    """Detect GPU hardware name from local CUDA device.
    
    Only returns hardware names that we have specs for (B200, MI300X).
    Returns None for unsupported hardware.
    """
    import torch

    if not torch.cuda.is_available():
        return None

    gpu_name = torch.cuda.get_device_name(0).upper()

    # Only return hardware we have roofline specs for
    if "B200" in gpu_name:
        return "B200"
    elif "MI300X" in gpu_name:
        return "MI300X"
    else:
        return None  # Unsupported hardware


def _detect_hardware_from_target(target_config) -> str | None:
    """Detect hardware from target configuration.
    
    Only returns hardware names that we have specs for (B200, MI300X).
    """
    gpu_type = getattr(target_config, "gpu_type", None)
    if gpu_type:
        gpu_upper = gpu_type.upper()
        if gpu_upper in HARDWARE_SPECS:
            return gpu_upper
    return None


async def _run_on_target(
    op: str,
    shape: list[str],
    dtype: str,
    hardware: str | None,
    target_name: str,
    num_warmup: int,
    num_runs: int,
    no_cache: bool,
    json_output: bool,
    verbose: bool,
    timeout: int,
) -> None:
    """Run baseline trace on a configured target via SSH."""
    from wafer_core.ssh import SSHClient
    from wafer_core.tools.dispatch_baseline.codegen import generate_trace_script
    from wafer_core.tools.dispatch_baseline.executor import trace_kernel_remote

    from .targets import load_target
    from .targets_ops import TargetExecError, get_target_ssh_info

    # Load target config
    try:
        target_config = load_target(target_name)
    except FileNotFoundError:
        typer.echo(f"Error: Target '{target_name}' not found", err=True)
        typer.echo("Run 'wafer config targets list' to see available targets", err=True)
        raise typer.Exit(1)

    # Auto-detect hardware from target if not specified
    if hardware is None:
        hardware = _detect_hardware_from_target(target_config)
        if hardware:
            if not json_output:
                typer.echo(f"Auto-detected hardware from target: {hardware}")
        else:
            if not json_output:
                typer.echo(f"Warning: No roofline specs for target's GPU", err=True)
                typer.echo(f"Supported hardware: {', '.join(HARDWARE_SPECS.keys())}", err=True)
                typer.echo("Roofline analysis will be skipped.", err=True)
                typer.echo("")

    # Get SSH info
    try:
        ssh_info = await get_target_ssh_info(target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)

    # Parse operation and create config
    try:
        op_spec = parse_op_string(op)
    except ValueError as e:
        typer.echo(f"Error parsing operation: {e}", err=True)
        raise typer.Exit(1)

    shapes: dict[str, tuple[int, ...]] = {}
    for shape_str in shape:
        try:
            name, dims = _parse_shape(shape_str)
            shapes[name] = dims
        except typer.BadParameter as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    if shapes:
        op_spec = update_shapes(op_spec, shapes)
    op_spec = update_dtypes(op_spec, dtype)

    config = KernelTraceConfig(
        op_spec=op_spec,
        hardware=hardware,
        num_warmup=num_warmup,
        num_runs=num_runs,
    )

    if not json_output:
        typer.echo(f"Profiling: {op_spec}")
        typer.echo(f"Target: {target_name}")
        typer.echo(f"Hardware: {hardware}")
        typer.echo("")

    # Create SSH client and run trace
    ssh_client = SSHClient(
        host=ssh_info.host,
        port=ssh_info.port,
        username=ssh_info.user,
        key_path=str(ssh_info.key_path),
    )

    try:
        ssh_client.connect()
        exec_result = trace_kernel_remote(config, ssh_client)
        result = exec_result.result

        # Cache the result
        if not result.error and not no_cache:
            store_baseline(
                result,
                exec_result.pytorch_version,
                exec_result.runtime_version,
                exec_result.gpu_arch,
            )
    finally:
        ssh_client.close()

    _output_result(result, json_output, verbose, from_cache=False)


async def _run_on_workspace(
    op: str,
    shape: list[str],
    dtype: str,
    hardware: str | None,
    workspace_name: str,
    num_warmup: int,
    num_runs: int,
    no_cache: bool,
    json_output: bool,
    verbose: bool,
    timeout: int,
) -> None:
    """Run baseline trace on a workspace."""
    import subprocess
    import tempfile
    from pathlib import Path

    from wafer_core.tools.dispatch_baseline.analyzer import parse_trace_output
    from wafer_core.tools.dispatch_baseline.codegen import generate_trace_script
    from wafer_core.tools.dispatch_baseline.executor import _add_roofline_analysis

    # Parse operation and create config
    try:
        op_spec = parse_op_string(op)
    except ValueError as e:
        typer.echo(f"Error parsing operation: {e}", err=True)
        raise typer.Exit(1)

    shapes: dict[str, tuple[int, ...]] = {}
    for shape_str in shape:
        try:
            name, dims = _parse_shape(shape_str)
            shapes[name] = dims
        except typer.BadParameter as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

    if shapes:
        op_spec = update_shapes(op_spec, shapes)
    op_spec = update_dtypes(op_spec, dtype)

    # Default hardware for workspaces (can be overridden)
    if hardware is None:
        # Try to detect from workspace name (only supported hardware)
        ws_lower = workspace_name.lower()
        if "b200" in ws_lower:
            hardware = "B200"
        elif "mi300" in ws_lower:
            hardware = "MI300X"
        else:
            hardware = None
        
        if hardware:
            if not json_output:
                typer.echo(f"Auto-detected hardware from workspace name: {hardware}")
        else:
            if not json_output:
                typer.echo(f"Warning: Could not detect hardware from workspace name '{workspace_name}'", err=True)
                typer.echo(f"Supported hardware: {', '.join(HARDWARE_SPECS.keys())}", err=True)
                typer.echo("Roofline analysis will be skipped.", err=True)
                typer.echo("")

    config = KernelTraceConfig(
        op_spec=op_spec,
        hardware=hardware,
        num_warmup=num_warmup,
        num_runs=num_runs,
    )

    if not json_output:
        typer.echo(f"Profiling: {op_spec}")
        typer.echo(f"Workspace: {workspace_name}")
        typer.echo(f"Hardware: {hardware}")
        typer.echo("")

    # Generate script
    script = generate_trace_script(config)

    # Write to temp file and sync to workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "baseline_trace.py"
        script_path.write_text(script)

        # Sync to workspace using wafer CLI
        sync_result = subprocess.run(
            ["wafer", "workspaces", "sync", workspace_name, str(tmpdir)],
            capture_output=True,
            text=True,
        )
        if sync_result.returncode != 0:
            typer.echo(f"Error syncing to workspace: {sync_result.stderr}", err=True)
            raise typer.Exit(1)

        # Execute on workspace
        exec_result = subprocess.run(
            ["wafer", "workspaces", "exec", "--timeout", str(timeout), workspace_name,
             "python /workspace/baseline_trace.py"],
            capture_output=True,
            text=True,
        )

        output = exec_result.stdout + exec_result.stderr

        # Parse result
        parsed = parse_trace_output(output, op_spec, hardware)
        result = _add_roofline_analysis(parsed.result, config)

        # Cache the result
        if not result.error and not no_cache:
            store_baseline(
                result,
                parsed.pytorch_version,
                parsed.runtime_version,
                parsed.gpu_arch,
            )

    _output_result(result, json_output, verbose, from_cache=False)


def _output_result(result, json_output: bool, verbose: bool, from_cache: bool = False) -> None:
    """Output trace result in the requested format."""
    if json_output:
        import json

        output = {
            "op": str(result.op_spec),
            "hardware": result.hardware,
            "total_duration_us": result.total_duration_us,
            "from_cache": from_cache,
            "kernels": [
                {
                    "name": k.name,
                    "duration_us": k.duration_us,
                }
                for k in result.kernels
            ],
            "primary_kernel": {
                "name": result.primary_kernel.name,
                "duration_us": result.primary_kernel.duration_us,
            }
            if result.primary_kernel
            else None,
            "roofline": {
                "achieved_tflops": result.roofline.achieved_tflops,
                "achieved_memory_bw_tbps": result.roofline.achieved_memory_bw_tbps,
                "compute_pct_of_peak": result.roofline.compute_pct_of_peak,
                "memory_bw_pct_of_peak": result.roofline.memory_bw_pct_of_peak,
                "bottleneck": result.roofline.bottleneck,
            }
            if result.roofline
            else None,
            "error": result.error,
        }
        typer.echo(json.dumps(output, indent=2))
    else:
        if result.error:
            typer.echo(f"Error: {result.error}", err=True)
            if verbose and result.raw_output:
                typer.echo("\nRaw output:")
                typer.echo(result.raw_output)
            raise typer.Exit(1)

        if from_cache:
            typer.echo("(from cache)")
            typer.echo("")

        typer.echo(result.summary())

        if verbose and result.raw_output:
            typer.echo("\n--- Raw Profiler Output ---")
            typer.echo(result.raw_output)


@baseline_app.command("hardware")
def hardware_cmd(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output as JSON",
    ),
) -> None:
    """List supported hardware and their specifications.

    Shows peak FLOPS and memory bandwidth for each supported GPU,
    used for roofline analysis calculations.

    Examples:
        wafer baseline hardware
        wafer baseline hardware --json
    """
    if json_output:
        import json

        output = {
            name: {
                "peak_fp16_tflops": spec.peak_fp16_tflops,
                "peak_fp32_tflops": spec.peak_fp32_tflops,
                "peak_memory_bw_tbps": spec.peak_memory_bw_tbps,
                "peak_fp8_tflops": spec.peak_fp8_tflops,
                "peak_int8_tops": spec.peak_int8_tops,
            }
            for name, spec in HARDWARE_SPECS.items()
        }
        typer.echo(json.dumps(output, indent=2))
    else:
        typer.echo("Supported Hardware for Roofline Analysis")
        typer.echo("=" * 60)
        typer.echo("")
        typer.echo(f"{'Name':<12} {'FP16 TFLOPS':<14} {'FP32 TFLOPS':<14} {'Mem BW (TB/s)':<14}")
        typer.echo("-" * 60)

        for name, spec in sorted(HARDWARE_SPECS.items()):
            typer.echo(
                f"{name:<12} {spec.peak_fp16_tflops:<14.1f} {spec.peak_fp32_tflops:<14.1f} {spec.peak_memory_bw_tbps:<14.2f}"
            )

        typer.echo("")
        typer.echo("Note: FP16 TFLOPS shown without sparsity for most GPUs.")
        typer.echo("Use --json for complete specifications.")


