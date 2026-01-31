# ruff: noqa: PLR0913, E402
# PLR0913 (too many arguments) is suppressed because Typer CLI commands
# naturally have many parameters - each --flag becomes a function argument.
# E402 (module level import not at top) is suppressed because we intentionally
# load .env files before importing other modules that may read env vars.
"""Wafer CLI - GPU development toolkit for LLM coding agents.

Core commands:
  agent       AI assistant for GPU kernel development
  evaluate    Test kernel correctness and performance
  corpus      Download GPU documentation for local access
  workspaces  Manage cloud GPU environments

Profiling tools:
  wafer nvidia ...   NVIDIA profiling (ncu, nsys, perfetto, tracelens)
  wafer amd ...      AMD profiling (isa, rocprof-sdk, rocprof-systems, rocprof-compute)

Setup:
  login/logout/whoami   Authentication
  config                CLI configuration and local GPU targets
"""

import atexit
import json
import os
import sys
import time
from pathlib import Path

import trio
import typer
from dotenv import load_dotenv

# Auto-load .env from current directory and ~/.wafer/.env
# This runs at import time so env vars are available before any config is accessed
load_dotenv()  # cwd/.env
load_dotenv(Path.home() / ".wafer" / ".env")  # ~/.wafer/.env

from .config import WaferConfig, WaferEnvironment
from .inference import infer_upload_files, resolve_environment
from .problems import (
    download_problems,
    get_problem_path,
    get_problems_path,
)
from .problems import (
    list_problems as list_problems_fn,
)

app = typer.Typer(
    help="GPU development toolkit for LLM coding agents",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,  # Don't dump local vars (makes tracebacks huge)
)

# =============================================================================
# Analytics tracking
# =============================================================================

# Track command start time for duration calculation
_command_start_time: float | None = None
# Track command outcome (defaults to failure, set to success on clean exit)
_command_outcome: str = "failure"


def _show_version() -> None:
    """Show CLI version and environment, then exit."""
    from .analytics import _get_cli_version
    from .global_config import load_global_config

    version = _get_cli_version()
    config = load_global_config()
    environment = config.environment

    typer.echo(f"wafer-cli {version} ({environment})")
    raise typer.Exit()


def _get_command_path(ctx: typer.Context) -> tuple[str, str | None]:
    """Extract command and subcommand from Typer context.

    Returns:
        Tuple of (command, subcommand). subcommand may be None.
    """
    # Build command path from invoked subcommand chain
    invoked = ctx.invoked_subcommand
    info_name = ctx.info_name or ""

    # Get parent command if exists
    parent_cmd = None
    if ctx.parent and ctx.parent.info_name and ctx.parent.info_name != "wafer":
        parent_cmd = ctx.parent.info_name

    if parent_cmd:
        return parent_cmd, info_name
    return info_name or "unknown", invoked


def _mark_command_success() -> None:
    """Mark the current command as successful.

    Call this at the end of successful command execution.
    Commands that raise typer.Exit(1) or exceptions will remain marked as failures.
    """
    global _command_outcome
    _command_outcome = "success"


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
    ),
) -> None:
    """Initialize analytics and track command execution."""
    if version:
        _show_version()
        return

    global _command_start_time, _command_outcome
    _command_start_time = time.time()
    _command_outcome = "success"  # Default to success, mark failure on exceptions

    # Initialize analytics (lazy import to avoid slowing down --help)
    from . import analytics

    analytics.init_analytics()

    # Install exception hook to catch SystemExit and mark failures
    # Also prints error message FIRST so it's visible even when traceback is truncated
    original_excepthook = sys.excepthook

    def custom_excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: object,
    ) -> None:
        global _command_outcome
        # Mark as failure if SystemExit with non-zero code, or any other exception
        if exc_type is SystemExit:
            exit_code = exc_value.code if hasattr(exc_value, "code") else 1
            if exit_code != 0 and exit_code is not None:
                _command_outcome = "failure"
        else:
            _command_outcome = "failure"
            # Print error summary FIRST (before traceback) so it's visible even if truncated
            print(
                f"\n\033[1;31m>>> ERROR: {exc_type.__name__}: {exc_value}\033[0m\n", file=sys.stderr
            )
        # Call original excepthook (prints the full traceback)
        original_excepthook(exc_type, exc_value, exc_traceback)

    sys.excepthook = custom_excepthook

    # Register tracking at exit to capture command outcome
    def track_on_exit() -> None:
        command, subcommand = _get_command_path(ctx)

        # Skip tracking for --help and --version
        if ctx.resilient_parsing:
            return

        # Calculate duration
        duration_ms = None
        if _command_start_time is not None:
            duration_ms = int((time.time() - _command_start_time) * 1000)

        # Track the command execution with the recorded outcome
        analytics.track_command(
            command=command,
            subcommand=subcommand,
            outcome=_command_outcome,
            duration_ms=duration_ms,
        )

    atexit.register(track_on_exit)


# =============================================================================
# Autocompletion helpers
# =============================================================================


def complete_target_name(incomplete: str) -> list[str]:
    """Autocomplete target names from ~/.wafer/targets/*.toml"""
    targets_dir = Path.home() / ".wafer" / "targets"
    if not targets_dir.exists():
        return []
    return [f.stem for f in targets_dir.glob("*.toml") if f.stem.startswith(incomplete)]


# =============================================================================
# Core subcommand groups (visible in --help)
# =============================================================================

# Config management (includes targets as nested subcommand)
config_app = typer.Typer(help="Manage CLI configuration and local GPU targets")
app.add_typer(config_app, name="config")

# Target management - nested under config
targets_app = typer.Typer(
    help="""Manage GPU targets for remote evaluation.

Targets define how to access GPUs. Use 'wafer config targets init' to set up:

  wafer config targets init ssh        # Your own GPU via SSH
  wafer config targets init runpod     # RunPod cloud GPUs (needs WAFER_RUNPOD_API_KEY)
  wafer config targets init digitalocean  # DigitalOcean AMD GPUs

Then use with: wafer evaluate --target <name> ..."""
)
config_app.add_typer(targets_app, name="targets")

# Workspace management (remote API-backed)
workspaces_app = typer.Typer(
    help="""Manage cloud GPU workspaces for remote development.

Workspaces are on-demand cloud GPU environments. Requires authentication (wafer login).

Available GPUs:
  MI300X  AMD Instinct MI300X (192GB HBM3, ROCm)
  B200    NVIDIA Blackwell B200 (180GB HBM3e, CUDA)

Commands:
  wafer workspaces create dev --gpu B200   # Create workspace
  wafer workspaces exec dev -- python x.py # Run commands
  wafer workspaces ssh dev                 # Interactive SSH
  wafer workspaces sync dev ./project      # Sync files
  wafer workspaces delete dev              # Clean up"""
)
app.add_typer(workspaces_app, name="workspaces")

# SSH Key management (BYOK - Bring Your Own Key)
ssh_keys_app = typer.Typer(
    help="""Manage SSH public keys for workspace access.

Register your SSH public keys here. These keys are installed in all workspaces
you provision, enabling SSH access from any machine with your private key.

  wafer ssh-keys list              # List registered keys
  wafer ssh-keys add               # Add key (auto-detects ~/.ssh/id_ed25519.pub)
  wafer ssh-keys add ~/.ssh/id_rsa.pub --name laptop  # Add specific key
  wafer ssh-keys remove <key-id>   # Remove a key"""
)
app.add_typer(ssh_keys_app, name="ssh-keys")

# Target operations (exec/ssh/sync on configured targets)
targets_ops_app = typer.Typer(
    help="""Execute commands on configured GPU targets.

Run commands, SSH, or sync files to targets without going through evaluate.
Useful for exploratory work, debugging, or custom scripts.

  wafer targets exec my-target -- python test.py    # Run command
  wafer targets ssh my-target                       # Interactive SSH
  wafer targets sync my-target ./local_dir          # Sync files

Supports: RunPod, DigitalOcean (auto-provisions), SSH targets (baremetal/vm).
Configure targets with: wafer config targets init ..."""
)
app.add_typer(targets_ops_app, name="targets")

# Billing management
billing_app = typer.Typer(help="Manage billing, credits, and subscription")
app.add_typer(billing_app, name="billing")

# Corpus management
corpus_app = typer.Typer(help="Download and manage GPU documentation")
app.add_typer(corpus_app, name="corpus")

# Evaluate (supports multiple kernel formats)
evaluate_app = typer.Typer(
    help="Test kernel correctness and performance",
    invoke_without_command=True,
)
app.add_typer(evaluate_app, name="evaluate")

# Nested subcommand for kernelbench format
kernelbench_app = typer.Typer(
    help="Evaluate kernels in KernelBench format (ModelNew class)",
    invoke_without_command=True,
)
evaluate_app.add_typer(kernelbench_app, name="kernelbench")

# Nested subcommand for gpumode format
gpumode_app = typer.Typer(
    help="Evaluate kernels in GPUMode format (custom_kernel/ref_kernel functions)",
    invoke_without_command=True,
)
evaluate_app.add_typer(gpumode_app, name="gpumode")

# =============================================================================
# Dev commands (internal, used by web app proxy)
# =============================================================================

dev_app = typer.Typer(help="Internal dev commands", hidden=True)
app.add_typer(dev_app, name="dev")


# =============================================================================
# NVIDIA profiling tools (wafer nvidia ...)
# =============================================================================

nvidia_app = typer.Typer(help="NVIDIA GPU profiling and analysis tools")
app.add_typer(nvidia_app, name="nvidia")

# NCU analysis - under nvidia
ncu_app = typer.Typer(help="Nsight Compute profile analysis")
nvidia_app.add_typer(ncu_app, name="ncu")

# NSYS analysis - under nvidia
nsys_app = typer.Typer(help="Nsight Systems profile analysis")
nvidia_app.add_typer(nsys_app, name="nsys")

# Perfetto trace analysis - under nvidia
perfetto_app = typer.Typer(help="Perfetto trace analysis and SQL queries")
nvidia_app.add_typer(perfetto_app, name="perfetto")

# TraceLens trace analysis - under nvidia
tracelens_app = typer.Typer(help="TraceLens performance reports")
nvidia_app.add_typer(tracelens_app, name="tracelens")

# =============================================================================
# AMD profiling tools (wafer amd ...)
# =============================================================================

amd_app = typer.Typer(help="AMD GPU profiling and analysis tools")
app.add_typer(amd_app, name="amd")

# Unified ISA Analyzer - supports both .co files and Triton artifacts
isa_app = typer.Typer(help="ISA analysis for AMD GPU kernels (.co, .s, .ll, .ttgir files)")
amd_app.add_typer(isa_app, name="isa")

# =============================================================================
# Trace comparison (wafer compare)
# =============================================================================

compare_app = typer.Typer(help="Compare GPU traces across platforms (AMD vs NVIDIA)")
app.add_typer(compare_app, name="compare")

# =============================================================================
# Roofline analysis (wafer roofline)
# =============================================================================


@app.command("roofline")
def roofline_cmd(
    gpu: str | None = typer.Option(
        None, "--gpu", "-g", help="GPU name (e.g., H100, B200, MI300X, A100)"
    ),
    bytes_moved: float | None = typer.Option(
        None, "--bytes", "-b", help="Theoretical minimum bytes moved"
    ),
    flops: float | None = typer.Option(None, "--flops", "-f", help="Theoretical minimum FLOPs"),
    time_ms: float | None = typer.Option(
        None, "--time-ms", "-t", help="Actual kernel time in milliseconds"
    ),
    dtype: str = typer.Option(
        "fp16", "--dtype", "-d", help="Data type for compute ceiling (fp16, fp32, bf16, fp8, int8)"
    ),
    list_gpus: bool = typer.Option(False, "--list-gpus", help="List available GPU specs and exit"),
) -> None:
    """Analyze kernel performance against roofline model.

    The roofline model shows the theoretical speed-of-light (SOL) for your kernel
    based on whether it's memory-bound or compute-bound.

    You need to provide:
    - The GPU you ran on
    - Theoretical minimum bytes moved (not actual - what the algorithm requires)
    - Theoretical minimum FLOPs
    - Actual measured kernel time

    Example:
        # Analyze a matmul kernel (4096x4096x4096, FP16)
        # Theoretical: 2*M*N*K FLOPs = 137.4 TFLOP
        # Theoretical bytes: (M*K + K*N + M*N) * 2 = 100.7 MB
        wafer roofline --gpu H100 --bytes 100.7e6 --flops 137.4e12 --time-ms 85

        # Analyze a memory-bound elementwise add (1B elements FP32)
        # Reads 2 tensors, writes 1 = 12 GB total
        # 1B adds = 1 GFLOP
        wafer roofline --gpu H100 --bytes 12e9 --flops 1e9 --time-ms 4 --dtype fp32

        # List available GPUs
        wafer roofline --list-gpus
    """
    from wafer_core.roofline import get_gpu_spec, roofline_analysis
    from wafer_core.roofline import list_gpus as get_all_gpus

    if list_gpus:
        typer.echo("Available GPUs:")
        for name in get_all_gpus():
            spec = get_gpu_spec(name)
            typer.echo(
                f"  {name}: {spec.peak_bandwidth_gbps:.0f} GB/s, {spec.peak_tflops_fp16:.0f} TFLOPS FP16"
            )
        return

    # Validate required args for analysis
    missing = []
    if gpu is None:
        missing.append("--gpu")
    if bytes_moved is None:
        missing.append("--bytes")
    if flops is None:
        missing.append("--flops")
    if time_ms is None:
        missing.append("--time-ms")

    if missing:
        typer.echo(f"Error: Missing required options: {', '.join(missing)}", err=True)
        typer.echo("", err=True)
        typer.echo("Run 'wafer roofline --help' for usage.", err=True)
        raise typer.Exit(1)

    try:
        result = roofline_analysis(
            gpu=gpu,
            dtype=dtype,
            bytes_moved=bytes_moved,
            flops=flops,
            time_ms=time_ms,
        )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(result.format_report())


# =============================================================================
# Skill management (wafer skill ...)
# =============================================================================

skill_app = typer.Typer(help="Manage AI coding assistant skills (Claude Code, Codex)")
app.add_typer(skill_app, name="skill")


