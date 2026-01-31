"""Tests for billing commands.

Tests the wafer billing, wafer billing topup, and wafer billing portal commands.

Run with: PYTHONPATH=. uv run pytest tests/test_billing.py -v
"""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest
from typer.testing import CliRunner

from wafer.cli import app

runner = CliRunner()


# =============================================================================
# Unit Tests for Business Logic
# =============================================================================


class TestFormatCents:
    """Test the format_cents helper function."""

    def test_format_2500_cents(self) -> None:
        """2500 cents formats to $25.00."""
        from wafer.billing import format_cents

        assert format_cents(2500) == "$25.00"

    def test_format_0_cents(self) -> None:
        """0 cents formats to $0.00."""
        from wafer.billing import format_cents

        assert format_cents(0) == "$0.00"

    def test_format_99_cents(self) -> None:
        """99 cents formats to $0.99."""
        from wafer.billing import format_cents

        assert format_cents(99) == "$0.99"

    def test_format_10000_cents(self) -> None:
        """10000 cents formats to $100.00."""
        from wafer.billing import format_cents

        assert format_cents(10000) == "$100.00"

    def test_format_150_cents(self) -> None:
        """150 cents formats to $1.50."""
        from wafer.billing import format_cents

        assert format_cents(150) == "$1.50"


class TestValidateTopupAmount:
    """Test the validate_topup_amount helper function."""

    def test_valid_minimum_amount(self) -> None:
        """$10 (1000 cents) should be valid."""
        from wafer.billing import validate_topup_amount

        # Should not raise
        validate_topup_amount(1000)

    def test_valid_maximum_amount(self) -> None:
        """$500 (50000 cents) should be valid."""
        from wafer.billing import validate_topup_amount

        # Should not raise
        validate_topup_amount(50000)

    def test_valid_middle_amount(self) -> None:
        """$25 (2500 cents) should be valid."""
        from wafer.billing import validate_topup_amount

        # Should not raise
        validate_topup_amount(2500)

    def test_amount_below_minimum(self) -> None:
        """$9 (900 cents) should raise ValueError."""
        from wafer.billing import validate_topup_amount

        with pytest.raises(ValueError, match="at least"):
            validate_topup_amount(900)

    def test_amount_above_maximum(self) -> None:
        """$501 (50100 cents) should raise ValueError."""
        from wafer.billing import validate_topup_amount

        with pytest.raises(ValueError, match="at most"):
            validate_topup_amount(50100)

    def test_amount_zero(self) -> None:
        """0 cents should raise ValueError."""
        from wafer.billing import validate_topup_amount

        with pytest.raises(ValueError, match="at least"):
            validate_topup_amount(0)


class TestFormatUsageText:
    """Test the format_usage_text helper function."""

    def test_pro_tier_active(self) -> None:
        """Format pro tier with active status."""
        from wafer.billing import format_usage_text

        usage = {
            "tier": "pro",
            "status": "active",
            "credits_used_cents": 5000,
            "credits_limit_cents": 10000,
            "credits_remaining_cents": 5000,
            "topup_balance_cents": 2000,
            "has_hardware_counters": True,
            "has_slack_access": True,
            "period_ends_at": "2024-02-15T00:00:00Z",
        }
        text = format_usage_text(usage)

        assert "Pro" in text
        assert "$50.00" in text  # used
        assert "$100.00" in text  # limit
        assert "$20.00" in text  # topup
        assert "active" in text.lower()

    def test_start_tier_shows_upgrade_prompt(self) -> None:
        """Start tier should suggest upgrade."""
        from wafer.billing import format_usage_text

        usage = {
            "tier": "start",
            "status": "active",
            "credits_used_cents": 0,
            "credits_limit_cents": 0,
            "credits_remaining_cents": 0,
            "topup_balance_cents": 0,
            "has_hardware_counters": False,
            "has_slack_access": False,
            "period_ends_at": None,
        }
        text = format_usage_text(usage)

        assert "Start" in text
        assert "upgrade" in text.lower() or "portal" in text.lower()

    def test_enterprise_tier_shows_unlimited(self) -> None:
        """Enterprise tier should show unlimited credits."""
        from wafer.billing import format_usage_text

        usage = {
            "tier": "enterprise",
            "status": "active",
            "credits_used_cents": 50000,
            "credits_limit_cents": -1,  # Unlimited
            "credits_remaining_cents": -1,
            "topup_balance_cents": 0,
            "has_hardware_counters": True,
            "has_slack_access": True,
            "period_ends_at": "2024-02-15T00:00:00Z",
        }
        text = format_usage_text(usage)

        assert "Enterprise" in text
        assert "Unlimited" in text or "unlimited" in text

    def test_past_due_status_shows_warning(self) -> None:
        """past_due status should show warning."""
        from wafer.billing import format_usage_text

        usage = {
            "tier": "pro",
            "status": "past_due",
            "credits_used_cents": 5000,
            "credits_limit_cents": 10000,
            "credits_remaining_cents": 5000,
            "topup_balance_cents": 0,
            "has_hardware_counters": True,
            "has_slack_access": True,
            "period_ends_at": "2024-02-15T00:00:00Z",
        }
        text = format_usage_text(usage)

        assert "past_due" in text.lower() or "warning" in text.lower() or "⚠" in text


