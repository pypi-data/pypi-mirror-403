"""Workspaces CLI - Manage remote GPU workspaces.

This module provides the implementation for the `wafer workspaces` subcommand.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx

from .api_client import get_api_url
from .auth import get_auth_headers

VALID_STATUSES = {"creating", "running", "error"}


def _get_client() -> tuple[str, dict[str, str]]:
    """Get API URL and auth headers."""
    api_url = get_api_url()
    headers = get_auth_headers()

    assert api_url, "API URL must be configured"
    assert api_url.startswith("http"), "API URL must be a valid HTTP(S) URL"

    return api_url, headers


def _friendly_error(status_code: int, response_text: str, workspace_id: str) -> str:
    """Convert API errors to friendly messages with guidance.

    Args:
        status_code: HTTP status code
        response_text: Response body
        workspace_id: Workspace ID or name for context

    Returns:
        User-friendly error message with suggested next steps
    """
    if status_code == 401:
        return "Not authenticated. Run: wafer login"

    if status_code == 402:
        return (
            "Insufficient credits.\n"
            "  Check usage: wafer billing\n"
            "  Add credits: wafer billing topup"
        )

    if status_code == 404:
        return (
            f"Workspace '{workspace_id}' not found.\n"
            "  List workspaces: wafer workspaces list\n"
            "  Create one: wafer workspaces create <name>"
        )

    if status_code == 503:
        return (
            "No GPU available.\n"
            "  The workspace is queued for GPU access. Try again in a moment.\n"
            "  Check status: wafer workspaces show " + workspace_id
        )

    # Parse common error details from response
    detail = ""
    if "not running" in response_text.lower() or "not found" in response_text.lower():
        return (
            f"Workspace '{workspace_id}' not found or not running.\n"
            "  Check status: wafer workspaces list\n"
            "  Create new:   wafer workspaces create <name>"
        )

    if "timeout" in response_text.lower():
        return (
            "Command timed out.\n"
            '  Increase timeout: wafer workspaces exec <workspace> "cmd" --timeout 600\n'
            "  Or set default: wafer config set defaults.exec_timeout 600"
        )

    if "creating" in response_text.lower():
        return (
            f"Workspace '{workspace_id}' is still creating.\n"
            "  Check status: wafer workspaces list"
        )

    # Generic error with response detail
    try:
        import json

        data = json.loads(response_text)
        detail = data.get("detail", response_text)
    except (json.JSONDecodeError, KeyError):
        detail = response_text

    return f"API error ({status_code}): {detail}"


def _list_workspaces_raw() -> list[dict]:
    """List workspaces and return raw data (for internal use)."""
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/workspaces")
            response.raise_for_status()
            workspaces = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    assert isinstance(workspaces, list), "API must return a list of workspaces"
    
    for ws in workspaces:
        status = ws.get("status", "unknown")
        assert status in VALID_STATUSES or status == "unknown", (
            f"Workspace {ws.get('id', 'unknown')} has invalid status '{status}'. "
            f"Valid statuses: {VALID_STATUSES}"
        )
    
    return workspaces


def resolve_workspace(specified: str | None) -> str:
    """Resolve workspace ID from specified name/ID, config default, or single workspace.

    Priority:
    1. If specified, return it (API will resolve name vs ID)
    2. If config has defaults.workspace, return that
    3. If user has exactly one workspace, return its ID
    4. Otherwise, error with guidance

    Args:
        specified: Workspace name or ID, or None to use default

    Returns:
        Workspace name or ID to use

    Raises:
        RuntimeError: If no workspace can be resolved
    """
    from .global_config import get_defaults

    # If specified, use it (API resolves name vs ID)
    if specified:
        return specified

    # Check config default
    defaults = get_defaults()
    if defaults.workspace:
        return defaults.workspace

    # Check if user has exactly one workspace
    workspaces = _list_workspaces_raw()

    if len(workspaces) == 0:
        raise RuntimeError("No workspaces found. Create one with: wafer workspaces create <name>")

    if len(workspaces) == 1:
        return workspaces[0]["id"]

    # Multiple workspaces, no default - error with guidance
    names = [ws.get("name", ws["id"]) for ws in workspaces]
    raise RuntimeError(
        f"Multiple workspaces found: {', '.join(names)}\n"
        "Specify one, or set default: wafer config set defaults.workspace <name>"
    )


def list_workspaces(json_output: bool = False) -> str:
    """List all workspaces for the current user.

    Args:
        json_output: If True, return raw JSON; otherwise return formatted text

    Returns:
        Workspaces list as string (JSON or formatted text)
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/workspaces")
            response.raise_for_status()
            workspaces = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    assert isinstance(workspaces, list), "API must return a list of workspaces"

    for ws in workspaces:
        status = ws.get("status", "unknown")
        assert status in VALID_STATUSES or status == "unknown", (
            f"Workspace {ws.get('id', 'unknown')} has invalid status '{status}'. "
            f"Valid statuses: {VALID_STATUSES}"
        )

    if json_output:
        return json.dumps(workspaces, indent=2)

    if not workspaces:
        return "No workspaces found."

    lines = ["Workspaces:", ""]
    for ws in workspaces:
        status = ws.get("status", "unknown")
        status_icon = {"running": "●", "creating": "◐", "error": "✗"}.get(status, "?")
        lines.append(f"  {status_icon} {ws['name']} ({ws['id']})")
        lines.append(f"    GPU: {ws.get('gpu_type', 'N/A')} | Image: {ws.get('image', 'N/A')}")

        if status == "error":
            lines.append(
                f"    Status: Provisioning failed. Delete and recreate: wafer workspaces delete {ws['name']}"
            )
        elif ws.get("ssh_host") and ws.get("ssh_port") and ws.get("ssh_user"):
            ssh_line = f"    SSH: ssh -p {ws['ssh_port']} {ws['ssh_user']}@{ws['ssh_host']}"
            if status == "creating":
                ssh_line += " (finalizing...)"
            lines.append(ssh_line)
        elif status == "running":
            lines.append(
                f"    Status: Running but SSH not ready. Try: wafer workspaces delete {ws['name']} && wafer workspaces create {ws['name']} --wait"
            )
        else:
            lines.append("    SSH: Not ready (workspace is still creating)")
        lines.append("")

    # Add SSH tip for users with running workspaces
    has_running_with_ssh = any(
        ws.get("status") == "running" and ws.get("ssh_host")
        for ws in workspaces
    )
    if has_running_with_ssh:
        lines.append("Tip: SSH directly for interactive work. 'exec' is for quick commands only.")
    
    has_error = any(ws.get("status") == "error" for ws in workspaces)
    if has_error:
        lines.append("Note: Error workspaces are auto-cleaned after 12 hours.")

    return "\n".join(lines)