@skill_app.command("install")
def skill_install(
    target: str = typer.Option(
        "all",
        "--target",
        "-t",
        help="Target tool: claude, codex, cursor, or all",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing skill"),
) -> None:
    """Install the wafer-guide skill for AI coding assistants.

    Installs the bundled skill to make wafer commands discoverable by
    Claude Code, OpenAI Codex CLI, and/or Cursor.

    Skills follow the open agent skills specification (agentskills.io).

    Examples:
        wafer skill install              # Install for all tools
        wafer skill install -t claude    # Install for Claude Code only
        wafer skill install -t codex     # Install for Codex CLI only
        wafer skill install -t cursor    # Install for Cursor only
        wafer skill install --force      # Overwrite existing installation
    """
    # Locate bundled skill
    skill_source = Path(__file__).parent / "skills" / "wafer-guide"
    if not skill_source.exists():
        typer.echo("Error: Bundled skill not found. Package may be corrupted.", err=True)
        raise typer.Exit(1)

    targets_to_install: list[tuple[str, Path]] = []

    if target in ("all", "claude"):
        targets_to_install.append((
            "Claude Code",
            Path.home() / ".claude" / "skills" / "wafer-guide",
        ))
    if target in ("all", "codex"):
        targets_to_install.append(("Codex CLI", Path.home() / ".codex" / "skills" / "wafer-guide"))
    if target in ("all", "cursor"):
        targets_to_install.append(("Cursor", Path.home() / ".cursor" / "skills" / "wafer-guide"))

    if not targets_to_install:
        typer.echo(
            f"Error: Unknown target '{target}'. Use: claude, codex, cursor, or all", err=True
        )
        raise typer.Exit(1)

    for tool_name, dest_path in targets_to_install:
        # Check if already exists
        if dest_path.exists():
            if not force:
                typer.echo(f"  {tool_name}: Already installed at {dest_path}")
                typer.echo("             Use --force to overwrite")
                continue
            # Remove existing
            if dest_path.is_symlink():
                dest_path.unlink()
            else:
                import shutil

                shutil.rmtree(dest_path)

        # Create parent directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Create symlink
        dest_path.symlink_to(skill_source)
        typer.echo(f"  {tool_name}: Installed at {dest_path}")

    typer.echo("")
    typer.echo("Restart your AI assistant to load the new skill.")


@skill_app.command("uninstall")
def skill_uninstall(
    target: str = typer.Option(
        "all",
        "--target",
        "-t",
        help="Target tool: claude, codex, cursor, or all",
    ),
) -> None:
    """Uninstall the wafer-guide skill.

    Examples:
        wafer skill uninstall              # Uninstall from all tools
        wafer skill uninstall -t claude    # Uninstall from Claude Code only
        wafer skill uninstall -t cursor    # Uninstall from Cursor only
    """
    targets_to_uninstall: list[tuple[str, Path]] = []

    if target in ("all", "claude"):
        targets_to_uninstall.append((
            "Claude Code",
            Path.home() / ".claude" / "skills" / "wafer-guide",
        ))
    if target in ("all", "codex"):
        targets_to_uninstall.append((
            "Codex CLI",
            Path.home() / ".codex" / "skills" / "wafer-guide",
        ))
    if target in ("all", "cursor"):
        targets_to_uninstall.append((
            "Cursor",
            Path.home() / ".cursor" / "skills" / "wafer-guide",
        ))

    if not targets_to_uninstall:
        typer.echo(
            f"Error: Unknown target '{target}'. Use: claude, codex, cursor, or all", err=True
        )
        raise typer.Exit(1)

    for tool_name, dest_path in targets_to_uninstall:
        if not dest_path.exists():
            typer.echo(f"  {tool_name}: Not installed")
            continue

        if dest_path.is_symlink():
            dest_path.unlink()
        else:
            import shutil

            shutil.rmtree(dest_path)
        typer.echo(f"  {tool_name}: Uninstalled from {dest_path}")


@skill_app.command("status")
def skill_status() -> None:
    """Show installation status of the wafer-guide skill.

    Examples:
        wafer skill status
    """
    skill_source = Path(__file__).parent / "skills" / "wafer-guide"

    typer.echo("Wafer Skill Status")
    typer.echo("=" * 40)
    typer.echo(f"Bundled skill: {skill_source}")
    typer.echo(f"  Exists: {skill_source.exists()}")
    typer.echo("")

    installations = [
        ("Claude Code", Path.home() / ".claude" / "skills" / "wafer-guide"),
        ("Codex CLI", Path.home() / ".codex" / "skills" / "wafer-guide"),
        ("Cursor", Path.home() / ".cursor" / "skills" / "wafer-guide"),
    ]

    for tool_name, path in installations:
        if path.exists():
            if path.is_symlink():
                target = path.resolve()
                typer.echo(f"{tool_name}: Installed (symlink -> {target})")
            else:
                typer.echo(f"{tool_name}: Installed (copy at {path})")
        else:
            typer.echo(f"{tool_name}: Not installed")


# =============================================================================
# Provider auth management (wafer auth ...)
# =============================================================================

provider_auth_app = typer.Typer(help="Manage API keys for cloud GPU providers")
app.add_typer(provider_auth_app, name="auth")


@provider_auth_app.command("login")
def provider_auth_login(
    provider: str = typer.Argument(
        ...,
        help="Provider name: runpod, digitalocean, modal, anthropic, or openai",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key (if not provided, reads from stdin)",
    ),
) -> None:
    """Save API key for a provider.

    Stores the key in ~/.wafer/auth.json. Environment variables
    (e.g., ANTHROPIC_API_KEY) take precedence over stored keys.

    Examples:
        wafer auth login anthropic --api-key sk-ant-xxx
        wafer auth login runpod --api-key rp_xxx
        wafer auth login openai --api-key sk-xxx
        echo $API_KEY | wafer auth login anthropic
    """
    import sys

    from wafer_core.auth import PROVIDERS, save_api_key

    # Validate provider
    if provider not in PROVIDERS:
        typer.echo(f"Error: Unknown provider '{provider}'", err=True)
        typer.echo(f"Valid providers: {', '.join(PROVIDERS.keys())}", err=True)
        raise typer.Exit(1)

    # Get API key from option or stdin
    if api_key is None:
        if sys.stdin.isatty():
            typer.echo(f"Enter API key for {PROVIDERS[provider]['display_name']}:")
            api_key = typer.prompt("API key", hide_input=True)
        else:
            api_key = sys.stdin.read().strip()

    if not api_key:
        typer.echo("Error: No API key provided", err=True)
        raise typer.Exit(1)

    # Save the key
    save_api_key(provider, api_key)
    typer.echo(f"API key saved for {PROVIDERS[provider]['display_name']}")
    typer.echo("Stored in: ~/.wafer/auth.json")


@provider_auth_app.command("logout")
def provider_auth_logout(
    provider: str = typer.Argument(
        ...,
        help="Provider name: runpod, digitalocean, modal, anthropic, or openai",
    ),
) -> None:
    """Remove stored API key for a cloud GPU provider.

    Examples:
        wafer auth logout runpod
        wafer auth logout digitalocean
    """
    from wafer_core.auth import PROVIDERS, remove_api_key

    # Validate provider
    if provider not in PROVIDERS:
        typer.echo(f"Error: Unknown provider '{provider}'", err=True)
        typer.echo(f"Valid providers: {', '.join(PROVIDERS.keys())}", err=True)
        raise typer.Exit(1)

    if remove_api_key(provider):
        typer.echo(f"API key removed for {PROVIDERS[provider]['display_name']}")
    else:
        typer.echo(f"No stored API key found for {PROVIDERS[provider]['display_name']}")


@provider_auth_app.command("status")
def provider_auth_status() -> None:
    """Show authentication status for all cloud GPU providers.

    Displays which providers have API keys configured and where
    the keys are coming from (environment variable or auth.json).

    Example:
        wafer auth status
    """
    from wafer_core.auth import get_all_auth_status

    statuses = get_all_auth_status()

    typer.echo("Cloud GPU Provider Authentication Status")
    typer.echo("=" * 45)

    for status in statuses:
        if status.is_authenticated:
            source_str = f"({status.source})" if status.source else ""
            typer.echo(f"  {status.display_name}: ✓ {status.key_preview} {source_str}")
        else:
            typer.echo(f"  {status.display_name}: ✗ Not configured")
            typer.echo(f"      Run: wafer auth login {status.provider}")
            typer.echo(f"      Or set: {status.key_url}")

    typer.echo("")
    typer.echo("Note: Environment variables take precedence over stored keys.")


@app.command(hidden=True)
def run(
    command: str = typer.Argument(..., help="Command to run in Docker container"),
    env: str | None = typer.Option(None, "--env", "-e", help="Environment name from config"),
    upload: list[str] | None = typer.Option(  # noqa: B008
        None, "--upload", "-u", help="Files to upload (default: auto-infer)"
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Override target from config",
        autocompletion=complete_target_name,
    ),
    follow: bool = typer.Option(True, "--follow/--no-follow", help="Stream output in real-time"),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run in background, return job ID"),
) -> None:
    """Run command on remote GPU in Docker container.

    Examples:
        # Run with auto-inferred files and default environment
        wafer run "make && ./kernel_test"

        # Specify environment
        wafer run "python train.py" --env pytorch

        # Override target
        wafer run "nvcc kernel.cu -o kernel && ./kernel" --target root@other-node:22

        # Upload specific files
        wafer run "make" --upload kernel.cu --upload Makefile

        # Run in background
        wafer run "python train.py --epochs 100" --detach
    """
    # Load config
    config_path = Path.home() / ".wafer" / "config.toml"
    if not config_path.exists():
        typer.echo(f"Error: Config not found: {config_path}", err=True)
        typer.echo(
            "Create ~/.wafer/config.toml with your settings. See documentation for format.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        config = WaferConfig.from_toml(config_path)
    except (AssertionError, ValueError, KeyError) as e:
        typer.echo(f"Error: Invalid config: {e}", err=True)
        raise typer.Exit(1) from None

    # Resolve environment
    try:
        environment = resolve_environment(config, env)
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Determine files to upload
    cwd = Path.cwd()
    if upload:
        files_to_upload = [cwd / f for f in upload]
        # Validate files exist
        for f in files_to_upload:
            if not f.exists():
                typer.echo(f"Error: File not found: {f}", err=True)
                raise typer.Exit(1)
            if not f.is_file():
                typer.echo(f"Error: Not a file: {f}", err=True)
                raise typer.Exit(1)
    else:
        try:
            files_to_upload = infer_upload_files(command, cwd)
        except (AssertionError, ValueError) as e:
            typer.echo(f"Error: Failed to infer files: {e}", err=True)
            raise typer.Exit(1) from None

    # Use target override if provided
    effective_target = target or config.target

    # Run async implementation
    try:
        trio.run(
            _run_async,
            effective_target,
            config.ssh_key,
            environment,
            command,
            files_to_upload,
            follow,
            detach,
        )
    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(130) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


async def _run_async(
    target: str,
    ssh_key: str,
    environment: WaferEnvironment,
    command: str,
    files_to_upload: list[Path],
    follow: bool,
    detach: bool,
) -> None:
    """Async wrapper for run command (runs sync SSH client in thread).

    Args:
        target: SSH target string (user@host:port)
        ssh_key: Path to SSH key
        environment: Environment configuration with Docker image
        command: Command to execute
        files_to_upload: List of files to upload
        follow: Whether to stream output
        detach: Whether to run in background

    Raises:
        Exception: On any execution failure
    """
    import trio

    await trio.to_thread.run_sync(
        lambda: _run_sync(target, ssh_key, environment, command, files_to_upload, follow, detach)
    )


def _run_sync(
    target: str,
    ssh_key: str,
    environment: WaferEnvironment,
    command: str,
    files_to_upload: list[Path],
    follow: bool,
    detach: bool,
) -> None:
    """Sync implementation of run command using internal SSHClient.

    Args:
        target: SSH target string (user@host:port)
        ssh_key: Path to SSH key
        environment: Environment configuration with Docker image
        command: Command to execute
        files_to_upload: List of files to upload
        follow: Whether to stream output
        detach: Whether to run in background

    Raises:
        Exception: On any execution failure
    """

    from wafer_core.ssh import SSHClient

    workspace_name = Path.cwd().name
    remote_workspace = f"~/.wafer/workspaces/{workspace_name}"

    client = SSHClient(target, ssh_key)

    # Ensure workspace directory exists
    print(f"Setting up workspace: {remote_workspace}")
    client.exec(f"mkdir -p {remote_workspace}")

    # Upload files
    if files_to_upload:
        print(f"Uploading {len(files_to_upload)} files...")
        for f in files_to_upload:
            remote_path = f"{remote_workspace}/{f.name}"
            client.upload_files(str(f), remote_path)
            print(f"  ✓ {f.name}")
    else:
        print("No files to upload (use --upload to specify)")

    # Expand workspace path for volume mount
    expanded_workspace = client.expand_path(remote_workspace)

    print(f"\nEnvironment: {environment.docker}")
    if environment.description:
        print(f"Description: {environment.description}")
    print(f"Command: {command}")
    print("-" * 60)

    # Check if Docker is available
    docker_check = client.exec("which docker")
    if docker_check.exit_code != 0:
        raise RuntimeError(
            "Docker not found on remote machine. Please install Docker with GPU support."
        )

    # Build docker command
    docker_cmd = _build_docker_run_cmd(
        image=environment.docker,
        inner_cmd=command,
        volumes={expanded_workspace: "/workspace"},
        working_dir="/workspace",
    )

    # Execute
    if follow and not detach:
        # Stream output in real-time
        try:
            for line in client.exec_stream(docker_cmd):
                print(line)
        except Exception as e:
            print(f"\nExecution failed: {e}", file=sys.stderr)
            raise
    else:
        # Non-streaming execution
        result = client.exec(docker_cmd)

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check exit code
        if result.exit_code != 0:
            print(
                f"\nCommand exited with code {result.exit_code}",
                file=sys.stderr,
            )
            raise typer.Exit(result.exit_code)


def _build_docker_run_cmd(
    image: str,
    inner_cmd: str,
    volumes: dict[str, str],
    working_dir: str,
    gpu_id: int = 0,
) -> str:
    """Build docker run command string."""
    import shlex

    parts = ["docker", "run", "--rm"]
    parts.extend(["--gpus", f"'device={gpu_id}'"])

    for host_path, container_path in volumes.items():
        parts.extend(["-v", f"{host_path}:{container_path}"])

    parts.extend(["-w", working_dir])
    parts.append(image)
    parts.append(f"bash -c {shlex.quote(inner_cmd)}")

    return " ".join(parts)


@app.command(hidden=True)
def status(job_id: str = typer.Argument(..., help="Job ID to check")) -> None:
    """Get status of a running job."""
    # TODO: Implement in Phase 3
    typer.echo(f"Status for job {job_id}: not yet implemented")
    typer.echo("Job persistence will be added in Phase 3")


@app.command(hidden=True)
def logs(
    job_id: str = typer.Argument(..., help="Job ID"),
    follow_logs: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """Get logs from a job."""
    # TODO: Implement in Phase 3
    typer.echo(f"Logs for job {job_id}: not yet implemented")
    typer.echo("Job persistence will be added in Phase 3")


@app.command(hidden=True)
def kill(job_id: str = typer.Argument(..., help="Job ID to kill")) -> None:
    """Kill a running job."""
    # TODO: Implement in Phase 3
    typer.echo(f"Kill job {job_id}: not yet implemented")
    typer.echo("Job persistence will be added in Phase 3")


# =============================================================================
# Config commands (wafer config ...)
# =============================================================================


@config_app.command("init")
def config_init(
    environment: str = typer.Option(
        "prod",
        "--env",
        "-e",
        help="Initial API environment (staging, prod, local)",
    ),
) -> None:
    """Initialize config file with defaults.

    Creates ~/.wafer/config.toml with the specified environment.

    Examples:
        wafer config init                  # use prod environment
        wafer config init --env staging    # use staging environment
    """
    from .global_config import (
        BUILTIN_ENVIRONMENTS,
        CONFIG_FILE,
        init_config,
    )

    if environment not in BUILTIN_ENVIRONMENTS:
        typer.echo(
            f"Error: Unknown environment '{environment}'. "
            f"Available: {', '.join(BUILTIN_ENVIRONMENTS.keys())}",
            err=True,
        )
        raise typer.Exit(1)

    if CONFIG_FILE.exists():
        typer.echo(f"Config already exists: {CONFIG_FILE}")
        typer.echo("Use 'wafer config set' to modify settings.")
        raise typer.Exit(1)

    config = init_config(environment)
    env = config.get_api_environment()
    typer.echo(f"Created {CONFIG_FILE}")
    typer.echo(f"Environment: {environment}")
    typer.echo(f"API URL: {env.api_url}")


@config_app.command("show")
def config_show_new() -> None:
    """Show current configuration.

    Displays both API configuration (environment, URLs) and
    Docker execution configuration (targets, environments).
    """
    from .global_config import CONFIG_FILE, load_global_config

    # Show global/API config
    typer.echo("=== API Configuration ===")
    try:
        global_cfg = load_global_config()
        env = global_cfg.get_api_environment()
        typer.echo(f"Environment: {global_cfg.environment}")
        typer.echo(f"API URL: {env.api_url}")
        typer.echo(f"Supabase URL: {env.supabase_url}")
        typer.echo(f"Mode: {global_cfg.preferences.mode}")
        if global_cfg.defaults.workspace:
            typer.echo(f"Default workspace: {global_cfg.defaults.workspace}")
        typer.echo(f"Default GPU: {global_cfg.defaults.gpu}")
        typer.echo(f"Exec timeout: {global_cfg.defaults.exec_timeout}s")
        if not CONFIG_FILE.exists():
            typer.echo("(using built-in defaults, run 'wafer config init' to create config file)")
    except Exception as e:
        typer.echo(f"Error loading global config: {e}", err=True)

    # Show Docker execution config (original config.toml behavior)
    typer.echo("\n=== Docker Execution Configuration ===")
    config_path = Path.home() / ".wafer" / "config.toml"
    if not config_path.exists():
        typer.echo("(no Docker config - only needed for 'wafer run' command)")
        return

    try:
        config = WaferConfig.from_toml(config_path)
        typer.echo(f"Target: {config.target}")
        typer.echo(f"SSH Key: {config.ssh_key}")
        typer.echo(f"Default Environment: {config.default_environment or '(none)'}")
        typer.echo("\nDocker Environments:")
        for name, env in config.environments.items():
            typer.echo(f"  {name}:")
            typer.echo(f"    Docker: {env.docker}")
            if env.description:
                typer.echo(f"    Description: {env.description}")
    except Exception as e:
        typer.echo(f"(Docker config parse error: {e})", err=True)


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (e.g., api.environment, defaults.workspace)"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a configuration value.

    Examples:
        wafer config set api.environment staging
        wafer config set defaults.workspace dev
        wafer config set defaults.exec_timeout 600
        wafer config set preferences.mode implicit
    """
    from dataclasses import replace

    from .global_config import (
        CONFIG_FILE,
        GlobalConfig,
        clear_config_cache,
        load_global_config,
        save_global_config,
    )

    # Load existing config or create new
    if CONFIG_FILE.exists():
        config = load_global_config()
    else:
        config = GlobalConfig()

    # Parse and apply the setting
    parts = key.split(".")
    if len(parts) != 2:
        typer.echo(f"Error: Invalid key format '{key}'. Use 'section.key' format.", err=True)
        typer.echo("Examples: api.environment, defaults.workspace, preferences.mode", err=True)
        raise typer.Exit(1)

    section, field = parts

    if section == "api":
        if field == "environment":
            if value not in config.environments:
                typer.echo(
                    f"Error: Unknown environment '{value}'. "
                    f"Available: {', '.join(config.environments.keys())}",
                    err=True,
                )
                raise typer.Exit(1)
            config = replace(config, environment=value)
        else:
            typer.echo(f"Error: Unknown api field '{field}'. Available: environment", err=True)
            raise typer.Exit(1)

    elif section == "defaults":
        if field == "workspace":
            new_defaults = replace(config.defaults, workspace=value if value else None)
            config = replace(config, defaults=new_defaults)
        elif field == "gpu":
            new_defaults = replace(config.defaults, gpu=value)
            config = replace(config, defaults=new_defaults)
        elif field == "exec_timeout":
            try:
                timeout = int(value)
                assert timeout > 0, "timeout must be positive"
            except (ValueError, AssertionError) as e:
                typer.echo(f"Error: exec_timeout must be a positive integer: {e}", err=True)
                raise typer.Exit(1) from None
            new_defaults = replace(config.defaults, exec_timeout=timeout)
            config = replace(config, defaults=new_defaults)
        else:
            typer.echo(
                f"Error: Unknown defaults field '{field}'. Available: workspace, gpu, exec_timeout",
                err=True,
            )
            raise typer.Exit(1)

    elif section == "preferences":
        if field == "mode":
            if value not in ("explicit", "implicit"):
                typer.echo(
                    f"Error: mode must be 'explicit' or 'implicit', got '{value}'",
                    err=True,
                )
                raise typer.Exit(1)
            new_prefs = replace(config.preferences, mode=value)
            config = replace(config, preferences=new_prefs)
        else:
            typer.echo(f"Error: Unknown preferences field '{field}'. Available: mode", err=True)
            raise typer.Exit(1)

    else:
        typer.echo(
            f"Error: Unknown section '{section}'. Available: api, defaults, preferences",
            err=True,
        )
        raise typer.Exit(1)

    # Save and clear cache
    save_global_config(config)
    clear_config_cache()
    typer.echo(f"Set {key} = {value}")


@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key to get (e.g., api.environment)"),
) -> None:
    """Get a configuration value.

    Examples:
        wafer config get api.environment
        wafer config get defaults.workspace
    """
    from .global_config import load_global_config

    config = load_global_config()

    parts = key.split(".")
    if len(parts) != 2:
        typer.echo(f"Error: Invalid key format '{key}'. Use 'section.key' format.", err=True)
        raise typer.Exit(1)

    section, field = parts

    if section == "api":
        if field == "environment":
            typer.echo(config.environment)
        elif field == "url":
            typer.echo(config.api_url)
        elif field == "supabase_url":
            typer.echo(config.supabase_url)
        else:
            typer.echo(f"Error: Unknown api field '{field}'", err=True)
            raise typer.Exit(1)

    elif section == "defaults":
        if field == "workspace":
            typer.echo(config.defaults.workspace or "")
        elif field == "gpu":
            typer.echo(config.defaults.gpu)
        elif field == "exec_timeout":
            typer.echo(str(config.defaults.exec_timeout))
        else:
            typer.echo(f"Error: Unknown defaults field '{field}'", err=True)
            raise typer.Exit(1)

    elif section == "preferences":
        if field == "mode":
            typer.echo(config.preferences.mode)
        else:
            typer.echo(f"Error: Unknown preferences field '{field}'", err=True)
            raise typer.Exit(1)

    else:
        typer.echo(f"Error: Unknown section '{section}'", err=True)
        raise typer.Exit(1)


# Keep old config-show as alias for backwards compatibility
@app.command("config-show", hidden=True)
def config_show_legacy() -> None:
    """Show current configuration (deprecated, use 'wafer config show')."""
    config_show_new()


@app.command()
def agent(  # noqa: PLR0913
    prompt: str | None = typer.Argument(
        None,
        help="Prompt to send (reads from stdin if not provided and not interactive)",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Launch full interactive TUI mode (default when no prompt given)",
    ),
    simple: bool = typer.Option(
        False,
        "--simple",
        help="Use simple stdout mode instead of TUI (for scripts/pipes)",
    ),
    single_turn: bool | None = typer.Option(
        None,
        "--single-turn",
        "-s",
        is_flag=True,
        flag_value=True,
        help="Single-turn mode: answer once and exit",
    ),
    resume: str | None = typer.Option(
        None,
        "--resume",
        "-r",
        help="Resume session by ID (or 'last' for most recent)",
    ),
    from_turn: int | None = typer.Option(
        None,
        "--from-turn",
        help="Branch from specific turn (default: resume from end)",
    ),
    list_sessions: bool = typer.Option(
        False,
        "--list-sessions",
        help="List recent sessions and exit",
    ),
    get_session: str | None = typer.Option(
        None,
        "--get-session",
        help="Get session by ID and print messages (use with --json)",
    ),
    tools: str | None = typer.Option(
        None,
        "--tools",
        help="Comma-separated list of tools to enable (default: all)",
    ),
    allow_spawn: bool = typer.Option(
        False,
        "--allow-spawn",
        help="Allow wafer tool to spawn sub-wevin agents (blocked by default)",
    ),
    max_tool_fails: int | None = typer.Option(
        None,
        "--max-tool-fails",
        help="Exit after N consecutive tool failures",
    ),
    max_turns: int | None = typer.Option(
        None,
        "--max-turns",
        help="Max conversation turns (default: 10)",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model override (default: claude-opus-4-5)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format (stream-json style)",
    ),
    template: str | None = typer.Option(
        None,
        "--template",
        "-t",
        help="Run with template (ask-docs, trace-analyze, optimize-kernel)",
    ),
    template_args: list[str] | None = typer.Option(
        None,
        "--args",
        help="Template variable (KEY=VALUE, can be repeated)",
    ),
    corpus: str | None = typer.Option(
        None,
        "--corpus",
        "-c",
        help="Documentation corpus to use (cuda, cutlass, hip, amd). Must be downloaded first.",
    ),
    no_sandbox: bool = typer.Option(
        False,
        "--no-sandbox",
        help="Disable OS-level sandboxing (YOU accept liability for any damage caused by the agent)",
    ),
    no_proxy: bool = typer.Option(
        False,
        "--no-proxy",
        help="Skip wafer proxy, use ANTHROPIC_API_KEY directly",
    ),
) -> None:
    """AI assistant for GPU kernel development.

    Helps with CUDA/Triton kernel optimization, GPU documentation queries,
    and performance analysis. Can read files, search docs, and run evaluations.

    Launches interactive TUI by default. Use --simple for stdout-only mode.

    Examples:
        # Interactive TUI (default)
        wafer agent

        # Ask a question (TUI with initial prompt)
        wafer agent "What is TMEM in CuTeDSL?"

        # Single-turn (answer and exit)
        wafer agent -s "What is TMEM in CuTeDSL?"

        # Simple mode for scripts/pipes
        cat kernel.py | wafer agent --simple -s "optimize this kernel"

        # Query GPU docs
        wafer agent -t ask-docs --corpus cuda "What causes bank conflicts?"

        # Resume a session
        wafer agent --resume last "follow up question"
    """
    from wafer.wevin_cli import main as wevin_main

    # Read from stdin if piped (non-TTY)
    actual_prompt = prompt
    stdin_input = None
    if not sys.stdin.isatty():
        stdin_input = sys.stdin.read().strip()
        if stdin_input and not actual_prompt:
            actual_prompt = stdin_input

    # Determine if we should use TUI:
    # - Default to TUI when both stdin and stdout are TTYs
    # - Use simple mode when: --simple flag, piped input/output, or --json
    has_tty = sys.stdin.isatty() and sys.stdout.isatty()
    use_tui = has_tty and not simple and not json_output

    # If user explicitly asked for -i, try TUI but warn if no TTY
    if interactive:
        if not has_tty:
            print("Warning: --interactive requires a TTY, using simple mode", file=sys.stderr)
        else:
            use_tui = True

    # Parse template args
    parsed_template_args: dict[str, str] | None = None
    if template_args:
        parsed_template_args = {}
        for arg in template_args:
            if "=" not in arg:
                typer.echo(f"Invalid --args format: {arg!r}. Use KEY=VALUE", err=True)
                raise typer.Exit(1)
            key, value = arg.split("=", 1)
            # Expand ~ to home directory in values (common for file paths)
            parsed_template_args[key] = os.path.expanduser(value)

    # Validate corpus if provided, auto-download if missing
    corpus_path: str | None = None
    if corpus:
        from wafer.corpus import CORPORA, download_corpus, get_corpus_path

        if corpus not in CORPORA:
            typer.echo(f"Unknown corpus: {corpus}", err=True)
            typer.echo(f"Available: {', '.join(CORPORA.keys())}", err=True)
            raise typer.Exit(1)
        path = get_corpus_path(corpus)  # type: ignore[arg-type]
        if path is None:
            typer.echo(f"Corpus '{corpus}' not downloaded. Downloading...", err=True)
            try:
                path = download_corpus(corpus)  # type: ignore[arg-type]
            except Exception as e:
                typer.echo(f"Failed to download corpus: {e}", err=True)
                raise typer.Exit(1) from None
        corpus_path = str(path)

    # Warn user about sandbox disabled
    if no_sandbox:
        print(
            "Warning: Sandbox disabled. You accept liability for any damage caused by the agent.",
            file=sys.stderr,
        )

    wevin_main(
        prompt=actual_prompt,
        interactive=use_tui,
        single_turn=single_turn,
        model=model,
        resume=resume,
        from_turn=from_turn,
        list_sessions=list_sessions,
        get_session=get_session,
        tools=tools.split(",") if tools else None,
        allow_spawn=allow_spawn,
        max_tool_fails=max_tool_fails,
        max_turns=max_turns,
        json_output=json_output,
        template=template,
        template_args=parsed_template_args,
        corpus_path=corpus_path,
        no_sandbox=no_sandbox,
        no_proxy=no_proxy,
    )


# =============================================================================
# Evaluate command
# Hidden aliases for agent command
def _make_agent_alias(name: str, doc: str) -> None:
    """Create a hidden alias that delegates to agent()."""

    @app.command(name=name, hidden=True)
    def alias_cmd(
        prompt: str | None = typer.Argument(None),
        interactive: bool = typer.Option(False, "--interactive", "-i"),
        simple: bool = typer.Option(False, "--simple"),
        single_turn: bool | None = typer.Option(
            None, "--single-turn", "-s", is_flag=True, flag_value=True
        ),
        resume: str | None = typer.Option(None, "--resume", "-r"),
        from_turn: int | None = typer.Option(None, "--from-turn"),
        list_sessions: bool = typer.Option(False, "--list-sessions"),
        get_session: str | None = typer.Option(None, "--get-session"),
        tools: str | None = typer.Option(None, "--tools"),
        allow_spawn: bool = typer.Option(False, "--allow-spawn"),
        max_tool_fails: int | None = typer.Option(None, "--max-tool-fails"),
        max_turns: int | None = typer.Option(None, "--max-turns"),
        model: str | None = typer.Option(None, "--model", "-m"),
        json_output: bool = typer.Option(False, "--json"),
        template: str | None = typer.Option(None, "--template", "-t"),
        template_args: list[str] | None = typer.Option(None, "--args"),
        corpus: str | None = typer.Option(None, "--corpus"),
        no_sandbox: bool = typer.Option(False, "--no-sandbox"),
        no_proxy: bool = typer.Option(False, "--no-proxy"),
    ) -> None:
        agent(
            prompt=prompt,
            interactive=interactive,
            simple=simple,
            single_turn=single_turn,
            resume=resume,
            from_turn=from_turn,
            list_sessions=list_sessions,
            get_session=get_session,
            tools=tools,
            allow_spawn=allow_spawn,
            max_tool_fails=max_tool_fails,
            max_turns=max_turns,
            model=model,
            json_output=json_output,
            template=template,
            template_args=template_args,
            corpus=corpus,
            no_sandbox=no_sandbox,
            no_proxy=no_proxy,
        )

    alias_cmd.__doc__ = doc
    return alias_cmd


_make_agent_alias("wanda", "Alias for 'wafer agent'.")
_make_agent_alias("wevin", "Alias for 'wafer agent'.")


# =============================================================================


@evaluate_app.callback(invoke_without_command=True)
def evaluate(  # noqa: PLR0913
    ctx: typer.Context,
    implementation: Path | None = typer.Option(
        None, "--impl", "-i", help="Path to implementation kernel file"
    ),
    reference: Path | None = typer.Option(
        None, "--reference", help="Path to reference kernel file"
    ),
    test_cases: Path | None = typer.Option(
        None, "--test-cases", help="Path to test cases JSON file"
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="GPU target name. See 'wafer config targets list' for available targets.",
        autocompletion=complete_target_name,
    ),
    benchmark: bool = typer.Option(False, "--benchmark", help="Run performance benchmarks"),
    profile: bool = typer.Option(False, "--profile", help="Enable profiling"),
    defensive: bool = typer.Option(
        False, "--defensive", help="Enable defensive timing to detect evaluation hacking"
    ),
    sync_artifacts: bool = typer.Option(
        True, "--sync-artifacts/--no-sync-artifacts", help="Download artifacts"
    ),
    gpu_id: int | None = typer.Option(None, "--gpu-id", help="Override GPU ID"),
) -> None:
    """Run kernel evaluation on a remote GPU target.

    Uses the functional format: custom_kernel(inputs) and ref_kernel(inputs).

    The evaluation checks:
      1. Correctness: Does the kernel produce the same output as the reference?
      2. Performance (--benchmark): How fast is it compared to the reference?
      3. Defense (--defensive): Detects evaluation hacking (stream injection, etc.)

    Examples:
        # Basic correctness check
        wafer evaluate --impl kernel.py --reference ref.py --test-cases tests.json

        # With benchmarking on a specific target
        wafer evaluate --impl kernel.py --reference ref.py --test-cases tests.json \\
            --target vultr-b200 --benchmark

        # Full evaluation with defensive timing (detects cheating)
        wafer evaluate --impl kernel.py --reference ref.py --test-cases tests.json \\
            --benchmark --defensive

    Subcommands:
        gpumode        Use GPUMode format (functional) - RECOMMENDED
        kernelbench    Use KernelBench format (ModelNew class)
        make-template  Generate template files for this format (deprecated)
    """
    # If a subcommand is being invoked, skip the main evaluation logic
    if ctx.invoked_subcommand is not None:
        return

    # Bare 'wafer evaluate' is no longer supported - must use subcommand
    typer.echo("Error: 'wafer evaluate' requires a subcommand.", err=True)
    typer.echo("", err=True)
    typer.echo("Available subcommands:", err=True)
    typer.echo(
        "  gpumode      Evaluate GPUMode format (custom_kernel/ref_kernel functions)", err=True
    )
    typer.echo("  kernelbench  Evaluate KernelBench format (ModelNew class)", err=True)
    typer.echo("", err=True)
    typer.echo("Examples:", err=True)
    typer.echo(
        "  wafer evaluate gpumode --impl kernel.py --reference ref.py --test-cases tests.json",
        err=True,
    )
    typer.echo(
        "  wafer evaluate kernelbench --impl impl.py --reference ref.py --benchmark", err=True
    )
    typer.echo("", err=True)
    typer.echo(
        "Run 'wafer evaluate gpumode --help' or 'wafer evaluate kernelbench --help' for options.",
        err=True,
    )
    raise typer.Exit(1)


TEMPLATE_KERNEL = '''\
import torch
import triton
import triton.language as tl


@triton.jit
def add_kernel(x_ptr, y_ptr, output_ptr, n_elements, BLOCK_SIZE: tl.constexpr):
    """Triton kernel for element-wise addition."""
    pid = tl.program_id(0)
    offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask)
    y = tl.load(y_ptr + offsets, mask=mask)
    tl.store(output_ptr + offsets, x + y, mask=mask)


def custom_kernel(inputs: tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
    """Your optimized kernel implementation.

    Args:
        inputs: Tuple from generate_input() - passed as single argument

    Returns:
        Output tensor matching ref_kernel output
    """
    x, y = inputs  # Unpack the input tuple
    output = torch.empty_like(x)
    n_elements = x.numel()
    grid = lambda meta: (triton.cdiv(n_elements, meta["BLOCK_SIZE"]),)
    add_kernel[grid](x, y, output, n_elements, BLOCK_SIZE=1024)
    return output
'''

TEMPLATE_REFERENCE = '''\
import torch


def ref_kernel(inputs: tuple[torch.Tensor, torch.Tensor]) -> torch.Tensor:
    """Ground truth implementation.

    Args:
        inputs: Tuple from generate_input() - passed as single argument

    Returns:
        Expected output tensor
    """
    x, y = inputs  # Unpack the input tuple
    return x + y


def generate_input(n: int, seed: int = 42, **kwargs) -> tuple[torch.Tensor, torch.Tensor]:
    """Generate test inputs based on test case parameters.

    Called with params from test_cases.json. The returned tuple is passed
    as a single argument to both ref_kernel and custom_kernel.

    Args:
        n: Size of tensors (from test case)
        seed: Random seed for reproducibility
        **kwargs: Any other params from test case

    Returns:
        Tuple of inputs (passed as single arg to kernels)
    """
    torch.manual_seed(seed)
    x = torch.randn(n, device="cuda", dtype=torch.float32)
    y = torch.randn(n, device="cuda", dtype=torch.float32)
    return (x, y)
'''

TEMPLATE_TEST_CASES = """\
[
  {"name": "small", "n": 1024, "seed": 42},
  {"name": "medium", "n": 65536, "seed": 42},
  {"name": "large", "n": 1048576, "seed": 42}
]
"""


@evaluate_app.command("make-template")
def evaluate_make_template(
    output_dir: Path = typer.Argument(
        Path("."),
        help="Directory to write template files (default: current directory)",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Generate template files for wafer evaluate (functional format).

    Creates three files:
    - kernel.py: Implementation template with custom_kernel
    - reference.py: Reference template with ref_kernel and generate_input
    - test_cases.json: Test case parameters

    Examples:
        wafer evaluate make-template                # Write to current directory
        wafer evaluate make-template ./my-kernel    # Write to specific directory
        wafer evaluate make-template --force        # Overwrite existing files
    """
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = [
        ("kernel.py", TEMPLATE_KERNEL),
        ("reference.py", TEMPLATE_REFERENCE),
        ("test_cases.json", TEMPLATE_TEST_CASES),
    ]

    for filename, content in files:
        path = output_dir / filename
        if path.exists() and not force:
            typer.echo(f"Skipping {path} (already exists, use --force to overwrite)")
            continue
        path.write_text(content)
        typer.echo(f"Created {path}")

    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(f"  1. Edit {output_dir / 'kernel.py'} with your optimized implementation")
    typer.echo(f"  2. Edit {output_dir / 'reference.py'} with the ground truth + input generator")
    typer.echo(f"  3. Edit {output_dir / 'test_cases.json'} with your test parameters")
    typer.echo("  4. Run:")
    typer.echo(f"     wafer evaluate --impl {output_dir / 'kernel.py'} \\")
    typer.echo(f"         --reference {output_dir / 'reference.py'} \\")
    typer.echo(f"         --test-cases {output_dir / 'test_cases.json'} --benchmark")


# =============================================================================
# KernelBench format evaluation
# =============================================================================


def _get_kernelbench_root() -> Path | None:
    """Get KernelBench problems root, preferring downloaded location."""
    # First check downloaded location
    downloaded = get_problems_path("kernelbench")
    if downloaded is not None:
        kb_root = downloaded / "KernelBench"
        if kb_root.exists():
            return kb_root
        return downloaded

    # Fall back to legacy location (for development)
    legacy = Path(__file__).parent.parent.parent.parent / "research" / "KernelBench" / "KernelBench"
    if legacy.exists():
        return legacy

    return None


@kernelbench_app.command("download")
def kernelbench_download(
    force: bool = typer.Option(False, "--force", "-f", help="Re-download even if exists"),
) -> None:
    """Download KernelBench problems from GitHub.

    Downloads the problem set to ~/.cache/wafer/problems/kernelbench/

    Examples:
        wafer evaluate kernelbench download
        wafer evaluate kernelbench download --force  # Re-download
    """
    try:
        path = download_problems("kernelbench", force=force, verbose=True)
        typer.echo("")
        typer.echo(f"Problems available at: {path}")
        typer.echo("Run 'wafer evaluate kernelbench list-problems' to see available problems.")
    except Exception as e:
        typer.echo(f"Error downloading problems: {e}", err=True)
        raise typer.Exit(1) from None


@kernelbench_app.command("list-problems")
def kernelbench_list_problems() -> None:
    """List available KernelBench problems.

    Examples:
        wafer evaluate kernelbench list-problems
    """
    try:
        list_problems_fn("kernelbench", verbose=True)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None


@kernelbench_app.callback(invoke_without_command=True)
def kernelbench_evaluate(  # noqa: PLR0913, PLR0915
    ctx: typer.Context,
    implementation: Path | None = typer.Option(
        None,
        "--implementation",
        "--impl",
        help="Path to implementation file (must define ModelNew)",
    ),
    reference: Path | None = typer.Option(
        None,
        "--reference",
        help="Path to reference file (must define Model, get_inputs, get_init_inputs)",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="GPU target name. See 'wafer config targets list' for available targets.",
        autocompletion=complete_target_name,
    ),
    pool: str | None = typer.Option(
        None,
        "--pool",
        "-p",
        help="Target pool name. Acquires first available target from the pool. "
        "Define pools in ~/.wafer/config.toml under [pools.<name>].",
    ),
    benchmark: bool = typer.Option(False, "--benchmark", help="Run performance benchmarks"),
    profile: bool = typer.Option(False, "--profile", help="Enable profiling"),
    inputs: Path | None = typer.Option(
        None, "--inputs", help="Custom inputs file to override get_inputs()"
    ),
    seed: int = typer.Option(42, "--seed", help="Random seed for weight initialization"),
    defensive: bool = typer.Option(
        False, "--defensive", help="Enable defensive timing to detect evaluation hacking"
    ),
    backend: str | None = typer.Option(
        None,
        "--backend",
        help="Kernel backend for static validation (hip, cuda, triton, cute, tilelang, thunderkittens). "
        "When specified, validates that the implementation uses the correct backend primitives.",
    ),
    sync_artifacts: bool = typer.Option(
        True, "--sync-artifacts/--no-sync-artifacts", help="Download artifacts"
    ),
    gpu_id: int | None = typer.Option(None, "--gpu-id", help="Override GPU ID"),
    stages: str = typer.Option(
        "compile,correctness",
        "--stages",
        help="Comma-separated stages to run: compile, correctness, benchmark, defense. "
        "Use 'all' for compile,correctness,benchmark,defense. Default: compile,correctness",
    ),
    prepare_only: bool = typer.Option(
        False,
        "--prepare-only",
        help="Sync files and generate eval script but don't run. "
        "Prints the command to run manually (useful for wrapping with rocprof, etc.)",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output as single JSON object (machine-readable)"
    ),
    jsonl_output: bool = typer.Option(
        False, "--jsonl", help="Output as streaming JSON Lines (one object per event)"
    ),
) -> None:
    """Run kernel evaluation in KernelBench format (ModelNew class).

    This format expects:
    - Implementation: Python file with `class ModelNew(nn.Module)` that mirrors Model interface
    - Reference: Python file with `class Model`, `get_inputs()`, and `get_init_inputs()`

    The evaluation checks:
      1. Correctness: Does ModelNew.forward() produce same output as Model.forward()?
      2. Performance (--benchmark): How fast is it compared to the reference?
      3. Defense (--defensive): Detects evaluation hacking

    Examples:
        # Basic correctness check
        wafer evaluate kernelbench --impl my_kernel.py --reference problem.py

        # With benchmarking
        wafer evaluate kernelbench --impl my_kernel.py --reference problem.py \\
            --target vultr-b200 --benchmark

    Subcommands:
        make-template  Extract a KernelBench problem as template
    """
    # If a subcommand is being invoked, skip the main evaluation logic
    if ctx.invoked_subcommand is not None:
        return

    # Validate required args when running evaluation (not subcommands)
    missing_args = []
    if implementation is None:
        missing_args.append("--impl")
    if reference is None:
        missing_args.append("--reference")

    if missing_args:
        typer.echo("Error: Missing required arguments", err=True)
        typer.echo(f"  Required: {', '.join(missing_args)}", err=True)
        typer.echo("", err=True)
        typer.echo(
            "Usage: wafer evaluate kernelbench --impl KERNEL.py --reference PROBLEM.py", err=True
        )
        typer.echo("", err=True)
        typer.echo("Run 'wafer evaluate kernelbench --help' for full options.", err=True)
        typer.echo(
            "Run 'wafer evaluate kernelbench make-template PROBLEM_ID DIR' to extract a problem.",
            err=True,
        )
        raise typer.Exit(1)

    # Validate --target and --pool are mutually exclusive
    if target and pool:
        typer.echo("Error: Cannot specify both --target and --pool", err=True)
        raise typer.Exit(1)

    from .evaluate import KernelBenchEvaluateArgs, run_evaluate_kernelbench
    from .output import OutputCollector, format_evaluate_result, get_output_format

    output_format = get_output_format(json_output, jsonl_output)
    collector = OutputCollector(format=output_format)

    # If pool specified, acquire a target from the pool
    resolved_target = target or ""
    pool_lock_context = None

    if pool:
        from .target_lock import acquire_from_pool
        from .targets import filter_pool_by_auth, get_pool

        try:
            pool_targets = get_pool(pool)
        except FileNotFoundError as e:
            collector.set_error("pool", "PoolNotFound", pool=pool, message=str(e))
            collector.finalize()
            raise typer.Exit(1) from None

        # Filter to only targets with valid auth
        usable_targets, skipped = filter_pool_by_auth(pool_targets)
        if skipped:
            collector.emit("pool_auth_skip", targets=skipped)

        if not usable_targets:
            collector.set_error("pool", "NoUsableTargets", pool=pool)
            collector.finalize()
            raise typer.Exit(1) from None

        collector.emit("pool_acquire", pool=pool, count=len(usable_targets))
        pool_lock_context = acquire_from_pool(usable_targets)
        acquired_target = pool_lock_context.__enter__()

        if acquired_target is None:
            # Exit context manager before raising to avoid resource leak
            pool_lock_context.__exit__(None, None, None)
            collector.set_error("pool", "AllTargetsBusy", pool=pool, targets=usable_targets)
            collector.finalize()
            raise typer.Exit(1)

        collector.emit("pool_acquired", target=acquired_target)
        resolved_target = acquired_target

    collector.target = resolved_target

    # Expand 'all' stages shorthand
    resolved_stages = stages
    if stages == "all":
        resolved_stages = "compile,correctness,benchmark,defense"

    # Handle backward compat: --benchmark and --defensive flags add to stages
    stage_set = set(resolved_stages.split(","))
    if benchmark and "benchmark" not in stage_set:
        stage_set.add("benchmark")
    if defensive and "defense" not in stage_set:
        stage_set.add("defense")
    resolved_stages = ",".join(
        sorted(
            stage_set,
            key=lambda s: (
                ["compile", "correctness", "benchmark", "defense"].index(s)
                if s in ["compile", "correctness", "benchmark", "defense"]
                else 99
            ),
        )
    )

    args = KernelBenchEvaluateArgs(
        implementation=implementation,
        reference=reference,
        target_name=resolved_target,
        benchmark=benchmark or "benchmark" in stage_set,
        profile=profile,
        inputs=inputs,
        seed=seed,
        defensive=defensive or "defense" in stage_set,
        backend=backend,
        sync_artifacts=sync_artifacts,
        gpu_id=gpu_id,
        stages=resolved_stages,
        prepare_only=prepare_only,
    )

    collector.emit("started", target=resolved_target)

    try:
        import trio_asyncio

        collector.emit("evaluation", status="running")
        result = trio_asyncio.run(run_evaluate_kernelbench, args)
    except KeyboardInterrupt:
        collector.set_error("evaluation", "Interrupted", message="Interrupted by user")
        collector.finalize()
        raise typer.Exit(130) from None
    except Exception as e:
        collector.set_error("evaluation", "Exception", message=str(e))
        collector.finalize()
        raise typer.Exit(1) from None
    finally:
        # Release pool lock if we acquired one
        if pool_lock_context is not None:
            pool_lock_context.__exit__(None, None, None)

    # Build structured output
    eval_output = format_evaluate_result(result, target=resolved_target)
    collector._result = eval_output

    # Print results based on output format
    if result.success:
        collector.output_text_result(result)
        collector.finalize()

        # For prepare-only mode, success means we prepared successfully (don't check correctness)
        # For compile-only (all_correct is None), also treat as success
        if not prepare_only and result.all_correct is not None and not result.all_correct:
            raise typer.Exit(1)
    else:
        collector.output_text_error(result.error_message or "Unknown error")
        collector.finalize()
        raise typer.Exit(1)


@kernelbench_app.command("make-template")
def kernelbench_make_template(
    problem: str = typer.Argument(
        ...,
        help="KernelBench problem ID (e.g., 'level1/1' or 'level1/1_Square_matrix_multiplication_')",
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Output file path (default: ./<problem_name>.py)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing file"),
) -> None:
    """Extract a KernelBench problem as a template file.

    The output file contains the reference Model class, get_inputs(), and get_init_inputs().
    You then create a separate implementation file with your ModelNew class.

    Examples:
        # Extract level1 problem 1 (square matrix multiplication)
        wafer evaluate kernelbench make-template level1/1

        # Extract to specific file
        wafer evaluate kernelbench make-template level1/1 --output ./matmul.py

        # Overwrite existing
        wafer evaluate kernelbench make-template level1/1 --force
    """
    # Get problems root (downloaded or legacy)
    kb_root = _get_kernelbench_root()
    if kb_root is None:
        typer.echo("Error: KernelBench problems not found.", err=True)
        typer.echo("Run 'wafer evaluate kernelbench download' to download problems.", err=True)
        raise typer.Exit(1)

    # Parse problem ID
    parts = problem.split("/")
    if len(parts) != 2:
        typer.echo(f"Error: Invalid problem ID '{problem}'. Expected format: level1/1", err=True)
        raise typer.Exit(1)

    level_str, problem_id_str = parts
    if not level_str.startswith("level"):
        level_str = f"level{level_str}"

    # Find the problem file
    problem_dir = kb_root / level_str
    if not problem_dir.exists():
        typer.echo(f"Error: KernelBench level directory not found: {problem_dir}", err=True)
        typer.echo("Run 'wafer evaluate kernelbench download' to download problems.", err=True)
        raise typer.Exit(1)

    # Find matching problem file
    problem_files = list(problem_dir.glob(f"{problem_id_str}_*.py"))
    if not problem_files:
        # Try exact match if it's a full filename
        exact_match = problem_dir / f"{problem_id_str}.py"
        if exact_match.exists():
            problem_files = [exact_match]
        else:
            typer.echo(
                f"Error: No problem file found matching '{problem_id_str}' in {problem_dir}",
                err=True,
            )
            typer.echo("Available problems:", err=True)
            for f in sorted(problem_dir.glob("*.py"))[:10]:
                typer.echo(f"  {level_str}/{f.stem}", err=True)
            raise typer.Exit(1)

    if len(problem_files) > 1:
        typer.echo(f"Error: Multiple files match '{problem_id_str}':", err=True)
        for f in problem_files:
            typer.echo(f"  {f.name}", err=True)
        typer.echo("Please use a more specific ID.", err=True)
        raise typer.Exit(1)

    problem_file = problem_files[0]

    # Determine output path
    if output is None:
        output = Path.cwd() / problem_file.name

    output = output.resolve()

    # Check if exists
    if output.exists() and not force:
        typer.echo(f"Error: {output} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(1)

    # Copy the file
    content = problem_file.read_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content)

    typer.echo(f"Created {output}")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo(f"  1. Read {output} to understand the Model interface")
    typer.echo("  2. Create an implementation file with your ModelNew class:")
    typer.echo("")
    typer.echo("     import torch.nn as nn")
    typer.echo("")
    typer.echo("     class ModelNew(nn.Module):")
    typer.echo("         def __init__(self, ...):")
    typer.echo("             # Same signature as Model.__init__")
    typer.echo("             ...")
    typer.echo("")
    typer.echo("         def forward(self, ...):")
    typer.echo("             # Same signature as Model.forward")
    typer.echo("             # Your optimized implementation here")
    typer.echo("             ...")
    typer.echo("")
    typer.echo("  3. Run evaluation:")
    typer.echo(f"     wafer evaluate kernelbench --impl my_kernel.py --reference {output}")


# =============================================================================
# GPUMode format evaluation
# =============================================================================


@gpumode_app.command("download")
def gpumode_download(
    force: bool = typer.Option(False, "--force", "-f", help="Re-download even if exists"),
) -> None:
    """Download GPUMode reference kernels from GitHub.

    Downloads the problem set to ~/.cache/wafer/problems/gpumode/

    Examples:
        wafer evaluate gpumode download
        wafer evaluate gpumode download --force  # Re-download
    """
    try:
        path = download_problems("gpumode", force=force, verbose=True)
        typer.echo("")
        typer.echo(f"Problems available at: {path}")
        typer.echo("Run 'wafer evaluate gpumode list-problems' to see available problems.")
    except Exception as e:
        typer.echo(f"Error downloading problems: {e}", err=True)
        raise typer.Exit(1) from None


@gpumode_app.command("list-problems")
def gpumode_list_problems() -> None:
    """List available GPUMode problems.

    Examples:
        wafer evaluate gpumode list-problems
    """
    try:
        list_problems_fn("gpumode", verbose=True)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None


@gpumode_app.command("make-template")
def gpumode_make_template(
    problem: str = typer.Option(
        ...,
        "--problem",
        "-p",
        help="Problem ID (e.g., 'pmpp/vectoradd_py' or 'amd/fp8-mm')",
    ),
    output: Path = typer.Option(
        None, "--output", "-o", help="Output directory (default: ./<problem_name>/)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
) -> None:
    """Extract a GPUMode problem as template files.

    Creates a directory with reference.py, task.yml, and other problem files.
    You then create kernel.py with your custom_kernel implementation.

    Examples:
        # Extract pmpp vectoradd problem
        wafer evaluate gpumode make-template --problem pmpp/vectoradd_py

        # Extract to specific directory
        wafer evaluate gpumode make-template --problem pmpp/vectoradd_py --output ./my-kernel/
    """
    import shutil

    # Get problem path
    problem_path = get_problem_path("gpumode", problem)
    if problem_path is None:
        # Check if problems are downloaded
        if get_problems_path("gpumode") is None:
            typer.echo("Error: GPUMode problems not downloaded.", err=True)
            typer.echo("Run 'wafer evaluate gpumode download' first.", err=True)
        else:
            typer.echo(f"Error: Problem '{problem}' not found.", err=True)
            typer.echo(
                "Run 'wafer evaluate gpumode list-problems' to see available problems.", err=True
            )
        raise typer.Exit(1)

    # Determine output path
    if output is None:
        output = Path.cwd() / problem.replace("/", "_")

    output = output.resolve()

    # Check if exists
    if output.exists() and not force:
        typer.echo(f"Error: {output} already exists. Use --force to overwrite.", err=True)
        raise typer.Exit(1)

    # Copy the problem directory
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(problem_path, output)

    typer.echo(f"Created {output}/")
    typer.echo("")
    typer.echo("Contents:")
    for f in sorted(output.iterdir()):
        if not f.name.startswith("."):
            typer.echo(f"  {f.name}")
    typer.echo("")
    typer.echo("Next steps:")
    typer.echo("  1. Read reference.py to understand the kernel interface")
    typer.echo("  2. Create kernel.py with your custom_kernel implementation:")
    typer.echo("")
    typer.echo("     def custom_kernel(data):")
    typer.echo("         # Your optimized implementation")
    typer.echo("         ...")
    typer.echo("")
    typer.echo("  3. Run evaluation:")
    typer.echo(
        f"     wafer evaluate gpumode --impl {output}/kernel.py --reference {output}/reference.py \\"
    )
    typer.echo(f"         --test-cases {output}/test_cases.json --target <target>")


@gpumode_app.callback(invoke_without_command=True)
def gpumode_evaluate(  # noqa: PLR0913, PLR0915
    ctx: typer.Context,
    implementation: Path | None = typer.Option(
        None, "--impl", "-i", help="Path to implementation kernel file"
    ),
    reference: Path | None = typer.Option(
        None, "--reference", help="Path to reference kernel file"
    ),
    test_cases: Path | None = typer.Option(
        None, "--test-cases", help="Path to test cases JSON file"
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="GPU target name. See 'wafer config targets list' for available targets.",
        autocompletion=complete_target_name,
    ),
    pool: str | None = typer.Option(
        None,
        "--pool",
        "-p",
        help="Target pool name. Acquires first available target from the pool. "
        "Define pools in ~/.wafer/config.toml under [pools.<name>].",
    ),
    benchmark: bool = typer.Option(False, "--benchmark", help="Run performance benchmarks"),
    profile: bool = typer.Option(False, "--profile", help="Enable profiling"),
    defensive: bool = typer.Option(
        False, "--defensive", help="Enable defensive timing to detect evaluation hacking"
    ),
    sync_artifacts: bool = typer.Option(
        True, "--sync-artifacts/--no-sync-artifacts", help="Download artifacts"
    ),
    gpu_id: int | None = typer.Option(None, "--gpu-id", help="Override GPU ID"),
) -> None:
    """Run kernel evaluation in GPUMode format (functional).

    This format expects:
    - Implementation: Python file with `custom_kernel(inputs)` function
    - Reference: Python file with `ref_kernel(inputs)` and `generate_input(**kwargs)` functions
    - Test cases: JSON file with test parameters

    Examples:
        # Basic correctness check
        wafer evaluate gpumode --impl kernel.py --reference ref.py --test-cases tests.json

        # With benchmarking
        wafer evaluate gpumode --impl kernel.py --reference ref.py --test-cases tests.json \\
            --target vultr-b200 --benchmark

    Subcommands:
        download       Download GPUMode problems from GitHub
        list-problems  List available problems
        make-template  Extract a problem as template files
    """
    # If a subcommand is being invoked, skip the main evaluation logic
    if ctx.invoked_subcommand is not None:
        return

    # Validate required args when running evaluation (not subcommands)
    missing_args = []
    if implementation is None:
        missing_args.append("--impl/-i")
    if reference is None:
        missing_args.append("--reference")
    if test_cases is None:
        missing_args.append("--test-cases")

    if missing_args:
        typer.echo("Error: Missing required arguments", err=True)
        typer.echo(f"  Required: {', '.join(missing_args)}", err=True)
        typer.echo("", err=True)
        typer.echo(
            "Usage: wafer evaluate gpumode --impl KERNEL.py --reference REF.py --test-cases TESTS.json",
            err=True,
        )
        typer.echo("", err=True)
        typer.echo("Run 'wafer evaluate gpumode --help' for full options.", err=True)
        typer.echo("Run 'wafer evaluate gpumode download' to download problem sets.", err=True)
        raise typer.Exit(1)

    # Validate --target and --pool are mutually exclusive
    if target and pool:
        typer.echo("Error: Cannot specify both --target and --pool", err=True)
        raise typer.Exit(1)

    from .evaluate import EvaluateArgs, run_evaluate

    # If pool specified, acquire a target from the pool
    resolved_target = target or ""
    pool_lock_context = None

    if pool:
        from .target_lock import acquire_from_pool
        from .targets import filter_pool_by_auth, get_pool

        try:
            pool_targets = get_pool(pool)
        except FileNotFoundError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None

        # Filter to only targets with valid auth
        usable_targets, skipped = filter_pool_by_auth(pool_targets)
        if skipped:
            typer.echo(f"Skipping targets without auth: {', '.join(skipped)}", err=True)

        if not usable_targets:
            typer.echo(f"Error: No usable targets in pool '{pool}'", err=True)
            typer.echo("  All targets require authentication that is not configured.", err=True)
            typer.echo("  Run 'wafer auth status' to see which providers need setup.", err=True)
            raise typer.Exit(1) from None

        typer.echo(f"Acquiring target from pool '{pool}' ({len(usable_targets)} targets)...")
        pool_lock_context = acquire_from_pool(usable_targets)
        acquired_target = pool_lock_context.__enter__()

        if acquired_target is None:
            # Exit context manager before raising to avoid resource leak
            pool_lock_context.__exit__(None, None, None)
            typer.echo(f"Error: All targets in pool '{pool}' are busy", err=True)
            typer.echo(f"  Targets: {', '.join(usable_targets)}", err=True)
            raise typer.Exit(1)

        typer.echo(f"Acquired target: {acquired_target}")
        resolved_target = acquired_target

    args = EvaluateArgs(
        implementation=implementation,
        reference=reference,
        test_cases=test_cases,
        target_name=resolved_target,
        benchmark=benchmark,
        profile=profile,
        defensive=defensive,
        sync_artifacts=sync_artifacts,
        gpu_id=gpu_id,
    )

    try:
        import trio_asyncio

        result = trio_asyncio.run(run_evaluate, args)
    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(130) from None
    except Exception as e:
        if hasattr(e, "exceptions") and e.exceptions:
            for exc in e.exceptions:
                typer.echo(f"Error: {type(exc).__name__}: {exc}", err=True)
        else:
            typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    finally:
        # Release pool lock if we acquired one
        if pool_lock_context is not None:
            pool_lock_context.__exit__(None, None, None)

    # Print results
    if result.success:
        typer.echo("")
        typer.echo("=" * 60)
        status = "PASS" if result.all_correct else "FAIL"
        typer.echo(f"Result: {status}")
        score_pct = f"{result.correctness_score:.1%}"
        typer.echo(f"Correctness: {result.passed_tests}/{result.total_tests} ({score_pct})")
        if result.geomean_speedup > 0:
            typer.echo(f"Speedup: {result.geomean_speedup:.2f}x")
        if result.artifact_path:
            typer.echo(f"Artifacts: {result.artifact_path}")
        typer.echo("=" * 60)

        if not result.all_correct:
            raise typer.Exit(1)
    else:
        typer.echo(f"Error: {result.error_message}", err=True)
        raise typer.Exit(1)


# =============================================================================
# Push and Remote-Run commands
# =============================================================================


@app.command("push", hidden=True)
def push(
    local_path: Path = typer.Argument(..., help="Local directory to upload"),
    workspace: str | None = typer.Option(None, "--workspace", "-w", help="Workspace name override"),
    direct: bool = typer.Option(False, "--direct", "-d", help="Use direct SSH instead of API"),
    target_name: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target for --direct mode. See 'wafer config targets list'.",
        autocompletion=complete_target_name,
    ),
) -> None:
    """Push directory to remote GPU.

    By default, uses wafer-api. Use --direct for direct SSH mode.

    Examples:
        wafer push ./my_project
        wafer push . --workspace my-kernel
        wafer push ./my_project --direct --target vultr-b200
    """
    # Validate path
    if not local_path.exists():
        typer.echo(f"Error: Path not found: {local_path}", err=True)
        raise typer.Exit(1)

    if not local_path.is_dir():
        typer.echo(f"Error: Not a directory: {local_path}", err=True)
        raise typer.Exit(1)

    # Resolve to absolute path
    local_path = local_path.resolve()

    if direct:
        # Direct SSH mode (requires target)
        if not target_name:
            typer.echo("Error: --target required for --direct mode", err=True)
            raise typer.Exit(1)

        from wafer_core.utils.kernel_utils.targets.config import ModalTarget

        from .gpu_run import push_directory as push_direct
        from .targets import load_target

        try:
            target = load_target(target_name)
        except FileNotFoundError:
            typer.echo(f"Error: Target not found: {target_name}", err=True)
            typer.echo("List targets with: wafer config targets list", err=True)
            raise typer.Exit(1) from None

        if isinstance(target, ModalTarget):
            typer.echo(
                f"Error: Target '{target_name}' is a Modal target. Direct push requires SSH.",
                err=True,
            )
            raise typer.Exit(1) from None

        typer.echo(f"Connecting to {target.ssh_target}...")
        try:
            result = push_direct(local_path, target)
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None

        typer.echo(f"Uploading {len(result.files_uploaded)} files to {result.workspace_path}")
        for f in result.files_uploaded:
            typer.echo(f"  ✓ {f}")
        typer.echo(f"Pushed to: {result.workspace_path}")
    else:
        # API mode (default)
        from .api_client import push_directory as push_api

        workspace_name = workspace or local_path.name
        typer.echo(f"Pushing {local_path.name} to wafer-api...")

        try:
            result = push_api(local_path, workspace_name)
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None

        typer.echo(f"Uploaded {len(result.files_uploaded)} files")
        for f in result.files_uploaded:
            typer.echo(f"  ✓ {f}")
        typer.echo(f"Workspace ID: {result.workspace_id}")


def _run_direct_mode(
    cmd_str: str,
    target_name: str,
    upload_dir: Path | None,
    workspace_id: str | None,
    gpu_id: int | None,
) -> int:
    """Run command via direct SSH mode. Returns exit code."""
    from wafer_core.utils.kernel_utils.targets.config import ModalTarget

    from .gpu_run import push_directory as push_direct
    from .gpu_run import run_command as run_direct
    from .targets import load_target

    try:
        target = load_target(target_name)
    except FileNotFoundError:
        typer.echo(f"Error: Target not found: {target_name}", err=True)
        typer.echo("List targets with: wafer config targets list", err=True)
        raise typer.Exit(1) from None

    if isinstance(target, ModalTarget):
        typer.echo(
            f"Error: Target '{target_name}' is a Modal target. Direct mode requires SSH.", err=True
        )
        raise typer.Exit(1) from None

    if not target.docker_image:
        typer.echo(f"Error: Target '{target_name}' has no docker_image configured", err=True)
        raise typer.Exit(1)

    # If upload_dir provided, push first
    workspace_name = workspace_id
    if upload_dir:
        typer.echo(f"Uploading {upload_dir.name}...")
        try:
            push_result = push_direct(upload_dir, target)
            workspace_name = push_result.workspace_name
            typer.echo(f"Uploaded {len(push_result.files_uploaded)} files")
        except Exception as e:
            typer.echo(f"Error uploading: {e}", err=True)
            raise typer.Exit(1) from None
    elif not workspace_name:
        workspace_name = "tmp"

    effective_gpu = gpu_id if gpu_id is not None else target.gpu_ids[0]
    typer.echo(f"Target: {target_name} (docker: {target.docker_image})")
    typer.echo(f"Workspace: {workspace_name}")
    typer.echo(f"GPU: {effective_gpu}")
    typer.echo(f"Command: {cmd_str}")
    typer.echo("-" * 60)

    try:
        return run_direct(cmd_str, workspace_name, target, gpu_id)
    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(130) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


def _run_api_mode(  # noqa: PLR0913
    cmd_str: str,
    upload_dir: Path | None,
    workspace_id: str | None,
    gpu_id: int | None,
    gpu_count: int,
    docker_image: str | None,
    docker_entrypoint: str | None,
    pull_image: bool,
    require_hwc: bool,
) -> int:
    """Run command via wafer-api. Returns exit code."""
    from .api_client import run_command_stream

    if upload_dir:
        typer.echo(f"Uploading: {upload_dir}")
    elif workspace_id:
        typer.echo(f"Workspace: {workspace_id}")
    if gpu_id is not None:
        typer.echo(f"GPU: {gpu_id}")
    if gpu_count > 1:
        typer.echo(f"GPU count: {gpu_count}")
    if docker_image:
        typer.echo(f"Image: {docker_image}")
    if docker_entrypoint:
        typer.echo(f"Entrypoint: {docker_entrypoint}")
    if pull_image:
        typer.echo("Pull image: yes")
    typer.echo(f"Command: {cmd_str}")
    if require_hwc:
        typer.echo("Hardware counters: required (baremetal)")
    typer.echo("-" * 60)

    try:
        return run_command_stream(
            command=cmd_str,
            upload_dir=upload_dir,
            workspace_id=workspace_id,
            gpu_id=gpu_id,
            gpu_count=gpu_count,
            docker_image=docker_image,
            docker_entrypoint=docker_entrypoint,
            pull_image=pull_image,
            require_hardware_counters=require_hwc,
        )
    except KeyboardInterrupt:
        typer.echo("\nInterrupted by user", err=True)
        raise typer.Exit(130) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command("remote-run", hidden=True)
def remote_run(  # noqa: PLR0913
    command: list[str] = typer.Argument(..., help="Command to run"),
    upload_dir: Path | None = typer.Option(
        None, "--upload-dir", "-u", help="Directory to upload (stateless mode)"
    ),
    workspace_id: str | None = typer.Option(
        None, "--workspace-id", "-w", help="Workspace ID (from wafer push)"
    ),
    gpu_id: int | None = typer.Option(None, "--gpu", "-g", help="GPU ID"),
    gpu_count: int = typer.Option(1, "--gpu-count", "-n", help="Number of GPUs (1-8)"),
    docker_image: str | None = typer.Option(None, "--image", "-i", help="Docker image override"),
    docker_entrypoint: str | None = typer.Option(
        None, "--docker-entrypoint", help="Override Docker entrypoint (e.g., 'bash')"
    ),
    pull_image: bool = typer.Option(
        False, "--pull-image", help="Pull image if not available on target"
    ),
    require_hwc: bool = typer.Option(
        False, "--require-hwc", help="Require hardware counters (baremetal)"
    ),
    direct: bool = typer.Option(False, "--direct", "-d", help="Use direct SSH instead of API"),
    target_name: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target for --direct mode. See 'wafer config targets list'.",
        autocompletion=complete_target_name,
    ),
) -> None:
    """Run command on remote GPU in Docker.

    Two modes:
    - High-level (stateless): --upload-dir uploads files and runs command
    - Low-level: --workspace-id uses existing workspace from 'wafer push'

    By default, uses wafer-api. Use --direct for direct SSH mode.

    Examples:
        # Stateless: upload and run
        wafer remote-run --upload-dir ./my_project -- python train.py

        # Run without files
        wafer remote-run -- nvidia-smi

        # Low-level: use existing workspace
        wafer remote-run --workspace-id ws_abc123 -- python train.py

        # Direct SSH mode
        wafer remote-run --upload-dir ./my_project --direct --target vultr-b200 -- python train.py
    """
    cmd_str = " ".join(command)
    if not cmd_str.strip():
        typer.echo("Error: Empty command", err=True)
        raise typer.Exit(1)

    if upload_dir and workspace_id:
        typer.echo("Error: --upload-dir and --workspace-id are mutually exclusive", err=True)
        raise typer.Exit(1)

    if upload_dir:
        if not upload_dir.exists():
            typer.echo(f"Error: Directory not found: {upload_dir}", err=True)
            raise typer.Exit(1)
        if not upload_dir.is_dir():
            typer.echo(f"Error: Not a directory: {upload_dir}", err=True)
            raise typer.Exit(1)
        upload_dir = upload_dir.resolve()

    if direct:
        if not target_name:
            typer.echo("Error: --target required for --direct mode", err=True)
            raise typer.Exit(1)
        exit_code = _run_direct_mode(cmd_str, target_name, upload_dir, workspace_id, gpu_id)
    else:
        exit_code = _run_api_mode(
            cmd_str,
            upload_dir,
            workspace_id,
            gpu_id,
            gpu_count,
            docker_image,
            docker_entrypoint,
            pull_image,
            require_hwc,
        )

    raise typer.Exit(exit_code)


# =============================================================================
# Authentication commands
# =============================================================================


@app.command("login")
def login(
    token: str | None = typer.Option(
        None, "--token", "-t", help="Access token (skip browser OAuth)"
    ),
    port: int | None = typer.Option(
        None,
        "--port",
        "-p",
        help="Port for OAuth callback server (local only, ignored for SSH)",
    ),
    no_device_code: bool = typer.Option(
        False,
        "--no-device-code",
        help="Force browser OAuth even on SSH (requires port forwarding)",
    ),
) -> None:
    """Authenticate CLI with wafer-api via GitHub OAuth.

    Local: Opens browser for GitHub authentication.
    SSH: Uses device code flow (no port forwarding needed).

    Uses the API environment from config (see 'wafer config show').

    SSH Users (Easiest):
    - Just run: wafer login
    - Visit the URL and enter the code shown
    - No port forwarding needed!

    SSH with browser (Advanced):
    - Use --no-device-code to force browser flow
    - Requires: ssh -L 8765:localhost:8765 user@host

    Manual token option:
    - Visit auth.wafer.ai, authenticate, copy token from URL
    - Run: wafer login --token <paste-token>

    Examples:
        wafer login                    # device code on SSH, browser on local
        wafer login --no-device-code   # force browser (needs port forwarding on SSH)
        wafer login --port 9000        # custom port for browser flow
        wafer login --token xyz        # manual token (no browser)

        # Change environment:
        wafer config set api.environment staging
        wafer login
    """
    import httpx

    from .auth import browser_login, device_code_login, save_credentials, verify_token
    from .global_config import get_api_url, get_supabase_url, load_global_config

    # Show which environment we're logging into
    config = load_global_config()
    typer.echo(f"Environment: {config.environment}")
    typer.echo(f"API: {get_api_url()}")
    typer.echo(f"Auth: {get_supabase_url()}")
    typer.echo("")

    # Auto-detect SSH
    is_ssh = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"))

    # Choose auth method
    refresh_token = None
    if token is None:
        try:
            if is_ssh and not no_device_code:
                # Use device code flow for SSH (no port forwarding needed)
                typer.echo("🔒 SSH session detected - using device code authentication")
                typer.echo("   (No port forwarding required!)")
                typer.echo("")
                token, refresh_token = device_code_login()
            else:
                # Use browser OAuth for local or if explicitly requested
                if is_ssh:
                    typer.echo("🔒 SSH session detected - using browser authentication")
                    typer.echo("   Make sure you have port forwarding set up:")
                    if port is None:
                        port = 8765
                        typer.echo(f"   ssh -L {port}:localhost:{port} user@host")
                    else:
                        typer.echo(f"   ssh -L {port}:localhost:{port} user@host")
                    typer.echo("")
                token, refresh_token = browser_login(port=port)
        except TimeoutError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None
        except RuntimeError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None
        except KeyboardInterrupt:
            typer.echo("\nCancelled", err=True)
            raise typer.Exit(1) from None

    if not token.strip():
        typer.echo("Error: Token cannot be empty", err=True)
        raise typer.Exit(1)

    token = token.strip()

    # Verify token with API
    typer.echo("Verifying token...")
    try:
        user_info = verify_token(token)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            typer.echo("Error: Invalid token", err=True)
        else:
            typer.echo(f"Error: API returned {e.response.status_code}", err=True)
        raise typer.Exit(1) from None
    except httpx.RequestError as e:
        typer.echo(f"Error: Could not reach API: {e}", err=True)
        raise typer.Exit(1) from None

    # Save credentials (with refresh token if available)
    save_credentials(token, refresh_token, user_info.email)

    # Track login event with analytics
    from . import analytics

    analytics.track_login(user_info.user_id, user_info.email)

    if user_info.email:
        typer.echo(f"Logged in as {user_info.email}")
    else:
        typer.echo(f"Logged in (user_id: {user_info.user_id})")
    typer.echo("Token saved to ~/.wafer/credentials.json")


@app.command("logout")
def logout() -> None:
    """Remove stored credentials."""
    from . import analytics
    from .auth import clear_credentials

    # Track logout event first (while credentials still exist for user identification)
    # Note: track_logout() handles the case where user is not logged in
    analytics.track_logout()

    # Clear credentials and report result
    if clear_credentials():
        typer.echo("Logged out. Credentials removed.")
    else:
        typer.echo("Not logged in (no credentials found).")


@app.command("whoami")
def whoami(
    verify: bool = typer.Option(False, "--verify", "-v", help="Verify token with API"),
    refresh: bool = typer.Option(False, "--refresh", "-r", help="Refresh token if expired"),
) -> None:
    """Show current authenticated user.

    By default, shows cached credentials. Use --verify to check if token is still valid.
    Use --refresh to automatically refresh an expired token (if refresh token available).
    """
    from .auth import get_valid_token, load_credentials, verify_token

    creds = load_credentials()
    if creds is None:
        typer.echo("Not logged in. Run: wafer login")
        raise typer.Exit(1)

    if verify or refresh:
        if refresh:
            # Try to get valid token with auto-refresh
            token = get_valid_token()
            if token is None:
                typer.echo("Token expired and refresh failed. Run: wafer login", err=True)
                raise typer.Exit(1)
            if token != creds.access_token:
                typer.echo("Token refreshed successfully")
            # Reload creds after potential refresh
            creds = load_credentials()

        try:
            user_info = verify_token(creds.access_token)
            typer.echo(f"{user_info.email or 'Logged in'} (verified)")
        except Exception as e:
            if creds.refresh_token and not refresh:
                typer.echo(f"Token expired: {e}", err=True)
                typer.echo("Try: wafer whoami --refresh", err=True)
            else:
                typer.echo(f"Token invalid or expired: {e}", err=True)
                typer.echo("Run: wafer login", err=True)
            raise typer.Exit(1) from None
    elif creds.email:
        typer.echo(creds.email)
    else:
        typer.echo("Logged in (email not available)")


@app.command("guide")
def guide() -> None:
    """Show the Wafer CLI usage guide.

    Displays a comprehensive guide covering:
    - Common workflows for kernel profiling and optimization
    - NCU/NSYS/Perfetto analysis commands
    - Understanding NCU recommendations
    - Workspace and target management
    """
    guide_path = Path(__file__).parent / "GUIDE.md"
    if not guide_path.exists():
        typer.echo("Error: GUIDE.md not found", err=True)
        raise typer.Exit(1)

    content = guide_path.read_text()
    typer.echo(content)


# =============================================================================
# Demo command
# =============================================================================

# Demo subcommand group
demo_app = typer.Typer(
    help="""Interactive demos for Wafer workflows.

  wafer demo docs   Query GPU documentation (downloads ~5MB)
  wafer demo trace  Analyze a sample performance trace
  wafer demo eval   Run kernel evaluation on cloud GPU (requires login)"""
)
app.add_typer(demo_app, name="demo")

DEMO_TRACES_URL = "https://github.com/wafer-ai/wafer/raw/main/apps/wafer-cli/wafer/demo_data"
DEMO_DIR = Path.home() / ".cache" / "wafer" / "demo"


@demo_app.command("setup")
def demo_setup() -> None:
    """Download sample data for demos and tutorials.

    Downloads sample traces and kernels to ~/.cache/wafer/demo/

    Examples:
        wafer demo setup
        wafer demo traces     # list downloaded traces
        wafer nvidia perfetto query ~/.cache/wafer/demo/attention_trace.json "SELECT ..."
    """
    import shutil

    DEMO_DIR.mkdir(parents=True, exist_ok=True)

    # For now, copy bundled demo data from package
    # In future, could download from GitHub releases
    demo_source = Path(__file__).parent / "demo_data"
    if demo_source.exists():
        for f in demo_source.iterdir():
            dest = DEMO_DIR / f.name
            if not dest.exists():
                shutil.copy(f, dest)
                typer.echo(f"  ✓ {f.name}")
        typer.echo(f"\nDemo data ready at: {DEMO_DIR}")
    else:
        # Fallback: create minimal synthetic trace
        sample_trace = DEMO_DIR / "sample_trace.json"
        if not sample_trace.exists():
            sample_trace.write_text("""{
  "traceEvents": [
    {"name": "matmul_kernel", "cat": "kernel", "ph": "X", "ts": 0, "dur": 1500000, "pid": 1, "tid": 1},
    {"name": "relu_kernel", "cat": "kernel", "ph": "X", "ts": 1600000, "dur": 50000, "pid": 1, "tid": 1},
    {"name": "softmax_kernel", "cat": "kernel", "ph": "X", "ts": 1700000, "dur": 200000, "pid": 1, "tid": 1},
    {"name": "attention_kernel", "cat": "kernel", "ph": "X", "ts": 2000000, "dur": 3000000, "pid": 1, "tid": 1},
    {"name": "layernorm_kernel", "cat": "kernel", "ph": "X", "ts": 5100000, "dur": 100000, "pid": 1, "tid": 1}
  ]
}""")
            typer.echo("  ✓ sample_trace.json (synthetic)")
        typer.echo(f"\nDemo data ready at: {DEMO_DIR}")

    typer.echo("\nTry these commands:")
    typer.echo(f"  wafer nvidia perfetto tables {DEMO_DIR}/sample_trace.json")
    typer.echo(
        f"  wafer nvidia perfetto query {DEMO_DIR}/sample_trace.json "
        '"SELECT name, dur/1e6 as ms FROM slice ORDER BY dur DESC"'
    )


@demo_app.command("traces")
def demo_traces() -> None:
    """List available demo traces.

    Shows demo traces in ~/.cache/wafer/demo/
    Run 'wafer demo setup' first to download sample data.
    """
    if not DEMO_DIR.exists():
        typer.echo("No demo data found. Run: wafer demo setup")
        raise typer.Exit(1)

    traces = list(DEMO_DIR.glob("*.json"))
    if not traces:
        typer.echo("No traces found. Run: wafer demo setup")
        raise typer.Exit(1)

    typer.echo("Available demo traces:\n")
    for trace in sorted(traces):
        size_kb = trace.stat().st_size / 1024
        typer.echo(f"  {trace.name} ({size_kb:.1f} KB)")
        typer.echo(f"    {trace}")
    typer.echo("\nExample queries:")
    typer.echo("  # Slowest operations")
    typer.echo(
        f'  wafer nvidia perfetto query {traces[0]} "SELECT name, dur/1e6 as ms FROM slice ORDER BY dur DESC LIMIT 10"'
    )
    typer.echo("")
    typer.echo("  # Time breakdown by category")
    typer.echo(
        f'  wafer nvidia perfetto query {traces[0]} "SELECT cat, SUM(dur)/1e6 as total_ms FROM slice GROUP BY cat ORDER BY total_ms DESC"'
    )


@demo_app.command("docs")
def demo_docs(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Demo: Ask GPU documentation questions.

    Downloads CUDA corpus (~5MB) and asks a sample question using AI.

    Example:
        wafer demo docs
        wafer demo docs -y  # skip confirmation
    """
    import subprocess

    from .corpus import download_corpus, get_corpus_path

    # Check if already downloaded
    corpus_path = get_corpus_path("cuda")
    needs_download = corpus_path is None

    if needs_download and not yes:
        typer.echo("This demo will:")
        typer.echo("  1. Download CUDA documentation corpus (~5MB)")
        typer.echo("  2. Ask a sample question using AI")
        typer.echo("")
        if not typer.confirm("Continue?"):
            raise typer.Exit(0)

    # Step 1: Download corpus if needed
    if needs_download:
        typer.echo("\n[1/2] Downloading CUDA corpus...")
        download_corpus("cuda")
    else:
        typer.echo("\n[1/2] CUDA corpus already downloaded")

    # Step 2: Ask a question
    typer.echo("\n[2/2] Asking: 'What is warp divergence?'\n")
    typer.echo("-" * 60)
    result = subprocess.run(
        [
            "wafer",
            "wevin",
            "-s",
            "-t",
            "ask-docs",
            "--corpus",
            "cuda",
            "What is warp divergence? Answer in 2-3 sentences.",
        ],
        check=False,
    )
    typer.echo("-" * 60)

    if result.returncode == 0:
        typer.echo("\n✓ Demo complete! Try your own questions:")
        typer.echo('  wafer agent -t ask-docs --corpus cuda "your question here"')
    else:
        typer.echo("\n✗ Demo failed. Check your configuration.")
        raise typer.Exit(1)


@demo_app.command("trace")
def demo_trace(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Demo: Analyze a performance trace.

    Creates a sample PyTorch trace and runs SQL queries on it.

    Example:
        wafer demo trace
        wafer demo trace -y  # skip confirmation
    """
    import subprocess

    if not yes:
        typer.echo("This demo will:")
        typer.echo("  1. Create a sample PyTorch-style trace")
        typer.echo("  2. Run SQL queries to find slowest kernels")
        typer.echo("")
        if not typer.confirm("Continue?"):
            raise typer.Exit(0)

    # Step 1: Setup demo data
    typer.echo("\n[1/2] Creating sample trace...")
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    sample_trace = DEMO_DIR / "sample_trace.json"
    sample_trace.write_text("""{
  "traceEvents": [
    {"name": "matmul_kernel", "cat": "kernel", "ph": "X", "ts": 0, "dur": 1500000, "pid": 1, "tid": 1},
    {"name": "relu_kernel", "cat": "kernel", "ph": "X", "ts": 1600000, "dur": 50000, "pid": 1, "tid": 1},
    {"name": "softmax_kernel", "cat": "kernel", "ph": "X", "ts": 1700000, "dur": 200000, "pid": 1, "tid": 1},
    {"name": "attention_kernel", "cat": "kernel", "ph": "X", "ts": 2000000, "dur": 3000000, "pid": 1, "tid": 1},
    {"name": "layernorm_kernel", "cat": "kernel", "ph": "X", "ts": 5100000, "dur": 100000, "pid": 1, "tid": 1}
  ]
}""")
    typer.echo(f"  Created: {sample_trace}")

    # Step 2: Query the trace
    typer.echo("\n[2/2] Finding slowest kernels...\n")
    typer.echo("-" * 60)
    result = subprocess.run(
        [
            "wafer",
            "nvidia",
            "perfetto",
            "query",
            str(sample_trace),
            "SELECT name, dur/1e6 as duration_ms FROM slice ORDER BY dur DESC",
        ],
        check=False,
    )
    typer.echo("-" * 60)

    if result.returncode == 0:
        typer.echo("\n✓ Demo complete! Try your own traces:")
        typer.echo('  wafer nvidia perfetto query <your_trace.json> "SELECT name, dur FROM slice"')
        typer.echo("")
        typer.echo("  Or use AI-assisted analysis:")
        typer.echo('  wafer agent -t trace-analyze --args trace=<your_trace.json> "What\'s slow?"')
    else:
        typer.echo("\n✗ Demo failed.")
        raise typer.Exit(1)


@demo_app.command("eval")
def demo_eval(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Demo: Evaluate a kernel on a cloud GPU.

    Creates a workspace, runs a sample Triton kernel evaluation, and cleans up.
    Requires authentication (wafer login).

    Example:
        wafer demo eval
        wafer demo eval -y  # skip confirmation
    """
    import subprocess
    import tempfile
    import time

    from .auth import load_credentials

    # Check auth first
    creds = load_credentials()
    if not creds:
        typer.echo("Error: Not authenticated. Run: wafer login")
        raise typer.Exit(1)

    if not yes:
        typer.echo("This demo will:")
        typer.echo("  1. Create a cloud GPU workspace (B200)")
        typer.echo("  2. Generate and upload a sample Triton kernel")
        typer.echo("  3. Run correctness + performance evaluation")
        typer.echo("  4. Delete the workspace")
        typer.echo("")
        typer.echo("  Note: Workspace usage is billed. Demo takes ~2-3 minutes.")
        typer.echo("")
        if not typer.confirm("Continue?"):
            raise typer.Exit(0)

    workspace_name = f"wafer-demo-{int(time.time()) % 100000}"

    try:
        # Step 1: Create workspace
        typer.echo(f"\n[1/4] Creating workspace '{workspace_name}'...")
        result = subprocess.run(
            ["wafer", "workspaces", "create", workspace_name, "--gpu", "B200", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        import json

        ws_info = json.loads(result.stdout)
        workspace_id = ws_info.get("id", workspace_name)
        typer.echo(f"  Created: {workspace_id}")

        # Step 2: Generate kernel template
        typer.echo("\n[2/4] Generating sample kernel...")
        with tempfile.TemporaryDirectory() as tmpdir:
            kernel_dir = Path(tmpdir) / "demo-kernel"
            subprocess.run(
                ["wafer", "evaluate", "make-template", str(kernel_dir)],
                capture_output=True,
                check=True,
            )
            typer.echo("  Generated Triton vector-add kernel")

            # Step 3: Run evaluation
            typer.echo("\n[3/4] Running evaluation on cloud GPU...\n")
            typer.echo("-" * 60)

            # Write a simple test script to avoid escaping hell
            test_script = kernel_dir / "run_test.py"
            test_script.write_text("""
import torch
import kernel
import reference

print(f"GPU: {torch.cuda.get_device_name(0)}")

# Test correctness
inputs = reference.generate_input(n=1048576, seed=42)
out = kernel.custom_kernel(inputs)
ref = reference.ref_kernel(inputs)
correct = torch.allclose(out, ref)
print(f"Correctness: {correct}")

# Benchmark
import time
for _ in range(10):
    kernel.custom_kernel(inputs)
torch.cuda.synchronize()

t0 = time.perf_counter()
for _ in range(100):
    kernel.custom_kernel(inputs)
torch.cuda.synchronize()
t1 = time.perf_counter()

print(f"Performance: {(t1-t0)/100*1e6:.1f} us/iter")
""")

            eval_result = subprocess.run(
                [
                    "wafer",
                    "workspaces",
                    "exec",
                    "--sync",
                    str(kernel_dir),
                    workspace_name,
                    "--",
                    "bash",
                    "-c",
                    "cd /workspace && uv pip install -q --system triton && python run_test.py",
                ],
                check=False,
            )
            typer.echo("-" * 60)

        # Step 4: Cleanup
        typer.echo(f"\n[4/4] Deleting workspace '{workspace_name}'...")
        subprocess.run(
            ["wafer", "workspaces", "delete", workspace_id],
            capture_output=True,
            check=False,
        )
        typer.echo("  Deleted")

        if eval_result.returncode == 0:
            typer.echo("\n✓ Demo complete! To evaluate your own kernels:")
            typer.echo("")
            typer.echo("  # Using workspaces (no setup required):")
            typer.echo("  wafer workspaces create dev --gpu B200")
            typer.echo("  wafer workspaces exec --sync ./my-kernel dev -- python my_test.py")
            typer.echo("")
            typer.echo("  # Or using wafer evaluate with a configured target:")
            typer.echo("  wafer evaluate make-template ./my-kernel")
            typer.echo("  wafer evaluate --impl ./my-kernel/kernel.py \\")
            typer.echo("      --reference ./my-kernel/reference.py \\")
            typer.echo("      --test-cases ./my-kernel/test_cases.json \\")
            typer.echo("      --target <your-target>")
        else:
            typer.echo("\n✗ Evaluation failed, but workspace was cleaned up.")
            raise typer.Exit(1)

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        typer.echo(f"\n✗ Error: {error_msg}")
        # Try to cleanup on failure
        typer.echo(f"Attempting to cleanup workspace '{workspace_name}'...")
        subprocess.run(
            ["wafer", "workspaces", "delete", workspace_name],
            capture_output=True,
            check=False,
        )
        raise typer.Exit(1) from None
    except KeyboardInterrupt:
        typer.echo(f"\n\nInterrupted. Cleaning up workspace '{workspace_name}'...")
        subprocess.run(
            ["wafer", "workspaces", "delete", workspace_name],
            capture_output=True,
            check=False,
        )
        raise typer.Exit(1) from None


# =============================================================================
# Targets subcommands
# =============================================================================

# Init subcommand group for interactive target setup
init_app = typer.Typer(
    help="""Initialize a new GPU target.

Choose based on your GPU access:

  local        GPU on current machine (no SSH)
  ssh          Your own hardware via SSH
  runpod       RunPod cloud GPUs (needs WAFER_RUNPOD_API_KEY)
  digitalocean DigitalOcean AMD MI300X (needs WAFER_AMD_DIGITALOCEAN_API_KEY)"""
)
targets_app.add_typer(init_app, name="init")


@init_app.command("local")
def init_local(
    name: str = typer.Option("local", "--name", "-n", help="Target name"),
    gpu_ids: str = typer.Option("0", "--gpu-ids", "-g", help="Comma-separated GPU IDs"),
) -> None:
    """Initialize a local target for GPU on current machine.

    Detects your local GPU and configures a target for direct execution
    (no SSH). Use this when running wafer on the same machine as the GPU.

    Examples:
        wafer config targets init local
        wafer config targets init local --name my-5090 --gpu-ids 0,1
    """
    from .targets import save_target

    # Parse GPU IDs
    try:
        parsed_gpu_ids = [int(g.strip()) for g in gpu_ids.split(",")]
    except ValueError:
        typer.echo(f"Error: Invalid GPU IDs '{gpu_ids}'. Use comma-separated integers.", err=True)
        raise typer.Exit(1) from None

    typer.echo("Detecting local GPU...")

    try:
        from wafer_core.gpu_detect import (
            detect_local_gpu,
            get_compute_capability,
            get_torch_requirements,
        )

        detected_gpu = detect_local_gpu()

        if detected_gpu:
            typer.echo(f"  Found: {detected_gpu.gpu_name}")
            if detected_gpu.vendor == "nvidia":
                typer.echo(f"  CUDA: {detected_gpu.driver_version}")
            else:
                typer.echo(f"  ROCm: {detected_gpu.driver_version}")
            typer.echo(f"  GPU count: {detected_gpu.gpu_count}")

            # Get torch requirements and compute capability
            torch_reqs = get_torch_requirements(detected_gpu)
            compute_capability = get_compute_capability(detected_gpu)
            gpu_type = _extract_gpu_type(detected_gpu.gpu_name)

            typer.echo(f"  PyTorch: {torch_reqs.packages[0]}")
        else:
            typer.echo("  No GPU detected (nvidia-smi/rocm-smi not found)", err=True)
            raise typer.Exit(1)

    except ImportError as e:
        typer.echo(f"Error: Missing dependency: {e}", err=True)
        raise typer.Exit(1) from None

    # Build target data
    target_data = {
        "name": name,
        "type": "local",
        "gpu_ids": parsed_gpu_ids,
        "gpu_type": gpu_type,
        "compute_capability": compute_capability,
        "torch_package": torch_reqs.packages[0],
        "torch_index_url": torch_reqs.index_url,
        "vendor": detected_gpu.vendor,
        "driver_version": detected_gpu.driver_version,
    }

    try:
        target = save_target(target_data)
        typer.echo(f"✓ Created target: {target.name}")
        typer.echo("  Type: Local (no SSH)")
        typer.echo(f"  GPU IDs: {parsed_gpu_ids}")
        typer.echo(f"  GPU Type: {gpu_type}")
        typer.echo(f"  Compute: {compute_capability}")
        typer.echo(f"  Torch: {torch_reqs.packages[0]}")
        typer.echo("")
        typer.echo(
            f"Usage: wafer evaluate --target {name} --impl kernel.py --reference ref.py --test-cases tests.json"
        )
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@init_app.command("runpod")
def init_runpod(
    name: str = typer.Option("runpod-mi300x", "--name", "-n", help="Target name"),
    gpu_type: str = typer.Option("MI300X", "--gpu", "-g", help="GPU type (MI300X, H100, A100)"),
    ssh_key: str = typer.Option("~/.ssh/id_ed25519", "--ssh-key", "-k", help="Path to SSH key"),
    keep_alive: bool = typer.Option(
        True, "--keep-alive/--no-keep-alive", help="Keep pod running after eval"
    ),
) -> None:
    """Initialize a RunPod target.

    Creates a target config for auto-provisioned RunPod GPUs.
    Requires WAFER_RUNPOD_API_KEY environment variable.

    Examples:
        wafer config targets init runpod
        wafer config targets init runpod --name my-runpod --gpu H100
    """
    import os

    from .targets import save_target

    # Check for API key
    api_key = os.environ.get("WAFER_RUNPOD_API_KEY", "")
    if not api_key:
        typer.echo("Error: WAFER_RUNPOD_API_KEY environment variable not set.", err=True)
        typer.echo("", err=True)
        typer.echo("Get your API key from: https://runpod.io/console/user/settings", err=True)
        typer.echo("Then run: export WAFER_RUNPOD_API_KEY=your_key_here", err=True)
        raise typer.Exit(1)

    # GPU type mappings
    gpu_configs = {
        "MI300X": {
            "gpu_type_id": "AMD Instinct MI300X OAM",
            "image": "rocm/pytorch:rocm7.0.2_ubuntu24.04_py3.12_pytorch_release_2.7.1",
            "compute_capability": "9.4",
        },
        "H100": {
            "gpu_type_id": "NVIDIA H100 80GB HBM3",
            "image": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            "compute_capability": "9.0",
        },
        "A100": {
            "gpu_type_id": "NVIDIA A100 80GB PCIe",
            "image": "runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04",
            "compute_capability": "8.0",
        },
    }

    if gpu_type not in gpu_configs:
        typer.echo(
            f"Error: Unknown GPU type '{gpu_type}'. Available: {', '.join(gpu_configs.keys())}",
            err=True,
        )
        raise typer.Exit(1)

    config = gpu_configs[gpu_type]

    # Build target data
    target_data = {
        "name": name,
        "type": "runpod",
        "ssh_key": ssh_key,
        "gpu_type_id": config["gpu_type_id"],
        "gpu_count": 1,
        "container_disk_gb": 50,
        "image": config["image"],
        "provision_timeout": 900,
        "eval_timeout": 600,
        "keep_alive": keep_alive,
        "gpu_type": gpu_type,
        "compute_capability": config["compute_capability"],
        "gpu_ids": [0],
        "ncu_available": False,
    }

    try:
        target = save_target(target_data)
        typer.echo(f"✓ Created target: {target.name}")
        typer.echo("  Type: RunPod")
        typer.echo(f"  GPU: {gpu_type}")
        typer.echo(f"  Image: {config['image']}")
        typer.echo(f"  Keep alive: {'Yes' if keep_alive else 'No'}")
        typer.echo("")
        typer.echo(
            f"Usage: wafer evaluate --target {name} --impl kernel.py --reference ref.py --test-cases tests.json"
        )
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@init_app.command("digitalocean")
def init_digitalocean(
    name: str = typer.Option("do-mi300x", "--name", "-n", help="Target name"),
    region: str = typer.Option("atl1", "--region", "-r", help="Region (atl1)"),
    ssh_key: str = typer.Option("~/.ssh/id_ed25519", "--ssh-key", "-k", help="Path to SSH key"),
    keep_alive: bool = typer.Option(
        True, "--keep-alive/--no-keep-alive", help="Keep droplet running after eval"
    ),
) -> None:
    """Initialize a DigitalOcean target.

    Creates a target config for auto-provisioned DigitalOcean AMD GPUs (MI300X).
    Requires WAFER_AMD_DIGITALOCEAN_API_KEY environment variable.

    Examples:
        wafer config targets init digitalocean
        wafer config targets init digitalocean --name my-do --region atl1
    """
    import os

    from .targets import save_target

    # Check for API key
    api_key = os.environ.get("WAFER_AMD_DIGITALOCEAN_API_KEY", "")
    if not api_key:
        typer.echo("Error: WAFER_AMD_DIGITALOCEAN_API_KEY environment variable not set.", err=True)
        typer.echo("", err=True)
        typer.echo("Get your API key from the DigitalOcean AMD Developer Cloud portal.", err=True)
        typer.echo("Then run: export WAFER_AMD_DIGITALOCEAN_API_KEY=your_key_here", err=True)
        raise typer.Exit(1)

    # Build target data
    target_data = {
        "name": name,
        "type": "digitalocean",
        "ssh_key": ssh_key,
        "region": region,
        "size_slug": "gpu-mi300x1-192gb-devcloud",
        "image": "amd-pytorchrocm7",  # PyTorch (ROCm7) marketplace image
        "provision_timeout": 600,
        "eval_timeout": 600,
        "keep_alive": keep_alive,
        "gpu_type": "MI300X",
        "compute_capability": "9.4",
        "gpu_ids": [0],
        "ncu_available": False,
    }

    try:
        target = save_target(target_data)
        typer.echo(f"✓ Created target: {target.name}")
        typer.echo("  Type: DigitalOcean")
        typer.echo("  GPU: MI300X")
        typer.echo(f"  Region: {region}")
        typer.echo(f"  Keep alive: {'Yes' if keep_alive else 'No'}")
        typer.echo("")
        typer.echo(
            f"Usage: wafer evaluate --target {name} --impl kernel.py --reference ref.py --test-cases tests.json"
        )
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@init_app.command("ssh")
def init_ssh(
    name: str = typer.Option(..., "--name", "-n", help="Target name"),
    host: str = typer.Option(..., "--host", "-H", help="SSH host (user@hostname:port)"),
    ssh_key: str = typer.Option("~/.ssh/id_ed25519", "--ssh-key", "-k", help="Path to SSH key"),
    gpu_ids: str = typer.Option("0", "--gpu-ids", "-g", help="Comma-separated GPU IDs"),
    gpu_type: str | None = typer.Option(
        None, "--gpu-type", help="GPU type (auto-detected if not specified)"
    ),
    docker_image: str | None = typer.Option(
        None, "--docker-image", "-d", help="Docker image (optional)"
    ),
    ncu: bool = typer.Option(False, "--ncu/--no-ncu", help="NCU profiling available"),
    no_detect: bool = typer.Option(False, "--no-detect", help="Skip GPU auto-detection"),
) -> None:
    """Initialize an SSH target for your own GPU hardware.

    Creates a target config for direct SSH access to a GPU machine.
    Automatically detects GPU type and selects compatible PyTorch version.

    Examples:
        # Auto-detect GPU (recommended)
        wafer config targets init ssh --name my-gpu --host user@192.168.1.100:22

        # Multiple GPUs with NCU profiling
        wafer config targets init ssh --name lab-h100 --host ubuntu@gpu.lab.com:22 --gpu-ids 0,1 --ncu

        # Skip detection, specify manually
        wafer config targets init ssh --name my-gpu --host user@host:22 --gpu-type H100 --no-detect
    """
    from .targets import save_target

    # Parse GPU IDs
    try:
        parsed_gpu_ids = [int(g.strip()) for g in gpu_ids.split(",")]
    except ValueError:
        typer.echo(f"Error: Invalid GPU IDs '{gpu_ids}'. Use comma-separated integers.", err=True)
        raise typer.Exit(1) from None

    # Validate host format
    if ":" not in host:
        typer.echo(f"Error: Host must include port (user@hostname:port), got: {host}", err=True)
        typer.echo("Example: user@192.168.1.100:22", err=True)
        raise typer.Exit(1)

    # Auto-detect GPU if not specified
    detected_gpu = None
    torch_package = None
    torch_index_url = None

    if not no_detect:
        typer.echo(f"Connecting to {host}...")
        try:
            import trio
            import trio_asyncio
            from wafer_core.async_ssh import AsyncSSHClient
            from wafer_core.gpu_detect import (
                detect_remote_gpu,
                get_compute_capability,
                get_torch_requirements,
            )

            expanded_key = str(Path(ssh_key).expanduser())

            async def _detect() -> None:
                nonlocal detected_gpu, torch_package, torch_index_url
                # Need trio_asyncio.open_loop() for asyncssh bridge
                async with trio_asyncio.open_loop():
                    async with AsyncSSHClient(host, expanded_key) as client:
                        detected_gpu = await detect_remote_gpu(client)

            trio.run(_detect)

            if detected_gpu:
                typer.echo(f"  Found: {detected_gpu.gpu_name}")
                if detected_gpu.vendor == "nvidia":
                    typer.echo(f"  CUDA: {detected_gpu.driver_version}")
                else:
                    typer.echo(f"  ROCm: {detected_gpu.driver_version}")

                # Get torch requirements
                torch_reqs = get_torch_requirements(detected_gpu)
                torch_package = torch_reqs.packages[0]  # Just torch, not all packages
                torch_index_url = torch_reqs.index_url
                typer.echo(f"  PyTorch: {torch_package}")

                # Use detected GPU type if not specified
                if not gpu_type:
                    # Extract GPU name (e.g., "H100" from "NVIDIA H100 80GB HBM3")
                    gpu_type = _extract_gpu_type(detected_gpu.gpu_name)
            else:
                typer.echo("  No GPU detected (nvidia-smi/rocm-smi not found)")
                if not gpu_type:
                    gpu_type = "H100"  # Default fallback
                    typer.echo(f"  Using default: {gpu_type}")

        except Exception as e:
            typer.echo(f"  Detection failed: {e}", err=True)
            if not gpu_type:
                gpu_type = "H100"
                typer.echo(f"  Using default: {gpu_type}")

    # Fallback if no detection
    if not gpu_type:
        gpu_type = "H100"

    # Compute capability mappings
    if detected_gpu:
        from wafer_core.gpu_detect import get_compute_capability

        compute_capability = get_compute_capability(detected_gpu)
    else:
        compute_caps = {
            "B200": "10.0",
            "H100": "9.0",
            "A100": "8.0",
            "A10": "8.6",
            "V100": "7.0",
            "MI300X": "9.4",
            "MI250X": "9.0",
            "RTX 5090": "10.0",
            "RTX 4090": "8.9",
            "RTX 3090": "8.6",
        }
        compute_capability = compute_caps.get(gpu_type, "8.0")

    # Build target data
    target_data = {
        "name": name,
        "type": "baremetal",
        "ssh_target": host,
        "ssh_key": ssh_key,
        "gpu_ids": parsed_gpu_ids,
        "gpu_type": gpu_type,
        "compute_capability": compute_capability,
        "ncu_available": ncu,
    }

    if docker_image:
        target_data["docker_image"] = docker_image

    # Add torch requirements if detected
    if torch_package:
        target_data["torch_package"] = torch_package
    if torch_index_url:
        target_data["torch_index_url"] = torch_index_url

    try:
        target = save_target(target_data)
        typer.echo(f"✓ Created target: {target.name}")
        typer.echo("  Type: Baremetal (SSH)")
        typer.echo(f"  Host: {host}")
        typer.echo(f"  GPU IDs: {parsed_gpu_ids}")
        typer.echo(f"  GPU Type: {gpu_type}")
        typer.echo(f"  Compute: {compute_capability}")
        typer.echo(f"  NCU: {'Yes' if ncu else 'No'}")
        if docker_image:
            typer.echo(f"  Docker: {docker_image}")
        if torch_package:
            typer.echo(f"  Torch: {torch_package}")
        typer.echo("")
        typer.echo(
            f"Usage: wafer evaluate --target {name} --impl kernel.py --reference ref.py --test-cases tests.json"
        )
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


def _extract_gpu_type(gpu_name: str) -> str:
    """Extract GPU type from full GPU name.

    Examples:
        "NVIDIA H100 80GB HBM3" -> "H100"
        "NVIDIA GeForce RTX 4090" -> "RTX 4090"
        "AMD Instinct MI300X OAM" -> "MI300X"
    """
    gpu_name_upper = gpu_name.upper()

    # Check for known GPU types
    known_types = [
        "B200",
        "B100",
        "H200",
        "H100",
        "A100",
        "A10",
        "V100",
        "RTX 5090",
        "RTX 5080",
        "RTX 4090",
        "RTX 4080",
        "RTX 3090",
        "RTX 3080",
        "MI300X",
        "MI250X",
        "MI100",
    ]

    for gpu_type in known_types:
        if gpu_type in gpu_name_upper:
            return gpu_type

    # Fallback: return cleaned name
    return gpu_name.replace("NVIDIA ", "").replace("AMD ", "").strip()


@targets_app.command("add")
def targets_add(
    file_path: Path = typer.Argument(..., help="Path to target TOML file"),
) -> None:
    """Add a target from a TOML config file.

    Example:
        wafer config targets add ~/configs/my-gpu.toml

    Target TOML schema (baremetal example):

        name = "my-gpu"
        type = "baremetal"
        ssh_target = "user@hostname"
        gpu_ids = [0]
        compute_capability = "9.0"
        ncu_available = true
        docker_image = "nvcr.io/nvidia/pytorch:24.01-py3"

    Available types: baremetal, vm, modal, workspace, runpod, digitalocean
    """
    from .targets import add_target_from_file, get_target_info

    try:
        target = add_target_from_file(file_path)
        typer.echo(f"Added target: {target.name}")
        info = get_target_info(target)
        for key, value in info.items():
            typer.echo(f"  {key}: {value}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except (ValueError, AssertionError) as e:
        typer.echo(f"Error: Invalid target config: {e}", err=True)
        raise typer.Exit(1) from None


@targets_app.command("list")
def targets_list() -> None:
    """List all configured targets with live provider status.

    Example:
        wafer config targets list
    """
    import socket

    import trio

    from .targets import get_default_target, list_targets, load_target, remove_target

    targets = list_targets()
    default = get_default_target()

    if not targets:
        typer.echo("No targets configured.")
        typer.echo("Add one with: wafer config targets add <path/to/target.toml>")
        return

    def _parse_ssh_target(ssh_target: str) -> tuple[str, int]:
        """Extract (host, port) from user@host:port string."""
        parts = ssh_target.rsplit(":", 1)
        host_part = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 22
        if "@" in host_part:
            host = host_part.split("@", 1)[1]
        else:
            host = host_part
        return (host, port)

    async def _get_live_provider_endpoints() -> set[tuple[str, int]]:
        """Query RunPod + DO APIs. Returns set of live (ip, port) endpoints."""
        from wafer_core.targets.digitalocean import list_running_droplets
        from wafer_core.targets.runpod import sync_pods_from_api

        live_endpoints: set[tuple[str, int]] = set()

        async def _fetch_runpod() -> None:
            try:
                pods = await sync_pods_from_api()
                for p in pods:
                    live_endpoints.add((p.public_ip, p.ssh_port))
            except Exception:
                pass

        async def _fetch_do() -> None:
            try:
                droplets = await list_running_droplets()
                for d in droplets:
                    live_endpoints.add((d.public_ip, d.ssh_port))
            except Exception:
                pass

        async with trio.open_nursery() as nursery:
            nursery.start_soon(_fetch_runpod)
            nursery.start_soon(_fetch_do)

        return live_endpoints

    async def _get_target_status(
        name: str,
        live_endpoints: set[tuple[str, int]],
    ) -> tuple[str, str, str]:
        """Returns (name, status, ssh_info)."""
        from wafer_core.targets.digitalocean import (
            _remove_droplet_from_state,
            check_droplet_running,
            get_droplet_state,
        )
        from wafer_core.targets.runpod import (
            _remove_pod_from_state,
            check_pod_running,
            get_pod_state,
        )
        from wafer_core.utils.kernel_utils.targets.config import (
            BaremetalTarget,
            DigitalOceanTarget,
            ModalTarget,
            RunPodTarget,
        )

        try:
            target = load_target(name)
        except (FileNotFoundError, ValueError, AssertionError, TypeError):
            return (name, "error", "")

        if isinstance(target, RunPodTarget):
            pod = get_pod_state(name)
            if not pod:
                return (name, "no instance", "")
            if await check_pod_running(pod.pod_id):
                return (name, "running", f"{pod.ssh_username}@{pod.public_ip}:{pod.ssh_port}")
            _remove_pod_from_state(name)
            return (name, "stopped", "")

        if isinstance(target, DigitalOceanTarget):
            droplet = get_droplet_state(name)
            if not droplet:
                return (name, "no instance", "")
            if await check_droplet_running(droplet.droplet_id):
                return (
                    name,
                    "running",
                    f"{droplet.ssh_username}@{droplet.public_ip}:{droplet.ssh_port}",
                )
            _remove_droplet_from_state(name)
            return (name, "stopped", "")

        if isinstance(target, BaremetalTarget):
            ssh_target = target.ssh_target
            host, port = _parse_ssh_target(ssh_target)

            def _tcp_check() -> bool:
                try:
                    sock = socket.create_connection((host, port), timeout=2)
                    sock.close()
                    return True
                except OSError:
                    return False

            reachable = await trio.to_thread.run_sync(_tcp_check)
            if reachable:
                return (name, "reachable", ssh_target)

            # Unreachable + has a provider = backed by an ephemeral instance.
            # If not in the live provider listing, the instance is gone — remove config.
            if target.provider and (host, port) not in live_endpoints:
                remove_target(name)
                return (name, "removed (dead pod)", ssh_target)

            return (name, "unreachable", ssh_target)

        if isinstance(target, ModalTarget):
            return (name, "serverless", "")

        # Unknown target type
        return (name, "unknown", "")

    async def _gather_statuses() -> list[tuple[str, str, str]]:
        live_endpoints = await _get_live_provider_endpoints()
        results: list[tuple[str, str, str]] = [("", "", "")] * len(targets)

        async def _check(i: int, name: str) -> None:
            results[i] = await _get_target_status(name, live_endpoints)

        async with trio.open_nursery() as nursery:
            for i, name in enumerate(targets):
                nursery.start_soon(_check, i, name)

        return results

    statuses = trio.run(_gather_statuses)

    typer.echo("Configured targets:")
    for name, status, ssh_info in statuses:
        marker = " (default)" if name == default else ""
        label = f"  {name}{marker}"
        detail = f"  {ssh_info}" if ssh_info else ""
        typer.echo(f"{label:<40}{status}{detail}")


@targets_app.command("show")
def targets_show(
    name: str = typer.Argument(..., help="Target name"),
) -> None:
    """Show details for a target.

    Example:
        wafer config targets show modal-b200
    """
    from .targets import get_target_info, load_target

    try:
        target = load_target(name)
        typer.echo(f"Target: {name}")
        info = get_target_info(target)
        for key, value in info.items():
            typer.echo(f"  {key}: {value}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@targets_app.command("probe")
def targets_probe(
    name: str = typer.Argument(..., help="Target name"),
) -> None:
    """Probe a target to discover available compilation backends.

    Connects to the target and checks what's available:
    - Triton
    - torch.compile/inductor
    - HIP/hipcc or CUDA/nvcc
    - ROCm or CUDA version
    - Python packages (torch, triton, etc.)

    Example:
        wafer config targets probe runpod-mi300x
    """
    import trio

    from .targets import ProbeError, load_target, probe_target_capabilities

    try:
        target = load_target(name)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Probing target: {name}...")

    try:
        capabilities = trio.run(probe_target_capabilities, target)
    except ProbeError as e:
        # ProbeError already has actionable context
        typer.echo(f"\nError: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        # Unexpected errors - include type for debugging
        typer.echo(f"\nUnexpected error probing target: {type(e).__name__}: {e}", err=True)
        raise typer.Exit(1) from None

    # Display results
    typer.echo(f"\nTarget: {name}")

    if capabilities.get("gpu_name"):
        typer.echo(f"  GPU: {capabilities['gpu_name']}")
    if capabilities.get("compute_capability"):
        typer.echo(f"  Compute: {capabilities['compute_capability']}")

    typer.echo("\n  Compilation Backends:")
    backends = capabilities.get("backends", {})

    # Triton
    triton_ver = backends.get("triton")
    if triton_ver:
        typer.echo(f"    ✓ Triton: {triton_ver}")
    else:
        typer.echo("    ✗ Triton: not installed")

    # torch.compile
    if triton_ver and backends.get("torch"):
        typer.echo("    ✓ torch.compile/inductor: available")
    else:
        typer.echo("    ✗ torch.compile/inductor: requires Triton")

    # HIP/CUDA compiler
    if backends.get("hipcc"):
        typer.echo(f"    ✓ HIP/hipcc: {backends['hipcc']}")
    elif backends.get("nvcc"):
        typer.echo(f"    ✓ CUDA/nvcc: {backends['nvcc']}")
    else:
        typer.echo("    ✗ No GPU compiler found")

    # ROCm/CUDA version
    if capabilities.get("rocm_version"):
        typer.echo(f"    ROCm: {capabilities['rocm_version']}")
    if capabilities.get("cuda_version"):
        typer.echo(f"    CUDA: {capabilities['cuda_version']}")

    typer.echo("\n  Python Environment:")
    typer.echo(f"    Python: {capabilities.get('python_version', 'unknown')}")

    packages = capabilities.get("packages", {})
    if packages.get("torch"):
        typer.echo(f"    PyTorch: {packages['torch']}")
    if triton_ver:
        typer.echo(f"    Triton: {triton_ver}")


@targets_app.command("remove")
def targets_remove(
    name: str = typer.Argument(..., help="Target name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
) -> None:
    """Remove a target.

    Example:
        wafer config targets remove modal-b200
    """
    from .targets import remove_target

    if not force:
        confirm = typer.confirm(f"Remove target '{name}'?")
        if not confirm:
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        remove_target(name)
        typer.echo(f"Removed target: {name}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@targets_app.command("default")
def targets_default(
    name: str = typer.Argument(..., help="Target name to set as default"),
) -> None:
    """Set the default target.

    Example:
        wafer config targets default modal-b200
    """
    from .targets import set_default_target

    try:
        set_default_target(name)
        typer.echo(f"Default target set to: {name}")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@targets_app.command("cleanup")
def targets_cleanup(
    name: str = typer.Argument(..., help="Target name to clean up (must be a RunPod target)"),
) -> None:
    """Terminate RunPod pod for a target.

    Only works for RunPod targets. Terminates any running pod associated
    with the target and removes it from the state file.

    Example:
        wafer config targets cleanup runpod-mi300x
    """
    import trio
    from wafer_core.targets.runpod import cleanup_target, get_pod_state

    from .targets import load_target

    try:
        target = load_target(name)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Check if it's a RunPod target
    from wafer_core.utils.kernel_utils.targets.config import RunPodTarget

    if not isinstance(target, RunPodTarget):
        typer.echo(
            f"Error: {name} is not a RunPod target (type: {type(target).__name__})", err=True
        )
        raise typer.Exit(1) from None

    # Check current state
    state = get_pod_state(name)
    if not state:
        typer.echo(f"No running pod found for target: {name}")
        return

    typer.echo(f"Found pod {state.pod_id} for target {name}")
    typer.echo(f"  IP: {state.public_ip}:{state.ssh_port}")
    typer.echo(f"  Created: {state.created_at}")
    typer.echo("Terminating...")

    async def _cleanup() -> bool:
        return await cleanup_target(name)

    success = trio.run(_cleanup)

    if success:
        typer.echo("Pod terminated successfully")
    else:
        typer.echo("Failed to terminate pod", err=True)
        raise typer.Exit(1) from None


# Known libraries that can be installed on targets
# TODO: Consider adding HipKittens to the default RunPod/DO Docker images
# so this install step isn't needed. For now, this command handles it.
# Architecture → branch mapping for libraries that ship per-arch branches.
# "default" is used when the detected arch has no explicit entry.
_ARCH_BRANCHES: dict[str, dict[str, str]] = {
    "hipkittens": {
        "gfx942": "cdna3",  # MI300X, MI325X
        "default": "main",  # MI350X, MI355X, and future CDNA4+
    },
}

INSTALLABLE_LIBRARIES: dict[str, dict[str, object]] = {
    "hipkittens": {
        "description": "HipKittens - AMD port of ThunderKittens",
        "git_url": "https://github.com/HazyResearch/HipKittens.git",
        "install_path": "/opt/hipkittens",
        "requires_amd": True,
    },
    # CK is already installed with ROCm 7.0, no action needed
    "repair-headers": {
        "description": "Repair ROCm thrust headers (fixes hipify corruption)",
        "custom_script": "apt-get update -qq && apt-get install --reinstall -y rocthrust >/dev/null 2>&1 && echo REPAIRED",
        "requires_amd": True,
    },
}


def _resolve_gfx_arch(target: object, ssh_cmd: list[str]) -> str | None:
    """Return the gfx architecture string for *target*.

    1. If the target config already carries a compute_capability, map it.
    2. Otherwise SSH in and probe with ``rocminfo``.
    Returns None only if detection fails entirely.
    """
    import subprocess

    from .evaluate import AMD_CC_TO_ARCH

    cc = getattr(target, "compute_capability", None)
    if cc and cc in AMD_CC_TO_ARCH:
        return AMD_CC_TO_ARCH[cc]

    typer.echo("  Detecting GPU architecture via rocminfo...")
    probe_script = "rocminfo 2>/dev/null | grep -oP 'gfx\\d+' | head -1"
    result = subprocess.run(
        ssh_cmd + [probe_script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    arch = result.stdout.strip()
    if result.returncode == 0 and arch.startswith("gfx"):
        typer.echo(f"  Detected: {arch}")
        return arch

    typer.echo("  Warning: could not detect GPU architecture", err=True)
    return None


@targets_app.command("install")
def targets_install(
    name: str = typer.Argument(..., help="Target name"),
    library: str = typer.Argument(..., help="Library to install (hipkittens, repair-headers)"),
) -> None:
    """Install a library or run maintenance on a target (idempotent).

    Installs header-only libraries like HipKittens on remote targets.
    Safe to run multiple times - will skip if already installed.

    For libraries with per-architecture branches (e.g. HipKittens), the
    correct branch is selected automatically based on the target's GPU.

    Available libraries:
        hipkittens     - HipKittens (AMD ThunderKittens port)
        repair-headers - Fix ROCm thrust headers (after hipify corruption)

    Examples:
        wafer config targets install runpod-mi300x hipkittens
        wafer config targets install runpod-mi300x repair-headers
        wafer config targets install do-mi300x hipkittens
    """
    import subprocess

    from .targets import load_target
    from .targets_ops import get_target_ssh_info

    if library not in INSTALLABLE_LIBRARIES:
        available = ", ".join(INSTALLABLE_LIBRARIES.keys())
        typer.echo(f"Error: Unknown library '{library}'. Available: {available}", err=True)
        raise typer.Exit(1)

    lib_info = INSTALLABLE_LIBRARIES[library]

    try:
        target = load_target(name)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Check if target is AMD (for AMD-only libraries)
    if lib_info.get("requires_amd"):
        from wafer_core.utils.kernel_utils.targets.config import (
            DigitalOceanTarget,
            RunPodTarget,
        )

        is_amd = isinstance(target, (RunPodTarget, DigitalOceanTarget))
        if not is_amd and hasattr(target, "compute_capability"):
            # Check compute capability for MI300X (gfx942 = 9.4)
            is_amd = target.compute_capability.startswith("9.")
        if not is_amd:
            typer.echo(f"Error: {library} requires an AMD GPU target", err=True)
            raise typer.Exit(1)

    typer.echo(f"Installing {library} on {name}...")
    typer.echo(f"  {lib_info['description']}")

    async def _install() -> bool:
        # get_target_ssh_info uses pure trio async (no asyncio bridging needed)
        # and we use subprocess for SSH, not AsyncSSHClient
        ssh_info = await get_target_ssh_info(target)

        ssh_cmd = [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-o",
            "ConnectTimeout=30",
            "-i",
            str(ssh_info.key_path),
            "-p",
            str(ssh_info.port),
            f"{ssh_info.user}@{ssh_info.host}",
        ]

        # Handle custom scripts (like repair-headers) vs git installs
        if "custom_script" in lib_info:
            install_script = str(lib_info["custom_script"])
            success_marker = "REPAIRED"
        else:
            install_path = lib_info["install_path"]
            git_url = lib_info["git_url"]

            # Resolve the branch for arch-aware libraries
            branch = "main"
            arch_map = _ARCH_BRANCHES.get(library)
            if arch_map:
                gfx = await trio.to_thread.run_sync(lambda: _resolve_gfx_arch(target, ssh_cmd))
                branch = arch_map.get(gfx, arch_map["default"]) if gfx else arch_map["default"]
                typer.echo(f"  Branch: {branch} (arch={gfx or 'unknown'})")

            # Idempotent: if already cloned, ensure correct branch & pull
            install_script = f"""
if [ -d "{install_path}" ]; then
    echo "ALREADY_INSTALLED: {install_path} exists"
    cd {install_path} && git fetch --quiet origin && git checkout {branch} --quiet && git pull --quiet origin {branch}
else
    echo "INSTALLING: cloning to {install_path}"
    git clone --quiet --branch {branch} {git_url} {install_path}
fi
echo "DONE"
"""
            success_marker = "DONE"

        def run_ssh() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ssh_cmd + [install_script],
                capture_output=True,
                text=True,
                timeout=120,
            )

        result = await trio.to_thread.run_sync(run_ssh)

        if result.returncode != 0:
            typer.echo(f"Error: {result.stderr}", err=True)
            return False

        output = result.stdout.strip()
        if "ALREADY_INSTALLED" in output:
            typer.echo(f"  Already installed at {lib_info.get('install_path', 'N/A')}")
        elif "INSTALLING" in output:
            typer.echo(f"  Installed to {lib_info.get('install_path', 'N/A')}")
        elif "REPAIRED" in output:
            typer.echo("  ROCm headers repaired")

        return success_marker in output

    try:
        success = trio.run(_install)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if success:
        typer.echo(f"✓ {library} ready on {name}")

        # Print usage hint
        if library == "hipkittens":
            typer.echo("")
            typer.echo("Usage in load_inline:")
            typer.echo('  extra_include_paths=["/opt/hipkittens/include", "/opt/rocm/include/hip"]')
    else:
        typer.echo(f"Failed to install {library}", err=True)
        raise typer.Exit(1)


@targets_app.command("pods")
def targets_pods() -> None:
    """List all running RunPod pods.

    Shows pods from the state file that are still running.

    Example:
        wafer config targets pods
    """
    import trio
    from wafer_core.targets.runpod import list_running_pods

    async def _list() -> list:
        return await list_running_pods()

    pods = trio.run(_list)

    if not pods:
        typer.echo("No running RunPod pods found")
        return

    typer.echo(f"Found {len(pods)} running pod(s):\n")
    for pod in pods:
        typer.echo(f"  Target: {pod.target_name}")
        typer.echo(f"  Pod ID: {pod.pod_id}")
        typer.echo(f"  SSH: {pod.ssh_username}@{pod.public_ip}:{pod.ssh_port}")
        typer.echo(f"  Created: {pod.created_at}")
        typer.echo()


# ── Pool commands ───────────────────────────────────────────────────────────


@targets_app.command("pool-list")
def targets_pool_list() -> None:
    """List all configured target pools.

    Example:
        wafer config targets pool-list
    """
    from .targets import get_pool, list_pools

    pools = list_pools()

    if not pools:
        typer.echo("No pools configured")
        typer.echo("")
        typer.echo("Define pools in ~/.wafer/config.toml:")
        typer.echo("  [pools.my-pool]")
        typer.echo('  targets = ["target-1", "target-2"]')
        return

    typer.echo("Configured pools:\n")
    for pool_name in pools:
        try:
            targets = get_pool(pool_name)
            typer.echo(f"  {pool_name}: {', '.join(targets)}")
        except Exception as e:
            typer.echo(f"  {pool_name}: (error: {e})")


@targets_app.command("pool-create")
def targets_pool_create(
    name: str = typer.Argument(..., help="Pool name"),
    targets: list[str] = typer.Argument(..., help="Target names to include in pool"),
) -> None:
    """Create or update a target pool.

    Example:
        wafer config targets pool-create mi300x-pool mi300x-1 mi300x-2 mi300x-3
    """
    from .targets import save_pool

    try:
        save_pool(name, targets)
        typer.echo(f"Pool '{name}' created with {len(targets)} targets")
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@targets_app.command("pool-status")
def targets_pool_status(
    name: str = typer.Argument(..., help="Pool name"),
) -> None:
    """Show status of targets in a pool (locked/available).

    Example:
        wafer config targets pool-status mi300x-pool
    """
    from .target_lock import get_lock_holder, is_target_locked
    from .targets import get_pool

    try:
        targets = get_pool(name)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Pool '{name}' ({len(targets)} targets):\n")

    available = 0
    for target_name in targets:
        locked = is_target_locked(target_name)
        if locked:
            pid = get_lock_holder(target_name)
            pid_str = f" (pid {pid})" if pid else ""
            typer.echo(f"  [busy]  {target_name}{pid_str}")
        else:
            typer.echo(f"  [free]  {target_name}")
            available += 1

    typer.echo("")
    typer.echo(f"Available: {available}/{len(targets)}")


# =============================================================================
# Billing commands
# =============================================================================


@billing_app.callback(invoke_without_command=True)
def billing_usage(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show current billing usage and subscription info.

    Example:
        wafer billing
        wafer billing --json
    """
    # Only show usage if no subcommand was invoked
    if ctx.invoked_subcommand is not None:
        return

    from .billing import get_usage

    try:
        result = get_usage(json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@billing_app.command("topup")
def billing_topup(
    amount: int = typer.Argument(25, help="Amount in dollars ($10-$500)"),
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print URL instead of opening browser"
    ),
) -> None:
    """Add credits to your account.

    Opens a Stripe checkout page to add credits. Default amount is $25.

    Example:
        wafer billing topup        # Add $25
        wafer billing topup 100    # Add $100
        wafer billing topup --no-browser  # Print URL instead
    """
    import webbrowser

    from .billing import create_topup, validate_topup_amount

    # Convert dollars to cents
    amount_cents = amount * 100

    # Validate amount client-side before API call
    try:
        validate_topup_amount(amount_cents)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    try:
        result = create_topup(amount_cents)
        checkout_url = result.get("checkout_url")

        if not checkout_url:
            typer.echo("Error: No checkout URL received from API", err=True)
            raise typer.Exit(1) from None

        if no_browser:
            typer.echo(f"Complete your purchase at:\n{checkout_url}")
        else:
            typer.echo(f"Opening checkout for ${amount}...")
            webbrowser.open(checkout_url)
            typer.echo("Browser opened. Complete your purchase there.")
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@billing_app.command("portal")
def billing_portal(
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print URL instead of opening browser"
    ),
) -> None:
    """Open Stripe billing portal.

    Manage your subscription, update payment method, or view invoices.

    Example:
        wafer billing portal
        wafer billing portal --no-browser
    """
    import webbrowser

    from .billing import get_portal_url

    try:
        result = get_portal_url()
        portal_url = result.get("portal_url")

        if not portal_url:
            typer.echo("Error: No portal URL received from API", err=True)
            raise typer.Exit(1) from None

        if no_browser:
            typer.echo(f"Billing portal:\n{portal_url}")
        else:
            typer.echo("Opening billing portal...")
            webbrowser.open(portal_url)
            typer.echo("Browser opened.")
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# =============================================================================
# SSH Keys commands (BYOK - Bring Your Own Key)
# =============================================================================


@ssh_keys_app.command("list")
def ssh_keys_list(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all registered SSH public keys.

    Example:
        wafer ssh-keys list
        wafer ssh-keys list --json
    """
    from .ssh_keys import list_ssh_keys

    try:
        result = list_ssh_keys(json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@ssh_keys_app.command("add")
def ssh_keys_add(
    pubkey_path: Path | None = typer.Argument(
        None, help="Path to public key file (auto-detects ~/.ssh/id_ed25519.pub if not specified)"
    ),
    name: str | None = typer.Option(None, "--name", "-n", help="Friendly name for the key"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Add an SSH public key.

    If no path is specified, auto-detects keys from ~/.ssh/ in preference order:
    id_ed25519.pub, id_rsa.pub, id_ecdsa.pub.

    Example:
        wafer ssh-keys add                              # Auto-detect
        wafer ssh-keys add ~/.ssh/id_rsa.pub            # Specific file
        wafer ssh-keys add ~/.ssh/id_ed25519.pub --name laptop
    """
    from .ssh_keys import add_ssh_key

    try:
        result = add_ssh_key(pubkey_path=pubkey_path, name=name, json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@ssh_keys_app.command("remove")
def ssh_keys_remove(
    key_id: str = typer.Argument(..., help="UUID of the SSH key to remove"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Remove an SSH public key.

    Get the key ID from 'wafer ssh-keys list'.

    Example:
        wafer ssh-keys remove abc123-def456-...
    """
    from .ssh_keys import remove_ssh_key

    try:
        result = remove_ssh_key(key_id=key_id, json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


# =============================================================================
# Workspaces commands
# =============================================================================


@workspaces_app.command("list")
def workspaces_list(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all workspaces.

    Example:
        wafer workspaces list
        wafer workspaces list --json
    """
    from .workspaces import list_workspaces

    try:
        result = list_workspaces(json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@workspaces_app.command("create")
def workspaces_create(
    name: str = typer.Argument(..., help="Workspace name"),
    gpu_type: str = typer.Option(
        "B200", "--gpu", "-g", help="GPU type: MI300X (AMD) or B200 (NVIDIA, default)"
    ),
    image: str | None = typer.Option(None, "--image", "-i", help="Docker image (optional)"),
    wait: bool = typer.Option(
        False, "--wait", "-w", help="Wait for provisioning and show SSH credentials"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Create a new workspace.

    Available GPUs:
        MI300X  AMD Instinct MI300X (192GB HBM3, ROCm)
        B200    NVIDIA Blackwell B200 (180GB HBM3e, CUDA)

    Example:
        wafer workspaces create my-kernel                # B200 (default)
        wafer workspaces create my-kernel --gpu MI300X   # AMD MI300X
        wafer workspaces create my-kernel --gpu B200     # NVIDIA B200
        wafer workspaces create my-kernel --image pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel
        wafer workspaces create my-kernel --wait
    """
    from .workspaces import create_workspace

    try:
        result = create_workspace(
            name,
            gpu_type=gpu_type,
            image=image,
            wait=wait,
            json_output=json_output,
        )
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@workspaces_app.command("delete")
def workspaces_delete(
    workspace_id: str = typer.Argument(..., help="Workspace ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Delete a workspace.

    Example:
        wafer workspaces delete ws_abc123
        wafer workspaces delete ws_abc123 -y
    """
    from .workspaces import delete_workspace

    try:
        if not yes:
            confirm = typer.confirm(f"Delete workspace '{workspace_id}'?")
            if not confirm:
                typer.echo("Cancelled.")
                raise typer.Exit(0)
        result = delete_workspace(workspace_id, json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@workspaces_app.command("show")
def workspaces_show(
    workspace_id: str = typer.Argument(..., help="Workspace ID to show"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show details of a workspace.

    Example:
        wafer workspaces show ws_abc123
        wafer workspaces show ws_abc123 --json
    """
    from .workspaces import get_workspace

    try:
        result = get_workspace(workspace_id, json_output=json_output)
        typer.echo(result)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@workspaces_app.command(
    "exec",
    context_settings={
        "allow_interspersed_args": False,
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
)
def workspaces_exec(
    ctx: typer.Context,
    workspace: str | None = typer.Argument(
        None, help="Workspace name or ID (optional if default set)"
    ),
    timeout: int | None = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Execution timeout in seconds (default: from config or 300)",
    ),
    sync: Path | None = typer.Option(
        None,
        "--sync",
        "-s",
        help="Sync local directory to workspace before executing",
    ),
    gpu: bool = typer.Option(False, "--gpu", help="Force GPU routing (default behavior)"),
    cpu: bool = typer.Option(False, "--cpu", help="Run in workspace container (no GPU)"),
    baremetal: bool = typer.Option(
        False, "--baremetal", help="Force baremetal target (for hardware counters like ncu/nsys)"
    ),
    pull_image: bool = typer.Option(False, "--pull-image", help="Pull image on target if missing"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Execute a command in workspace.

    By default, auto-detects whether to route to GPU based on the command.
    Use --gpu, --cpu, or --baremetal to override.

    Routing options:
      --gpu       Force GPU container (Modal or baremetal with GPU)
      --cpu       Run in workspace container directly (no GPU)
      --baremetal Force baremetal target (for ncu, nsys, hardware counters)

    If workspace is not specified, uses the default workspace from config,
    or the only workspace if you have exactly one.

    IMPORTANT: Options must come before the workspace name.

    Examples:
        wafer workspaces exec dev -- python train.py
        wafer workspaces exec dev -- python -c "import torch; print(torch.cuda.is_available())"
        wafer workspaces exec -- python train.py             # uses default workspace
        wafer workspaces exec dev "make && ./kernel" --timeout 600
        wafer workspaces exec dev --sync . -- python train.py  # sync first, then run
    """
    from .global_config import get_defaults, get_preferences
    from .workspaces import exec_command, resolve_workspace, sync_files

    # Enforce option ordering to avoid treating CLI flags as remote commands
    known_options = {
        "--timeout",
        "-t",
        "--sync",
        "-s",
        "--gpu",
        "--cpu",
        "--baremetal",
        "--pull-image",
        "--verbose",
        "-v",
        "--quiet",
        "-q",
        "--help",
        "-h",
    }
    for arg in ctx.args:
        if arg == "--":
            break
        if arg in known_options:
            typer.echo(
                "Error: options must come before the workspace name. "
                "Example: wafer workspaces exec --pull-image dev -- python -V",
                err=True,
            )
            raise typer.Exit(1)

    # Validate mutually exclusive routing flags
    routing_flags = sum([gpu, cpu, baremetal])
    if routing_flags > 1:
        typer.echo("Error: --gpu, --cpu, and --baremetal are mutually exclusive", err=True)
        raise typer.Exit(1)

    # Determine routing (None = auto-detect)
    routing: str | None = None
    if gpu:
        routing = "gpu"
    elif cpu:
        routing = "cpu"
    elif baremetal:
        routing = "baremetal"

    # Resolve workspace (specified, config default, or single workspace)
    try:
        resolved_workspace = resolve_workspace(workspace)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Use config default if no timeout specified
    effective_timeout = timeout
    if effective_timeout is None:
        defaults = get_defaults()
        effective_timeout = defaults.exec_timeout

    # Determine verbosity based on mode (explicit = verbose by default)
    # --quiet flag overrides mode, --verbose flag forces verbose
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    if show_status:
        routing_label = routing or "auto"
        typer.echo(f"[wafer] Workspace: {resolved_workspace} (routing: {routing_label})", err=True)

    # Sync files if requested
    if sync is not None:
        if not sync.exists():
            typer.echo(f"Error: Sync path not found: {sync}", err=True)
            raise typer.Exit(1)
        if not sync.is_dir():
            typer.echo(f"Error: Sync path is not a directory: {sync}", err=True)
            raise typer.Exit(1)

        if show_status:
            typer.echo(f"[wafer] Syncing {sync}...", err=True)

        def on_progress(msg: str) -> None:
            if show_status:
                typer.echo(f"[wafer] {msg}", err=True)

        try:
            file_count, warning = sync_files(
                resolved_workspace, sync.resolve(), on_progress=on_progress
            )
        except RuntimeError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None

    # Get command from context args (passthrough after --)
    import shlex

    command = list(ctx.args)
    if command and command[0] == "--":
        command = command[1:]

    if not command:
        typer.echo("Error: No command specified", err=True)
        raise typer.Exit(1)

    if show_status:
        typer.echo(f"[wafer] Executing (timeout: {effective_timeout}s)...", err=True)

    # Build command string
    # Handle two cases:
    # 1. Single element: user quoted the whole command (e.g., "echo hello world")
    #    -> use directly, don't re-quote
    # 2. Multiple elements: user passed separate args (e.g., -- python -c "print(1)")
    #    -> use shlex.join to properly quote args with spaces
    if len(command) == 1:
        command_str = command[0]
    else:
        command_str = shlex.join(command)

    try:
        exit_code = exec_command(
            workspace_id=resolved_workspace,
            command=command_str,
            timeout_seconds=effective_timeout,
            routing=routing,
            pull_image=pull_image,
        )
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Exit code: {exit_code}", err=True)

    raise typer.Exit(exit_code)


@workspaces_app.command("ssh")
def workspaces_ssh(
    workspace: str | None = typer.Argument(
        None, help="Workspace name or ID (optional if default set)"
    ),
) -> None:
    """SSH into a workspace.

    Examples:
        wafer workspaces ssh dev
        wafer workspaces ssh           # uses default workspace
    """
    import os

    from .workspaces import get_workspace_raw, resolve_workspace

    # Resolve workspace name/ID
    try:
        resolved_workspace = resolve_workspace(workspace)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Get workspace SSH credentials
    try:
        ws = get_workspace_raw(resolved_workspace)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    ssh_host = ws.get("ssh_host")
    ssh_port = ws.get("ssh_port")
    ssh_user = ws.get("ssh_user")

    if not ssh_host or not ssh_port or not ssh_user:
        typer.echo("Error: Workspace not ready. Wait a few seconds and retry.", err=True)
        raise typer.Exit(1)

    # Connect via SSH
    os.execvp(
        "ssh",
        [
            "ssh",
            "-p",
            str(ssh_port),
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"{ssh_user}@{ssh_host}",
        ],
    )


@workspaces_app.command("sync")
def workspaces_sync(
    workspace: str | None = typer.Argument(
        None, help="Workspace name or ID (optional if default set)"
    ),
    path: Path = typer.Argument(..., help="Local file or directory to sync"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Sync local files to workspace.

    Uses rsync over SSH to sync files to the workspace's /workspace directory.
    If workspace is not specified, uses the default workspace.

    Examples:
        wafer workspaces sync dev ./my-project
        wafer workspaces sync ./my-project        # uses default workspace
        wafer workspaces sync dev .               # sync current directory
        wafer workspaces sync dev ./script.py     # sync single file
    """
    from .global_config import get_preferences
    from .workspaces import resolve_workspace, sync_files

    # Determine verbosity based on mode
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    # Validate path
    if not path.exists():
        typer.echo(f"Error: Path not found: {path}", err=True)
        raise typer.Exit(1)

    # Resolve workspace
    try:
        resolved_workspace = resolve_workspace(workspace)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Syncing {path} to workspace {resolved_workspace}...", err=True)

    def on_progress(msg: str) -> None:
        if show_status:
            typer.echo(f"[wafer] {msg}", err=True)

    try:
        file_count, warning = sync_files(
            resolved_workspace, path.resolve(), on_progress=on_progress
        )
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@workspaces_app.command("pull")
def workspaces_pull(
    workspace: str = typer.Argument(..., help="Workspace name or ID"),
    remote_path: str = typer.Argument(
        ..., help="Remote path in workspace (relative to /workspace or absolute)"
    ),
    local_path: Path = typer.Argument(
        Path("."), help="Local destination path (default: current directory)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Pull files from workspace to local machine.

    Uses rsync over SSH to download files from the workspace's /workspace directory.

    Examples:
        wafer workspaces pull dev kernel.py ./           # Pull single file
        wafer workspaces pull dev kernel.py ./my_kernel.py  # Pull and rename
        wafer workspaces pull dev /workspace/results ./  # Pull directory
    """
    from .global_config import get_preferences
    from .workspaces import pull_files

    # Determine verbosity based on mode
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    if show_status:
        typer.echo(f"[wafer] Pulling {remote_path} from workspace {workspace}...", err=True)

    def on_progress(msg: str) -> None:
        if show_status:
            typer.echo(f"[wafer] {msg}", err=True)

    try:
        file_count = pull_files(
            workspace, remote_path, local_path.resolve(), on_progress=on_progress
        )
        if show_status:
            typer.echo(f"[wafer] Pulled {file_count} files to {local_path}", err=True)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# =============================================================================
# Target operations commands (exec/ssh/sync)
# =============================================================================


@targets_ops_app.command("exec", context_settings={"allow_interspersed_args": False})
def targets_exec(
    target: str = typer.Argument(
        ...,
        help="Target name",
        autocompletion=complete_target_name,
    ),
    command: list[str] = typer.Argument(..., help="Command to execute"),
    timeout: int | None = typer.Option(
        None,
        "--timeout",
        "-t",
        help="Execution timeout in seconds (default: 300)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Execute a command on a configured target.

    Provisions the target if needed (RunPod, DigitalOcean), then runs the command via SSH.
    For cloud targets, the instance is kept alive after execution - use
    'wafer config targets cleanup <name>' to terminate.

    Supported targets: RunPod, DigitalOcean, SSH (baremetal/vm).
    Not supported: Modal (serverless), Local (no SSH), Workspace (use 'wafer workspaces exec').

    Examples:
        wafer targets exec runpod-mi300x -- python -c "import torch; print(torch.cuda.is_available())"
        wafer targets exec runpod-mi300x -- rocm-smi
        wafer targets exec my-ssh-server -- nvidia-smi
        wafer targets exec runpod-mi300x "echo hello && ls -la" --timeout 60
    """
    from .global_config import get_preferences
    from .targets import load_target
    from .targets_ops import TargetExecError, exec_on_target_sync, get_target_ssh_info

    # Determine verbosity
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    # Load target
    try:
        target_config = load_target(target)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("List available targets with: wafer config targets list", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error loading target config: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Target: {target} ({type(target_config).__name__})", err=True)

    # Get SSH info (may provision)
    if show_status:
        typer.echo("[wafer] Connecting to target...", err=True)

    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Connected: {ssh_info.user}@{ssh_info.host}:{ssh_info.port}", err=True)

    # Build command string
    if isinstance(command, list):
        import shlex

        # Remove leading "--" if present
        if command and command[0] == "--":
            command = command[1:]

        if not command:
            typer.echo("Error: No command specified", err=True)
            raise typer.Exit(1)

        if len(command) == 1:
            command_str = command[0]
        else:
            command_str = shlex.join(command)
    else:
        command_str = command

    # Default timeout
    effective_timeout = timeout if timeout is not None else 300

    if show_status:
        typer.echo(f"[wafer] Executing (timeout: {effective_timeout}s)...", err=True)

    # Execute
    try:
        exit_code = exec_on_target_sync(ssh_info, command_str, effective_timeout)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Exit code: {exit_code}", err=True)

    raise typer.Exit(exit_code)


@targets_ops_app.command("ssh")
def targets_ssh(
    target: str = typer.Argument(
        ...,
        help="Target name",
        autocompletion=complete_target_name,
    ),
) -> None:
    """SSH into a configured target.

    Provisions the target if needed (RunPod, DigitalOcean), then starts an interactive SSH session.
    For cloud targets, the instance is kept alive - use 'wafer config targets cleanup <name>' to terminate.

    Examples:
        wafer targets ssh runpod-mi300x
        wafer targets ssh my-baremetal-server
    """
    from .targets import load_target
    from .targets_ops import TargetExecError, get_target_ssh_info

    # Load target
    try:
        target_config = load_target(target)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("List available targets with: wafer config targets list", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error loading target config: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Connecting to target: {target}...", err=True)

    # Get SSH info (may provision)
    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # Build SSH command
    ssh_args = [
        "ssh",
        "-i",
        str(ssh_info.key_path),
        "-p",
        str(ssh_info.port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        f"{ssh_info.user}@{ssh_info.host}",
    ]

    # Replace current process with SSH
    os.execvp("ssh", ssh_args)


@targets_ops_app.command("sync")
def targets_sync(
    target: str = typer.Argument(
        ...,
        help="Target name",
        autocompletion=complete_target_name,
    ),
    path: Path = typer.Argument(..., help="Local file or directory to sync"),
    dest: str | None = typer.Option(
        None,
        "--dest",
        "-d",
        help="Remote destination path (default: /tmp/<basename>)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Sync local files to a configured target.

    Uses rsync over SSH to copy files to the target. Provisions the target if needed.

    Examples:
        wafer targets sync runpod-mi300x ./my-project
        wafer targets sync runpod-mi300x ./script.py --dest /workspace/script.py
        wafer targets sync my-server ./kernels --dest /tmp/kernels
    """
    from .global_config import get_preferences
    from .targets import load_target
    from .targets_ops import TargetExecError, get_target_ssh_info, sync_to_target

    # Determine verbosity
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    # Validate path
    if not path.exists():
        typer.echo(f"Error: Path not found: {path}", err=True)
        raise typer.Exit(1)

    # Load target
    try:
        target_config = load_target(target)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("List available targets with: wafer config targets list", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error loading target config: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Target: {target} ({type(target_config).__name__})", err=True)

    # Get SSH info (may provision)
    if show_status:
        typer.echo("[wafer] Connecting to target...", err=True)

    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Connected: {ssh_info.user}@{ssh_info.host}:{ssh_info.port}", err=True)

    # Sync
    def on_progress(msg: str) -> None:
        if show_status:
            typer.echo(f"[wafer] {msg}", err=True)

    try:
        file_count = sync_to_target(ssh_info, path.resolve(), dest, on_progress)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Done. Synced {file_count} files.", err=True)


@targets_ops_app.command("scp")
def targets_scp(
    source: str = typer.Argument(..., help="Source path (prefix with target: for remote)"),
    dest: str = typer.Argument(..., help="Destination path (prefix with target: for remote)"),
    recursive: bool = typer.Option(False, "-r", "--recursive", help="Copy directories recursively"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Copy files to/from a target using scp-style syntax.

    Use target: prefix to indicate remote paths. Exactly one of source or dest
    must be remote.

    Examples:
        wafer targets scp runpod-mi300x:/tmp/trace.json ./trace.json  # download
        wafer targets scp ./script.py runpod-mi300x:/tmp/script.py    # upload
        wafer targets scp -r ./kernels runpod-mi300x:/tmp/kernels     # upload dir
        wafer targets scp -r runpod-mi300x:/tmp/results ./results     # download dir
    """
    from .global_config import get_preferences
    from .targets import load_target
    from .targets_ops import TargetExecError, get_target_ssh_info, parse_scp_path, scp_transfer

    # Determine verbosity
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    # Parse source and dest
    source_target, source_path = parse_scp_path(source)
    dest_target, dest_path = parse_scp_path(dest)

    # Validate: exactly one must be remote
    if source_target and dest_target:
        typer.echo("Error: Both paths are remote. Use ssh to transfer between remotes.", err=True)
        raise typer.Exit(1)

    if not source_target and not dest_target:
        typer.echo("Error: Both paths are local. Use regular cp command.", err=True)
        raise typer.Exit(1)

    # Determine direction and target
    is_download = source_target is not None
    target_name = source_target if is_download else dest_target

    # Load target
    try:
        target_config = load_target(target_name)
    except FileNotFoundError:
        typer.echo(f"Error: Target '{target_name}' not found.", err=True)
        typer.echo("Run 'wafer config targets list' to see available targets.", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error loading target config: {e}", err=True)
        raise typer.Exit(1) from None

    # Validate local path exists (for upload)
    if not is_download:
        local_path = Path(source_path)
        if not local_path.exists():
            typer.echo(f"Error: Local path '{source_path}' does not exist.", err=True)
            raise typer.Exit(1)
        if local_path.is_dir() and not recursive:
            typer.echo(
                f"Error: '{source_path}' is a directory. Use -r flag for recursive copy.", err=True
            )
            raise typer.Exit(1)

    if show_status:
        typer.echo(f"[wafer] Target: {target_name} ({type(target_config).__name__})", err=True)
        typer.echo("[wafer] Connecting to target...", err=True)

    # Get SSH info (may provision)
    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Connected: {ssh_info.user}@{ssh_info.host}:{ssh_info.port}", err=True)
        direction = "Downloading" if is_download else "Uploading"
        typer.echo(f"[wafer] {direction}...", err=True)

    # Transfer
    try:
        if is_download:
            scp_transfer(ssh_info, source_path, dest_path, is_download=True, recursive=recursive)
        else:
            scp_transfer(ssh_info, source_path, dest_path, is_download=False, recursive=recursive)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo("[wafer] Done.", err=True)


@targets_ops_app.command("ensure")
def targets_ensure(  # noqa: PLR0915
    target: str = typer.Argument(
        None,
        help="Target name",
        autocompletion=complete_target_name,
    ),
    tool: str = typer.Argument(None, help="Tool to ensure is installed"),
    check_only: bool = typer.Option(False, "--check-only", "-c", help="Only check, don't install"),
    force: bool = typer.Option(False, "--force", "-f", help="Reinstall even if present"),
    list_tools: bool = typer.Option(False, "--list", "-l", help="List available tools"),
    timeout: int = typer.Option(300, "--timeout", "-t", help="Installation timeout in seconds"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show [wafer] status messages"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress [wafer] status messages"),
) -> None:
    """Ensure a tool is installed on a target.

    Checks if a tool exists on the target and installs it if missing.
    Useful for profiling tools like rocprof-compute that aren't pre-installed.

    Examples:
        wafer targets ensure runpod-mi300x rocprof-compute
        wafer targets ensure runpod-mi300x rocprof-compute --check-only
        wafer targets ensure runpod-mi300x rocprof-compute --force
        wafer targets ensure --list
    """
    from .global_config import get_preferences
    from .targets import load_target
    from .targets_ops import (
        TOOL_REGISTRY,
        TargetExecError,
        ensure_tool,
        get_target_platform,
        get_target_ssh_info,
    )

    # Handle --list flag
    if list_tools:
        typer.echo("Available tools:\n")
        typer.echo("AMD tools:")
        for name, spec in sorted(TOOL_REGISTRY.items()):
            if spec.platform == "amd":
                auto = "auto-install" if spec.install_cmd else "manual"
                typer.echo(f"  {name:20} ({auto}) - {spec.description}")

        typer.echo("\nNVIDIA tools:")
        for name, spec in sorted(TOOL_REGISTRY.items()):
            if spec.platform == "nvidia":
                auto = "auto-install" if spec.install_cmd else "manual"
                typer.echo(f"  {name:20} ({auto}) - {spec.description}")

        typer.echo("\nCross-platform:")
        for name, spec in sorted(TOOL_REGISTRY.items()):
            if spec.platform == "any":
                auto = "auto-install" if spec.install_cmd else "manual"
                typer.echo(f"  {name:20} ({auto}) - {spec.description}")
        return

    # Require target and tool if not listing
    if not target:
        typer.echo("Error: Missing argument 'TARGET'", err=True)
        typer.echo("Usage: wafer targets ensure TARGET TOOL", err=True)
        typer.echo("   or: wafer targets ensure --list", err=True)
        raise typer.Exit(1)

    if not tool:
        typer.echo("Error: Missing argument 'TOOL'", err=True)
        typer.echo("Usage: wafer targets ensure TARGET TOOL", err=True)
        typer.echo("   or: wafer targets ensure --list", err=True)
        raise typer.Exit(1)

    # Check tool exists
    if tool not in TOOL_REGISTRY:
        typer.echo(f"Error: Unknown tool '{tool}'", err=True)
        typer.echo(f"Available tools: {', '.join(sorted(TOOL_REGISTRY.keys()))}", err=True)
        typer.echo("Run 'wafer targets ensure --list' for details.", err=True)
        raise typer.Exit(1)

    spec = TOOL_REGISTRY[tool]

    # Determine verbosity
    prefs = get_preferences()
    if quiet:
        show_status = False
    elif verbose:
        show_status = True
    else:
        show_status = prefs.mode == "explicit"

    # Load target
    try:
        target_config = load_target(target)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        typer.echo("List available targets with: wafer config targets list", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error loading target config: {e}", err=True)
        raise typer.Exit(1) from None

    # Platform validation
    platform = get_target_platform(target_config)
    if spec.platform != "any" and spec.platform != platform:
        typer.echo(
            f"Error: {tool} is an {spec.platform.upper()} tool but target '{target}' "
            f"is {platform.upper()}",
            err=True,
        )
        raise typer.Exit(1)

    if show_status:
        typer.echo(f"[wafer] Target: {target} ({platform.upper()})", err=True)
        typer.echo(f"[wafer] Checking for {tool}...", err=True)

    # Get SSH info (may provision)
    try:
        ssh_info = trio.run(get_target_ssh_info, target_config)
    except TargetExecError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if show_status:
        typer.echo(f"[wafer] Connected: {ssh_info.user}@{ssh_info.host}:{ssh_info.port}", err=True)

    # Check-only mode
    if check_only:
        from .targets_ops import TargetExecError, exec_on_target_sync

        try:
            exit_code = exec_on_target_sync(ssh_info, spec.check_cmd, timeout_seconds=30)
        except TargetExecError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from None
        if exit_code == 0:
            typer.echo(f"{tool} is installed")
        else:
            typer.echo(f"{tool} is NOT installed", err=True)
            raise typer.Exit(1)
        return

    # Ensure tool is installed
    result = ensure_tool(ssh_info, tool, force=force, timeout=timeout)

    if result.error:
        typer.echo(f"Error: {result.error}", err=True)
        raise typer.Exit(1)

    if result.already_installed:
        typer.echo(f"{tool} is already installed")
    elif result.installed:
        if result.verified:
            typer.echo(f"{tool} installed successfully")
        else:
            typer.echo(f"{tool} installed (verification skipped)")


# =============================================================================
# Perfetto trace analysis commands
# =============================================================================


@perfetto_app.command("query")
def perfetto_query(
    trace_path: Path = typer.Argument(..., help="Path to Perfetto trace file"),
    sql: str = typer.Argument(..., help="SQL query to execute"),
    json_output: bool = typer.Option(True, "--json", "-j", help="Output as JSON"),
) -> None:
    """Execute SQL query against a Perfetto trace.

    Starts trace_processor, loads the trace, executes the query, and returns results.

    Examples:
        wafer perfetto query trace.perfetto "SELECT * FROM slice LIMIT 10"
        wafer perfetto query trace.perfetto "SELECT name, dur FROM slice ORDER BY dur DESC LIMIT 5"
    """
    from wafer_core.lib.perfetto.perfetto_tool import PerfettoConfig, PerfettoTool

    config = PerfettoConfig(
        workspace_root=".",
        storage_dir=str(Path.home() / ".wafer" / "perfetto"),
    )
    tool = PerfettoTool(config)

    try:
        results, err = tool.query(sql, str(trace_path))
        if err:
            typer.echo(f"Error: {err}", err=True)
            raise typer.Exit(1)

        if json_output:
            typer.echo(json.dumps({"results": results, "count": len(results or [])}, indent=2))
        else:
            if not results:
                typer.echo("No results")
            else:
                # Simple table output
                if results:
                    headers = list(results[0].keys())
                    typer.echo("\t".join(headers))
                    for row in results:
                        typer.echo("\t".join(str(row.get(h, "")) for h in headers))
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# Common tables for --common flag (most useful for trace analysis)
COMMON_PERFETTO_TABLES = [
    "slice",
    "track",
    "thread",
    "process",
    "thread_track",
    "process_track",
    "counter",
    "counter_track",
    "sched_slice",
    "gpu_slice",
]


@perfetto_app.command("tables")
def perfetto_tables(
    trace_path: Path = typer.Argument(..., help="Path to Perfetto trace file"),
    common: bool = typer.Option(False, "--common", help="Show commonly used tables (default)"),
    tables_filter: str | None = typer.Option(
        None, "--tables", "-t", help="Comma-separated list of table names to show"
    ),
    all_tables: bool = typer.Option(False, "--all", help="Show all tables (including internal)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List available tables in a Perfetto trace.

    Examples:
        wafer nvidia perfetto tables trace.json              # shows common tables (default)
        wafer nvidia perfetto tables trace.json --tables slice,track,thread
        wafer nvidia perfetto tables trace.json --all
    """
    from wafer_core.lib.perfetto.perfetto_tool import PerfettoConfig, PerfettoTool

    # Default to --common if no filter specified
    flag_count = sum([common, tables_filter is not None, all_tables])
    if flag_count == 0:
        common = True
        flag_count = 1
    if flag_count > 1:
        typer.echo("Error: Use only one of --common, --tables, or --all", err=True)
        raise typer.Exit(1)

    config = PerfettoConfig(
        workspace_root=".",
        storage_dir=str(Path.home() / ".wafer" / "perfetto"),
    )
    tool = PerfettoTool(config)

    try:
        all_table_names, err = tool.get_tables(str(trace_path))
        if err:
            typer.echo(f"Error: {err}", err=True)
            raise typer.Exit(1)

        all_table_names = all_table_names or []

        # Filter tables based on flag
        if all_tables:
            filtered = all_table_names
        elif common:
            # Show common tables that exist in this trace
            filtered = [t for t in COMMON_PERFETTO_TABLES if t in all_table_names]
        else:
            # --tables flag
            requested = [t.strip() for t in (tables_filter or "").split(",") if t.strip()]
            filtered = [t for t in requested if t in all_table_names]
            missing = [t for t in requested if t not in all_table_names]
            if missing:
                typer.echo(f"Warning: Tables not found: {', '.join(missing)}", err=True)

        if json_output:
            typer.echo(json.dumps({"tables": filtered}, indent=2))
        else:
            typer.echo(f"Found {len(filtered)} tables:")
            for table in filtered:
                typer.echo(f"  {table}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@perfetto_app.command("schema")
def perfetto_schema(
    trace_path: Path = typer.Argument(..., help="Path to Perfetto trace file"),
    table: str = typer.Argument(..., help="Table name"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Get schema for a table in a Perfetto trace.

    Examples:
        wafer perfetto schema trace.perfetto slice
        wafer perfetto schema trace.perfetto thread --json
    """
    from wafer_core.lib.perfetto.perfetto_tool import PerfettoConfig, PerfettoTool

    config = PerfettoConfig(
        workspace_root=".",
        storage_dir=str(Path.home() / ".wafer" / "perfetto"),
    )
    tool = PerfettoTool(config)

    try:
        columns, err = tool.get_schema(table, str(trace_path))
        if err:
            typer.echo(f"Error: {err}", err=True)
            raise typer.Exit(1)

        if json_output:
            typer.echo(json.dumps({"table": table, "columns": columns}, indent=2))
        else:
            typer.echo(f"Schema for table '{table}':")
            for col in columns or []:
                nullable = "NULL" if col.get("nullable") else "NOT NULL"
                typer.echo(f"  {col['name']}: {col['type']} {nullable}")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@perfetto_app.command("check")
def perfetto_check(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Check if trace_processor is available.

    Examples:
        wafer perfetto check
        wafer perfetto check --json
    """
    from wafer_core.lib.perfetto.perfetto_tool import PerfettoConfig, PerfettoTool

    config = PerfettoConfig(
        workspace_root=".",
        storage_dir=str(Path.home() / ".wafer" / "perfetto"),
    )
    tool = PerfettoTool(config)

    status = tool.check_processor()

    if json_output:
        typer.echo(json.dumps(status.to_dict(), indent=2))
    else:
        if status.available:
            typer.echo(f"✓ trace_processor available at {status.binary_path}")
            typer.echo(f"  Version: {status.version}")
            if not status.version_matches_ui:
                typer.echo(f"  ⚠ Version mismatch with UI (expected: {status.ui_version})")
        else:
            typer.echo(f"✗ trace_processor not available: {status.error}")
            typer.echo("  Run 'wafer perfetto check' to auto-download")


# =============================================================================
# NCU Analyze command
# =============================================================================


@ncu_app.command("analyze")
def ncu_analyze(
    filepath: Path = typer.Argument(..., help="Path to .ncu-rep profile file"),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory for analysis files"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON instead of formatted text"
    ),
    remote: bool | None = typer.Option(
        None,
        "--remote/--local",
        help="Force remote (via API) or local analysis. Default: auto-detect (remote if NCU not installed locally)",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Target for direct SSH mode. See 'wafer config targets list'.",
    ),
    include_source: bool = typer.Option(
        False,
        "--include-source",
        "-s",
        help="Include SASS source correlation for each kernel (requires --remote)",
    ),
) -> None:
    """Analyze an NVIDIA Nsight Compute profile (.ncu-rep file).

    Returns kernel performance metrics including duration, occupancy,
    compute/memory throughput, and optimization recommendations.

    By default, uses local NCU if available, otherwise runs analysis
    remotely via wafer-api (requires authentication: wafer login).

    Use --target for direct SSH mode (like wafer remote-run --direct).
    Use --include-source to fetch SASS assembly with register/instruction data.

    Examples:
        wafer nvidia ncu analyze profile.ncu-rep
        wafer nvidia ncu analyze profile.ncu-rep --json
        wafer nvidia ncu analyze profile.ncu-rep --output-dir ./analysis
        wafer nvidia ncu analyze profile.ncu-rep --remote
        wafer nvidia ncu analyze profile.ncu-rep --target vultr-b200
        wafer nvidia ncu analyze profile.ncu-rep --include-source --json
    """
    from .ncu_analyze import analyze_ncu_profile

    if not filepath.exists():
        typer.echo(f"Error: File not found: {filepath}", err=True)
        raise typer.Exit(1)

    if filepath.suffix != ".ncu-rep":
        typer.echo(f"Error: Expected .ncu-rep file, got: {filepath.suffix}", err=True)
        raise typer.Exit(1)

    try:
        result = analyze_ncu_profile(
            filepath,
            output_dir=output_dir,
            json_output=json_output,
            remote=remote,
            target=target,
            include_source=include_source,
        )
        typer.echo(result)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# =============================================================================
# NSYS commands
# =============================================================================


@nsys_app.command("check")
def nsys_check() -> None:
    """Check if NSYS (Nsight Systems) is installed and show version.

    NSYS is required for local analysis. If not installed, shows install instructions.

    Examples:
        wafer nvidia nsys check
    """
    from .nsys_analyze import check_nsys_installation

    result = check_nsys_installation()

    if result.installed:
        typer.echo(f"✓ NSYS installed: {result.path}")
        if result.version:
            typer.echo(f"  Version: {result.version}")
    else:
        typer.echo("✗ NSYS not installed")
        if result.install_command:
            typer.echo(f"  Install with: {result.install_command}")


@nsys_app.command("analyze")
def nsys_analyze(
    filepath: Path = typer.Argument(..., help="Path to .nsys-rep profile file"),
    output_dir: Path | None = typer.Option(
        None, "--output-dir", "-o", help="Output directory for analysis files"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output raw JSON instead of formatted text"
    ),
    remote: bool | None = typer.Option(
        None,
        "--remote/--local",
        help="Force remote (via API) or local analysis. Default: auto-detect (remote if nsys not installed locally)",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        "-t",
        help="Remote target: 'workspace:id' for workspace execution, or target name from ~/.wafer/targets/",
    ),
) -> None:
    """Analyze an NVIDIA Nsight Systems profile (.nsys-rep file).

    Returns timeline events, kernel information, memory usage, and diagnostics.

    By default, uses local nsys if available, otherwise runs analysis
    remotely via wafer-api (requires authentication: wafer login).

    Supports multiple execution modes:
    - Local: Uses local nsys CLI (no GPU required for analysis)
    - Remote API: Uploads file and runs analysis on Modal
    - Workspace: Runs analysis on a Wafer workspace via SSH
    - Target: Runs analysis on a configured target machine via SSH

    Examples:
        wafer nvidia nsys analyze profile.nsys-rep
        wafer nvidia nsys analyze profile.nsys-rep --json
        wafer nvidia nsys analyze profile.nsys-rep --local
        wafer nvidia nsys analyze profile.nsys-rep --remote
        wafer nvidia nsys analyze profile.nsys-rep --target workspace:abc123
        wafer nvidia nsys analyze profile.nsys-rep --target vultr-b200
        wafer nvidia nsys analyze profile.nsys-rep -o ./results/
    """
    from .nsys_analyze import analyze_nsys_profile

    if not filepath.exists():
        typer.echo(f"Error: File not found: {filepath}", err=True)
        raise typer.Exit(1)

    if filepath.suffix != ".nsys-rep":
        typer.echo(f"Error: Expected .nsys-rep file, got: {filepath.suffix}", err=True)
        raise typer.Exit(1)

    # Warn if both remote flag and target are specified
    if target and remote is not None:
        typer.echo(
            "Warning: --target overrides --remote/--local flag",
            err=True,
        )

    try:
        result = analyze_nsys_profile(
            filepath,
            json_output=json_output,
            remote=remote,
            target=target,
            output_dir=output_dir,
        )
        typer.echo(result)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except (RuntimeError, ValueError, NotImplementedError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@nsys_app.command("profile", context_settings={"allow_interspersed_args": False})
def nsys_profile(
    command: list[str] = typer.Argument(..., help="Command to profile"),
    output: str = typer.Option(
        "profile",
        "--output",
        "-o",
        help="Output filename (without .nsys-rep extension)",
    ),
    trace: str | None = typer.Option(
        None,
        "--trace",
        "-t",
        help="Trace APIs to capture (comma-separated: cuda,nvtx,osrt,cudnn,cublas). Default: cuda",
    ),
    duration: int | None = typer.Option(
        None,
        "--duration",
        "-d",
        help="Maximum profiling duration in seconds",
    ),
    target: str | None = typer.Option(
        None,
        "--target",
        help="Remote target: 'workspace:id' for workspace execution, or target name from ~/.wafer/targets/",
    ),
    analyze: bool = typer.Option(
        False,
        "--analyze",
        "-a",
        help="Automatically analyze the profile after completion",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output analysis as JSON (only with --analyze)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show verbose progress messages",
    ),
    extra_args: str | None = typer.Option(
        None,
        "--extra",
        help="Extra arguments to pass to nsys profile",
    ),
) -> None:
    """Profile a command with NVIDIA Nsight Systems.

    Runs nsys profile on the specified command and generates a .nsys-rep file.
    Profiling requires an NVIDIA GPU. Use --target to run on a remote GPU server
    or workspace.

    Examples:
        wafer nvidia nsys profile -- python train.py
        wafer nvidia nsys profile -o gemm_profile -- ./gemm_kernel
        wafer nvidia nsys profile --trace cuda,nvtx -- python model.py
        wafer nvidia nsys profile --duration 60 -- ./long_running_app
        wafer nvidia nsys profile --target workspace:abc123 -- python test.py
        wafer nvidia nsys profile --target vultr-b200 -- ./benchmark
        wafer nvidia nsys profile --analyze -- python train.py
        wafer nvidia nsys profile --analyze --json -- ./kernel > results.json
    """
    # Parse command
    import shlex

    from .nsys_analyze import _parse_target
    from .nsys_profile import (
        NSYSProfileOptions,
        profile_and_analyze,
        profile_local,
        profile_remote_ssh,
        profile_workspace,
    )

    if isinstance(command, list):
        # Remove leading "--" if present
        if command and command[0] == "--":
            command = command[1:]
        if len(command) == 1:
            command_str = command[0]
        else:
            command_str = shlex.join(command)
    else:
        command_str = command

    if not command_str:
        typer.echo("Error: No command specified", err=True)
        raise typer.Exit(1)

    # Parse trace options
    trace_list = trace.split(",") if trace else None

    # Build options
    options = NSYSProfileOptions(
        command=command_str,
        output=output,
        trace=trace_list,
        duration=duration,
        extra_args=extra_args,
    )

    if verbose:
        typer.echo(f"[nsys] Command: {command_str}", err=True)
        if target:
            typer.echo(f"[nsys] Target: {target}", err=True)

    # Execute
    if analyze:
        profile_result, analysis_result = profile_and_analyze(
            options,
            target=target,
            json_output=json_output,
            verbose=verbose,
        )
    else:
        if target:
            target_type, target_id = _parse_target(target)
            if target_type == "workspace":
                profile_result = profile_workspace(target_id, options, verbose=verbose)
            else:
                profile_result = profile_remote_ssh(target_id, options, verbose=verbose)
        else:
            profile_result = profile_local(options, verbose=verbose)
        analysis_result = None

    # Report results
    if not profile_result.success:
        typer.echo(f"Error: {profile_result.error}", err=True)
        if profile_result.stderr:
            typer.echo(f"stderr: {profile_result.stderr}", err=True)
        raise typer.Exit(1)

    if verbose or not analyze:
        typer.echo(f"Profile created: {profile_result.output_path}")

    if analysis_result:
        if not analysis_result.success:
            typer.echo(f"Analysis error: {analysis_result.error}", err=True)
            raise typer.Exit(1)


# =============================================================================
# ROCprof-Compute commands
# =============================================================================

# Create rocprof-sdk subcommand group (under amd)
rocprof_sdk_app = typer.Typer(help="ROCprofiler-SDK profiling tool commands")
amd_app.add_typer(rocprof_sdk_app, name="rocprof-sdk")


@rocprof_sdk_app.command("check")
def rocprof_sdk_check(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check if rocprofv3 is installed.

    Examples:
        wafer rocprof-sdk check
        wafer rocprof-sdk check --json
    """
    from .rocprof_sdk import check_command

    try:
        result = check_command(json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_sdk_app.command("list-counters")
def rocprof_sdk_list_counters() -> None:
    """List available hardware counters for your GPU.

    Examples:
        wafer rocprof-sdk list-counters
        wafer rocprof-sdk list-counters | grep SQ_
    """
    from .rocprof_sdk import list_counters_command

    try:
        list_counters_command()
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_sdk_app.command("profile")
def rocprof_sdk_profile(
    command: str = typer.Argument(..., help="Command to profile"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    output_format: str = typer.Option(
        "csv", "--format", "-f", help="Output format (csv, json, rocpd, pftrace, otf2)"
    ),
    counters: str | None = typer.Option(
        None, "--counters", "-c", help="Comma-separated hardware counters"
    ),
    kernel_include: str | None = typer.Option(
        None, "--kernel-include", help="Include only kernels matching this regex"
    ),
    kernel_exclude: str | None = typer.Option(
        None, "--kernel-exclude", help="Exclude kernels matching this regex"
    ),
    trace_hip_runtime: bool = typer.Option(
        False, "--trace-hip-runtime", help="Enable HIP runtime API tracing"
    ),
    trace_hip_compiler: bool = typer.Option(
        False, "--trace-hip-compiler", help="Enable HIP compiler code tracing"
    ),
    trace_hsa: bool = typer.Option(False, "--trace-hsa", help="Enable HSA API tracing"),
    trace_marker: bool = typer.Option(False, "--trace-marker", help="Enable ROCTx marker tracing"),
    trace_memory_copy: bool = typer.Option(
        False, "--trace-memory-copy", help="Enable memory copy tracing"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Profile a command with rocprofv3.

    Examples:
        wafer rocprof-sdk profile './my_kernel'
        wafer rocprof-sdk profile './app' --format csv --output-dir ./results
        wafer rocprof-sdk profile './kernel' --counters SQ_WAVES,L2_CACHE_HITS
        wafer rocprof-sdk profile './app' --kernel-include 'vectorAdd|matmul'
        wafer rocprof-sdk profile './app' --trace-hip-runtime --trace-memory-copy
    """
    from .rocprof_sdk import profile_command

    counter_list = counters.split(",") if counters else None

    try:
        result = profile_command(
            command,
            output_dir,
            output_format,
            counter_list,
            kernel_include,
            kernel_exclude,
            trace_hip_runtime,
            trace_hip_compiler,
            trace_hsa,
            trace_marker,
            trace_memory_copy,
            json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_sdk_app.command("analyze")
def rocprof_sdk_analyze(
    file_path: Path = typer.Argument(
        ..., help="Path to rocprofiler output file (.csv, .json, .db)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Analyze a rocprofiler output file.

    Supports:
    - CSV stats files (stats_*.csv)
    - JSON trace files (*.json)
    - rocpd databases (*_results.db, *.rocpd)

    Examples:
        wafer rocprof-sdk analyze stats_kernel.csv
        wafer rocprof-sdk analyze results.json
        wafer rocprof-sdk analyze profile_results.db --json
    """
    from .rocprof_sdk import analyze_command

    if not file_path.exists():
        typer.echo(f"Error: File not found: {file_path}", err=True)
        raise typer.Exit(1)

    try:
        result = analyze_command(str(file_path), json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# Create rocprof-systems subcommand group (under amd)
rocprof_systems_app = typer.Typer(help="ROCprofiler-Systems profiling tool commands")
amd_app.add_typer(rocprof_systems_app, name="rocprof-systems")


@rocprof_systems_app.command("check")
def rocprof_systems_check(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check if rocprof-sys tools are installed.

    Examples:
        wafer rocprof-systems check
        wafer rocprof-systems check --json
    """
    from .rocprof_systems import check_command

    try:
        result = check_command(json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_systems_app.command("run")
def rocprof_systems_run(
    command: str = typer.Argument(..., help="Command to profile"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    trace: bool = typer.Option(
        True, "--trace/--no-trace", help="Generate detailed trace (Perfetto)"
    ),
    profile: bool = typer.Option(False, "--profile", help="Generate call-stack-based profile"),
    flat_profile: bool = typer.Option(False, "--flat-profile", help="Generate flat profile"),
    sample: bool = typer.Option(False, "--sample", help="Enable sampling profiling"),
    host: bool = typer.Option(False, "--host", help="Enable host metrics"),
    device: bool = typer.Option(False, "--device", help="Enable device metrics"),
    wait: float | None = typer.Option(None, "--wait", help="Wait time before collecting (seconds)"),
    duration: float | None = typer.Option(
        None, "--duration", help="Duration of collection (seconds)"
    ),
    use_rocm: bool = typer.Option(True, "--use-rocm/--no-rocm", help="Enable ROCm backend"),
    use_sampling: bool = typer.Option(False, "--use-sampling", help="Enable sampling backend"),
    use_kokkosp: bool = typer.Option(
        False, "--use-kokkosp", help="Enable Kokkos profiling backend"
    ),
    use_mpip: bool = typer.Option(False, "--use-mpip", help="Enable MPI profiling backend"),
    use_rocpd: bool = typer.Option(False, "--use-rocpd", help="Enable rocpd database output"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Run system profiling with rocprof-sys-run.

    Examples:
        wafer rocprof-systems run './my_app'
        wafer rocprof-systems run './app' --trace --profile --output-dir ./results
        wafer rocprof-systems run './kernel' --host --device --duration 10
        wafer rocprof-systems run './app' --use-kokkosp --use-mpip
    """
    from .rocprof_systems import run_command

    try:
        result = run_command(
            command=command,
            output_dir=output_dir,
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
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_systems_app.command("analyze")
def rocprof_systems_analyze(
    file_path: Path = typer.Argument(..., help="Path to rocprof-sys output file (.json, .txt)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Analyze a rocprof-sys output file.

    Supports:
    - JSON files (wall_clock-*.json, metadata-*.json, functions-*.json)
    - Text files (wall-clock.txt)

    Examples:
        wafer rocprof-systems analyze wall_clock-12345.json
        wafer rocprof-systems analyze wall-clock.txt --json
    """
    from .rocprof_systems import analyze_command

    if not file_path.exists():
        typer.echo(f"Error: File not found: {file_path}", err=True)
        raise typer.Exit(1)

    try:
        result = analyze_command(str(file_path), json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_systems_app.command("sample")
def rocprof_systems_sample(
    command: str = typer.Argument(..., help="Command to profile"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    frequency: int | None = typer.Option(
        None, "--frequency", "--freq", "-f", help="Sampling frequency in Hz"
    ),
    trace: bool = typer.Option(False, "--trace", help="Generate detailed trace"),
    profile: bool = typer.Option(False, "--profile", help="Generate call-stack profile"),
    flat_profile: bool = typer.Option(False, "--flat-profile", help="Generate flat profile"),
    host: bool = typer.Option(False, "--host", help="Enable host metrics"),
    device: bool = typer.Option(False, "--device", help="Enable device metrics"),
    wait: float | None = typer.Option(None, "--wait", help="Wait time (seconds)"),
    duration: float | None = typer.Option(None, "--duration", help="Duration (seconds)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Run sampling profiling with rocprof-sys-sample.

    Examples:
        wafer rocprof-systems sample ./my_app --frequency 100
        wafer rocprof-systems sample ./kernel --freq 500 --output-dir ./results
    """
    from .rocprof_systems import sample_command

    try:
        result = sample_command(
            command=command,
            output_dir=output_dir,
            frequency=frequency,
            trace=trace,
            profile=profile,
            flat_profile=flat_profile,
            host=host,
            device=device,
            wait=wait,
            duration=duration,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_systems_app.command("instrument")
def rocprof_systems_instrument(
    command: str = typer.Argument(..., help="Command to instrument"),
    output_dir: str | None = typer.Option(None, "--output-dir", "-o", help="Output directory"),
    simulate: bool = typer.Option(False, "--simulate", help="Simulate without creating binary"),
    function_include: list[str] | None = typer.Option(
        None, "--function-include", help="Function patterns to include"
    ),
    function_exclude: list[str] | None = typer.Option(
        None, "--function-exclude", help="Function patterns to exclude"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Run binary instrumentation with rocprof-sys-instrument.

    Examples:
        wafer rocprof-systems instrument ./my_app --simulate
        wafer rocprof-systems instrument ./kernel --output-dir ./results
    """
    from .rocprof_systems import instrument_command

    try:
        result = instrument_command(
            command=command,
            output_dir=output_dir,
            simulate=simulate,
            function_include=function_include,
            function_exclude=function_exclude,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_systems_app.command("query")
def rocprof_systems_query(
    components: bool = typer.Option(False, "--components", help="Query available components"),
    hw_counters: bool = typer.Option(False, "--hw-counters", help="Query hardware counters"),
    all_metrics: bool = typer.Option(False, "--all", help="Query all metrics"),
    filter_pattern: str | None = typer.Option(None, "--filter", help="Filter results"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Query available profiling metrics and components.

    Examples:
        wafer rocprof-systems query --components
        wafer rocprof-systems query --hw-counters
        wafer rocprof-systems query --components --filter cpu
    """
    from .rocprof_systems import query_command

    try:
        result = query_command(
            components=components,
            hw_counters=hw_counters,
            all_metrics=all_metrics,
            filter_pattern=filter_pattern,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# Create rocprof-compute subcommand group (under amd)
rocprof_compute_app = typer.Typer(help="ROCprofiler-Compute profiling tool commands")
amd_app.add_typer(rocprof_compute_app, name="rocprof-compute")


@rocprof_compute_app.command("check")
def rocprof_compute_check(
    json_output: bool = typer.Option(False, "--json", help="Output status as JSON"),
) -> None:
    """Check if rocprof-compute is installed.

    Examples:
        wafer rocprof-compute check
        wafer rocprof-compute check --json
    """
    from .rocprof_compute import check_command

    try:
        result = check_command(json_output=json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_compute_app.command("profile")
def rocprof_compute_profile(
    command: str = typer.Argument(..., help="Command to profile"),
    name: str = typer.Option(..., "--name", "-n", help="Workload name"),
    path: str | None = typer.Option(None, "--path", "-p", help="Workload base path"),
    kernel: str | None = typer.Option(
        None, "--kernel", "-k", help="Kernel filter (comma-separated)"
    ),
    dispatch: str | None = typer.Option(
        None, "--dispatch", "-d", help="Dispatch filter (comma-separated)"
    ),
    block: str | None = typer.Option(None, "--block", "-b", help="Block filter (comma-separated)"),
    no_roof: bool = typer.Option(False, "--no-roof", help="Skip roofline data"),
    roof_only: bool = typer.Option(False, "--roof-only", help="Profile roofline only (fastest)"),
    hip_trace: bool = typer.Option(False, "--hip-trace", help="Enable HIP trace"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Profile a command with rocprof-compute.

    Executes rocprof-compute profiling on the target command and generates
    analysis results including roofline data, memory analysis, and kernel statistics.

    Examples:
        wafer rocprof-compute profile --name vcopy -- './vcopy -n 1048576'
        wafer rocprof-compute profile -n test -b SQ,TCC -- './kernel'
        wafer rocprof-compute profile -n trace --hip-trace -- './app'
        wafer rocprof-compute profile -n test --roof-only -- './app'
    """
    from .rocprof_compute import profile_command

    try:
        result = profile_command(
            command,
            name,
            path,
            kernel,
            dispatch,
            block,
            no_roof,
            roof_only,
            hip_trace,
            verbose,
            json_output,
        )
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_compute_app.command("analyze")
def rocprof_compute_analyze(
    workload_path: Path = typer.Argument(..., help="Path to workload directory"),
    kernel: str | None = typer.Option(None, "--kernel", "-k", help="Kernel filter"),
    dispatch: str | None = typer.Option(None, "--dispatch", "-d", help="Dispatch filter"),
    block: str | None = typer.Option(None, "--block", "-b", help="Block filter"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file"),
    list_stats: bool = typer.Option(
        False, "--list-stats", help="List all detected kernels and dispatches"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    gui: bool = typer.Option(
        False, "--gui", help="Launch interactive GUI viewer (bundled Python viewer by default)"
    ),
    port: int = typer.Option(8050, "--port", "-p", help="Port for GUI server"),
    external: bool = typer.Option(
        False,
        "--external",
        help="Use AMD's native rocprof-compute GUI instead of bundled (requires ROCm)",
    ),
) -> None:
    """Analyze a rocprof-compute workload directory.

    Parses workload data and displays kernel statistics, roofline analysis,
    and performance metrics. Can optionally launch an interactive GUI viewer.

    GUI Modes:
        --gui           Uses Wafer's bundled Python viewer (works anywhere, no ROCm needed)
        --gui --external Uses AMD's native rocprof-compute GUI (requires ROCm installation)

    Examples:
        wafer rocprof-compute analyze ./workloads/vcopy
        wafer rocprof-compute analyze ./workloads/test --json
        wafer rocprof-compute analyze ./workloads/app -d 0,1 -o filtered.csv
        wafer rocprof-compute analyze ./workloads/app --list-stats
        wafer rocprof-compute analyze ./workloads/app --gui
        wafer rocprof-compute analyze ./workloads/app --gui --port 9000
        wafer rocprof-compute analyze ./workloads/app --gui --external
    """
    from .rocprof_compute import analyze_command

    if not workload_path.exists():
        typer.echo(f"Error: Workload path not found: {workload_path}", err=True)
        raise typer.Exit(1)

    try:
        result = analyze_command(
            str(workload_path),
            kernel,
            dispatch,
            block,
            output,
            list_stats,
            json_output,
            gui,
            port,
            external,
        )
        if json_output or not gui:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@rocprof_compute_app.command("list-metrics")
def rocprof_compute_list_metrics(
    arch: str = typer.Argument(..., help="Architecture (gfx90a, gfx942, etc.)"),
) -> None:
    """List available metrics for an architecture.

    Examples:
        wafer rocprof-compute list-metrics gfx90a
        wafer rocprof-compute list-metrics gfx942
    """
    from .rocprof_compute import list_metrics_command

    try:
        result = list_metrics_command(arch)
        if result:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


# =============================================================================
# Autotuner commands
# =============================================================================

# Create autotuner subcommand group (hidden for now - TBD placement)
autotuner_app = typer.Typer(help="Hyperparameter sweep for performance engineering")
app.add_typer(autotuner_app, name="autotuner", hidden=True)


def _setup_wafer_core_env() -> None:
    """Set environment variables for wafer-core to use.

    Call this before using any wafer-core functions that need API access.

    Respects explicit environment variable overrides:
    - WAFER_API_URL: If already set, uses that instead of config
    - WAFER_AUTH_TOKEN: If already set, uses that instead of cached token
    """
    from .auth import get_valid_token
    from .global_config import get_api_url

    # Set API URL (get_api_url already respects WAFER_API_URL env var)
    os.environ["WAFER_API_URL"] = get_api_url()

    # Only set auth token if not explicitly provided in environment
    # This allows CI/service accounts to override with their own tokens
    if "WAFER_AUTH_TOKEN" not in os.environ:
        token = get_valid_token()
        if token:
            os.environ["WAFER_AUTH_TOKEN"] = token


@autotuner_app.command("list")
def autotuner_list(
    show_all: bool = typer.Option(
        False, "--all", help="Show all sweeps including pending and failed"
    ),
) -> None:
    """List sweeps for the current user.

    By default, only shows running and completed sweeps.
    Use --all to include pending and failed sweeps.

    Examples:
        wafer autotuner list
        wafer autotuner list --all
    """
    _setup_wafer_core_env()
    from .autotuner import list_command

    try:
        result = list_command(show_all=show_all)
        print(result)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@autotuner_app.command("delete")
def autotuner_delete(
    sweep_id: str | None = typer.Argument(None, help="Sweep ID to delete (omit when using --all)"),
    delete_all: bool = typer.Option(
        False, "--all", help="Delete all sweeps (optionally filtered by --status)"
    ),
    status: str | None = typer.Option(
        None,
        "--status",
        help="Filter by status when using --all (pending, running, completed, failed)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Delete a sweep (or all sweeps) and their trials.

    WARNING: This permanently deletes sweeps and cannot be undone.

    Examples:
        # Delete single sweep
        wafer autotuner delete <sweep-id>
        wafer autotuner delete <sweep-id> --yes

        # Delete all sweeps
        wafer autotuner delete --all
        wafer autotuner delete --all --status pending
        wafer autotuner delete --all --status failed --yes
    """
    _setup_wafer_core_env()
    from .autotuner import delete_all_command, delete_command

    # Validate arguments
    if delete_all and sweep_id:
        typer.echo("Error: Cannot specify both sweep_id and --all flag", err=True)
        raise typer.Exit(1)

    if not delete_all and not sweep_id:
        typer.echo("Error: Must specify either sweep_id or --all flag", err=True)
        raise typer.Exit(1)

    if status and not delete_all:
        typer.echo("Error: --status can only be used with --all flag", err=True)
        raise typer.Exit(1)

    try:
        if delete_all:
            # Delete all sweeps
            if not yes:
                status_msg = f" with status '{status}'" if status else ""
                confirm = typer.confirm(f"Are you sure you want to delete all sweeps{status_msg}?")
                if not confirm:
                    typer.echo("Deletion cancelled.")
                    raise typer.Exit(0)

            result = delete_all_command(status_filter=status)
        else:
            # Delete single sweep
            if not yes:
                confirm = typer.confirm(f"Are you sure you want to delete sweep {sweep_id}?")
                if not confirm:
                    typer.echo("Deletion cancelled.")
                    raise typer.Exit(0)

            result = delete_command(sweep_id)

        print(result)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@autotuner_app.command("run")
def autotuner_run(
    config_file: Path | None = typer.Argument(
        None, help="Path to JSON config file (required unless --resume)"
    ),
    parallel: int = typer.Option(
        4, "--parallel", "-p", help="Number of trials to run concurrently"
    ),
    resume: str | None = typer.Option(None, "--resume", "-r", help="Resume existing sweep by ID"),
) -> None:
    """Run hyperparameter sweep from JSON config or resume existing sweep.

    Examples:
        # Start new sweep
        wafer autotuner run config.json
        wafer autotuner run config.json --parallel 8

        # Resume failed/interrupted sweep
        wafer autotuner run --resume <sweep-id>
        wafer autotuner run --resume <sweep-id> --parallel 8
    """
    _setup_wafer_core_env()
    from .autotuner import run_sweep_command

    # Validate arguments
    if not resume and not config_file:
        typer.echo("Error: Must specify either config file or --resume <sweep-id>", err=True)
        raise typer.Exit(1)

    if resume and config_file:
        typer.echo("Error: Cannot specify both config file and --resume", err=True)
        raise typer.Exit(1)

    try:
        result = run_sweep_command(
            config_file=config_file, parallel=parallel, resume_sweep_id=resume
        )
        print(result)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@autotuner_app.command("results")
def autotuner_results(
    sweep_id: str = typer.Argument(..., help="Sweep ID to retrieve"),
    mode: str = typer.Argument("list", help="Display mode: 'list', 'best', or trial number"),
    sort_by: str | None = typer.Option(
        None, "--sort-by", help="Metric name to sort by (list mode)"
    ),
    direction: str = typer.Option("maximize", "--direction", help="Sort direction (list mode)"),
    pareto: str | None = typer.Option(
        None, "--pareto", help="Comma-separated metrics for Pareto frontier (list mode)"
    ),
    show_all: bool = typer.Option(
        False, "--show-all", help="Include failed and constraint-violated trials (list mode)"
    ),
    limit: int | None = typer.Option(
        None, "--limit", help="Maximum number of results to show (list mode, default: all)"
    ),
    metric: str | None = typer.Option(
        None, "--metric", help="Metric to optimize (REQUIRED for best mode)"
    ),
) -> None:
    """Show sweep results (list/best/trial).

    Commands:
        wafer autotuner results <sweep-id>                    # List all results
        wafer autotuner results <sweep-id> --sort-by <metric> # List sorted
        wafer autotuner results <sweep-id> best --metric <m>  # Show best config
        wafer autotuner results <sweep-id> <N>                # Show trial N
    """
    from .autotuner import best_command, results_command, trial_command

    try:
        if mode == "best":
            if not metric:
                typer.echo("Error: --metric is required for 'best' mode", err=True)
                raise typer.Exit(1)
            result = best_command(sweep_id=sweep_id, metric=metric)
        elif mode == "list":
            result = results_command(
                sweep_id=sweep_id,
                sort_by=sort_by,
                direction=direction,
                pareto=pareto,
                show_all=show_all,
                limit=limit,
            )
        else:
            # Try to parse as trial number
            try:
                trial_number = int(mode)
                result = trial_command(sweep_id=sweep_id, trial_number=trial_number)
            except ValueError as e:
                typer.echo(
                    f"Error: Invalid mode '{mode}'. Use 'list', 'best', or a trial number.",
                    err=True,
                )
                raise typer.Exit(1) from e

        print(result)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command("capture")
def capture_command(  # noqa: PLR0915
    label: str = typer.Argument(
        ..., help="Label for this capture (e.g., 'baseline', 'optimized-v2')"
    ),
    command: str = typer.Argument(..., help="Command to execute and capture"),
    variant: str | None = typer.Option(
        None, "--variant", "-v", help="Variant identifier for grouping related captures"
    ),
    tags: list[str] | None = typer.Option(
        None, "--tag", "-t", help="Tags for categorization (can be specified multiple times)"
    ),  # noqa: B008
    working_dir: Path | None = typer.Option(
        None, "--dir", "-d", help="Working directory (default: current directory)"
    ),
    sweep: list[str] | None = typer.Option(
        None, "--sweep", "-s", help="Parameter sweep (format: VAR=val1,val2,val3)"
    ),  # noqa: B008
    code_denylist: list[str] | None = typer.Option(
        None,
        "--code-denylist",
        help="Patterns to exclude from code files (e.g., '*.log', '**/test/**')",
    ),  # noqa: B008
    artifact_denylist: list[str] | None = typer.Option(
        None,
        "--artifact-denylist",
        help="Patterns to exclude from artifacts (e.g., '*.tmp', '*.o')",
    ),  # noqa: B008
) -> None:
    """Capture a complete execution snapshot for reproducibility.

    Captures everything needed to reproduce a benchmark run:
    - Command output (stdout/stderr), exit code, duration
    - Generated artifacts (outputs, profiles, logs)
    - Code files used in execution
    - Git context (repo, commit, branch, dirty status)
    - System context (GPU model, CUDA version, hostname)
    - Metrics extracted from stdout (latency, throughput, etc.)

    All data is uploaded to Supabase for later analysis and comparison.

    Denylist Configuration (precedence: CLI > Project > Global > Defaults):
        1. CLI flags: --code-denylist and --artifact-denylist
        2. Project config: .wafer-capture.toml in working directory
        3. Global config: ~/.wafer/capture.toml
        4. Built-in defaults (excludes common binaries, dependencies, etc.)

    Examples:
        # Basic capture
        wafer capture baseline "python benchmark.py"

        # With variant for A/B testing
        wafer capture optimized "python benchmark.py" --variant v2

        # With tags
        wafer capture test-run "make && ./kernel" --tag cuda --tag fp16

        # Different working directory
        wafer capture training "python train.py" --dir ./experiments/run1

        # Custom denylists via CLI
        wafer capture test "make" --code-denylist "*.log" --code-denylist "**/test/**"

        # Parameter sweep (runs multiple captures with different values)
        wafer capture batch-sizes "python train.py --batch-size {BATCH}" --sweep "BATCH=16,32,64,128"

        # Multiple variable sweep (cartesian product)
        wafer capture grid-search "python train.py --lr {LR} --bs {BS}" --sweep "LR=0.001,0.01,0.1" --sweep "BS=16,32"
    """
    import itertools
    import os
    import tomllib

    from .auth import get_valid_token
    from .global_config import get_api_url

    # Set environment variables for wafer-core BEFORE importing it
    # wafer-core backend.py reads WAFER_API_URL and WAFER_AUTH_TOKEN from env
    os.environ["WAFER_API_URL"] = get_api_url()

    # Only set auth token if not explicitly provided in environment
    # This allows CI/service accounts to override with their own tokens
    if "WAFER_AUTH_TOKEN" not in os.environ:
        token = get_valid_token()
        if token:
            os.environ["WAFER_AUTH_TOKEN"] = token

    import trio
    from wafer_core.tools.capture_tool import (  # pragma: no cover
        CaptureConfig,
        capture,
        execute_command,
    )

    # Resolve working directory
    work_dir = working_dir.resolve() if working_dir else Path.cwd()

    # Load denylists from config files (precedence: project > global > defaults)
    config_code_denylist = None
    config_artifact_denylist = None

    # 1. Try global config (~/.wafer/capture.toml)
    global_config_path = Path.home() / ".wafer" / "capture.toml"
    if global_config_path.exists():
        try:
            with open(global_config_path, "rb") as f:
                capture_config_data = tomllib.load(f)
            config_code_denylist = capture_config_data.get("code_denylist")
            config_artifact_denylist = capture_config_data.get("artifact_denylist")
        except Exception as e:
            typer.echo(f"⚠️  Warning: Failed to load {global_config_path}: {e}", err=True)

    # 2. Try project-specific config (.wafer-capture.toml in working dir)
    project_config_path = work_dir / ".wafer-capture.toml"
    if project_config_path.exists():
        try:
            with open(project_config_path, "rb") as f:
                project_config_data = tomllib.load(f)
            # Project config overrides global config
            if "code_denylist" in project_config_data:
                config_code_denylist = project_config_data["code_denylist"]
            if "artifact_denylist" in project_config_data:
                config_artifact_denylist = project_config_data["artifact_denylist"]
        except Exception as e:
            typer.echo(f"⚠️  Warning: Failed to load {project_config_path}: {e}", err=True)

    # Parse sweep parameters (format: "VAR=val1,val2,val3")
    sweep_vars: dict[str, list[str]] = {}
    if sweep:
        for sweep_spec in sweep:
            if "=" not in sweep_spec:
                typer.echo(f"❌ Invalid sweep format: {sweep_spec}", err=True)
                typer.echo("   Expected format: VAR=val1,val2,val3", err=True)
                raise typer.Exit(1)

            var_name, values_str = sweep_spec.split("=", 1)
            values = [v.strip() for v in values_str.split(",")]
            sweep_vars[var_name] = values

    # Generate all combinations (cartesian product) of sweep variables
    if sweep_vars:
        var_names = list(sweep_vars.keys())
        var_values = [sweep_vars[name] for name in var_names]
        combinations = list(itertools.product(*var_values))

        typer.echo(f"🔬 Running sweep: {label}")
        typer.echo(f"   Variables: {', '.join(var_names)}")
        typer.echo(f"   Total runs: {len(combinations)}")
        typer.echo()
    else:
        # Single run (no sweep)
        combinations = [()]
        var_names = []

    # Progress callback
    def progress(msg: str) -> None:
        typer.echo(f"  {msg}")

    async def run_capture_sweep() -> None:
        successful = 0
        failed = 0

        for idx, combo in enumerate(combinations, 1):
            # Substitute variables in command
            substituted_cmd = command
            sweep_info = {}
            for var_name, value in zip(var_names, combo, strict=True):
                substituted_cmd = substituted_cmd.replace(f"{{{var_name}}}", value)
                sweep_info[var_name] = value

            # Create variant name for sweep runs
            if sweep_vars:
                variant_parts = [f"{k}={v}" for k, v in sweep_info.items()]
                run_variant = "_".join(variant_parts)
                if variant:
                    run_variant = f"{variant}_{run_variant}"
            else:
                run_variant = variant

            # Create config for this run
            # Build denylist kwargs with precedence: CLI > Config File > Defaults
            denylist_kwargs = {}

            # Code denylist: CLI flag takes precedence over config file
            if code_denylist:
                denylist_kwargs["code_denylist"] = code_denylist
            elif config_code_denylist:
                denylist_kwargs["code_denylist"] = config_code_denylist
            # Otherwise use CaptureConfig defaults

            # Artifact denylist: CLI flag takes precedence over config file
            if artifact_denylist:
                denylist_kwargs["artifact_denylist"] = artifact_denylist
            elif config_artifact_denylist:
                denylist_kwargs["artifact_denylist"] = config_artifact_denylist
            # Otherwise use CaptureConfig defaults

            config = CaptureConfig(
                label=label,
                command=substituted_cmd,
                working_dir=work_dir,
                variant=run_variant,
                tags=tags or [],
                **denylist_kwargs,
            )

            try:
                if sweep_vars:
                    typer.echo(
                        f"[{idx}/{len(combinations)}] {', '.join(f'{k}={v}' for k, v in sweep_info.items())}"
                    )
                else:
                    typer.echo(f"🔬 Capturing: {label}")

                typer.echo(f"   Command: {substituted_cmd}")
                typer.echo(f"   Working dir: {work_dir}")
                typer.echo()

                result = await capture(
                    config=config, runner=execute_command, progress_callback=progress
                )

                typer.echo()
                typer.echo("✅ Capture complete!")
                typer.echo(f"   ID: {result.id}")
                typer.echo(f"   Exit code: {result.exit_code}")
                typer.echo(f"   Duration: {result.duration_seconds:.2f}s")
                typer.echo(f"   Code files: {len(result.code_files)}")
                typer.echo(f"   Artifacts: {len(result.artifacts)}")
                if result.metrics.stdout_metrics:
                    typer.echo(f"   Metrics: {len(result.metrics.stdout_metrics)}")
                typer.echo()

                successful += 1

            except Exception as e:
                typer.echo(f"\n❌ Capture failed: {e}", err=True)
                typer.echo()
                failed += 1

        # Summary for sweep runs
        if sweep_vars and len(combinations) > 1:
            typer.echo("=" * 60)
            typer.echo(f"Sweep complete: {successful} successful, {failed} failed")

        if failed > 0:
            raise typer.Exit(1)

    trio.run(run_capture_sweep)


@app.command("capture-list", hidden=True)
def capture_list_command(
    label: str | None = typer.Option(None, "--label", "-l", help="Filter by label"),
    limit: int = typer.Option(100, "--limit", "-n", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List captured executions.

    Query captures from the backend with optional filtering and pagination.
    Output can be formatted as a table (default) or JSON.

    Examples:
        # List all captures
        wafer capture-list

        # Filter by label
        wafer capture-list --label baseline

        # Get JSON output for scripting
        wafer capture-list --json --limit 10

        # Pagination
        wafer capture-list --limit 20 --offset 20
    """
    import os

    from .auth import get_valid_token
    from .global_config import get_api_url

    # Set environment variables for wafer-core BEFORE importing it
    os.environ["WAFER_API_URL"] = get_api_url()

    # Only set auth token if not explicitly provided in environment
    # This allows CI/service accounts to override with their own tokens
    if "WAFER_AUTH_TOKEN" not in os.environ:
        token = get_valid_token()
        if token:
            os.environ["WAFER_AUTH_TOKEN"] = token

    import trio
    from wafer_core.utils.backend import list_captures  # pragma: no cover

    async def run_list() -> None:
        try:
            captures = await list_captures(label=label, limit=limit, offset=offset)

            if json_output:
                # JSON output for machine consumption
                typer.echo(json.dumps(captures, indent=2))
            else:
                # Human-readable table output
                if not captures:
                    typer.echo("No captures found.")
                    return

                typer.echo(f"Found {len(captures)} captures:\n")

                # Print table header
                typer.echo(
                    f"{'ID':<36}  {'Label':<20}  {'Variant':<20}  {'Exit':<4}  {'Duration':<8}  {'Created'}"
                )
                typer.echo("-" * 120)

                # Print each capture
                for cap in captures:
                    cap_id = cap.get("id", "")[:36]
                    cap_label = cap.get("label", "")[:20]
                    cap_variant = (cap.get("variant") or "")[:20]
                    exit_code = cap.get("exit_code", "")
                    duration = f"{cap.get('duration_seconds', 0):.2f}s"
                    created = cap.get("created_at", "")[:19]  # Strip microseconds

                    typer.echo(
                        f"{cap_id:<36}  {cap_label:<20}  {cap_variant:<20}  {exit_code:<4}  {duration:<8}  {created}"
                    )

        except Exception as e:
            typer.echo(f"❌ Failed to list captures: {e}", err=True)
            raise typer.Exit(1) from None

    trio.run(run_list)


# =============================================================================
# Corpus commands
# =============================================================================


@corpus_app.command("download")
def corpus_download(
    name: str = typer.Argument(..., help="Corpus name (cuda, cutlass, hip, amd)"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-download even if exists"),
) -> None:
    """Download a documentation corpus for agent filesystem access.

    Examples:
        wafer corpus download cuda
        wafer corpus download amd
        wafer corpus download cutlass --force
    """
    from .corpus import CORPORA, download_corpus

    if name not in CORPORA:
        typer.echo(f"Unknown corpus: {name}", err=True)
        typer.echo(f"Available: {', '.join(CORPORA.keys())}", err=True)
        raise typer.Exit(1)
    try:
        path = download_corpus(name, force=force)  # type: ignore[arg-type]
        typer.echo(f"\nCorpus ready at: {path}")
    except Exception as e:
        typer.echo(f"Failed to download corpus: {e}", err=True)
        raise typer.Exit(1) from None


@corpus_app.command("sync")
def corpus_sync(
    name: str = typer.Argument(..., help="Corpus name to sync"),
) -> None:
    """Re-download a corpus to get latest version.

    Examples:
        wafer corpus sync cuda
    """
    from .corpus import CORPORA, sync_corpus

    if name not in CORPORA:
        typer.echo(f"Unknown corpus: {name}", err=True)
        typer.echo(f"Available: {', '.join(CORPORA.keys())}", err=True)
        raise typer.Exit(1)
    try:
        path = sync_corpus(name)  # type: ignore[arg-type]
        typer.echo(f"\nCorpus synced at: {path}")
    except Exception as e:
        typer.echo(f"Failed to sync corpus: {e}", err=True)
        raise typer.Exit(1) from None


@corpus_app.command("list")
def corpus_list() -> None:
    """List available corpora and download status.

    Examples:
        wafer corpus list
    """
    from .corpus import list_corpora

    list_corpora(verbose=True)


@corpus_app.command("path")
def corpus_path(
    name: str = typer.Argument(..., help="Corpus name"),
) -> None:
    """Print path to downloaded corpus (for scripting).

    Exits with code 1 if corpus not downloaded.

    Examples:
        wafer corpus path cuda
        cd $(wafer corpus path cutlass)
    """
    from .corpus import CORPORA, get_corpus_path

    if name not in CORPORA:
        typer.echo(f"Unknown corpus: {name}", err=True)
        raise typer.Exit(1)
    path = get_corpus_path(name)  # type: ignore[arg-type]
    if path is None:
        typer.echo(f"Corpus '{name}' not downloaded. Run: wafer corpus download {name}", err=True)
        raise typer.Exit(1)
    typer.echo(str(path))


# =============================================================================
# TraceLens commands (wafer tracelens ...)
# =============================================================================


@tracelens_app.command("check")
def tracelens_check(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check if TraceLens is installed.

    Examples:
        wafer tracelens check
        wafer tracelens check --json
    """
    from .tracelens import check_command

    try:
        result = check_command(json_output)
        if json_output:
            typer.echo(result)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@tracelens_app.command("report")
def tracelens_report(
    trace_path: str = typer.Argument(..., help="Path to trace file (.json, .zip, .gz, .pb)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    trace_format: str = typer.Option(
        "auto", "--format", "-f", help="Trace format: auto, pytorch, rocprof, jax"
    ),
    short_kernel: bool = typer.Option(
        False, "--short-kernel", help="Include short kernel analysis"
    ),
    kernel_details: bool = typer.Option(
        False, "--kernel-details", help="Include detailed kernel breakdown"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate performance report from trace file.

    Generates an Excel report with hierarchical breakdowns, kernel statistics,
    and efficiency metrics (TFLOP/s, TB/s).

    Examples:
        wafer tracelens report trace.json
        wafer tracelens report trace.json --format pytorch --kernel-details
        wafer tracelens report rocprof_results.json --format rocprof -o analysis.xlsx
    """
    from .tracelens import report_command

    try:
        result = report_command(
            trace_path=trace_path,
            output_path=output,
            trace_format=trace_format,
            short_kernel=short_kernel,
            kernel_details=kernel_details,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except RuntimeError:
        raise typer.Exit(1) from None


@tracelens_app.command("compare")
def tracelens_compare(
    baseline: str = typer.Argument(..., help="Path to baseline Excel report"),
    candidate: str = typer.Argument(..., help="Path to candidate Excel report"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output comparison file"),
    baseline_name: str = typer.Option(
        "baseline", "--baseline-name", help="Display name for baseline"
    ),
    candidate_name: str = typer.Option(
        "candidate", "--candidate-name", help="Display name for candidate"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Compare two performance reports.

    Quantifies differences between baseline and candidate reports.
    Useful for measuring optimization impact or regression detection.

    Examples:
        wafer tracelens compare baseline.xlsx candidate.xlsx
        wafer tracelens compare old.xlsx new.xlsx --baseline-name v1.0 --candidate-name v1.1
    """
    from .tracelens import compare_command

    try:
        result = compare_command(
            baseline_path=baseline,
            candidate_path=candidate,
            output_path=output,
            baseline_name=baseline_name,
            candidate_name=candidate_name,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except RuntimeError:
        raise typer.Exit(1) from None


@tracelens_app.command("collective")
def tracelens_collective(
    trace_dir: str = typer.Argument(..., help="Directory containing trace files for all ranks"),
    world_size: int = typer.Option(..., "--world-size", "-w", help="Number of ranks (GPUs)"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate multi-rank collective performance report.

    Analyzes distributed training traces across multiple GPUs,
    providing communication analysis and scaling insights.

    Examples:
        wafer tracelens collective ./traces --world-size 8
        wafer tracelens collective ./multi_gpu_traces -w 4 -o collective_analysis.xlsx
    """
    from .tracelens import collective_command

    try:
        result = collective_command(
            trace_dir=trace_dir,
            world_size=world_size,
            output_path=output,
            json_output=json_output,
        )
        if json_output:
            typer.echo(result)
    except RuntimeError:
        raise typer.Exit(1) from None


# =============================================================================
# Unified ISA Analysis Commands (wafer amd isa ...)
# =============================================================================


@isa_app.command("analyze")
def isa_analyze(
    path: Path = typer.Argument(..., help="Path to file or directory to analyze"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    csv_output: bool = typer.Option(False, "--csv", help="Output as CSV"),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="Scan directories recursively"
    ),
    filter_expr: str | None = typer.Option(
        None, "--filter", "-f", help="Filter results (e.g., 'spills > 0')"
    ),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Write output to file"),
    kernel_index: int = typer.Option(0, "--kernel", "-k", help="Kernel index if multiple in file"),
) -> None:
    """Analyze AMD GPU ISA files (.co, .s, .ll, .ttgir).

    Performs static analysis to extract performance metrics like register
    pressure, spills, MFMA density, and occupancy limits.

    Supports:
      - AMD GPU code objects (.co) - Requires API authentication
      - AMDGCN ISA assembly (.s, .gcn, .asm) - Local parsing
      - LLVM-IR files (.ll) - Local parsing
      - TTGIR files (.ttgir, .ttir, .mlir) - Local parsing

    Examples:
        wafer amd isa analyze kernel.co              # Code object (needs login)
        wafer amd isa analyze kernel.s               # ISA assembly
        wafer amd isa analyze kernel.s --json        # Output as JSON
        wafer amd isa analyze ~/.triton/cache/ --filter 'spills > 0'
        wafer amd isa analyze . -r --csv -o metrics.csv
    """
    from .auth import get_auth_headers
    from .global_config import get_api_url
    from .kernel_scope import analyze_command

    # Get API credentials for .co files
    api_url = get_api_url()
    auth_headers = get_auth_headers()

    try:
        output = analyze_command(
            path=str(path),
            json_output=json_output,
            csv_output=csv_output,
            recursive=recursive,
            filter_expr=filter_expr,
            output_file=str(output_file) if output_file else None,
            kernel_index=kernel_index,
            api_url=api_url,
            auth_headers=auth_headers,
        )
        typer.echo(output)

    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None


@isa_app.command("metrics")
def isa_metrics() -> None:
    """List available metrics for ISA analysis.

    Shows all metrics that can be extracted from AMD GPU ISA files,
    along with their derivation.

    Examples:
        wafer amd isa metrics
    """
    from .kernel_scope import metrics_command

    output = metrics_command()
    typer.echo(output)


@isa_app.command("targets")
def isa_targets() -> None:
    """List supported GPU targets and their specifications.

    Shows hardware specs (VGPRs, SGPRs, LDS, etc.) for each supported
    AMD GPU architecture.

    Examples:
        wafer amd isa targets
    """
    from .kernel_scope import targets_command

    output = targets_command()
    typer.echo(output)


# =============================================================================
# Trace comparison commands
# =============================================================================


@compare_app.command("analyze")
def compare_analyze(
    trace1: Path = typer.Argument(..., help="First trace file (AMD or NVIDIA)", exists=True),
    trace2: Path = typer.Argument(..., help="Second trace file (AMD or NVIDIA)", exists=True),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, text-layers, csv, csv-layers, json",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
    phase: str = typer.Option(
        "all",
        "--phase",
        help="Filter by phase: all, prefill, decode",
    ),
    layers: bool = typer.Option(False, "--layers", help="Show layer-wise performance breakdown"),
    all: bool = typer.Option(False, "--all", help="Show all items (no truncation for layers, operations, kernels)"),
    stack_traces: bool = typer.Option(False, "--stack-traces", help="Show Python stack traces for operations"),
    json: bool = typer.Option(False, "--json", hidden=True, help="Ignored (for compatibility with cliExecutor)"),
) -> None:
    """Compare GPU traces from two platforms platforms.

    Analyzes performance differences between traces, identifying which operations
    are faster/slower on each platform and providing kernel-level details.

    Examples:
        # Basic comparison (stdout)
        wafer compare analyze amd_trace.json nvidia_trace.json

        # Show layer-wise breakdown
        wafer compare analyze amd_trace.json nvidia_trace.json --layers
        wafer compare analyze amd_trace.json nvidia_trace.json --format text-layers

        # Show all layers without truncation
        wafer compare analyze amd_trace.json nvidia_trace.json --layers --all

        # Show Python stack traces
        wafer compare analyze amd_trace.json nvidia_trace.json --stack-traces

        # Show all stack traces without truncation
        wafer compare analyze amd_trace.json nvidia_trace.json --stack-traces --all

        # Save to file
        wafer compare analyze amd_trace.json nvidia_trace.json -o report.txt

        # CSV output (operations) to file
        wafer compare analyze amd_trace.json nvidia_trace.json --format csv -o operations.csv

        # CSV output (layers) to file
        wafer compare analyze amd_trace.json nvidia_trace.json --format csv-layers -o layers.csv

        # JSON output to file
        wafer compare analyze amd_trace.json nvidia_trace.json --format json -o report.json

        # Analyze only prefill phase
        wafer compare analyze amd_trace.json nvidia_trace.json --phase prefill
    """
    from .trace_compare import compare_traces

    compare_traces(
        trace1=trace1,
        trace2=trace2,
        output=output,
        output_format=format,
        phase=phase,
        show_layers=layers,
        show_all=all,
        show_stack_traces=stack_traces,
    )
    _mark_command_success()


@compare_app.command("fusion")
def compare_fusion_cmd(
    trace1: Path = typer.Argument(..., help="First trace file (AMD or NVIDIA)", exists=True),
    trace2: Path = typer.Argument(..., help="Second trace file (AMD or NVIDIA)", exists=True),
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, csv, json",
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output file (default: stdout)"),
    min_group_size: int = typer.Option(
        50,
        "--min-group-size",
        help="Minimum correlation group size to analyze",
    ),
    json: bool = typer.Option(False, "--json", hidden=True, help="Ignored (for compatibility with cliExecutor)"),
) -> None:
    """Analyze kernel fusion differences between AMD and NVIDIA traces.

    Detects which operations are fused differently on each platform by analyzing
    how many kernel launches each platform uses for the same logical operations.

    Examples:
        # Basic fusion analysis (stdout)
        wafer compare fusion amd_trace.json nvidia_trace.json

        # Save to file
        wafer compare fusion amd_trace.json nvidia_trace.json -o fusion_report.txt

        # JSON output to file
        wafer compare fusion amd_trace.json nvidia_trace.json --format json -o fusion.json

        # CSV output to file
        wafer compare fusion amd_trace.json nvidia_trace.json --format csv -o fusion.csv
    """
    from .trace_compare import compare_fusion

    compare_fusion(
        trace1=trace1,
        trace2=trace2,
        output=output,
        format_type=format,
        min_group_size=min_group_size,
    )
    _mark_command_success()


def main() -> None:
    """Entry point for wafer CLI."""
    app()


if __name__ == "__main__":
    main()
