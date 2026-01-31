"""Request and response types for the billing.io API.

All types are plain dataclasses with a ``from_dict`` class method that
builds an instance from the raw JSON dictionary returned by the API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


# ---------------------------------------------------------------------------
# String-literal type aliases (enum stand-ins)
# ---------------------------------------------------------------------------

Chain = Literal["tron", "arbitrum"]
"""Blockchain network."""

Token = Literal["USDT", "USDC"]
"""Stablecoin token."""

CheckoutStatus = Literal[
    "pending",
    "detected",
    "confirming",
    "confirmed",
    "expired",
    "failed",
]
"""Lifecycle status of a checkout."""

EventType = Literal[
    "checkout.created",
    "checkout.payment_detected",
    "checkout.confirming",
    "checkout.completed",
    "checkout.expired",
    "checkout.failed",
]
"""Webhook event type."""


# ---------------------------------------------------------------------------
# Resource models
# ---------------------------------------------------------------------------


@dataclass
class Checkout:
    """A crypto payment checkout."""

    checkout_id: str
    deposit_address: str
    chain: Chain
    token: Token
    amount_usd: float
    amount_atomic: str
    status: CheckoutStatus
    confirmations: int
    required_confirmations: int
    expires_at: str
    created_at: str
    tx_hash: Optional[str] = None
    detected_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Checkout:
        return cls(
            checkout_id=data["checkout_id"],
            deposit_address=data["deposit_address"],
            chain=data["chain"],
            token=data["token"],
            amount_usd=data["amount_usd"],
            amount_atomic=data["amount_atomic"],
            status=data["status"],
            confirmations=data.get("confirmations", 0),
            required_confirmations=data.get("required_confirmations", 0),
            expires_at=data["expires_at"],
            created_at=data["created_at"],
            tx_hash=data.get("tx_hash"),
            detected_at=data.get("detected_at"),
            confirmed_at=data.get("confirmed_at"),
            metadata=data.get("metadata") or {},
        )


@dataclass
class CheckoutStatusResponse:
    """Lightweight status snapshot returned by the polling endpoint."""

    checkout_id: str
    status: CheckoutStatus
    confirmations: int
    required_confirmations: int
    polling_interval_ms: int
    tx_hash: Optional[str] = None
    detected_at: Optional[str] = None
    confirmed_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CheckoutStatusResponse:
        return cls(
            checkout_id=data["checkout_id"],
            status=data["status"],
            confirmations=data.get("confirmations", 0),
            required_confirmations=data.get("required_confirmations", 0),
            polling_interval_ms=data.get("polling_interval_ms", 2000),
            tx_hash=data.get("tx_hash"),
            detected_at=data.get("detected_at"),
            confirmed_at=data.get("confirmed_at"),
        )


@dataclass
class CheckoutList:
    """A paginated list of checkouts."""

    data: List[Checkout]
    has_more: bool
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CheckoutList:
        return cls(
            data=[Checkout.from_dict(c) for c in data.get("data", [])],
            has_more=data.get("has_more", False),
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class WebhookEndpoint:
    """A registered webhook endpoint."""

    webhook_id: str
    url: str
    events: List[EventType]
    status: str
    created_at: str
    secret: Optional[str] = None
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WebhookEndpoint:
        return cls(
            webhook_id=data["webhook_id"],
            url=data["url"],
            events=data.get("events", []),
            status=data.get("status", "active"),
            created_at=data["created_at"],
            secret=data.get("secret"),
            description=data.get("description"),
        )


@dataclass
class WebhookEndpointList:
    """A paginated list of webhook endpoints."""

    data: List[WebhookEndpoint]
    has_more: bool
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WebhookEndpointList:
        return cls(
            data=[WebhookEndpoint.from_dict(w) for w in data.get("data", [])],
            has_more=data.get("has_more", False),
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class Event:
    """A webhook event."""

    event_id: str
    type: EventType
    checkout_id: str
    data: Checkout
    created_at: str

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> Event:
        return cls(
            event_id=raw["event_id"],
            type=raw["type"],
            checkout_id=raw["checkout_id"],
            data=Checkout.from_dict(raw["data"]),
            created_at=raw["created_at"],
        )


@dataclass
class EventList:
    """A paginated list of events."""

    data: List[Event]
    has_more: bool
    next_cursor: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EventList:
        return cls(
            data=[Event.from_dict(e) for e in data.get("data", [])],
            has_more=data.get("has_more", False),
            next_cursor=data.get("next_cursor"),
        )


@dataclass
class HealthResponse:
    """Service health status."""

    status: str
    version: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> HealthResponse:
        return cls(
            status=data["status"],
            version=data["version"],
        )
