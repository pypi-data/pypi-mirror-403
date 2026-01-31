"""High-level client for the billing.io API.

Usage::

    from billingio import BillingIO

    client = BillingIO(api_key="sk_live_...")
    checkout = client.checkouts.create(
        amount_usd=49.99,
        chain="tron",
        token="USDT",
    )
    print(checkout.checkout_id)
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ._http import _HTTPClient
from .types import (
    Chain,
    Checkout,
    CheckoutList,
    CheckoutStatus,
    CheckoutStatusResponse,
    Event,
    EventList,
    EventType,
    HealthResponse,
    Token,
    WebhookEndpoint,
    WebhookEndpointList,
)

_DEFAULT_BASE_URL = "https://api.billing.io/v1"


# ========================================================================= #
# Resource namespaces
# ========================================================================= #


class _Checkouts:
    """Operations on the ``/checkouts`` resource."""

    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def create(
        self,
        amount_usd: float,
        chain: Chain,
        token: Token,
        *,
        expires_in_seconds: int = 1800,
        metadata: Optional[Dict[str, str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Checkout:
        """Create a new checkout.

        Parameters
        ----------
        amount_usd:
            Payment amount in US dollars (min 0.01).
        chain:
            Blockchain network (``"tron"`` or ``"arbitrum"``).
        token:
            Stablecoin token (``"USDT"`` or ``"USDC"``).
        expires_in_seconds:
            Checkout TTL in seconds.  Must be between 300 and 86400.
            Defaults to 1800 (30 minutes).
        metadata:
            Arbitrary key-value pairs attached to the checkout (max 20 keys).
        idempotency_key:
            Client-generated UUID for safe retries.  Reusing a key with
            different parameters returns a 409.
        """
        body: Dict = {
            "amount_usd": amount_usd,
            "chain": chain,
            "token": token,
            "expires_in_seconds": expires_in_seconds,
        }
        if metadata is not None:
            body["metadata"] = metadata

        headers: Optional[Dict[str, str]] = None
        if idempotency_key is not None:
            headers = {"Idempotency-Key": idempotency_key}

        data = self._http.post("/checkouts", json=body, headers=headers)
        return Checkout.from_dict(data)

    def list(
        self,
        *,
        cursor: Optional[str] = None,
        limit: int = 25,
        status: Optional[CheckoutStatus] = None,
    ) -> CheckoutList:
        """Return a paginated list of checkouts, newest first.

        Parameters
        ----------
        cursor:
            Opaque cursor for the next page.  Omit for the first page.
        limit:
            Number of items per page (1--100, default 25).
        status:
            Filter by checkout status.
        """
        params = {"cursor": cursor, "limit": limit, "status": status}
        data = self._http.get("/checkouts", params=params)
        return CheckoutList.from_dict(data)

    def get(self, checkout_id: str) -> Checkout:
        """Retrieve a single checkout by ID.

        Parameters
        ----------
        checkout_id:
            The checkout identifier (prefixed ``co_``).
        """
        data = self._http.get(f"/checkouts/{checkout_id}")
        return Checkout.from_dict(data)

    def get_status(self, checkout_id: str) -> CheckoutStatusResponse:
        """Lightweight status endpoint optimised for polling.

        Parameters
        ----------
        checkout_id:
            The checkout identifier (prefixed ``co_``).
        """
        data = self._http.get(f"/checkouts/{checkout_id}/status")
        return CheckoutStatusResponse.from_dict(data)


class _Webhooks:
    """Operations on the ``/webhooks`` resource."""

    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def create(
        self,
        url: str,
        events: List[EventType],
        *,
        description: Optional[str] = None,
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint.

        Parameters
        ----------
        url:
            HTTPS endpoint to receive events.
        events:
            Event types to subscribe to.
        description:
            Optional human-readable label (max 256 characters).
        """
        body: Dict = {"url": url, "events": events}
        if description is not None:
            body["description"] = description

        data = self._http.post("/webhooks", json=body)
        return WebhookEndpoint.from_dict(data)

    def list(
        self,
        *,
        cursor: Optional[str] = None,
        limit: int = 25,
    ) -> WebhookEndpointList:
        """Return a paginated list of webhook endpoints.

        Parameters
        ----------
        cursor:
            Opaque cursor for the next page.
        limit:
            Number of items per page (1--100, default 25).
        """
        params = {"cursor": cursor, "limit": limit}
        data = self._http.get("/webhooks", params=params)
        return WebhookEndpointList.from_dict(data)

    def get(self, webhook_id: str) -> WebhookEndpoint:
        """Retrieve a single webhook endpoint by ID.

        Parameters
        ----------
        webhook_id:
            The webhook endpoint identifier (prefixed ``we_``).
        """
        data = self._http.get(f"/webhooks/{webhook_id}")
        return WebhookEndpoint.from_dict(data)

    def delete(self, webhook_id: str) -> None:
        """Delete a webhook endpoint.

        Parameters
        ----------
        webhook_id:
            The webhook endpoint identifier (prefixed ``we_``).
        """
        self._http.delete(f"/webhooks/{webhook_id}")


class _Events:
    """Operations on the ``/events`` resource."""

    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def list(
        self,
        *,
        cursor: Optional[str] = None,
        limit: int = 25,
        type: Optional[EventType] = None,
        checkout_id: Optional[str] = None,
    ) -> EventList:
        """Return a paginated list of webhook events, newest first.

        Parameters
        ----------
        cursor:
            Opaque cursor for the next page.
        limit:
            Number of items per page (1--100, default 25).
        type:
            Filter by event type.
        checkout_id:
            Filter events for a specific checkout.
        """
        params = {
            "cursor": cursor,
            "limit": limit,
            "type": type,
            "checkout_id": checkout_id,
        }
        data = self._http.get("/events", params=params)
        return EventList.from_dict(data)

    def get(self, event_id: str) -> Event:
        """Retrieve a single event by ID.

        Parameters
        ----------
        event_id:
            The event identifier (prefixed ``evt_``).
        """
        data = self._http.get(f"/events/{event_id}")
        return Event.from_dict(data)


class _Health:
    """Operations on the ``/health`` resource."""

    def __init__(self, http: _HTTPClient) -> None:
        self._http = http

    def get(self) -> HealthResponse:
        """Check whether the billing.io API is healthy."""
        data = self._http.get("/health")
        return HealthResponse.from_dict(data)


# ========================================================================= #
# Main client
# ========================================================================= #


class BillingIO:
    """Official Python client for the billing.io API.

    Parameters
    ----------
    api_key:
        Your secret API key (prefixed ``sk_live_`` or ``sk_test_``).
    base_url:
        Override the API base URL.  Defaults to
        ``https://api.billing.io/v1``.

    Example
    -------
    ::

        from billingio import BillingIO

        client = BillingIO(api_key="sk_test_...")
        checkout = client.checkouts.create(
            amount_usd=9.99,
            chain="tron",
            token="USDT",
        )
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._http = _HTTPClient(api_key, base_url)

        self.checkouts = _Checkouts(self._http)
        """Access the :doc:`Checkouts <checkouts>` resource."""

        self.webhooks = _Webhooks(self._http)
        """Access the :doc:`Webhooks <webhooks>` resource."""

        self.events = _Events(self._http)
        """Access the :doc:`Events <events>` resource."""

        self.health = _Health(self._http)
        """Access the :doc:`Health <health>` resource."""