def create_workspace(
    name: str,
    gpu_type: str = "B200",
    image: str | None = None,
    wait: bool = False,
    json_output: bool = False,
) -> str:
    """Create a new workspace.

    Args:
        name: Workspace name (must be unique)
        gpu_type: GPU type (default: B200)
        image: Docker image (optional, uses default if not specified)
        wait: If True, stream provisioning progress and return SSH credentials
        json_output: If True, return raw JSON; otherwise return formatted text

    Returns:
        Created workspace info as string

    Raises:
        RuntimeError: If name already exists or API error
    """
    # Validate inputs
    assert name, "Workspace name must be non-empty"
    assert gpu_type, "GPU type must be non-empty"

    api_url, headers = _get_client()

    # Check for duplicate name
    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/workspaces")
            response.raise_for_status()
            existing = response.json()
            existing_names = [ws.get("name") for ws in existing]
            if name in existing_names:
                raise RuntimeError(
                    f"Workspace '{name}' already exists.\n"
                    f"  Use a different name, or delete the existing one:\n"
                    f"  wafer workspaces delete {name}"
                )
    except httpx.HTTPStatusError:
        pass  # Continue with create, let API handle auth errors
    except httpx.RequestError:
        pass  # Continue with create, let API handle connection errors

    request_body: dict = {
        "name": name,
        "gpu_type": gpu_type,
    }
    if image:
        request_body["image"] = image

    try:
        with httpx.Client(timeout=60.0, headers=headers) as client:
            response = client.post(f"{api_url}/v1/workspaces", json=request_body)
            response.raise_for_status()
            workspace = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 400:
            raise RuntimeError(f"Bad request: {e.response.text}") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    # Validate API response has required fields
    assert "id" in workspace, "API response must contain workspace id"
    assert "name" in workspace, "API response must contain workspace name"

    if wait:
        ssh_info = _wait_for_provisioning(workspace["id"])
        if json_output:
            payload = {
                "workspace_id": workspace["id"],
                "ssh_host": ssh_info["ssh_host"],
                "ssh_port": ssh_info["ssh_port"],
                "ssh_user": ssh_info["ssh_user"],
            }
            return json.dumps(payload, indent=2)
        return (
            f"Workspace ready: {workspace['name']} ({workspace['id']})\n"
            f"SSH: ssh -p {ssh_info['ssh_port']} {ssh_info['ssh_user']}@{ssh_info['ssh_host']}"
        )

    if json_output:
        return json.dumps(workspace, indent=2)

    return (
        f"Creating workspace: {workspace['name']} ({workspace['id']})\n"
        "Check status with: wafer workspaces list\n"
        "Estimated time: ~30 seconds"
    )


