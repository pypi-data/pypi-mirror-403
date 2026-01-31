"""Target management for Wafer CLI.

CRUD operations for GPU targets stored in ~/.wafer/targets/.
"""

import tomllib
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from wafer_core.utils.kernel_utils.targets.config import (
    BaremetalTarget,
    DigitalOceanTarget,
    ModalTarget,
    RunPodTarget,
    TargetConfig,
    VMTarget,
    WorkspaceTarget,
)


def _filter_dataclass_fields(data: dict[str, Any], dataclass_type: type) -> dict[str, Any]:
    """Filter dict to only include fields that exist in the dataclass."""
    valid_fields = {f.name for f in fields(dataclass_type)}
    return {k: v for k, v in data.items() if k in valid_fields}

# Default paths
WAFER_DIR = Path.home() / ".wafer"
TARGETS_DIR = WAFER_DIR / "targets"
CONFIG_FILE = WAFER_DIR / "config.toml"


def _ensure_dirs() -> None:
    """Ensure ~/.wafer/targets/ exists."""
    TARGETS_DIR.mkdir(parents=True, exist_ok=True)


def _target_path(name: str) -> Path:
    """Get path to target config file."""
    return TARGETS_DIR / f"{name}.toml"


def _parse_target(data: dict[str, Any]) -> TargetConfig:
    """Parse TOML dict into target dataclass.

    Args:
        data: Parsed TOML data

    Returns:
        TargetConfig (BaremetalTarget, VMTarget, ModalTarget, or WorkspaceTarget)

    Raises:
        ValueError: If target type is unknown or required fields missing
    """
    target_type = data.get("type")
    if not target_type:
        raise ValueError(
            "Target must have 'type' field (baremetal, vm, modal, workspace, runpod, or digitalocean)"
        )

    # Remove type field before passing to dataclass
    data_copy = {k: v for k, v in data.items() if k != "type"}

    # Convert pip_packages list to tuple (TOML parses as list, dataclass expects tuple)
    if "pip_packages" in data_copy and isinstance(data_copy["pip_packages"], list):
        data_copy["pip_packages"] = tuple(data_copy["pip_packages"])

    # Convert gpu_ids list to tuple for RunPodTarget
    if "gpu_ids" in data_copy and isinstance(data_copy["gpu_ids"], list):
        data_copy["gpu_ids"] = tuple(data_copy["gpu_ids"])

    if target_type == "baremetal":
        return BaremetalTarget(**_filter_dataclass_fields(data_copy, BaremetalTarget))
    elif target_type == "vm":
        return VMTarget(**_filter_dataclass_fields(data_copy, VMTarget))
    elif target_type == "modal":
        return ModalTarget(**_filter_dataclass_fields(data_copy, ModalTarget))
    elif target_type == "workspace":
        return WorkspaceTarget(**_filter_dataclass_fields(data_copy, WorkspaceTarget))
    elif target_type == "runpod":
        return RunPodTarget(**_filter_dataclass_fields(data_copy, RunPodTarget))
    elif target_type == "digitalocean":
        return DigitalOceanTarget(**_filter_dataclass_fields(data_copy, DigitalOceanTarget))
    else:
        raise ValueError(
            f"Unknown target type: {target_type}. Must be baremetal, vm, modal, workspace, runpod, or digitalocean"
        )


def _serialize_target(target: TargetConfig) -> dict[str, Any]:
    """Serialize target dataclass to TOML-compatible dict.

    Args:
        target: Target config

    Returns:
        Dict with 'type' field added
    """
    data = asdict(target)

    # Add type field
    if isinstance(target, BaremetalTarget):
        data["type"] = "baremetal"
    elif isinstance(target, VMTarget):
        data["type"] = "vm"
    elif isinstance(target, ModalTarget):
        data["type"] = "modal"
    elif isinstance(target, WorkspaceTarget):
        data["type"] = "workspace"
    elif isinstance(target, RunPodTarget):
        data["type"] = "runpod"
    elif isinstance(target, DigitalOceanTarget):
        data["type"] = "digitalocean"

    # Convert pip_packages tuple to list for TOML serialization
    if "pip_packages" in data and isinstance(data["pip_packages"], tuple):
        data["pip_packages"] = list(data["pip_packages"])

    # Convert gpu_ids tuple to list for TOML serialization
    if "gpu_ids" in data and isinstance(data["gpu_ids"], tuple):
        data["gpu_ids"] = list(data["gpu_ids"])

    # Remove empty pip_packages to keep config clean
    if "pip_packages" in data and not data["pip_packages"]:
        del data["pip_packages"]

    return data


