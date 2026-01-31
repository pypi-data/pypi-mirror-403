"""CLI authentication and credential management.

Handles storing/loading credentials from ~/.wafer/credentials.json
and verifying tokens against the wafer-api.

Supports automatic token refresh using Supabase refresh tokens.
"""

import json
import socket
import sys
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

from .global_config import get_api_url, get_supabase_url


def _safe_symbol(unicode_sym: str, ascii_fallback: str) -> str:
    """Return unicode symbol if terminal supports it, otherwise ASCII fallback."""
    # Check if stdout can handle UTF-8
    if not sys.stdout.isatty():
        return ascii_fallback
    try:
        encoding = sys.stdout.encoding or "ascii"
        unicode_sym.encode(encoding)
        return unicode_sym
    except (UnicodeEncodeError, LookupError):
        return ascii_fallback


# Safe symbols for terminal output
CHECK = _safe_symbol("✓", "[OK]")
CROSS = _safe_symbol("✗", "[FAIL]")

CREDENTIALS_DIR = Path.home() / ".wafer"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"


@dataclass
class Credentials:
    """Stored credentials."""

    access_token: str
    refresh_token: str | None = None
    email: str | None = None


@dataclass
class UserInfo:
    """User info from token verification."""

    user_id: str
    email: str | None


def save_credentials(
    access_token: str,
    refresh_token: str | None = None,
    email: str | None = None,
) -> None:
    """Save credentials to ~/.wafer/credentials.json."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    data = {"access_token": access_token}
    if refresh_token:
        data["refresh_token"] = refresh_token
    if email:
        data["email"] = email
    CREDENTIALS_FILE.write_text(json.dumps(data, indent=2))
    # Set restrictive permissions (owner read/write only)
    CREDENTIALS_FILE.chmod(0o600)


def load_credentials() -> Credentials | None:
    """Load credentials from ~/.wafer/credentials.json.

    Returns None if file doesn't exist or is invalid.
    """
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        data = json.loads(CREDENTIALS_FILE.read_text())
        return Credentials(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            email=data.get("email"),
        )
    except (json.JSONDecodeError, KeyError):
        return None


def clear_credentials() -> bool:
    """Remove credentials file.

    Returns True if file was removed, False if it didn't exist.
    """
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()
        return True
    return False


def get_auth_headers() -> dict[str, str]:
    """Get Authorization headers with a valid token.

    Automatically refreshes expired tokens if a refresh token is available.

    Returns empty dict if not logged in or refresh fails.
    """
    token = get_valid_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def verify_token(token: str) -> UserInfo:
    """Verify token with wafer-api and return user info.

    Raises:
        httpx.HTTPStatusError: If token is invalid (401) or other HTTP error
        httpx.RequestError: If API is unreachable
    """
    api_url = get_api_url()
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{api_url}/v1/auth/verify",
            json={"token": token},
        )
        response.raise_for_status()
        data = response.json()
        return UserInfo(
            user_id=data["user_id"],
            email=data.get("email"),
        )


def refresh_access_token(refresh_token: str) -> tuple[str, str]:
    """Use refresh token to get a new access token from Supabase.

    Args:
        refresh_token: The refresh token from previous auth

    Returns:
        Tuple of (new_access_token, new_refresh_token)

    Raises:
        httpx.HTTPStatusError: If refresh fails (e.g., refresh token expired)
        httpx.RequestError: If Supabase is unreachable
    """
    from .global_config import get_supabase_anon_key

    supabase_url = get_supabase_url()
    anon_key = get_supabase_anon_key()
    with httpx.Client(timeout=10.0) as client:
        response = client.post(
            f"{supabase_url}/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
            headers={
                "Content-Type": "application/json",
                "apikey": anon_key,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["access_token"], data["refresh_token"]


def get_valid_token() -> str | None:
    """Get a valid access token, refreshing if necessary.

    Attempts to verify the current token. If it's expired and we have a
    refresh token, automatically refreshes and saves the new tokens.

    Returns:
        Valid access token, or None if not logged in or refresh failed
    """
    creds = load_credentials()
    if not creds:
        return None

    # Try current token
    try:
        verify_token(creds.access_token)
        return creds.access_token
    except httpx.HTTPStatusError as e:
        if e.response.status_code != 401:
            # Not an auth error, re-raise
            raise
    except httpx.RequestError:
        # Network error (timeout, connection refused, DNS failure, etc.)
        # Cannot verify token - return None to trigger re-login prompt
        return None

    # Token expired, try refresh
    if not creds.refresh_token:
        return None

    try:
        new_access, new_refresh = refresh_access_token(creds.refresh_token)
        save_credentials(new_access, new_refresh, creds.email)
        return new_access
    except httpx.HTTPStatusError:
        # Refresh failed, need to re-login
        return None
    except httpx.RequestError:
        # Network error during refresh - return None to trigger re-login prompt
        return None


def _find_free_port() -> int:
    """Find a free port for the callback server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that catches the OAuth callback with access token."""

    access_token: str | None = None
    refresh_token: str | None = None
    error: str | None = None

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET request - catch the callback or serve the HTML page."""
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            # This is the redirect from Supabase with hash fragment
            # But hash fragments aren't sent to server, so serve a page that extracts it
            html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Wafer CLI Login</title></head>
<body>
<h2>Completing login...</h2>
<script>
// Extract tokens from hash fragment
const hash = window.location.hash.substring(1);
const params = new URLSearchParams(hash);
const accessToken = params.get('access_token');
const refreshToken = params.get('refresh_token');
const error = params.get('error_description') || params.get('error');