def _wait_for_provisioning(workspace_id: str) -> dict[str, str | int]:
    """Wait for workspace provisioning to complete via SSE."""
    import sys

    assert workspace_id, "Workspace ID must be non-empty"
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=None, headers=headers) as client:
            with client.stream(
                "POST",
                f"{api_url}/v1/workspaces/{workspace_id}/provision-stream",
            ) as response:
                if response.status_code != 200:
                    error_body = response.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        _friendly_error(response.status_code, error_body, workspace_id)
                    )

                ssh_info: dict[str, str | int] | None = None
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    content = line[6:]
                    if content.startswith("[STATUS:"):
                        status = content[8:-1]
                        print(f"[wafer] {status.lower()}...", file=sys.stderr)
                        if status == "ERROR":
                            raise RuntimeError(
                                "Workspace provisioning failed. Check status with: wafer workspaces list"
                            )
                    elif content.startswith("[SSH:"):
                        parts = content[5:-1].split(":")
                        if len(parts) != 3:
                            raise RuntimeError("Malformed SSH info in provisioning stream")
                        ssh_info = {
                            "ssh_host": parts[0],
                            "ssh_port": int(parts[1]),
                            "ssh_user": parts[2],
                        }
                        break

                if ssh_info is None:
                    raise RuntimeError("Provisioning did not return SSH credentials")
                return ssh_info
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e


def delete_workspace(workspace_id: str, json_output: bool = False) -> str:
    """Delete a workspace.

    Args:
        workspace_id: Workspace ID to delete
        json_output: If True, return raw JSON; otherwise return formatted text

    Returns:
        Deletion status as string
    """
    assert workspace_id, "Workspace ID must be non-empty"

    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.delete(f"{api_url}/v1/workspaces/{workspace_id}")
            response.raise_for_status()
            result = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 404:
            raise RuntimeError(f"Workspace not found: {workspace_id}") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps(result, indent=2)

    return f"Deleted workspace: {workspace_id}"


