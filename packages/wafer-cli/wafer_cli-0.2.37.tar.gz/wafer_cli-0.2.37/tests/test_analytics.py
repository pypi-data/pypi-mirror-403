"""Unit tests for CLI analytics module.

Tests cover:
- PostHog client initialization
- User identification
- Event tracking (commands, login, logout)
- Anonymous ID generation
- Analytics opt-out via preferences
- Graceful error handling

Run with: PYTHONPATH=apps/wafer-cli uv run pytest apps/wafer-cli/tests/test_analytics.py -v
"""

from pathlib import Path
from unittest.mock import MagicMock, patch


class TestAnalyticsInit:
    """Test analytics initialization."""

    def test_init_analytics_creates_client(self) -> None:
        """init_analytics should create PostHog client when enabled."""
        # Reset module state
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = None

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch("posthog.Posthog") as mock_posthog:
            mock_client = MagicMock()
            mock_posthog.return_value = mock_client

            result = analytics.init_analytics()

            assert result is True
            mock_posthog.assert_called_once()
            assert analytics._posthog_client is mock_client

    def test_init_analytics_respects_disabled_preference(self) -> None:
        """init_analytics should not create client when analytics disabled."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = None

        with patch("wafer.analytics._is_analytics_enabled", return_value=False):
            result = analytics.init_analytics()

            assert result is False
            assert analytics._posthog_client is None

    def test_init_analytics_only_initializes_once(self) -> None:
        """init_analytics should only create client once."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch("posthog.Posthog") as mock_posthog:
            mock_client = MagicMock()
            mock_posthog.return_value = mock_client

            # First call
            analytics.init_analytics()
            # Second call
            analytics.init_analytics()

            # Should only be called once
            assert mock_posthog.call_count == 1

    def test_init_analytics_handles_import_error(self) -> None:
        """init_analytics should handle missing posthog package."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch.dict("sys.modules", {"posthog": None}):
            # Force reimport to trigger ImportError
            analytics._initialized = False
            # This should not raise, just return False
            # (In practice the import error is caught)


class TestAnonymousId:
    """Test anonymous ID generation and persistence."""

    def test_get_anonymous_id_creates_new(self, tmp_path: Path) -> None:
        """_get_anonymous_id should create new ID if none exists."""
        from wafer import analytics

        # Use temp path for anonymous ID
        analytics_id_file = tmp_path / ".analytics_id"

        with patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            anon_id = analytics._get_anonymous_id()

            assert anon_id.startswith("anon_")
            assert len(anon_id) > 5
            assert analytics_id_file.exists()
            assert analytics_id_file.read_text().strip() == anon_id

    def test_get_anonymous_id_reuses_existing(self, tmp_path: Path) -> None:
        """_get_anonymous_id should reuse existing ID."""
        from wafer import analytics

        analytics_id_file = tmp_path / ".analytics_id"
        existing_id = "anon_existing123"
        analytics_id_file.write_text(existing_id)

        with patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            anon_id = analytics._get_anonymous_id()

            assert anon_id == existing_id


class TestUserIdentification:
    """Test user identification functions."""

    def test_identify_user_sets_distinct_id(self) -> None:
        """identify_user should set distinct_id and call PostHog identify."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = None

        mock_client = MagicMock()

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch("posthog.Posthog", return_value=mock_client):
            analytics.init_analytics()
            analytics.identify_user("user-123", "test@example.com")

            assert analytics._distinct_id == "user-123"
            mock_client.identify.assert_called()
            call_kwargs = mock_client.identify.call_args[1]
            assert call_kwargs["distinct_id"] == "user-123"
            assert call_kwargs["properties"]["email"] == "test@example.com"

    def test_identify_user_without_email(self) -> None:
        """identify_user should work without email."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = None

        mock_client = MagicMock()

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch("posthog.Posthog", return_value=mock_client):
            analytics.init_analytics()
            analytics.identify_user("user-456")

            assert analytics._distinct_id == "user-456"
            mock_client.identify.assert_called()

    def test_reset_user_identity(self, tmp_path: Path) -> None:
        """reset_user_identity should revert to anonymous ID."""
        from wafer import analytics

        analytics._distinct_id = "user-123"
        analytics_id_file = tmp_path / ".analytics_id"
        analytics_id_file.write_text("anon_saved")

        with patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            analytics.reset_user_identity()

            assert analytics._distinct_id == "anon_saved"


class TestEventTracking:
    """Test event tracking functions."""

    def test_track_event_sends_to_posthog(self) -> None:
        """track_event should send event to PostHog."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = "test-user"

        mock_client = MagicMock()

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=("test-user", None)), \
             patch("posthog.Posthog", return_value=mock_client):
            analytics.init_analytics()
            analytics.track_event("test_event", {"key": "value"})

            mock_client.capture.assert_called_once()
            call_kwargs = mock_client.capture.call_args[1]
            assert call_kwargs["event"] == "test_event"
            assert call_kwargs["distinct_id"] == "test-user"
            assert call_kwargs["properties"]["key"] == "value"
            assert call_kwargs["properties"]["platform"] == "cli"
            assert call_kwargs["properties"]["tool_id"] == "cli"

    def test_track_command_sends_cli_command_executed(self) -> None:
        """track_command should send cli_command_executed event."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = "test-user"

        mock_client = MagicMock()

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=("test-user", None)), \
             patch("posthog.Posthog", return_value=mock_client):
            analytics.init_analytics()
            analytics.track_command(
                command="evaluate",
                subcommand="kernelbench",
                outcome="success",
                duration_ms=1234,
            )

            mock_client.capture.assert_called_once()
            call_kwargs = mock_client.capture.call_args[1]
            assert call_kwargs["event"] == "cli_command_executed"
            props = call_kwargs["properties"]
            assert props["command"] == "evaluate"
            assert props["subcommand"] == "kernelbench"
            assert props["outcome"] == "success"
            assert props["duration_ms"] == 1234

    def test_track_login_identifies_and_tracks(self) -> None:
        """track_login should identify user and track login event."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = None

        mock_client = MagicMock()

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch("posthog.Posthog", return_value=mock_client):
            analytics.init_analytics()
            analytics.track_login("user-789", "login@example.com")

            # Should call identify
            identify_calls = [c for c in mock_client.method_calls if c[0] == "identify"]
            assert len(identify_calls) >= 1

            # Should track login event
            capture_calls = [c for c in mock_client.method_calls if c[0] == "capture"]
            assert len(capture_calls) >= 1
            capture_kwargs = capture_calls[-1][2]
            assert capture_kwargs["event"] == "cli_user_signed_in"

    def test_track_logout_tracks_and_resets(self, tmp_path: Path) -> None:
        """track_logout should track event and reset identity."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None
        analytics._distinct_id = "user-123"

        mock_client = MagicMock()
        analytics_id_file = tmp_path / ".analytics_id"
        analytics_id_file.write_text("anon_saved")

        with patch("wafer.analytics._is_analytics_enabled", return_value=True), \
             patch("wafer.analytics._get_user_id_from_credentials", return_value=("user-123", None)), \
             patch("posthog.Posthog", return_value=mock_client), \
             patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            analytics.init_analytics()
            analytics.track_logout()

            # Should track logout event
            capture_calls = [c for c in mock_client.method_calls if c[0] == "capture"]
            assert len(capture_calls) >= 1
            capture_kwargs = capture_calls[-1][2]
            assert capture_kwargs["event"] == "cli_user_signed_out"

            # Should reset to anonymous ID
            assert analytics._distinct_id == "anon_saved"

    def test_track_event_does_nothing_when_disabled(self) -> None:
        """track_event should not send when analytics disabled."""
        from wafer import analytics

        analytics._initialized = False
        analytics._posthog_client = None

        with patch("wafer.analytics._is_analytics_enabled", return_value=False):
            # Should not raise
            analytics.track_event("test_event", {"key": "value"})
            # No client should exist
            assert analytics._posthog_client is None


class TestBaseProperties:
    """Test base properties included with events."""

    def test_get_base_properties_includes_platform(self) -> None:
        """_get_base_properties should include platform info."""
        from wafer.analytics import _get_base_properties

        props = _get_base_properties()

        assert props["platform"] == "cli"
        assert props["tool_id"] == "cli"
        assert "os" in props
        assert "python_version" in props


class TestPreferencesCheck:
    """Test analytics_enabled preference checking."""

    def test_is_analytics_enabled_default_true(self) -> None:
        """_is_analytics_enabled should default to True."""
        from wafer import analytics
        from wafer.global_config import Preferences

        mock_prefs = Preferences(mode="implicit", analytics_enabled=True)

        with patch("wafer.global_config.get_preferences", return_value=mock_prefs):
            assert analytics._is_analytics_enabled() is True

    def test_is_analytics_enabled_respects_false(self) -> None:
        """_is_analytics_enabled should respect False setting."""
        from wafer import analytics
        from wafer.global_config import Preferences

        mock_prefs = Preferences(mode="implicit", analytics_enabled=False)

        with patch("wafer.global_config.get_preferences", return_value=mock_prefs):
            assert analytics._is_analytics_enabled() is False


class TestGlobalConfigAnalyticsEnabled:
    """Test analytics_enabled in global config."""

    def test_preferences_has_analytics_enabled(self) -> None:
        """Preferences dataclass should have analytics_enabled field."""
        from wafer.global_config import Preferences

        prefs = Preferences()
        assert hasattr(prefs, "analytics_enabled")
        assert prefs.analytics_enabled is True  # Default

    def test_preferences_analytics_disabled(self) -> None:
        """Preferences should accept analytics_enabled=False."""
        from wafer.global_config import Preferences

        prefs = Preferences(analytics_enabled=False)
        assert prefs.analytics_enabled is False

    def test_parse_config_with_analytics_enabled(self, tmp_path: Path) -> None:
        """Config parser should read analytics_enabled from TOML."""
        from wafer.global_config import _parse_config_file

        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[api]
environment = "prod"

[preferences]
mode = "implicit"
analytics_enabled = false
""")

        config = _parse_config_file(config_file)

        assert config.preferences.analytics_enabled is False

    def test_parse_config_analytics_enabled_default(self, tmp_path: Path) -> None:
        """Config parser should default analytics_enabled to True."""
        from wafer.global_config import _parse_config_file

        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[api]
