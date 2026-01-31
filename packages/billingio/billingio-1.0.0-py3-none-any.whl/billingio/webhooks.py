"""Webhook signature verification for the billing.io SDK.

Port of the reference TypeScript implementation.  Uses only the Python
standard library (``hmac``, ``hashlib``, ``json``, ``time``).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict

from .errors import WebhookVerificationError

SIGNATURE_HEADER = "x-billing-signature"
"""The HTTP header that carries the webhook signature."""

_DEFAULT_TOLERANCE = 300  # 5 minutes


def verify_webhook_signature(
    raw_body: str,
    signature_header: str,
    secret: str,
    tolerance: int = _DEFAULT_TOLERANCE,
) -> Dict[str, Any]:
    """Verify an incoming webhook and return the parsed event payload.

    Parameters
    ----------
    raw_body:
        The raw request body as a string.  Do **not** parse the JSON before
        passing it in -- the signature is computed over the raw bytes.
    signature_header:
        The value of the ``X-Billing-Signature`` header.  Format:
        ``t={unix_timestamp},v1={hex_hmac_sha256}``.
    secret:
        Your webhook endpoint signing secret (prefixed ``whsec_``).
    tolerance:
        Maximum allowed age of the event in seconds.  Defaults to 300 (5
        minutes).  Set to ``0`` to disable the timestamp check.

    Returns
    -------
    dict
        The parsed webhook event payload.

    Raises
    ------
    WebhookVerificationError
        If the header is missing or malformed, the timestamp is outside the
        tolerance window, or the signature does not match.
    """

    if not signature_header:
        raise WebhookVerificationError("Missing signature header")

    if not secret:
        raise WebhookVerificationError("Missing webhook secret")

    timestamp, signature = _parse_signature_header(signature_header)

    # -- Timestamp tolerance check ------------------------------------------
    if tolerance > 0:
        now = int(time.time())
        if abs(now - timestamp) > tolerance:
            raise WebhookVerificationError(
                f"Timestamp outside tolerance. Event: {timestamp}, "
                f"now: {now}, tolerance: {tolerance}s"
            )

    # -- HMAC-SHA256 verification -------------------------------------------
    signed_payload = f"{timestamp}.{raw_body}"
    expected = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise WebhookVerificationError("Signature mismatch")

    # -- Parse payload ------------------------------------------------------
    try:
        return json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise WebhookVerificationError(
            "Invalid JSON in webhook body"
        ) from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_signature_header(header: str) -> tuple[int, str]:
    """Parse ``t={timestamp},v1={hex_signature}`` into its components."""

    parts: Dict[str, str] = {}
    for segment in header.split(","):
        key, _, value = segment.partition("=")
        parts[key.strip()] = value.strip()

    try:
        timestamp = int(parts["t"])
    except (KeyError, ValueError):
        raise WebhookVerificationError(
            "Invalid signature header format. "
            "Expected: t={timestamp},v1={signature}"
        )

    signature = parts.get("v1")
    if not signature:
        raise WebhookVerificationError(
            "Invalid signature header format. "
            "Expected: t={timestamp},v1={signature}"
        )

    return timestamp, signature