def sync_files(
    workspace_id: str,
    local_path: Path,
    on_progress: Callable[[str], None] | None = None,
) -> tuple[int, str | None]:
    """Sync local files or directories to workspace via rsync over SSH.

    After rsync completes, calls the API to sync files to Modal volume
    so they're available for exec commands.

    Args:
        workspace_id: Workspace ID or name
        local_path: Local file or directory to sync
        on_progress: Optional callback for progress messages

    Returns:
        Tuple of (file_count, warning_message). Warning is None on success.

    Raises:
        RuntimeError: If rsync fails
    """
    import subprocess

    def emit(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    assert workspace_id, "Workspace ID must be non-empty"
    assert local_path.exists(), f"Path not found: {local_path}"

    ws = get_workspace_raw(workspace_id)
    resolved_id = ws["id"]
    workspace_status = ws.get("status")
    assert workspace_status in VALID_STATUSES, (
        f"Workspace {workspace_id} has invalid status '{workspace_status}'. "
        f"Valid statuses: {VALID_STATUSES}"
    )
    if workspace_status == "error":
        raise RuntimeError(
            f"Workspace provisioning failed. Delete and recreate:\n"
            f"  wafer workspaces delete {workspace_id}\n"
            f"  wafer workspaces create {ws.get('name', workspace_id)} --wait"
        )
    if workspace_status != "running":
        raise RuntimeError(
            f"Workspace is {workspace_status}. Wait for it to be running before syncing."
        )
    ssh_host = ws.get("ssh_host")
    ssh_port = ws.get("ssh_port")
    ssh_user = ws.get("ssh_user")
    if not ssh_host or not ssh_port or not ssh_user:
        # Workspace is running but SSH credentials are missing - unusual state
        raise RuntimeError(
            f"Workspace is running but SSH not ready.\n"
            f"  Delete and recreate: wafer workspaces delete {workspace_id}\n"
            f"  Then: wafer workspaces create {ws.get('name', workspace_id)} --wait"
        )
    assert isinstance(ssh_port, int) and ssh_port > 0, "Workspace missing valid ssh_port"

    # Build rsync command
    # -a: archive mode (preserves permissions, etc.)
    # -v: verbose
    # -z: compress during transfer
    if local_path.is_dir():
        # Directory: sync contents (trailing slash)
        source = f"{local_path}/"
    else:
        # Single file: sync the file itself
        source = str(local_path)

    # Build SSH command for rsync
    # If key_path is None (BYOK model), SSH will use default key from ~/.ssh/
    ssh_opts = f"-p {ssh_port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    
    rsync_cmd = [
        "rsync",
        "-avz",
        "-e",
        f"ssh {ssh_opts}",
        source,
        f"{ssh_user}@{ssh_host}:/workspace/",
    ]

    try:
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"rsync failed: {result.stderr}")

        # Count files from rsync output (lines that don't start with special chars)
        lines = result.stdout.strip().split("\n")
        file_count = sum(
            1
            for line in lines
            if line and not line.startswith((" ", "sent", "total", "receiving", "building"))
        )

    except FileNotFoundError:
        raise RuntimeError("rsync not found. Install rsync to use sync feature.") from None
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Sync failed: {e}") from e

    emit(f"Synced {file_count} files to SSH host")

    # Notify API to sync files to Modal volume (so exec can see them)
    # Use resolved UUID, not the name
    emit("Syncing to Modal volume...")
    warning = _init_sync_state(resolved_id)

    if warning:
        emit(f"Modal sync warning: {warning}")
    else:
        emit("Modal sync complete")

    return file_count, warning