def _write_toml(path: Path, data: dict[str, Any]) -> None:
    """Write dict as TOML file.

    Simple TOML writer - handles flat dicts and lists.
    """
    lines = []
    for key, value in data.items():
        if value is None:
            continue  # Skip None values
        if isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, int | float):
            lines.append(f"{key} = {value}")
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, list):
            # Format list
            if all(isinstance(v, int) for v in value):
                lines.append(f"{key} = {value}")
            else:
                formatted = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                lines.append(f"{key} = [{formatted}]")

    path.write_text("\n".join(lines) + "\n")


def load_target(name: str) -> TargetConfig:
    """Load target config by name.

    Args:
        name: Target name (filename without .toml)

    Returns:
        Target config

    Raises:
        FileNotFoundError: If target doesn't exist
        ValueError: If target config is invalid
    """
    path = _target_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Target not found: {name} (looked in {path})")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return _parse_target(data)


def save_target(target: TargetConfig | dict[str, Any]) -> TargetConfig:
    """Save target config.

    Args:
        target: Target config (TargetConfig object or dict with 'type' field)

    Returns:
        The saved TargetConfig object

    Creates ~/.wafer/targets/{name}.toml
    """
    _ensure_dirs()

    # If dict, parse into TargetConfig first
    if isinstance(target, dict):
        target = _parse_target(target)

    data = _serialize_target(target)
    path = _target_path(target.name)
    _write_toml(path, data)
    return target


