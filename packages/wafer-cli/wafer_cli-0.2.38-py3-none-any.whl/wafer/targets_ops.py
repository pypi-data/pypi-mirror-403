"""Target operations for exec/ssh/sync commands.

This module provides the business logic for running commands on targets,
getting SSH credentials, and syncing files. It handles:
- RunPod: Auto-provision pod, get SSH credentials
- DigitalOcean: Auto-provision droplet, get SSH credentials
- Baremetal/VM: Direct SSH with configured credentials
- Workspace: Delegate to workspace API
- Modal/Local: Not supported (no SSH access)
"""

from __future__ import annotations

import logging
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wafer_core.utils.kernel_utils.targets.config import (
        BaremetalTarget,
        DigitalOceanTarget,
        RunPodTarget,
        TargetConfig,
        VMTarget,
    )

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TargetSSHInfo:
    """SSH connection info for a target."""

    host: str
    port: int
    user: str
    key_path: Path


class TargetExecError(Exception):
    """Error during target operation (exec/ssh/sync)."""

    pass


def _expand_key_path(ssh_key: str) -> Path:
    """Expand SSH key path (synchronous, fast operation)."""
    return Path(ssh_key).expanduser()


def _parse_ssh_target(ssh_target: str) -> tuple[str, str, int]:
    """Parse ssh_target string into (user, host, port).

    Format: user@host:port
    """
    # Split user@host:port
    if "@" not in ssh_target:
        raise ValueError(f"Invalid ssh_target format: {ssh_target} (expected user@host:port)")

    user, rest = ssh_target.split("@", 1)

    if ":" not in rest:
        raise ValueError(f"Invalid ssh_target format: {ssh_target} (expected user@host:port)")

    host, port_str = rest.rsplit(":", 1)

    try:
        port = int(port_str)
    except ValueError as e:
        raise ValueError(f"Invalid port in ssh_target: {port_str}") from e

    return user, host, port


async def get_target_ssh_info(target: TargetConfig) -> TargetSSHInfo:
    """Get SSH connection info for a target.

    For RunPod/DigitalOcean: Provisions if needed, returns SSH info.
    For Baremetal/VM: Returns configured SSH info directly.
    For Modal/Local/Workspace: Raises (no SSH access).

    Args:
        target: Target configuration

    Returns:
        TargetSSHInfo with host, port, user, key_path

    Raises:
        TargetExecError: If target type doesn't support SSH
    """
    from wafer_core.utils.kernel_utils.targets.config import (
        BaremetalTarget,
        DigitalOceanTarget,
        LocalTarget,
        ModalTarget,
        RunPodTarget,
        VMTarget,
        WorkspaceTarget,
    )

    if isinstance(target, RunPodTarget):
        return await _get_runpod_ssh_info(target)
    elif isinstance(target, DigitalOceanTarget):
        return await _get_digitalocean_ssh_info(target)
    elif isinstance(target, (BaremetalTarget, VMTarget)):
        return _get_direct_ssh_info(target)
    elif isinstance(target, WorkspaceTarget):
        raise TargetExecError(
            f"WorkspaceTarget '{target.name}' uses API-based access.\n"
            "Use 'wafer workspaces exec/ssh/sync' instead."
        )
    elif isinstance(target, ModalTarget):
        raise TargetExecError(
            f"ModalTarget '{target.name}' is serverless and has no SSH access.\n"
            "Use 'wafer evaluate' to run code on Modal targets."
        )
    elif isinstance(target, LocalTarget):
        raise TargetExecError(
            f"LocalTarget '{target.name}' runs locally and has no SSH.\n"
            "Run commands directly on this machine."
        )
    else:
        raise TargetExecError(f"Unknown target type: {type(target).__name__}")