def pull_files(
    workspace_id: str,
    remote_path: str,
    local_path: Path,
    on_progress: Callable[[str], None] | None = None,
) -> int:
    """Pull files from workspace to local via rsync over SSH.

    Args:
        workspace_id: Workspace ID or name
        remote_path: Remote path in workspace (relative to /workspace or absolute)
        local_path: Local destination path
        on_progress: Optional callback for progress messages

    Returns:
        Number of files transferred

    Raises:
        RuntimeError: If rsync fails or workspace not accessible
    """
    import subprocess

    def emit(msg: str) -> None:
        if on_progress:
            on_progress(msg)

    assert workspace_id, "Workspace ID must be non-empty"

    ws = get_workspace_raw(workspace_id)
    workspace_status = ws.get("status")
    assert workspace_status in VALID_STATUSES, (
        f"Workspace {workspace_id} has invalid status '{workspace_status}'. "
        f"Valid statuses: {VALID_STATUSES}"
    )
    if workspace_status == "error":
        raise RuntimeError(
            f"Workspace provisioning failed. Delete and recreate:\n"
            f"  wafer workspaces delete {workspace_id}\n"
            f"  wafer workspaces create {ws.get('name', workspace_id)} --wait"
        )
    if workspace_status != "running":
        raise RuntimeError(
            f"Workspace is {workspace_status}. Wait for it to be running before pulling files."
        )
    ssh_host = ws.get("ssh_host")
    ssh_port = ws.get("ssh_port")
    ssh_user = ws.get("ssh_user")
    if not ssh_host or not ssh_port or not ssh_user:
        raise RuntimeError(
            f"Workspace is running but SSH not ready.\n"
            f"  Delete and recreate: wafer workspaces delete {workspace_id}\n"
            f"  Then: wafer workspaces create {ws.get('name', workspace_id)} --wait"
        )
    assert isinstance(ssh_port, int) and ssh_port > 0, "Workspace missing valid ssh_port"

    # Normalize remote path - if not absolute, assume relative to /workspace
    if not remote_path.startswith("/"):
        remote_path = f"/workspace/{remote_path}"

    # Build SSH command for rsync
    ssh_opts = f"-p {ssh_port} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

    # Build rsync command (reverse of sync - from remote to local)
    rsync_cmd = [
        "rsync",
        "-avz",
        "-e",
        f"ssh {ssh_opts}",
        f"{ssh_user}@{ssh_host}:{remote_path}",
        str(local_path),
    ]

    emit(f"Pulling {remote_path} from workspace...")

    try:
        result = subprocess.run(rsync_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"rsync failed: {result.stderr}")

        # Count files from rsync output
        lines = result.stdout.strip().split("\n")
        file_count = sum(
            1
            for line in lines
            if line and not line.startswith((" ", "sent", "total", "receiving", "building"))
        )

    except FileNotFoundError:
        raise RuntimeError("rsync not found. Install rsync to use pull feature.") from None
    except subprocess.SubprocessError as e:
        raise RuntimeError(f"Pull failed: {e}") from e

    emit(f"Pulled {file_count} files")
    return file_count


