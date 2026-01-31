"""PostHog analytics for Wafer CLI.

Tracks CLI command usage and user activity for product analytics.
Mirrors the analytics implementation in apps/wevin-extension/src/services/analytics.ts.

Usage:
    from .analytics import track_command, identify_user, shutdown_analytics

    # Track a command execution
    track_command("evaluate", {"subcommand": "kernelbench", "outcome": "success"})

    # Identify user after login
    identify_user("user-id", "user@example.com")
"""

import atexit
import platform
import uuid
from pathlib import Path
from typing import Any

# PostHog configuration - same as wevin-extension
POSTHOG_API_KEY = "phc_9eDjkY72ud9o4l1mA1Gr1dnRT1yx71rP3XY9z66teFh"
POSTHOG_HOST = "https://us.i.posthog.com"

# Anonymous ID storage
ANONYMOUS_ID_FILE = Path.home() / ".wafer" / ".analytics_id"

# Global state
_posthog_client: Any = None
_distinct_id: str | None = None
_initialized: bool = False


def _get_anonymous_id() -> str:
    """Get or create anonymous ID for users who aren't logged in."""
    if ANONYMOUS_ID_FILE.exists():
        return ANONYMOUS_ID_FILE.read_text().strip()

    # Generate new anonymous ID
    anonymous_id = f"anon_{uuid.uuid4().hex}"
    ANONYMOUS_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    ANONYMOUS_ID_FILE.write_text(anonymous_id)
    return anonymous_id


def _get_user_id_from_credentials() -> tuple[str | None, str | None]:
    """Get user ID and email from stored credentials.

    Returns:
        Tuple of (user_id, email), both may be None if not logged in.
    """
    # Import here to avoid circular imports
    from .auth import load_credentials, verify_token

    creds = load_credentials()
    if not creds:
        return None, None

    # Try to get user info from token
    try:
        user_info = verify_token(creds.access_token)
        return user_info.user_id, user_info.email or creds.email
    except Exception:
        # Token verification failed, use email from credentials if available
        return None, creds.email


def _is_analytics_enabled() -> bool:
    """Check if analytics is enabled via preferences.

    Returns True by default, respects user preference in config.
    """
    from .global_config import get_preferences

    try:
        prefs = get_preferences()
        return getattr(prefs, "analytics_enabled", True)
    except Exception:
        # Default to enabled if we can't read preferences
        return True


def init_analytics() -> bool:
    """Initialize PostHog client.

    Returns:
        True if initialization succeeded, False otherwise.
    """
    global _posthog_client, _distinct_id, _initialized

    if _initialized:
        return _posthog_client is not None

    _initialized = True

    # Check if analytics is enabled
    if not _is_analytics_enabled():
        return False

    try:
        from posthog import Posthog

        _posthog_client = Posthog(
            api_key=POSTHOG_API_KEY,
            host=POSTHOG_HOST,
            # Flush immediately for CLI - commands are short-lived
            flush_at=1,
            flush_interval=1,
            # Disable debug logging
            debug=False,
        )

        # Set up distinct ID - prefer authenticated user, fall back to anonymous
        user_id, email = _get_user_id_from_credentials()
        if user_id:
            _distinct_id = user_id
            # Identify the user with their email
            if email:
                _posthog_client.identify(
                    distinct_id=user_id,
                    properties={
                        "email": email,
                        "auth_provider": "github",
                    },
                )
        else:
            _distinct_id = _get_anonymous_id()

        # Register shutdown handler to flush events
        atexit.register(shutdown_analytics)

        return True

    except ImportError:
        # PostHog not installed - analytics disabled
        return False
    except Exception:
        # Any other error - fail silently, don't break CLI
        return False


def shutdown_analytics() -> None:
    """Shutdown PostHog client and flush pending events."""
    global _posthog_client

    if _posthog_client is not None:
        try:
            _posthog_client.flush()
            _posthog_client.shutdown()
        except Exception:
            pass  # Fail silently on shutdown
        _posthog_client = None


def identify_user(user_id: str, email: str | None = None) -> None:
    """Identify a user after login.

    Args:
        user_id: Supabase user ID
        email: User's email address
    """
    global _distinct_id

    if not init_analytics():
        return

    if _posthog_client is None:
        return

    _distinct_id = user_id

    try:
        properties: dict[str, Any] = {"auth_provider": "github"}
        if email:
            properties["email"] = email

        _posthog_client.identify(
            distinct_id=user_id,
            properties=properties,
        )
        _posthog_client.flush()
    except Exception:
        pass  # Fail silently


def reset_user_identity() -> None:
    """Reset user identity after logout."""
    global _distinct_id

    _distinct_id = _get_anonymous_id()


def get_distinct_id() -> str:
    """Get current distinct ID for tracking."""
    global _distinct_id

    if _distinct_id is None:
        user_id, _ = _get_user_id_from_credentials()
        _distinct_id = user_id or _get_anonymous_id()

    return _distinct_id


def _get_cli_version() -> str:
    """Get CLI version from package metadata."""
    try:
        from importlib.metadata import version

        return version("wafer-cli")
    except Exception:
        return "unknown"


def _get_base_properties() -> dict[str, Any]:
    """Get base properties included with all events."""
    return {
        "platform": "cli",
        "tool_id": "cli",
        "cli_version": _get_cli_version(),
        "os": platform.system().lower(),
        "os_version": platform.release(),
        "python_version": platform.python_version(),
    }


def track_event(event_name: str, properties: dict[str, Any] | None = None) -> None:
    """Track a generic event.

    Args:
        event_name: Name of the event to track
        properties: Additional properties to include
    """
    if not init_analytics():
        return

    if _posthog_client is None:
        return

    try:
        event_properties = _get_base_properties()
        if properties:
            event_properties.update(properties)

        _posthog_client.capture(
            distinct_id=get_distinct_id(),
            event=event_name,
            properties=event_properties,
        )
    except Exception:
        pass  # Fail silently


def track_command(
    command: str,
    subcommand: str | None = None,
    outcome: str = "success",
    duration_ms: int | None = None,
    properties: dict[str, Any] | None = None,
) -> None:
    """Track a CLI command execution.

    This event counts towards DAU in the internal dashboard.

    Args:
        command: The main command name (e.g., "evaluate", "agent")
        subcommand: Optional subcommand (e.g., "kernelbench")
        outcome: "success" or "error"
        duration_ms: Command execution time in milliseconds
        properties: Additional properties to include
    """
    event_properties: dict[str, Any] = {
        "command": command,
        "outcome": outcome,
    }

    if subcommand:
        event_properties["subcommand"] = subcommand

    if duration_ms is not None:
        event_properties["duration_ms"] = duration_ms

    if properties:
        event_properties.update(properties)

    track_event("cli_command_executed", event_properties)


def track_login(user_id: str, email: str | None = None) -> None:
    """Track user login event.

    Args:
        user_id: Supabase user ID
        email: User's email address
    """
    # First identify the user
    identify_user(user_id, email)

    # Then track the login event
    track_event("cli_user_signed_in", {"user_id": user_id})


def track_logout() -> None:
    """Track user logout event."""
    track_event("cli_user_signed_out")
    reset_user_identity()