async def _get_runpod_ssh_info(target: RunPodTarget) -> TargetSSHInfo:
    """Get SSH info for RunPod target, provisioning if needed."""
    from wafer_core.targets.runpod import check_pod_running, get_pod_state, runpod_ssh_context

    key_path = _expand_key_path(target.ssh_key)

    # Check if pod already exists and is running
    existing = get_pod_state(target.name)
    if existing and await check_pod_running(existing.pod_id):
        # Reuse existing pod
        return TargetSSHInfo(
            host=existing.public_ip,
            port=existing.ssh_port,
            user=existing.ssh_username,
            key_path=key_path,
        )

    # Need to provision - use the context manager but don't terminate
    # We'll provision and keep the pod running for the exec/ssh/sync operation
    # The user can run `wafer config targets cleanup` to terminate later

    # Temporarily override keep_alive to True so we don't terminate after getting info
    target_keep_alive = replace(target, keep_alive=True)

    async with runpod_ssh_context(target_keep_alive) as ssh_info:
        return TargetSSHInfo(
            host=ssh_info.host,
            port=ssh_info.port,
            user=ssh_info.user,
            key_path=key_path,
        )


async def _get_digitalocean_ssh_info(target: DigitalOceanTarget) -> TargetSSHInfo:
    """Get SSH info for DigitalOcean target, provisioning if needed."""
    from wafer_core.targets.digitalocean import (
        check_droplet_running,
        digitalocean_ssh_context,
        get_droplet_state,
    )

    key_path = _expand_key_path(target.ssh_key)

    # Check if droplet already exists and is running
    existing = get_droplet_state(target.name)
    if existing and await check_droplet_running(existing.droplet_id):
        # Reuse existing droplet
        return TargetSSHInfo(
            host=existing.public_ip,
            port=22,  # DigitalOcean uses standard SSH port
            user=existing.ssh_username,
            key_path=key_path,
        )

    # Need to provision - use the context manager but don't terminate
    target_keep_alive = replace(target, keep_alive=True)

    async with digitalocean_ssh_context(target_keep_alive) as ssh_info:
        return TargetSSHInfo(
            host=ssh_info.host,
            port=ssh_info.port,
            user=ssh_info.user,
            key_path=key_path,
        )


def _get_direct_ssh_info(target: BaremetalTarget | VMTarget) -> TargetSSHInfo:
    """Get SSH info for Baremetal/VM target (no provisioning needed)."""
    user, host, port = _parse_ssh_target(target.ssh_target)
    key_path = _expand_key_path(target.ssh_key)

    if not key_path.exists():
        raise TargetExecError(f"SSH key not found: {key_path}")

    return TargetSSHInfo(
        host=host,
        port=port,
        user=user,
        key_path=key_path,
    )


def exec_on_target_sync(
    ssh_info: TargetSSHInfo,
    command: str,
    timeout_seconds: int | None = None,
) -> int:
    """Execute a command on target via SSH (synchronous).

    Args:
        ssh_info: SSH connection info
        command: Command to execute
        timeout_seconds: Optional timeout

    Returns:
        Exit code from the remote command
    """
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
        "-o",
        "LogLevel=ERROR",
        f"{ssh_info.user}@{ssh_info.host}",
        command,
    ]

    try:
        result = subprocess.run(
            ssh_args,
            timeout=timeout_seconds,
        )
        return result.returncode
    except subprocess.TimeoutExpired as e:
        raise TargetExecError(f"Command timed out after {timeout_seconds}s") from e


