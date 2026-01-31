"""SSH Keys CLI - Manage SSH public keys for workspace access.

This module provides the implementation for the `wafer ssh-keys` subcommand.
Users register their SSH public keys here, which are then installed in all
workspaces they attach to (BYOK - Bring Your Own Key model).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import httpx

from .api_client import get_api_url
from .auth import get_auth_headers


@dataclass(frozen=True)
class SshKey:
    """Registered SSH key info."""

    id: str
    public_key: str
    name: str | None
    created_at: str


def _get_client() -> tuple[str, dict[str, str]]:
    """Get API URL and auth headers."""
    api_url = get_api_url()
    headers = get_auth_headers()

    assert api_url, "API URL must be configured"
    assert api_url.startswith("http"), "API URL must be a valid HTTP(S) URL"

    return api_url, headers


def _get_key_fingerprint(public_key: str) -> str:
    """Extract a short fingerprint from a public key for display.

    Returns the first 12 characters of the base64 data portion.
    """
    parts = public_key.strip().split()
    if len(parts) >= 2:
        return parts[1][:12] + "..."
    return public_key[:12] + "..."


def _get_key_type(public_key: str) -> str:
    """Extract the key type from a public key."""
    parts = public_key.strip().split()
    if parts:
        return parts[0]
    return "unknown"


def _detect_ssh_keys() -> list[Path]:
    """Detect existing SSH public keys on disk.

    Returns list of paths to found public key files, in preference order.
    """
    ssh_dir = Path.home() / ".ssh"
    candidates = [
        "id_ed25519.pub",  # Preferred (modern, secure, fast)
        "id_rsa.pub",  # Legacy but common
        "id_ecdsa.pub",  # Less common
        "id_dsa.pub",  # Deprecated
    ]

    found = []
    for filename in candidates:
        key_path = ssh_dir / filename
        if key_path.exists():
            found.append(key_path)

    return found


def list_ssh_keys(json_output: bool = False) -> str:
    """List all registered SSH keys.

    Returns:
        Formatted output string
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/user/ssh-keys")
            response.raise_for_status()
            keys = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps(keys, indent=2)

    if not keys:
        return (
            "No SSH keys registered.\n"
            "\n"
            "Add your SSH key:\n"
            "  wafer ssh-keys add\n"
            "\n"
            "This will auto-detect your key from ~/.ssh/"
        )

    lines = ["SSH Keys:"]
    for key in keys:
        key_type = _get_key_type(key["public_key"])
        fingerprint = _get_key_fingerprint(key["public_key"])
        name = key.get("name") or "(no name)"
        lines.append(f"  • {name}: {key_type} {fingerprint}")
        lines.append(f"    ID: {key['id']}")

    return "\n".join(lines)


def add_ssh_key(
    pubkey_path: Path | None = None,
    name: str | None = None,
    json_output: bool = False,
) -> str:
    """Add an SSH public key.

    Args:
        pubkey_path: Path to public key file (auto-detects if None)
        name: Optional friendly name for the key
        json_output: Return JSON instead of formatted output

    Returns:
        Formatted output string
    """
    # Auto-detect if no path provided
    if pubkey_path is None:
        detected = _detect_ssh_keys()
        if not detected:
            raise RuntimeError(
                "No SSH key found in ~/.ssh/\n"
                "\n"
                "Generate one with:\n"
                "  ssh-keygen -t ed25519\n"
                "\n"
                "Or specify a path:\n"
                "  wafer ssh-keys add /path/to/key.pub"
            )
        pubkey_path = detected[0]

    # Validate path
    if not pubkey_path.exists():
        raise RuntimeError(f"File not found: {pubkey_path}")

    if not pubkey_path.suffix == ".pub" and "pub" not in pubkey_path.name:
        raise RuntimeError(
            f"Expected a public key file (.pub), got: {pubkey_path}\n"
            "\n"
            "Make sure you're adding the PUBLIC key, not the private key."
        )

    # Read key content
    try:
        public_key = pubkey_path.read_text().strip()
    except Exception as e:
        raise RuntimeError(f"Could not read key file: {e}") from e

    # Validate basic format
    if not public_key.startswith(("ssh-", "ecdsa-", "sk-")):
        raise RuntimeError(
            f"Invalid SSH public key format in {pubkey_path}\n"
            "\n"
            "Expected OpenSSH format (e.g., 'ssh-ed25519 AAAAC3... user@host')"
        )

    # Auto-generate name from key type and filename if not provided
    if name is None:
        key_type = _get_key_type(public_key)
        # Use key type without prefix (e.g., "ed25519" instead of "ssh-ed25519")
        short_type = key_type.replace("ssh-", "").replace("ecdsa-sha2-", "")
        name = short_type

    # Call API
    api_url, headers = _get_client()
    request_body = {
        "public_key": public_key,
        "name": name,
    }

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.post(
                f"{api_url}/v1/user/ssh-keys",
                json=request_body,
            )
            response.raise_for_status()
            key_data = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 400:
            # Parse error detail
            try:
                detail = e.response.json().get("detail", e.response.text)
            except Exception:
                detail = e.response.text
            raise RuntimeError(f"Invalid key: {detail}") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps(key_data, indent=2)

    key_type = _get_key_type(public_key)
    fingerprint = _get_key_fingerprint(public_key)

    return (
        f"✓ SSH key registered: {name}\n"
        f"  Type: {key_type}\n"
        f"  Fingerprint: {fingerprint}\n"
        f"  Source: {pubkey_path}\n"
        f"\n"
        f"Your key will be installed in all workspaces you attach to."
    )


def remove_ssh_key(key_id: str, json_output: bool = False) -> str:
    """Remove an SSH key.

    Args:
        key_id: UUID of the key to remove
        json_output: Return JSON instead of formatted output

    Returns:
        Formatted output string
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.delete(f"{api_url}/v1/user/ssh-keys/{key_id}")
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 404:
            raise RuntimeError(f"SSH key not found: {key_id}") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps({"status": "deleted", "key_id": key_id}, indent=2)

    return f"✓ SSH key removed: {key_id}"