# =============================================================================
# Integration Tests with Mocked HTTP
# =============================================================================


class TestBillingUsageCommand:
    """Test wafer billing (usage) command."""

    def test_not_logged_in(self) -> None:
        """Should error with login guidance when not authenticated."""
        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {}  # No auth header

            with patch("wafer.billing.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.text = '{"detail": "Not authenticated"}'
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=mock_response
                )
                mock_client.return_value.__enter__.return_value.get.return_value = mock_response

                result = runner.invoke(app, ["billing"])

                assert result.exit_code != 0
                assert "login" in result.output.lower()

    def test_json_output(self) -> None:
        """Should return raw JSON with --json flag."""
        usage_data = {
            "tier": "pro",
            "status": "active",
            "credits_used_cents": 5000,
            "credits_limit_cents": 10000,
            "credits_remaining_cents": 5000,
            "topup_balance_cents": 2000,
            "has_hardware_counters": True,
            "has_slack_access": True,
            "period_ends_at": "2024-02-15T00:00:00Z",
        }

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = usage_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

                    result = runner.invoke(app, ["billing", "--json"])

                    assert result.exit_code == 0
                    data = json.loads(result.stdout)
                    assert data["tier"] == "pro"

    def test_formatted_output(self) -> None:
        """Should return formatted text without --json flag."""
        usage_data = {
            "tier": "pro",
            "status": "active",
            "credits_used_cents": 5000,
            "credits_limit_cents": 10000,
            "credits_remaining_cents": 5000,
            "topup_balance_cents": 2000,
            "has_hardware_counters": True,
            "has_slack_access": True,
            "period_ends_at": "2024-02-15T00:00:00Z",
        }

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = usage_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.get.return_value = mock_response

                    result = runner.invoke(app, ["billing"])

                    assert result.exit_code == 0
                    assert "Pro" in result.output
                    assert "$" in result.output

    def test_api_error(self) -> None:
        """Should show graceful error on API failure."""
        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_client.return_value.__enter__.return_value.get.side_effect = (
                        httpx.RequestError("Connection failed")
                    )

                    result = runner.invoke(app, ["billing"])

                    assert result.exit_code != 0
                    assert "error" in result.output.lower() or "reach" in result.output.lower()