def sync_to_target(
    ssh_info: TargetSSHInfo,
    local_path: Path,
    remote_path: str | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """Sync files to target via rsync over SSH.

    Args:
        ssh_info: SSH connection info
        local_path: Local file or directory to sync
        remote_path: Remote destination (default: /tmp/{basename})
        on_progress: Optional callback for progress messages

    Returns:
        Number of files synced
    """
    if remote_path is None:
        remote_path = f"/tmp/{local_path.name}"

    # Build rsync command
    ssh_cmd = (
        f"ssh -i {ssh_info.key_path} -p {ssh_info.port} "
        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
    )

    # Add trailing slash to sync directory contents
    source = str(local_path.resolve())
    if local_path.is_dir():
        source = source.rstrip("/") + "/"

    rsync_args = [
        "rsync",
        "-avz",
        "--progress",
        "-e",
        ssh_cmd,
        source,
        f"{ssh_info.user}@{ssh_info.host}:{remote_path}",
    ]

    if on_progress:
        on_progress(f"Syncing {local_path} to {ssh_info.host}:{remote_path}")

    result = subprocess.run(
        rsync_args,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise TargetExecError(f"rsync failed: {result.stderr}")

    # Count files from rsync output (lines that don't start with special chars)
    file_count = 0
    for line in result.stdout.splitlines():
        # rsync shows transferred files without leading special chars
        if line and not line.startswith((" ", ".", "sent", "total", "building")):
            file_count += 1

    if on_progress:
        on_progress(f"Synced {file_count} files")

    return file_count


def parse_scp_path(path: str) -> tuple[str | None, str]:
    """Parse scp-style path into (target_name, path).

    Returns (None, path) for local paths, (target_name, remote_path) for remote.

    Examples:
        "./local/file" -> (None, "./local/file")
        "target:/remote/path" -> ("target", "/remote/path")
        "my-target:/tmp/foo" -> ("my-target", "/tmp/foo")
    """
    if ":" in path:
        # Check if it looks like a Windows path (e.g., C:\...)
        if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
            return (None, path)
        target, remote_path = path.split(":", 1)
        return (target, remote_path)
    return (None, path)


def _has_glob_chars(path: str) -> bool:
    """Check if path contains glob characters."""
    return any(c in path for c in "*?[]")


def _sanitize_glob_pattern(pattern: str) -> str:
    """Sanitize a glob pattern for safe shell execution.

    Escapes dangerous shell metacharacters while preserving glob characters (* ? [ ]).
    This prevents command injection while allowing glob expansion.
    """
    # Characters that could enable command injection
    dangerous_chars = {
        ";": r"\;",
        "$": r"\$",
        "`": r"\`",
        "|": r"\|",
        "&": r"\&",
        "(": r"\(",
        ")": r"\)",
        "{": r"\{",
        "}": r"\}",
        "<": r"\<",
        ">": r"\>",
        "\n": "",  # Remove newlines entirely
        "\r": "",
    }
    result = pattern
    for char, escaped in dangerous_chars.items():
        result = result.replace(char, escaped)
    return result


def _expand_remote_glob(ssh_info: TargetSSHInfo, pattern: str) -> list[str]:
    """Expand a glob pattern on the remote host.

    Returns list of matching file paths, empty if no matches.
    """
    # Sanitize pattern to prevent command injection while preserving glob chars
    safe_pattern = _sanitize_glob_pattern(pattern)

    # Use ls -1d to expand glob (handles files and dirs, one per line)
    # The -d flag prevents listing directory contents
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
        "-o",
        "LogLevel=ERROR",
        f"{ssh_info.user}@{ssh_info.host}",
        f"ls -1d {safe_pattern} 2>/dev/null",
    ]

    result = subprocess.run(ssh_args, capture_output=True, text=True)

    if result.returncode != 0 or not result.stdout.strip():
        return []

    return result.stdout.strip().split("\n")


def _scp_single_file(
    ssh_info: TargetSSHInfo,
    remote_path: str,
    local_dest: str,
    recursive: bool,
) -> None:
    """Download a single file/dir from remote."""
    scp_args = [
        "scp",
        "-i",
        str(ssh_info.key_path),
        "-P",
        str(ssh_info.port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "LogLevel=ERROR",
    ]

    if recursive:
        scp_args.append("-r")

    scp_args.extend([
        f"{ssh_info.user}@{ssh_info.host}:{remote_path}",
        local_dest,
    ])

    result = subprocess.run(scp_args, capture_output=True, text=True)
    if result.returncode != 0:
        raise TargetExecError(f"scp failed for {remote_path}: {result.stderr}")


def _scp_glob_download(
    ssh_info: TargetSSHInfo,
    remote_pattern: str,
    local_dest: str,
    recursive: bool,
) -> None:
    """Download files matching a glob pattern from remote.

    Expands the glob on the remote host, then downloads each file.
    """
    files = _expand_remote_glob(ssh_info, remote_pattern)

    if not files:
        logger.warning(f"No files matched pattern: {remote_pattern}")
        return

    for remote_file in files:
        _scp_single_file(ssh_info, remote_file, local_dest, recursive)


def scp_transfer(
    ssh_info: TargetSSHInfo,
    source: str,
    dest: str,
    is_download: bool,
    recursive: bool = False,
) -> None:
    """Transfer files via scp. Supports glob patterns for downloads.

    Args:
        ssh_info: SSH connection info
        source: Source path (local for upload, remote for download)
        dest: Destination path (remote for upload, local for download)
        is_download: True if downloading from remote, False if uploading
        recursive: Whether to copy directories recursively

    Raises:
        TargetExecError: If scp fails
    """
    # Handle glob patterns for downloads
    if is_download and _has_glob_chars(source):
        return _scp_glob_download(ssh_info, source, dest, recursive)

    scp_args = [
        "scp",
        "-i",
        str(ssh_info.key_path),
        "-P",
        str(ssh_info.port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "LogLevel=ERROR",
    ]

    if recursive:
        scp_args.append("-r")

    if is_download:
        # remote -> local
        scp_args.extend([
            f"{ssh_info.user}@{ssh_info.host}:{source}",
            dest,
        ])
    else:
        # local -> remote
        scp_args.extend([
            source,
            f"{ssh_info.user}@{ssh_info.host}:{dest}",
        ])

    result = subprocess.run(scp_args, capture_output=True, text=True)
    if result.returncode != 0:
        raise TargetExecError(f"scp failed: {result.stderr}")


# =============================================================================
# Tool Registry for `wafer targets ensure`
# =============================================================================


@dataclass(frozen=True)
class ToolSpec:
    """Specification for a tool that can be installed on a target."""

    name: str
    check_cmd: str  # Command to check if installed (exit 0 = installed)
    install_cmd: str | None  # Command to install (None = can't auto-install)
    verify_cmd: str | None = None  # Command to verify after install
    platform: str = "any"  # "amd", "nvidia", or "any"
    description: str = ""


TOOL_REGISTRY: dict[str, ToolSpec] = {
    # AMD Tools
    "rocprof-compute": ToolSpec(
        name="rocprof-compute",
        check_cmd="which rocprof-compute",
        # rocprofiler-compute requires ROCm >= 6.3 and apt install (not pip)
        # For older ROCm, users need to upgrade or install manually
        install_cmd="apt-get update && apt-get install -y rocprofiler-compute && python3 -m pip install -r /opt/rocm/libexec/rocprofiler-compute/requirements.txt",
        verify_cmd="rocprof-compute --version",
        platform="amd",
        description="AMD GPU profiling (roofline, memory, etc.) - requires ROCm >= 6.3",
    ),
    "rocprof-systems": ToolSpec(
        name="rocprof-systems",
        check_cmd="which rocprof-systems",
        # rocprofiler-systems also requires apt install on ROCm >= 6.3
        install_cmd="apt-get update && apt-get install -y rocprofiler-systems && python3 -m pip install -r /opt/rocm/libexec/rocprofiler-systems/requirements.txt",
        verify_cmd="rocprof-systems --version",
        platform="amd",
        description="AMD system-wide tracing - requires ROCm >= 6.3",
    ),
    "rocprof": ToolSpec(
        name="rocprof",
        check_cmd="which rocprof",
        install_cmd=None,  # Part of ROCm base install
        platform="amd",
        description="AMD kernel profiling (part of ROCm)",
    ),
    # NVIDIA Tools
    "ncu": ToolSpec(
        name="ncu",
        check_cmd="which ncu",
        install_cmd=None,  # Part of CUDA toolkit
        platform="nvidia",
        description="NVIDIA Nsight Compute (part of CUDA toolkit)",
    ),
    "nsys": ToolSpec(
        name="nsys",
        check_cmd="which nsys",
        install_cmd=None,  # Part of CUDA toolkit
        platform="nvidia",
        description="NVIDIA Nsight Systems (part of CUDA toolkit)",
    ),
    "nvtx": ToolSpec(
        name="nvtx",
        check_cmd='python -c "import nvtx"',
        install_cmd="pip install nvtx",
        verify_cmd='python -c "import nvtx; print(nvtx.__version__)"',
        platform="nvidia",
        description="NVIDIA Tools Extension (Python)",
    ),
    # Cross-platform Python packages
    "triton": ToolSpec(
        name="triton",
        check_cmd='python -c "import triton"',
        install_cmd="pip install triton",
        verify_cmd='python -c "import triton; print(triton.__version__)"',
        platform="any",
        description="OpenAI Triton compiler",
    ),
    "torch": ToolSpec(
        name="torch",
        check_cmd='python -c "import torch"',
        install_cmd="pip install torch",
        verify_cmd='python -c "import torch; print(torch.__version__)"',
        platform="any",
        description="PyTorch",
    ),
}


def get_target_platform(target: TargetConfig) -> str:
    """Determine platform (amd/nvidia) from target config."""
    # Import target types for isinstance checks
    from wafer_core.utils.kernel_utils.targets.config import (
        DigitalOceanTarget,
        LocalTarget,
        RunPodTarget,
    )

    # RunPod and DigitalOcean are always AMD MI300X
    if isinstance(target, (RunPodTarget, DigitalOceanTarget)):
        return "amd"

    # LocalTarget has explicit vendor field
    if isinstance(target, LocalTarget):
        return target.vendor

    # For Baremetal/VM, check gpu_type or compute_capability
    gpu_type = getattr(target, "gpu_type", "")
    if "MI300" in gpu_type:
        return "amd"

    compute_cap = getattr(target, "compute_capability", "")
    if compute_cap == "9.4":  # gfx942 = MI300X
        return "amd"

    # Default to nvidia for other compute capabilities
    return "nvidia"


@dataclass
class EnsureResult:
    """Result of ensure_tool operation."""

    tool: str
    already_installed: bool
    installed: bool
    verified: bool
    error: str | None = None


def ensure_tool(
    ssh_info: TargetSSHInfo,
    tool: str,
    force: bool = False,
    timeout: int = 300,
) -> EnsureResult:
    """Ensure a tool is installed on target.

    Args:
        ssh_info: SSH connection info
        tool: Tool name from TOOL_REGISTRY
        force: If True, reinstall even if present
        timeout: Timeout for install command

    Returns:
        EnsureResult with status
    """
    if tool not in TOOL_REGISTRY:
        return EnsureResult(
            tool=tool,
            already_installed=False,
            installed=False,
            verified=False,
            error=f"Unknown tool: {tool}. Available: {', '.join(sorted(TOOL_REGISTRY.keys()))}",
        )

    spec = TOOL_REGISTRY[tool]

    # Check if already installed
    if not force:
        exit_code = exec_on_target_sync(ssh_info, spec.check_cmd, timeout_seconds=30)
        if exit_code == 0:
            return EnsureResult(
                tool=tool,
                already_installed=True,
                installed=False,
                verified=True,
            )

    # Can't auto-install
    if spec.install_cmd is None:
        return EnsureResult(
            tool=tool,
            already_installed=False,
            installed=False,
            verified=False,
            error=f"{tool} cannot be auto-installed. It's part of the base platform (ROCm/CUDA).",
        )

    # Install
    exit_code = exec_on_target_sync(ssh_info, spec.install_cmd, timeout_seconds=timeout)
    if exit_code != 0:
        return EnsureResult(
            tool=tool,
            already_installed=False,
            installed=False,
            verified=False,
            error=f"Installation failed (exit code {exit_code})",
        )

    # Verify
    verified = True
    if spec.verify_cmd:
        exit_code = exec_on_target_sync(ssh_info, spec.verify_cmd, timeout_seconds=30)
        verified = exit_code == 0

    return EnsureResult(
        tool=tool,
        already_installed=False,
        installed=True,
        verified=verified,
        error=None if verified else "Installation succeeded but verification failed",
    )