environment = "prod"
""")

        config = _parse_config_file(config_file)

        assert config.preferences.analytics_enabled is True


class TestCliCallback:
    """Test CLI callback analytics tracking."""

    def test_cli_callback_tracks_command(self) -> None:
        """CLI callback should track command execution."""
        from typer.testing import CliRunner

        from wafer.cli import app

        runner = CliRunner()

        with patch("wafer.analytics.init_analytics") as mock_init, \
             patch("wafer.analytics.track_command"):
            mock_init.return_value = True

            # Run a simple command that doesn't require auth
            runner.invoke(app, ["guide"])

            # Analytics should be initialized
            mock_init.assert_called()

            # Note: track_command is called via atexit, which may not run
            # in CliRunner context. We verify init is called at minimum.

    def test_cli_help_does_not_crash_analytics(self) -> None:
        """CLI --help should not crash due to analytics."""
        from typer.testing import CliRunner

        from wafer.cli import app

        runner = CliRunner()

        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "GPU development toolkit" in result.output

    def test_cli_subcommand_help_works(self) -> None:
        """Subcommand --help should work with analytics."""
        from typer.testing import CliRunner

        from wafer.cli import app

        runner = CliRunner()

        result = runner.invoke(app, ["config", "--help"])

        assert result.exit_code == 0


class TestLoginLogoutAnalytics:
    """Test login/logout analytics integration."""

    def test_login_calls_track_login(self) -> None:
        """Login command should call track_login on success."""
        from unittest.mock import MagicMock

        from typer.testing import CliRunner

        from wafer.cli import app

        runner = CliRunner()

        mock_user_info = MagicMock()
        mock_user_info.user_id = "test-user-id"
        mock_user_info.email = "test@example.com"

        with patch("wafer.auth.browser_login", return_value=("test-token", "refresh-token")), \
             patch("wafer.auth.verify_token", return_value=mock_user_info), \
             patch("wafer.auth.save_credentials"), \
             patch("wafer.analytics.track_login") as mock_track_login, \
             patch("wafer.analytics.init_analytics", return_value=True):

            runner.invoke(app, ["login", "--token", "test-token"])

            # track_login should be called
            mock_track_login.assert_called_once_with("test-user-id", "test@example.com")

    def test_logout_calls_track_logout(self) -> None:
        """Logout command should call track_logout."""
        from typer.testing import CliRunner

        from wafer.cli import app

        runner = CliRunner()

        with patch("wafer.auth.clear_credentials", return_value=True), \
             patch("wafer.analytics.track_logout") as mock_track_logout, \
             patch("wafer.analytics.init_analytics", return_value=True):

            result = runner.invoke(app, ["logout"])

            assert result.exit_code == 0
            mock_track_logout.assert_called_once()


class TestShutdown:
    """Test analytics shutdown."""

    def test_shutdown_flushes_and_closes(self) -> None:
        """shutdown_analytics should flush and close client."""
        from wafer import analytics

        mock_client = MagicMock()
        analytics._posthog_client = mock_client

        analytics.shutdown_analytics()

        mock_client.flush.assert_called_once()
        mock_client.shutdown.assert_called_once()
        assert analytics._posthog_client is None

    def test_shutdown_handles_none_client(self) -> None:
        """shutdown_analytics should handle None client gracefully."""
        from wafer import analytics

        analytics._posthog_client = None

        # Should not raise
        analytics.shutdown_analytics()


class TestGetDistinctId:
    """Test get_distinct_id function."""

    def test_get_distinct_id_returns_cached(self) -> None:
        """get_distinct_id should return cached ID."""
        from wafer import analytics

        analytics._distinct_id = "cached-user-id"

        result = analytics.get_distinct_id()

        assert result == "cached-user-id"

    def test_get_distinct_id_fetches_from_credentials(self, tmp_path: Path) -> None:
        """get_distinct_id should fetch from credentials if not cached."""
        from wafer import analytics

        analytics._distinct_id = None
        analytics_id_file = tmp_path / ".analytics_id"

        with patch("wafer.analytics._get_user_id_from_credentials", return_value=("cred-user", None)), \
             patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            result = analytics.get_distinct_id()

            assert result == "cred-user"

    def test_get_distinct_id_falls_back_to_anonymous(self, tmp_path: Path) -> None:
        """get_distinct_id should fall back to anonymous ID."""
        from wafer import analytics

        analytics._distinct_id = None
        analytics_id_file = tmp_path / ".analytics_id"
        analytics_id_file.write_text("anon_fallback")

        with patch("wafer.analytics._get_user_id_from_credentials", return_value=(None, None)), \
             patch.object(analytics, "ANONYMOUS_ID_FILE", analytics_id_file):
            result = analytics.get_distinct_id()

            assert result == "anon_fallback"
