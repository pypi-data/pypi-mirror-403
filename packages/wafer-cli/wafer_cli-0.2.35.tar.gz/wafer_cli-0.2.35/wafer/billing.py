"""Billing CLI - Manage credits and subscription.

This module provides the implementation for the `wafer billing` subcommand.
"""

import json

import httpx

from .api_client import get_api_url
from .auth import get_auth_headers


def _get_client() -> tuple[str, dict[str, str]]:
    """Get API URL and auth headers."""
    api_url = get_api_url()
    headers = get_auth_headers()

    assert api_url, "API URL must be configured"
    assert api_url.startswith("http"), "API URL must be a valid HTTP(S) URL"

    return api_url, headers


def format_cents(cents: int) -> str:
    """Format cents as a dollar amount.

    Args:
        cents: Amount in cents (e.g., 2500 for $25.00)

    Returns:
        Formatted string (e.g., "$25.00")
    """
    dollars = cents / 100
    return f"${dollars:.2f}"


def validate_topup_amount(amount_cents: int) -> None:
    """Validate topup amount is within allowed range.

    Args:
        amount_cents: Amount in cents

    Raises:
        ValueError: If amount is out of range ($10-$500)
    """
    min_cents = 1000  # $10
    max_cents = 50000  # $500

    if amount_cents < min_cents:
        raise ValueError(f"Amount must be at least ${min_cents // 100}")

    if amount_cents > max_cents:
        raise ValueError(f"Amount must be at most ${max_cents // 100}")


def format_usage_text(usage: dict) -> str:
    """Format billing usage as human-readable text.

    Args:
        usage: Usage data from API

    Returns:
        Formatted multi-line string
    """
    tier = usage.get("tier", "unknown")
    status = usage.get("status", "unknown")
    credits_used = usage.get("credits_used_cents", 0)
    credits_limit = usage.get("credits_limit_cents", 0)
    credits_remaining = usage.get("credits_remaining_cents", 0)
    topup_balance = usage.get("topup_balance_cents", 0)
    has_hw_counters = usage.get("has_hardware_counters", False)
    has_slack = usage.get("has_slack_access", False)
    period_ends = usage.get("period_ends_at")

    # Capitalize tier for display
    tier_display = tier.capitalize()

    lines = [
        "Billing Summary",
        "===============",
        "",
        f"  Tier: {tier_display}",
        f"  Status: {status}",
    ]

    # Status warnings
    if status == "past_due":
        lines.append("  ⚠ Warning: Payment past due. Please update payment method.")

    lines.append("")

    # Credits section - different handling for enterprise (unlimited)
    if credits_limit == -1 or tier.lower() == "enterprise":
        lines.extend([
            "Credits:",
            f"  Used this period: {format_cents(credits_used)}",
            "  Limit: Unlimited",
        ])
    else:
        lines.extend([
            "Credits:",
            f"  Used: {format_cents(credits_used)}",
            f"  Limit: {format_cents(credits_limit)}",
            f"  Remaining: {format_cents(credits_remaining)}",
        ])

    # Topup balance
    if topup_balance > 0:
        lines.append(f"  Topup balance: {format_cents(topup_balance)}")

    lines.append("")

    # Features
    lines.append("Features:")
    lines.append(f"  Hardware counters: {'Yes' if has_hw_counters else 'No'}")
    lines.append(f"  Slack support: {'Yes' if has_slack else 'No'}")

    # Period end date
    if period_ends:
        lines.append("")
        lines.append(f"Period ends: {period_ends}")

    # Upgrade prompt for Start tier
    if tier.lower() == "start":
        lines.extend([
            "",
            "Upgrade to Pro for hardware counters and credit topups:",
            "  wafer billing portal",
        ])

    return "\n".join(lines)


def get_usage(json_output: bool = False) -> str:
    """Get billing usage information.

    Args:
        json_output: If True, return raw JSON; otherwise return formatted text

    Returns:
        Usage info as string (JSON or formatted text)

    Raises:
        RuntimeError: On authentication or API errors
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.get(f"{api_url}/v1/billing/usage")
            response.raise_for_status()
            usage = response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e

    if json_output:
        return json.dumps(usage, indent=2)

    return format_usage_text(usage)


def create_topup(amount_cents: int) -> dict:
    """Create a topup checkout session.

    Args:
        amount_cents: Amount to add in cents (1000-50000)

    Returns:
        Dict with checkout_url and session_id

    Raises:
        RuntimeError: On authentication, validation, or API errors
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.post(
                f"{api_url}/v1/billing/topup",
                json={"amount_cents": amount_cents},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        if e.response.status_code == 400:
            # Invalid amount
            try:
                detail = e.response.json().get("detail", e.response.text)
            except Exception:
                detail = e.response.text
            raise RuntimeError(f"Invalid amount: {detail}") from e
        if e.response.status_code == 403:
            # Start tier or other restriction
            raise RuntimeError(
                "Topup not available for your subscription tier.\n"
                "Upgrade your subscription first: wafer billing portal"
            ) from e
        if e.response.status_code == 503:
            raise RuntimeError("Billing service temporarily unavailable. Please try again later.") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e


def get_portal_url() -> dict:
    """Get Stripe billing portal URL.

    Returns:
        Dict with portal_url

    Raises:
        RuntimeError: On authentication or API errors
    """
    api_url, headers = _get_client()

    try:
        with httpx.Client(timeout=30.0, headers=headers) as client:
            response = client.post(f"{api_url}/v1/billing/portal")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise RuntimeError("Not authenticated. Run: wafer login") from e
        raise RuntimeError(f"API error: {e.response.status_code} - {e.response.text}") from e
    except httpx.RequestError as e:
        raise RuntimeError(f"Could not reach API: {e}") from e