class TestBillingTopupCommand:
    """Test wafer billing topup command."""

    def test_not_logged_in(self) -> None:
        """Should error with login guidance when not authenticated."""
        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {}

            with patch("wafer.billing.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.text = '{"detail": "Not authenticated"}'
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=mock_response
                )
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                result = runner.invoke(app, ["billing", "topup"])

                assert result.exit_code != 0
                assert "login" in result.output.lower()

    def test_default_amount_25(self) -> None:
        """Default amount should be $25."""
        checkout_data = {
            "checkout_url": "https://checkout.stripe.com/test",
            "session_id": "cs_test_123",
        }

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = checkout_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    with patch("webbrowser.open") as mock_browser:
                        result = runner.invoke(app, ["billing", "topup"])

                        assert result.exit_code == 0
                        # Verify $25 = 2500 cents was sent
                        call_args = mock_client.return_value.__enter__.return_value.post.call_args
                        assert call_args[1]["json"]["amount_cents"] == 2500
                        mock_browser.assert_called_once()

    def test_custom_amount_100(self) -> None:
        """Custom amount $100 should work."""
        checkout_data = {
            "checkout_url": "https://checkout.stripe.com/test",
            "session_id": "cs_test_123",
        }

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = checkout_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    with patch("webbrowser.open") as mock_browser:
                        result = runner.invoke(app, ["billing", "topup", "100"])

                        assert result.exit_code == 0
                        call_args = mock_client.return_value.__enter__.return_value.post.call_args
                        assert call_args[1]["json"]["amount_cents"] == 10000
                        mock_browser.assert_called_once()

    def test_amount_below_minimum(self) -> None:
        """Amount below $10 should error."""
        result = runner.invoke(app, ["billing", "topup", "5"])

        assert result.exit_code != 0
        assert "10" in result.output  # Should mention minimum

    def test_amount_above_maximum(self) -> None:
        """Amount above $500 should error."""
        result = runner.invoke(app, ["billing", "topup", "600"])

        assert result.exit_code != 0
        assert "500" in result.output  # Should mention maximum

    def test_start_tier_blocked(self) -> None:
        """Start tier users should be blocked with upgrade message."""
        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 403
                    mock_response.text = '{"detail": "Topup not available for Start tier"}'
                    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                        "403", request=MagicMock(), response=mock_response
                    )
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    result = runner.invoke(app, ["billing", "topup"])

                    assert result.exit_code != 0
                    assert "upgrade" in result.output.lower() or "portal" in result.output.lower()

    def test_no_browser_flag(self) -> None:
        """--no-browser should print URL instead of opening browser."""
        checkout_data = {
            "checkout_url": "https://checkout.stripe.com/test",
            "session_id": "cs_test_123",
        }

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = checkout_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    with patch("webbrowser.open") as mock_browser:
                        result = runner.invoke(app, ["billing", "topup", "--no-browser"])

                        assert result.exit_code == 0
                        assert "https://checkout.stripe.com/test" in result.output
                        mock_browser.assert_not_called()


class TestBillingPortalCommand:
    """Test wafer billing portal command."""

    def test_not_logged_in(self) -> None:
        """Should error with login guidance when not authenticated."""
        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {}

            with patch("wafer.billing.httpx.Client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.text = '{"detail": "Not authenticated"}'
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=mock_response
                )
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                result = runner.invoke(app, ["billing", "portal"])

                assert result.exit_code != 0
                assert "login" in result.output.lower()

    def test_success_opens_browser(self) -> None:
        """Should open browser with portal URL."""
        portal_data = {"portal_url": "https://billing.stripe.com/test"}

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = portal_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    with patch("webbrowser.open") as mock_browser:
                        result = runner.invoke(app, ["billing", "portal"])

                        assert result.exit_code == 0
                        mock_browser.assert_called_once_with("https://billing.stripe.com/test")

    def test_no_browser_flag(self) -> None:
        """--no-browser should print URL instead of opening browser."""
        portal_data = {"portal_url": "https://billing.stripe.com/test"}

        with patch("wafer.billing.get_auth_headers") as mock_auth:
            mock_auth.return_value = {"Authorization": "Bearer test"}

            with patch("wafer.billing.get_api_url") as mock_url:
                mock_url.return_value = "https://api.example.com"

                with patch("wafer.billing.httpx.Client") as mock_client:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = portal_data
                    mock_response.raise_for_status.return_value = None
                    mock_client.return_value.__enter__.return_value.post.return_value = mock_response

                    with patch("webbrowser.open") as mock_browser:
                        result = runner.invoke(app, ["billing", "portal", "--no-browser"])

                        assert result.exit_code == 0
                        assert "https://billing.stripe.com/test" in result.output
                        mock_browser.assert_not_called()


# =============================================================================
# Tests for 402 Error Handling
# =============================================================================


class TestInsufficientCreditsError:
    """Test 402 error handling in _friendly_error."""

    def test_402_error_message(self) -> None:
        """402 should show billing guidance."""
        from wafer.workspaces import _friendly_error

        message = _friendly_error(402, '{"detail": "Insufficient credits"}', "test-workspace")

        assert "credit" in message.lower()
        assert "wafer billing" in message.lower()