if (accessToken) {
    // Send both tokens to our local server
    let url = '/token?access_token=' + encodeURIComponent(accessToken);
    if (refreshToken) {
        url += '&refresh_token=' + encodeURIComponent(refreshToken);
    }
    fetch(url)
        .then(() => {
            document.body.innerHTML = '<h2>✓ Login successful!</h2><p>You can close this window.</p>';
        });
} else if (error) {
    fetch('/token?error=' + encodeURIComponent(error));
    document.body.innerHTML = '<h2>✗ Login failed</h2><p>' + error + '</p>';
} else {
    document.body.innerHTML = '<h2>✗ No token received</h2>';
}
</script>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())

        elif parsed.path == "/token":
            # JavaScript sends us the tokens
            params = parse_qs(parsed.query)
            if "access_token" in params:
                OAuthCallbackHandler.access_token = params["access_token"][0]
                if "refresh_token" in params:
                    OAuthCallbackHandler.refresh_token = params["refresh_token"][0]
            elif "error" in params:
                OAuthCallbackHandler.error = params["error"][0]

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()


def browser_login(timeout: int = 120, port: int | None = None) -> tuple[str, str | None]:
    """Open browser for GitHub OAuth and return tokens.

    Starts a local HTTP server, opens browser to Supabase OAuth,
    and waits for the callback with the tokens.

    Args:
        timeout: Seconds to wait for callback (default 120)
        port: Port for callback server. If None, finds a free port (default None)

    Returns:
        Tuple of (access_token, refresh_token). refresh_token may be None.

    Raises:
        TimeoutError: If no callback received within timeout
        RuntimeError: If OAuth flow failed
    """
    if port is None:
        port = _find_free_port()
    redirect_uri = f"http://localhost:{port}/callback"
    supabase_url = get_supabase_url()

    # Build OAuth URL
    auth_url = f"{supabase_url}/auth/v1/authorize?provider=github&redirect_to={redirect_uri}"

    # Reset state
    OAuthCallbackHandler.access_token = None
    OAuthCallbackHandler.refresh_token = None
    OAuthCallbackHandler.error = None

    # Start local server
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.timeout = 1  # Check for token every second

    # Open browser
    print("Opening browser for GitHub authentication...")
    print(f"If browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback
    start = time.time()
    print("Waiting for authentication...", end="", flush=True)

    while time.time() - start < timeout:
        server.handle_request()

        if OAuthCallbackHandler.access_token:
            print(f" {CHECK}")
            server.server_close()
            return OAuthCallbackHandler.access_token, OAuthCallbackHandler.refresh_token

        if OAuthCallbackHandler.error:
            print(f" {CROSS}")
            server.server_close()
            raise RuntimeError(f"OAuth failed: {OAuthCallbackHandler.error}")

    server.server_close()
    raise TimeoutError(f"No response within {timeout} seconds")


def device_code_login(timeout: int = 600) -> tuple[str, str | None]:
    """Authenticate using state-based flow (no browser/port forwarding needed).

    This is the SSH-friendly auth flow similar to GitHub CLI:
    1. Request a state token from the API
    2. Display the auth URL with state parameter
    3. User visits URL on any device and signs in normally
    4. Poll API until user completes authentication

    Args:
        timeout: Seconds to wait for authentication (default 600 = 10 minutes)

    Returns:
        Tuple of (access_token, refresh_token). refresh_token may be None.

    Raises:
        TimeoutError: If user doesn't authenticate within timeout
        RuntimeError: If auth flow failed
    """
    api_url = get_api_url()

    # Request state and auth URL
    with httpx.Client(timeout=10.0) as client:
        response = client.post(f"{api_url}/v1/auth/cli-auth/start", json={})
        response.raise_for_status()
        data = response.json()

    state = data["state"]
    auth_url = data["auth_url"]
    expires_in = data["expires_in"]

    # Display instructions to user
    print("\n" + "=" * 60)
    print("  WAFER CLI - Authentication")
    print("=" * 60)
    print(f"\n  Visit: {auth_url}")
    print("\n  Sign in with GitHub to complete authentication")
    print("\n" + "=" * 60 + "\n")

    # Poll for authentication
    start = time.time()
    poll_interval = 5  # Poll every 5 seconds
    last_poll = 0.0

    print("Waiting for authentication", end="", flush=True)

    while time.time() - start < min(timeout, expires_in):
        # Show progress dots
        if time.time() - last_poll >= poll_interval:
            print(".", end="", flush=True)

            # Poll the API
            with httpx.Client(timeout=10.0) as client:
                try:
                    response = client.post(f"{api_url}/v1/auth/cli-auth/token", json={"state": state})

                    if response.status_code == 200:
                        # Success!
                        data = response.json()
                        print(f" {CHECK}\n")
                        return data["access_token"], data.get("refresh_token")

                    if response.status_code == 428:
                        # Still waiting
                        last_poll = time.time()
                        time.sleep(1)
                        continue

                    # Some other error
                    print(f" {CROSS}\n")
                    raise RuntimeError(f"CLI auth flow failed: {response.status_code} {response.text}")

                except httpx.RequestError:
                    # Network error, retry
                    print("!", end="", flush=True)
                    last_poll = time.time()
                    time.sleep(1)
                    continue

        time.sleep(0.5)  # Small sleep to avoid busy loop

    print(f" {CROSS}\n")
    raise TimeoutError(f"Authentication not completed within {expires_in} seconds")