def add_target_from_file(file_path: Path) -> TargetConfig:
    """Add target from TOML file.

    Args:
        file_path: Path to TOML file

    Returns:
        Parsed and saved target

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    target = _parse_target(data)
    save_target(target)
    return target


def list_targets() -> list[str]:
    """List all configured target names.

    Returns:
        Sorted list of target names
    """
    _ensure_dirs()
    return sorted(p.stem for p in TARGETS_DIR.glob("*.toml"))


def remove_target(name: str) -> None:
    """Remove target config.

    Args:
        name: Target name to remove

    Raises:
        FileNotFoundError: If target doesn't exist
    """
    path = _target_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Target not found: {name}")
    path.unlink()


def get_default_target() -> str | None:
    """Get default target name from config.

    Returns:
        Default target name, or None if not set
    """
    if not CONFIG_FILE.exists():
        return None

    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    return data.get("default_target")


# ── Pool Management ─────────────────────────────────────────────────────────


def get_pool(name: str) -> list[str]:
    """Get list of targets in a named pool.

    Pools are defined in ~/.wafer/config.toml:
        [pools.my-pool]
        targets = ["target-1", "target-2", "target-3"]

    Args:
        name: Pool name

    Returns:
        List of target names in the pool

    Raises:
        FileNotFoundError: If pool doesn't exist
    """
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Pool not found: {name} (no config file)")

    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    pools = data.get("pools", {})
    if name not in pools:
        raise FileNotFoundError(
            f"Pool not found: {name}\n"
            f"  Define pools in ~/.wafer/config.toml:\n"
            f"  [pools.{name}]\n"
            f'  targets = ["target-1", "target-2"]'
        )

    pool_config = pools[name]
    targets = pool_config.get("targets", [])

    if not targets:
        raise ValueError(f"Pool '{name}' has no targets defined")

    return targets


def get_target_type(name: str) -> str | None:
    """Get the type of a target without fully loading it.

    Args:
        name: Target name

    Returns:
        Target type string (runpod, digitalocean, baremetal, etc.) or None if not found
    """
    path = _target_path(name)
    if not path.exists():
        return None

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return data.get("type")


def filter_pool_by_auth(target_names: list[str]) -> tuple[list[str], list[str]]:
    """Filter pool targets to only those with valid authentication.

    Args:
        target_names: List of target names to filter

    Returns:
        Tuple of (usable_targets, skipped_targets)
    """
    from wafer_core.auth import get_api_key

    usable = []
    skipped = []

    for name in target_names:
        target_type = get_target_type(name)
        if target_type is None:
            # Target doesn't exist, skip it
            skipped.append(name)
            continue

        # Check auth requirements by target type
        if target_type == "runpod":
            if not get_api_key("runpod"):
                skipped.append(name)
                continue
        elif target_type == "digitalocean":
            if not get_api_key("digitalocean"):
                skipped.append(name)
                continue
        # Other types (baremetal, vm, workspace, modal) don't need runtime API keys

        usable.append(name)

    return usable, skipped


def list_pools() -> list[str]:
    """List all configured pool names.

    Returns:
        Sorted list of pool names
    """
    if not CONFIG_FILE.exists():
        return []

    with open(CONFIG_FILE, "rb") as f:
        data = tomllib.load(f)

    return sorted(data.get("pools", {}).keys())


def save_pool(name: str, targets: list[str]) -> None:
    """Save or update a pool configuration.

    Args:
        name: Pool name
        targets: List of target names (must all exist)

    Raises:
        FileNotFoundError: If any target doesn't exist
    """
    # Verify all targets exist
    existing_targets = list_targets()
    missing = [t for t in targets if t not in existing_targets]
    if missing:
        raise FileNotFoundError(f"Targets not found: {', '.join(missing)}")

    _ensure_dirs()

    # Load existing config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    # Update pools section
    if "pools" not in data:
        data["pools"] = {}

    data["pools"][name] = {"targets": targets}

    # Write back - need custom handling for nested structure
    _write_config_with_pools(data)


def _write_config_with_pools(data: dict) -> None:
    """Write config file with pools support.

    Handles the nested [pools.name] TOML structure and preserves
    existing nested sections like [default], [api], [environments.*].
    """
    lines = []

    # Collect nested sections to write after top-level keys
    nested_sections: dict[str, dict] = {}

    # Write top-level keys first (except pools and nested dicts)
    for key, value in data.items():
        if key == "pools":
            continue
        if value is None:
            continue
        if isinstance(value, dict):
            # Save nested sections for later
            nested_sections[key] = value
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, int | float):
            lines.append(f"{key} = {value}")
        elif isinstance(value, list):
            if all(isinstance(v, int) for v in value):
                lines.append(f"{key} = {value}")
            else:
                formatted = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                lines.append(f"{key} = [{formatted}]")

    # Write nested sections (e.g., [default], [api], [environments.foo])
    for section_name, section_data in nested_sections.items():
        lines.append("")
        lines.append(f"[{section_name}]")
        for key, value in section_data.items():
            if value is None:
                continue
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, int | float):
                lines.append(f"{key} = {value}")
            elif isinstance(value, list):
                if all(isinstance(v, int) for v in value):
                    lines.append(f"{key} = {value}")
                else:
                    formatted = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                    lines.append(f"{key} = [{formatted}]")

    # Write pools
    pools = data.get("pools", {})
    for pool_name, pool_config in pools.items():
        lines.append("")
        lines.append(f"[pools.{pool_name}]")
        targets = pool_config.get("targets", [])
        formatted = ", ".join(f'"{t}"' for t in targets)
        lines.append(f"targets = [{formatted}]")

    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def set_default_target(name: str) -> None:
    """Set default target.

    Args:
        name: Target name (must exist)

    Raises:
        FileNotFoundError: If target doesn't exist
    """
    # Verify target exists
    if name not in list_targets():
        raise FileNotFoundError(f"Target not found: {name}")

    _ensure_dirs()

    # Load existing config or create new
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
    else:
        data = {}

    data["default_target"] = name

    # Write back (simple TOML)
    _write_toml(CONFIG_FILE, data)


def get_target_info(target: TargetConfig) -> dict[str, str]:
    """Get human-readable info about target.

    Args:
        target: Target config

    Returns:
        Dict of field name -> display value
    """
    info = {}

    if isinstance(target, BaremetalTarget):
        info["Type"] = "Baremetal"
        info["SSH"] = target.ssh_target
        info["GPUs"] = ", ".join(str(g) for g in target.gpu_ids)
        info["NCU"] = "Yes" if target.ncu_available else "No"
        # Docker info
        if target.docker_image:
            info["Docker"] = target.docker_image
            if target.pip_packages:
                info["Packages"] = ", ".join(target.pip_packages)
            if target.torch_package:
                info["Torch"] = target.torch_package
    elif isinstance(target, VMTarget):
        info["Type"] = "VM"
        info["SSH"] = target.ssh_target
        info["GPUs"] = ", ".join(str(g) for g in target.gpu_ids)
        info["NCU"] = "Yes" if target.ncu_available else "No"
        # Docker info
        if target.docker_image:
            info["Docker"] = target.docker_image
            if target.pip_packages:
                info["Packages"] = ", ".join(target.pip_packages)
            if target.torch_package:
                info["Torch"] = target.torch_package
    elif isinstance(target, ModalTarget):
        info["Type"] = "Modal"
        info["App"] = target.modal_app_name
        info["GPU"] = target.gpu_type
        info["Timeout"] = f"{target.timeout_seconds}s"
        info["NCU"] = "No (Modal)"
    elif isinstance(target, WorkspaceTarget):
        info["Type"] = "Workspace"
        info["Workspace ID"] = target.workspace_id
        info["GPU"] = target.gpu_type
        info["Timeout"] = f"{target.timeout_seconds}s"
        info["NCU"] = "No (Workspace)"
    elif isinstance(target, RunPodTarget):
        info["Type"] = "RunPod"
        info["GPU Type"] = target.gpu_type_id
        info["GPU Count"] = str(target.gpu_count)
        info["Image"] = target.image
        info["Keep Alive"] = "Yes" if target.keep_alive else "No"
        info["NCU"] = "No (RunPod)"
    elif isinstance(target, DigitalOceanTarget):
        info["Type"] = "DigitalOcean"
        info["Region"] = target.region
        info["Size"] = target.size_slug
        info["Image"] = target.image
        info["Keep Alive"] = "Yes" if target.keep_alive else "No"
        info["NCU"] = "No (DigitalOcean)"

    info["Compute"] = target.compute_capability

    return info


# Probe script to run on target - checks available backends
_PROBE_SCRIPT = """
import json
import shutil
import sys

