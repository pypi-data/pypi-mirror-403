"""Tests for authentication and credential management.

Tests the auth module's token verification and network error handling.

Run with: PYTHONPATH=. uv run pytest tests/test_auth.py -v
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

# =============================================================================
# Unit Tests for get_valid_token Network Error Handling
# =============================================================================


class TestGetValidTokenNetworkErrors:
    """Test that get_valid_token handles network errors gracefully."""

    def test_returns_none_on_read_timeout(self) -> None:
        """get_valid_token returns None when verify_token times out."""
        from wafer.auth import Credentials, get_valid_token

        mock_creds = Credentials(
            access_token="test_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", side_effect=httpx.ReadTimeout("timeout")):
                result = get_valid_token()

        assert result is None

    def test_returns_none_on_connect_timeout(self) -> None:
        """get_valid_token returns None when connection times out."""
        from wafer.auth import Credentials, get_valid_token

        mock_creds = Credentials(
            access_token="test_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", side_effect=httpx.ConnectTimeout("timeout")):
                result = get_valid_token()

        assert result is None

    def test_returns_none_on_connection_error(self) -> None:
        """get_valid_token returns None when connection is refused."""
        from wafer.auth import Credentials, get_valid_token

        mock_creds = Credentials(
            access_token="test_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", side_effect=httpx.ConnectError("refused")):
                result = get_valid_token()

        assert result is None

    def test_returns_none_on_refresh_timeout(self) -> None:
        """get_valid_token returns None when refresh token request times out."""
        from wafer.auth import Credentials, get_valid_token

        mock_creds = Credentials(
            access_token="expired_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        # Create a mock 401 response for verify_token
        mock_response = MagicMock()
        mock_response.status_code = 401
        http_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_response)

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", side_effect=http_error):
                with patch("wafer.auth.refresh_access_token", side_effect=httpx.ReadTimeout("timeout")):
                    result = get_valid_token()

        assert result is None

    def test_returns_token_when_verify_succeeds(self) -> None:
        """get_valid_token returns token when verification succeeds."""
        from wafer.auth import Credentials, UserInfo, get_valid_token

        mock_creds = Credentials(
            access_token="valid_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        mock_user_info = UserInfo(user_id="user123", email="test@example.com")

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", return_value=mock_user_info):
                result = get_valid_token()

        assert result == "valid_token"

    def test_returns_none_when_no_credentials(self) -> None:
        """get_valid_token returns None when no credentials are stored."""
        from wafer.auth import get_valid_token

        with patch("wafer.auth.load_credentials", return_value=None):
            result = get_valid_token()

        assert result is None


class TestVerifyTokenRaisesOnNetworkError:
    """Document that verify_token raises network errors (caller must handle)."""

    def test_verify_token_raises_read_timeout(self) -> None:
        """verify_token raises ReadTimeout when API times out."""
        from wafer.auth import verify_token

        with patch("wafer.auth.get_api_url", return_value="https://api.example.com"):
            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.__enter__ = MagicMock(return_value=mock_client)
                mock_client.__exit__ = MagicMock(return_value=False)
                mock_client.post.side_effect = httpx.ReadTimeout("timeout")
                mock_client_class.return_value = mock_client

                with pytest.raises(httpx.ReadTimeout):
                    verify_token("test_token")

    def test_verify_token_raises_connect_error(self) -> None:
        """verify_token raises ConnectError when API is unreachable."""
        from wafer.auth import verify_token

        with patch("wafer.auth.get_api_url", return_value="https://api.example.com"):
            with patch("httpx.Client") as mock_client_class:
                mock_client = MagicMock()
                mock_client.__enter__ = MagicMock(return_value=mock_client)
                mock_client.__exit__ = MagicMock(return_value=False)
                mock_client.post.side_effect = httpx.ConnectError("refused")
                mock_client_class.return_value = mock_client

                with pytest.raises(httpx.ConnectError):
                    verify_token("test_token")


# =============================================================================
# Unit Tests for get_auth_headers
# =============================================================================


class TestGetAuthHeaders:
    """Test get_auth_headers returns empty dict on network errors."""

    def test_returns_empty_dict_on_network_error(self) -> None:
        """get_auth_headers returns {} when network error occurs."""
        from wafer.auth import Credentials, get_auth_headers

        mock_creds = Credentials(
            access_token="test_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", side_effect=httpx.ReadTimeout("timeout")):
                result = get_auth_headers()

        assert result == {}

    def test_returns_headers_on_success(self) -> None:
        """get_auth_headers returns Bearer token when successful."""
        from wafer.auth import Credentials, UserInfo, get_auth_headers

        mock_creds = Credentials(
            access_token="valid_token",
            refresh_token="test_refresh",
            email="test@example.com",
        )

        mock_user_info = UserInfo(user_id="user123", email="test@example.com")

        with patch("wafer.auth.load_credentials", return_value=mock_creds):
            with patch("wafer.auth.verify_token", return_value=mock_user_info):
                result = get_auth_headers()

        assert result == {"Authorization": "Bearer valid_token"}