def _init_sync_state(workspace_id: str) -> str | None:
    """Tell API to sync files from bare metal to Modal volume.

    This must be called after rsync completes so exec commands
    can access the synced files.

    Returns:
        None on success, warning message on failure (non-fatal)
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=120.0, headers=headers) as client:
            response = client.post(f"{api_url}/v1/workspaces/{workspace_id}/init-sync-state")
            response.raise_for_status()
            return None
    except httpx.HTTPStatusError as e:
        # Non-fatal: sync to bare metal succeeded, Modal sync failed
        # User can still SSH in and use files, just not via exec
        if e.response.status_code == 404:
            # Workspace not found or no target - sync still worked for SSH
            return None
        else:
            # Extract error detail from response if available
            detail = ""
            try:
                data = e.response.json()
                detail = data.get("detail", "")
            except Exception:
                detail = e.response.text[:200] if e.response.text else ""

            # Return warning instead of raising - rsync succeeded
            if detail:
                return f"Files synced to SSH, but Modal sync failed: {detail}"
            return f"Files synced to SSH, but Modal sync failed ({e.response.status_code}). Use SSH or retry sync."
    except httpx.RequestError:
        # Network error - sync to bare metal succeeded
        return None


def get_workspace_raw(workspace_id: str) -> dict:
    """Get workspace details as raw JSON dict."""
    assert workspace_id, "Workspace ID must be non-empty"

    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/workspaces/{workspace_id}")
            response.raise_for_status()
            workspace = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 404:
            raise RuntimeError(f"Workspace not found: {workspace_id}") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    assert "id" in workspace, "API response must contain workspace id"
    assert "name" in workspace, "API response must contain workspace name"
    
    status = workspace.get("status", "unknown")
    assert status in VALID_STATUSES or status == "unknown", (
        f"Workspace {workspace['id']} has invalid status '{status}'. "
        f"Valid statuses: {VALID_STATUSES}"
    )
    
    return workspace


def get_workspace(workspace_id: str, json_output: bool = False) -> str:
    """Get details of a specific workspace.

    Args:
        workspace_id: Workspace ID to get
        json_output: If True, return raw JSON; otherwise return formatted text

    Returns:
        Workspace details as string
    """
    workspace = get_workspace_raw(workspace_id)

    if json_output:
        return json.dumps(workspace, indent=2)

    status = workspace.get("status", "unknown")
    lines = [
        f"Workspace: {workspace['name']} ({workspace['id']})",
        "",
        f"  Status: {status}",
        f"  GPU Type: {workspace.get('gpu_type', 'N/A')}",
        f"  Image: {workspace.get('image', 'N/A')}",
        f"  Created: {workspace.get('created_at', 'N/A')}",
        f"  Last Used: {workspace.get('last_used_at', 'N/A')}",
    ]

    if status == "error":
        lines.extend([
            "",
            "Provisioning failed. Delete and recreate:",
            f"  wafer workspaces delete {workspace['name']}",
            f"  wafer workspaces create {workspace['name']} --wait",
            "",
            "Note: Error workspaces are auto-cleaned after 12 hours.",
        ])
    elif workspace.get("ssh_host"):
        lines.extend([
            "",
            "SSH Info:",
            f"  Host: {workspace['ssh_host']}",
            f"  Port: {workspace.get('ssh_port', 22)}",
            f"  User: {workspace.get('ssh_user', 'root')}",
            "",
            "Tip: SSH directly for interactive work. 'exec' is for quick commands only.",
        ])
    elif status == "creating":
        lines.extend(["", "SSH: available once workspace is running"])
    elif status == "running":
        # Running but no SSH credentials - unusual state
        lines.extend([
            "",
            "Status: Running but SSH not ready.",
            f"  Delete and recreate: wafer workspaces delete {workspace['name']}",
        ])

    return "\n".join(lines)


def _handle_sync_event(sync_type: str) -> None:
    """Handle sync events and print status to stderr.

    Sync events:
    - FORWARD:START - Starting workspace → GPU sync
    - FORWARD:DONE:N - Synced N files to GPU
    - FORWARD:WARN:msg - Warning during forward sync
    - REVERSE:START - Starting GPU → workspace sync
    - REVERSE:DONE:N - Synced N artifacts back
    """
    import sys

    if sync_type == "FORWARD:START":
        print("[sync] Syncing workspace → GPU...", end="", file=sys.stderr, flush=True)
    elif sync_type.startswith("FORWARD:DONE:"):
        count = sync_type.split(":")[-1]
        print(f" done ({count} files)", file=sys.stderr)
    elif sync_type.startswith("FORWARD:WARN:"):
        msg = sync_type[13:]  # Remove "FORWARD:WARN:"
        print(f" warning: {msg}", file=sys.stderr)
    elif sync_type == "REVERSE:START":
        print("[sync] Syncing artifacts back...", end="", file=sys.stderr, flush=True)
    elif sync_type.startswith("REVERSE:DONE:"):
        count = sync_type.split(":")[-1]
        print(f" done ({count} files)", file=sys.stderr)


@dataclass(frozen=True)
class SSEEvent:
    """Parsed SSE event result."""

    output: str | None  # Content to print (None = no output)
    exit_code: int | None  # Exit code if stream should end (None = continue)
    is_error: bool  # Whether output goes to stderr
    sync_event: str | None = None  # Sync event type (e.g., "FORWARD:START")


def _parse_sse_content(content: str) -> SSEEvent:
    """Parse SSE content into structured event.

    Pure function: content in, event out. No side effects.
    """
    if content == "[DONE]":
        return SSEEvent(output=None, exit_code=0, is_error=False)

    if content.startswith("[EXIT:"):
        # Parse exit code: [EXIT:0] or [EXIT:1]
        try:
            code = int(content[6:-1])
        except ValueError:
            code = 0
        return SSEEvent(output=None, exit_code=code, is_error=False)

    if content.startswith("[ERROR]"):
        return SSEEvent(output=content[8:], exit_code=1, is_error=True)

    # Sync events: [SYNC:FORWARD:START], [SYNC:FORWARD:DONE:5], etc.
    if content.startswith("[SYNC:"):
        # Extract sync type (e.g., "FORWARD:START" or "REVERSE:DONE:5")
        sync_type = content[6:-1]  # Remove [SYNC: and ]
        return SSEEvent(output=None, exit_code=None, is_error=False, sync_event=sync_type)

    # Status events we can ignore (already handled elsewhere)
    if content.startswith("[STATUS:") or content.startswith("[CONTEXT:"):
        return SSEEvent(output=None, exit_code=None, is_error=False)

    # Regular output
    return SSEEvent(output=content, exit_code=None, is_error=False)


def exec_command(
    workspace_id: str,
    command: str,
    timeout_seconds: int | None = None,
    routing: str | None = None,
    pull_image: bool = False,
) -> int:
    """Execute a command in workspace, streaming output.

    Args:
        workspace_id: Workspace ID or name
        command: Command to execute
        timeout_seconds: Execution timeout (default: 300, from config)
        routing: Routing hint - "auto", "gpu", "cpu", or "baremetal" (default: auto)

    Returns:
        Exit code (0 = success, non-zero = failure)
    """
    import base64
    import sys

    assert workspace_id, "Workspace ID must be non-empty"
    assert command, "Command must be non-empty"

    api_url, headers = _get_client()

    # Base64 encode command to avoid escaping issues
    command_b64 = base64.b64encode(command.encode("utf-8")).decode("utf-8")

    request_body: dict = {"command_b64": command_b64, "pull_image": pull_image}
    if timeout_seconds:
        request_body["timeout_seconds"] = timeout_seconds

    # Add routing hint if specified
    if routing:
        request_body["requirements"] = {"routing": routing}

    try:
        # Use streaming request for SSE output
        with httpx.Client(timeout=None, headers=headers) as client:
            with client.stream(
                "POST",
                f"{api_url}/v1/workspaces/{workspace_id}/exec",
                json=request_body,
            ) as response:
                if response.status_code != 200:
                    # Read error body and provide friendly message
                    error_body = response.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        _friendly_error(response.status_code, error_body, workspace_id)
                    )

                exit_code = 0
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    event = _parse_sse_content(line[6:])

                    # Handle sync events - display status to stderr
                    if event.sync_event:
                        _handle_sync_event(event.sync_event)
                        continue

                    if event.output is not None:
                        print(event.output, file=sys.stderr if event.is_error else sys.stdout)

                    if event.exit_code is not None:
                        exit_code = event.exit_code
                        break

                return exit_code

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            _friendly_error(e.response.status_code, e.response.text, workspace_id)
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e


def exec_command_capture(
    workspace_id: str,
    command: str,
    timeout_seconds: int | None = None,
    routing: str | None = None,
    pull_image: bool = False,
) -> tuple[int, str]:
    """Execute a command in workspace and capture output.

    Similar to exec_command but returns output as string instead of printing.

    Args:
        workspace_id: Workspace ID or name
        command: Command to execute
        timeout_seconds: Execution timeout (default: 300)
        routing: Routing hint - "auto", "gpu", "cpu", or "baremetal"

    Returns:
        Tuple of (exit_code, output_string)
    """
    import base64

    assert workspace_id, "Workspace ID must be non-empty"
    assert command, "Command must be non-empty"

    api_url, headers = _get_client()

    # Base64 encode command to avoid escaping issues
    command_b64 = base64.b64encode(command.encode("utf-8")).decode("utf-8")

    request_body: dict = {"command_b64": command_b64, "pull_image": pull_image}
    if timeout_seconds:
        request_body["timeout_seconds"] = timeout_seconds

    if routing:
        request_body["requirements"] = {"routing": routing}

    output_lines: list[str] = []

    try:
        with httpx.Client(timeout=None, headers=headers) as client:
            with client.stream(
                "POST",
                f"{api_url}/v1/workspaces/{workspace_id}/exec",
                json=request_body,
            ) as response:
                if response.status_code != 200:
                    error_body = response.read().decode("utf-8", errors="replace")
                    raise RuntimeError(
                        _friendly_error(response.status_code, error_body, workspace_id)
                    )

                exit_code = 0
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    event = _parse_sse_content(line[6:])

                    # Skip sync events
                    if event.sync_event:
                        continue

                    if event.output is not None:
                        output_lines.append(event.output)

                    if event.exit_code is not None:
                        exit_code = event.exit_code
                        break

                return exit_code, "\n".join(output_lines)

    except httpx.HTTPStatusError as e:
        raise RuntimeError(
            _friendly_error(e.response.status_code, e.response.text, workspace_id)
        ) from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e