def probe():
    result = {
        "python_version": sys.version.split()[0],
        "backends": {},
        "packages": {},
    }

    # Check Triton
    try:
        import triton
        result["backends"]["triton"] = triton.__version__
    except ImportError:
        result["backends"]["triton"] = None

    # Check torch
    try:
        import torch
        result["packages"]["torch"] = torch.__version__
        result["backends"]["torch"] = torch.__version__
        result["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            result["gpu_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            result["compute_capability"] = f"{props.major}.{props.minor}"
    except ImportError:
        result["packages"]["torch"] = None

    # Check hipcc (AMD)
    hipcc = shutil.which("hipcc")
    result["backends"]["hipcc"] = hipcc

    # Check nvcc (NVIDIA)
    nvcc = shutil.which("nvcc")
    result["backends"]["nvcc"] = nvcc

    # Check ROCm version
    try:
        with open("/opt/rocm/.info/version", "r") as f:
            result["rocm_version"] = f.read().strip()
    except Exception:
        result["rocm_version"] = None

    # Check CUDA version from nvcc
    if nvcc:
        import subprocess
        try:
            out = subprocess.check_output([nvcc, "--version"], text=True)
            for line in out.split("\\n"):
                if "release" in line.lower():
                    # Parse "Cuda compilation tools, release 12.1, V12.1.105"
                    parts = line.split("release")
                    if len(parts) > 1:
                        result["cuda_version"] = parts[1].split(",")[0].strip()
                    break
        except Exception:
            pass

    print(json.dumps(result))

if __name__ == "__main__":
    probe()
"""


class ProbeError(Exception):
    """Error during target probing with actionable context."""

    pass


async def probe_target_capabilities(target: TargetConfig) -> dict[str, Any]:
    """Probe a target to discover available compilation backends.

    Connects to the target and runs a probe script to check:
    - Triton availability
    - torch availability
    - HIP/CUDA compiler
    - ROCm/CUDA version
    - GPU info

    Args:
        target: Target config

    Returns:
        Dict with capabilities info

    Raises:
        ProbeError: With actionable error message on failure
    """
    import json
    import subprocess

    if isinstance(target, RunPodTarget):
        import trio_asyncio
        from wafer_core.targets.runpod import RunPodError, get_pod_state, runpod_ssh_context

        # Check if pod exists before trying to connect
        pod_state = get_pod_state(target.name)

        try:
            # Need trio_asyncio.open_loop() for asyncssh bridge used by runpod_ssh_context
            async with trio_asyncio.open_loop():
                async with runpod_ssh_context(target) as ssh_info:
                    ssh_target = f"{ssh_info.user}@{ssh_info.host}"
                    port = ssh_info.port
                    key_path = target.ssh_key

                    # Find Python and run probe using subprocess (simpler than async ssh)
                    def run_ssh_cmd(cmd: str) -> tuple[int, str, str]:
                        try:
                            result = subprocess.run(
                                [
                                    "ssh",
                                    "-o",
                                    "StrictHostKeyChecking=no",
                                    "-o",
                                    "UserKnownHostsFile=/dev/null",
                                    "-o",
                                    "ConnectTimeout=30",
                                    "-i",
                                    str(key_path),
                                    "-p",
                                    str(port),
                                    ssh_target,
                                    cmd,
                                ],
                                capture_output=True,
                                text=True,
                                timeout=60,
                            )
                            return result.returncode, result.stdout, result.stderr
                        except subprocess.TimeoutExpired:
                            raise ProbeError(
                                f"SSH connection timed out\n"
                                f"  Host: {ssh_target}:{port}\n"
                                f"  Hint: The pod may be starting up. Try again in 30 seconds."
                            ) from None

                    # Find Python
                    python_exe = "python3"
                    for candidate in [
                        "/opt/conda/envs/py_3.10/bin/python3",
                        "/opt/conda/bin/python3",
                    ]:
                        code, out, _ = run_ssh_cmd(f"{candidate} --version 2>/dev/null && echo OK")
                        if code == 0 and "OK" in out:
                            python_exe = candidate
                            break

                    # Run probe script
                    escaped_script = _PROBE_SCRIPT.replace("'", "'\"'\"'")
                    code, out, err = run_ssh_cmd(f"{python_exe} -c '{escaped_script}'")
                    if code != 0:
                        raise ProbeError(
                            f"Probe script failed on target\n"
                            f"  Exit code: {code}\n"
                            f"  Error: {err.strip() if err else 'unknown'}"
                        )

                    try:
                        return json.loads(out)
                    except json.JSONDecodeError as e:
                        raise ProbeError(
                            f"Failed to parse probe output\n  Error: {e}\n  Output: {out[:200]}..."
                        ) from None

        except RunPodError as e:
            # RunPod API errors (provisioning, pod not found, etc.)
            raise ProbeError(f"RunPod error for target '{target.name}'\n  {e}") from None
        except OSError as e:
            # SSH connection errors
            if pod_state:
                raise ProbeError(
                    f"SSH connection failed to target '{target.name}'\n"
                    f"  Host: {pod_state.ssh_username}@{pod_state.public_ip}:{pod_state.ssh_port}\n"
                    f"  Error: {e}\n"
                    f"  Hint: Check if the pod is still running with 'wafer config targets pods'"
                ) from None
            raise ProbeError(
                f"SSH connection failed to target '{target.name}'\n"
                f"  Error: {e}\n"
                f"  Hint: No pod found. One will be provisioned on next probe attempt."
            ) from None

    elif isinstance(target, (BaremetalTarget, VMTarget)):
        import subprocess

        # Parse ssh_target (user@host:port or user@host)
        ssh_target = target.ssh_target
        if ":" in ssh_target.split("@")[-1]:
            host_port = ssh_target.split("@")[-1]
            host = host_port.rsplit(":", 1)[0]
            port = host_port.rsplit(":", 1)[1]
            user = ssh_target.split("@")[0]
            ssh_target = f"{user}@{host}"
        else:
            host = ssh_target.split("@")[-1]
            port = "22"
            user = ssh_target.split("@")[0]

        key_path = target.ssh_key

        def run_ssh_cmd(cmd: str) -> tuple[int, str, str]:
            try:
                result = subprocess.run(
                    [
                        "ssh",
                        "-o",
                        "StrictHostKeyChecking=no",
                        "-o",
                        "UserKnownHostsFile=/dev/null",
                        "-o",
                        "ConnectTimeout=30",
                        "-i",
                        str(key_path),
                        "-p",
                        port,
                        ssh_target,
                        cmd,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                return result.returncode, result.stdout, result.stderr
            except subprocess.TimeoutExpired:
                raise ProbeError(
                    f"SSH connection timed out\n"
                    f"  Host: {ssh_target}:{port}\n"
                    f"  Hint: Check if the host is reachable and SSH is running."
                ) from None

        # Test SSH connection first
        code, out, err = run_ssh_cmd("echo OK")
        if code != 0:
            raise ProbeError(
                f"SSH connection failed to target '{target.name}'\n"
                f"  Host: {user}@{host}:{port}\n"
                f"  Key: {key_path}\n"
                f"  Error: {err.strip() if err else 'connection refused or timeout'}\n"
                f"  Hint: Verify the host is reachable and the SSH key is authorized."
            )

        # Run probe script
        escaped_script = _PROBE_SCRIPT.replace("'", "'\"'\"'")
        code, out, err = run_ssh_cmd(f"python3 -c '{escaped_script}'")
        if code != 0:
            raise ProbeError(
                f"Probe script failed on target '{target.name}'\n"
                f"  Exit code: {code}\n"
                f"  Error: {err.strip() if err else 'unknown'}\n"
                f"  Hint: Ensure python3 is installed on the target."
            )

        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            raise ProbeError(
                f"Failed to parse probe output from '{target.name}'\n"
                f"  Error: {e}\n"
                f"  Output: {out[:200]}..."
            ) from None

    else:
        raise ProbeError(
            f"Probing not supported for target type: {type(target).__name__}\n"
            f"  Supported types: RunPod, Baremetal, VM"
        )
