"""billing.io Python SDK -- official client library for the billing.io API.

Quick start::

    from billingio import BillingIO

    client = BillingIO(api_key="sk_test_...")
    checkout = client.checkouts.create(
        amount_usd=49.99,
        chain="tron",
        token="USDT",
    )
    print(checkout.checkout_id)
"""

from .client import BillingIO
from .errors import BillingIOError, WebhookVerificationError
from .pagination import auto_paginate
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
from .webhooks import SIGNATURE_HEADER, verify_webhook_signature

__version__ = "1.0.0"

__all__ = [
    # Client
    "BillingIO",
    # Errors
    "BillingIOError",
    "WebhookVerificationError",
    # Types
    "Chain",
    "Checkout",
    "CheckoutList",
    "CheckoutStatus",
    "CheckoutStatusResponse",
    "Event",
    "EventList",
    "EventType",
    "HealthResponse",
    "Token",
    "WebhookEndpoint",
    "WebhookEndpointList",
    # Webhooks
    "SIGNATURE_HEADER",
    "verify_webhook_signature",
    # Pagination
    "auto_paginate",
]
